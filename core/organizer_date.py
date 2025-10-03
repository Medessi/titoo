# coding: utf-8

import os
import shutil

import time
from logs.logger import logger






from .organizer_utils import obtenir_date_creation, creer_dossier_si_absent, verifier_conflit_fichier

from .history import  enregistrer_action,enregistrer_organisation




def classer_par_date(dossier, mode_simulation=False, limite_traitement=None):
    """
    Organise les fichiers par année/mois dans des sous-dossiers basés sur leur date de création.
    
    Args:
        dossier: Le dossier à organiser
        mode_simulation: Si True, montre les actions sans les exécuter
        limite_traitement: Nombre maximum de fichiers à traiter (None pour tous)
    """
    fichiers = [f for f in os.listdir(dossier) if os.path.isfile(os.path.join(dossier, f))]
    
    # Appliquer la limite si spécifiée
    if limite_traitement and len(fichiers) > limite_traitement:
        logger.info(f"Limitation à {limite_traitement} fichiers sur {len(fichiers)} au total")
        fichiers = fichiers[:limite_traitement]
    
    fichiers_traites = 0
    for fichier in fichiers:
        chemin_complet = os.path.join(dossier, fichier)
        date_fichier = obtenir_date_creation(chemin_complet)
       # Déterminer l'année et le trimestre
        annee = str(date_fichier.year)
        mois = date_fichier.strftime("%B").capitalize()  # Nom complet du mois en français
        
        chemin_destination = os.path.join(dossier, annee)
        
        if not mode_simulation:
            creer_dossier_si_absent(chemin_destination)
        
        nouveau_chemin = os.path.join(chemin_destination, fichier)
        nouveau_chemin = verifier_conflit_fichier(nouveau_chemin)
        liste_actions = []

        if mode_simulation:
           if mode_simulation:
            logger.info(f"[SIMULATION] Déplacement par date: {fichier} → {annee}/{os.path.basename(nouveau_chemin)}")
        else:
            try:
                
                liste_actions.append({
                    "type": "Déplacement",
                    "source": chemin_complet,
                    "destination": nouveau_chemin,
                   
                })
                enregistrer_organisation(liste_actions)
                enregistrer_action("Organisation par date", f"Dossier : {dossier}", "nouveau sous dossier crée")

                shutil.move(chemin_complet, nouveau_chemin)

                logger.info(f"Déplacé par date: {fichier} → {annee}/{os.path.basename(nouveau_chemin)}")
                fichiers_traites += 1

            except Exception as e:
                logger.error(f"Erreur lors du déplacement de {fichier}: {e}")
                # Attendre et réessayer une fois
                try:
                    time.sleep(1)  # Attendre 1 seconde
                    shutil.move(chemin_complet, nouveau_chemin)
                    logger.info(f"Déplacé après reprise: {fichier} → {annee}/{os.path.basename(nouveau_chemin)}")
                    fichiers_traites += 1
                except Exception as e2:
                    logger.error(f"Échec définitif pour {fichier}: {e2}")
    
    return fichiers_traites
