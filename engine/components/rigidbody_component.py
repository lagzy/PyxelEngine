from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from panda3d.core import Vec3
from engine.core.component import Component

class RigidbodyComponent(Component):
    def __init__(self):
        super().__init__()
        self.mass = 1.0
        self.is_kinematic = False
        self.use_gravity = True

        # Bullet nodes will be created in on_added
        self.rb_node = None
        self.rb_np = None
        self._attached = False  # Track if attached to physics world

    def on_added(self):
        """Create the Bullet Rigid Body node and attach to render."""
        from engine.panda_app import PandaApp
        app = PandaApp.get_instance()
        if not app:
            return
        render = app.render

        # Create the BulletRigidBodyNode with proper name
        self.rb_node = BulletRigidBodyNode(f"rb_{self.game_object.id}")

        # Add a default collision shape
        self.rb_node.addShape(BulletBoxShape(Vec3(0.5, 0.5, 0.5)))

        # Attach to render
        self.rb_np = render.attachNewNode(self.rb_node)

    def on_start(self):
        """Configure physics properties and attach to physics world when game starts."""
        if self._attached:
            return  # Already attached
        from engine.panda_app import PandaApp
        app = PandaApp.get_instance()
        if not app or not self.rb_np:
            return
        render = app.render

        # Match visual transform before simulation starts
        self.rb_np.setTransform(render, self.game_object.node_path.getTransform(render))

        # Tag the Bullet node with the GameObject for collision detection
        self.rb_node.setPythonTag("game_object", self.game_object)

        if self.is_kinematic:
            # Kinematic: mass=0, moved by code, not affected by forces/gravity
            self.rb_node.setMass(0)
            self.rb_node.setKinematic(True)
        else:
            # Dynamic: mass > 0, affected by forces and gravity
            self.rb_node.setMass(self.mass)
            self.rb_node.setKinematic(False)
            self.rb_node.setActive(True)

        # Attach to global Bullet World
        from engine.core.physics_world import physics_world
        physics_world.add_rigid_body(self.rb_node)
        self._attached = True

    def on_update(self, dt):
        if not self._attached or not self.rb_np:
            return
        from engine.panda_app import PandaApp
        app = PandaApp.get_instance()
        if not app:
            return
        render = app.render

        if self.is_kinematic:
            # Kinematic: visual position drives physics body
            self.rb_np.setTransform(render, self.game_object.node_path.getTransform(render))
        else:
            # Dynamic: physics body drives visual
            self.game_object.node_path.setTransform(render, self.rb_np.getTransform(render))

            # If use_gravity is False, apply counter-force to cancel world gravity
            if not self.use_gravity:
                # Get world gravity and apply opposite force
                from engine.core.physics_world import physics_world
                gravity = physics_world.world.getGravity()
                # Apply force to cancel gravity: F = -m * g
                cancel_force = -gravity * self.mass
                self.rb_node.applyCentralForce(cancel_force)

    def stop(self):
        """Remove from physics world when game stops."""
        from engine.core.physics_world import physics_world
        if self._attached and self.rb_node:
            physics_world.remove_rigid_body(self.rb_node)
            self._attached = False
        if self.rb_node:
            self.rb_node.setLinearVelocity(Vec3(0, 0, 0))
            self.rb_node.setAngularVelocity(Vec3(0, 0, 0))

    def on_remove(self):
        """Clean up when component is removed."""
        self.stop()
        if self.rb_np:
            self.rb_np.removeNode()
            self.rb_np = None
            self.rb_node = None
