# -*- coding: utf-8 -*-
"""
Configuration - TITO (Gestionnaire de fichiers intelligent)
Ce fichier contient des configurations et des constantes utilisées dans l'application.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

# ----------- CONFIGURATIONS GÉNÉRALES -----------

APP_VERSION = "1.0.0"
APP_NAME = "TITO"
APP_DESCRIPTION = "Gestionnaire de fichiers"

# Répertoires de base
USER_HOME = os.path.expanduser("~")
APP_DIR = os.path.join(USER_HOME, ".tito")
CONFIG_FILE = os.path.join(APP_DIR, "settings.json")
LOG_FILE = os.path.join(APP_DIR, "tito.log")

# Création des répertoires nécessaires
os.makedirs(APP_DIR, exist_ok=True)

# ----------- CONFIGURATION DES TYPES DE FICHIERS -----------

DEFAULT_TYPES_FICHIERS = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".md"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".webp"],
    "Vidéos": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
    "Musique": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z", ".iso"],
    "Exécutables": [".exe", ".msi", ".bat", ".sh", ".apk", ".appx", ".app", ".deb", ".rpm"],
    "Feuilles de calcul": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
    "Présentations": [".ppt", ".pptx", ".odp", ".key"],
    "Code": [".py", ".java", ".c", ".cpp", ".js", ".html", ".css", ".php", ".rb", ".go", ".ts"],
    "Base de données": [".db", ".sqlite", ".mdb", ".accdb", ".sql"],
    "Ebooks": [".epub", ".mobi", ".azw", ".fb2"],
    "Design": [".psd", ".ai", ".xd", ".sketch", ".figma", ".xcf"],
    "Polices": [".ttf", ".otf", ".woff", ".woff2"],
    "Téléchargements": [],
    "Autres": []
}

# ----------- CONFIGURATION DES PARAMÈTRES DYNAMIQUES -----------

DEFAULT_RETENTION_DAYS = 30

# Configuration par défaut unifiée
default_settings = {
    "watched_folders": [os.path.join(USER_HOME, "Bureau")],  # Liste de dossiers
    "organized_folder": os.path.join(USER_HOME, "Bureau", "Organisé"),
    "auto_watch": True,
    "organization_mode": "type",  # 'type', 'date', 'nom'
    "undo_batch_mode": True,  # Annulation par groupe ou individuelle
    "history_retention_days": DEFAULT_RETENTION_DAYS
}

def load_settings():
    """Charge les paramètres depuis le fichier JSON avec migration automatique."""
    
    # Charger le fichier si possible
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    # Migration de l'ancienne structure vers la nouvelle
    needs_save = False
    
    # Migration: watched_folder -> watched_folders
    if "watched_folder" in settings and "watched_folders" not in settings:
        settings["watched_folders"] = [settings["watched_folder"]]
        settings.pop("watched_folder")  # Supprimer l'ancienne clé
        needs_save = True
    
    # Migration: retention_days -> history_retention_days
    if "retention_days" in settings and "history_retention_days" not in settings:
        settings["history_retention_days"] = settings["retention_days"]
        settings.pop("retention_days")  # Supprimer l'ancienne clé
        needs_save = True

    # Compléter avec les valeurs par défaut manquantes
    for key, value in default_settings.items():
        if key not in settings:
            settings[key] = value
            needs_save = True

    # Validation des données
    # S'assurer que watched_folders est une liste
    if not isinstance(settings.get("watched_folders"), list):
        settings["watched_folders"] = [settings.get("watched_folders", default_settings["watched_folders"][0])]
        needs_save = True
    
    # S'assurer qu'il y a au moins un dossier surveillé
    if not settings["watched_folders"]:
        settings["watched_folders"] = default_settings["watched_folders"]
        needs_save = True

    # Sauvegarder si des modifications ont été apportées
    if needs_save:
        save_settings(settings)

    return settings

def save_settings(settings):
    """Sauvegarde les paramètres utilisateur dans le fichier JSON."""
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur de sauvegarde de la configuration : {e}")
        raise

def update_setting(key, value):
    """Met à jour un paramètre et le sauvegarde."""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)

def reset_settings():
    """Réinitialise les paramètres utilisateur aux valeurs par défaut."""
    try:
        save_settings(default_settings.copy())
        print("Paramètres réinitialisés avec succès.")
    except Exception as e:
        print(f"Erreur lors de la réinitialisation : {e}")
        raise

def get_setting(key, default_value=None):
    """Récupère une valeur de configuration spécifique."""
    settings = load_settings()
    return settings.get(key, default_value)

def validate_settings():
    """Valide la configuration actuelle et retourne les erreurs éventuelles."""
    settings = load_settings()
    errors = []
    
    # Vérifier les dossiers surveillés
    watched_folders = settings.get("watched_folders", [])
    if not watched_folders:
        errors.append("Aucun dossier surveillé configuré")
    else:
        for folder in watched_folders:
            if not os.path.exists(folder):
                errors.append(f"Dossier surveillé inexistant : {folder}")
    
    # Vérifier le dossier organisé
    organized_folder = settings.get("organized_folder")
    if organized_folder and not os.path.exists(os.path.dirname(organized_folder)):
        errors.append(f"Répertoire parent du dossier organisé inexistant : {organized_folder}")
    
    # Vérifier les valeurs numériques
    retention_days = settings.get("history_retention_days", 0)
    if not isinstance(retention_days, int) or retention_days < 1:
        errors.append("Durée de rétention invalide")
    
    return errors

def setup_logging():
    """Configure le système de logging."""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )
    
    # Ajouter aussi un handler pour la console en mode debug
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

# Initialiser le logging au chargement du module
setup_logging()

