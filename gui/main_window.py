import os
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QFileDialog, QTextEdit, QWidget, QProgressBar, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class OrganizerThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)

    def __init__(self, file_organizer, folder_path):
        super().__init__()
        self.file_organizer = file_organizer
        self.folder_path = folder_path

    def run(self):
        total_files = sum([len(files) for r, d, files in os.walk(self.folder_path)])
        processed_files = 0

        def process_callback(message):
            nonlocal processed_files
            processed_files += 1
            progress = int((processed_files / total_files) * 100)
            self.update_progress.emit(progress)
            self.update_log.emit(message)

        self.file_organizer.organize_folder(self.folder_path, process_callback)

class MainWindow(QMainWindow):
    def __init__(self, file_organizer):
        super().__init__()
        self.file_organizer = file_organizer
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('AI File Organizer')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.select_folder_button = QPushButton('Select Folder')
        self.select_folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_folder_button)

        self.organize_button = QPushButton('Organize Files')
        self.organize_button.clicked.connect(self.organize_files)
        layout.addWidget(self.organize_button)

        self.undo_button = QPushButton('Undo Changes')
        self.undo_button.clicked.connect(self.undo_changes)
        layout.addWidget(self.undo_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel('Ready')
        layout.addWidget(self.status_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.log_text.append(f"Selected folder: {folder}")
            self.selected_folder = folder

    def organize_files(self):
        if hasattr(self, 'selected_folder'):
            self.log_text.append("Organizing files...")
            self.progress_bar.setValue(0)
            self.status_label.setText('Organizing...')
            self.organizer_thread = OrganizerThread(self.file_organizer, self.selected_folder)
            self.organizer_thread.update_progress.connect(self.update_progress)
            self.organizer_thread.update_log.connect(self.update_log)
            self.organizer_thread.finished.connect(self.organization_complete)
            self.organizer_thread.start()
        else:
            self.log_text.append("Please select a folder first.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_text.append(message)

    def organization_complete(self):
        self.log_text.append("Organization complete!")
        self.status_label.setText('Ready')

    def undo_changes(self):
        self.log_text.append("Undoing changes...")
        self.file_organizer.undo_changes()
        self.log_text.append("Changes undone!")