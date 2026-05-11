from .transform_component import Transform

class SceneManager:
    def __init__(self):
        self.game_objects = []

    def register(self, go):
        if go not in self.game_objects:
            self.game_objects.append(go)

    def unregister(self, go):
        if go in self.game_objects:
            self.game_objects.remove(go)

    def clear(self):
        for go in self.game_objects[:]:
            self.unregister(go)

    def get_all_game_objects(self):
        """Return all game objects in the scene."""
        return self.game_objects

    def serialize(self):
        data = []
        for go in self.game_objects:
            go_data = {
                "id": go.id,
                "name": go.name,
                "components": {}
            }
            for comp_class, comp in go.components.items():
                if isinstance(comp, Transform):
                    go_data["components"][comp_class.__name__] = {
                        "position": [comp.get_pos().x, comp.get_pos().y, comp.get_pos().z],
                        "rotation": [comp.get_hpr().x, comp.get_hpr().y, comp.get_hpr().z],
                        "scale": [comp.get_scale().x, comp.get_scale().y, comp.get_scale().z]
                    }
            data.append(go_data)
        return data

    def deserialize(self, data):
        self.clear()
        for go_data in data:
            from .game_object import GameObject
            go = GameObject(name=go_data["name"], id_value=go_data["id"])
            for comp_name, comp_data in go_data["components"].items():
                if comp_name == "Transform":
                    transform = go.get_component(Transform)
                    if "position" in comp_data:
                        transform.set_pos(*comp_data["position"])
                    if "rotation" in comp_data:
                        transform.set_hpr(*comp_data["rotation"])
                    if "scale" in comp_data:
                        transform.set_scale(*comp_data["scale"])

scene_manager = SceneManager()
