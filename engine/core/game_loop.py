# engine/core/game_loop.py
from enum import Enum

class EngineState(Enum):
    EDITOR = 0
    PLAYING = 1
    PAUSED = 2

class GameLoop:
    def __init__(self):
        self.state = EngineState.EDITOR
        self.transform_cache = {}
        self._state_callbacks = []

    def register_state_callback(self, callback):
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def unregister_state_callback(self, callback):
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def _notify_state_change(self):
        for callback in self._state_callbacks:
            callback(self.state)

    def start_play_mode(self):
        from .scene_manager import scene_manager
        from engine.panda_app import PandaApp
        self.state = EngineState.PLAYING
        self.transform_cache.clear()

        app = PandaApp.get_instance()
        if not app:
            return
        render = app.render

        for go in scene_manager.get_all_game_objects():
            self.transform_cache[go.id] = go.node_path.getTransform(render)
            
            # Safely get components
            comps = go.components.values() if isinstance(go.components, dict) else go.components
            for component in comps:
                if hasattr(component, 'on_start'):
                    print(f"DEBUG: Starting component {component.__class__.__name__}")
                    component.on_start()
        print("DEBUG: Play mode started. Caches created.")
        self._notify_state_change()

    def stop_play_mode(self):
        from .scene_manager import scene_manager
        from engine.panda_app import PandaApp
        self.state = EngineState.EDITOR
        
        app = PandaApp.get_instance()
        if app:
            render = app.render
        else:
            render = None
        
        for go in scene_manager.get_all_game_objects():
            if render and go.id in self.transform_cache:
                go.node_path.setTransform(render, self.transform_cache[go.id])
            
            # Safely get components
            comps = go.components.values() if isinstance(go.components, dict) else go.components
            for component in comps:
                if hasattr(component, 'stop'):
                    print(f"DEBUG: Stopping component {component.__class__.__name__}")
                    component.stop()
        self.transform_cache.clear()
        print("DEBUG: Play mode stopped. Transforms restored.")
        self._notify_state_change()

    def play(self):
        """Start or resume play mode."""
        if self.state == EngineState.EDITOR:
            self.start_play_mode()
        elif self.state == EngineState.PAUSED:
            self.state = EngineState.PLAYING
            self._notify_state_change()
            print("DEBUG: Resumed from PAUSED to PLAYING")

    def pause(self):
        """Pause play mode."""
        if self.state == EngineState.PLAYING:
            self.state = EngineState.PAUSED
            self._notify_state_change()
            print("DEBUG: Paused")

    def stop(self):
        """Stop play mode and return to editor."""
        if self.state != EngineState.EDITOR:
            self.stop_play_mode()

    def update(self, dt):
        """Compatibility stub - actual updates handled by global_update_task."""
        # This method is kept for compatibility with existing call sites.
        # The actual update logic is in PandaApp.global_update_task.
        pass

game_loop = GameLoop()
