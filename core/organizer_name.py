# coding: utf-8

import os
import shutil
import datetime
import time
from logs.logger import logger
import re
from pathlib import Path
from collections import defaultdict
from .organizer_utils import creer_dossier_si_absent, verifier_conflit_fichier
from .history import enregistrer_organisation


def extraire_nom_base(nom_fichier):
    """
    Extrait le nom de base d'un fichier en enlevant les numéros, dates, versions, etc.
    
    Args:
        nom_fichier: Le nom du fichier avec ou sans extension
    
    Returns:
        Le nom de base nettoyé
    """
    # Enlever l'extension
    nom_sans_ext = Path(nom_fichier).stem
    
    # Enlever les numéros à la fin (ex: fichier_001, document_2, photo_12)
    nom_base = re.sub(r'[-_\s]*\d+$', '', nom_sans_ext)
    
    # Enlever les dates (formats variés)
    nom_base = re.sub(r'[-_\s]*\d{2,4}[-_]\d{1,2}[-_]\d{1,4}', '', nom_base)
    nom_base = re.sub(r'[-_\s]*\d{8}', '', nom_base)  # Format YYYYMMDD
    
    # Enlever les timestamps
    nom_base = re.sub(r'[-_\s]*\d{6,}', '', nom_base)
    
    # Enlever les versions et suffixes courants
    suffixes_pattern = r'[-_\s]*(copy|copie|final|finale?|v\d+|version\d*|draft|brouillon|temp|tmp|backup|bak|old|ancien|nouveau|new)$'
    nom_base = re.sub(suffixes_pattern, '', nom_base, flags=re.IGNORECASE)
    
    # Enlever les espaces et caractères spéciaux en début/fin
    nom_base = nom_base.strip('_-. ')
    
    return nom_base if nom_base else nom_sans_ext


def detecter_prefixe_commun(noms_fichiers):
    """
    Détecte le préfixe commun le plus long entre plusieurs noms de fichiers
    
    Args:
        noms_fichiers: Liste des noms de fichiers
    
    Returns:
        Le préfixe commun ou chaîne vide
    """
    if not noms_fichiers or len(noms_fichiers) < 2:
        return ""
    
    # Trouve le préfixe commun
    prefixe = os.path.commonprefix(noms_fichiers)
    
    # S'assurer que le préfixe se termine à un caractère logique
    if prefixe and not prefixe[-1].isalnum():
        prefixe = prefixe.rstrip('_-. ')
    
    # Retourner seulement si le préfixe est significatif (plus de 3 caractères)
    return prefixe if len(prefixe) > 3 else ""


def grouper_fichiers_par_nom(fichiers, seuil_minimum=2):
    """
    Groupe les fichiers ayant des noms similaires
    
    Args:
        fichiers: Liste des noms de fichiers
        seuil_minimum: Nombre minimum de fichiers pour former un groupe
    
    Returns:
        Dictionnaire {nom_groupe: [liste_fichiers]}
    """
    groupes = defaultdict(list)
    
    # Étape 1: Grouper par nom de base
    groupes_nom_base = defaultdict(list)
    for fichier in fichiers:
        nom_base = extraire_nom_base(fichier)
        if nom_base:
            groupes_nom_base[nom_base].append(fichier)
    
    # Étape 2: Conserver les groupes avec assez de fichiers
    fichiers_restants = []
    for nom_base, liste_fichiers in groupes_nom_base.items():
        if len(liste_fichiers) >= seuil_minimum:
            groupes[nom_base] = liste_fichiers
        else:
            fichiers_restants.extend(liste_fichiers)
    
    # Étape 3: Grouper les fichiers restants par préfixes
    if fichiers_restants:
        groupes_prefixes = defaultdict(list)
        
        for fichier in fichiers_restants:
            # Extraire le premier mot comme préfixe potentiel
            mots = re.split(r'[-_\s]+', Path(fichier).stem)
            if len(mots) > 1 and len(mots[0]) > 2:
                prefixe = mots[0]
                groupes_prefixes[prefixe].append(fichier)
            else:
                # Fichiers sans pattern clair
                groupes_prefixes['Divers'].append(fichier)
        
        # Ajouter les groupes de préfixes suffisamment grands
        for prefixe, liste_fichiers in groupes_prefixes.items():
            if len(liste_fichiers) >= seuil_minimum:
                groupes[f"Prefixe_{prefixe}"] = liste_fichiers
    
    return groupes


def creer_nom_dossier_securise(nom):
    """
    Crée un nom de dossier sûr en supprimant les caractères invalides
    
    Args:
        nom: Le nom proposé pour le dossier
    
    Returns:
        Un nom de dossier valide
    """
    # Remplacer les caractères interdits par des underscores
    nom_securise = re.sub(r'[<>:"/\\|?*]', '_', nom)
    
    # Limiter la longueur
    if len(nom_securise) > 50:
        nom_securise = nom_securise[:50]
    
    # S'assurer que le nom n'est pas vide
    if not nom_securise.strip():
        nom_securise = "Groupe_Fichiers"
    
    return nom_securise.strip()


