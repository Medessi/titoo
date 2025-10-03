
# -*- coding: utf-8 -*-


from PyQt6.QtWidgets import QApplication
from gui.main_window import FileManager 
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec())