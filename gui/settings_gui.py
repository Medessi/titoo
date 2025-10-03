from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QGroupBox, QFormLayout,
     QAbstractItemView,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
import os
import json


class SettingsDialog(QDialog):
    def __init__(self, parent=None, preferences_path="preferences.json"):
        super().__init__(parent)
        self.setWindowTitle("Paramètres de TITO - Surveillance Multi-Dossiers")
        self.resize(700, 650)
        self.setWindowIcon(QIcon("icons/settings.png"))
        self.preferences_path = preferences_path
        self.load_preferences()
        self.setup_ui()
        
    def load_preferences(self):
        """Charge les préférences depuis le fichier JSON."""
        try:
            if os.path.exists(self.preferences_path):
                with open(self.preferences_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dossiers = data.get("dossiers", [])
            else:
                # Configuration par défaut
                self.dossiers = []
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des préférences : {e}")
            self.dossiers = []
            
    def save_preferences(self):
        """Sauvegarde les préférences dans le fichier JSON."""
        try:
            data = {"dossiers": self.dossiers}
            os.makedirs(os.path.dirname(self.preferences_path), exist_ok=True)
            with open(self.preferences_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {e}")
            return False
        
    def setup_ui(self):
        # Style général
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1.5ex;
                padding: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QPushButton.danger {
                background-color: #e74c3c;
            }
            QPushButton.warning {
                background-color: #f39c12;
            }
            QPushButton.secondary {
                background-color: #f0f0f0;
                color: #333333;
            }
            QLineEdit, QSpinBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
                selection-background-color: #4a86e8;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                gridline-color: #eeeeee;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e0e0ff;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre principal
        title_label = QLabel("Configuration de la Surveillance Multi-Dossiers")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Groupe de configuration des dossiers surveillés
        watched_group = QGroupBox("Dossiers surveillés")
        watched_layout = QVBoxLayout()
        
        # Tableau des dossiers
        self.setup_folders_table()
        watched_layout.addWidget(self.folders_table)
        
        # Boutons de gestion
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ajouter")
        add_btn.setIcon(QIcon("icons/add.png"))
        add_btn.clicked.connect(self.add_folder_dialog)
        
        edit_btn = QPushButton("Modifier")
        edit_btn.setIcon(QIcon("icons/edit.png"))
        edit_btn.clicked.connect(self.edit_folder_dialog)
        
        remove_btn = QPushButton("Supprimer")
        remove_btn.setIcon(QIcon("icons/delete.png"))
        remove_btn.setProperty("class", "danger")
        remove_btn.setStyleSheet("background-color: #e74c3c;")
        remove_btn.clicked.connect(self.remove_folder)
        
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addWidget(remove_btn)
        buttons_layout.addStretch()
        
        watched_layout.addLayout(buttons_layout)
        watched_group.setLayout(watched_layout)
        main_layout.addWidget(watched_group)
        
        # Boutons d'action principaux
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.setProperty("class", "warning")
        reset_btn.setStyleSheet("background-color: #f39c12; color: white;")
        reset_btn.clicked.connect(self.reset_settings)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setStyleSheet("background-color: #f0f0f0; color: #333333;")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Sauvegarder")
        save_btn.setIcon(QIcon("icons/save.png"))
        save_btn.clicked.connect(self.save_settings)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)

    def setup_folders_table(self):
        """Configure le tableau des dossiers surveillés."""
        self.folders_table = QTableWidget()
        self.folders_table.setColumnCount(3)
        self.folders_table.setHorizontalHeaderLabels(["Chemin du dossier", "Mode d'organisation", "Fréquence"])
        
        # Configuration des colonnes
        header = self.folders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Sélection par ligne complète
        self.folders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.folders_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Chargement des données
        self.refresh_folders_table()
        
    def refresh_folders_table(self):
        """Actualise le contenu du tableau."""
        self.folders_table.setRowCount(len(self.dossiers))
        
        for i, config in enumerate(self.dossiers):
            # Chemin
            path_item = QTableWidgetItem(config["chemin"])
            path_item.setFlags(path_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.folders_table.setItem(i, 0, path_item)
            
            # Mode
            mode_item = QTableWidgetItem(config["mode"])
            mode_item.setFlags(mode_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.folders_table.setItem(i, 1, mode_item)
            
            # Fréquence
            freq_item = QTableWidgetItem(config["frequence"])
            freq_item.setFlags(freq_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.folders_table.setItem(i, 2, freq_item)

    def add_folder_dialog(self):
        """Ouvre la boîte de dialogue pour ajouter un dossier."""
        dialog = FolderConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            
            # Vérifier si le dossier n'est pas déjà surveillé
            for existing in self.dossiers:
                if existing["chemin"] == config["chemin"]:
                    QMessageBox.warning(self, "Attention", "Ce dossier est déjà surveillé.")
                    return
                    
            self.dossiers.append(config)
            self.refresh_folders_table()

    def edit_folder_dialog(self):
        """Ouvre la boîte de dialogue pour modifier un dossier."""
        current_row = self.folders_table.currentRow()
        if current_row == -1:
            QMessageBox.information(self, "Information", "Veuillez sélectionner un dossier à modifier.")
            return
            
        config = self.dossiers[current_row]
        dialog = FolderConfigDialog(self, config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.dossiers[current_row] = dialog.get_config()
            self.refresh_folders_table()

    def remove_folder(self):
        """Supprime le dossier sélectionné."""
        current_row = self.folders_table.currentRow()
        if current_row == -1:
            QMessageBox.information(self, "Information", "Veuillez sélectionner un dossier à supprimer.")
            return
            
        reply = QMessageBox.question(self, "Confirmation", 
                                   "Êtes-vous sûr de vouloir supprimer ce dossier de la surveillance ?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.dossiers[current_row]
            self.refresh_folders_table()

    def reset_settings(self):
        """Réinitialise tous les paramètres."""
        reply = QMessageBox.question(self, "Confirmation", 
                                   "Êtes-vous sûr de vouloir supprimer toute la configuration ?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.dossiers = []
            self.refresh_folders_table()
            QMessageBox.information(self, "Succès", "Configuration réinitialisée.")

    def save_settings(self):
        """Sauvegarde les paramètres."""
        if not self.dossiers:
            QMessageBox.warning(self, "Attention", "Veuillez configurer au moins un dossier à surveiller.")
            return
            
        if self.save_preferences():
            QMessageBox.information(self, "Succès", "Configuration sauvegardée avec succès.")
            self.accept()

    def sizeHint(self):
        return QSize(700, 650)


class FolderConfigDialog(QDialog):
    """Boîte de dialogue pour configurer un dossier."""
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration du dossier")
        self.setModal(True)
        self.config = config or {"chemin": "", "mode": "type", "frequence": "journalier"}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Titre
        if self.config.get("chemin"):
            title_label = QLabel("Modifier la configuration du dossier")
        else:
            title_label = QLabel("Ajouter un nouveau dossier")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Chemin du dossier
        folder_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.config["chemin"])
        self.path_input.setPlaceholderText("Chemin du dossier à surveiller")
        
        browse_btn = QPushButton("Parcourir")
        browse_btn.clicked.connect(self.browse_folder)
        
        folder_layout.addWidget(self.path_input)
        folder_layout.addWidget(browse_btn)
        form_layout.addRow("Dossier :", folder_layout)
        
        # Mode d'organisation
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["type", "date", "nom"])
        self.mode_combo.setCurrentText(self.config["mode"])
        form_layout.addRow("Mode d'organisation :", self.mode_combo)
        
        # Fréquence
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["journalier", "hebdomadaire", "mensuel"])
        self.freq_combo.setCurrentText(self.config["frequence"])
        form_layout.addRow("Fréquence :", self.freq_combo)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_config)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(ok_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def browse_folder(self):
        """Ouvre le sélecteur de dossier."""
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier à surveiller")
        if folder:
            self.path_input.setText(folder)
            
    def accept_config(self):
        """Valide et accepte la configuration."""
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un dossier.")
            return
            
        if not os.path.exists(path):
            reply = QMessageBox.question(self, "Dossier inexistant", 
                                       f"Le dossier '{path}' n'existe pas. Voulez-vous continuer ?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
                
        self.accept()
        
    def get_config(self):
        """Retourne la configuration actuelle."""
        return {
            "chemin": self.path_input.text().strip(),
            "mode": self.mode_combo.currentText(),
            "frequence": self.freq_combo.currentText()
        }