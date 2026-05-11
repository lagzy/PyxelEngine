from panda3d.core import Vec3
from .component import Component

class Transform(Component):
    def get_pos(self):
        return self.game_object.node_path.getPos()

    def set_pos(self, x, y, z):
        self.game_object.node_path.setPos(x, y, z)

    def get_hpr(self):
        return self.game_object.node_path.getHpr()

    def set_hpr(self, h, p, r):
        self.game_object.node_path.setHpr(h, p, r)

    def get_scale(self):
        return self.game_object.node_path.getScale()

    def set_scale(self, x, y, z):
        self.game_object.node_path.setScale(x, y, z)

    @property
    def position(self):
        return self.get_pos()

    @position.setter
    def position(self, value):
        if isinstance(value, Vec3):
            self.set_pos(value.x, value.y, value.z)
        elif isinstance(value, (list, tuple)) and len(value) == 3:
            self.set_pos(*value)

    @property
    def rotation(self):
        return self.get_hpr()

    @rotation.setter
    def rotation(self, value):
        if isinstance(value, Vec3):
            self.set_hpr(value.x, value.y, value.z)
        elif isinstance(value, (list, tuple)) and len(value) == 3:
            self.set_hpr(*value)

    @property
    def scale(self):
        return self.get_scale()

    @scale.setter
    def scale(self, value):
        if isinstance(value, Vec3):
            self.set_scale(value.x, value.y, value.z)
        elif isinstance(value, (list, tuple)) and len(value) == 3:
            self.set_scale(*value)

    def to_dict(self):
        pos = self.get_pos()
        hpr = self.get_hpr()
        scale = self.get_scale()
        return {
            "position": [pos.x, pos.y, pos.z],
            "rotation": [hpr.x, hpr.y, hpr.z],
            "scale": [scale.x, scale.y, scale.z]
        }

    def apply_dict(self, data):
        if "position" in data:
            self.set_pos(*data["position"])
        if "rotation" in data:
            self.set_hpr(*data["rotation"])
        if "scale" in data:
            self.set_scale(*data["scale"])
