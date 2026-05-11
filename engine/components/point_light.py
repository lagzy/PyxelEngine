from engine.components.light_component import LightComponent
from panda3d.core import PointLight, Vec3

class PointLightComponent(LightComponent):
    def __init__(self):
        super().__init__()
        self._range = 10.0

    def _create_light(self):
        light = PointLight("point_light")
        light.setAttenuation(Vec3(0, 0, 1.0 / max(self._range, 0.1)))
        return light

    @property
    def range(self):
        return self._range

    @range.setter
    def range(self, value):
        self._range = max(value, 0.1)
        if hasattr(self, '_light'):
            self._light.setAttenuation(Vec3(0, 0, 1.0 / self._range))
