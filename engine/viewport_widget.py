"""
PySide6 widget that embeds the Panda3D render window.
"""

import sys
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QKeyEvent
from engine.panda_app import PandaApp
from engine.editor_camera import EditorCamera
from engine.core.game_loop import game_loop
from panda3d.core import WindowProperties, Point2, Point3, Vec3, Plane, BitMask32, CollisionNode, CollisionRay, CollisionSegment, CollisionTraverser, CollisionHandlerQueue, Quat, GeomNode
import math
from engine.core.command_system import history
from editor.editor_commands import TransformCommand

class ViewportWidget(QWidget):
    object_moved_signal = Signal(object)  # Emitted when object is moved via gizmo
    object_selected_signal = Signal(object)  # Emitted when object is selected via click
    hotkey_triggered = Signal(str)  # Emitted when editor hotkeys are pressed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.panda_app = None
        self.timer = None
        self.camera_controller = None
        self.gizmo_manager = None
        self.dragging = False
        self.drag_axis = None
        self.drag_start_pos = None
        self.drag_start_hpr = None
        self.drag_start_scale = None
        self.drag_plane = None
        self.drag_start_point = None
        self.selected_game_object = None
        self.hovered_axis = "NEEDS_RESET"  # Track currently hovered gizmo axis
        self.mouse_pos = None  # Will store the latest mouse position from Qt
        self.event_sheet_processor = None  # Set by MainWindow after construction
        self.setMouseTracking(True)
        # Ensure widget can accept focus via click and keyboard
        self.setFocusPolicy(Qt.StrongFocus)
        self.init_panda()

    def init_panda(self):
        """Initialize Panda3D embedded window and input bindings."""
        # Create Panda3D app with this widget as parent
        self.panda_app = PandaApp(parent_window_handle=int(self.winId()))

        # Set up camera controller
        self.camera_controller = EditorCamera(self.panda_app)

        # Set up persistent raycaster for gizmo picking
        self.picker_node = CollisionNode('mouseRay')
        self.picker_ray = CollisionRay()
        self.picker_node.addSolid(self.picker_ray)
        self.picker_node.setFromCollideMask(BitMask32.bit(1) | BitMask32.bit(2))
        self.picker_np = self.panda_app.camera.attachNewNode(self.picker_node)
        self.traverser = CollisionTraverser('viewport_traverser')
        self.queue = CollisionHandlerQueue()
        self.traverser.addCollider(self.picker_np, self.queue)

        # --- THIS IS THE MISSING ENGINE DRIVER ---
        print("DEBUG: Reinstalling Panda3D Task Manager driver (QTimer).")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_panda_task)
        self.timer.start(0)  # Run as fast as possible

        # Bind Panda3D mouse events
        self.panda_app.accept("mouse1", self.on_panda_mouse_down)
        self.panda_app.accept("mouse1-up", self.on_mouse_up)
        self.panda_app.accept("mouse3", self.on_right_mouse_down)
        self.panda_app.accept("mouse3-up", self.on_right_mouse_up)
        self.panda_app.accept("mouse2", self.on_middle_mouse_down)
        self.panda_app.accept("mouse2-up", self.on_middle_mouse_up)
        self.panda_app.accept("wheel_up", self.on_wheel_up)
        self.panda_app.accept("wheel_down", self.on_wheel_down)

        # Key event bridge: Panda3D's native window steals OS keyboard focus
        # from Qt when clicked, so Qt's keyPressEvent never fires. We catch
        # keys inside Panda3D's event system and route them via Qt signals.
        self.panda_app.accept("q", lambda: self.hotkey_triggered.emit('Q'))
        self.panda_app.accept("w", lambda: self.hotkey_triggered.emit('W'))
        self.panda_app.accept("e", lambda: self.hotkey_triggered.emit('E'))
        self.panda_app.accept("r", lambda: self.hotkey_triggered.emit('R'))
        self.panda_app.accept("f", lambda: self.hotkey_triggered.emit('F'))
        self.panda_app.accept("p", lambda: self._panda_key_play())
        self.panda_app.accept("o", lambda: self._panda_key_pause())
        self.panda_app.accept("l", lambda: self._panda_key_stop())
        self.panda_app.accept("control-c", lambda: self.window().copy_selected_object() if hasattr(self.window(), 'copy_selected_object') else None)
        self.panda_app.accept("control-v", lambda: self.window().paste_object() if hasattr(self.window(), 'paste_object') else None)
        self.panda_app.accept("delete", lambda: self.window().delete_selected_object() if hasattr(self.window(), 'delete_selected_object') else None)

        # Add a Panda3D task to handle continuous mouse movement
        self.panda_app.taskMgr.add(self.mouse_update_task, "ViewportMouseUpdateTask")

        # Add a dedicated task for gizmo hover highlighting
        self.panda_app.taskMgr.add(self.update_hover_task, "GizmoHoverTask")

    def update_panda_task(self):
        """Step Panda3D's task manager and update game loop."""
        # 1. Step Panda3D's internal tasks (Rendering, Window Events)
        if hasattr(self, 'panda_app') and self.panda_app.taskMgr is not None:
            self.panda_app.taskMgr.step()

        # 2. MANUALLY FORCE THE GAME LOOP TO TICK
        try:
            from panda3d.core import ClockObject
            from engine.core.game_loop import game_loop

            # String conversion bypasses Enum reference errors
            if str(game_loop.state) == "EngineState.PLAYING" or getattr(game_loop.state, 'name', '') == 'PLAYING':
                dt = ClockObject.getGlobalClock().getDt()

                # A. Step Physics
                from engine.core.physics_world import physics_world
                physics_world.update(dt)

                # B. Sync Rigidbodies (physics -> visual) before collision checks
                from engine.core.scene_manager import scene_manager
                from engine.components.rigidbody_component import RigidbodyComponent
                all_objs = list(scene_manager.get_all_game_objects())
                for go in all_objs:
                    rb = go.get_component(RigidbodyComponent)
                    if rb:
                        rb.on_update(dt)

                # C. Update all other Components (including Colliders)
                for go in all_objs:
                    comps = go.components.values() if isinstance(go.components, dict) else go.components
                    for comp in comps:
                        # Skip RigidbodyComponent - already updated
                        if isinstance(comp, RigidbodyComponent):
                            continue
                        if hasattr(comp, 'on_update'):
                            comp.on_update(dt)

                # D. Run Event Sheet logic
                if self.event_sheet_processor:
                    self.event_sheet_processor.update(dt)

        except Exception as e:
            import traceback
            print(f"CRITICAL ENGINE ERROR IN QT TICK:\n{traceback.format_exc()}")

    def mousePressEvent(self, event):
        """Handle Qt mouse press events for viewport clicking."""
        # Left click - perform selection raycast
        if event.button() == Qt.MouseButton.LeftButton:
            # Grant keyboard focus to this widget so keyPressEvent works
            self.setFocus(Qt.MouseFocusReason)
            # Get mouse position from Qt event
            qt_pos = event.position()
            # Perform the actual selection raycast with Qt coordinates
            self.perform_selection_raycast_qt(qt_pos)
        
        super().mousePressEvent(event)

    def on_panda_mouse_down(self):
        """Panda3D native mouse click handler - grants Qt focus and selects."""
        # Grant keyboard focus to this widget so keyPressEvent works
        self.setFocus(Qt.MouseFocusReason)
        # Perform the actual selection raycast
        self.perform_selection_raycast()

    def perform_selection_raycast_qt(self, qt_pos):
        """Perform raycast using Qt mouse position with direct lens extrusion."""
        if self.panda_app is None or self.panda_app.camera is None:
            print("[DEBUG] No panda_app or camera")
            return

        # Validate viewport dimensions
        if self.width() <= 0 or self.height() <= 0:
            print(f"[DEBUG] Invalid viewport size: {self.width()}x{self.height()}")
            return

        # Convert Qt pixel coordinates to normalized device coordinates [-1, 1]
        ndc_x = (qt_pos.x() / self.width()) * 2.0 - 1.0
        ndc_y = -((qt_pos.y() / self.height()) * 2.0 - 1.0)  # Flip Y for Panda3D

        # Extrude ray directly from camera lens
        near_point = Point3()
        far_point = Point3()
        self.panda_app.camLens.extrude(Point2(ndc_x, ndc_y), near_point, far_point)

        # Transform points from camera space to render (world) space
        near_world = self.panda_app.render.getRelativePoint(self.panda_app.camera, near_point)
        far_world = self.panda_app.render.getRelativePoint(self.panda_app.camera, far_point)

        # Create collision segment (more reliable than ray for embedded windows)
        picker_segment = CollisionSegment(near_world, far_world)
        picker_node = CollisionNode('mouseSegment')
        picker_node.addSolid(picker_segment)
        # Only collide with GameObjects (bit 1), ignore gizmos
        picker_node.setFromCollideMask(BitMask32.bit(1))
        picker_node.setIntoCollideMask(BitMask32.allOff())

        picker_np = self.panda_app.render.attachNewNode(picker_node)
        picker_traverser = CollisionTraverser('mouse_picker')
        picker_queue = CollisionHandlerQueue()
        picker_traverser.addCollider(picker_np, picker_queue)

        # Perform traversal
        picker_traverser.traverse(self.panda_app.render)

        if picker_queue.getNumEntries() > 0:
            picker_queue.sortEntries()
            for i in range(picker_queue.getNumEntries()):
                hit_entry = picker_queue.getEntry(i)
                hit_np = hit_entry.getIntoNodePath()
                
                # Traverse up to find GameObject tag
                game_obj_np = hit_np.findNetPythonTag("game_object")
                if not game_obj_np.isEmpty():
                    game_object = game_obj_np.getPythonTag("game_object")
                    if game_object:
                        self.selected_game_object = game_object
                        self.gizmo_manager.set_selected_node(game_object.node_path)
                        self.update_outline(game_object.node_path)
                        
                        if hasattr(self.gizmo_manager, 'selection_callback') and self.gizmo_manager.selection_callback:
                            self.gizmo_manager.selection_callback(game_object.node_path)
                        
                        if hasattr(self, 'object_selected_signal'):
                            self.object_selected_signal.emit(self.selected_game_object)
                        picker_np.removeNode()
                        return
            
            # No valid GameObject found in hits
            self.gizmo_manager.set_selected_node(None)
            self.update_outline(None)
            self.selected_game_object = None
            if hasattr(self, 'object_selected_signal'):
                self.object_selected_signal.emit(None)
        else:
            # Nothing hit - clear selection
            self.gizmo_manager.set_selected_node(None)
            self.update_outline(None)
            self.selected_game_object = None
            if hasattr(self, 'object_selected_signal'):
                self.object_selected_signal.emit(None)

        picker_np.removeNode()

    def perform_selection_raycast(self):
        """Perform raycast to select objects or interact with gizmos using direct lens extrusion."""
        if not self.panda_app.mouseWatcherNode.hasMouse():
            return

        m_x = self.panda_app.mouseWatcherNode.getMouseX()
        m_y = self.panda_app.mouseWatcherNode.getMouseY()

        # Extrude ray from lens
        near_point = Point3()
        far_point = Point3()
        self.panda_app.camLens.extrude(Point2(m_x, m_y), near_point, far_point)
        near_world = self.panda_app.render.getRelativePoint(self.panda_app.camera, near_point)
        far_world = self.panda_app.render.getRelativePoint(self.panda_app.camera, far_point)

        # Create collision segment
        picker_segment = CollisionSegment(near_world, far_world)
        picker_node = CollisionNode('mouseSegment')
        picker_node.addSolid(picker_segment)
        picker_node.setFromCollideMask(BitMask32.bit(1) | BitMask32.bit(2))  # GameObjects + Gizmos
        picker_node.setIntoCollideMask(BitMask32.allOff())

        picker_np = self.panda_app.render.attachNewNode(picker_node)
        picker_traverser = CollisionTraverser('mouse_picker')
        picker_queue = CollisionHandlerQueue()
        picker_traverser.addCollider(picker_np, picker_queue)
        picker_traverser.traverse(self.panda_app.render)

        if self.gizmo_manager:
            mode = getattr(self.gizmo_manager, 'active_mode', 'TRANSLATE')

        if picker_queue.getNumEntries() > 0:
            picker_queue.sortEntries()

            hit_gizmo = None
            hit_scene = None

            for i in range(picker_queue.getNumEntries()):
                entry = picker_queue.getEntry(i)
                name = entry.getIntoNode().getName()

                if name in ["gizmo_x", "gizmo_y", "gizmo_z"]:
                    hit_gizmo = entry
                    break
                elif hit_scene is None:
                    hit_scene = entry

            if hit_gizmo:
                if not self.gizmo_manager.selected_node:
                    picker_np.removeNode()
                    return

                self.dragging = True
                self.drag_axis = hit_gizmo.getIntoNode().getName()[-1].upper()
                self.gizmo_manager.dragging = True
                self.gizmo_manager.locked_axis = self.drag_axis.lower()
                self.gizmo_manager.set_highlight(self.drag_axis)

                self.drag_start_pos = self.gizmo_manager.selected_node.getPos(self.panda_app.render)
                self.drag_start_hpr = self.gizmo_manager.selected_node.getHpr(self.panda_app.render)
                self.drag_start_scale = self.gizmo_manager.selected_node.getScale(self.panda_app.render)
                
                # Store original transform for Undo
                self.original_transform_state = (
                    Point3(self.drag_start_pos),
                    Point3(self.drag_start_hpr),
                    Point3(self.drag_start_scale)
                )

                # Setup Math Plane based on mode
                if mode == 'ROTATE':
                    if self.drag_axis == 'X': self.drag_plane = Plane(Vec3(1,0,0), self.drag_start_pos)
                    elif self.drag_axis == 'Y': self.drag_plane = Plane(Vec3(0,1,0), self.drag_start_pos)
                    else: self.drag_plane = Plane(Vec3(0,0,1), self.drag_start_pos)
                else:  # Translate / Scale
                    if self.drag_axis in ['X', 'Y']:
                        self.drag_plane = Plane(Vec3(0,0,1), self.drag_start_pos)
                    else:
                        cam_v = self.panda_app.camera.getPos(self.panda_app.render) - self.drag_start_pos
                        cam_v.setZ(0)
                        if cam_v.lengthSquared() == 0: cam_v = Vec3(0,-1,0)
                        self.drag_plane = Plane(cam_v, self.drag_start_pos)

                # Store the start point for dragging
                self.drag_start_point = Point3()
                self.drag_plane.intersectsLine(self.drag_start_point, near_world, far_world)

            elif hit_scene:
                target_np = hit_scene.getIntoNodePath()
                game_obj_np = target_np.findNetPythonTag("game_object")
                
                if not game_obj_np.isEmpty():
                    game_object = game_obj_np.getPythonTag("game_object")
                    if game_object:
                        self.selected_game_object = game_object
                        self.gizmo_manager.set_selected_node(game_object.node_path)
                        self.update_outline(game_object.node_path)
                        
                        if hasattr(self.gizmo_manager, 'selection_callback') and self.gizmo_manager.selection_callback:
                            self.gizmo_manager.selection_callback(game_object.node_path)
                        
                        if hasattr(self, 'object_selected_signal'):
                            self.object_selected_signal.emit(self.selected_game_object)
                    else:
                        self.gizmo_manager.set_selected_node(None)
                        self.update_outline(None)
                        self.selected_game_object = None
                        if hasattr(self, 'object_selected_signal'):
                            self.object_selected_signal.emit(None)
                else:
                    self.gizmo_manager.set_selected_node(None)
                    self.update_outline(None)
                    self.selected_game_object = None
                    if hasattr(self, 'object_selected_signal'):
                        self.object_selected_signal.emit(None)
                        
            else:
                self.gizmo_manager.set_selected_node(None)
                self.update_outline(None)
                self.selected_game_object = None
                if hasattr(self, 'object_selected_signal'):
                    self.object_selected_signal.emit(None)
        else:
            # Nothing hit - clear selection
            self.gizmo_manager.set_selected_node(None)
            self.update_outline(None)
            self.selected_game_object = None
            if hasattr(self, 'object_selected_signal'):
                self.object_selected_signal.emit(None)

        picker_np.removeNode()

    def contextMenuEvent(self, event):
        """Handle right-click context menu in the viewport."""
        # Raycast to select object at cursor position before showing menu
        self.perform_selection_raycast_qt(event.position())

        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        copy_act = menu.addAction("Copy (Ctrl+C)")
        paste_act = menu.addAction("Paste (Ctrl+V)")
        menu.addSeparator()
        delete_act = menu.addAction("Delete (Del)")

        # Enable/Disable based on selection
        if not self.selected_game_object:
            copy_act.setEnabled(False)
            delete_act.setEnabled(False)

        main_win = self.window()
        selected_action = menu.exec(event.globalPos())

        if selected_action == copy_act:
            if hasattr(main_win, 'copy_selected_object'):
                main_win.copy_selected_object()
        elif selected_action == paste_act:
            if hasattr(main_win, 'paste_object'):
                main_win.paste_object()
        elif selected_action == delete_act:
            if hasattr(main_win, 'delete_selected_object'):
                main_win.delete_selected_object()

    def keyPressEvent(self, event):
        """Handle keyboard input and emit hotkey signals for editor tools."""
        key = event.key()
        modifiers = event.modifiers()
        ctrl = modifiers & Qt.ControlModifier
        
        # Copy / Paste / Delete Shortcuts
        if ctrl and key == Qt.Key_C:
            main_win = self.window()
            if hasattr(main_win, 'copy_selected_object'):
                main_win.copy_selected_object()
            event.accept()
            return
        elif ctrl and key == Qt.Key_V:
            main_win = self.window()
            if hasattr(main_win, 'paste_object'):
                main_win.paste_object()
            event.accept()
            return
        elif key == Qt.Key_Delete:
            main_win = self.window()
            if hasattr(main_win, 'delete_selected_object'):
                main_win.delete_selected_object()
            event.accept()
            return

        # Emit hotkey signals for editor tool shortcuts
        if key == Qt.Key_Q:
            self.hotkey_triggered.emit('Q')
            event.accept()
            return
        elif key == Qt.Key_W:
            self.hotkey_triggered.emit('W')
            event.accept()
            return
        elif key == Qt.Key_E:
            self.hotkey_triggered.emit('E')
            event.accept()
            return
        elif key == Qt.Key_R:
            self.hotkey_triggered.emit('R')
            event.accept()
            return
        elif key == Qt.Key_F:
            self.hotkey_triggered.emit('F')
            event.accept()
            return
        
        # Playback shortcuts (viewport-specific)
        elif key == Qt.Key_P:
            from engine.core.game_loop import game_loop
            game_loop.play()
            event.accept()
            return
        elif key == Qt.Key_O:
            from engine.core.game_loop import game_loop
            game_loop.pause()
            event.accept()
            return
        elif key == Qt.Key_L:
            from engine.core.game_loop import game_loop
            game_loop.stop()
            event.accept()
            return
        
        # Pass through any other keys
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Ignore all key release events to prevent focus issues."""
        event.ignore()
        super().keyReleaseEvent(event)

    # --- Panda3D key bridge helpers (called from accept() lambdas) ---
    def _panda_key_play(self):
        from engine.core.game_loop import game_loop
        game_loop.play()

    def _panda_key_pause(self):
        from engine.core.game_loop import game_loop
        game_loop.pause()

    def _panda_key_stop(self):
        from engine.core.game_loop import game_loop
        game_loop.stop()

    def update_outline(self, node):
        """Create or update the selection outline around a node."""
        # Clean up existing outline
        if hasattr(self, 'outline_np') and self.outline_np is not None:
            if not self.outline_np.isEmpty():
                self.outline_np.removeNode()
            self.outline_np = None

        if node is None:
            return

        # Create outline as a copy of the node
        self.outline_np = node.copyTo(self.panda_app.render)
        self.outline_np.setName("selection_outline")
        self.outline_np.setPythonTag("managed", True)

        # Remove collision nodes and gizmo children from outline
        for c_node in self.outline_np.findAllMatches("**/+CollisionNode"):
            c_node.removeNode()
        for gizmo_child in self.outline_np.findAllMatches("**/gizmo"):
            gizmo_child.removeNode()

        # Match the node's transform
        self.outline_np.setTransform(node.getTransform(self.panda_app.render))

        # Style as wireframe outline
        self.outline_np.setRenderModeWireframe()
        self.outline_np.setRenderModeThickness(4.0)
        self.outline_np.setColor(1.0, 0.5, 0.0, 1.0, 1)  # Orange with priority 1
        
        # Scale up slightly so it doesn't z-fight with the object itself
        current_scale = self.outline_np.getScale()
        self.outline_np.setScale(current_scale * 1.05)
        
        self.outline_np.setLightOff(1)
        self.outline_np.setBin("fixed", 41)
        self.outline_np.setDepthTest(False)
        self.outline_np.setDepthWrite(False)
        self.outline_np.setTextureOff(1)

        # Reparent to the node to follow it
        self.outline_np.wrtReparentTo(node)

    def focus_on_selected(self):
        if not self.selected_game_object:
            return
            
        # Get object bounds
        bounds = self.selected_game_object.node_path.getTightBounds()
        if bounds:
            min_b, max_b = bounds
            center = (min_b + max_b) / 2.0
            
            # Use camera controller's focus_on method
            self.camera_controller.focus_on(self.selected_game_object.node_path)

    def on_mouse_up(self):
        if self.dragging and self.gizmo_manager and self.gizmo_manager.selected_node:
            # Record transform command for Undo/Redo
            new_state = (
                Point3(self.gizmo_manager.selected_node.getPos(self.panda_app.render)),
                Point3(self.gizmo_manager.selected_node.getHpr(self.panda_app.render)),
                Point3(self.gizmo_manager.selected_node.getScale(self.panda_app.render))
            )
            # Only record if something actually changed
            if hasattr(self, 'original_transform_state') and self.original_transform_state != new_state:
                game_object = self.gizmo_manager.selected_node.getPythonTag("game_object")
                if game_object:
                    cmd = TransformCommand(game_object, self.original_transform_state, new_state)
                    history.execute(cmd)

        self.dragging = False
        self.drag_axis = None
        if self.gizmo_manager:
            self.gizmo_manager.dragging = False
            self.gizmo_manager.locked_axis = None
        self.hovered_axis = "NEEDS_RESET"

    def on_right_mouse_down(self):
        if self.panda_app.mouseWatcherNode.hasMouse():
            ndc_x = self.panda_app.mouseWatcherNode.getMouseX()
            ndc_y = self.panda_app.mouseWatcherNode.getMouseY()
            pixel_x = (ndc_x + 1) * 0.5 * self.width()
            pixel_y = (1 - ndc_y) * 0.5 * self.height()
            self.camera_controller.start_look((pixel_x, pixel_y))

    def on_right_mouse_up(self):
        self.camera_controller.stop_look()

    def on_middle_mouse_down(self):
        if self.panda_app.mouseWatcherNode.hasMouse():
            ndc_x = self.panda_app.mouseWatcherNode.getMouseX()
            ndc_y = self.panda_app.mouseWatcherNode.getMouseY()
            pixel_x = (ndc_x + 1) * 0.5 * self.width()
            pixel_y = (1 - ndc_y) * 0.5 * self.height()
            self.camera_controller.start_pan((pixel_x, pixel_y))

    def on_middle_mouse_up(self):
        self.camera_controller.stop_pan()

    def on_wheel_up(self):
        self.camera_controller.zoom(1.0)

    def on_wheel_down(self):
        self.camera_controller.zoom(-1.0)

    def mouseMoveEvent(self, event):
        """Capture Qt local mouse position for hover detection."""
        self.mouse_pos = event.position()
        super().mouseMoveEvent(event)

    def mouse_update_task(self, task):
        dt = task.dt
        game_loop.update(dt)
        
        if not self.panda_app.mouseWatcherNode.hasMouse():
            return task.cont

        if self.gizmo_manager and self.gizmo_manager.dragging and self.gizmo_manager.selected_node:
            if self.drag_plane is None:
                self.on_mouse_up()
                return task.cont

            m_x = self.panda_app.mouseWatcherNode.getMouseX()
            m_y = self.panda_app.mouseWatcherNode.getMouseY()

            p_near, p_far = Point3(), Point3()
            self.panda_app.camLens.extrude(Point2(m_x, m_y), p_near, p_far)
            p_near = self.panda_app.render.getRelativePoint(self.panda_app.camera, p_near)
            p_far = self.panda_app.render.getRelativePoint(self.panda_app.camera, p_far)

            current_hit = Point3()
            if self.drag_plane.intersectsLine(current_hit, p_near, p_far):
                mode = self.gizmo_manager.active_mode

                if mode == 'TRANSLATE':
                    delta_vec = current_hit - self.drag_start_point
                    new_pos = Point3(self.drag_start_pos)

                    if self.drag_axis == 'X':
                        shift = delta_vec.dot(Vec3(1, 0, 0))
                        new_pos.setX(new_pos.getX() + shift)
                    elif self.drag_axis == 'Y':
                        shift = delta_vec.dot(Vec3(0, 1, 0))
                        new_pos.setY(new_pos.getY() + shift)
                    elif self.drag_axis == 'Z':
                        shift = delta_vec.dot(Vec3(0, 0, 1))
                        new_pos.setZ(new_pos.getZ() + shift)

                    self.gizmo_manager.selected_node.setPos(self.panda_app.render, new_pos)

                elif mode == 'ROTATE':
                    start_vec = self.drag_start_point - self.drag_start_pos
                    current_vec = current_hit - self.drag_start_pos

                    # Determine rotation axis
                    if self.drag_axis == 'X':
                        axis = Vec3(1, 0, 0)
                    elif self.drag_axis == 'Y':
                        axis = Vec3(0, 1, 0)
                    else:  # Z
                        axis = Vec3(0, 0, 1)

                    # Project vectors onto plane perpendicular to rotation axis
                    start_proj = start_vec - axis * start_vec.dot(axis)
                    current_proj = current_vec - axis * current_vec.dot(axis)

                    # Normalize projections
                    s_len = start_proj.length()
                    c_len = current_proj.length()
                    if s_len < 0.001 or c_len < 0.001:
                        return task.cont

                    start_proj /= s_len
                    current_proj /= c_len

                    # Compute signed angle via cross/dot (stable, no atan2 wrapping)
                    dot = start_proj.dot(current_proj)
                    dot = max(-1.0, min(1.0, dot))
                    angle_rad = math.acos(dot)

                    # Sign from cross product relative to axis
                    cross = start_proj.cross(current_proj)
                    if cross.dot(axis) < 0:
                        angle_rad = -angle_rad

                    angle_diff = math.degrees(angle_rad)

                    # Apply rotation to initial orientation (not cumulative)
                    start_quat = Quat()
                    start_quat.setHpr(self.drag_start_hpr)
                    delta_quat = Quat()
                    delta_quat.setFromAxisAngle(angle_diff, axis)
                    new_quat = start_quat * delta_quat
                    self.gizmo_manager.selected_node.setQuat(self.panda_app.render, new_quat)

                elif mode == 'SCALE':
                    start_dist = (self.drag_start_point - self.drag_start_pos).length()
                    current_dist = (current_hit - self.drag_start_pos).length()
                    if start_dist > 0.001:
                        scale_factor = current_dist / start_dist
                        new_scale = Point3(self.drag_start_scale)
                        if self.drag_axis == 'X':
                            new_scale.setX(new_scale.getX() * scale_factor)
                        elif self.drag_axis == 'Y':
                            new_scale.setY(new_scale.getY() * scale_factor)
                        elif self.drag_axis == 'Z':
                            new_scale.setZ(new_scale.getZ() * scale_factor)
                        self.gizmo_manager.selected_node.setScale(self.panda_app.render, new_scale)

                if hasattr(self, 'object_moved_signal'):
                    self.object_moved_signal.emit(self.gizmo_manager.selected_node)

        elif self.camera_controller.looking or self.camera_controller.panning:
            ndc_x = self.panda_app.mouseWatcherNode.getMouseX()
            ndc_y = self.panda_app.mouseWatcherNode.getMouseY()
            pixel_x = (ndc_x + 1) * 0.5 * self.width()
            pixel_y = (1 - ndc_y) * 0.5 * self.height()
            self.camera_controller.update_mouse((pixel_x, pixel_y))

        return task.cont

    def update_hover_task(self, task):
        if self.dragging or not self.gizmo_manager:
            return task.cont

        current_hover = None
        if self.mouse_pos and self.gizmo_manager.gizmo_root and not self.gizmo_manager.gizmo_root.isHidden():
            m_x = (self.mouse_pos.x() / self.width()) * 2 - 1
            m_y = -((self.mouse_pos.y() / self.height()) * 2 - 1)

            self.picker_ray.setFromLens(self.panda_app.camNode, m_x, m_y)
            self.queue.clearEntries()
            self.traverser.traverse(self.gizmo_manager.gizmo_root)

            if self.queue.getNumEntries() > 0:
                self.queue.sortEntries()
                name = self.queue.getEntry(0).getIntoNode().getName()
                if "gizmo_x" in name: current_hover = "X"
                elif "gizmo_y" in name: current_hover = "Y"
                elif "gizmo_z" in name: current_hover = "Z"

        if self.hovered_axis != current_hover:
            self.hovered_axis = current_hover
            if self.gizmo_manager:
                self.gizmo_manager.set_highlight(self.hovered_axis)

        return task.cont

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.panda_app and self.panda_app.win:
            width = self.width()
            height = self.height()
            props = WindowProperties()
            props.setOrigin(0, 0)
            props.setSize(width, height)
            self.panda_app.win.requestProperties(props)
            if self.panda_app.cam.node().getLens():
                self.panda_app.cam.node().getLens().setAspectRatio(width / height)

    def closeEvent(self, event):
        if self.timer:
            self.timer.stop()
        if self.panda_app:
            self.panda_app.destroy()
        super().closeEvent(event)