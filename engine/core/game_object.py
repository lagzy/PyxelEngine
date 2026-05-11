import uuid
import sys
from panda3d.core import NodePath
from .component import Component
from .transform_component import Transform
from .scene_manager import scene_manager

class GameObject:
    def __init__(self, name="GameObject", id_value=None, uuid_value=None):
        self.uuid = uuid_value if uuid_value else str(uuid.uuid4())
        self.id = id_value if id_value else str(uuid.uuid4())
        self.name = name
        self.node_path = NodePath(f"GameObject_{self.id}")
        self.node_path.setPythonTag("game_object", self)
        self.components = {}
        sys.stderr.write(f"DEBUG [GameObject]: Created GameObject '{self.name}' UUID={self.uuid} ID={self.id}. Object ID: {id(self)}.\n")
        sys.stderr.flush()
        self.add_component(Transform)
        scene_manager.register(self)

    def add_component(self, component_class, *args, **kwargs):
        if component_class in self.components:
            existing = self.components[component_class]
            sys.stderr.write(f"DEBUG [GameObject]: Component {component_class.__name__} already exists on GameObject '{self.name}' (ID: {self.id}). Returning existing instance ID {id(existing)}.\n")
            return existing
        instance = component_class(*args, **kwargs)
        instance.game_object = self
        self.components[component_class] = instance
        sys.stderr.write(f"DEBUG [GameObject]: Added component {component_class.__name__} to GameObject '{self.name}' (ID: {self.id}). Instance ID: {id(instance)}.\n")
        if hasattr(instance, 'on_added'):
            instance.on_added()
        return instance

    def get_component(self, component_class):
        result = self.components.get(component_class, None)
        sys.stderr.write(f"DEBUG [GameObject]: get_component({component_class.__name__}) on GameObject '{self.name}' (ID: {self.id}) returned instance ID: {id(result) if result else 'None'}.\n")
        return result

    def has_component(self, component_class):
        result = component_class in self.components
        sys.stderr.write(f"DEBUG [GameObject]: has_component({component_class.__name__}) on GameObject '{self.name}' (ID: {self.id}) returned {result}.\n")
        return result

    def remove_component(self, component_class):
        if component_class in self.components:
            instance = self.components[component_class]
            sys.stderr.write(f"DEBUG [GameObject]: Removing component {component_class.__name__} from GameObject '{self.name}' (ID: {self.id}). Instance ID: {id(instance)}.\n")
            if hasattr(instance, 'on_remove'):
                instance.on_remove()
            del self.components[component_class]
        else:
            sys.stderr.write(f"DEBUG [GameObject]: Attempted to remove non-existent component {component_class.__name__} from GameObject '{self.name}' (ID: {self.id}).\n")

    def serialize(self):
        """Serializes the GameObject and its components to a dictionary."""
        data = {
            "uuid": self.uuid,
            "id": self.id,
            "name": self.name,
            "components": {}
        }
        for comp_class, comp in self.components.items():
            data["components"][comp_class.__name__] = comp.to_dict()
        return data

    @classmethod
    def create_from_data(cls, data):
        """Creates a new GameObject instance from serialized data."""
        from .transform_component import Transform
        from engine.components.mesh_renderer import MeshRendererComponent
        from engine.components.directional_light import DirectionalLightComponent
        from engine.components.point_light import PointLightComponent
        from engine.components.spot_light import SpotLightComponent
        from engine.components.camera_component import CameraComponent
        from engine.components.rigidbody_component import RigidbodyComponent
        from engine.components.box_collider import BoxColliderComponent
        from engine.components.sphere_collider import SphereColliderComponent
        from engine.components.capsule_collider import CapsuleColliderComponent

        comp_registry = {
            "Transform": Transform,
            "MeshRendererComponent": MeshRendererComponent,
            "DirectionalLightComponent": DirectionalLightComponent,
            "PointLightComponent": PointLightComponent,
            "SpotLightComponent": SpotLightComponent,
            "CameraComponent": CameraComponent,
            "RigidbodyComponent": RigidbodyComponent,
            "BoxColliderComponent": BoxColliderComponent,
            "SphereColliderComponent": SphereColliderComponent,
            "CapsuleColliderComponent": CapsuleColliderComponent
        }

        go = cls(
            name=data.get("name", "GameObject"),
            id_value=data.get("id"),
            uuid_value=data.get("uuid")
        )
        for comp_name, comp_data in data.get("components", {}).items():
            if comp_name in comp_registry:
                comp_class = comp_registry[comp_name]
                comp = go.get_component(comp_class)
                if not comp:
                    comp = go.add_component(comp_class)
                comp.apply_dict(comp_data)
        return go

    def destroy(self):
        """Cleanly removes the GameObject from the scene and engine."""
        sys.stderr.write(f"DEBUG [GameObject]: Destroying GameObject '{self.name}' (ID: {self.id})\n")
        # Unregister from scene manager
        scene_manager.unregister(self)
        # Remove from Panda3D scene graph
        if self.node_path:
            self.node_path.removeNode()
        # Clean up components
        for comp in list(self.components.values()):
            if hasattr(comp, 'on_remove'):
                comp.on_remove()
        self.components.clear()
