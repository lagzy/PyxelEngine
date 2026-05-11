class Component:
    def __init__(self):
        self.game_object = None

    def on_start(self):
        pass

    def on_update(self, dt):
        pass

    def on_added(self):
        pass

    def on_remove(self):
        pass

    def to_dict(self):
        """Returns a dictionary representation of the component's state."""
        return {}

    def apply_dict(self, data):
        """Applies state from a dictionary to the component."""
        pass
