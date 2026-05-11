"""
Project data management and serialization.
"""

import json
import os

class ProjectData:
    def __init__(self, project_path):
        self.project_path = project_path
        self.project_json = os.path.join(project_path, "project.json")
        self.events_file = os.path.join(project_path, "events.ess")
        self.data = self.load()
        self.events_data = self.load_events()

    def load(self):
        if os.path.exists(self.project_json):
            with open(self.project_json, "r") as f:
                return json.load(f)
        return {}

    def load_events(self):
        if os.path.exists(self.events_file):
            with open(self.events_file, "r") as f:
                try:
                    return json.load(f)
                except Exception:
                    pass
        return []

    def save(self):
        with open(self.project_json, "w") as f:
            json.dump(self.data, f, indent=4)
        with open(self.events_file, "w") as f:
            json.dump(self.events_data, f, indent=4)

    @property
    def name(self):
        return self.data.get("name", "Unnamed Project")

    @property
    def version(self):
        return self.data.get("version", "1.0")

    @property
    def assets_path(self):
        return os.path.join(self.project_path, "assets")

    @property
    def scenes_path(self):
        return os.path.join(self.project_path, "scenes")

    @property
    def scripts_path(self):
        return os.path.join(self.project_path, "scripts")