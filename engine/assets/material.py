import json
from panda3d.core import Vec4

class Material:
    def __init__(self):
        self.base_color = Vec4(1.0, 1.0, 1.0, 1.0)
        self.diffuse_map = ""
        self.normal_map = ""
        self.specular_map = ""

    def to_dict(self):
        return {
            "base_color": [self.base_color.x, self.base_color.y, self.base_color.z, self.base_color.w],
            "diffuse_map": self.diffuse_map,
            "normal_map": self.normal_map,
            "specular_map": self.specular_map
        }

    @classmethod
    def from_dict(cls, data):
        mat = cls()
        bc = data.get("base_color", [1.0, 1.0, 1.0, 1.0])
        mat.base_color = Vec4(bc[0], bc[1], bc[2], bc[3])
        mat.diffuse_map = data.get("diffuse_map", "")
        mat.normal_map = data.get("normal_map", "")
        mat.specular_map = data.get("specular_map", "")
        return mat

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, path):
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
