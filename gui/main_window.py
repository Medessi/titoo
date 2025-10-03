import os
import sys


import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QTreeWidget, QLabel, QLineEdit, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                            QFileDialog, QInputDialog, QMessageBox, QSplitter, QFrame,
                            QCheckBox, QProgressBar, QToolButton, QMenu, QSpinBox, 
                            QGroupBox, QDialog, QFileIconProvider, QListView, QDateEdit, QDialogButtonBox, QTextEdit, QFormLayout)
from PyQt6.QtCore import Qt, QSize, QTimer, QUrl, QFileInfo, QDate
import mimetypes
import subprocess
import csv
import json
import traceback
from datetime import datetime
from PyQt6.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem, QDoubleValidator, QAction, QPixmap, QFont, QColor
from PyQt6.QtWidgets import  QProgressDialog
# Importation des modules d'organisation
from core.organizer_utils import supprimer_doublons

# Import ThumbnailGenerator for thumbnail creation

from core.rename import renommer_fichiers
                      
from core.organizer_date import classer_par_date
from core.organizer_type import classer_fichier_par_type
from core.organizer_name import organiser_par_nom


from logs.logger import logger
import time

from .threads import LoadFilesWorker

from core.undo_redo import undo, redo


from core.watcher import lancer_watch


from .settings_gui import SettingsDialog
from core.history import annuler_derniere_organisation,retablir_derniere_organisation
from .dialog_code import show_info_dialog
class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialisation de la fenêtre principale
        self.setWindowTitle("TITO - Gestionnaire de fichiers")
        self.setWindowIcon(QIcon("assets/logo/logo.svg"))

         
        self.setMinimumSize(1000, 650)

            # Palette de couleurs modernisée
        self.primary_color = "#191970"    # Bleu nuit élégant
        self.secondary_color = "#2980B9"   # Bleu vif et dynamique
        self.accent_color = "#FFD700"      # Orange profond pour attirer l’attention
        self.light_bg = "#F8F9FA"          # Gris très clair pour un fond moderne
        self.dark_text = "#333333"         # Noir doux pour une lisibilité optimale
        self.light_text = "#FFFFFF"        # Blanc pur pour les éléments contrastés
        self.hover_color = "#2C3E50"       # Bleu foncé plus subtil au survol
        self.border_radius = "8px"         # Légèrement arrondi pour un aspect plus fluide
          # Rayon des bords arrondi
     
        # Configuration des polices
        font_family = "Segoe UI, Roboto, 'Helvetica Neue', Arial, sans-serif"
        self.setStyleSheet(f"""
            QWidget {{
                font-family: {font_family};
                font-size: 12px;
                color: {self.dark_text};             /* ← Couleur du texte par défaut */
                background-color: {self.light_bg};   /* ← Fond clair par défaut */
            }}
        """)
        
        # Variables pour stocker le chemin courant et les fichiers sélectionnés
        self.current_directory = os.path.expanduser("~")
        self.selected_files = []
        
        # Initialisation du thread de surveillance
        self.watcher_thread = None
        self.is_watching = False
        self.watcher_settings = {
            'delay': 30,
            'auto_organize_by_type': True,
            'auto_remove_duplicates': False,
            'recursive': True
        }
        self.current_view_mode = "Icônes"  # Mode d'affichage par défaut
        self.file_data = []  # Stockage des données de fichiers pour les différentes vues
        self.icon_provider = QFileIconProvider()  # Pour obtenir les icônes des fichiers
        self.icon_provider = QFileIconProvider()  # Pour obtenir les icônes des fichiers
        self.thumbs_cache = {}  # Cache pour les miniatures
        self.thumbnail_workers = []  # Liste pour suivre les threads de génération de miniatures
        
        # Initialiser la bibliothèque mimetypes
        mimetypes.init()
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Charger les fichiers initiaux
        self.directory_label.setText(f"Dossier: {self.current_directory}")
        self.load_files(self.current_directory)
        self.file_table.itemDoubleClicked.connect(self.open_file)
          # Connexion du double-clic à la fonction
        
    
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        
        # Barre de titre avec style moderne
        self.title_bar = QWidget()
        self.title_bar.setStyleSheet(f"""
            background-color: {self.primary_color};
            color: {self.light_text};
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        """)
        self.title_bar.setFixedHeight(60)
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(15, 5, 15, 5)

        # Logo et titre avec style moderne
        title_container = QWidget()
        title_container_layout = QVBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        title_container_layout.setSpacing(2)

        title_label = QLabel("TITO")
        title_label.setPixmap(QIcon("assets/logo/logo.svg").pixmap(32, 32))  # Logo
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; letter-spacing: 1px;")
        title_container_layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Gestionnaire de fichiers intelligent")
        desc_label.setStyleSheet("font-size: 13px; font-weight: 300; opacity: 0.8;")
        title_container_layout.addWidget(desc_label)

        self.title_bar_layout.addWidget(title_container)

        # Ajout d'un espace extensible
        self.title_bar_layout.addStretch()

        # Barre d'outils à droite
        toolbar_container = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)

        # Style pour les boutons de la barre d'outils
        toolbar_button_style = f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: {self.light_text};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QToolButton {{
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: {self.light_text};
                font-size: 16px;
            }}
            QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QToolButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QToolButton::menu-indicator {{
                image: url(assets/icon/arrow_down.svg);
                subcontrol-origin: padding;
                subcontrol-position: right center;
                padding-right: 3px;
            }}
        """
        info_button = QPushButton()
        info_button.setIcon(QIcon("assets/icon/info.svg"))
        info_button.setStyleSheet(toolbar_button_style)
        info_button.setToolTip("Informations sur le logiciel")
        info_button.clicked.connect(show_info_dialog)
       
        
        # Remplacer le bouton d'annulation simple par un bouton avec menu déroulant
        undo_button = QToolButton()
        undo_button.setIcon(QIcon("assets/icon/undo.svg"))
        undo_button.setStyleSheet(toolbar_button_style)
        undo_button.setToolTip("Annuler")
        undo_button.clicked.connect(undo)
        
        # Créer le menu déroulant
        undo_menu = QMenu(undo_button)
        undo_last_organization_action = QAction("Annuler la dernière organisation", undo_menu)
        undo_last_organization_action.triggered.connect(annuler_derniere_organisation)
        undo_menu.addAction(undo_last_organization_action)
        
        # Configurer le bouton pour afficher le menu
        undo_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        undo_button.setMenu(undo_menu)
        
        
        undo_button.clicked.connect(undo)
        redo_button = QToolButton()
        redo_button.setIcon(QIcon("assets//icon//redo.svg"))
        redo_button.setToolTip("Rétablir")
        redo_button.clicked.connect(redo)
        redo_button.setStyleSheet(toolbar_button_style)
        redo_menu = QMenu(redo_button)
        redo_last_organization_action = QAction("Rétablir la dernière organisation", redo_menu)
        redo_last_organization_action.triggered.connect(retablir_derniere_organisation)
        redo_menu.addAction(redo_last_organization_action)
        
        # Configurer le bouton pour afficher le menu
        redo_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        redo_button.setMenu(redo_menu)
        
        toolbar_layout.addWidget(info_button)
        
        toolbar_layout.addWidget(undo_button)
        toolbar_layout.addWidget(redo_button)

        
        history_btn = QPushButton()
        history_btn.setStyleSheet(toolbar_button_style)
        history_btn.setIcon(QIcon("assets/icon/history_ico.svg"))
       
        history_btn.setToolTip("Afficher l'historique")  # Ajout d'un tooltip pour expliciter l'action
        history_btn.clicked.connect(self.afficher_historique)
  # Utilisation d'une icône moderne
     
        toolbar_layout.addWidget(history_btn)

        settings_button = QPushButton()
        settings_button.setIcon(QIcon("assets\\icon\\settings-hammer-svgrepo-com.svg"))
        settings_button.setStyleSheet(toolbar_button_style)
        settings_button.clicked.connect(self.ouvrir_parametres)
        stats_btn = QPushButton()
        stats_btn.setIcon(QIcon("assets/icon/statistics_icon.svg"))
        
        
        stats_btn.setToolTip("Afficher les statistiques")  # Ajout d'un tooltip pour expliciter l'action
        stats_btn.clicked.connect(self.show_statistics)
        donate_button = QPushButton()
        donate_button.setIcon(QIcon("assets\\icon\\donate.svg"))
        donate_button.setStyleSheet(toolbar_button_style + "font-weight: bold;")
        donate_button.setToolTip("Faire un don")
        donate_button.clicked.connect(self.open_donation_dialog)

        toolbar_layout.addWidget(settings_button)
        toolbar_layout.addWidget(stats_btn)
        toolbar_layout.addWidget(donate_button)

        self.title_bar_layout.addWidget(toolbar_container)
        main_layout.addWidget(self.title_bar)

        self.setCentralWidget(central_widget)
        button_style = f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {self.light_text};
                padding: 8px 15px;
                border-radius: {self.border_radius};
                border: none;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """
        btn_title_layout = f"""
            QPushButton {{
                background-color: {self.primary_color};
                color: {self.light_text};
                padding: 10px 15px;
                border-radius: {self.border_radius};
                font-weight: 500;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color};
            }}
            QPushButton:pressed {{
                background-color: #1e2b38;
            }}
        """
        history_btn = QPushButton()
        history_btn.setStyleSheet(btn_title_layout)
        history_btn.setIcon(QIcon("assets/icon/history_ico.svg"))
        history_btn.setToolTip("Afficher l'historique")  # Ajout d'un tooltip pour expliciter l'action
        history_btn.setIconSize(QSize(24, 24))  # Taille de l'icône
        history_btn.setFixedSize(40, 40)  # Taille du bouton
      

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
     
        navigation_widget = QWidget()
        navigation_widget.setMaximumWidth(280)
        navigation_widget.setStyleSheet(f"""
            background-color: {self.light_bg};
            border-right: 1px solid #dadce0;
        """)
        nav_layout = QVBoxLayout(navigation_widget)
        nav_layout.setContentsMargins(12, 15, 12, 15)
        nav_layout.setSpacing(10)
        
        # Bouton de sélection de dossier moderne
        self.select_button = QPushButton(QIcon("assets\\icon\\folder.svg"),"Choisir un dossier")
        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_color};
                color: {self.light_text};
                padding: 10px 15px;
                border-radius: {self.border_radius};
                font-weight: 500;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #000000;
                color: #ffd700
            }}
            QPushButton:pressed {{
                background-color: {self.primary_color};
            }}
        """)
        self.select_button.clicked.connect(self.select_directory)
        nav_layout.addWidget(self.select_button)
        
        # Label du dossier actuel avec style moderne
        self.directory_label = QLabel("Dossier: Aucun dossier sélectionné")
        self.directory_label.setWordWrap(True)
        self.directory_label.setStyleSheet(f"""
            padding: 8px 10px;
            font-size: 11px;
            color: {self.dark_text};
            background-color: rgba(0, 0, 0, 0.03);
            border-radius: {self.border_radius};
        """)
        nav_layout.addWidget(self.directory_label)
        
        # Séparateur élégant
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #dadce0; max-height: 1px;")
        nav_layout.addWidget(separator)
        
        # Options d'organisation avec des cases à cocher modernes
        organize_group = QGroupBox("Options d'organisation")
        organize_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 13px;
                padding-top: 15px;
                border: 1px solid #dadce0;
                border-radius: {self.border_radius};
                margin-top: 5px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px;
            }}
        """)
        organize_layout = QVBoxLayout(organize_group)
        organize_layout.setContentsMargins(15, 15, 15, 15)
        organize_layout.setSpacing(8)
        
        # Style moderne pour les checkboxes
        checkbox_style = f"""
            QCheckBox {{
                spacing: 8px;
                color: {self.dark_text};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #b8b8b8;
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.primary_color};
                border: 1px solid { self.accent_color};
                image: url(check.png);
            }}
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid { self.accent_color};
            }}
        """
        
        # Cases à cocher pour les options d'organisation
        self.organize_by_type = QCheckBox("Organiser par type")
        self.organize_by_type.setToolTip("Classer les fichiers par type (images, vidéos, etc.)")
        self.organize_by_type.setStyleSheet(checkbox_style)
        organize_layout.addWidget(self.organize_by_type)
        
        self.organize_by_date = QCheckBox("Organiser par date")
        self.organize_by_date.setToolTip("Classer les fichiers par date de création ou de modification")
        self.organize_by_date.setStyleSheet(checkbox_style)
        organize_layout.addWidget(self.organize_by_date)
        
        self.organize_by_name = QCheckBox("Organiser par nom")
        self.organize_by_name.setToolTip("Classer les fichiers par nom")
        self.organize_by_name.setStyleSheet(checkbox_style)
        organize_layout.addWidget(self.organize_by_name)
        
        self.rename_files = QCheckBox("Renommer les fichiers")
        self.rename_files.setToolTip("Renommer les fichiers selon un format cohérent")
        self.rename_files.setStyleSheet(checkbox_style)
        organize_layout.addWidget(self.rename_files)
        
        self.remove_duplicates = QCheckBox("Supprimer les doublons")
        self.remove_duplicates.setToolTip("Supprimer les fichiers en double")
        self.remove_duplicates.setStyleSheet(checkbox_style)
        organize_layout.addWidget(self.remove_duplicates)
        
        
        
        # Bouton d'organisation moderne
        self.organize_btn = QPushButton("TITO-Organiser")
        self.organize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: #191970;
                padding: 10px 15px;
                border-radius: {self.border_radius};
                font-weight: 500;
                border: none;
                margin-top: 8px;
            }}
            QPushButton:hover {{
                background-color: #000000;
                color: #ffd700;
            }}
            QPushButton:pressed {{
                background-color: #191970;
                color: #ffd700
            }}
        """)
        self.organize_btn.setToolTip("Organiser les fichiers selon les options sélectionnées")
        self.organize_btn.clicked.connect(self.organize_files)
        organize_layout.addWidget(self.organize_btn)
        
        nav_layout.addWidget(organize_group)
        
        # Section de surveillance élégante
        watch_group = QGroupBox("Surveillance automatique")
        watch_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 13px;
                padding-top: 15px;
                border: 1px solid #dadce0;
                border-radius: {self.border_radius};
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px;
            }}
        """)
        watch_layout = QVBoxLayout(watch_group)
        watch_layout.setContentsMargins(15, 15, 15, 15)
        watch_layout.setSpacing(8)
        
        # Bouton de démarrage/arrêt de surveillance moderne
        self.watch_btn = QPushButton(QIcon("assets\\icon\\eye-closed.svg"),"Surveiller le dossier")
        self.watch_btn.setToolTip("Démarrer/Arrêter la surveillance du dossier")
        self.watch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #27ae60;
                color: {self.light_text};
                padding: 10px 15px;
                border-radius: {self.border_radius};
                font-weight: 500;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #219955;
            }}
            QPushButton:pressed {{
                background-color: #1e874b;
            }}
        """)
        self.watch_btn.clicked.connect(lancer_watch)
        watch_layout.addWidget(self.watch_btn)
        
        # Bouton de configuration de surveillance avec style moderne
        self.config_watch_btn = QPushButton("⚙️  Configurer la surveillance")
        self.config_watch_btn.setToolTip("Configurer les options de surveillance")
        self.config_watch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.light_bg};
                color: {self.dark_text};
                padding: 10px 15px;
                border-radius: {self.border_radius};
                font-weight: 500;
                border: 1px solid #dadce0;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
            }}
            QPushButton:pressed {{
                background-color: #d0d0d0;
            }}
        """)

        watch_layout.addWidget(self.config_watch_btn)
        
        # Ajouter une étiquette d'état de surveillance élégante
        self.watch_status_label = QLabel("État: Inactif")
        self.watch_status_label.setStyleSheet(f"""
            font-style: italic;
            font-size: 11px;
            color: {self.dark_text};
            padding: 5px;
            background-color: rgba(0, 0, 0, 0.03);
            border-radius: 3px;
        """)
        watch_layout.addWidget(self.watch_status_label)
        
        nav_layout.addWidget(watch_group)
        
      
        # Option de statistiques moderne
        # Avec couleur et taille personnalisées
        
        #title_bar_layout.addWidget(stats_btn)

       
        # Ajout du widget de navigation au splitter
        splitter.addWidget(navigation_widget)
        
        # Zone principale à droite avec style moderne
        main_area = QWidget()
        main_area.setStyleSheet(f"background-color: #ffffff;")
        main_area_layout = QVBoxLayout(main_area)
        main_area_layout.setContentsMargins(20, 20, 20, 20)
        main_area_layout.setSpacing(15)
        
        # Barre de recherche et filtres modernes
        search_filter_widget = QWidget()
        search_filter_layout = QHBoxLayout(search_filter_widget)
        search_filter_layout.setContentsMargins(0, 0, 0, 0)
        search_filter_layout.setSpacing(10)
        
        # Zone de recherche élégante
        search_container = QWidget()
        search_container.setStyleSheet(f"""
            background-color: {self.light_bg};
            border-radius: {self.border_radius};
            padding: 0;
        """)
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(10, 2, 10, 2)
        
       
        search_label = QLabel()  # Crée un widget QLabel pour afficher l'icône
        search_label.setPixmap(QIcon("assets/icon/search.svg").pixmap(24, 24))  # Convertit QIcon en image affichable
        search_container_layout.addWidget(search_label)

        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher des fichiers...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                padding: 8px;
                background: transparent;
                font-size: 13px;
            }}
        """)
        self.search_input.textChanged.connect(self.search_files)
        search_container_layout.addWidget(self.search_input)
        
        search_filter_layout.addWidget(search_container, 1)  # Stretch factor 1
        
        # Filtres rapides modernes
        filter_label = QLabel("Filtrer par:")
        filter_label.setStyleSheet(f"color: {self.dark_text}; font-weight: 500;")
        search_filter_layout.addWidget(filter_label)
        
        # Filtre par type élégant
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tous")
        for type_name in ["Images", "Documents", "Vidéos", "Audios", "Archives", "Autres","Présentations", "Feuilles de calcul", "Exécutables", "Code"]:
            self.type_filter.addItem(type_name)
        self.type_filter.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid #dadce0;
                border-radius: {self.border_radius};
                padding: 8px 15px;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border: 1px solid #b8b8b8;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }}
        """)
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        search_filter_layout.addWidget(self.type_filter)
        
        # Bouton de réinitialisation des filtres élégant
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.secondary_color};
                padding: 8px 15px;
                border: 1px solid {self.secondary_color};
                border-radius: {self.border_radius};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(52, 152, 219, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(52, 152, 219, 0.2);
            }}
        """)
        reset_btn.clicked.connect(self.reset_filters)
        search_filter_layout.addWidget(reset_btn)
        
        main_area_layout.addWidget(search_filter_widget)
        
        # Barre d'outils pour les actions sur les fichiers
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(f"""
            background-color: {self.light_bg};
            border-radius: {self.border_radius};
            padding: 5px;
        """)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(8)
        
        # Style pour les boutons d'action
        action_button_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {self.dark_text};
                padding: 8px 15px;
                border: none;
                border-radius: {self.border_radius};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.05);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """
        
        # Importer QtAwesome
        

        open_btn = QPushButton(QIcon('assets\\icon\\file.svg'), " Ouvrir")
        open_btn.setStyleSheet(action_button_style)
        from PyQt6.QtCore import QDir

        file_path = QDir.toNativeSeparators(self.current_directory)
        # Utiliser QUrl pour ouvrir le fichier
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(file_path)))


        toolbar_layout.addWidget(open_btn)

        rename_btn = QPushButton(QIcon("assets/icon/pencil.svg"), " Renommer")
        rename_btn.setStyleSheet(action_button_style)
        rename_btn.clicked.connect(self.rename_file)
        toolbar_layout.addWidget(rename_btn)

        delete_btn = QPushButton(QIcon("assets/icon/trash.svg"), " Supprimer")
        delete_btn.setStyleSheet(action_button_style)
        delete_btn.clicked.connect(self.delete_file)
        toolbar_layout.addWidget(delete_btn)
   
        
        # Mode d'affichage élégant
        view_label = QLabel("Affichage:")
        view_label.setStyleSheet(f"color: {self.dark_text}; font-weight: 500;")
        toolbar_layout.addWidget(view_label)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Détails", "Icônes", "Liste"])
        self.view_combo.setCurrentIndex(0)
        self.view_combo.currentTextChanged.connect(self.change_view_mode)
        toolbar_layout.addWidget(self.view_combo)
        self.view_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid #dadce0;
                border-radius: {self.border_radius};
                padding: 8px 15px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border: 1px solid #b8b8b8;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }}
        """)
        toolbar_layout.addWidget(self.view_combo)
        
        main_area_layout.addWidget(toolbar_widget)
        
        # Tableau des fichiers moderne
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(["Nom", "Type", "Taille", "Date de modification", "Hash"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        self.file_table.setStyleSheet(f"""
    QTableWidget {{
        border: 1px solid #dadce0;
        border-radius: {self.border_radius};
        gridline-color: transparent;
        selection-background-color: rgba(52, 152, 219, 0.25);
        selection-color: {self.dark_text};
        background-color: {self.light_bg};
        alternate-background-color: rgba(245, 245, 245, 0.6);
        font-size: 14px;
    }}
    
    QTableWidget::item {{
        padding: 10px;
        border-bottom: 1px solid rgba(220, 220, 220, 0.4);
    }}
    
    QHeaderView::section {{
        background-color: {self.light_bg};
        color: #191970;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #dadce0;
        font-weight: bold;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    QTableWidget::item:selected {{
        background-color: rgba(52, 152, 219, 0.3);
        border-bottom: 1px solid rgba(52, 152, 219, 0.3);
    }}

    QTableWidget::item:hover {{
        background-color: rgba(52, 152, 219, 0.15);
        transition: 0.3s ease-in-out;
    }}
""")

        self.file_table.itemSelectionChanged.connect(self.update_selected_files)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        
        main_area_layout.addWidget(self.file_table)
        
        # Barre de progression moderne
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - Organisation en cours...")
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {self.border_radius};
                background-color: #f5f5f5;
                height: 20px;
                text-align: center;
                color: {self.dark_text};
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {self.secondary_color};
                border-radius: {self.border_radius};
            }}
        """)
        main_area_layout.addWidget(self.progress_bar)
        
        # Barre de statut moderne
        status_bar = QWidget()
        status_bar.setStyleSheet(f"""
            background-color: {self.light_bg};
            border-radius: {self.border_radius};
        """)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(15, 10, 15, 10)
        
        self.status_label = QLabel("0 éléments")
        self.status_label.setStyleSheet(f"color: {self.dark_text}; font-weight: 500;")
        status_layout.addWidget(self.status_label)
        
        # Ajouter un espace extensible
        status_layout.addStretch()
        self.icon_model = QStandardItemModel()
        self.list_model = QStandardItemModel()

        self.icon_view = QListView()
        self.icon_view.setViewMode(QListView.ViewMode.IconMode)
        self.icon_view.setIconSize(QSize(64, 64))
        self.icon_view.setGridSize(QSize(100, 100))
        self.icon_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.icon_view.setSpacing(10)
        self.icon_view.setModel(self.icon_model)
        self.icon_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.icon_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.icon_view.setWrapping(True)
        self.icon_view.hide()
        main_area_layout.addWidget(self.icon_view)


        self.list_view = QListView()
        self.list_view.setViewMode(QListView.ViewMode.ListMode)
        self.list_view.setIconSize(QSize(16, 16))
        self.list_view.setModel(self.list_model)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.list_view.hide()
        main_area_layout.addWidget(self.list_view)

        self.load_files()
        # Information sur l'espace disque avec style moderne
        self.space_label = QLabel("Espace libre: calcul en cours...")
        self.space_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.space_label.setStyleSheet(f"color: {self.dark_text}; font-weight: 500;")
        status_layout.addWidget(self.space_label)
        
        main_area_layout.addWidget(status_bar)
        
        # Ajout de la zone principale au splitter
        splitter.addWidget(main_area)
        
        # Configuration du splitter avec style moderne
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dadce0;
                width: 1px;
            }
        """)
        splitter.setStretchFactor(0, 1)  # Navigation à gauche
        splitter.setStretchFactor(1, 3)  # Zone principale à droite
        
        main_layout.addWidget(splitter)
        
        self.setCentralWidget(central_widget)
        
        # Mettre à jour l'information sur l'espace disque
        self.update_disk_space()
    def update_disk_space(self):
            """Met à jour l'information sur l'espace disque disponible"""
            try:
                if not self.current_directory:
                    return
                    
                disk_usage = shutil.disk_usage(self.current_directory)
                free_space = disk_usage.free
                total_space = disk_usage.total
                
                # Conversion en format lisible
                def format_size(size_bytes):
                    if size_bytes < 1024**2:  # Moins de 1 MB
                        return f"{size_bytes / 1024:.1f} KB"
                    elif size_bytes < 1024**3:  # Moins de 1 GB
                        return f"{size_bytes / (1024**2):.1f} MB"
                    elif size_bytes < 1024**4:  # Moins de 1 TB
                        return f"{size_bytes / (1024**3):.1f} GB"
                    else:
                        return f"{size_bytes / (1024**4):.1f} TB"
                
                free_space_str = format_size(free_space)
                total_space_str = format_size(total_space)
                percent_free = (free_space / total_space) * 100
                
                # Appliquer des couleurs différentes selon l'espace disponible
                color = "#27ae60"  # Vert pour beaucoup d'espace
                if percent_free < 10:
                    color = self.accent_color  # Rouge pour peu d'espace
                elif percent_free < 25:
                    color = "#f39c12"  # Orange pour espace modéré
                    
                self.space_label.setText(f"Espace libre: <span style='color:{color};'>{free_space_str}</span> / {total_space_str}")
                self.space_label.setToolTip(f"{percent_free:.1f}% d'espace libre")
            except Exception as e:
                self.space_label.setText("Espace libre: Non disponible")
                
    def select_directory(self):
            """Ouvre une boîte de dialogue pour sélectionner un dossier"""
            directory = QFileDialog.getExistingDirectory(
                self,
                "Sélectionner un dossier",
                self.current_directory or os.path.expanduser("~"),
                QFileDialog.Option.ShowDirsOnly
            )
            
            if directory:
                self.current_directory = directory
                self.directory_label.setText(f"Dossier: {self.current_directory}")
                self.load_files(self.current_directory)
                self.update_disk_space()
                
        
        
                
    def file_matches_type(self, file_type, selected_type):
            """Vérifie si un fichier correspond au type de filtre sélectionné"""
            if selected_type == "Images":
                return file_type in ["JPG", "JPEG", "PNG", "GIF", "BMP", "WEBP", "SVG", "TIFF"]
            elif selected_type == "Documents":
                return file_type in ["PDF", "DOC", "DOCX", "TXT", "RTF", "XLS", "XLSX", "PPT", "PPTX", "ODT"]
            elif selected_type == "Vidéos":
                return file_type in ["MP4", "AVI", "MKV", "MOV", "WMV", "FLV", "WEBM"]
            elif selected_type == "Audios":
                return file_type in ["MP3", "WAV", "OGG", "FLAC", "AAC", "M4A"]
            elif selected_type == "Archives":
                return file_type in ["ZIP", "RAR", "7Z", "TAR", "GZ", "BZ2"]
            elif selected_type == "Code":
                return file_type in ["PY", "JS", "HTML", "CSS", "JAVA", "C", "CPP", "PHP"]
            elif selected_type == "Présentations":
                return file_type in ["PPT", "PPTX"]
            else:
                return True
                
        
            
    def update_selected_files(self):
            """Met à jour la liste des fichiers sélectionnés"""
            self.selected_files = []
            
            for item in self.file_table.selectedItems():
                if item.column() == 0:  # Pour ne compter que les noms de fichiers (colonne 0)
                    file_name = item.text()
                    file_path = os.path.join(self.current_directory, file_name)
                    self.selected_files.append(file_path)
                    
    def show_context_menu(self, position):
            """Affiche un menu contextuel pour les fichiers sélectionnés"""
            context_menu = QMenu(self)
            context_menu.setStyleSheet(f"""
                QMenu {{
                    background-color: white;
                    border: 1px solid #dadce0;
                    border-radius: {self.border_radius};
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 8px 20px 8px 30px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: rgba(52, 152, 219, 0.1);
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: #dadce0;
                    margin: 5px 15px;
                }}
                QMenu::icon {{
                    padding-left: 20px;
                }}
            """)
            
            if self.selected_files:
                context_menu.addAction("📄 Ouvrir", self.open_file)
        
                
                context_menu.addSeparator()
                context_menu.addAction("✏️ Renommer", self.rename_file)
                context_menu.addAction("🗑️ Supprimer", self.delete_file)
                context_menu.addSeparator()

            else:
            
        
                context_menu.addAction("🔄 Actualiser", lambda: self.load_files())
                
            context_menu.exec(self.file_table.mapToGlobal(position))
            
    
    def show_notification(self, message, type_="info"):
            """Affiche une notification élégante à l'utilisateur"""
            notification = QDialog(self)
            notification.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
            notification.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            
            # Configurer le style selon le type
            bg_color = "#3498db"  # Bleu pour info
            icon = "ℹ️"
            
            if type_ == "success":
                bg_color = "#2ecc71"  # Vert pour succès
                icon = "✅"
            elif type_ == "warning":
                bg_color = "#f39c12"  # Orange pour avertissement
                icon = "⚠️"
            elif type_ == "error":
                bg_color = "#e74c3c"  # Rouge pour erreur
                icon = "❌"
                
            layout = QHBoxLayout(notification)
            
            content = QWidget()
            content.setStyleSheet(f"""
                background-color: {bg_color};
                border-radius: 10px;
                color: white;
            """)
            content_layout = QHBoxLayout(content)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px; padding-right: 10px;")
            content_layout.addWidget(icon_label)
            
            msg_label = QLabel(message)
            msg_label.setStyleSheet("font-size: 14px; font-weight: 500;")
            content_layout.addWidget(msg_label)
            
            layout.addWidget(content)
            
            # Position en haut à droite
            desktop = QApplication.desktop()
            screen_rect = desktop.availableGeometry(self)
            notification.setGeometry(
                screen_rect.width() - 400,
                50,
                350,
                80
            )
            
            # Afficher et fermer après 3 secondes
            notification.show()
            QTimer.singleShot(3000, notification.close)
            
    def open_file(self, item: QTableWidgetItem):
            """Ouvre un fichier avec l'application par défaut du système."""
            file_path = item.text().strip()

            if not file_path:
                QMessageBox.warning(self, "Erreur", "Aucun fichier sélectionné.")
                return

            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Erreur", f"Le fichier '{file_path}' est introuvable.")
                return

            try:
                if sys.platform.startswith("win"):  # Windows
                    os.startfile(file_path)
                elif sys.platform.startswith("darwin"):  # macOS
                    subprocess.run(["open", file_path], check=True)
                else:  # Linux
                    subprocess.run(["xdg-open", file_path], check=True)
            except Exception as e:
                QMessageBox.warning(self, "Avertissement", f"Impossible d'ouvrir {os.path.basename(file_path)}\nErreur: {str(e)}")
    def rename_file(self):
            """Renomme le fichier sélectionné"""
            if len(self.selected_files) != 1:
                QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un seul fichier à renommer")
                return
                
            file_path = self.selected_files[0]
            old_name = os.path.basename(file_path)
            
            # Interface de renommage élégante
            rename_dialog = QDialog(self)
            rename_dialog.setWindowTitle("Renommer")
            rename_dialog.setFixedSize(400, 150)
            rename_dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: white;
                    border-radius: {self.border_radius};
                }}
            """)
            
            dialog_layout = QVBoxLayout(rename_dialog)
            
            # Étiquette d'information
            info_label = QLabel(f"Renommer '{old_name}'")
            info_label.setStyleSheet("font-weight: 600; font-size: 14px; margin-bottom: 10px;")
            dialog_layout.addWidget(info_label)
            
            # Champ de saisie
            new_name_input = QLineEdit(old_name)
            new_name_input.setStyleSheet(f"""
                QLineEdit {{
                    padding: 10px;
                    border: 1px solid #dadce0;
                    border-radius: {self.border_radius};
                    font-size: 13px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {self.secondary_color};
                }}
            """)
            new_name_input.selectAll()
            dialog_layout.addWidget(new_name_input)
            
            # Boutons
            buttons_layout = QHBoxLayout()
            
            cancel_btn = QPushButton("Annuler")
            cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 8px 15px;
                    background-color: #f5f5f5;
                    border: none;
                    border-radius: {self.border_radius};
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: #e0e0e0;
                }}
            """)
            cancel_btn.clicked.connect(rename_dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            rename_btn = QPushButton("Renommer")
            rename_btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 8px 15px;
                    background-color: {self.secondary_color};
                    color: white;
                    border: none;
                    border-radius: {self.border_radius};
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: #2980b9;
                }}
            """)
            rename_btn.clicked.connect(rename_dialog.accept)
            buttons_layout.addWidget(rename_btn)
            
            dialog_layout.addLayout(buttons_layout)
            
            # Exécuter le dialogue
            if rename_dialog.exec() == QDialog.DialogCode.Accepted:
                new_name = new_name_input.text()
                
                if new_name and new_name != old_name:
                    try:
                        new_path = os.path.join(os.path.dirname(file_path), new_name)
                        os.rename(file_path, new_path)
                        self.load_files()  # Actualiser
                        self.show_notification(f"'{old_name}' renommé en '{new_name}'", "success")
                    except Exception as e:
                        QMessageBox.critical(self, "Erreur", f"Impossible de renommer le fichier: {str(e)}")
            
            # Ajouter un espace extensible
        
    def select_directory(self):
            """Ouvre un dialogue pour sélectionner un dossier et charge les fichiers"""
            directory = QFileDialog.getExistingDirectory(self, "Choisir un dossier", self.current_directory)
            if directory:
                self.current_directory = directory
                self.directory_label.setText(f"Dossier: {directory}")
                self.load_files(directory)
                self.update_disk_space()
        
    def load_files(self, directory=None):
                """Charge les fichiers dans le tableau en utilisant un thread pour éviter les blocages"""
                self.file_table.setRowCount(0)
                self.status_label.setText("Chargement des fichiers...")
                QApplication.processEvents()

                target_dir = directory or self.current_directory

                if not target_dir or not os.path.isdir(target_dir):
                    return

                self.loader = LoadFilesWorker(target_dir)
                self.loader.files_loaded.connect(self.populate_file_table)
                self.loader.error.connect(self.show_loading_error)
                self.loader.start()


    def organize_from_watcher(self, path):
            if self.organize_by_type.isChecked():
                classer_fichier_par_type(path)
            if self.organize_by_date.isChecked():
                classer_par_date(path)
            if self.remove_duplicates.isChecked():
                supprimer_doublons(path)
            if self.rename_files.isChecked():
                renommer_fichiers(path)

    def donate(self):
            """
            Méthode pour gérer les dons - ouvre une boîte de dialogue ou rediriger vers un site web de donation
            """
            # Option 1: Ouvrir directement un site web de donation
            donation_url = "https://example.com/donation"  # Remplacez par votre URL de donation
            QDesktopServices.openUrl(QUrl(donation_url))
            
            # Option 2: Ouvrir une boîte de dialogue personnalisée
            # self.open_donation_dialog()
        
    def open_donation_dialog(self):
            """
            Ouvre une boîte de dialogue de donation personnalisée avec un style professionnel
            """
            # Création de la boîte de dialogue
            dialog = QDialog(self)
            dialog.setWindowTitle("Faire un don")
            dialog.setMinimumWidth(400)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #f5f5f5;
                }
                QLabel {
                    color: #333333;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-bottom: 5px;
                }
                QLabel#headerLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #191970;
                    margin: 10px 0;
                }
                QLabel#descriptionLabel {
                    font-size: 13px;
                    color: #555555;
                    margin-bottom: 15px;
                }
                QComboBox {
                    padding: 8px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: white;
                    min-height: 30px;
                    margin-bottom: 15px;
                }
                QComboBox:hover {
                    border: 1px solid #3498db;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 25px;
                    border-left: 1px solid #cccccc;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1c6ea4;
                }
                QPushButton#cancelButton {
                    background-color: #f5f5f5;
                    color: #555555;
                    border: 1px solid #cccccc;
                }
                QPushButton#cancelButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            
            # Création du layout principal
            layout = QVBoxLayout()
            layout.setSpacing(12)
            layout.setContentsMargins(25, 25, 25, 25)
            
            # En-tête avec icône
            header_layout = QHBoxLayout()
            heart_icon = QLabel()
            heart_icon.setPixmap(QIcon("assets\\icon\\donate.svg").pixmap(32, 32))
            header_layout.addWidget(heart_icon)
            
            title_label = QLabel("Faire un don")
            title_label.setObjectName("headerLabel")
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            layout.addLayout(header_layout)
            
            # Ligne de séparation
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            separator.setStyleSheet("background-color: #dddddd; max-height: 1px;")
            layout.addWidget(separator)
            layout.addSpacing(10)
            
            # Message de remerciement et description
            thank_label = QLabel("Merci de soutenir notre projet !")
            thank_label.setObjectName("headerLabel")
            layout.addWidget(thank_label)
            
            description_label = QLabel("Votre contribution nous aide à continuer le développement de cette application et à fournir des mises à jour régulières.")
            description_label.setObjectName("descriptionLabel")
            description_label.setWordWrap(True)
            layout.addWidget(description_label)
            layout.addSpacing(10)
            
            # Options de montant de don
            amount_label = QLabel("Choisissez un montant:")
            layout.addWidget(amount_label)
            
            amount_combo = QComboBox()
            amount_combo.setObjectName("amountCombo")
            amounts = ["500 FCFA", "1000 FCFA", "2000 FCFA", "5000 FCFA", "10000 FCFA", "Autre..."]
            amount_combo.addItems(amounts)
            layout.addWidget(amount_combo)
            
            # Zone pour montant personnalisé (initialement cachée)
            custom_amount_widget = QWidget()
            custom_amount_layout = QHBoxLayout(custom_amount_widget)
            custom_amount_layout.setContentsMargins(0, 0, 0, 0)
            
            custom_amount_label = QLabel("Montant personnalisé:")
            custom_amount_layout.addWidget(custom_amount_label)
            
            custom_amount_input = QLineEdit()
            custom_amount_input.setPlaceholderText("Entrez un montant")
            custom_amount_input.setValidator(QDoubleValidator(0.99, 9999.99, 2))
            custom_amount_layout.addWidget(custom_amount_input)
            
            euro_label = QLabel("FCFA")
            custom_amount_layout.addWidget(euro_label)
            
            layout.addWidget(custom_amount_widget)
            custom_amount_widget.setVisible(False)
            
            # Afficher le champ de montant personnalisé si "Autre..." est sélectionné
            def on_amount_changed(index):
                custom_amount_widget.setVisible(amount_combo.currentText() == "Autre...")
            
            amount_combo.currentIndexChanged.connect(on_amount_changed)
            
            # Boutons d'action
            button_layout = QHBoxLayout()
            cancel_button = QPushButton("Annuler")
            cancel_button.setObjectName("cancelButton")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            donate_button = QPushButton("Procéder au paiement")
            donate_button.setDefault(True)
        
            def get_donation_amount():
                if amount_combo.currentText() == "Autre...":
                    try:
                        amount = float(custom_amount_input.text().replace(',', '.'))
                        return f"{amount:.2f} €"
                    except ValueError:
                        QMessageBox.warning(dialog, "Montant invalide", "Veuillez entrer un montant valide.")
                        return None
                else:
                    return amount_combo.currentText()
            
            donate_button.clicked.connect(lambda: self.process_donation(get_donation_amount()) if get_donation_amount() else None)
            button_layout.addWidget(donate_button)
            layout.addSpacing(10)
            layout.addLayout(button_layout)
        
            # Configuration finale et affichage
            dialog.setLayout(layout)
            return dialog.exec()
        
        
    def process_donation(self, amount):
            """
            Traite le don en fonction du montant sélectionné
            """
            # Ici, vous intégreriez un système de paiement comme PayPal, Stripe, etc.
            QMessageBox.information(self, "Merci!", f"Redirection vers la page de paiement pour un don de {amount}")
            
            # Rediriger vers la page de paiement
            # Exemple avec PayPal:
            # paypal_url = f"https://www.paypal.com/donate?amount={amount}&currency_code=EUR&your_paypal_id"
            # QDesktopServices.openUrl(QUrl(paypal_url))

    
        
    
    def update_disk_space(self):
            """Met à jour les informations sur l'espace disque disponible"""
            try:
                if os.path.exists(self.current_directory):
                    disk_info = shutil.disk_usage(self.current_directory)
                    free_gb = disk_info.free / (1024**3)
                    total_gb = disk_info.total / (1024**3)
                    self.space_label.setText(f"Espace libre: {free_gb:.1f} GB / {total_gb:.1f} GB")
            except Exception:
                self.space_label.setText("Espace libre: inconnu")
        
        
        
    def search_files(self):
            """Filtre les fichiers selon le texte de recherche"""
            search_text = self.search_input.text().lower()
            self.apply_filters()  # Réappliquer également les filtres
        

                
    
    def show_statistics(self):
            from gui.statistics_window import StatisticsWindow
            stats_window = StatisticsWindow(self.current_directory)
            stats_window.exec()

    def ouvrir_parametres(self):
            dialog = SettingsDialog(self)
            dialog.exec()
    def apply_filters(self):
            """Applique les filtres combinés (recherche et type)"""
            search_text = self.search_input.text().lower()
            type_filter = self.type_filter.currentText()
            
            for row in range(self.file_table.rowCount()):
                show_row = True
                file_name = self.file_table.item(row, 0).text().lower()
                file_type = self.file_table.item(row, 1).text()
                
                # Filtre par texte de recherche
                if search_text and search_text not in file_name:
                    show_row = False
                
                # Filtre par type
                if type_filter != "Tous" and file_type != type_filter:
                    show_row = False
                
                self.file_table.setRowHidden(row, not show_row)
            

            
        
    def reset_filters(self):
            """Réinitialise tous les filtres"""
            self.search_input.clear()
            self.type_filter.setCurrentText("Tous")
            # Afficher tous les fichiers
            for row in range(self.file_table.rowCount()):
                self.file_table.setRowHidden(row, False)
        
    def update_selected_files(self):
            """Met à jour la liste des fichiers sélectionnés"""
            self.selected_files = []
            selected_rows = set()
            
            for item in self.file_table.selectedItems():
                row = item.row()
                selected_rows.add(row)
            
            for row in selected_rows:
                file_name = self.file_table.item(row, 0).text()
                self.selected_files.append(file_name)
        
        
    def update_selected_files(self):
            """Met à jour la liste des fichiers sélectionnés"""
            self.selected_files = []
            for item in self.file_table.selectedItems():
                if item.column() == 0:  # Colonne du nom de fichier
                    self.selected_files.append(item.text())
        
        
    def rename_file(self):
            """Renomme le fichier sélectionné"""
            if not self.selected_files or len(self.selected_files) > 1:
                QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un seul fichier à renommer.")
                return
            
            # Ici, vous pourriez appeler votre fonction existante
            current_name = self.selected_files[0]
            new_name, ok = QInputDialog.getText(
                self, "Renommer le fichier", 
                "Nouveau nom:", 
                text=current_name
            )
            
            if ok and new_name:
                print(f"Renommer '{current_name}' en '{new_name}'")
                # Mettre à jour l'interface après le renommage
                selected_rows = self.file_table.selectedItems()
                if selected_rows and selected_rows[0].column() == 0:
                    row = selected_rows[0].row()
                    self.file_table.item(row, 0).setText(new_name)
            
    def delete_file(self):
            """Supprime le(s) fichier(s) sélectionné(s)"""
            if not self.selected_files:
                QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un fichier à supprimer.")
                return
            
            reply = QMessageBox.question(
                self, "Confirmation de suppression", 
                f"Êtes-vous sûr de vouloir supprimer {len(self.selected_files)} fichier(s) ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Ici, vous pourriez appeler votre fonction existante
                print(f"Supprimer les fichiers: {self.selected_files}")
                
                # Supprimer de l'interface
                rows_to_remove = []
                for i in range(self.file_table.rowCount()):
                    if self.file_table.item(i, 0).text() in self.selected_files:
                        rows_to_remove.append(i)
                
                # Supprimer en commençant par la fin pour éviter les décalages d'index
                for row in sorted(rows_to_remove, reverse=True):
                    self.file_table.removeRow(row)
                
                # Mettre à jour le statut
                self.update_status()
            
    def organize_files(self):
            """Organise automatiquement les fichiers dans le répertoire actuel selon les options cochées."""
            
            # Vérifier qu'au moins une option est cochée
            selected_options = [
                self.organize_by_type.isChecked(),
                self.organize_by_date.isChecked(),
                self.organize_by_name.isChecked(),
                self.rename_files.isChecked(),
                self.remove_duplicates.isChecked()
                
            ]
            
            if not any(selected_options):
                QMessageBox.information(self, "Aucune option sélectionnée", "Veuillez cocher au moins une option.")
                return

            # Estimer le nombre de fichiers pour calculer le temps
            try:
                file_count = sum([len(files) for _, _, files in os.walk(self.current_directory)])
            except:
                file_count = 100  # Estimation par défaut
            
            # Créer une notification de progression
            notification = QProgressDialog("Initialisation...", "Annuler", 0, 100, self)
            notification.setWindowTitle("Organisation des fichiers")
            notification.setWindowModality(Qt.WindowModality.WindowModal)
            notification.setMinimumDuration(0)
            notification.setValue(0)
            notification.show()
            
            # Variables pour le calcul du temps restant
            start_time = time.time()
            tasks_completed = 0
            total_tasks = sum(selected_options)
            
            def update_remaining_time(current_progress, task_name):
                """Met à jour l'affichage avec le temps restant estimé."""
                nonlocal tasks_completed, start_time
                
                if current_progress > 0:
                    elapsed_time = time.time() - start_time
                    if current_progress < 100:
                        estimated_total_time = elapsed_time * (100 / current_progress)
                        remaining_time = estimated_total_time - elapsed_time
                        
                        if remaining_time > 60:
                            time_str = f"{int(remaining_time // 60)}m {int(remaining_time % 60)}s"
                        else:
                            time_str = f"{int(remaining_time)}s"
                        
                        notification.setLabelText(f"{task_name}\nTemps restant estimé: {time_str}")
                    else:
                        notification.setLabelText(f"{task_name}\nTerminé!")
                else:
                    notification.setLabelText(task_name)
                
                notification.setValue(current_progress)
                QApplication.processEvents()
                
                # Vérifier si l'utilisateur a annulé
                return not notification.wasCanceled()

            try:
                progress = 0
                step = 100 // total_tasks
                
                # Estimation du temps par tâche basée sur le nombre de fichiers
                base_time_per_file = 0.01  # 10ms par fichier (estimation conservative)
                
                if self.organize_by_type.isChecked():
                    if not update_remaining_time(progress, "Classement des fichiers par type..."):
                        return
                    
                    task_start = time.time()
                    
                    # Simulation de progression pour les gros dossiers
                    if file_count > 50:
                        for i in range(0, step, max(1, step // 10)):
                            if notification.wasCanceled():
                                return
                            update_remaining_time(progress + i, "Classement des fichiers par type...")
                            time.sleep(0.1)  # Petite pause pour éviter le gel
                    
                    classer_fichier_par_type(self.current_directory)
                    progress += step
                    tasks_completed += 1
                    
                    if not update_remaining_time(progress, "Classement par type terminé"):
                        return
                    

                if self.organize_by_date.isChecked():
                    if not update_remaining_time(progress, "Classement des fichiers par date..."):
                        return
                    
                    # Simulation de progression pour les gros dossiers
                    if file_count > 50:
                        for i in range(0, step, max(1, step // 10)):
                            if notification.wasCanceled():
                                return
                            update_remaining_time(progress + i, "Classement des fichiers par date...")
                            time.sleep(0.1)
                    
                    classer_par_date(self.current_directory)
                    progress += step
                    tasks_completed += 1
                    
                    if not update_remaining_time(progress, "Classement par date terminé"):
                        return
         
                if self.organize_by_name.isChecked():
                    if not update_remaining_time(progress, "Organisation des fichiers par nom..."):
                        return
                    
                    # Simulation de progression pour les gros dossiers
                    if file_count > 50:
                        for i in range(0, step, max(1, step // 10)):
                            if notification.wasCanceled():
                                return
                            update_remaining_time(progress + i, "Organisation des fichiers par nom...")
                            time.sleep(0.1)
                    
                    organiser_par_nom(self.current_directory)
                    progress += step
                    tasks_completed += 1
                    
                    if not update_remaining_time(progress, "Organisation par nom terminée"):
                        return
                if self.rename_files.isChecked():
                    if not update_remaining_time(progress, "Renommage des fichiers..."):
                        return
                    
                    # Simulation de progression pour les gros dossiers
                    if file_count > 50:
                        for i in range(0, step, max(1, step // 10)):
                            if notification.wasCanceled():
                                return
                            update_remaining_time(progress + i, "Renommage des fichiers...")
                            time.sleep(0.1)
                    
                    renommer_fichiers(self.current_directory)
                    progress += step
                    tasks_completed += 1
                    
                    if not update_remaining_time(progress, "Renommage terminé"):
                        return

                if self.remove_duplicates.isChecked():
                    if not update_remaining_time(progress, "Suppression des doublons..."):
                        return
                    
                    # Cette tâche peut être plus longue, simulation plus détaillée
                    if file_count > 30:
                        for i in range(0, step, max(1, step // 15)):
                            if notification.wasCanceled():
                                return
                            update_remaining_time(progress + i, "Analyse et suppression des doublons...")
                            time.sleep(0.1)
                    
                    supprimer_doublons(self.current_directory)
                    progress += step
                    tasks_completed += 1
                    
                    if not update_remaining_time(progress, "Suppression des doublons terminée"):
                        return

                # Finalisation
                update_remaining_time(100, "Organisation terminée avec succès!")
                self.load_files(self.current_directory)
                time.sleep(0.5)  # Laisser le temps de voir le message final
                
                notification.close()
                
                total_time = time.time() - start_time
                time_message = f"Temps total: {int(total_time // 60)}m {int(total_time % 60)}s" if total_time > 60 else f"Temps total: {int(total_time)}s"
                
                QMessageBox.information(self, "Organisation automatique", 
                                    f"Les fichiers ont été organisés avec succès!\n{time_message}")
                self.load_files(self.current_directory)
            except Exception as e:
                if 'notification' in locals():
                    notification.close()
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {str(e)}")
            
            finally:
                # S'assurer que la notification est fermée
                if 'notification' in locals() and notification:
                    notification.close()
    
    
    
    def populate_file_table(self, file_list):
        """Affiche les fichiers dans le tableau après chargement"""
        self.file_table.setRowCount(len(file_list))
        for row, (name, type_, size, date, hash_, _) in enumerate(file_list):
            self.file_table.setItem(row, 0, QTableWidgetItem(name))
            self.file_table.setItem(row, 1, QTableWidgetItem(type_))
            self.file_table.setItem(row, 2, QTableWidgetItem(size))
            self.file_table.setItem(row, 3, QTableWidgetItem(date))
            self.file_table.setItem(row, 4, QTableWidgetItem(hash_))

        total_files = len(file_list)
        total_size_kb = sum(item[5] for item in file_list)

        if total_size_kb < 1024:
            size_text = f"{total_size_kb:.2f} KB"
        else:
            total_size_mb = total_size_kb / 1024
            size_text = f"{total_size_mb:.2f} MB" if total_size_mb < 1024 else f"{total_size_mb / 1024:.2f} GB"

        self.status_label.setText(f"{total_files} éléments - {size_text}")
        
    def add_file_to_table(self, file_data):
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        name, type_, size, date, hash_, size_kb = file_data
        self.file_table.setItem(row, 0, QTableWidgetItem(name))
        self.file_table.setItem(row, 1, QTableWidgetItem(type_))
        self.file_table.setItem(row, 2, QTableWidgetItem(size))
        self.file_table.setItem(row, 3, QTableWidgetItem(date))
        self.file_table.setItem(row, 4, QTableWidgetItem(hash_))

        self.total_size_kb += size_kb
        self.total_files += 1
        
    def finish_loading_files(self):
        if self.total_size_kb < 1024:
            size_text = f"{self.total_size_kb:.2f} KB"
        else:
            total_size_mb = self.total_size_kb / 1024
            size_text = f"{total_size_mb:.2f} MB" if total_size_mb < 1024 else f"{total_size_mb / 1024:.2f} GB"

        self.status_label.setText(f"{self.total_files} éléments - {size_text}")

    def show_loading_error(self, error_msg):
        """Affiche un message d'erreur si le chargement échoue"""
        self.status_label.setText("Erreur de chargement")
        QMessageBox.critical(self, "Erreur", f"Impossible de charger les fichiers :\n{error_msg}")

    def load_files(self, directory=None):
        self.file_table.setRowCount(0)
        self.icon_model.clear()
        self.list_model.clear()
        self.file_data = []  # Vider les données existantes
        self.status_label.setText("Chargement des fichiers...")
        QApplication.processEvents()
        
        target_dir = directory or self.current_directory
        if not target_dir or not os.path.isdir(target_dir):
            return
        
        self.current_directory = target_dir  # Mettre à jour le répertoire courant
        self.total_size_kb = 0
        self.total_files = 0
        
        self.loader = LoadFilesWorker(target_dir)
        self.loader.file_found.connect(self.add_file_to_table)
        self.loader.finished.connect(self.finish_loading_files)
        self.loader.error.connect(self.show_loading_error)
        self.loader.start()
    
    def add_file_to_table(self, file_data):
        # Ajouter au tableau détaillé
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        name, type_, size, date, hash_, size_kb = file_data
        
        self.file_table.setItem(row, 0, QTableWidgetItem(name))
        self.file_table.setItem(row, 1, QTableWidgetItem(type_))
        self.file_table.setItem(row, 2, QTableWidgetItem(size))
        self.file_table.setItem(row, 3, QTableWidgetItem(date))
        self.file_table.setItem(row, 4, QTableWidgetItem(hash_))
        
        # Stocker les données pour les autres vues
        self.file_data.append(file_data)
        
        self.total_size_kb += size_kb
        self.total_files += 1
    
    def finish_loading_files(self):
        if self.total_size_kb < 1024:
            size_text = f"{self.total_size_kb:.2f} KB"
        else:
            total_size_mb = self.total_size_kb / 1024
            size_text = f"{total_size_mb:.2f} MB" if total_size_mb < 1024 else f"{total_size_mb / 1024:.2f} GB"
        
        self.status_label.setText(f"{self.total_files} éléments - {size_text}")
        
        # Après avoir chargé les fichiers, mettre à jour la vue actuelle
        self.refresh_current_view()

    def search_files(self):
            """Filtre les fichiers selon le texte de recherche"""
            search_text = self.search_input.text().lower()
            self.apply_filters()
                
    def apply_filters(self):
            """Applique les filtres (recherche + type)"""
            search_text = self.search_input.text().lower()
            selected_type = self.type_filter.currentText()
            
            # Masquer/afficher les lignes selon les filtres
            for row in range(self.file_table.rowCount()):
                file_name = self.file_table.item(row, 0).text().lower()
                file_type = self.file_table.item(row, 1).text()
                
                # Vérifier si le fichier correspond au texte de recherche
                matches_search = search_text == "" or search_text in file_name
                
                # Vérifier si le fichier correspond au type sélectionné
                matches_type = selected_type == "Tous" or self.file_matches_type(file_type, selected_type)
                
                # Afficher ou masquer la ligne
                self.file_table.setRowHidden(row, not (matches_search and matches_type))
                
            # Mettre à jour le statut
            visible_count = sum(1 for row in range(self.file_table.rowCount()) if not self.file_table.isRowHidden(row))
            self.status_label.setText(f"{visible_count} éléments visibles sur {self.file_table.rowCount()}")



    def reset_filters(self):
        """Réinitialise tous les filtres"""
        self.search_input.clear()
        self.type_filter.setCurrentText("Tous")
        
        # Afficher toutes les lignes
        for row in range(self.file_table.rowCount()):
            self.file_table.setRowHidden(row, False)
            
        # Mettre à jour le statut
        self.status_label.setText(f"{self.file_table.rowCount()} éléments")    


    def change_view_mode(self, mode):
            self.current_view_mode = mode
            
            # Cacher toutes les vues
            self.file_table.hide()
            self.icon_view.hide()
            self.list_view.hide()
            
            # Afficher la vue sélectionnée
            if mode == "Détails":
                self.file_table.show()
            elif mode == "Icônes":
                self.icon_view.show()
            elif mode == "Liste":
                self.list_view.show()
                
            # Mettre à jour les données dans la vue appropriée
            self.refresh_current_view()

    def refresh_current_view(self):
            """Met à jour la vue actuellement active avec les données actuelles"""
            if self.current_view_mode == "Détails":
                # La vue détaillée est déjà mise à jour par les méthodes existantes
                pass
            elif self.current_view_mode == "Icônes":
                self.update_icon_view()
            elif self.current_view_mode == "Liste":
                self.update_list_view()

    def update_icon_view(self):
            """Met à jour la vue en mode icônes avec les données actuelles"""
            self.icon_model.clear()
            
            for file_data in self.file_data:
                name, type_, size, date, hash_, size_kb = file_data
                
                # Créer un élément pour ce fichier
                item = QStandardItem()
                item.setText(name)
                item.setToolTip(f"Type: {type_}\nTaille: {size}\nDate: {date}")
                
                # Obtenir l'icône appropriée pour ce type de fichier
                file_path = os.path.join(self.current_directory, name)
                if os.path.exists(file_path):
                    icon = self.icon_provider.icon(QFileInfo(file_path))

                    if icon:
                        item.setIcon(icon)
                
                # Stocker les données complètes pour référence
                item.setData(file_data, Qt.ItemDataRole.UserRole)
                
                self.icon_model.appendRow(item)


    def update_list_view(self):
            """Met à jour la vue en mode liste avec les données actuelles"""
            self.list_model.clear()
            
            for file_data in self.file_data:
                name, type_, size, date, hash_, size_kb = file_data
                
                # Créer un élément pour ce fichier
                item = QStandardItem()
                # Dans la vue liste, on affiche plus d'informations dans le texte
                item.setText(f"{name} - {type_} - {size} - {date}")
                item.setToolTip(f"Type: {type_}\nTaille: {size}\nDate: {date}\nHash: {hash_}")
                
                # Vérifier si une miniature est disponible ou nécessaire
            file_path = os.path.join(self.current_directory, name)  # Define file_path
            is_image = file_data[1].lower() in ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]
            is_video = file_data[1].lower() in ["mp4", "avi", "mkv", "mov", "wmv"]
            if (is_image or is_video) and file_path in self.thumbs_cache:
                # Utiliser la miniature mise en cache
                item.setIcon(QIcon(self.thumbs_cache[file_path]))
            elif is_image or is_video:
                # Générer une miniature en arrière-plan
                self.request_thumbnail(file_path, item, thumb_size=32)  # Taille plus petite pour la vue liste
            else:
                # Utiliser l'icône standard du système
                if os.path.exists(file_path):
                    icon = self.icon_provider.icon(QFileInfo(file_path))
                    if icon:
                        item.setIcon(icon)
            
            # Stocker les données complètes pour référence
            item.setData(file_data, Qt.ItemDataRole.UserRole)
            
            self.list_model.appendRow(item)
    
    
    def afficher_historique(self):
        """Affiche l'historique des actions dans une interface modernisée."""
        # Trouver le chemin du fichier historique
        program_directory = os.path.dirname(os.path.abspath(__file__))
        history_file = os.path.join(program_directory, "json", "history_organisations.json")
        
        if not os.path.exists(history_file):
            alternative_path = os.path.join(os.getcwd(), "json", "history_organisations.json")
            
            if os.path.exists(alternative_path):
                history_file = alternative_path
            else:
                QMessageBox.warning(self,
                   "Historique non trouvé", 
                    f"<b>Aucun historique trouvé.</b><br><br>"
                    f"Chemins recherchés :<br>"
                    f"• {history_file}<br>"
                    f"• {alternative_path}"
                )
                return
                
        try:
            # Charger le contenu du fichier JSON
            with open(history_file, "r", encoding="utf-8") as file:
                try:
                    history_data = json.load(file)
                except json.JSONDecodeError:
                    QMessageBox.critical(
                         "Fichier corrompu", 
                        "Le fichier d'historique est corrompu et ne peut pas être lu."
                    )
                    return
            
            # Afficher le chemin du fichier d'historique utilisé (pour le débogage)
            logger.debug(f"Fichier d'historique chargé: {history_file}")
            
            # Vérifier si l'historique est vide
            if not history_data:
                QMessageBox.information(
                    "Historique vide", 
                    "L'historique ne contient aucune entrée pour le moment."
                )
                return
                
            # Création de la fenêtre de dialogue
            dialog = QDialog()
            dialog.setWindowTitle("Historique des actions")
            dialog.resize(1000, 650)
            dialog.setMinimumSize(800, 500)
            dialog.setWindowIcon(QIcon("assets//icon//history_ico.svg"))  # Ajouter une icône si disponible
            
            # Application du style moderne
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #dfe3e8;
                    border-radius: 6px;
                    margin-top: 1.5ex;
                    padding: 10px;
                    background-color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 8px;
                    background-color: white;
                }
                QPushButton {
                    background-color: #4a86e8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                    min-width: 80px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a76d8;
                }
                QPushButton:pressed {
                    background-color: #2a66c8;
                }
                QPushButton#dangerButton {
                    background-color: #e53935;
                }
                QPushButton#dangerButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton#secondaryButton {
                    background-color: #757575;
                }
                QPushButton#secondaryButton:hover {
                    background-color: #616161;
                }
                QLineEdit, QDateEdit, QComboBox {
                    border: 1px solid #dfe3e8;
                    border-radius: 4px;
                    padding: 8px;
                    background-color: #ffffff;
                    selection-background-color: #4a86e8;
                    min-height: 20px;
                }
                QTableWidget {
                    border: 1px solid #dfe3e8;
                    border-radius: 4px;
                    alternate-background-color: #f3f7fb;
                    gridline-color: #e6e6e6;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QTableWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #212121;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    border: none;
                    border-bottom: 1px solid #dfe3e8;
                    padding: 8px;
                    font-weight: bold;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #f0f0f0;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #b0b0b0;
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #808080;
                }
                QLabel#titleLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #222222;
                }
                QLabel#statsLabel {
                    color: #555555;
                    font-style: italic;
                }
                QTextEdit {
                    border: 1px solid #dfe3e8;
                    border-radius: 4px;
                }
            """)
            
            # Layout principal
            main_layout = QVBoxLayout(dialog)
            main_layout.setSpacing(15)
            main_layout.setContentsMargins(20, 20, 20, 20)
            
            # En-tête avec titre et infos
            header_layout = QHBoxLayout()
            
            # Titre avec icône
            title_layout = QHBoxLayout()
            title_icon = QLabel()
            title_icon_pixmap = QPixmap("assets//icon/history_ico.svg")  # Ajouter une icône si disponible
            if not title_icon_pixmap.isNull():
                title_icon.setPixmap(title_icon_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                title_icon.setText("📋")
                title_icon.setFont(QFont("", 16))
                
            title_label = QLabel("Historique des actions")
            title_label.setObjectName("titleLabel")
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_label.setFont(title_font)
            
            title_layout.addWidget(title_icon)
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            
            header_layout.addLayout(title_layout)
            header_layout.addStretch()
            
            # Informations sur le fichier (affichées discrètement)
            file_info = QLabel(f"Source : {os.path.basename(history_file)}")
            file_info.setStyleSheet("color: #888888; font-style: italic;")
            header_layout.addWidget(file_info)
            
            main_layout.addLayout(header_layout)
            
            # Groupe pour les filtres
            filter_group = QGroupBox("Filtres de recherche")
            filter_layout = QHBoxLayout()
            filter_layout.setSpacing(15)
            
            # Filtre par date
            date_layout = QVBoxLayout()
            date_label = QLabel("Date:")
            date_filter = QDateEdit()
            date_filter.setCalendarPopup(True)
            date_filter.setDate(QDate.currentDate())
            date_filter.setEnabled(False)
            date_check = QCheckBox("Activer le filtre par date")
            
            date_layout.addWidget(date_label)
            date_layout.addWidget(date_filter)
            date_layout.addWidget(date_check)
            
            # Filtre par action
            action_layout = QVBoxLayout()
            action_label = QLabel("Type d'action:")
            action_filter = QComboBox()
            action_filter.addItem("Toutes les actions")
            
            # Extraire les types d'actions uniques
            actions = set()
            for entry in history_data:
                actions.add(entry.get("action", "Inconnue"))
            
            for action in sorted(actions):
                action_filter.addItem(action)
                
            action_layout.addWidget(action_label)
            action_layout.addWidget(action_filter)
            action_layout.addStretch()
            
            # Recherche
            search_layout = QVBoxLayout()
            search_label = QLabel("Recherche textuelle:")
            search_input = QLineEdit()
            search_input.setPlaceholderText("Rechercher dans les chemins...")
            
            search_layout.addWidget(search_label)
            search_layout.addWidget(search_input)
            search_layout.addStretch()
            
            # Ajouter les widgets aux filtres
            filter_layout.addLayout(date_layout)
            filter_layout.addLayout(action_layout)
            filter_layout.addLayout(search_layout)
            
            filter_group.setLayout(filter_layout)
            main_layout.addWidget(filter_group)
            
            # Tableau d'historique
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Date et heure", "Action", "Source", "Destination"])
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            
            # Configuration des colonnes
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            
            # Fonction pour rafraîchir le tableau avec les filtres
            def refresh_table():
                table.setRowCount(0)  # Effacer le tableau
                
                filtered_history = history_data
                
                # Appliquer les filtres
                if date_check.isChecked():
                    selected_date = date_filter.date().toString("yyyy-MM-dd")
                    filtered_history = [
                        entry for entry in filtered_history
                        if entry.get("date", "").startswith(selected_date)
                    ]
                
                if action_filter.currentText() != "Toutes les actions":
                    selected_action = action_filter.currentText()
                    filtered_history = [
                        entry for entry in filtered_history
                        if entry.get("action") == selected_action
                    ]
                
                if search_text := search_input.text().strip():
                    search_text = search_text.lower()
                    filtered_history = [
                        entry for entry in filtered_history
                        if (search_text in entry.get("source", "").lower() or 
                            search_text in entry.get("destination", "").lower())
                    ]
                
                # Tri par date décroissante (le plus récent en premier)
                filtered_history.sort(key=lambda x: x.get("date", ""), reverse=True)
                
                # Remplir le tableau
                table.setRowCount(len(filtered_history))
                
                for row, entry in enumerate(filtered_history):
                    # Formater la date et l'heure
                    try:
                        date_str = entry.get("date", "")
                        datetime_obj = datetime.fromisoformat(date_str)
                        formatted_date = datetime_obj.strftime("%d/%m/%Y %H:%M:%S")
                    except (ValueError, TypeError):
                        formatted_date = date_str
                    
                    # Couleur de fond selon le type d'action
                    action_type = entry.get("action", "")
                    row_color = QColor(255, 255, 255)  # Blanc par défaut
                    
                    if "déplacement" in action_type.lower():
                        row_color = QColor(232, 245, 253)  # Bleu clair
                    elif "suppression" in action_type.lower():
                        row_color = QColor(253, 237, 237)  # Rouge clair
                    elif "renommage" in action_type.lower():
                        row_color = QColor(240, 244, 195)  # Jaune clair
                    
                    # Créer et configurer les items du tableau
                    date_item = QTableWidgetItem(formatted_date)
                    action_item = QTableWidgetItem(action_type)
                    
                    source_path = entry.get("source", "")
                    dest_path = entry.get("destination", "N/A")
                    
                    source_item = QTableWidgetItem(source_path)
                    source_item.setToolTip(source_path)
                    
                    dest_item = QTableWidgetItem(dest_path)
                    dest_item.setToolTip(dest_path)
                    
                    # Appliquer la couleur de fond
                    date_item.setBackground(row_color)
                    action_item.setBackground(row_color)
                    source_item.setBackground(row_color)
                    dest_item.setBackground(row_color)
                    
                    # Ajouter les items à la ligne
                    table.setItem(row, 0, date_item)
                    table.setItem(row, 1, action_item)
                    table.setItem(row, 2, source_item)
                    table.setItem(row, 3, dest_item)
                
                # Mise à jour des statistiques
                visible_rows = table.rowCount()
                total_entries = len(history_data)
                if visible_rows == total_entries:
                    stats_label.setText(f"{total_entries} entrées au total")
                else:
                    stats_label.setText(f"{visible_rows} entrées affichées sur {total_entries} au total")
            
            # Ajouter le tableau au layout principal
            main_layout.addWidget(table)
            
            # Barre de statistiques
            stats_layout = QHBoxLayout()
            stats_label = QLabel()
            stats_label.setObjectName("statsLabel")
            stats_layout.addWidget(stats_label)
            stats_layout.addStretch()
            
            main_layout.addLayout(stats_layout)
            
            # Boutons d'action
            buttons_layout = QHBoxLayout()
            
            # Bouton d'exportation
            export_button = QPushButton("Exporter")
            export_button.setIcon(QIcon("icons/export.png"))  # Ajouter une icône si disponible
            
            # Bouton pour effacer l'historique
            clear_button = QPushButton("Effacer l'historique")
            clear_button.setObjectName("dangerButton")
            clear_button.setIcon(QIcon("icons/delete.png"))  # Ajouter une icône si disponible
            
            # Bouton de fermeture
            close_button = QPushButton("Fermer")
            close_button.setObjectName("secondaryButton")
            
            # Ajouter les boutons au layout
            buttons_layout.addWidget(export_button)
            buttons_layout.addWidget(clear_button)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_button)
            
            main_layout.addLayout(buttons_layout)
            
            # Fonction d'exportation
            def export_history():
                options = QFileDialog.Options()
                filename, _ = QFileDialog.getSaveFileName(
                    dialog,
                    "Exporter l'historique",
                    "",
                    "Fichiers CSV (*.csv);;Fichiers JSON (*.json)",
                    options=options
                )
                
                if not filename:
                    return
                    
                try:
                    if filename.endswith(".csv"):
                        with open(filename, "w", encoding="utf-8", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Date", "Action", "Source", "Destination"])
                            for entry in history_data:
                                writer.writerow([
                                    entry.get("date", ""),
                                    entry.get("action", ""),
                                    entry.get("source", ""),
                                    entry.get("destination", "N/A")
                                ])
                    elif filename.endswith(".json"):
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(history_data, f, indent=4)
                    else:
                        # Ajouter l'extension par défaut
                        filename += ".csv"
                        with open(filename, "w", encoding="utf-8", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Date", "Action", "Source", "Destination"])
                            for entry in history_data:
                                writer.writerow([
                                    entry.get("date", ""),
                                    entry.get("action", ""),
                                    entry.get("source", ""),
                                    entry.get("destination", "N/A")
                                ])
                    
                    QMessageBox.information(
                        dialog, 
                        "Exportation réussie", 
                        f"<b>Exportation réussie !</b><br><br>"
                        f"L'historique a été exporté vers :<br>"
                        f"{filename}"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        dialog, 
                        "Erreur d'exportation", 
                        f"<b>Erreur lors de l'exportation</b><br><br>"
                        f"Détail de l'erreur :<br>{str(e)}"
                    )
            
            # Fonction pour effacer l'historique
            def clear_history():
                confirm_dialog = QDialog(dialog)
                confirm_dialog.setWindowTitle("Confirmation")
                confirm_dialog.setFixedSize(400, 200)
                confirm_dialog.setStyleSheet(dialog.styleSheet())
                
                confirm_layout = QVBoxLayout(confirm_dialog)
                
                warning_icon = QLabel("⚠️")
                warning_icon.setFont(QFont("", 24))
                warning_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                confirm_msg = QLabel(
                    "<b>Êtes-vous sûr de vouloir effacer tout l'historique ?</b><br><br>"
                    "Cette action est irréversible. Une sauvegarde sera créée, "
                    "mais l'historique actuel sera vidé."
                )
                confirm_msg.setWordWrap(True)
                confirm_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                confirm_layout.addWidget(warning_icon)
                confirm_layout.addWidget(confirm_msg)
                
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Yes | 
                    QDialogButtonBox.StandardButton.No
                )
                buttons.button(QDialogButtonBox.StandardButton.Yes).setText("Oui, effacer")
                buttons.button(QDialogButtonBox.StandardButton.Yes).setStyleSheet(
                    "background-color: #e53935; font-weight: bold;"
                )
                buttons.button(QDialogButtonBox.StandardButton.No).setText("Annuler")
                
                confirm_layout.addWidget(buttons)
                
                buttons.accepted.connect(confirm_dialog.accept)
                buttons.rejected.connect(confirm_dialog.reject)
                
                result = confirm_dialog.exec()
                
                if result == QDialog.DialogCode.Accepted:
                    try:
                        # Sauvegarder une copie de sauvegarde
                        backup_file = history_file + f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        shutil.copy2(history_file, backup_file)
                        
                        # Écrire un tableau vide
                        with open(history_file, "w", encoding="utf-8") as f:
                            json.dump([], f)
                        
                        QMessageBox.information(
                            dialog,
                            "Historique effacé",
                            f"<b>Historique effacé avec succès</b><br><br>"
                            f"Une sauvegarde a été créée :<br>"
                            f"{os.path.basename(backup_file)}"
                        )
                        
                        # Fermer la fenêtre
                        dialog.accept()
                    except Exception as e:
                        QMessageBox.critical(
                            dialog, 
                            "Erreur", 
                            f"<b>Erreur lors de l'effacement</b><br><br>"
                            f"Détail de l'erreur :<br>{str(e)}"
                        )
            
            # Fonction pour afficher les détails d'une entrée
            def show_details(row, column):
                source = table.item(row, 2).text()
                destination = table.item(row, 3).text()
                action = table.item(row, 1).text()
                date = table.item(row, 0).text()
                
                detail_dialog = QDialog(dialog)
                detail_dialog.setWindowTitle(f"Détails - {action}")
                detail_dialog.resize(750, 400)
                detail_dialog.setStyleSheet(dialog.styleSheet())
                
                detail_layout = QVBoxLayout(detail_dialog)
                detail_layout.setSpacing(15)
                detail_layout.setContentsMargins(20, 20, 20, 20)
                
                # Titre avec l'action
                action_title = QLabel(f"<b>{action}</b>")
                action_title.setFont(QFont("", 14))
                detail_layout.addWidget(action_title)
                
                # Informations sur la date
                date_label = QLabel(f"Effectué le {date}")
                date_label.setStyleSheet("color: #666666;")
                detail_layout.addWidget(date_label)
                
                # Séparateur
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                separator.setStyleSheet("background-color: #dfe3e8;")
                detail_layout.addWidget(separator)
                
                # Formulaire détaillé
                detail_form = QFormLayout()
                detail_form.setSpacing(10)
                detail_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
                
                # Détails source
                source_label = QLabel("<b>Fichier source :</b>")
                source_text = QTextEdit()
                source_text.setReadOnly(True)
                source_text.setText(source)
                source_text.setMaximumHeight(100)
                source_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
                detail_form.addRow(source_label, source_text)
                
                # Détails destination
                dest_label = QLabel("<b>Destination :</b>")
                dest_text = QTextEdit()
                dest_text.setReadOnly(True)
                dest_text.setText(destination)
                dest_text.setMaximumHeight(100)
                dest_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
                detail_form.addRow(dest_label, dest_text)
                
                detail_layout.addLayout(detail_form)
                
                # Actions sur les fichiers
                actions_group = QGroupBox("Actions")
                actions_layout = QHBoxLayout()
                
                # Vérifier si les fichiers existent
                source_exists = os.path.exists(source)
                dest_exists = os.path.exists(destination) and destination != "N/A"
                
                if source_exists:
                    open_source_dir_button = QPushButton("Ouvrir dossier source")
                    open_source_dir_button.setIcon(QIcon("icons/folder.png"))
                    open_source_dir_button.clicked.connect(
                        lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(source)))
                    )
                    actions_layout.addWidget(open_source_dir_button)
                    
                    if os.path.isfile(source):
                        open_source_file_button = QPushButton("Ouvrir fichier source")
                        open_source_file_button.setIcon(QIcon("icons/file.png"))
                        open_source_file_button.clicked.connect(
                            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(source))
                        )
                        actions_layout.addWidget(open_source_file_button)
                
                if dest_exists:
                    open_dest_dir_button = QPushButton("Ouvrir dossier destination")
                    open_dest_dir_button.setIcon(QIcon("icons/folder.png"))
                    open_dest_dir_button.clicked.connect(
                        lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(destination)))
                    )
                    actions_layout.addWidget(open_dest_dir_button)
                    
                    if os.path.isfile(destination):
                        open_dest_file_button = QPushButton("Ouvrir fichier destination")
                        open_dest_file_button.setIcon(QIcon("icons/file.png"))
                        open_dest_file_button.clicked.connect(
                            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(destination))
                        )
                        actions_layout.addWidget(open_dest_file_button)
                
                if actions_layout.count() > 0:
                    actions_group.setLayout(actions_layout)
                    detail_layout.addWidget(actions_group)
                else:
                    not_found_label = QLabel("⚠️ Les fichiers n'existent plus ou ne sont pas accessibles.")
                    not_found_label.setStyleSheet("color: #e53935;")
                    not_found_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    detail_layout.addWidget(not_found_label)
                
                # Boutons de dialogue
                button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
                button_box.rejected.connect(detail_dialog.reject)
                detail_layout.addWidget(button_box)
                
                # Afficher la boîte de dialogue
                detail_dialog.exec()
            
            # Connecter les événements
            date_check.stateChanged.connect(lambda: date_filter.setEnabled(date_check.isChecked()))
            date_check.stateChanged.connect(refresh_table)
            date_filter.dateChanged.connect(refresh_table)
            action_filter.currentIndexChanged.connect(refresh_table)
            search_input.textChanged.connect(refresh_table)
            table.cellDoubleClicked.connect(show_details)
            export_button.clicked.connect(export_history)
            clear_button.clicked.connect(clear_history)
            close_button.clicked.connect(dialog.accept)
            
            # Afficher les données initiales
            refresh_table()
            
            # Afficher la fenêtre de dialogue
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self,
                 
                "Erreur critique", 
                f"<b>Erreur lors de l'affichage de l'historique</b><br><br>"
                f"Détail de l'erreur :<br>{str(e)}"
            )
            logger.error(f"Exception dans afficher_historique: {traceback.format_exc()}")