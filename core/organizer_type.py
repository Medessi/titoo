# coding: utf-8

import os
import shutil

import time
from logs.logger import logger
import re


from .organizer_utils import creer_dossier_si_absent, verifier_conflit_fichier
from .history import enregistrer_organisation, enregistrer_action


from config import DEFAULT_TYPES_FICHIERS

def classer_fichier_par_type(dossier, mode_simulation=False, limite_traitement=None):
    """
    Classe les fichiers par type dans des sous-dossiers.
    
    Args:
        dossier: Le dossier à organiser
        mode_simulation: Si True, montre les actions sans les exécuter
        limite_traitement: Nombre maximum de fichiers à traiter (None pour tous)
    """
    fichiers = [f for f in os.listdir(dossier) if os.path.isfile(os.path.join(dossier, f))]
    liste_actions = []
    
    # Appliquer la limite si spécifiée
    if limite_traitement and len(fichiers) > limite_traitement:
        logger.info(f"Limitation à {limite_traitement} fichiers sur {len(fichiers)} au total")
        fichiers = fichiers[:limite_traitement]
    
    fichiers_traites = 0
    for fichier in fichiers:
        chemin_complet = os.path.join(dossier, fichier)

        if os.path.isfile(chemin_complet):
            _, extension = os.path.splitext(fichier)
            extension = extension.lower()

            destination = extension.lstrip('.').capitalize()  # Enlever le point et mettre en majuscule
            for type_, extensions in DEFAULT_TYPES_FICHIERS.items():
                if extension in extensions:
                    destination = type_
                    break

            dossier_destination = os.path.join(dossier, destination)
            
            if not mode_simulation:
                creer_dossier_si_absent(dossier_destination)
            
            nouveau_chemin = os.path.join(dossier_destination, fichier)
            nouveau_chemin = verifier_conflit_fichier(nouveau_chemin)
            
            if mode_simulation:
                logger.info(f"[SIMULATION] Déplacement: {fichier} → {destination}/{os.path.basename(nouveau_chemin)}")
            else:
                try:
                    from datetime import datetime

                    date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                   
                    
                    
                    shutil.move(chemin_complet, nouveau_chemin)
                   

                    
                    fichiers_traites += 1
               
                    logger.info(f"Déplacé: {fichier} → {destination}/{os.path.basename(nouveau_chemin)}")
                   
                    
                except FileNotFoundError:
                    logger.error(f"Fichier introuvable lors du déplacement: {fichier}")
                except Exception as e:
                    logger.error(f"Erreur lors du déplacement de {fichier}: {e}")
                    # Attendre et réessayer une fois
                    try:
                        time.sleep(1)  # Attendre 1 seconde
                        shutil.move(chemin_complet, nouveau_chemin)
                        logger.info(f"Déplacé après reprise: {fichier} → {destination}/{os.path.basename(nouveau_chemin)}")
                        fichiers_traites += 1
                    except Exception as e2:
                        logger.error(f"Échec définitif pour {fichier}: {e2}")
                   
    
    return fichiers_traites