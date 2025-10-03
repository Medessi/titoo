#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'interface pour l'affichage des statistiques de dossiers
pour le projet MIDEESSI.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTreeWidget, QTreeWidgetItem, QSizePolicy,
    QWidget, QFrame, QProgressBar, QHeaderView, QStyle,
    QSpacerItem, QFileDialog,QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QFont,  QColor
import csv

# Import du module de statistiques
# Adapter cet import selon votre structure de projet
from core.starts import generate_basic_report, generate_normal_report, generate_pro_report


class StatisticsWindow(QDialog):
    """
    Fenêtre de dialogue pour afficher les statistiques d'un dossier
    avec différents niveaux de détails.
    """
    
    def __init__(self, directory, parent=None):
        """
        Initialise la fenêtre des statistiques.
        
        Args:
            directory (str): Chemin du dossier à analyser
            parent (QWidget, optional): Widget parent. Par défaut None.
        """
        super().__init__(parent)
        self.directory = directory
        self.worker_thread = None
        
        # Configuration de la fenêtre
        self.setWindowTitle(f"Statistiques du dossier")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowTitleHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Appliquer une feuille de style globale
        self.apply_global_stylesheet()
        
        # Création de l'interface
        self.setup_ui()
        
        # Connexion des signaux
        self.connect_signals()
        
        # Par défaut, on sélectionne le niveau "Basic"
        self.level_combo.setCurrentIndex(0)
    
    def apply_global_stylesheet(self):
        """Applique une feuille de style globale à la fenêtre"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f7f9fc;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #333;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                selection-background-color: #2a82da;
                min-height: 25px;
            }
            QComboBox:hover {
                border: 1px solid #2a82da;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #ccc;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                border-radius: 3px;
            }
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f5f8fa;
                selection-background-color: #e0ebff;
                selection-color: #333;
                padding: 5px;
            }
            QTreeWidget::item {
                min-height: 28px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #e0ebff;
                color: #333;
            }
            QHeaderView::section {
                background-color: #f0f5fa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
                color: #444;
            }
        """)
    
    def setup_ui(self):
        """Configure l'interface utilisateur de la fenêtre."""
        # Layout principal avec marges élégantes
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # En-tête avec information du dossier et icône
        header_layout = QHBoxLayout()
        
        # Icône de dossier
        folder_icon_label = QLabel()
        folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        folder_icon_label.setPixmap(folder_icon.pixmap(48, 48))
        header_layout.addWidget(folder_icon_label)
        
        # Informations du dossier
        folder_info_layout = QVBoxLayout()
        
        # Titre du dossier avec une police élégante
        self.folder_title = QLabel(f"<b>{os.path.basename(self.directory) or self.directory}</b>")
        self.folder_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.folder_title.setStyleSheet("color: #2a82da;")
        
        # Chemin complet du dossier
        self.folder_path = QLabel(self.directory)
        self.folder_path.setFont(QFont("Segoe UI", 9))
        self.folder_path.setStyleSheet("color: #666;")
        
        folder_info_layout.addWidget(self.folder_title)
        folder_info_layout.addWidget(self.folder_path)
        header_layout.addLayout(folder_info_layout)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Séparateur horizontal élégant
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0; margin: 5px 0;")
        main_layout.addWidget(separator)
        
        # Zone de contrôle avec niveau et bouton de génération
        control_panel = QWidget()
        control_panel.setStyleSheet("background-color: #f0f5fa; border-radius: 6px; padding: 10px;")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 10, 15, 10)
        
        # Sélecteur de niveau avec style amélioré
        level_label = QLabel("Niveau de détail:")
        level_label.setFont(QFont("Segoe UI", 10))
        level_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Basic", "Normal", "Professionnel"])
        self.level_combo.setMinimumWidth(180)
        self.level_combo.setFont(QFont("Segoe UI", 10))
        
        control_layout.addWidget(level_label)
        control_layout.addWidget(self.level_combo)
        
        # Spacer pour pousser le bouton vers la droite
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Bouton générer avec style moderne
        self.generate_btn = QPushButton("Générer")
        self.generate_btn.setMinimumWidth(140)
        self.generate_btn.setMinimumHeight(36)
        self.generate_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.generate_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.generate_btn.setIconSize(QSize(18, 18))
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
            QPushButton:disabled {
                background-color: #a0c8f0;
            }
        """)
        control_layout.addWidget(self.generate_btn)
        
        main_layout.addWidget(control_panel)
        
        # Barre de progression améliorée
        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Préparation des statistiques...")
        self.status_label.setFont(QFont("Segoe UI", 9))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar, 1)
        
        self.progress_container.setVisible(False)
        main_layout.addWidget(self.progress_container)
        
        # Zone d'affichage des statistiques avec style amélioré
        self.stats_tree = QTreeWidget()
        self.stats_tree.setColumnCount(2)
        self.stats_tree.setHeaderLabels(["Statistique", "Valeur"])
        self.stats_tree.setAlternatingRowColors(True)
        self.stats_tree.setFont(QFont("Segoe UI", 10))
        
        # Configuration de l'en-tête
        header = self.stats_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        main_layout.addWidget(self.stats_tree, 1)  # 1 = stretch factor pour prendre l'espace disponible
        
        # Boutons d'action en bas
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Bouton d'exportation
        self.export_btn = QPushButton("Exporter")
        self.export_btn.setMinimumWidth(120)
        self.export_btn.setMinimumHeight(36)
        self.export_btn.setFont(QFont("Segoe UI", 10))
        self.export_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #aaa;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        button_layout.addWidget(self.export_btn)
        
        # Bouton Fermer
        self.close_btn = QPushButton("Fermer")
        self.close_btn.setMinimumWidth(120)
        self.close_btn.setMinimumHeight(36)
        self.close_btn.setFont(QFont("Segoe UI", 10))
        self.close_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #aaa;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connecte les signaux aux slots."""
        self.generate_btn.clicked.connect(self.start_statistics_thread)
        self.close_btn.clicked.connect(self.close)
        self.export_btn.clicked.connect(self.export_statistics)
    
    def start_statistics_thread(self):
        """Démarre la génération des statistiques dans un thread séparé."""
        # Désactiver le bouton générer pendant le traitement
        self.generate_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        # Afficher la barre de progression
        self.progress_container.setVisible(True)
        self.status_label.setText("Analyse du dossier en cours...")
        
        # Créer et démarrer le thread de travail
        level = self.level_combo.currentText()
        self.worker_thread = StatisticsWorkerThread(self.directory, level)
        self.worker_thread.finished.connect(self.on_statistics_ready)
        self.worker_thread.error.connect(self.on_statistics_error)
        self.worker_thread.start()
    
    def on_statistics_ready(self, stats_data):
        """
        Traite les statistiques générées par le thread.
        
        Args:
            stats_data (dict): Données des statistiques.
        """
        # Afficher les statistiques selon le niveau
        self.stats_tree.clear()
        
        level = self.level_combo.currentText()
        if level == "Basic":
            self.display_basic_stats(stats_data)
        elif level == "Normal":
            self.display_normal_stats(stats_data)
        else:  # Professionnel
            self.display_pro_stats(stats_data)
        
        # Réactiver les contrôles
        self.progress_container.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
    
    def on_statistics_error(self, error_message):
        """
        Traite les erreurs générées par le thread.
        
        Args:
            error_message (str): Message d'erreur.
        """
        # Effacer et afficher l'erreur
        self.stats_tree.clear()
        error_item = QTreeWidgetItem(["Erreur", error_message])
        error_item.setForeground(0, QColor("#d9534f"))
        error_item.setForeground(1, QColor("#d9534f"))
        error_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
        error_item.setFont(1, QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.stats_tree.addTopLevelItem(error_item)
        
        # Réactiver les contrôles
        self.progress_container.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
    
    def export_statistics(self):
        """Exporte les statistiques dans un fichier CSV ou PDF."""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Exporter les statistiques", "", "Fichiers CSV (*.csv);;Fichiers PDF (*.pdf)"
        )
        
        if file_name:
            # Implémenter l'exportation selon le format choisi
            if file_name.endswith(".csv"):
                self.export_to_csv(file_name)
            elif file_name.endswith(".pdf"):
                self.export_to_pdf(file_name)
    
    def export_to_csv(self, file_name):
        """
        Exporte les statistiques au format CSV.
        
        Args:
            file_name (str): Nom du fichier d'exportation.
        """
        try:
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Statistique", "Valeur"])
                
                # Parcourir tous les éléments du TreeWidget
                for i in range(self.stats_tree.topLevelItemCount()):
                    top_item = self.stats_tree.topLevelItem(i)
                    writer.writerow([top_item.text(0), top_item.text(1)])
                    
                    # Parcourir les enfants
                    for j in range(top_item.childCount()):
                        child = top_item.child(j)
                        writer.writerow([f"    {child.text(0)}", child.text(1)])
                        
                        # Parcourir les petits-enfants
                        for k in range(child.childCount()):
                            grandchild = child.child(k)
                            writer.writerow([f"        {grandchild.text(0)}", grandchild.text(1)])
            
            QMessageBox.information(self, "Exportation réussie", 
                                   f"Les statistiques ont été exportées avec succès dans le fichier CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'exportation", 
                                f"Erreur lors de l'exportation: {str(e)}")
    
    def export_to_pdf(self, file_name):
        """
        Exporte les statistiques au format PDF.
        
        Args:
            file_name (str): Nom du fichier d'exportation.
        """
        try:
            # Cette fonction nécessite la bibliothèque reportlab
            # Implémentation simplement esquissée ici
            QMessageBox.information(self, "Fonctionnalité à venir", 
                                   "L'exportation au format PDF sera disponible dans une prochaine version.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'exportation", 
                                f"Erreur lors de l'exportation: {str(e)}")
    
    def display_basic_stats(self, stats_data):
        """
        Affiche les statistiques du niveau Basic.
        
        Args:
            stats_data (dict): Données des statistiques basiques.
        """
        # Créer des QTreeWidgetItem avec style
        self.create_styled_group("Informations générales", [
            ("Nom du dossier", stats_data["name"]),
            ("Nombre total de fichiers", str(stats_data["total_files"])),
            ("Taille totale", stats_data["total_size_formatted"])
        ], icon=QStyle.StandardPixmap.SP_FileDialogInfoView)
        
        # Développer tous les groupes par défaut
        self.stats_tree.expandAll()
    
    def display_normal_stats(self, stats_data):
        """
        Affiche les statistiques du niveau Normal.
        
        Args:
            stats_data (dict): Données des statistiques normales.
        """
        # Informations générales
        self.create_styled_group("Informations générales", [
            ("Nom du dossier", stats_data["name"]),
            ("Nombre total de fichiers", str(stats_data["total_files"])),
            ("Taille totale", stats_data["total_size_formatted"])
        ], icon=QStyle.StandardPixmap.SP_FileDialogInfoView)
        
        # Extensions les plus fréquentes
        ext_items = [(ext, str(count)) for ext, count in stats_data["top_extensions"]]
        self.create_styled_group("Extensions les plus fréquentes", ext_items, 
                                icon=QStyle.StandardPixmap.SP_FileIcon)
        
        # Utilisation du disque
        disk_data = stats_data["disk_usage"]
        self.create_styled_group("Utilisation du disque", [
            ("Espace total", disk_data["total_formatted"]),
            ("Espace utilisé", disk_data["used_formatted"]),
            ("Espace libre", disk_data["free_formatted"]),
            ("Pourcentage utilisé", f"{disk_data['usage_percent']:.1f}%")
        ], icon=QStyle.StandardPixmap.SP_DriveHDIcon)
        
        # Développer tous les groupes par défaut
        self.stats_tree.expandAll()
    
    def display_pro_stats(self, stats_data):
        """
        Affiche les statistiques du niveau Professionnel.
        
        Args:
            stats_data (dict): Données des statistiques pro.
        """
        # Informations générales
        self.create_styled_group("Informations générales", [
            ("Nom du dossier", stats_data["name"]),
            ("Nombre total de fichiers", str(stats_data["total_files"])),
            ("Taille totale", stats_data["total_size_formatted"])
        ], icon=QStyle.StandardPixmap.SP_FileDialogInfoView)
        
        # Extensions les plus fréquentes
        ext_items = [(ext, str(count)) for ext, count in stats_data["top_extensions"]]
        self.create_styled_group("Extensions les plus fréquentes", ext_items, 
                                icon=QStyle.StandardPixmap.SP_FileIcon)
        
        # Utilisation du disque
        disk_data = stats_data["disk_usage"]
        self.create_styled_group("Utilisation du disque", [
            ("Espace total", disk_data["total_formatted"]),
            ("Espace utilisé", disk_data["used_formatted"]),
            ("Espace libre", disk_data["free_formatted"]),
            ("Pourcentage utilisé", f"{disk_data['usage_percent']:.1f}%")
        ], icon=QStyle.StandardPixmap.SP_DriveHDIcon)
        
        # Statistiques moyennes
        avg_group_items = [("Taille moyenne par fichier", stats_data["average_file_size_formatted"])]
        avg_group = self.create_styled_group("Statistiques moyennes", avg_group_items, 
                                           icon=QStyle.StandardPixmap.SP_FileDialogDetailedView)
        
        # Taille moyenne par extension (sous-groupe)
        avg_ext_items = []
        top_exts = list(stats_data["average_size_by_extension"].items())[:10]
        for ext, data in top_exts:
            avg_ext_items.append((ext, data["formatted"]))
        
        self.create_styled_subgroup(avg_group, "Taille moyenne par extension", avg_ext_items)
        
        # Les dossiers les plus volumineux
        folder_items = []
        for folder_data in stats_data["largest_folders"][:5]:
            folder_name = os.path.basename(folder_data["path"]) or folder_data["path"]
            folder_items.append((folder_name, folder_data["formatted_size"]))
        
        self.create_styled_group("Dossiers les plus volumineux", folder_items, 
                                icon=QStyle.StandardPixmap.SP_DirIcon)
        
        # Les fichiers les plus volumineux
        file_items = []
        for file_data in stats_data["largest_files"][:5]:
            file_name = os.path.basename(file_data["path"])
            file_items.append((file_name, file_data["formatted_size"]))
        
        self.create_styled_group("Fichiers les plus volumineux", file_items, 
                                icon=QStyle.StandardPixmap.SP_FileIcon)
        
        # Développer tous les groupes par défaut
        self.stats_tree.expandAll()
    
    def create_styled_group(self, title, items, icon=None):
        """
        Crée un groupe stylisé dans le TreeWidget.
        
        Args:
            title (str): Titre du groupe.
            items (list): Liste de tuples (clé, valeur).
            icon (QStyle.StandardPixmap, optional): Icône à utiliser.
            
        Returns:
            QTreeWidgetItem: L'élément du groupe créé.
        """
        group = QTreeWidgetItem([title, ""])
        group.setFont(0, QFont("Segoe UI", 11, QFont.Weight.Bold))
        group.setForeground(0, QColor("#2a82da"))
        group.setBackground(0, QColor("#f0f5fa"))
        group.setBackground(1, QColor("#f0f5fa"))
        
        if icon:
            group.setIcon(0, self.style().standardIcon(icon))
        
        self.stats_tree.addTopLevelItem(group)
        
        for key, value in items:
            item = QTreeWidgetItem([key, value])
            item.setFont(0, QFont("Segoe UI", 10))
            item.setFont(1, QFont("Segoe UI", 10))
            group.addChild(item)
        
        return group
    
    def create_styled_subgroup(self, parent_group, title, items):
        """
        Crée un sous-groupe stylisé dans le TreeWidget.
        
        Args:
            parent_group (QTreeWidgetItem): Groupe parent.
            title (str): Titre du sous-groupe.
            items (list): Liste de tuples (clé, valeur).
            
        Returns:
            QTreeWidgetItem: L'élément du sous-groupe créé.
        """
        subgroup = QTreeWidgetItem([title, ""])
        subgroup.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
        subgroup.setForeground(0, QColor("#444"))
        
        parent_group.addChild(subgroup)
        
        for key, value in items:
            item = QTreeWidgetItem([key, value])
            item.setFont(0, QFont("Segoe UI", 10))
            item.setFont(1, QFont("Segoe UI", 10))
            subgroup.addChild(item)
        
        return subgroup
    

class StatisticsWorkerThread(QThread):
    """Thread pour générer les statistiques sans bloquer l'interface principale."""
    
    # Signaux personnalisés
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, directory, level):
        """
        Initialise le thread de travail.
        
        Args:
            directory (str): Chemin du dossier à analyser.
            level (str): Niveau de détail des statistiques.
        """
        super().__init__()
        self.directory = directory
        self.level = level
    
    def run(self):
        """Exécute le thread de travail."""
        try:
            # Générer les statistiques selon le niveau
            if self.level == "Basic":
                stats_data = generate_basic_report(self.directory)
            elif self.level == "Normal":
                stats_data = generate_normal_report(self.directory)
            else:  # Professionnel
                stats_data = generate_pro_report(self.directory)
            
            # Émettre le signal avec les données
            self.finished.emit(stats_data)
            
        except Exception as e:
            # En cas d'erreur, émettre le signal d'erreur
            self.error.emit(str(e))