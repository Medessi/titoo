import sys
import os
import json
import threading
import socket
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QFileDialog, QListWidget, 
                            QTextEdit, QTabWidget, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import webbrowser

class ServerSignals(QObject):
    status_changed = pyqtSignal(str)
    file_requested = pyqtSignal(str)

class SwitchSyncServer:
    def __init__(self, signals):
        self.app = Flask(__name__)
        CORS(self.app)
        self.signals = signals
        self.shared_files = {}
        self.current_state = {"type": "none", "data": ""}
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/api/status')
        def status():
            return jsonify({"status": "running", "device": "PC"})
        
        @self.app.route('/api/files')
        def get_files():
            return jsonify(self.shared_files)
        
        @self.app.route('/api/files/<file_id>')
        def serve_file(file_id):
            if file_id in self.shared_files:
                file_path = self.shared_files[file_id]['path']
                self.signals.file_requested.emit(file_path)
                return send_file(file_path)
            return jsonify({"error": "File not found"}), 404
        
        @self.app.route('/api/sync', methods=['POST'])
        def sync_state():
            data = request.get_json()
            if data:
                self.current_state = data
                self.signals.status_changed.emit(f"Sync received: {data.get('type', 'unknown')}")
            return jsonify({"status": "success"})
        
        @self.app.route('/api/sync', methods=['GET'])
        def get_sync_state():
            return jsonify(self.current_state)
        
        @self.app.route('/api/browser', methods=['POST'])
        def sync_browser():
            data = request.get_json()
            url = data.get('url', '')
            if url:
                webbrowser.open(url)
                self.signals.status_changed.emit(f"Opening URL: {url}")
            return jsonify({"status": "success"})
    
    def add_file(self, file_path):
        file_id = str(len(self.shared_files) + 1)
        file_name = os.path.basename(file_path)
        self.shared_files[file_id] = {
            "name": file_name,
            "path": file_path,
            "size": os.path.getsize(file_path)
        }
        return file_id
    
    def remove_file(self, file_id):
        if file_id in self.shared_files:
            del self.shared_files[file_id]
    
    def update_sync_state(self, state_type, data):
        self.current_state = {"type": state_type, "data": data}

class SwitchSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signals = ServerSignals()
        self.server = SwitchSyncServer(self.signals)
        self.server_thread = None
        self.init_ui()
        self.setup_signals()
        self.setup_tray()
        
    def init_ui(self):
        self.setWindowTitle("SwitchSync - PC")
        self.setGeometry(100, 100, 500, 600)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Status
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        layout.addWidget(self.status_label)
        
        # Contrôles serveur
        server_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        
        server_layout.addWidget(self.start_btn)
        server_layout.addWidget(self.stop_btn)
        layout.addLayout(server_layout)
        
        # Onglets
        tabs = QTabWidget()
        
        # Onglet Fichiers
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        
        files_controls = QHBoxLayout()
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        remove_file_btn = QPushButton("Remove File")
        remove_file_btn.clicked.connect(self.remove_file)
        
        files_controls.addWidget(add_file_btn)
        files_controls.addWidget(remove_file_btn)
        files_layout.addLayout(files_controls)
        
        self.files_list = QListWidget()
        files_layout.addWidget(self.files_list)
        
        tabs.addTab(files_tab, "Files")
        
        # Onglet Sync
        sync_tab = QWidget()
        sync_layout = QVBoxLayout(sync_tab)
        
        sync_controls = QHBoxLayout()
        sync_url_btn = QPushButton("Sync Current URL")
        sync_url_btn.clicked.connect(self.sync_current_url)
        
        sync_controls.addWidget(sync_url_btn)
        sync_layout.addLayout(sync_controls)
        
        self.sync_log = QTextEdit()
        self.sync_log.setReadOnly(True)
        self.sync_log.setMaximumHeight(200)
        sync_layout.addWidget(QLabel("Sync Log:"))
        sync_layout.addWidget(self.sync_log)
        
        tabs.addTab(sync_tab, "Sync")
        
        layout.addWidget(tabs)
        
        # IP Info
        self.ip_label = QLabel("Server will run on: http://localhost:5000")
        self.ip_label.setStyleSheet("QLabel { color: blue; }")
        layout.addWidget(self.ip_label)
        
    def setup_signals(self):
        self.signals.status_changed.connect(self.update_status)
        self.signals.file_requested.connect(self.log_file_request)
        
    def setup_tray(self):
        # Créer une icône simple
        self.tray_icon = QSystemTrayIcon(self)
        
        # Menu du tray
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            return
            
        self.server_thread = threading.Thread(
            target=lambda: self.server.app.run(host='0.0.0.0', port=5000, debug=False)
        )
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Obtenir l'IP locale
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"Server running on: http://{local_ip}:5000")
        except:
            self.ip_label.setText("Server running on: http://localhost:5000")
        
    def stop_server(self):
        # Note: Flask dev server cannot be stopped programmatically easily
        # In production, you'd use a proper WSGI server
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select file to share",
            "",
            "All Files (*)"
        )
        
        if file_path:
            file_id = self.server.add_file(file_path)
            file_name = os.path.basename(file_path)
            self.files_list.addItem(f"{file_id}: {file_name}")
            self.update_status(f"Added file: {file_name}")
    
    def remove_file(self):
        current_item = self.files_list.currentItem()
        if current_item:
            file_id = current_item.text().split(':')[0]
            self.server.remove_file(file_id)
            self.files_list.takeItem(self.files_list.row(current_item))
            self.update_status(f"Removed file ID: {file_id}")
    
    def sync_current_url(self):
        # Simulation - dans la vraie version, on récupèrerait l'URL du navigateur
        url = "https://example.com"
        self.server.update_sync_state("browser", {"url": url})
        self.update_status(f"Synced URL: {url}")
    
    def update_status(self, message):
        self.sync_log.append(f"[{self.get_current_time()}] {message}")
        
    def log_file_request(self, file_path):
        self.update_status(f"File requested: {os.path.basename(file_path)}")
        
    def get_current_time(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        
    def quit_app(self):
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = SwitchSyncApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()