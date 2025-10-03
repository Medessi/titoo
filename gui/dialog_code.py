from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

def show_info_dialog():
    """
    Affiche une boîte de dialogue professionnelle à propos de TITO.
    """
    # Création de la boîte de dialogue
    about_dialog = QDialog()
    about_dialog.setWindowTitle("À propos de TITO")
    about_dialog.setMinimumSize(600, 600)
    about_dialog.setStyleSheet("""
        QDialog {
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        QLabel {
            font-family: 'Segoe UI', sans-serif;
            font-size: 12pt;
            color: #2c3e50;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
    """)
    about_dialog.setWindowIcon(QIcon("assets/logo/logo.svg"))

    # Mise en page
    layout = QVBoxLayout(about_dialog)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)

    # Contenu HTML
    content_html = """
    <div style="line-height: 1.6; font-family: 'Segoe UI', sans-serif;">
        <div style="text-align: center;">
            <h1 style="font-size: 20px; color: #ffd700; margin-bottom: 5px;">TITO</h1>
            <h2 style="font-size: 14px; color: #191970; margin-top: 0;">Solutiond'organisation de fichiers</h2>
            <p style="color: #7f8c8d; font-style: italic;">Version 1.0 stable • 2025</p>
        </div>

        <hr style="margin: 10px 0; border: none; border-top: 1px solid #bdc3c7;"/>

        <p><strong style="color: #191970;">Développé par :</strong> MIDEESSI</p>
        <p><strong style="color: #191970;">Licence :</strong> VTO</p>

        <p><strong style="color: #191970;">Description :</strong><br>
        TITO est une solution logicielle conçue pour automatiser l’organisation de vos fichiers selon des critères personnalisés (date, type, nom, etc.). Grâce à son système d’historique intelligent, vous pouvez annuler ou restaurer toutes les actions effectuées.</p>

       

        <p><strong style="color: #191970;">Startup :</strong> TITO – Une initiative indépendante propulsée par <strong style = "color: #191970;">MIDEESSI</strong></p>

        <p><strong style="color: #191970;">Contact :</strong><br>
        <a href="mailto:mideessi_tmp@gmail.com" style="color: #3498db; text-decoration: none;">
        mideessi_tmp@gmail.com</a></p>
    </div>
    """

    content_label = QLabel()
    content_label.setText(content_html)
    content_label.setTextFormat(Qt.TextFormat.RichText)
    content_label.setOpenExternalLinks(True)
    content_label.setWordWrap(True)
    layout.addWidget(content_label)

    # Bouton de fermeture
    close_button = QPushButton("Fermer")
    close_button.clicked.connect(about_dialog.accept)
    layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

    # Affichage modal
    about_dialog.setModal(True)
    about_dialog.exec()
