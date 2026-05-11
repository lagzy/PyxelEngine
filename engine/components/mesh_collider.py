from .collider_component import ColliderComponent
from panda3d.bullet import BulletGhostNode, BulletTriangleMeshShape, BulletTriangleMesh
from panda3d.core import Vec3

class MeshColliderComponent(ColliderComponent):
    def __init__(self):
        super().__init__()

    def _create_ghost_node(self):
        ghost = BulletGhostNode(f"ghost_mesh_{self.game_object.id if self.game_object else 'unknown'}")

        # Build triangle mesh from the GameObject's geometry
        mesh = BulletTriangleMesh()
        self._build_triangle_mesh(mesh)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        ghost.addShape(shape)

        return ghost

    def _build_triangle_mesh(self, bullet_mesh):
        """Extract triangles from the GameObject's GeomNodes and add to BulletTriangleMesh."""
        # Get all GeomNodes under the GameObject
        geom_nodes = self.game_object.node_path.findAllMatches("**/+GeomNode")
        for gn in geom_nodes:
            geom_node = gn.node()
            # Get the transform from the GeomNode to the GameObject's root
            transform = self.game_object.node_path.getTransform(gn)
            for i in range(geom_node.getNumGeoms()):
                geom = geom_node.getGeom(i)
                bullet_mesh.addGeom(geom, transform)

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value):
        if isinstance(value, (list, tuple)):
            self._center = Vec3(value[0], value[1], value[2])
        else:
            self._center = value
        if self._ghost_np:
            self._ghost_np.setPos(self._center)
