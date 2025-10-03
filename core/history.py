# -*- coding: utf-8 -*-
# Ce fichier gère l'historique des actions effectuées par l'utilisateur, y compris la sauvegarde, le chargement et l'affichage de l'historique.
# Il utilise un fichier JSON pour stocker les données et un fichier de log pour enregistrer les erreurs et les actions.
# Il inclut également des fonctionnalités pour nettoyer l'historique en fonction d'une période de rétention définie et pour exporter l'historique dans différents formats.

# Importation des bibliothèques nécessaires


import os
import json



from datetime import datetime, timedelta
from tabulate import tabulate

# Importation des modules personnalisés
from logs.logger import logger


# Configuration avec chemins relatifs par rapport à la racine de l'application
HISTORY_FILE = r"json/history_organisations.json"
ANNULATION_TEMP_FILE = r"json/annulation_temp.jsonl"
RETENTION_DAYS = 30

ORGANISATION_HISTORY_FILE = "json/history_organisations.json"
os.makedirs(os.path.dirname(ORGANISATION_HISTORY_FILE), exist_ok=True)
os.makedirs(os.path.dirname(ANNULATION_TEMP_FILE), exist_ok=True)
# Créer les répertoires pour les logs et l'historique s'ils n'existent pas
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)




def charger_historique():
    """
    Charge l'historique depuis le fichier JSON ou GZIP si disponible.
    """
    if not os.path.exists(HISTORY_FILE):
        logger.warning("Fichier d'historique introuvable.")
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de décodage JSON : {e}")
        return []

def sauvegarder_historique(historique):
    """
    Sauvegarde l'historique dans un fichier JSON.
    """
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(historique, f, indent=4, ensure_ascii=False)
        logger.info("Historique sauvegardé avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'historique : {e}")

def enregistrer_action(date: str, action: str, chemin_source: str, chemin_destination: str = None):
    """
    Ajoute une action à l'historique avec validation des entrées.
    """
    if not isinstance(action, str) or not action:
        raise ValueError("L'action doit être une chaîne non vide.")
    if not os.path.exists(chemin_source):
        raise ValueError(f"Le chemin source n'existe pas : {chemin_source}")

    historique = charger_historique()
    nouvelle_entree = {
        "date" :  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
       
        "action": action,
        "source": chemin_source,
        "destination": chemin_destination or "N/A"
    }
    historique.append(nouvelle_entree)
    sauvegarder_historique(historique)
    logger.info(f"Action enregistrée : {action}, source : {chemin_source}, destination : {chemin_destination}")

def afficher_historique():
    """
    Affiche l'historique en format tabulaire.
    """
    historique = charger_historique()
    if not historique:
        print("📂 Aucun historique disponible.")
        return

    table = [[entry["date"], entry["action"], entry["source"], entry.get("destination", "N/A")] for entry in historique]
    print("\n===== 📊 HISTORIQUE =====")
    print(tabulate(table, headers=["Date", "Action", "Source", "Destination"]))

def nettoyer_historique():
    """
    Supprime les entrées de l'historique vieilles de plus de RETENTION_DAYS jours.
    """
    historique = charger_historique()
    maintenant = datetime.now()
    filtré = [
        h for h in historique
        if datetime.fromisoformat(h["date"]) > maintenant - timedelta(days=RETENTION_DAYS)
    ]
    sauvegarder_historique(filtré)
    logger.info(f"Historique nettoyé. Entrées restantes : {len(filtré)}")

def exporter_historique(format="csv"):
    """
    Exporte l'historique dans le format spécifié (CSV ou JSON).
    """
    historique = charger_historique()
    if not historique:
        logger.warning("Aucun historique à exporter.")
        return

    if format == "csv":
        try:
            with open("history.csv", "w", encoding="utf-8") as f:
                f.write("Date,Action,Source,Destination\n")
                for entry in historique:
                    f.write(f'{entry["date"]},{entry["action"]},{entry["source"]},{entry.get("destination", "N/A")}\n')
            logger.info("Historique exporté au format CSV.")
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation au format CSV : {e}")
    elif format == "json":
        try:
            with open("history_export.json", "w", encoding="utf-8") as f:
                json.dump(historique, f, indent=4)
            logger.info("Historique exporté au format JSON.")
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation au format JSON : {e}")
    else:
        logger.warning(f"Format d'exportation non pris en charge : {format}")

