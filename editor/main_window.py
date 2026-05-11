"""
Main Editor Window with dockable panels.
"""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QLabel, QTreeView,
    QFormLayout, QLineEdit, QFileSystemModel, QTreeView as QFileTreeView, QToolBar, QTabWidget
)
from PySide6.QtCore import Qt
from panda3d.core import BitMask32
from PySide6.QtGui import QAction
from engine.viewport_widget import ViewportWidget
from core.project_data import ProjectData
from editor.hierarchy_panel import HierarchyPanel
from editor.inspector_panel import InspectorPanel
from editor.asset_browser import AssetBrowser
from editor.console_panel import ConsolePanel
from editor.event_sheet_panel import EventSheetWidget
from engine.gizmo_manager import GizmoManager
from engine.primitives_generator import PrimitivesGenerator
from engine.core.game_loop import game_loop
from engine.core.event_sheet_processor import EventSheetProcessor
from engine.core.scene_manager import scene_manager
from engine.core.command_system import history
from editor.editor_commands import CreateObjectCommand, DeleteObjectCommand

class MainWindow(QMainWindow):
    def __init__(self, project_path):
        super().__init__()
        self.project_data = ProjectData(project_path)
        self.setWindowTitle(f"Pyxel Editor - {self.project_data.name}")
        self.setGeometry(100, 100, 1200, 800)
        self.clipboard_data = None
        self.event_clipboard = None
        self.init_ui()
        self.load_project()

    def copy_selected_object(self):
        """Serializes the currently selected object to the clipboard."""
        go = self.hierarchy_panel.selected_game_object
        if go:
            self.clipboard_data = {
                "data": go.serialize(),
                "node_path": go.node_path,
                "source_uuid": go.uuid
            }
            sys.stderr.write(f"DEBUG [MainWindow]: Copied object '{go.name}' to clipboard.\n")

    def paste_object(self):
        """Creates a new object from the clipboard data via a command."""
        if self.clipboard_data:
            import re
            data = self.clipboard_data["data"]
            source_np = self.clipboard_data["node_path"]
            source_uuid = self.clipboard_data.get("source_uuid")

            # Increment name logic
            original_name = data.get("name", "GameObject")
            base_name = re.sub(r"\s\(\d+\)$", "", original_name)
            existing_names = [go.name for go in scene_manager.game_objects]
            
            count = 1
            new_name = f"{base_name} ({count})"
            while new_name in existing_names:
                count += 1
                new_name = f"{base_name} ({count})"
            
            data["name"] = new_name
            
            # Use Command for Undo/Redo
            from panda3d.core import Vec3
            cmd = CreateObjectCommand(self, data, visual_source_np=source_np, offset=Vec3(0.5, 0.5, 0))
            history.execute(cmd)

            # Clone event blocks if necessary
            if source_uuid and self.event_sheet_processor and cmd.created_go:
                self._clone_event_blocks(source_uuid, cmd.created_go.uuid)
            
            sys.stderr.write(f"DEBUG [MainWindow]: Pasted object '{new_name}' via command.\n")

    def _clone_event_blocks(self, old_uuid, new_uuid):
        """Finds event blocks referencing old_uuid, deep-clones them with new_uuid."""
        import copy
        from engine.core.event_sheet_processor import EventBlockData

        blocks_to_clone = []
        for block in self.event_sheet_processor.event_blocks:
            references_old = False
            for action in block.actions:
                if getattr(action, 'game_object_uuid', None) == old_uuid:
                    references_old = True
                    break
            if references_old:
                blocks_to_clone.append(block)

        for original_block in blocks_to_clone:
            new_block = EventBlockData()

            # Deep-clone conditions
            for cond in original_block.conditions:
                new_cond = copy.deepcopy(cond)
                new_block.conditions.append(new_cond)

            # Deep-clone actions and replace uuid
            for action in original_block.actions:
                new_action = copy.deepcopy(action)
                if getattr(new_action, 'game_object_uuid', None) == old_uuid:
                    new_action.game_object_uuid = new_uuid
                new_block.actions.append(new_action)

            # Register with processor
            self.event_sheet_processor.add_block(new_block)

            # Add visual row to event sheet UI
            self.event_sheet.add_block_widget(new_block)

    def delete_selected_object(self):
        """Destroys the currently selected object via a command."""
        go = self.hierarchy_panel.selected_game_object
        if go:
            cmd = DeleteObjectCommand(self, go)
            history.execute(cmd)
            sys.stderr.write(f"DEBUG [MainWindow]: Deleted object '{go.name}' via command.\n")

    def init_ui(self):
        # Central widget: Tabs
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Tab 1: Viewport
        self.viewport = ViewportWidget()
        self.tab_widget.addTab(self.viewport, "Layout 1")

        # Event Sheet Processor (runtime executor)
        self.event_sheet_processor = EventSheetProcessor(scene_manager)
        self.viewport.event_sheet_processor = self.event_sheet_processor

        # Tab 2: Event Sheet
        self.event_sheet = EventSheetWidget(
            processor=self.event_sheet_processor,
            scene_manager=scene_manager,
        )
        self.tab_widget.addTab(self.event_sheet, "Event sheet 1")

        # Gizmo Manager (needs to be created before toolbar)
        self.gizmo_manager = GizmoManager(self.viewport.panda_app)
        self.viewport.gizmo_manager = self.gizmo_manager

        # Create panels
        self.hierarchy_panel = HierarchyPanel()
        self.inspector_panel = InspectorPanel()
        
        # Hierarchy tree should not steal focus from viewport
        self.hierarchy_panel.tree_widget.setFocusPolicy(Qt.NoFocus)

        # Connect gizmo manager to panels
        self.gizmo_manager.inspector_panel = self.inspector_panel
        self.gizmo_manager.selection_callback = self.on_scene_selection

        # Toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)

        self.select_action = QAction("Select (Q)", self)
        self.select_action.triggered.connect(lambda: self.set_tool("select"))
        self.toolbar.addAction(self.select_action)

        self.translate_action = QAction("Translate (W)", self)
        self.translate_action.triggered.connect(lambda: self.set_tool("translate"))
        self.toolbar.addAction(self.translate_action)

        self.rotate_action = QAction("Rotate (E)", self)
        self.rotate_action.triggered.connect(lambda: self.set_tool("rotate"))
        self.toolbar.addAction(self.rotate_action)

        self.scale_action = QAction("Scale (R)", self)
        self.scale_action.triggered.connect(lambda: self.set_tool("scale"))
        self.toolbar.addAction(self.scale_action)

        self.toolbar.addSeparator()

        self.play_action = QAction("Play", self)
        self.play_action.triggered.connect(game_loop.play)
        self.toolbar.addAction(self.play_action)

        self.pause_action = QAction("Pause", self)
        self.pause_action.triggered.connect(game_loop.pause)
        self.toolbar.addAction(self.pause_action)

        self.stop_action = QAction("Stop", self)
        self.stop_action.triggered.connect(game_loop.stop)
        self.toolbar.addAction(self.stop_action)

        # Prevent toolbar and its buttons from stealing focus
        self.toolbar.setFocusPolicy(Qt.NoFocus)
        for action in self.toolbar.actions():
            widget = self.toolbar.widgetForAction(action)
            if widget:
                widget.setFocusPolicy(Qt.NoFocus)

        self.current_tool = "select"

        # Register for game loop state changes
        game_loop.register_state_callback(self.update_play_mode_ui)
        self.update_play_mode_ui(game_loop.state)

        # Hierarchy Dock (Left)
        self.hierarchy_dock = QDockWidget("Hierarchy")
        self.hierarchy_dock.setWidget(self.hierarchy_panel)
        self.hierarchy_dock.setFocusPolicy(Qt.NoFocus)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.hierarchy_dock)

        # Inspector Dock (Right)
        self.inspector_dock = QDockWidget("Inspector")
        self.inspector_dock.setWidget(self.inspector_panel)
        self.inspector_dock.setFocusPolicy(Qt.NoFocus)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)

        # Asset Browser Dock (Bottom)
        self.asset_dock = QDockWidget("Asset Browser")
        self.asset_browser = AssetBrowser(self.project_data.project_path)
        self.asset_browser.tree_view.setFocusPolicy(Qt.NoFocus)
        self.asset_dock.setWidget(self.asset_browser)
        self.asset_dock.setFocusPolicy(Qt.NoFocus)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.asset_dock)

        # Console Dock (Bottom)
        self.console_dock = QDockWidget("Console")
        self.console_panel = ConsolePanel()
        self.console_dock.setWidget(self.console_panel)
        self.console_dock.setFocusPolicy(Qt.NoFocus)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)

        # Connect signals
        self.hierarchy_panel.node_selected.connect(self.inspector_panel.set_node)
        self.hierarchy_panel.node_selected.connect(
            lambda go: self.gizmo_manager.set_selected_node(go.node_path) if go else self.gizmo_manager.set_selected_node(None)
        )
        self.hierarchy_panel.node_selected.connect(
            lambda go: self.viewport.update_outline(go.node_path) if go else self.viewport.update_outline(None)
        )
        self.hierarchy_panel.create_primitive_signal.connect(self.create_primitive)
        self.asset_browser.model_loaded.connect(self.load_model)
        self.viewport.object_selected_signal.connect(self.inspector_panel.set_node)
        self.viewport.object_moved_signal.connect(lambda node: self.inspector_panel.update_values() if self.inspector_panel.current_game_object and self.inspector_panel.current_game_object.node_path == node else None)

        # Connect viewport hotkey signal
        self.viewport.hotkey_triggered.connect(self.handle_viewport_hotkey)

        self.setup_menu_bar()

    def set_tool(self, tool):
        self.current_tool = tool
        self.gizmo_manager.set_mode(tool)

        # Force hover reset so it highlights the new tool immediately
        if hasattr(self, 'viewport') and self.viewport:
            self.viewport.hovered_axis = "NEEDS_RESET"

    def tool_select_mode(self):
        self.set_tool("select")

    def tool_translate_mode(self):
        self.set_tool("translate")

    def tool_rotate_mode(self):
        self.set_tool("rotate")

    def tool_scale_mode(self):
        self.set_tool("scale")

    def focus_camera_on_selection(self):
        if hasattr(self, 'viewport'):
            self.viewport.focus_on_selected()

    def handle_viewport_hotkey(self, key_str):
        """Route hotkey signals from the viewport to tool actions."""
        if key_str == 'Q':
            self.tool_select_mode()
        elif key_str == 'W':
            self.tool_translate_mode()
        elif key_str == 'E':
            self.tool_rotate_mode()
        elif key_str == 'R':
            self.tool_scale_mode()
        elif key_str == 'F':
            self.focus_camera_on_selection()

    def update_play_mode_ui(self, state):
        """Update toolbar button colors based on engine state."""
        from engine.core.game_loop import EngineState
        # Reset all buttons to default
        self.toolbar.widgetForAction(self.play_action).setStyleSheet("")
        self.toolbar.widgetForAction(self.pause_action).setStyleSheet("")
        self.toolbar.widgetForAction(self.stop_action).setStyleSheet("")

        if state == EngineState.PLAYING:
            self.toolbar.widgetForAction(self.play_action).setStyleSheet("background-color: #4CAF50; color: white;")
        elif state == EngineState.PAUSED:
            self.toolbar.widgetForAction(self.pause_action).setStyleSheet("background-color: #FF9800; color: white;")

    def on_scene_selection(self, node_path):
        """Handle selection of scene objects from viewport raycast."""
        if node_path is None:
            return
        go_np = node_path.findNetPythonTag("game_object")
        if not go_np.isEmpty():
            game_object = go_np.getPythonTag("game_object")
            self.hierarchy_panel.select_node(game_object)

    def select_translate_tool(self):
        self.set_tool("translate")

    def select_rotate_tool(self):
        self.set_tool("rotate")

    def select_scale_tool(self):
        self.set_tool("scale")

    def trigger_focus(self):
        if hasattr(self, 'viewport'):
            self.viewport.focus_on_selected()

    def load_model(self, file_path):
        # Load the model into the scene
        from engine.core.game_object import GameObject
        from engine.components.mesh_renderer import MeshRendererComponent
        from panda3d.core import BitMask32

        sys.stderr.write(f"DEBUG [MainWindow]: Loading model from {file_path}\n")
        game_object = GameObject(name=file_path.split("/")[-1].split("\\")[-1])
        sys.stderr.write(f"DEBUG [MainWindow]: Created GameObject ID {game_object.id}, Object ID: {id(game_object)}\n")
        
        mesh_renderer = game_object.add_component(MeshRendererComponent)
        mesh_renderer.model_path = file_path
        
        game_object.node_path.reparentTo(self.viewport.panda_app.render)
        self.hierarchy_panel.update_hierarchy()
        self.hierarchy_panel.select_node(game_object)

    def setup_menu_bar(self):
        """Initializes the top menu bar with File, Edit, and View menus."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1e1e1e;
                color: #cccccc;
                border-bottom: 1px solid #333333;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
            }
            QMenuBar::item:selected {
                background-color: #333333;
                color: #ffffff;
            }
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #454545;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
        """)

        # --- File Menu ---
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Project", lambda: print("Action: New Project"))
        file_menu.addAction("Open Project", lambda: print("Action: Open Project"))
        file_menu.addSeparator()
        file_menu.addAction("Save", self.save_project).setShortcut("Ctrl+S")
        file_menu.addAction("Save As...", lambda: print("Action: Save As"))
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # --- Edit Menu ---
        edit_menu = menubar.addMenu("Edit")
        undo_act = edit_menu.addAction("Undo", history.undo)
        undo_act.setShortcut("Ctrl+Z")
        redo_act = edit_menu.addAction("Redo", history.redo)
        redo_act.setShortcut("Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("Copy", self.copy_selected_object).setShortcut("Ctrl+C")
        edit_menu.addAction("Paste", self.paste_object).setShortcut("Ctrl+V")
        edit_menu.addAction("Delete", self.delete_selected_object).setShortcut("Del")

        # --- View Menu ---
        view_menu = menubar.addMenu("View")
        
        # Sub-menu for UI Elements
        ui_menu = view_menu.addMenu("UI Elements")
        ui_menu.addAction(self.hierarchy_dock.toggleViewAction())
        ui_menu.addAction(self.inspector_dock.toggleViewAction())
        ui_menu.addAction(self.asset_dock.toggleViewAction())
        ui_menu.addAction(self.console_dock.toggleViewAction())
        ui_menu.addSeparator()
        ui_menu.addAction(self.toolbar.toggleViewAction())
        
        view_menu.addSeparator()
        view_menu.addAction("Toggle Grid", self._on_toggle_grid)
        full_act = view_menu.addAction("Fullscreen", self._toggle_fullscreen)
        full_act.setShortcut("F11")

    def _toggle_fullscreen(self):
        """Toggle between fullscreen and normal windowed mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_toggle_grid(self):
        """Toggle the 3D editor grid."""
        if hasattr(self, 'viewport') and self.viewport.panda_app:
            if hasattr(self.viewport.panda_app, 'editor_grid'):
                self.viewport.panda_app.editor_grid.toggle()

    def create_primitive(self, shape_name):
        """Create a primitive shape and add it to the scene."""
        from engine.core.game_object import GameObject
        from engine.components.mesh_renderer import MeshRendererComponent

        if shape_name not in ["Cube", "Sphere", "Capsule"]:
            return

        sys.stderr.write(f"DEBUG [MainWindow]: Creating primitive '{shape_name}'\n")
        game_object = GameObject(name=shape_name)
        sys.stderr.write(f"DEBUG [MainWindow]: Created GameObject ID {game_object.id}, Object ID: {id(game_object)}\n")
        
        mesh_renderer = game_object.add_component(MeshRendererComponent)
        mesh_renderer.model_path = f"Primitive:{shape_name}"
        
        game_object.node_path.reparentTo(self.viewport.panda_app.render)
        self.hierarchy_panel.update_hierarchy()
        self.hierarchy_panel.select_node(game_object)

    def save_project(self):
        """Serializes the entire project state and saves it to disk."""
        sys.stderr.write("DEBUG [MainWindow]: Saving project...\n")
        
        # 1. Serialize GameObjects
        scene_data = []
        for go in scene_manager.game_objects:
            # Skip editor-only objects if any
            scene_data.append(go.serialize())
        
        # 2. Serialize Event Blocks
        event_data = []
        if self.event_sheet_processor:
            for block in self.event_sheet_processor.event_blocks:
                event_data.append(block.to_dict())
                
        # 3. Update ProjectData
        self.project_data.data["scene"] = scene_data
        self.project_data.events_data = event_data
        
        # 4. Save to file
        self.project_data.save()
        sys.stderr.write("DEBUG [MainWindow]: Project saved successfully.\n")

    def load_project(self):
        """Loads the project state from disk and reconstructs the scene and events."""
        data = self.project_data.data
        if not data:
            return

        sys.stderr.write("DEBUG [MainWindow]: Loading project...\n")
        
        # 1. Clear current state (if any)
        # (For now we assume it's a fresh start)
        
        # 2. Load GameObjects
        scene_data = data.get("scene", [])
        from engine.core.game_object import GameObject
        from panda3d.core import BitMask32
        
        for go_data in scene_data:
            go = GameObject.create_from_data(go_data)
            go.node_path.reparentTo(self.viewport.panda_app.render)
            go.node_path.setCollideMask(BitMask32.bit(1))
            
        self.hierarchy_panel.update_hierarchy()
        
        # 3. Load Event Blocks
        event_data = self.project_data.events_data
        from engine.core.event_sheet_processor import EventBlockData
        
        for block_dict in event_data:
            block = EventBlockData.from_dict(block_dict)
            if block:
                self.event_sheet_processor.add_block(block)
                self.event_sheet.add_block_widget(block)
                
        sys.stderr.write("DEBUG [MainWindow]: Project loaded successfully.\n")