def classer_fichier_par_nom(dossier, mode_simulation=False, limite_traitement=None, seuil_minimum=2):
    """
    Classe les fichiers par noms similaires dans des sous-dossiers.
    
    Args:
        dossier: Le dossier à organiser
        mode_simulation: Si True, montre les actions sans les exécuter
        limite_traitement: Nombre maximum de fichiers à traiter (None pour tous)
        seuil_minimum: Nombre minimum de fichiers pour créer un groupe
    
    Returns:
        Nombre de fichiers traités
    """
    logger.info(f"Début de l'organisation par nom dans: {dossier}")
    
    # Récupérer tous les fichiers du dossier
    tous_fichiers = [f for f in os.listdir(dossier) if os.path.isfile(os.path.join(dossier, f))]
    
    if not tous_fichiers:
        logger.info("Aucun fichier trouvé dans le dossier")
        return 0
    
    logger.info(f"Nombre total de fichiers trouvés: {len(tous_fichiers)}")
    
    # Appliquer la limite si spécifiée
    if limite_traitement and len(tous_fichiers) > limite_traitement:
        logger.info(f"Limitation à {limite_traitement} fichiers sur {len(tous_fichiers)} au total")
        fichiers = tous_fichiers[:limite_traitement]
    else:
        fichiers = tous_fichiers
    
    # Grouper les fichiers par noms similaires
    groupes = grouper_fichiers_par_nom(fichiers, seuil_minimum)
    
    if not groupes:
        logger.info("Aucun groupe de fichiers similaires trouvé")
        return 0
    
    logger.info(f"Nombre de groupes détectés: {len(groupes)}")
    
    fichiers_traites = 0
    liste_actions = []
    
    for nom_groupe, fichiers_groupe in groupes.items():
        logger.info(f"Traitement du groupe '{nom_groupe}' avec {len(fichiers_groupe)} fichiers")
        
        # Créer un nom de dossier sécurisé
        nom_dossier = creer_nom_dossier_securise(nom_groupe)
        dossier_destination = os.path.join(dossier, nom_dossier)
        
        if not mode_simulation:
            creer_dossier_si_absent(dossier_destination)
        
        # Traiter chaque fichier du groupe
        for fichier in fichiers_groupe:
            chemin_source = os.path.join(dossier, fichier)
            
            if not os.path.exists(chemin_source):
                logger.warning(f"Fichier introuvable: {fichier}")
                continue
            
            # Vérifier les conflits et obtenir le chemin final
            chemin_destination = os.path.join(dossier_destination, fichier)
            chemin_destination = verifier_conflit_fichier(chemin_destination)
            
            if mode_simulation:
                logger.info(f"[SIMULATION] Déplacement: {fichier} → {nom_dossier}/{os.path.basename(chemin_destination)}")
            else:
                try:
                    date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    
                    # Déplacer le fichier
                    shutil.move(chemin_source, chemin_destination)
                    
                    # Enregistrer l'action
                    action = {
                        "type": "Organisation par nom",
                        "source": chemin_source,
                        "destination": chemin_destination,
                        "date": date,
                        "details": f"Déplacement de {fichier} vers {nom_dossier}/{os.path.basename(chemin_destination)}"
                    }
                    liste_actions.append(action)
                    
                    logger.info(f"Déplacé: {fichier} → {nom_dossier}/{os.path.basename(chemin_destination)}")
                    fichiers_traites += 1
                    
                except FileNotFoundError:
                    logger.error(f"Fichier introuvable lors du déplacement: {fichier}")
                except Exception as e:
                    logger.error(f"Erreur lors du déplacement de {fichier}: {e}")
                    
                    # Tentative de reprise après délai
                    try:
                        time.sleep(1)
                        shutil.move(chemin_source, chemin_destination)
                        logger.info(f"Déplacé après reprise: {fichier} → {nom_dossier}/{os.path.basename(chemin_destination)}")
                        fichiers_traites += 1
                        
                        # Enregistrer l'action après reprise
                        action = {
                            "type": "Organisation par nom",
                            "source": chemin_source,
                            "destination": chemin_destination,
                            "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "details": f"Déplacement de {fichier} vers {nom_dossier}/{os.path.basename(chemin_destination)} (après reprise)"
                        }
                        liste_actions.append(action)
                        
                    except Exception as e2:
                        logger.error(f"Échec définitif pour {fichier}: {e2}")
    
    # Enregistrer toutes les actions dans l'historique
    if liste_actions and not mode_simulation:
        enregistrer_organisation(liste_actions)
    
    logger.info(f"Organisation terminée. Fichiers traités: {fichiers_traites}")
    return fichiers_traites


# Fonction utilitaire pour utilisation directe
def organiser_par_nom(dossier_cible, simulation=False, limite=None, seuil=2):
    """
    Fonction simple pour organiser un dossier par noms de fichiers
    
    Args:
        dossier_cible: Chemin du dossier à organiser
        simulation: Mode simulation (True/False)
        limite: Limite de fichiers à traiter
        seuil: Nombre minimum de fichiers pour créer un groupe
    
    Returns:
        Nombre de fichiers traités
    """
    if not os.path.exists(dossier_cible):
        logger.error(f"Le dossier {dossier_cible} n'existe pas")
        return 0
    
    return classer_fichier_par_nom(dossier_cible, simulation, limite, seuil)


