from engine.components.point_light import PointLightComponent
from panda3d.core import Spotlight, PerspectiveLens, Vec3

class SpotLightComponent(PointLightComponent):
    def __init__(self):
        super().__init__()
        self._cone_angle = 45.0

    def _create_light(self):
        light = Spotlight("spot_light")
        lens = PerspectiveLens()
        lens.setFov(self._cone_angle)
        light.setLens(lens)
        # Set attenuation based on range
        light.setAttenuation(Vec3(0, 0, 1.0 / max(self.range, 0.1)))
        return light

    @property
    def cone_angle(self):
        return self._cone_angle

    @cone_angle.setter
    def cone_angle(self, value):
        self._cone_angle = max(value, 1.0)
        if hasattr(self, '_light') and self._light and self._light.getLens():
            self._light.getLens().setFov(self._cone_angle)
