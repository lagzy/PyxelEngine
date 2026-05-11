"""
Inspector Panel for editing GameObject component properties.
"""
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
                            QLineEdit, QCheckBox, QHBoxLayout, QPushButton, 
                            QFileDialog, QComboBox, QMenu, QDoubleSpinBox)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from functools import partial
from panda3d.core import Vec3, Vec4
from engine.core.transform_component import Transform

from engine.components.mesh_renderer import MeshRendererComponent
from engine.components.directional_light import DirectionalLightComponent
from engine.components.point_light import PointLightComponent
from engine.components.spot_light import SpotLightComponent
from engine.components.camera_component import CameraComponent
from engine.components.rigidbody_component import RigidbodyComponent
from engine.components.box_collider import BoxColliderComponent
from engine.components.sphere_collider import SphereColliderComponent
from engine.components.capsule_collider import CapsuleColliderComponent
from engine.components.mesh_collider import MeshColliderComponent


class InspectorPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.current_game_object = None
        self._transform_spinboxes = []  # [pos_x, pos_y, pos_z, rot_x, rot_y, rot_z, scale_x, scale_y, scale_z]
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.show_no_selection()

    def show_no_selection(self):
        self.clear_layout()
        self.layout.addWidget(QLabel("Inspector - No selection"))
        self._transform_spinboxes = []

    def set_node(self, game_object):
        sys.stderr.write(f"DEBUG [Inspector]: set_node called with GameObject: {game_object.name if game_object else 'None'} (ID: {id(game_object) if game_object else 'None'})\n")
        self.current_game_object = game_object
        self.generate_ui()

    def generate_ui(self):
        sys.stderr.write(f"DEBUG [Inspector]: generate_ui called for GameObject: {self.current_game_object.name if self.current_game_object else 'None'} (ID: {id(self.current_game_object) if self.current_game_object else 'None'})\n")
        self.clear_layout()
        if not self.current_game_object:
            self.show_no_selection()
            return

        self.layout.addWidget(QLabel(f"Inspector - {self.current_game_object.name}"))
        self._transform_spinboxes = []

        for comp in self.current_game_object.components.values():
            sys.stderr.write(f"DEBUG [Inspector]: Processing component {comp.__class__.__name__} with instance ID {id(comp)}\n")
            if comp.__class__.__name__ == "Transform":
                self._create_transform_ui(comp)
            else:
                self._create_component_ui(comp)

        add_component_btn = QPushButton("Add Component")
        add_component_btn.setMinimumHeight(40)
        add_component_btn.clicked.connect(self.show_add_component_menu)
        self.layout.addWidget(add_component_btn)
        self.layout.addStretch()

    def _create_transform_ui(self, transform_comp):
        """Manually create Transform UI with QDoubleSpinBox widgets."""
        group = QGroupBox("Transform")
        form = QFormLayout()
        
        # Position
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position"))
        pos_x = QDoubleSpinBox()
        pos_y = QDoubleSpinBox()
        pos_z = QDoubleSpinBox()
        for spinbox in (pos_x, pos_y, pos_z):
            spinbox.setRange(-10000, 10000)
            spinbox.setSingleStep(0.1)
            pos_layout.addWidget(spinbox)
        # Set initial values
        pos = transform_comp.get_pos()
        pos_x.setValue(pos.x)
        pos_y.setValue(pos.y)
        pos_z.setValue(pos.z)
        # Store references
        self._transform_spinboxes = [pos_x, pos_y, pos_z]
        form.addRow(pos_layout)

        # Rotation
        rot_layout = QHBoxLayout()
        rot_layout.addWidget(QLabel("Rotation"))
        rot_x = QDoubleSpinBox()
        rot_y = QDoubleSpinBox()
        rot_z = QDoubleSpinBox()
        for spinbox in (rot_x, rot_y, rot_z):
            spinbox.setRange(-360, 360)
            spinbox.setSingleStep(1.0)
            rot_layout.addWidget(spinbox)
        # Set initial values
        hpr = transform_comp.get_hpr()
        rot_x.setValue(hpr.x)
        rot_y.setValue(hpr.y)
        rot_z.setValue(hpr.z)
        self._transform_spinboxes.extend([rot_x, rot_y, rot_z])
        form.addRow(rot_layout)

        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale"))
        scale_x = QDoubleSpinBox()
        scale_y = QDoubleSpinBox()
        scale_z = QDoubleSpinBox()
        for spinbox in (scale_x, scale_y, scale_z):
            spinbox.setRange(0.01, 1000)
            spinbox.setSingleStep(0.1)
            scale_layout.addWidget(spinbox)
        # Set initial values
        scale = transform_comp.get_scale()
        scale_x.setValue(scale.x)
        scale_y.setValue(scale.y)
        scale_z.setValue(scale.z)
        self._transform_spinboxes.extend([scale_x, scale_y, scale_z])
        form.addRow(scale_layout)

        # Connect signals using partial
        for spinbox in self._transform_spinboxes:
            spinbox.valueChanged.connect(partial(self._on_transform_changed, transform_comp))
        
        group.setLayout(form)
        self.layout.addWidget(group)

    def _on_transform_changed(self, transform_comp, value=None):
        """Update Transform when any spinbox value changes."""
        if len(self._transform_spinboxes) < 9:
            return
        pos_x, pos_y, pos_z, rot_x, rot_y, rot_z, scale_x, scale_y, scale_z = self._transform_spinboxes
        sys.stderr.write(f"DEBUG [Handler IN]: Transform change on component ID {id(transform_comp)}: pos=({pos_x.value()},{pos_y.value()},{pos_z.value()}), rot=({rot_x.value()},{rot_y.value()},{rot_z.value()}), scale=({scale_x.value()},{scale_y.value()},{scale_z.value()})\n")
        transform_comp.set_pos(pos_x.value(), pos_y.value(), pos_z.value())
        transform_comp.set_hpr(rot_x.value(), rot_y.value(), rot_z.value())
        transform_comp.set_scale(scale_x.value(), scale_y.value(), scale_z.value())
        sys.stderr.write(f"DEBUG [Handler WRITE]: Transform updated. Verified pos: {transform_comp.get_pos()}, rot: {transform_comp.get_hpr()}, scale: {transform_comp.get_scale()}\n")

    def _create_component_ui(self, comp):
        """Dynamically create UI for non-Transform components with proper property handling."""
        group = QGroupBox(comp.__class__.__name__)
        form = QFormLayout()

        for attr_name in dir(comp):
            if attr_name.startswith('_'):
                continue
            # Get the class-level attribute to check if it's a property/method
            attr = getattr(type(comp), attr_name, None)
            # Skip methods and other callables that are not properties
            if callable(attr) and not isinstance(attr, property):
                continue

            # Get the current value from the instance (invokes property getter if applicable)
            value = getattr(comp, attr_name)
            comp_id_str = f"UUID={comp._uuid}" if hasattr(comp, '_uuid') else f"ID={id(comp)}"
            sys.stderr.write(f"DEBUG [Inspector READ]: For component {comp_id_str}, reading '{attr_name}'. Found value: {value}. Setting checkbox/widget.\n")
            sys.stderr.flush()

            if isinstance(value, bool):
                check = QCheckBox()
                check.blockSignals(True)
                check.setChecked(value)
                check.blockSignals(False)
                check.stateChanged.connect(partial(self._on_bool_changed, comp, attr_name))
                form.addRow(attr_name + ":", check)

            elif isinstance(value, (int, float)):
                spinbox = QDoubleSpinBox()
                spinbox.setRange(-10000, 10000)
                spinbox.setSingleStep(0.1 if isinstance(value, float) else 1.0)
                spinbox.blockSignals(True)
                spinbox.setValue(float(value))
                spinbox.blockSignals(False)
                spinbox.valueChanged.connect(partial(self._on_float_changed, comp, attr_name))
                form.addRow(attr_name + ":", spinbox)

            elif isinstance(value, str):
                if attr_name == "projection_type":
                    combo = QComboBox()
                    combo.addItems(["Perspective", "Orthographic"])
                    combo.blockSignals(True)
                    combo.setCurrentText(value)
                    combo.blockSignals(False)
                    combo.currentTextChanged.connect(partial(self._on_string_changed, comp, attr_name))
                    form.addRow(attr_name + ":", combo)
                elif attr_name.endswith("_path"):
                    widget = QWidget()
                    h_layout = QHBoxLayout()
                    edit = QLineEdit(value)
                    browse_btn = QPushButton("Browse")
                    browse_btn.clicked.connect(partial(self._on_browse_file, comp, attr_name))
                    h_layout.addWidget(edit)
                    h_layout.addWidget(browse_btn)
                    widget.setLayout(h_layout)
                    form.addRow(attr_name + ":", widget)
                else:
                    edit = QLineEdit(value)
                    edit.editingFinished.connect(partial(self._on_string_changed, comp, attr_name))
                    form.addRow(attr_name + ":", edit)

        group.setLayout(form)
        self.layout.addWidget(group)

    def _is_property(self, obj, attr_name):
        """Check if an attribute is a property (including inherited)."""
        attr = getattr(type(obj), attr_name, None)
        return isinstance(attr, property)

    def _set_attribute(self, obj, attr_name, value):
        """Set attribute value, using property setter if available."""
        if self._is_property(obj, attr_name):
            setattr(obj, attr_name, value)
        else:
            obj.__dict__[attr_name] = value

    def _on_bool_changed(self, component, attr_name, state):
        """Handle boolean property changes."""
        import sys
        comp_id_str = f"UUID={component._uuid}" if hasattr(component, '_uuid') else f"ID={id(component)}"
        sys.stderr.write(f"DEBUG [Handler IN]: Raw state={state}, type={type(state)}\n")
        sys.stderr.flush()
        new_value = bool(state)
        sys.stderr.write(f"DEBUG [Handler IN]: {comp_id_str} new_value={new_value}\n")
        sys.stderr.flush()
        sys.stderr.write(f"DEBUG [Handler IN]: Signal received for component {comp_id_str} to change '{attr_name}' to '{new_value}'.\n")
        sys.stderr.flush()
        self._set_attribute(component, attr_name, new_value)
        verified_value = getattr(component, attr_name)
        sys.stderr.write(f"DEBUG [Handler WRITE]: setattr called. Verified value on component {comp_id_str} is now: {verified_value}.\n")
        sys.stderr.flush()
        if verified_value != new_value:
            sys.stderr.write(f"CRITICAL ERROR: Verification failed! The value did not stick to the Python object!\n")
            sys.stderr.flush()

    def _on_float_changed(self, component, attr_name, value):
        """Handle float/int property changes."""
        sys.stderr.write(f"DEBUG [Handler IN]: Signal received for component ID {id(component)} to change '{attr_name}' to '{value}'.\n")
        self._set_attribute(component, attr_name, value)
        verified_value = getattr(component, attr_name)
        sys.stderr.write(f"DEBUG [Handler WRITE]: setattr called. Verified value on component ID {id(component)} is now: {verified_value}.\n")
        if verified_value != value:
            sys.stderr.write(f"CRITICAL ERROR: Verification failed! The value did not stick to the Python object!\n")

    def _on_string_changed(self, component, attr_name):
        """Handle string property changes."""
        sender = self.sender()
        if isinstance(sender, QLineEdit):
            new_value = sender.text()
            sys.stderr.write(f"DEBUG [Handler IN]: Signal received for component ID {id(component)} to change '{attr_name}' to '{new_value}'.\n")
            self._set_attribute(component, attr_name, new_value)
            verified_value = getattr(component, attr_name)
            sys.stderr.write(f"DEBUG [Handler WRITE]: setattr called. Verified value on component ID {id(component)} is now: {verified_value}.\n")
            if verified_value != new_value:
                sys.stderr.write(f"CRITICAL ERROR: Verification failed! The value did not stick to the Python object!\n")

    def _on_combo_changed(self, component, attr_name, text):
        """Handle combo box changes."""
        sys.stderr.write(f"DEBUG [Handler IN]: Signal received for component ID {id(component)} to change '{attr_name}' to '{text}'.\n")
        self._set_attribute(component, attr_name, text)
        verified_value = getattr(component, attr_name)
        sys.stderr.write(f"DEBUG [Handler WRITE]: setattr called. Verified value on component ID {id(component)} is now: {verified_value}.\n")
        if verified_value != text:
            sys.stderr.write(f"CRITICAL ERROR: Verification failed! The value did not stick to the Python object!\n")

    def _on_browse_file(self, component, attr_name):
        """Handle file browse button."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Material Files (*.mat)")
        if file_path:
            sys.stderr.write(f"DEBUG [Handler IN]: Signal received for component ID {id(component)} to change '{attr_name}' to '{file_path}'.\n")
            self._set_attribute(component, attr_name, file_path)
            verified_value = getattr(component, attr_name)
            sys.stderr.write(f"DEBUG [Handler WRITE]: setattr called. Verified value on component ID {id(component)} is now: {verified_value}.\n")
            if verified_value != file_path:
                sys.stderr.write(f"CRITICAL ERROR: Verification failed! The value did not stick to the Python object!\n")

    def show_add_component_menu(self):
        menu = QMenu(self)
        
        physics_menu = menu.addMenu("Physics")
        
        rb_action = physics_menu.addAction("Rigidbody")
        rb_action.triggered.connect(partial(self.add_component_to_selected, RigidbodyComponent))
        
        box_action = physics_menu.addAction("Box Collider")
        box_action.triggered.connect(partial(self.add_component_to_selected, BoxColliderComponent))
        
        sphere_action = physics_menu.addAction("Sphere Collider")
        sphere_action.triggered.connect(partial(self.add_component_to_selected, SphereColliderComponent))
        
        capsule_action = physics_menu.addAction("Capsule Collider")
        capsule_action.triggered.connect(partial(self.add_component_to_selected, CapsuleColliderComponent))
        
        mesh_action = physics_menu.addAction("Mesh Collider")
        mesh_action.triggered.connect(partial(self.add_component_to_selected, MeshColliderComponent))
        
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def add_component_to_selected(self, component_class):
        if self.current_game_object:
            sys.stderr.write(f"DEBUG [Inspector]: Attempting to add {component_class.__name__} to GameObject '{self.current_game_object.name}' (ID: {id(self.current_game_object)})\n")
            if self.current_game_object.has_component(component_class):
                existing = self.current_game_object.get_component(component_class)
                sys.stderr.write(f"DEBUG [Inspector]: Component {component_class.__name__} already exists (instance ID: {id(existing)}). Skipping add.\n")
                return
            sys.stderr.write(f"DEBUG [Inspector]: Component {component_class.__name__} does not exist. Proceeding with add.\n")
            self.current_game_object.add_component(component_class)
            self.generate_ui()

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    self._clear_layout_recursive(layout)
                    layout.deleteLater()

    def _clear_layout_recursive(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                sublayout = item.layout()
                if sublayout:
                    self._clear_layout_recursive(sublayout)
                    sublayout.deleteLater()

    def update_values(self):
        """Refresh Transform spinbox values without recreating UI."""
        if not self.current_game_object or len(self._transform_spinboxes) < 9:
            return
        try:
            transform = self.current_game_object.get_component(Transform)
            if transform is None:
                return
            pos = transform.get_pos()
            hpr = transform.get_hpr()
            scale = transform.get_scale()
            
            pos_x, pos_y, pos_z, rot_x, rot_y, rot_z, scale_x, scale_y, scale_z = self._transform_spinboxes
            
            pos_x.setValue(pos.x)
            pos_y.setValue(pos.y)
            pos_z.setValue(pos.z)
            rot_x.setValue(hpr.x)
            rot_y.setValue(hpr.y)
            rot_z.setValue(hpr.z)
            scale_x.setValue(scale.x)
            scale_y.setValue(scale.y)
            scale_z.setValue(scale.z)
        except (AttributeError, RuntimeError):
            pass
