# engine/panda_app.py
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, AmbientLight, DirectionalLight, VBase4, ClockObject

from engine.core.physics_world import physics_world
from engine.core.scene_manager import scene_manager

class PandaApp(ShowBase):
    _instance = None
    game_loop = None  # Class variable to hold game_loop reference

    def __init__(self, parent_window_handle=None):
        PandaApp._instance = self
        ShowBase.__init__(self, windowType='none')
        self.parent_window_handle = parent_window_handle
        self.window_opened = False

        # Import and store game_loop
        from engine.core import game_loop as gl_module
        PandaApp.game_loop = gl_module.game_loop

        if parent_window_handle is not None:
            self.open_embedded_window()
        
        # Always setup editor lights and heartbeat
        self.setup_editor_lights()
        
        # Setup Editor Grid
        from engine.core.editor_grid import EditorGrid
        self.editor_grid = EditorGrid(self.render)

    @classmethod
    def get_instance(cls):
        return cls._instance

    def open_embedded_window(self):
        if self.window_opened:
            return
        props = WindowProperties()
        props.setParentWindow(self.parent_window_handle)
        props.setOrigin(0, 0)
        props.setSize(100, 100)
        props.setUndecorated(True)
        self.openMainWindow(props=props)
        self.window_opened = True
        self.setBackgroundColor(0.15, 0.15, 0.15, 1.0)
        self.disableMouse()

    def setup_editor_lights(self):
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor(VBase4(0.3, 0.3, 0.3, 1))
        self.ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(self.ambient_light_np)

        dir_light = DirectionalLight("dir_light")
        dir_light.setColor(VBase4(0.8, 0.8, 0.8, 1))
        self.dir_light_np = self.render.attachNewNode(dir_light)
        self.dir_light_np.setHpr(0, -60, 0)
        self.render.setLight(self.dir_light_np)