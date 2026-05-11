from panda3d.core import LineSegs, NodePath

class EditorGrid:
    """A simple 3D ground grid for spatial orientation in the editor."""
    def __init__(self, parent, size=100, spacing=1, major_spacing=10):
        self.parent = parent
        self.size = size
        self.spacing = spacing
        self.major_spacing = major_spacing
        self.grid_np = None
        self.create_grid()

    def create_grid(self):
        """Generates the grid geometry using LineSegs."""
        if self.grid_np:
            self.grid_np.removeNode()

        ls = LineSegs()
        ls.setThickness(1)
        
        half_size = self.size / 2
        num_steps = int(self.size / self.spacing)

        for i in range(num_steps + 1):
            pos = -half_size + (i * self.spacing)
            
            # Determine color (Major lines are brighter)
            is_major = (i * self.spacing) % self.major_spacing == 0
            if is_major:
                ls.setColor(0.4, 0.4, 0.4, 1.0)
            else:
                ls.setColor(0.25, 0.25, 0.25, 1.0)

            # Lines parallel to Y axis
            ls.moveTo(pos, -half_size, 0)
            ls.drawTo(pos, half_size, 0)

            # Lines parallel to X axis
            ls.moveTo(-half_size, pos, 0)
            ls.drawTo(half_size, pos, 0)

        # Create the node and apply editor-friendly settings
        self.grid_np = NodePath(ls.create())
        self.grid_np.reparentTo(self.parent)
        self.grid_np.setLightOff()
        self.grid_np.setDepthWrite(False) # Don't block objects
        self.grid_np.setBin("background", 10) # Render behind most things
        self.grid_np.setName("EditorGrid")

    def toggle(self):
        """Toggles grid visibility."""
        if self.grid_np.isHidden():
            self.grid_np.show()
        else:
            self.grid_np.hide()

    def show(self):
        self.grid_np.show()

    def hide(self):
        self.grid_np.hide()
