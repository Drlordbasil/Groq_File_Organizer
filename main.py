import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from organizer.file_organizer import FileOrganizer
from config import Config

def main():
    config = Config()
    file_organizer = FileOrganizer(config)
    
    app = QApplication(sys.argv)
    main_window = MainWindow(file_organizer)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()