from engine.core.component import Component
from panda3d.core import Vec3
from engine.core.physics_world import physics_world
from engine.core.scene_manager import scene_manager

class ColliderComponent(Component):
    """Base class for all collider components using Bullet ghost nodes."""
    def __init__(self):
        super().__init__()
        self._center = Vec3(0, 0, 0)
        self._ghost_node = None
        self._ghost_np = None
        self._editor_visual_np = None
        self._previous_overlaps = set()
        self._attached = False  # Track if attached to physics world

    def on_added(self):
        """Create the ghost node and attach it to the GameObject."""
        from engine.panda_app import PandaApp
        app = PandaApp.get_instance()
        if not app:
            return
        render = app.render

        # Create ghost node (trigger collider)
        self._ghost_node = self._create_ghost_node()
        self._ghost_np = self.game_object.node_path.attachNewNode(self._ghost_node)
        self._ghost_np.setPos(self._center)
        self._ghost_np.setPythonTag("managed", True)

        # Tag the ghost node with the GameObject for collision detection
        self._ghost_node.setPythonTag("game_object", self.game_object)

        self._add_editor_visual()

    def on_start(self):
        """Add ghost to physics world when game starts."""
        if self._ghost_node and not self._attached:
            physics_world.add_ghost(self._ghost_node)
            self._attached = True
            self._previous_overlaps.clear()

    def on_update(self, dt):
        """Check for overlaps and generate collision events."""
        if not self._ghost_node:
            return

        # Snapshot of all game objects to avoid modification during iteration
        all_game_objects = list(scene_manager.get_all_game_objects())
        go_by_id = {go.id: go for go in all_game_objects}

        # Get current overlapping nodes
        current_overlaps = set()
        overlapping_objs = []  # list of (node, other_go) for non-self overlaps
        overlapping = physics_world.get_overlapping(self._ghost_node)
        for node in overlapping:
            other_go = node.getPythonTag("game_object") if node.hasPythonTag("game_object") else None
            if other_go and hasattr(other_go, 'id') and other_go.id != self.game_object.id:
                current_overlaps.add(other_go.id)
                overlapping_objs.append((node, other_go))

        # Compare with previous frame to detect changes
        exited = self._previous_overlaps - current_overlaps
        entered = current_overlaps - self._previous_overlaps
        stayed = current_overlaps & self._previous_overlaps

        # Call collision events for entered and stayed
        for node, other_go in overlapping_objs:
            if other_go.id in entered:
                self._call_collision_method(other_go, "on_collision_enter")
            if other_go.id in stayed:
                self._call_collision_method(other_go, "on_collision_stay")

        # Call exit events using snapshot to avoid iteration issues
        for go_id in exited:
            other_go = go_by_id.get(go_id)
            if other_go:
                self._call_collision_method(other_go, "on_collision_exit")

        self._previous_overlaps = current_overlaps

    def stop(self):
        """Remove from physics world when game stops."""
        if self._attached and self._ghost_node:
            physics_world.remove_ghost(self._ghost_node)
            self._attached = False

    def on_remove(self):
        """Clean up when component is removed."""
        self.stop()
        if self._editor_visual_np:
            self._editor_visual_np.removeNode()
            self._editor_visual_np = None
        if self._ghost_np:
            self._ghost_np.removeNode()
            self._ghost_np = None
            self._ghost_node = None

    def _add_editor_visual(self):
        """Optionally implemented by subclasses to show collider in editor."""
        pass

    def _create_ghost_node(self):
        """Create the BulletGhostNode - must be implemented by subclass."""
        raise NotImplementedError

    def _call_collision_method(self, other_game_object, method_name):
        """Call the specified collision method on this GameObject's components."""
        if self.game_object:
            for comp in self.game_object.components.values():
                if hasattr(comp, method_name) and callable(getattr(comp, method_name)):
                    getattr(comp, method_name)(other_game_object)

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
