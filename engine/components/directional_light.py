from engine.components.light_component import LightComponent
from panda3d.core import DirectionalLight

class DirectionalLightComponent(LightComponent):
    def _create_light(self):
        return DirectionalLight("directional_light")
