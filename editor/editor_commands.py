from engine.core.command_system import Command
from panda3d.core import Point3, Vec3, Quat

class TransformCommand(Command):
    """Command for moving, rotating, or scaling a GameObject."""
    def __init__(self, game_object, old_transform, new_transform):
        self.game_object = game_object
        # transform is a tuple of (pos, hpr, scale)
        self.old_pos, self.old_hpr, self.old_scale = old_transform
        self.new_pos, self.new_hpr, self.new_scale = new_transform

    def execute(self):
        if self.game_object.node_path:
            self.game_object.node_path.setPos(self.new_pos)
            self.game_object.node_path.setHpr(self.new_hpr)
            self.game_object.node_path.setScale(self.new_scale)

    def undo(self):
        if self.game_object.node_path:
            self.game_object.node_path.setPos(self.old_pos)
            self.game_object.node_path.setHpr(self.old_hpr)
            self.game_object.node_path.setScale(self.old_scale)

class CreateObjectCommand(Command):
    """Command for creating/pasting a GameObject."""
    def __init__(self, main_window, go_data, visual_source_np=None, offset=None):
        self.main_window = main_window
        self.go_data = go_data
        self.visual_source_np = visual_source_np
        self.offset = offset
        self.created_go = None
        self.cloned_visuals = []

    def execute(self):
        from engine.core.game_object import GameObject
        from panda3d.core import BitMask32
        
        # Create object
        self.created_go = GameObject.create_from_data(self.go_data)
        self.created_go.node_path.reparentTo(self.main_window.viewport.panda_app.render)
        self.created_go.node_path.setCollideMask(BitMask32.bit(1))
        
        # Apply visual cloning if source provided
        if self.visual_source_np:
            for child in self.visual_source_np.getChildren():
                if child.getName() != "gizmo" and not child.getPythonTag("managed"):
                    new_child = child.copyTo(self.created_go.node_path)
                    self.cloned_visuals.append(new_child)
        
        # Apply offset if provided
        if self.offset:
            self.created_go.node_path.setPos(self.created_go.node_path.getPos() + self.offset)
            
        self.main_window.hierarchy_panel.update_hierarchy()
        self.main_window.hierarchy_panel.select_node(self.created_go)

    def undo(self):
        if self.created_go:
            self.created_go.destroy()
            self.created_go = None
            self.cloned_visuals.clear()
            self.main_window.hierarchy_panel.update_hierarchy()
            self.main_window.inspector_panel.set_node(None)

class DeleteObjectCommand(Command):
    """Command for deleting a GameObject."""
    def __init__(self, main_window, game_object):
        self.main_window = main_window
        self.game_object = game_object
        self.go_data = game_object.serialize()
        self.visual_source_np = None # Not easily restorable if complex, but we'll try

    def execute(self):
        self.game_object.destroy()
        self.main_window.hierarchy_panel.update_hierarchy()
        self.main_window.viewport.update_outline(None)
        self.main_window.inspector_panel.set_node(None)

    def undo(self):
        # This is a simple version - recreating from serialized data
        from engine.core.game_object import GameObject
        from panda3d.core import BitMask32
        self.game_object = GameObject.create_from_data(self.go_data)
        self.game_object.node_path.reparentTo(self.main_window.viewport.panda_app.render)
        self.game_object.node_path.setCollideMask(BitMask32.bit(1))
        self.main_window.hierarchy_panel.update_hierarchy()
        self.main_window.hierarchy_panel.select_node(self.game_object)
