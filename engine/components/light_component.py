import sys
from engine.core.component import Component
from panda3d.core import Vec4, BitMask32, CollisionNode, CollisionSphere, GeomNode
from engine.primitives_generator import PrimitivesGenerator

class LightComponent(Component):
    def __init__(self):
        super().__init__()
        self._color = Vec4(1.0, 1.0, 1.0, 1.0)
        self._intensity = 1.0
        self._light_np = None
        self._light = None
        self._editor_visual_np = None
        self._editor_collision_np = None

    def on_added(self):
        if not self.game_object:
            return
        sys.stderr.write(f"DEBUG [LightComponent]: on_added for {self.game_object.name}\n")
        self._light = self._create_light()
        self._light.setColor(self._color * self._intensity)
        self._light_np = self.game_object.node_path.attachNewNode(self._light)
        self._light_np.setPythonTag("managed", True)
        from engine.panda_app import PandaApp
        app = PandaApp.get_instance()
        if app:
            app.render.setLight(self._light_np)
        
        self._add_editor_visual()
        self._add_editor_collision()
        sys.stderr.write(f"DEBUG [LightComponent]: Visual created: {self._editor_visual_np}\n")

    def _add_editor_visual(self):
        generator = PrimitivesGenerator()
        self._editor_visual_np = generator.create_sphere("light_visual", segments=8)
        self._editor_visual_np.setRenderModeWireframe()
        self._editor_visual_np.setRenderModeThickness(3.0)
        self._editor_visual_np.setColor(self._color.x, self._color.y, self._color.z, 1.0)
        self._editor_visual_np.setLightOff()
        self._editor_visual_np.setBin("fixed", 40)
        self._editor_visual_np.setDepthTest(False)
        self._editor_visual_np.setDepthWrite(False)
        self._editor_visual_np.setPythonTag("managed", True)
        self._editor_visual_np.reparentTo(self.game_object.node_path)
        self._editor_visual_np.setScale(0.8)

    def _add_editor_collision(self):
        coll_node = CollisionNode(f"light_collision_{self.game_object.id}")
        coll_node.addSolid(CollisionSphere(0, 0, 0, 0.5))
        coll_node.setIntoCollideMask(GeomNode.getDefaultCollideMask() | BitMask32.bit(1))
        self._editor_collision_np = self.game_object.node_path.attachNewNode(coll_node)
        self._editor_collision_np.setPythonTag("managed", True)

    def on_remove(self):
        if self._editor_visual_np:
            self._editor_visual_np.removeNode()
            self._editor_visual_np = None
        if self._editor_collision_np:
            self._editor_collision_np.removeNode()
            self._editor_collision_np = None
        if self._light_np:
            from engine.panda_app import PandaApp
            app = PandaApp.get_instance()
            if app:
                app.render.clearLight(self._light_np)
            self._light_np.removeNode()
            self._light_np = None
            self._light = None

    def _create_light(self):
        raise NotImplementedError("Subclasses must implement _create_light")

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if isinstance(value, (list, tuple)):
            self._color = Vec4(value[0], value[1], value[2], value[3] if len(value) > 3 else 1.0)
        else:
            self._color = value
        if self._light and hasattr(self._light, 'setColor'):
            self._light.setColor(self._color * self._intensity)

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, value):
        self._intensity = value
        if self._light and hasattr(self._light, 'setColor'):
            self._light.setColor(self._color * self._intensity)
