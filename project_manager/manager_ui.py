"""
Project Manager UI for creating and opening projects.
"""

import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QInputDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt

class ProjectManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyxel Editor - Project Manager")
        self.setGeometry(300, 300, 600, 400)
        self.recent_projects = self.load_recent_projects()
        self.editor_window = None  # Keep reference to prevent garbage collection
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("PYXEL DevBuild")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: light; font-family: 'Helvetica';" )
        layout.addWidget(title)

        # Buttons
        button_layout = QHBoxLayout()
        new_project_btn = QPushButton("New Project")
        new_project_btn.clicked.connect(self.create_new_project)
        button_layout.addWidget(new_project_btn)

        open_project_btn = QPushButton("Open Project")
        open_project_btn.clicked.connect(self.open_existing_project)
        button_layout.addWidget(open_project_btn)

        layout.addLayout(button_layout)

        # Recent Projects
        recent_label = QLabel("Recent Projects:")
        layout.addWidget(recent_label)

        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self.open_recent_project)
        self.populate_recent_projects()
        layout.addWidget(self.recent_list)

        self.setLayout(layout)

    def create_new_project(self):
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        if not ok or not project_name:
            return

        project_dir = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if not project_dir:
            return

        full_path = os.path.join(project_dir, project_name)
        if os.path.exists(full_path):
            QMessageBox.warning(self, "Error", "Project directory already exists.")
            return

        # Create folder structure
        os.makedirs(os.path.join(full_path, "assets"))
        os.makedirs(os.path.join(full_path, "scenes"))
        os.makedirs(os.path.join(full_path, "scripts"))

        # Create project.json
        project_data = {
            "name": project_name,
            "version": "1.0",
            "engine": "Pyxel3D"

        }
        with open(os.path.join(full_path, "project.json"), "w") as f:
            json.dump(project_data, f, indent=4)

        self.add_to_recent_projects(full_path)
        self.launch_editor(full_path)

    def open_existing_project(self):
        project_dir = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if not project_dir:
            return

        project_json = os.path.join(project_dir, "project.json")
        if not os.path.exists(project_json):
            QMessageBox.warning(self, "Error", "Invalid project directory. No project.json found.")
            return

        self.add_to_recent_projects(project_dir)
        self.launch_editor(project_dir)

    def open_recent_project(self, item):
        project_path = item.data(Qt.UserRole)
        if os.path.exists(project_path):
            self.launch_editor(project_path)
        else:
            QMessageBox.warning(self, "Error", "Project directory no longer exists.")
            self.recent_projects.remove(project_path)
            self.save_recent_projects()
            self.populate_recent_projects()

    def populate_recent_projects(self):
        self.recent_list.clear()
        for path in self.recent_projects:
            if os.path.exists(path):
                project_name = os.path.basename(path)
                item = QListWidgetItem(project_name)
                item.setData(Qt.UserRole, path)
                self.recent_list.addItem(item)

    def add_to_recent_projects(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        self.recent_projects = self.recent_projects[:10]  # Keep only 10 recent
        self.save_recent_projects()
        self.populate_recent_projects()

    def load_recent_projects(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".panda_editor")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "recent_projects.json")
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                return json.load(f)
        return []

    def save_recent_projects(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".panda_editor")
        config_file = os.path.join(config_dir, "recent_projects.json")
        with open(config_file, "w") as f:
            json.dump(self.recent_projects, f)

    def launch_editor(self, project_path):
        # Launch the main editor window with the project path
        import sys
        import os
        # Add project root to Python path so 'engine' and 'editor' packages can be found
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        self.hide()
        from editor.main_window import MainWindow
        self.editor_window = MainWindow(project_path)
        self.editor_window.show()