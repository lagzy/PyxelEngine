from .collider_component import ColliderComponent
from panda3d.bullet import BulletGhostNode, BulletBoxShape, BulletSphereShape, BulletCapsuleShape
from panda3d.core import Vec3

class BoxColliderComponent(ColliderComponent):
    def __init__(self):
        super().__init__()
        self._size = Vec3(1.0, 1.0, 1.0)

    def _create_ghost_node(self):
        half_size = Vec3(self._size.x/2, self._size.y/2, self._size.z/2)
        ghost = BulletGhostNode(f"ghost_box_{self.game_object.id if self.game_object else 'unknown'}")
        ghost.addShape(BulletBoxShape(half_size))
        return ghost

    def _add_editor_visual(self):
        from engine.primitives_generator import PrimitivesGenerator
        generator = PrimitivesGenerator()
        self._editor_visual_np = generator.create_cube("box_collider_visual")
        self._editor_visual_np.setRenderModeWireframe()
        self._editor_visual_np.setRenderModeThickness(2.0)
        self._editor_visual_np.setColor(0.0, 1.0, 0.0, 1.0) # Green for colliders
        self._editor_visual_np.setLightOff()
        self._editor_visual_np.setBin("fixed", 40)
        self._editor_visual_np.setDepthTest(False)
        self._editor_visual_np.setDepthWrite(False)
        self._editor_visual_np.setPythonTag("managed", True)
        self._editor_visual_np.reparentTo(self.game_object.node_path)
        self._editor_visual_np.setPos(self._center)
        self._editor_visual_np.setScale(self._size)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if isinstance(value, (list, tuple)):
            self._size = Vec3(value[0], value[1], value[2])
        else:
            self._size = value
        if self._ghost_node:
            # Recreate ghost node with new shape
            self._ghost_node.removeShape(0)
            half_size = Vec3(self._size.x/2, self._size.y/2, self._size.z/2)
            self._ghost_node.addShape(BulletBoxShape(half_size))
        
        if self._editor_visual_np:
            self._editor_visual_np.setScale(self._size)
