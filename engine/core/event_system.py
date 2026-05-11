"""
Event System — Core data model, condition/action classes, and registry.

This module defines the building blocks for the Construct 3-style visual
scripting system: base Condition/Action classes, concrete implementations,
a central EVENT_REGISTRY, and a ParameterDialog for collecting user input.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QComboBox, QLabel, QLineEdit
)
from PySide6.QtCore import Qt


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------

class Condition:
    """Base class for all event conditions."""

    display_name = "Condition"

    def __init__(self):
        self.parameters = {}

    def get_param(self, key, default=None):
        val = self.parameters.get(key, default)
        if isinstance(val, dict):
            return val.get("value", val.get("default", default))
        return val

    def evaluate(self, dt):
        """Return True if this condition is met."""
        return False

    def get_display_text(self):
        """Return a human-readable description for the UI."""
        return self.display_name

    def to_dict(self):
        """Serializes condition to a dictionary."""
        return {
            "type": self.__class__.__name__,
            "parameters": self.parameters
        }

    @staticmethod
    def from_dict(data):
        """Reconstructs a condition from a dictionary."""
        from engine.core.event_system import EVENT_REGISTRY
        cls_name = data.get("type")
        # Search registry for class
        for cat in EVENT_REGISTRY.values():
            for cls in cat.get("conditions", []):
                if cls.__name__ == cls_name:
                    inst = cls()
                    inst.parameters = data.get("parameters", {})
                    return inst
        return None


class Action:
    """Base class for all event actions."""

    display_name = "Action"

    def __init__(self):
        self.parameters = {}

    def get_param(self, key, default=None):
        val = self.parameters.get(key, default)
        if isinstance(val, dict):
            return val.get("value", val.get("default", default))
        return val

    def execute(self):
        """Perform the action."""
        pass

    def get_display_text(self):
        """Return a human-readable description for the UI."""
        return self.display_name

    def to_dict(self):
        """Serializes action to a dictionary."""
        # Include game_object_uuid if it exists
        data = {
            "type": self.__class__.__name__,
            "parameters": self.parameters
        }
        if hasattr(self, "game_object_uuid"):
            data["game_object_uuid"] = self.game_object_uuid
        return data

    @staticmethod
    def from_dict(data):
        """Reconstructs an action from a dictionary."""
        from engine.core.event_system import EVENT_REGISTRY
        cls_name = data.get("type")
        # Search registry for class
        for cat in EVENT_REGISTRY.values():
            for cls in cat.get("actions", []):
                if cls.__name__ == cls_name:
                    # Instantiate with uuid if provided
                    uuid = data.get("game_object_uuid")
                    if uuid:
                        inst = cls(game_object_uuid=uuid)
                    else:
                        inst = cls()
                    inst.parameters = data.get("parameters", {})
                    return inst
        return None


# ---------------------------------------------------------------------------
# Concrete conditions
# ---------------------------------------------------------------------------

class EveryTickCondition(Condition):
    """Condition that is always True — fires every engine tick."""

    display_name = "Every tick"

    def __init__(self):
        super().__init__()
        # No parameters needed

    def evaluate(self, dt):
        return True

    def get_display_text(self):
        return "System: Every tick"


class KeyIsDownCondition(Condition):
    """Check if a specific key is pressed."""

    display_name = "Key is down"

    def __init__(self):
        super().__init__()
        self.parameters = {
            "key": {"type": "str", "default": "w"},
        }

    def evaluate(self, dt):
        from engine.panda_app import PandaApp
        from panda3d.core import KeyboardButton
        key_str = self.get_param("key", "w")
        app = PandaApp.get_instance()
        if not app or not app.mouseWatcherNode:
            return False
        btn = KeyboardButton.asciiKey(key_str) if len(key_str) == 1 else KeyboardButton.keyboardKey(key_str)
        return app.mouseWatcherNode.isButtonDown(btn)

    def get_display_text(self):
        key = self.get_param("key", "w")
        return f"Keyboard: '{key}' is down"


class EveryXSecondsCondition(Condition):
    """Fires every X seconds."""

    display_name = "Every X seconds"

    def __init__(self):
        super().__init__()
        self.parameters = {
            "interval": {"type": "float", "default": 1.0},
        }
        self.timer = 0.0

    def evaluate(self, dt):
        self.timer += dt
        interval = self.get_param("interval", 1.0)
        if self.timer >= interval:
            self.timer -= interval
            return True
        return False

    def get_display_text(self):
        interval = self.get_param("interval", 1.0)
        return f"System: Every {interval} seconds"


# ---------------------------------------------------------------------------
# Concrete actions
# ---------------------------------------------------------------------------

class SetPositionAction(Action):
    """Set one axis of a GameObject's position to an absolute value."""

    display_name = "Set position"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "axis": {"type": "choice", "choices": ["X", "Y", "Z"], "default": "X"},
            "value": {"type": "float", "default": 0.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        from engine.core.transform_component import Transform

        target = None
        for go in scene_manager.get_all_game_objects():
            if go.uuid == self.game_object_uuid:
                target = go
                break

        if target is None:
            return

        transform = target.get_component(Transform)
        if transform is None:
            return

        axis = self.get_param("axis", "X")
        value = self.get_param("value", 0.0)

        pos = transform.get_pos()
        if axis == "X":
            transform.set_pos(float(value), pos.y, pos.z)
        elif axis == "Y":
            transform.set_pos(pos.x, float(value), pos.z)
        elif axis == "Z":
            transform.set_pos(pos.x, pos.y, float(value))

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        axis = self.get_param("axis", "X")
        value = self.get_param("value", 0.0)
        return f"{name}: Set position {axis} to {value}"


class ChangePositionAction(Action):
    """Add a relative value to one axis of a GameObject's position."""

    display_name = "Change position"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "axis": {"type": "choice", "choices": ["X", "Y", "Z"], "default": "X"},
            "value": {"type": "float", "default": 0.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        if target:
            axis = self.get_param("axis", "X")
            value = self.get_param("value", 0.0)
            dx, dy, dz = (0, 0, 0)
            if axis == "X": dx = value
            elif axis == "Y": dy = value
            elif axis == "Z": dz = value
            target.node_path.setPos(target.node_path, dx, dy, dz)

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        axis = self.get_param("axis", "X")
        value = self.get_param("value", 0.0)
        return f"{name}: Change position {axis} by {value}"


class SetRotationAction(Action):
    """Set the absolute rotation (Heading, Pitch, Roll) of a GameObject."""

    display_name = "Set rotation"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "h": {"type": "float", "default": 0.0},
            "p": {"type": "float", "default": 0.0},
            "r": {"type": "float", "default": 0.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        if target:
            h = self.get_param("h", 0.0)
            p = self.get_param("p", 0.0)
            r = self.get_param("r", 0.0)
            target.node_path.setHpr(h, p, r)

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        h = self.get_param("h", 0.0)
        p = self.get_param("p", 0.0)
        r = self.get_param("r", 0.0)
        return f"{name}: Set rotation to ({h}, {p}, {r})"


class ChangeRotationAction(Action):
    """Add a relative rotation (Heading, Pitch, Roll) to a GameObject."""

    display_name = "Change rotation"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "h": {"type": "float", "default": 0.0},
            "p": {"type": "float", "default": 0.0},
            "r": {"type": "float", "default": 0.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        if target:
            h = self.get_param("h", 0.0)
            p = self.get_param("p", 0.0)
            r = self.get_param("r", 0.0)
            target.node_path.setHpr(target.node_path, h, p, r)

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        h = self.get_param("h", 0.0)
        p = self.get_param("p", 0.0)
        r = self.get_param("r", 0.0)
        return f"{name}: Change rotation by ({h}, {p}, {r})"


class ApplyImpulseAction(Action):
    """Apply a physics impulse to a GameObject's Rigidbody."""

    display_name = "Apply impulse"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "x": {"type": "float", "default": 0.0},
            "y": {"type": "float", "default": 0.0},
            "z": {"type": "float", "default": 0.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        from engine.components.rigidbody_component import RigidbodyComponent
        from panda3d.core import LVector3
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        if target:
            rb = target.get_component(RigidbodyComponent)
            if rb and rb.node:
                x = self.get_param("x", 0.0)
                y = self.get_param("y", 0.0)
                z = self.get_param("z", 0.0)
                rb.node.applyCentralImpulse(LVector3(x, y, z))

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        x = self.get_param("x", 0.0)
        y = self.get_param("y", 0.0)
        z = self.get_param("z", 0.0)
        return f"{name}: Apply impulse ({x}, {y}, {z})"


class SetScaleAction(Action):
    """Set the absolute scale of a GameObject."""

    display_name = "Set scale"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "x": {"type": "float", "default": 1.0},
            "y": {"type": "float", "default": 1.0},
            "z": {"type": "float", "default": 1.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        if target:
            x = self.get_param("x", 1.0)
            y = self.get_param("y", 1.0)
            z = self.get_param("z", 1.0)
            target.node_path.setScale(x, y, z)

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        x = self.get_param("x", 1.0)
        y = self.get_param("y", 1.0)
        z = self.get_param("z", 1.0)
        return f"{name}: Set scale to ({x}, {y}, {z})"


class ChangeScaleAction(Action):
    """Add a relative scale to a GameObject."""

    display_name = "Change scale"

    def __init__(self, game_object_uuid=None):
        super().__init__()
        self.game_object_uuid = game_object_uuid
        self.parameters = {
            "x": {"type": "float", "default": 0.0},
            "y": {"type": "float", "default": 0.0},
            "z": {"type": "float", "default": 0.0},
        }

    def execute(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        if target:
            x = self.get_param("x", 0.0)
            y = self.get_param("y", 0.0)
            z = self.get_param("z", 0.0)
            cur = target.node_path.getScale()
            target.node_path.setScale(cur.x + x, cur.y + y, cur.z + z)

    def get_display_text(self):
        from engine.core.scene_manager import scene_manager
        target = next((go for go in scene_manager.get_all_game_objects() if go.uuid == self.game_object_uuid), None)
        name = target.name if target else "Unknown"
        x = self.get_param("x", 0.0)
        y = self.get_param("y", 0.0)
        z = self.get_param("z", 0.0)
        return f"{name}: Change scale by ({x}, {y}, {z})"


class LogAction(Action):
    """Print a message to the console."""

    display_name = "Log message"

    def __init__(self):
        super().__init__()
        self.parameters = {
            "message": {"type": "str", "default": "Hello World"},
        }

    def execute(self):
        msg = self.get_param("message", "")
        print(f"[EventSheet] {msg}")

    def get_display_text(self):
        msg = self.get_param("message", "")
        return f"Log: '{msg}'"


# ---------------------------------------------------------------------------
# Event Registry
# ---------------------------------------------------------------------------

EVENT_REGISTRY = {
    "System": {
        "conditions": [EveryTickCondition, EveryXSecondsCondition],
        "actions": [LogAction],
    },
    "Keyboard": {
        "conditions": [KeyIsDownCondition],
        "actions": [],
    },
    "GameObject": {
        "conditions": [],
        "actions": [
            SetPositionAction, 
            ChangePositionAction, 
            SetRotationAction, 
            ChangeRotationAction,
            ApplyImpulseAction,
            SetScaleAction,
            ChangeScaleAction
        ],
    },
}


# ---------------------------------------------------------------------------
# Parameter Dialog
# ---------------------------------------------------------------------------

class ParameterDialog(QDialog):
    """Dynamically-generated dialog for editing an action/condition's parameters."""

    def __init__(self, parameters, initial_values=None, parent=None):
        """
        Args:
            parameters: dict of {name: {"type": ..., "default": ..., ...}}
            initial_values: optional dict of {name: current_value}
        """
        super().__init__(parent)
        self.setWindowTitle("Set Parameters")
        self.resize(320, 200)
        self._param_widgets = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()

        for name, spec in parameters.items():
            param_type = spec.get("type", "float")
            
            # Use initial_values if provided, otherwise fallback to default in spec
            val = initial_values.get(name) if initial_values and name in initial_values else spec.get("default")

            if param_type == "float":
                widget = QDoubleSpinBox()
                widget.setRange(-999999.0, 999999.0)
                widget.setDecimals(3)
                widget.setValue(float(val))
                self._param_widgets[name] = widget

            elif param_type == "choice":
                widget = QComboBox()
                choices = spec.get("choices", [])
                widget.addItems(choices)
                idx = widget.findText(str(val))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                self._param_widgets[name] = widget

            elif param_type == "str":
                widget = QLineEdit()
                widget.setText(str(val))
                self._param_widgets[name] = widget

            else:
                # Fallback: show a label
                widget = QLabel(f"(unsupported type: {param_type})")

            form.addRow(name.capitalize() + ":", widget)

        layout.addLayout(form)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_values(self):
        """Return a dict of {param_name: user_entered_value}."""
        result = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, QDoubleSpinBox):
                result[name] = widget.value()
            elif isinstance(widget, QComboBox):
                result[name] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                result[name] = widget.text()
        return result
