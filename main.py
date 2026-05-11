#!/usr/bin/env python3
"""
Entry point for the Panda3D Editor application.
Launches the Project Manager window.
"""

import sys
import os

# Add project root to Python path for package imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Inject local Panda3D build path before any Panda3D imports
_local_panda_build = os.path.join(project_root, 'core_engine', 'built')
if os.path.exists(_local_panda_build):
    sys.path.insert(0, _local_panda_build)
    print(f"Using local engine build at: {_local_panda_build}")
else:
    print(f"WARNING: Local engine build not found at {_local_panda_build}")
    print("Please run build_engine_simple.bat to build the engine from source.")

from PySide6.QtWidgets import QApplication
from project_manager.manager_ui import ProjectManagerWindow
from editor.theme import EDITOR_THEME

def main():
    try:
        print("Starting QApplication...")
        app = QApplication(sys.argv)
        # Prevent application from quitting when last window is closed
        app.setQuitOnLastWindowClosed(False)
        # Apply the editor theme globally
        app.setStyleSheet(EDITOR_THEME)
        print("Creating ProjectManagerWindow...")
        window = ProjectManagerWindow()
        print("Showing window...")
        window.show()
        print("Starting up...")
        result = app.exec()
        print(f"exited with {result}")
        sys.exit(result)
    except Exception as e:
        print(f"Exception in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
