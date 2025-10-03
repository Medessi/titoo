import sys
import os
from datetime import datetime
import shutil

from core.organizer_utils import (renommer_fichiers, 
                      supprimer_doublons)
from core.organizer_type import classer_fichier_par_type
from core.organizer_date import classer_par_date


from logs.logger import logger
import time

import os
import time
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap, QImage
import json
import mimetypes


class WatcherThread(QThread):
    """Thread pour la surveillance des dossiers"""
    status_update = pyqtSignal(str)
    file_changed = pyqtSignal(str)

    def __init__(self, directory, delay=30):
        super().__init__()
        self.directory = directory
        self.running = True
        self.delay = delay  # Délai en secondes (peut ne pas être directement utilisé ici)
        self.observer = None
        self.event_handler = None

    def run(self):
        from core.watcher import FolderHandler, Observer, logger  # Importez ici pour éviter les problèmes de dépendances cycliques potentiels

        if not os.path.exists(self.directory):
            self.status_update.emit(f"❌ Le dossier {self.directory} n'existe pas.")
            return

        self.event_handler = FolderHandler(self.directory, self.delay) # Utilisez le délai du WatcherThread
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.directory, recursive=False)

        self.status_update.emit(f"👁️ Surveillance activée sur le dossier: {self.directory}")
        self.observer.start()

        try:
            while self.running:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Erreur dans le thread de surveillance: {e}")
            self.status_update.emit(f"⚠️ Erreur de surveillance: {str(e)}")
        finally:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
                self.status_update.emit("🛑 Surveillance arrêtée.")

    def stop(self):
        self.running = False
        self.wait()
class LoadFilesWorker(QThread):
    file_found = pyqtSignal(tuple)
    files_loaded = pyqtSignal(list)  # ✅ Nouveau signal pour envoyer tous les fichiers
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        all_files = []  # ✅ Liste pour stocker toutes les infos
        try:
            for file_name in os.listdir(self.directory):
                file_path = os.path.join(self.directory, file_name)
                if os.path.isfile(file_path):
                    try:
                        file_info = os.stat(file_path)
                        file_hash = "N/A"  # Placeholder, à remplacer si calcul de hash

                        _, extension = os.path.splitext(file_name)
                        extension = extension.lower()

                        file_type = "Autres"
                        for type_name, extensions in {
                            "Documents": [".pdf", ".doc", ".docx", ".txt", ".odt"],
                            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                            "Vidéos": [".mp4", ".avi", ".mov", ".mkv"],
                            "Musique": [".mp3", ".wav", ".aac", ".flac"],
                            "Archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
                            "Exécutables": [".exe", ".msi", ".bat", ".sh", ".apk"],
                            "Feuilles de calcul": [".xls", ".xlsx", ".csv", ".ods"],
                            "Présentations": [".ppt", ".pptx", ".odp"],
                            "Code": [".py", ".java", ".c", ".cpp", ".js", ".html", ".css"],
                        }.items():
                            if extension in extensions:
                                file_type = type_name
                                break

                        size_kb = file_info.st_size / 1024
                        if size_kb < 1024:
                            size_str = f"{size_kb:.2f} KB"
                        else:
                            size_mb = size_kb / 1024
                            size_str = f"{size_mb:.2f} MB" if size_mb < 1024 else f"{size_mb / 1024:.2f} GB"

                        mod_date = datetime.fromtimestamp(file_info.st_mtime).strftime("%d/%m/%Y %H:%M")

                        file_data = (file_name, file_type, size_str, mod_date, file_hash, size_kb)
                        self.file_found.emit(file_data)    # Emission individuelle
                        all_files.append(file_data)        # Stockage pour le signal groupé
                    except Exception as e:
                        print(f"Erreur pour {file_name}: {e}")

            self.files_loaded.emit(all_files)  # ✅ Emission groupée pour populate_file_table
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def get_file_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return ext[1:].upper() if ext else "Fichier"


class ThumbnailGenerator(QThread):
    thumbnail_ready = pyqtSignal(str, QPixmap)
    
    def __init__(self, file_path, thumb_size=128):
        super().__init__()
        self.file_path = file_path
        self.thumb_size = thumb_size
    
    def run(self):
        try:
            # Créer la miniature
            pixmap = self.create_thumbnail()
            if pixmap and not pixmap.isNull():
                self.thumbnail_ready.emit(self.file_path, pixmap)
        except Exception as e:
            print(f"Erreur lors de la génération de la miniature pour {self.file_path}: {str(e)}")
    
    def create_thumbnail(self):
        """Crée une miniature pour le fichier spécifié"""
        mime_type = mimetypes.guess_type(self.file_path)[0]
        
        if mime_type and mime_type.startswith('image/'):
            # Créer une miniature d'image
            img = QImage(self.file_path)
            if not img.isNull():
                return QPixmap.fromImage(img.scaled(
                    QSize(self.thumb_size, self.thumb_size),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
        
        elif mime_type and mime_type.startswith('video/'):
           
            video_icon = QPixmap(self.thumb_size, self.thumb_size)
            video_icon.fill(Qt.GlobalColor.darkBlue)  # Remplir avec une couleur
            return video_icon
        
        return None
    

