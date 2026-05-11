"""
Event Sheet Panel — Data-driven UI for the Construct 3-style visual scripting.

Provides multi-step dialogs for choosing an object type, picking a
condition/action from the EVENT_REGISTRY, filling parameters, and wiring
the result into both the UI and the runtime EventSheetProcessor.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QDialog,
    QListWidget, QListWidgetItem, QListView,
    QDialogButtonBox, QStyle, QMenu
)
from PySide6.QtCore import Qt, QSize, Signal

from engine.core.event_system import (
    EVENT_REGISTRY, ParameterDialog,
    Condition, Action,
)
from engine.core.event_sheet_processor import EventBlockData


# ---------------------------------------------------------------------------
# Reusable Components
# ---------------------------------------------------------------------------

class ClickableLabel(QLabel):
    """A QLabel that emits clicked and double_clicked signals."""
    clicked = Signal()
    double_clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


# ---------------------------------------------------------------------------
# Event Block Widget (one row in the sheet)
# ---------------------------------------------------------------------------

class EventBlockWidget(QFrame):
    """Visual representation of a single event row backed by EventBlockData."""
    deletion_requested = Signal(object)

    def __init__(self, row_number, block_data=None, parent_sheet=None):
        super().__init__()
        self.block_data = block_data or EventBlockData()
        self.parent_sheet = parent_sheet
        self.row_number = row_number

        self.setStyleSheet("""
            EventBlockWidget {
                border: none;
                border-bottom: 1px solid #1e1e1e;
                background-color: #2b2b2b;
                margin: 0px;
                padding: 0px;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Row number / Margin area ---
        self.margin_frame = QFrame()
        self.margin_frame.setFixedWidth(28)
        self.margin_frame.setStyleSheet("background-color: #3c3c3c; border-right: 1px solid #1e1e1e;")
        self.margin_layout = QVBoxLayout(self.margin_frame)
        self.margin_layout.setContentsMargins(0, 8, 0, 8)
        self.margin_layout.setSpacing(4)
        self.margin_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.margin_label = QLabel(str(self.row_number))
        self.margin_label.setStyleSheet("color: #777777; font-weight: bold; font-size: 12px; border: none;")
        self.margin_layout.addWidget(self.margin_label)

        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setFlat(True)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton { color: #555555; border: none; font-size: 16px; font-weight: bold; }
            QPushButton:hover { color: #f48771; }
        """)
        self.delete_btn.setToolTip("Delete this event block")
        self.delete_btn.clicked.connect(self._on_delete_block)
        self.margin_layout.addWidget(self.delete_btn)

        self.main_layout.addWidget(self.margin_frame)

        # --- Conditions column ---
        self.conditions_frame = QFrame()
        self.conditions_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border: none;
                border-right: 1px solid #1e1e1e;
            }
            QLabel {
                background-color: transparent;
                color: #d4d4d4;
                border: none;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        self.conditions_layout = QVBoxLayout(self.conditions_frame)
        self.conditions_layout.setContentsMargins(0, 4, 0, 4)
        self.conditions_layout.setSpacing(0)
        self.conditions_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(self.conditions_frame, stretch=1)

        # --- Actions column ---
        self.actions_frame = QFrame()
        self.actions_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: none;
            }
            QLabel {
                background-color: transparent;
                color: #d4d4d4;
                border: none;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        self.actions_layout = QVBoxLayout(self.actions_frame)
        self.actions_layout.setContentsMargins(0, 4, 0, 4)
        self.actions_layout.setSpacing(0)
        self.actions_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(self.actions_frame, stretch=2)

        self._update_display()

    def set_row_number(self, num):
        """Updates the visual row number."""
        self.row_number = num
        self.margin_label.setText(str(num))

    def _create_item_row(self, item_data, on_delete_callback):
        """Helper to create a row with a double-clickable label and a small delete button."""
        row_widget = QWidget()
        row_widget.setObjectName("ItemRow")
        row_widget.setStyleSheet("""
            QWidget#ItemRow:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(4, 2, 4, 2)
        row_layout.setSpacing(4)

        label = ClickableLabel(item_data.get_display_text())
        label.setToolTip("Double-click to edit")
        label.double_clicked.connect(lambda: self._on_item_double_clicked(item_data))
        row_layout.addWidget(label, stretch=1)

        del_btn = QPushButton("×")
        del_btn.setFixedSize(20, 20)
        del_btn.setFlat(True)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                color: #555555;
                font-weight: bold;
                border: none;
                background: transparent;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                color: #f48771;
            }
        """)
        del_btn.clicked.connect(on_delete_callback)
        row_layout.addWidget(del_btn)
        return row_widget

    def _update_display(self):
        """Clears and redraws the condition and action labels based on current data."""
        # Clear conditions layout
        while self.conditions_layout.count():
            item = self.conditions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add conditions with delete buttons
        for i, cond in enumerate(self.block_data.conditions):
            row = self._create_item_row(
                cond, 
                lambda idx=i: self._on_delete_condition(idx)
            )
            self.conditions_layout.addWidget(row)

        if not self.block_data.conditions:
            self.conditions_layout.addWidget(QLabel("No condition"))

        # Clickable label for adding condition
        add_cond_label = ClickableLabel("+ Add condition")
        add_cond_label.setStyleSheet("color: #777777; font-size: 13px; padding: 4px 8px;")
        add_cond_label.clicked.connect(self._on_add_condition_requested)
        self.conditions_layout.addWidget(add_cond_label)

        # Clear actions layout
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add actions with delete buttons
        for i, act in enumerate(self.block_data.actions):
            row = self._create_item_row(
                act, 
                lambda idx=i: self._on_delete_action(idx)
            )
            self.actions_layout.addWidget(row)

        if not self.block_data.actions:
            self.actions_layout.addWidget(QLabel("No action"))

        # Clickable label for adding action
        add_act_label = ClickableLabel("+ Add action")
        add_act_label.setStyleSheet("color: #777777; font-size: 13px; padding: 4px 8px;")
        add_act_label.clicked.connect(self._on_add_action_requested)
        self.actions_layout.addWidget(add_act_label)

    def _on_item_double_clicked(self, item_data):
        """Opens the ParameterDialog to edit an existing condition or action."""
        if not item_data.parameters:
            return

        # Prepare current values
        current_values = {}
        for k, v in item_data.parameters.items():
            if isinstance(v, dict):
                current_values[k] = v.get("value", v.get("default"))
            else:
                current_values[k] = v

        dlg = ParameterDialog(
            item_data.parameters, 
            initial_values=current_values, 
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            new_values = dlg.get_values()
            for k, v in new_values.items():
                if isinstance(item_data.parameters[k], dict):
                    item_data.parameters[k]["value"] = v
                else:
                    item_data.parameters[k] = v
            self._update_display()

    def _on_delete_condition(self, index):
        if 0 <= index < len(self.block_data.conditions):
            self.block_data.conditions.pop(index)
            self._update_display()

    def _on_delete_action(self, index):
        if 0 <= index < len(self.block_data.actions):
            self.block_data.actions.pop(index)
            self._update_display()

    def _on_delete_block(self):
        self.deletion_requested.emit(self)

    def _on_add_condition_requested(self):
        if not self.parent_sheet:
            return
        new_item = self.parent_sheet.request_logic_item(logic_type="condition")
        if new_item and isinstance(new_item, Condition):
            self.block_data.conditions.append(new_item)
            self._update_display()

    def _on_add_action_requested(self):
        if not self.parent_sheet:
            return
        new_item = self.parent_sheet.request_logic_item(logic_type="action")
        if new_item and isinstance(new_item, Action):
            self.block_data.actions.append(new_item)
            self._update_display()

    def contextMenuEvent(self, event):
        """Right-click menu for copying/pasting/deleting event blocks."""
        menu = QMenu(self)
        copy_act = menu.addAction("Copy Event")
        paste_act = menu.addAction("Paste Event")
        menu.addSeparator()
        delete_act = menu.addAction("Delete Event")

        # Disable paste if nothing in clipboard
        main_win = self.window()
        if not hasattr(main_win, 'event_clipboard') or not main_win.event_clipboard:
            paste_act.setEnabled(False)

        selected = menu.exec(event.globalPos())

        if selected == copy_act:
            self._copy_block()
        elif selected == paste_act:
            if self.parent_sheet:
                self.parent_sheet.paste_event()
        elif selected == delete_act:
            self._on_delete_block()

    def _copy_block(self):
        """Serializes current block data to the global clipboard."""
        import copy
        main_win = self.window()
        if hasattr(main_win, 'event_clipboard'):
            main_win.event_clipboard = copy.deepcopy(self.block_data)

    def keyPressEvent(self, event):
        """Shortcuts for event blocks."""
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self._copy_block()
                event.accept()
                return
            elif event.key() == Qt.Key_V:
                if self.parent_sheet:
                    self.parent_sheet.paste_event()
                event.accept()
                return
        if event.key() == Qt.Key_Delete:
            self._on_delete_block()
            event.accept()
            return
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class AddConditionDialog(QDialog):
    """Step 1 — Pick an object type (System, Keyboard, or a scene GameObject)."""

    def __init__(self, scene_manager, parent=None, title="Pick Object"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 340)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListView.IconMode)
        self.list_widget.setIconSize(QSize(64, 64))
        self.list_widget.setGridSize(QSize(100, 100))
        self.list_widget.setResizeMode(QListView.Adjust)
        self.list_widget.setMovement(QListView.Static)
        self.list_widget.setSpacing(8)
        self.list_widget.setWrapping(True)

        # Static entries
        static_items = [
            ("System",   QStyle.StandardPixmap.SP_ComputerIcon),
            ("Keyboard", QStyle.StandardPixmap.SP_DialogApplyButton),
            ("Mouse",    QStyle.StandardPixmap.SP_ArrowUp),
        ]
        for name, px in static_items:
            icon = self.style().standardIcon(px)
            item = QListWidgetItem(icon, name)
            item.setTextAlignment(Qt.AlignCenter)
            # Store None as uuid for static items
            item.setData(Qt.UserRole, None)
            self.list_widget.addItem(item)

        # Dynamic entries from scene
        if scene_manager:
            go_icon = self.style().standardIcon(
                QStyle.StandardPixmap.SP_MediaPlay
            )
            for go in scene_manager.get_all_game_objects():
                item = QListWidgetItem(go_icon, go.name)
                item.setTextAlignment(Qt.AlignCenter)
                # Store the uuid so we can reference it later
                item.setData(Qt.UserRole, go.uuid)
                self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def selected_text(self):
        cur = self.list_widget.currentItem()
        return cur.text() if cur else ""

    def selected_uuid(self):
        cur = self.list_widget.currentItem()
        if cur:
            return cur.data(Qt.UserRole)
        return None


class PickItemDialog(QDialog):
    """Step 2 — Pick a specific condition or action for the chosen object type."""

    def __init__(self, items, title="Pick Item", parent=None):
        """
        Args:
            items: list of condition/action *classes* to choose from.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(320, 260)
        self._classes = items

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for cls in items:
            self.list_widget.addItem(cls.display_name)
        layout.addWidget(self.list_widget)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def selected_class(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._classes):
            return self._classes[row]
        return None


# ---------------------------------------------------------------------------
# Event Sheet Widget (main panel)
# ---------------------------------------------------------------------------

class EventSheetWidget(QWidget):
    """Top-level widget for the Event Sheet tab."""

    def __init__(self, processor=None, scene_manager=None):
        super().__init__()
        self.processor = processor
        self.scene_manager = scene_manager
        self._event_counter = 0

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("background-color: #2b2b2b;")

        # Scrollable event list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #2b2b2b; border: none;")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #2b2b2b;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # "Add Event" button
        add_event_btn = QPushButton("Add Event")
        add_event_btn.setMinimumHeight(36)
        add_event_btn.setCursor(Qt.PointingHandCursor)
        add_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                margin: 12px 16px 16px 16px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
        """)
        add_event_btn.clicked.connect(self.on_add_event_clicked)
        main_layout.addWidget(add_event_btn)

        # Ensure we can capture key events for pasting
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        """Shortcuts for the whole sheet (e.g. Paste)."""
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_V:
            self.paste_event()
            event.accept()
            return
        super().keyPressEvent(event)

    def paste_event(self):
        """Clones the event block from the global clipboard and adds it to this sheet."""
        import copy
        main_win = self.window()
        if hasattr(main_win, 'event_clipboard') and main_win.event_clipboard:
            cloned_data = copy.deepcopy(main_win.event_clipboard)
            
            # Register with processor
            if self.processor:
                self.processor.add_block(cloned_data)
            
            # Add visual row
            self.add_block_widget(cloned_data)
            self._update_row_numbers()

    # ------------------------------------------------------------------
    # Reusable Dialog Flow
    # ------------------------------------------------------------------

    def request_logic_item(self, logic_type="condition"):
        """
        Handles the multi-step dialog flow to create a Condition or Action instance.
        Returns the instance or None if cancelled.
        """
        # Step 1: Pick object type
        dlg1_title = "Add Condition — Pick Object" if logic_type == "condition" else "Add Action — Pick Object"
        dlg1 = AddConditionDialog(self.scene_manager, parent=self, title=dlg1_title)
        if dlg1.exec() != QDialog.Accepted:
            return None

        selected_name = dlg1.selected_text()
        selected_uuid = dlg1.selected_uuid()
        if not selected_name:
            return None

        # Determine registry key
        registry_key = selected_name if selected_name in EVENT_REGISTRY else "GameObject"
        registry_entry = EVENT_REGISTRY.get(registry_key)
        if registry_entry is None:
            return None

        # Filter items based on logic_type
        if logic_type == "condition":
            available_items = registry_entry.get("conditions", [])
        else:
            available_items = registry_entry.get("actions", [])

        if not available_items:
            return None

        # Step 2: Pick specific condition/action
        dlg2 = PickItemDialog(
            available_items,
            title=f"Pick {logic_type.capitalize()} — {selected_name}",
            parent=self,
        )
        if dlg2.exec() != QDialog.Accepted:
            return None

        chosen_class = dlg2.selected_class()
        if chosen_class is None:
            return None

        # Instantiate
        if issubclass(chosen_class, Action) and selected_uuid:
            instance = chosen_class(game_object_uuid=selected_uuid)
        else:
            instance = chosen_class()

        # Step 3: Collect parameters (if any)
        if instance.parameters:
            dlg3 = ParameterDialog(instance.parameters, parent=self)
            if dlg3.exec() != QDialog.Accepted:
                return None
            user_values = dlg3.get_values()
            for key, val in user_values.items():
                if isinstance(instance.parameters[key], dict):
                    instance.parameters[key]["value"] = val
                else:
                    instance.parameters[key] = val

        return instance

    def on_add_event_clicked(self):
        """Creates a new event block by first requesting a condition."""
        # New events must start with at least one condition
        new_cond = self.request_logic_item(logic_type="condition")
        if not new_cond:
            return

        # Build data block
        block_data = EventBlockData()
        block_data.conditions.append(new_cond)

        # Register with processor
        if self.processor:
            self.processor.add_block(block_data)

        # Create the visual row
        self._event_counter += 1
        widget = EventBlockWidget(
            self._event_counter, 
            block_data=block_data, 
            parent_sheet=self
        )
        widget.deletion_requested.connect(self._on_block_deletion_requested)
        self.scroll_layout.addWidget(widget)

    def add_block_widget(self, block_data):
        """Programmatically add a visual row for an existing EventBlockData."""
        self._event_counter += 1
        widget = EventBlockWidget(
            self._event_counter,
            block_data=block_data,
            parent_sheet=self
        )
        widget.deletion_requested.connect(self._on_block_deletion_requested)
        self.scroll_layout.addWidget(widget)

    def _on_block_deletion_requested(self, widget):
        """Handles the removal of an entire event block."""
        # 1. Remove from processor
        if self.processor:
            self.processor.remove_block(widget.block_data)

        # 2. Remove from layout and delete
        self.scroll_layout.removeWidget(widget)
        widget.deleteLater()

        # 3. Update row numbers
        self._update_row_numbers()

    def _update_row_numbers(self):
        """Iterates through remaining blocks and re-sequences their numbers."""
        count = 0
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, EventBlockWidget):
                count += 1
                widget.set_row_number(count)
        self._event_counter = count
