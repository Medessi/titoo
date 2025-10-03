import os
import time
import json
from datetime import datetime, timedelta
from .organizer_type import classer_fichier_par_type
from .organizer_date import classer_par_date
from .organizer_name import classer_fichier_par_nom
from logs.logger import logger

def charger_preferences(path="preferences.json"):
    if not os.path.exists(path):
        raise FileNotFoundError("Fichier de préférences introuvable.")
    with open(path, "r") as f:
        return json.load(f)["dossiers"]

def doit_organiser(derniere_exec, frequence):
    maintenant = datetime.now()
    if frequence == "journalier":
        return maintenant.date() > derniere_exec.date()
    elif frequence == "hebdomadaire":
        return maintenant - derniere_exec >= timedelta(weeks=1)
    elif frequence == "mensuel":
        return maintenant.month != derniere_exec.month or maintenant.year != derniere_exec.year
    return False

def lancer_watch():
    try:
        prefs = charger_preferences()

        # Initialise l'état d'exécution pour chaque dossier
        etat_exec = {p["chemin"]: datetime.now() - timedelta(days=1) for p in prefs}

        print("🛡️ Surveillance multi-dossiers activée.\n")

        while True:
            for config in prefs:
                chemin = config["chemin"]
                frequence = config["frequence"]
                mode = config["mode"]
                derniere_exec = etat_exec.get(chemin, datetime.min)

                if not os.path.isdir(chemin):
                    print(f"⚠️ Dossier non valide : {chemin}")
                    continue

                if doit_organiser(derniere_exec, frequence):
                    print(f"[{datetime.now()}] 📁 Organisation de '{chemin}' par {mode}...")

                    if mode == "type":
                        classer_fichier_par_type(chemin)
                    elif mode == "date":
                        classer_par_date(chemin)
                    elif mode == "nom":
                        classer_fichier_par_nom(chemin)

                    etat_exec[chemin] = datetime.now()
                    print(f"[{datetime.now()}] ✅ Organisation de '{chemin}' terminée.\n")

            time.sleep(60)

    except Exception as e:
        print(f"❌ Erreur dans le watcher : {e}")
