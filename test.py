#!/usr/bin/env python3
"""
Test script to verify basic functionality without GUI.
"""

import sys
import os

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import all required modules
try:
    from core.project_data import ProjectData
    from engine.panda_app import PandaApp
    PROJECT_DATA_AVAILABLE = True
    PANDA_APP_AVAILABLE = True
except ImportError:
    PROJECT_DATA_AVAILABLE = False
    PANDA_APP_AVAILABLE = False

def test_imports():
    try:
        from project_manager.manager_ui import ProjectManagerWindow
        from editor.main_window import MainWindow
        from engine.panda_app import PandaApp
        from engine.viewport_widget import ViewportWidget
        from engine.editor_camera import EditorCamera
        from editor.hierarchy_panel import HierarchyPanel
        from editor.inspector_panel import InspectorPanel
        from editor.asset_browser import AssetBrowser
        from core.project_data import ProjectData
        from core.scene_manager import SceneManager
        print("[PASS] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_project_data():
    if not PROJECT_DATA_AVAILABLE:
        print("[FAIL] Project data test failed: ProjectData import failed")
        return False

    try:
        import tempfile
        import shutil

        # Create a temporary project directory
        temp_dir = tempfile.mkdtemp()
        project_data = ProjectData(temp_dir)

        # Check properties
        assert project_data.name == "Unnamed Project"
        assert project_data.version == "1.0"
        assert project_data.assets_path == os.path.join(temp_dir, "assets")
        assert project_data.scenes_path == os.path.join(temp_dir, "scenes")
        assert project_data.scripts_path == os.path.join(temp_dir, "scripts")

        # Clean up
        shutil.rmtree(temp_dir)
        print("[PASS] Project data test passed")
        return True
    except Exception as e:
        print(f"[FAIL] Project data test failed: {e}")
        return False

def test_panda_app():
    if not PANDA_APP_AVAILABLE:
        print("[FAIL] Panda3D app test failed: PandaApp import failed")
        return False

    try:
        # Test basic Panda3D app creation
        from panda3d.core import loadPrcFileData
        loadPrcFileData('', 'window-type none')  # Headless mode

        app = PandaApp()
        assert app.render is not None
        app.destroy()
        print("[PASS] Panda3D app test passed")
        return True
    except Exception as e:
        print(f"[FAIL] Panda3D app test failed: {e}")
        return False

def test_project_data():
    try:
        import tempfile
        import shutil

        # Create a temporary project directory
        temp_dir = tempfile.mkdtemp()
        project_data = ProjectData(temp_dir)

        # Check properties
        assert project_data.name == "Unnamed Project"
        assert project_data.version == "1.0"
        assert project_data.assets_path == os.path.join(temp_dir, "assets")
        assert project_data.scenes_path == os.path.join(temp_dir, "scenes")
        assert project_data.scripts_path == os.path.join(temp_dir, "scripts")

        # Clean up
        shutil.rmtree(temp_dir)
        print("[PASS] Project data test passed")
        return True
    except Exception as e:
        print(f"[FAIL] Project data test failed: {e}")
        return False

def test_panda_app():
    try:
        # Test basic Panda3D app creation
        from panda3d.core import loadPrcFileData
        loadPrcFileData('', 'window-type none')  # Headless mode

        app = PandaApp()
        assert app.render is not None
        app.destroy()
        print("[PASS] Panda3D app test passed")
        return True
    except Exception as e:
        print(f"[FAIL] Panda3D app test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running Panda3D Editor tests...\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_project_data()
    all_passed &= test_panda_app()

    if all_passed:
        print("\n[PASS] All tests passed! The editor should work correctly.")
    else:
        print("\n[FAIL] Some tests failed. Please check the errors above.")