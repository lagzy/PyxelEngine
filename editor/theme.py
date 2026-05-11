#!/usr/bin/env python3
"""
Editor Theme - Qt StyleSheet (QSS) for AAA Game Engine Aesthetics
Deep blue palette with Unreal Engine/Unity/Blender readability
"""

EDITOR_THEME = """
/* --- GLOBAL --- */
* {
    color: #d4d4d4;
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    font-size: 10pt;
    outline: none;
}

QWidget {
    background-color: #2b2b2b;
}

/* --- TOOLBARS & DOCK HEADERS --- */
QToolBar {
    background-color: #333333;
    border-bottom: 1px solid #1e1e1e;
    padding: 4px;
    spacing: 6px;
}

QDockWidget {
    titlebar-close-icon: url(close.png); /* Fallback */
    titlebar-normal-icon: url(float.png);
}

QDockWidget::title {
    background-color: #333333;
    border-bottom: 1px solid #1e1e1e;
    padding: 6px 10px;
    font-weight: bold;
    color: #cccccc;
}

/* --- BUTTONS --- */
QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #1e1e1e;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
    text-align: center;
}

QPushButton:flat {
    background-color: transparent;
    border: none;
    padding: 2px 6px;
}

QPushButton:hover:flat {
    background-color: #444444;
    border: 1px solid #555555;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border: 1px solid #555555;
}

QPushButton:pressed {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
}

QPushButton::menu-indicator {
    image: none;
    width: 0px;
}

QToolButton {
    background-color: #3c3c3c;
    border: 1px solid #1e1e1e;
    border-radius: 3px;
    padding: 4px;
    color: #ffffff;
}

QToolButton:hover {
    background-color: #4a4a4a;
}

QToolButton::menu-indicator {
    image: none;
    width: 0px;
}

/* --- INPUTS & VIEWS (Inset look) --- */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 3px;
    padding: 4px;
    selection-background-color: #0e639c;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #0e639c;
}

/* Spinbox Arrows - Pure CSS Border Triangles */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 14px;
    height: 10px;
    margin: 1px;
}

/* DRAWING ARROWS USING NEGATIVE SPACE */
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    border-left: 4px solid #1e1e1e; 
    border-right: 4px solid #1e1e1e; 
    border-bottom: 5px solid #cccccc; 
    width: 0px;
    height: 0px;
    background: none;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    border-left: 4px solid #1e1e1e; 
    border-right: 4px solid #1e1e1e; 
    border-top: 5px solid #cccccc; 
    width: 0px;
    height: 0px;
    background: none;
}

QAbstractSpinBox:up-arrow:hover, QAbstractSpinBox:down-arrow:hover {
    border-color: #4daafc;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #3c3c3c;
}

/* --- HIERARCHY & ASSET BROWSER (Trees and Lists) --- */
QTreeView, QListView {
    background-color: #1e1e1e;
    border: none;
    border-top: 1px solid #333333;
}

QTreeView::item, QListView::item {
    padding: 4px;
    border-radius: 2px;
    margin: 1px 4px;
}

QTreeView::item:hover, QListView::item:hover {
    background-color: #2b2b2b;
}

QTreeView::item:selected, QListView::item:selected {
    background-color: #0e639c;
    color: white;
}

QHeaderView::section {
    background-color: #333333;
    border: none;
    border-right: 1px solid #1e1e1e;
    border-bottom: 1px solid #1e1e1e;
    padding: 4px 6px;
    font-weight: bold;
}

/* --- INSPECTOR (Group Boxes) --- */
QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
    color: #4daafc;
    font-weight: bold;
}

/* --- MENUS --- */
QMenu {
    background-color: #333333;
    border: 1px solid #1e1e1e;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 24px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #0e639c;
}

/* --- SCROLLBARS (Crucial for modern look) --- */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #444444;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #555555;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px; 
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #444444;
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* --- TABS (Central Tab Widget) --- */
QTabWidget::pane {
    border: 1px solid #1e1e1e;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #333333;
    border: 1px solid #1e1e1e;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 16px;
    margin-right: 2px;
    color: #aaaaaa;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    color: #ffffff;
    font-weight: bold;
    border-top: 2px solid #0e639c;
}

QTabBar::tab:hover:!selected {
    background-color: #3c3c3c;
    color: #e0e0e0;
}
"""