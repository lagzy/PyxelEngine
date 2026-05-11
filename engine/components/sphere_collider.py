from .collider_component import ColliderComponent
from panda3d.bullet import BulletGhostNode, BulletSphereShape

class SphereColliderComponent(ColliderComponent):
    def __init__(self):
        super().__init__()
        self._radius = 0.5

    def _create_ghost_node(self):
        ghost = BulletGhostNode(f"ghost_sphere_{self.game_object.id if self.game_object else 'unknown'}")
        ghost.addShape(BulletSphereShape(self._radius))
        return ghost

    def _add_editor_visual(self):
        from engine.primitives_generator import PrimitivesGenerator
        generator = PrimitivesGenerator()
        self._editor_visual_np = generator.create_sphere("sphere_collider_visual", segments=12)
        self._editor_visual_np.setRenderModeWireframe()
        self._editor_visual_np.setRenderModeThickness(2.0)
        self._editor_visual_np.setColor(0.0, 1.0, 0.0, 1.0)
        self._editor_visual_np.setLightOff()
        self._editor_visual_np.setBin("fixed", 40)
        self._editor_visual_np.setDepthTest(False)
        self._editor_visual_np.setDepthWrite(False)
        self._editor_visual_np.setPythonTag("managed", True)
        self._editor_visual_np.reparentTo(self.game_object.node_path)
        self._editor_visual_np.setPos(self._center)
        self._editor_visual_np.setScale(self._radius * 2)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = max(value, 0.1)
        if self._ghost_node:
            self._ghost_node.removeShape(0)
            self._ghost_node.addShape(BulletSphereShape(self._radius))
        
        if self._editor_visual_np:
            self._editor_visual_np.setScale(self._radius * 2)
