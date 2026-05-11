from panda3d.core import NodePath, LineSegs, CollisionNode, CollisionTube, BitMask32, Vec3, GeomVertexFormat, GeomVertexData, Geom, GeomTriangles, GeomVertexWriter, GeomNode
import math

class GizmoManager:
    def __init__(self, base):
        self.base = base
        self.gizmo_root = NodePath("gizmo_root")
        self.gizmo_root.setDepthTest(False)
        self.gizmo_root.setDepthWrite(False)
        self.gizmo_root.setBin("fixed", 40)
        self.gizmo_root.hide() # Hidden by default

        self.selected_node = None
        self.dragging = False
        self.locked_axis = None

        # Compatibility attributes for main_window.py
        self.inspector_panel = None
        self.selection_callback = None

        self.active_mode = 'TRANSLATE'

        self._create_visuals()
        self._create_colliders()

        # Enforce initial mode (hide all except active)
        self.set_mode(self.active_mode)

        # Constant screen size task
        self.base.taskMgr.add(self.update_scale_task, "GizmoScaleTask")

    def set_selected_node(self, node_path):
        """Attach gizmo to the selected node, or hide if None.
        The gizmo is parented to render (not the object) and only follows position."""
        self.selected_node = node_path
        if node_path is not None:
            # Parent to render (not the object) to avoid inheriting scale/rotation
            self.gizmo_root.reparentTo(self.base.render)
            # Match the object's world position
            pos = node_path.getPos(self.base.render)
            self.gizmo_root.setPos(pos)
            # Keep gizmo axis-aligned (no rotation) and unit scale
            self.gizmo_root.setHpr(0, 0, 0)
            self.gizmo_root.setScale(1, 1, 1)
            # Only show gizmo if not in select mode
            if self.active_mode in ['TRANSLATE', 'SCALE', 'ROTATE']:
                self.gizmo_root.show()
            else:
                self.gizmo_root.hide()
        else:
            self.gizmo_root.hide()
            self.gizmo_root.reparentTo(self.base.render)

    def _create_visuals(self):
        # Translate & Scale Visuals (Length 0.75)
        self.t_x = self._draw_line((1,0,0), (0,0,0), (0.75,0,0))
        self.t_y = self._draw_line((0,1,0), (0,0,0), (0,0.75,0))
        self.t_z = self._draw_line((0,0,1), (0,0,0), (0,0,0.75))

        # Translate caps (cones)
        self.t_cap_x = self._create_cone((1,0,0), 'x')
        self.t_cap_y = self._create_cone((0,1,0), 'y')
        self.t_cap_z = self._create_cone((0,0,1), 'z')

        self.s_x = self._draw_line((1,0.5,0), (0,0,0), (0.75,0,0))
        self.s_y = self._draw_line((1,0.5,0), (0,0,0), (0,0.75,0))
        self.s_z = self._draw_line((1,0.5,0), (0,0,0), (0,0,0.75))

        # Scale caps (cubes)
        self.s_cap_x = self._create_cube((1,0.5,0), 'x')
        self.s_cap_y = self._create_cube((1,0.5,0), 'y')
        self.s_cap_z = self._create_cube((1,0.5,0), 'z')

        # Rotate Visuals (Radius 0.75)
        self.r_x = self._draw_circle((1,0,0), "x")
        self.r_y = self._draw_circle((0,1,0), "y")
        self.r_z = self._draw_circle((0,0,1), "z")

    def _create_colliders(self):
        # Straight Tubes for Translate and Scale
        self.col_t_x = self._add_tube("gizmo_x", (0,0,0), (0.75,0,0))
        self.col_t_y = self._add_tube("gizmo_y", (0,0,0), (0,0.75,0))
        self.col_t_z = self._add_tube("gizmo_z", (0,0,0), (0,0,0.75))

        # Ring/Torus segments for Rotate
        self.col_r_x = self._add_ring_collider("gizmo_x", "x")
        self.col_r_y = self._add_ring_collider("gizmo_y", "y")
        self.col_r_z = self._add_ring_collider("gizmo_z", "z")

    def _add_tube(self, name, p1, p2):
        from panda3d.core import CollisionNode, CollisionTube, BitMask32
        tube = CollisionTube(*p1, *p2, 0.125)
        cnode = CollisionNode(name)
        cnode.addSolid(tube)
        cnode.setIntoCollideMask(BitMask32.bit(2))
        np = self.gizmo_root.attachNewNode(cnode)
        np.hide()  # Explicitly hide collision visualization
        # np.show() # <--- UNCOMMENT THIS TO SEE THE HITBOXES IN-GAME!
        return np

    def _add_ring_collider(self, name, axis):
        from panda3d.core import CollisionNode, CollisionTube, BitMask32
        import math
        cnode = CollisionNode(name)
        segments = 12
        radius = 0.75
        for i in range(segments):
            a1 = math.radians(i * (360/segments))
            a2 = math.radians((i+1) * (360/segments))
            if axis == "z":
                p1 = (math.cos(a1)*radius, math.sin(a1)*radius, 0)
                p2 = (math.cos(a2)*radius, math.sin(a2)*radius, 0)
            elif axis == "y":
                p1 = (math.cos(a1)*radius, 0, math.sin(a1)*radius)
                p2 = (math.cos(a2)*radius, 0, math.sin(a2)*radius)
            elif axis == "x":
                p1 = (0, math.cos(a1)*radius, math.sin(a1)*radius)
                p2 = (0, math.cos(a2)*radius, math.sin(a2)*radius)
            cnode.addSolid(CollisionTube(*p1, *p2, 0.1))

        cnode.setIntoCollideMask(BitMask32.bit(2))
        np = self.gizmo_root.attachNewNode(cnode)
        np.hide()  # Explicitly hide collision visualization
        # np.show() # <--- UNCOMMENT THIS TO SEE THE HITBOXES IN-GAME!
        return np

    def _draw_line(self, color, start, end):
        ls = LineSegs()
        ls.setThickness(9.5)
        ls.setColor(*color, 1.0)
        ls.moveTo(*start)
        ls.drawTo(*end)
        np = self.gizmo_root.attachNewNode(ls.create())
        return np

    def _draw_circle(self, color, axis):
        import math
        ls = LineSegs()
        ls.setThickness(9.5)
        ls.setColor(*color, 1.0)
        for i in range(37):
            rad = math.radians(i * 10)
            c, s = math.cos(rad) * 0.75, math.sin(rad) * 0.75
            if axis == "z": ls.drawTo(c, s, 0)
            elif axis == "y": ls.drawTo(c, 0, s)
            elif axis == "x": ls.drawTo(0, c, s)
        np = self.gizmo_root.attachNewNode(ls.create())
        return np

    def _create_cone(self, color, axis):
        """Create a cone (arrowhead) for the translate gizmo."""
        # Create vertex data
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('cone', format, Geom.UHDynamic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')

        # Cone parameters
        radius = 0.2
        height = 0.3
        segments = 8

        # Tip of the cone
        vertex.addData3(0, 0, height)
        normal.addData3(0, 0, 1)

        # Base center
        vertex.addData3(0, 0, 0)
        normal.addData3(0, 0, -1)

        # Base ring vertices
        for i in range(segments):
            angle = (i / segments) * 2 * 3.14159
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertex.addData3(x, y, 0)
            # Normal points outward and slightly up
            nx = math.cos(angle)
            ny = math.sin(angle)
            normal.addData3(nx, ny, 0.3)

        # Create triangles
        tris = GeomTriangles(Geom.UHDynamic)

        # Side triangles (fan from tip to base ring)
        for i in range(segments):
            next_i = (i + 1) % segments
            # Tip (0) to base edge (2+i, 2+next_i)
            tris.addVertices(0, 2 + i, 2 + next_i)

        # Base triangles (fan from base center)
        for i in range(1, segments - 1):
            tris.addVertices(1, 2 + i, 2 + i + 1)

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        node = GeomNode('cone')
        node.addGeom(geom)

        cone = NodePath(node)
        cone.setColor(*color, 1.0)
        cone.setScale(0.6, 0.6, 0.6)  # 2x smaller (was 0.1,0.1,0.15)
        if axis == 'x':
            cone.setPos(0.75, 0, 0)
            cone.setHpr(90, 90, 0)   # Pitch +90: Z -> +X
        elif axis == 'y':
            cone.setPos(0, 0.75, 0)
            cone.setHpr(270, 0, -90)  # Roll -90: Z -> +Y
        elif axis == 'z':
            cone.setPos(0, 0, 0.75)
            cone.setHpr(0, 0, 0)    # Already points +Z
        cone.reparentTo(self.gizmo_root)
        cone.setLightOff()
        return cone

    def _create_cube(self, color, axis):
        """Create a cube for the scale gizmo."""
        # Create vertex data
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('cube', format, Geom.UHDynamic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')

        s = 0.075  # Half-size of cube

        # 6 faces, each with 4 vertices = 24 vertices
        # Format: (vertices for face, normal for face)
        faces_data = [
            # Front face (z = -s), normal (0, 0, -1)
            [(-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s)], (0, 0, -1),
            # Back face (z = s), normal (0, 0, 1)
            [(s, -s, s), (-s, -s, s), (-s, s, s), (s, s, s)], (0, 0, 1),
            # Left face (x = -s), normal (-1, 0, 0)
            [(-s, -s, s), (-s, -s, -s), (-s, s, -s), (-s, s, s)], (-1, 0, 0),
            # Right face (x = s), normal (1, 0, 0)
            [(s, -s, -s), (s, -s, s), (s, s, s), (s, s, -s)], (1, 0, 0),
            # Bottom face (y = -s), normal (0, -1, 0)
            [(-s, -s, -s), (-s, -s, s), (s, -s, s), (s, -s, -s)], (0, -1, 0),
            # Top face (y = s), normal (0, 1, 0)
            [(-s, s, s), (-s, s, -s), (s, s, -s), (s, s, s)], (0, 1, 0),
        ]

        for i in range(0, len(faces_data), 2):
            face_verts = faces_data[i]
            face_normal = faces_data[i + 1]
            for v in face_verts:
                vertex.addData3(*v)
                normal.addData3(*face_normal)

        # Create triangles (2 per face, 12 total)
        tris = GeomTriangles(Geom.UHDynamic)
        for face in range(6):
            base = face * 4
            # Triangle 1: 0, 1, 2
            tris.addVertices(base, base + 1, base + 2)
            # Triangle 2: 0, 2, 3
            tris.addVertices(base, base + 2, base + 3)

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        node = GeomNode('cube')
        node.addGeom(geom)

        cube = NodePath(node)
        cube.setColor(*color, 1.0)
        cube.setScale(0.666, 0.666, 0.666)  # 3x smaller than previous scale(2)
        if axis == 'x':
            cube.setPos(0.75, 0, 0)
        elif axis == 'y':
            cube.setPos(0, 0.75, 0)
        elif axis == 'z':
            cube.setPos(0, 0, 0.75)
        cube.reparentTo(self.gizmo_root)
        cube.setLightOff()
        return cube

    def set_mode(self, mode):
        """Switch gizmo mode with explicit state management."""
        self.active_mode = mode.upper()

        # === STEP 1: Hide all visuals ===
        for np in [self.t_x, self.t_y, self.t_z, self.t_cap_x, self.t_cap_y, self.t_cap_z,
                   self.s_x, self.s_y, self.s_z, self.s_cap_x, self.s_cap_y, self.s_cap_z,
                   self.r_x, self.r_y, self.r_z]:
            np.hide()

        # === STEP 2: Hide all colliders (remove from collision tree) ===
        # Use reparentTo to fully remove from collision traverser instead of stash/unstash
        for np in [self.col_t_x, self.col_t_y, self.col_t_z, self.col_r_x, self.col_r_y, self.col_r_z]:
            np.reparentTo(self.base.render)  # Move out of gizmo_root
            np.hide()

        # === STEP 3: Show visuals and re-attach colliders for active mode ===
        if self.active_mode == 'TRANSLATE':
            self.t_x.show()
            self.t_y.show()
            self.t_z.show()
            self.t_cap_x.show()
            self.t_cap_y.show()
            self.t_cap_z.show()
            # Re-attach translate colliders to gizmo_root
            self.col_t_x.reparentTo(self.gizmo_root)
            self.col_t_y.reparentTo(self.gizmo_root)
            self.col_t_z.reparentTo(self.gizmo_root)
        elif self.active_mode == 'SCALE':
            self.s_x.show()
            self.s_y.show()
            self.s_z.show()
            self.s_cap_x.show()
            self.s_cap_y.show()
            self.s_cap_z.show()
            # Re-attach scale colliders (same as translate) to gizmo_root
            self.col_t_x.reparentTo(self.gizmo_root)
            self.col_t_y.reparentTo(self.gizmo_root)
            self.col_t_z.reparentTo(self.gizmo_root)
        elif self.active_mode == 'ROTATE':
            self.r_x.show()
            self.r_y.show()
            self.r_z.show()
            # Re-attach rotate colliders to gizmo_root
            self.col_r_x.reparentTo(self.gizmo_root)
            self.col_r_y.reparentTo(self.gizmo_root)
            self.col_r_z.reparentTo(self.gizmo_root)
        # SELECT mode - hide gizmo, no colliders needed

        # === STEP 4: Update gizmo_root visibility ===
        if self.selected_node and self.active_mode in ['TRANSLATE', 'SCALE', 'ROTATE']:
            self.gizmo_root.show()
        else:
            self.gizmo_root.hide()

        # === STEP 5: Reset highlight ===
        self.set_highlight(None)

    def set_highlight(self, axis):
        # Reset all
        for np in [self.t_x, self.t_y, self.t_z, self.t_cap_x, self.t_cap_y, self.t_cap_z,
                   self.s_x, self.s_y, self.s_z, self.s_cap_x, self.s_cap_y, self.s_cap_z,
                   self.r_x, self.r_y, self.r_z]:
            np.setColorScale(1, 1, 1, 1)

        if not axis: return
        boost = (2.5, 2.5, 2.5, 1.0)

        if self.active_mode == 'TRANSLATE':
            if axis == 'X':
                self.t_x.setColorScale(boost)
                self.t_cap_x.setColorScale(boost)
            elif axis == 'Y':
                self.t_y.setColorScale(boost)
                self.t_cap_y.setColorScale(boost)
            elif axis == 'Z':
                self.t_z.setColorScale(boost)
                self.t_cap_z.setColorScale(boost)
        elif self.active_mode == 'SCALE':
            if axis == 'X':
                self.s_x.setColorScale(boost)
                self.s_cap_x.setColorScale(boost)
            elif axis == 'Y':
                self.s_y.setColorScale(boost)
                self.s_cap_y.setColorScale(boost)
            elif axis == 'Z':
                self.s_z.setColorScale(boost)
                self.s_cap_z.setColorScale(boost)
        elif self.active_mode == 'ROTATE':
            if axis == 'X': self.r_x.setColorScale(boost)
            elif axis == 'Y': self.r_y.setColorScale(boost)
            elif axis == 'Z': self.r_z.setColorScale(boost)

    def update_scale_task(self, task):
        if not self.gizmo_root.isHidden() and self.selected_node:
            # Sync gizmo position with selected object's world position
            obj_pos = self.selected_node.getPos(self.base.render)
            self.gizmo_root.setPos(obj_pos)

            # Constant screen size scaling
            dist = (self.base.camera.getPos(self.base.render) - obj_pos).length()
            scale = dist * 0.15
            self.gizmo_root.setScale(self.base.render, scale, scale, scale)
        return task.cont
