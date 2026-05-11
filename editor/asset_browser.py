"""
Asset Browser Panel.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QMenu
from PySide6.QtCore import QDir, Signal
from PySide6.QtGui import QContextMenuEvent

from engine.primitives_generator import PrimitivesGenerator


class AssetBrowser(QWidget):
    model_loaded = Signal(str)  # Signal when a model is loaded

    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.model = QFileSystemModel()
        self.model.setRootPath(self.project_path)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.project_path))
        self.tree_view.doubleClicked.connect(self.on_double_click)
        layout.addWidget(self.tree_view)

        self.setLayout(layout)

    def on_double_click(self, index):
        file_path = self.model.filePath(index)
        if file_path.endswith(('.egg', '.bam', '.gltf', '.glb')):
            self.model_loaded.emit(file_path)

    def create_primitive_bam(self, shape_name):
        """Create a primitive and save it as a BAM file."""
        generator = PrimitivesGenerator()

        if shape_name == "Cube":
            node = generator.create_cube()
        elif shape_name == "Sphere":
            node = generator.create_sphere()
        elif shape_name == "Capsule":
            node = generator.create_capsule()
        else:
            return

        if node:
            # Get current directory from context menu
            current_dir = getattr(self, '_context_dir', self.project_path)
            if not QDir(current_dir).exists():
                current_dir = self.project_path

            # Create file path
            file_path = QDir(current_dir).filePath(f"{shape_name}.bam")

            # Save as BAM file (don't attach to render)
            node.writeBamFile(file_path)

            # Refresh the model by re-setting the root path
            current_root = self.model.rootPath()
            self.model.setRootPath("")
            self.model.setRootPath(current_root)

    def create_material(self):
        """Create a new Material asset file."""
        from engine.assets.material import Material
        import os
        current_dir = getattr(self, '_context_dir', self.project_path)
        if not os.path.isdir(current_dir):
            current_dir = self.project_path
        # Generate unique file path
        base_name = "New Material"
        file_path = os.path.join(current_dir, f"{base_name}.mat")
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(current_dir, f"{base_name} {counter}.mat")
            counter += 1
        # Create and save default material
        mat = Material()
        mat.save(file_path)
        # Refresh asset browser
        current_root = self.model.rootPath()
        self.model.setRootPath("")
        self.model.setRootPath(current_root)

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Show context menu on right-click."""
        # Get the directory at the click position
        index = self.tree_view.indexAt(event.pos())
        if index.isValid():
            path = self.model.filePath(index)
            if QDir(path).exists():
                self._context_dir = path
            else:
                self._context_dir = QDir(path).absolutePath()
        else:
            # Use the current root directory
            root_index = self.tree_view.rootIndex()
            if root_index.isValid():
                self._context_dir = self.model.filePath(root_index)
            else:
                self._context_dir = self.project_path

        menu = QMenu(self)

        create_menu = menu.addMenu("Create")
        objects_menu = create_menu.addMenu("3D Object")
        objects_menu.addAction("Cube", lambda: self.create_primitive_bam("Cube"))
        objects_menu.addAction("Sphere", lambda: self.create_primitive_bam("Sphere"))
        objects_menu.addAction("Capsule", lambda: self.create_primitive_bam("Capsule"))
        create_menu.addAction("Material", self.create_material)

        menu.exec(event.globalPos())