from engine.core.component import Component
from engine.assets.material import Material
from panda3d.core import Material as PandaMaterial

class MeshRendererComponent(Component):
    def __init__(self):
        super().__init__()
        self._material_path = ""
        self._panda_mat = PandaMaterial()
        self._model_path = ""
        self._loaded_node = None

    @property
    def model_path(self):
        return self._model_path

    @model_path.setter
    def model_path(self, value):
        self._model_path = value
        self._load_model()

    def _load_model(self):
        if not self.game_object or not self._model_path:
            return
            
        # Clean up existing node if any
        if self._loaded_node:
            self._loaded_node.removeNode()
            self._loaded_node = None

        from panda3d.core import BitMask32

        if self._model_path.startswith("Primitive:"):
            shape_name = self._model_path.split(":", 1)[1]
            from engine.primitives_generator import PrimitivesGenerator
            generator = PrimitivesGenerator()
            if shape_name == "Cube":
                self._loaded_node = generator.create_cube()
            elif shape_name == "Sphere":
                self._loaded_node = generator.create_sphere()
            elif shape_name == "Capsule":
                self._loaded_node = generator.create_capsule()
        else:
            # Load from file
            from engine.panda_app import PandaApp
            app = PandaApp.get_instance()
            if app:
                self._loaded_node = app.loader.loadModel(self._model_path)

        if self._loaded_node:
            self._loaded_node.reparentTo(self.game_object.node_path)
            self._loaded_node.setCollideMask(BitMask32.bit(1))
            self._apply_material()

    @property
    def material_path(self):
        return self._material_path

    @material_path.setter
    def material_path(self, value):
        self._material_path = value
        self._apply_material()

    def _apply_material(self):
        if not self.game_object or not self._material_path:
            return
        try:
            mat_asset = Material.load(self._material_path)
            self._panda_mat.setBaseColor(mat_asset.base_color)
            if mat_asset.diffuse_map:
                from engine.panda_app import PandaApp
                app = PandaApp.get_instance()
                if app:
                    tex = app.loader.loadTexture(mat_asset.diffuse_map)
                    self.game_object.node_path.setTexture(tex, 1)
            self.game_object.node_path.setMaterial(self._panda_mat)
        except Exception as e:
            print(f"MeshRenderer: Failed to apply material: {e}")

    def to_dict(self):
        return {
            "model_path": self._model_path,
            "material_path": self._material_path
        }

    def apply_dict(self, data):
        if "model_path" in data:
            self.model_path = data["model_path"]
        if "material_path" in data:
            self.material_path = data["material_path"]
