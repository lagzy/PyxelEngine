from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QToolButton, QMenu
from PySide6.QtCore import Qt, Signal
from engine.core.scene_manager import scene_manager
from engine.core.game_object import GameObject
from engine.components.mesh_renderer import MeshRendererComponent
from engine.components.directional_light import DirectionalLightComponent
from engine.components.point_light import PointLightComponent
from engine.components.spot_light import SpotLightComponent
from engine.components.camera_component import CameraComponent
from engine.components.rigidbody_component import RigidbodyComponent
from engine.components.box_collider import BoxColliderComponent
from engine.components.sphere_collider import SphereColliderComponent
from engine.components.capsule_collider import CapsuleColliderComponent
from engine.components.mesh_collider import MeshColliderComponent
import sys

class HierarchyPanel(QWidget):
    node_selected = Signal(object)  # GameObject
    create_primitive_signal = Signal(str)  # Primitive type name

    def __init__(self):
        super().__init__()
        self.node_map = {}  # Map tree items to GameObject id
        self.selected_game_object = None
        self.init_ui()
        self.update_hierarchy()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Top bar with add button only (title provided by QDockWidget)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        top_bar.addStretch()

        # 1. Use QToolButton (ignores native OS margins)
        self.add_button = QToolButton()
        self.add_button.setText("+")
        self.add_button.setFixedSize(24, 24)

        # 2. Strict Inline CSS to override ALL global theme padding
        self.add_button.setStyleSheet("""
            QToolButton {
                background-color: #1c2b6e;
                color: #ffffff;
                font-family: Arial;
                font-size: 16px; /* Slightly smaller to guarantee fit */
                font-weight: bold;
                border: 1px solid #253993;
                border-radius: 3px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:hover {
                background-color: #253993;
            }
        """)

        # 3. Create the menu (NOT using setMenu!)
        self.add_menu = QMenu()

        objects_menu = self.add_menu.addMenu("3D Object")
        objects_menu.addAction("Cube", lambda: self.create_primitive_signal.emit("Cube"))
        objects_menu.addAction("Sphere", lambda: self.create_primitive_signal.emit("Sphere"))
        objects_menu.addAction("Capsule", lambda: self.create_primitive_signal.emit("Capsule"))

        render_menu = self.add_menu.addMenu("Render")
        render_menu.addAction("Directional Light", lambda: self.create_new_gameobject("Directional Light", DirectionalLightComponent))
        render_menu.addAction("Point Light", lambda: self.create_new_gameobject("Point Light", PointLightComponent))
        render_menu.addAction("Spot Light", lambda: self.create_new_gameobject("Spot Light", SpotLightComponent))
        render_menu.addAction("Camera", lambda: self.create_new_gameobject("Camera", CameraComponent))

        collider_menu = self.add_menu.addMenu("Collider")
        collider_menu.addAction("Box Collider", lambda: self.create_new_gameobject("Box Collider", BoxColliderComponent))
        collider_menu.addAction("Sphere Collider", lambda: self.create_new_gameobject("Sphere Collider", SphereColliderComponent))
        collider_menu.addAction("Capsule Collider", lambda: self.create_new_gameobject("Capsule Collider", CapsuleColliderComponent))
        collider_menu.addAction("Mesh Collider", lambda: self.create_new_gameobject("Mesh Collider", MeshColliderComponent))

        # 4. Connect to the manual menu trigger (Do NOT use setMenu)
        self.add_button.clicked.connect(self.show_add_menu)
        top_bar.addWidget(self.add_button)

        layout.addLayout(top_bar)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setRootIsDecorated(True)  # Show expand/collapse for top-level items
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.on_context_menu)
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)

    def on_context_menu(self, pos):
        """Shows the Copy/Paste/Delete context menu for the hierarchy."""
        menu = QMenu(self)
        copy_act = menu.addAction("Copy")
        paste_act = menu.addAction("Paste")
        menu.addSeparator()
        delete_act = menu.addAction("Delete")

        # Disable selection-dependent actions if no object is selected
        if not self.selected_game_object:
            copy_act.setEnabled(False)
            delete_act.setEnabled(False)

        # Get MainWindow to trigger global actions
        main_win = self.window()
        
        global_pos = self.tree_widget.mapToGlobal(pos)
        selected_action = menu.exec(global_pos)

        if selected_action == copy_act:
            if hasattr(main_win, 'copy_selected_object'):
                main_win.copy_selected_object()
        elif selected_action == paste_act:
            if hasattr(main_win, 'paste_object'):
                main_win.paste_object()
        elif selected_action == delete_act:
            if hasattr(main_win, 'delete_selected_object'):
                main_win.delete_selected_object()

    def show_add_menu(self):
        # Map the bottom-left corner of the button to global screen coordinates
        from PySide6.QtCore import QPoint
        global_pos = self.add_button.mapToGlobal(QPoint(0, self.add_button.height()))

        # Manually show the menu at this exact pixel location
        self.add_menu.exec(global_pos)

    def create_new_gameobject(self, name, component_class):
        sys.stderr.write(f"DEBUG [Hierarchy]: Creating new GameObject '{name}' with initial component {component_class.__name__}\n")
        go = GameObject(name=name)
        
        from engine.panda_app import PandaApp
        app = PandaApp.get_instance()
        if app:
            go.node_path.reparentTo(app.render)
            
        go.add_component(component_class)
        sys.stderr.write(f"DEBUG [Hierarchy]: Created GameObject ID {go.id}, Object ID: {id(go)}\n")
        self.update_hierarchy()
        self.node_selected.emit(go)
        self.select_node(go)

    def update_hierarchy(self):
        self.tree_widget.clear()
        self.node_map.clear()
        for go in scene_manager.game_objects:
            item = QTreeWidgetItem()
            item.setText(0, go.name)
            self.node_map[item] = go.id
            self.tree_widget.addTopLevelItem(item)

    def on_selection_changed(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            go_id = self.node_map.get(item)
            if go_id:
                game_object = next((go for go in scene_manager.game_objects if go.id == go_id), None)
                if game_object:
                    self.selected_game_object = game_object
                    self.node_selected.emit(game_object)
        else:
            self.selected_game_object = None

    def select_node(self, game_object):
        """Programmatically select a GameObject in the hierarchy."""
        for item, go_id in self.node_map.items():
            if go_id == game_object.id:
                self.tree_widget.setCurrentItem(item)
                self.node_selected.emit(game_object)
                break
