from .collider_component import ColliderComponent
from panda3d.bullet import BulletGhostNode, BulletCapsuleShape
from panda3d.core import Vec3

class CapsuleColliderComponent(ColliderComponent):
    def __init__(self):
        super().__init__()
        self._radius = 0.5
        self._height = 2.0

    def _create_ghost_node(self):
        # BulletCapsuleShape(radius, height, axis)
        # Axis: 0=X, 1=Y, 2=Z. We'll use Z-axis (vertical)
        ghost = BulletGhostNode(f"ghost_capsule_{self.game_object.id if self.game_object else 'unknown'}")
        ghost.addShape(BulletCapsuleShape(self._radius, self._height, 2))  # 2 = Z-axis
        return ghost

    def _add_editor_visual(self):
        from engine.primitives_generator import PrimitivesGenerator
        generator = PrimitivesGenerator()
        self._editor_visual_np = generator.create_capsule("capsule_collider_visual", height=self._height, radius=self._radius)
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

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = max(value, 0.1)
        if self._ghost_node:
            self._ghost_node.removeShape(0)
            self._ghost_node.addShape(BulletCapsuleShape(self._radius, self._height, 2))
        
        if self._editor_visual_np:
            self._editor_visual_np.removeNode()
            self._add_editor_visual()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = max(value, 0.2)
        if self._ghost_node:
            self._ghost_node.removeShape(0)
            self._ghost_node.addShape(BulletCapsuleShape(self._radius, self._height, 2))
            
        if self._editor_visual_np:
            self._editor_visual_np.removeNode()
            self._add_editor_visual()
