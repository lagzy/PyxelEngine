from engine.core.component import Component
from panda3d.core import Camera, PerspectiveLens, OrthographicLens, BitMask32, CollisionNode, CollisionSphere, GeomNode
from engine.core.scene_manager import scene_manager
from engine.primitives_generator import PrimitivesGenerator

class CameraComponent(Component):
    def __init__(self):
        super().__init__()
        self._fov = 60.0
        self._near = 0.1
        self._far = 1000.0
        self._projection = "Perspective"
        self._is_main = False
        self._cam_np = None
        self._lens = None
        self._editor_visual_np = None
        self._editor_collision_np = None

    def on_added(self):
        if not self.game_object:
            return
        self._init_camera()
        self._add_editor_visual()
        self._add_editor_collision()

    def _add_editor_visual(self):
        generator = PrimitivesGenerator()
        self._editor_visual_np = generator.create_sphere("camera_visual", segments=8)
        self._editor_visual_np.setRenderModeWireframe()
        self._editor_visual_np.setRenderModeThickness(3.0)
        self._editor_visual_np.setColor(0.0, 0.5, 1.0, 1.0)  # Blue for camera
        self._editor_visual_np.setLightOff()
        self._editor_visual_np.setBin("fixed", 40)
        self._editor_visual_np.setDepthTest(False)
        self._editor_visual_np.setDepthWrite(False)
        self._editor_visual_np.setPythonTag("managed", True)
        self._editor_visual_np.reparentTo(self.game_object.node_path)
        self._editor_visual_np.setScale(0.8)

    def _add_editor_collision(self):
        coll_node = CollisionNode(f"camera_collision_{self.game_object.id}")
        coll_node.addSolid(CollisionSphere(0, 0, 0, 0.5))
        coll_node.setIntoCollideMask(GeomNode.getDefaultCollideMask() | BitMask32.bit(1))
        self._editor_collision_np = self.game_object.node_path.attachNewNode(coll_node)
        self._editor_collision_np.setPythonTag("managed", True)

    def _init_camera(self):
        self._lens = PerspectiveLens() if self._projection == "Perspective" else OrthographicLens()
        self._lens.setFov(self._fov)
        self._lens.setNear(self._near)
        self._lens.setFar(self._far)
        cam = Camera("camera")
        cam.setLens(self._lens)
        self._cam_np = self.game_object.node_path.attachNewNode(cam)
        self._cam_np.setPythonTag("managed", True)

    def on_remove(self):
        if self._editor_visual_np:
            self._editor_visual_np.removeNode()
            self._editor_visual_np = None
        if self._editor_collision_np:
            self._editor_collision_np.removeNode()
            self._editor_collision_np = None
        if self._cam_np:
            self._cam_np.removeNode()
            self._cam_np = None
            self._lens = None

    @property
    def field_of_view(self):
        return self._fov

    @field_of_view.setter
    def field_of_view(self, value):
        self._fov = max(value, 1.0)
        if self._lens:
            self._lens.setFov(self._fov)

    @property
    def near_clip(self):
        return self._near

    @near_clip.setter
    def near_clip(self, value):
        self._near = max(value, 0.01)
        if self._lens:
            self._lens.setNear(self._near)

    @property
    def far_clip(self):
        return self._far

    @far_clip.setter
    def far_clip(self, value):
        self._far = max(value, self._near + 0.1)
        if self._lens:
            self._lens.setFar(self._far)

    @property
    def projection_type(self):
        return self._projection

    @projection_type.setter
    def projection_type(self, value):
        if value not in ("Perspective", "Orthographic"):
            return
        if value == self._projection:
            return
        self._projection = value
        self._init_camera()

    @property
    def is_main_camera(self):
        return self._is_main

    @is_main_camera.setter
    def is_main_camera(self, value):
        self._is_main = bool(value)
        if self._is_main and self.game_object:
            for go in scene_manager.game_objects:
                cam_comp = go.get_component(CameraComponent)
                if cam_comp and cam_comp != self and cam_comp.is_main_camera:
                    cam_comp._is_main = False
