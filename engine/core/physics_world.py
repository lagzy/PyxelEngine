from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletGhostNode
from panda3d.core import Vec3

class PhysicsWorld:
    def __init__(self):
        # BulletWorld is incredibly stable and easy to use
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.ghost_nodes = []  # Track ghost nodes for collision detection

    def update(self, dt):
        # Step the bullet physics simulation
        self.world.doPhysics(dt)

    def add_rigid_body(self, rb_node):
        """Add a rigid body to the physics world."""
        # BulletWorld doesn't have a contains method, but we can track ourselves if needed.
        # For simplicity, we assume proper start/stop lifecycle.
        self.world.attachRigidBody(rb_node)

    def remove_rigid_body(self, rb_node):
        """Remove a rigid body from the physics world."""
        self.world.removeRigidBody(rb_node)

    def add_ghost(self, ghost_node):
        """Add a ghost node (trigger collider) to the physics world."""
        if ghost_node not in self.ghost_nodes:
            self.world.attachGhost(ghost_node)
            self.ghost_nodes.append(ghost_node)

    def remove_ghost(self, ghost_node):
        """Remove a ghost node from the physics world."""
        self.world.removeGhost(ghost_node)
        if ghost_node in self.ghost_nodes:
            self.ghost_nodes.remove(ghost_node)

    def get_overlapping(self, ghost_node):
        """Get all nodes overlapping with the given ghost node."""
        if ghost_node in self.ghost_nodes:
            return ghost_node.getOverlappingNodes()
        return []

physics_world = PhysicsWorld()
