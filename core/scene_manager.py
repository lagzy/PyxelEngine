"""
Scene management for saving and loading scenes to JSON.
"""

import json
import os
from panda3d.core import NodePath

class SceneManager:
    def __init__(self, panda_app, project_data):
        self.panda_app = panda_app
        self.project_data = project_data

    def save_scene(self, scene_name):
        scene_data = self.serialize_scene(self.panda_app.render)
        scene_file = os.path.join(self.project_data.scenes_path, f"{scene_name}.json")
        with open(scene_file, "w") as f:
            json.dump(scene_data, f, indent=4)

    def load_scene(self, scene_name):
        scene_file = os.path.join(self.project_data.scenes_path, f"{scene_name}.json")
        if not os.path.exists(scene_file):
            return
        with open(scene_file, "r") as f:
            scene_data = json.load(f)
        self.deserialize_scene(scene_data, self.panda_app.render)

    def serialize_scene(self, node_path, parent_data=None):
        if parent_data is None:
            parent_data = {}
        data = {
            "name": node_path.getName(),
            "pos": [node_path.getX(), node_path.getY(), node_path.getZ()],
            "hpr": [node_path.getH(), node_path.getP(), node_path.getR()],
            "scale": [node_path.getSx(), node_path.getSy(), node_path.getSz()],
            "children": []
        }
        for child in node_path.getChildren():
            data["children"].append(self.serialize_scene(child))
        return data

    def deserialize_scene(self, data, parent_node):
        node = NodePath(data["name"])
        node.setPos(*data["pos"])
        node.setHpr(*data["hpr"])
        node.setScale(*data["scale"])
        node.reparentTo(parent_node)
        for child_data in data["children"]:
            self.deserialize_scene(child_data, node)