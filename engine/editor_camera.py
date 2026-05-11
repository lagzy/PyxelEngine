"""
Editor camera controls: Orbit camera with pivot, look, pan, zoom.
"""

from panda3d.core import Vec3, Quat
from math import radians

class EditorCamera:
    def __init__(self, panda_app):
        self.panda_app = panda_app
        self.camera = panda_app.camera if panda_app else None
        self.mouse_sensitivity = 0.2
        self.zoom_speed = 0.5
        self.pan_speed = 0.01

        # Orbit camera attributes
        self.target = Vec3(0, 0, 0)  # Pivot point (world space)
        self.distance = 10.0  # Distance from pivot to camera
        self.heading = 0  # Yaw (H)
        self.pitch = 0  # Pitch (P)
        self.update_camera_orientation()

        # State
        self.looking = False
        self.panning = False
        self.last_mouse_pos = None

    def focus_on(self, node_path):
        """Focus the camera on the given node path."""
        from panda3d.core import Point3
        # Get tight bounds
        bounds = node_path.getTightBounds()
        if bounds is None:
            return  # No valid bounds
        min_bound, max_bound = bounds
        
        # Calculate center and radius
        center = (min_bound + max_bound) * 0.5
        bbox_diagonal = max_bound - min_bound
        radius = bbox_diagonal.length() * 0.5
        
        # Ideal distance: 3x radius, minimum 1.0
        ideal_distance = max(radius * 3.0, 1.0)
        
        # Update pivot/target to object center
        self.target = Point3(center)
        self.distance = ideal_distance
        
        # Update camera orientation to look at target
        self.camera.lookAt(self.panda_app.render, center)
        hpr = self.camera.getHpr(self.panda_app.render)
        self.heading = hpr.x
        self.pitch = hpr.y
        self.pitch = max(-89, min(89, self.pitch))
        
        # Apply changes instantly
        self.update_camera_orientation()

    def start_look(self, mouse_pos):
        self.looking = True
        self.last_mouse_pos = mouse_pos

    def stop_look(self):
        self.looking = False
        self.last_mouse_pos = None

    def start_pan(self, mouse_pos):
        self.panning = True
        self.last_mouse_pos = mouse_pos

    def stop_pan(self):
        self.panning = False
        self.last_mouse_pos = None

    def update_mouse(self, mouse_pos):
        if not self.last_mouse_pos:
            self.last_mouse_pos = mouse_pos
            return

        dx = mouse_pos[0] - self.last_mouse_pos[0]
        dy = mouse_pos[1] - self.last_mouse_pos[1]

        if self.looking:
            self.look(dx, dy)
        elif self.panning:
            self.pan(dx, dy)

        self.last_mouse_pos = mouse_pos

    def look(self, dx, dy):
        self.heading -= dx * self.mouse_sensitivity
        self.pitch -= dy * self.mouse_sensitivity
        self.pitch = max(-89, min(89, self.pitch))  # Clamp pitch
        self.update_camera_orientation()

    def pan(self, dx, dy):
        # Get camera's right and up vectors in world space
        quat = Quat()
        quat.setHpr(Vec3(self.heading, self.pitch, 0))
        right = quat.getRight()
        up = quat.getUp()
        
        pan_vector = right * (-dx * self.pan_speed) + up * (dy * self.pan_speed)
        self.target += pan_vector
        self.update_camera_orientation()

    def zoom(self, delta):
        # Adjust distance from pivot
        self.distance -= delta * self.zoom_speed * 5.0
        self.distance = max(1.0, self.distance)  # Minimum distance
        self.update_camera_orientation()

    def update_camera_orientation(self):
        if not self.camera:
            return
        # Calculate forward vector from heading and pitch
        quat = Quat()
        quat.setHpr(Vec3(self.heading, self.pitch, 0))
        forward = quat.getForward()
        
        # Position camera at target - forward * distance
        camera_pos = self.target - (forward * self.distance)
        self.camera.setPos(self.panda_app.render, camera_pos)
        self.camera.setHpr(self.panda_app.render, self.heading, self.pitch, 0)