def enregistrer_organisation(liste_actions):
    """
    Enregistre une organisation complète (liste d’actions) dans un fichier dédié.
    """
    if not liste_actions:
        logger.warning("Tentative d’enregistrement d’une organisation vide.")
        return

    try:
        with open(ORGANISATION_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(liste_actions) + "\n")
        logger.info(f"Organisation enregistrée avec {len(liste_actions)} actions.")
    except Exception as e:
        logger.error(f"Erreur lors de l’enregistrement de l’organisation : {e}")


def annuler_derniere_organisation():
    """
    Annule toutes les organisations enregistrées en restaurant les fichiers déplacés.
    """
    try:
        if not os.path.exists(ORGANISATION_HISTORY_FILE):
            print("❌ Aucun historique d'organisation trouvé.")
            return

        with open(ORGANISATION_HISTORY_FILE, "r", encoding="utf-8") as f:
            lignes = f.readlines()

        if not lignes:
            print("❌ Aucune organisation à annuler.")
            return

        print(f"🔁 Annulation de {len(lignes)} organisation(s)...")

        for index, ligne in enumerate(reversed(lignes), 1):
            try:
                organisation = json.loads(ligne)
                for action in reversed(organisation):  # Annuler dans l’ordre inverse
                    if action["type"] == "Déplacement":
                        if os.path.exists(action["destination"]):
                            os.makedirs(os.path.dirname(action["source"]), exist_ok=True)
                            os.rename(action["destination"], action["source"])
                            print(f"✅ Annulé : {action['destination']} ➜ {action['source']}")
                            # Supprimer les dossiers vides après l'annulation
                            if not os.listdir(os.path.dirname(action["destination"])):
                                os.rmdir(os.path.dirname(action["destination"]))
                        else:
                            print(f"⚠️ Fichier introuvable pour annulation : {action['destination']}")
            except json.JSONDecodeError:
                print(f"❌ Ligne {index} invalide dans l’historique, sautée.")

        # Vider totalement le fichier d’historique
        # Sauvegarder les actions annulées dans le fichier temporaire
        with open(ANNULATION_TEMP_FILE, "a", encoding="utf-8") as f:
            f.writelines(lignes)

        with open(ORGANISATION_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("")

        logger.info("Toutes les organisations ont été annulées avec succès.")
        print("✅ Toutes les organisations ont été annulées.")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation des organisations : {e}")
        print(f"❌ Erreur : {e}")


def retablir_derniere_organisation():
    """
    Rétablit la dernière organisation annulée (restaure les fichiers déplacés).
    """
    try:
        if not os.path.exists(ANNULATION_TEMP_FILE):
            print("❌ Aucune organisation annulée à rétablir.")
            return

        with open(ANNULATION_TEMP_FILE, "r", encoding="utf-8") as f:
            lignes = f.readlines()

        if not lignes:
            print("❌ Rien à rétablir.")
            return

        # On restaure la dernière organisation annulée
        derniere_annulation = json.loads(lignes)
        for action in derniere_annulation:
            if action["type"] == "Déplacement":
                if os.path.exists(action["source"]):
                    os.makedirs(os.path.dirname(action["destination"]), exist_ok=True)
                    os.rename(action["source"], action["destination"])
                    print(f"✅ Rétabli : {action['source']} ➜ {action['destination']}")
                else:
                    print(f"⚠️ Fichier introuvable pour rétablir : {action['source']}")

        # Réenregistrer dans l'historique principal
        with open(ORGANISATION_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(derniere_annulation, ensure_ascii=False) + "\n")

        # Supprimer cette entrée du fichier temporaire
        with open(ANNULATION_TEMP_FILE, "w", encoding="utf-8") as f:
            f.writelines(lignes[:-1])

        logger.info("Organisation rétablie avec succès.")
        print("✅ Organisation rétablie avec succès.")

    except Exception as e:
        logger.error(f"Erreur lors du rétablissement : {e}")
        print(f"❌ Erreur : {e}")