"""Results panel embedded in the peak fitting control panel sidebar."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QGroupBox, QStyle, QToolButton, QVBoxLayout, QWidget

from .overall_stats_widget import OverallStatsWidget
from .pixel_details_widget import PixelDetailsWidget


def _style_icon(name):
    app = QApplication.instance()
    if app is None:
        return None
    return app.style().standardIcon(name)


class CollapsibleSection(QWidget):
    """Small collapsible section used inside the results panel."""

    def __init__(self, title: str, icon_name, child: QWidget, parent=None):
        super().__init__(parent)
        self.child = child

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_button.setToolTip(f"Collapse or expand {title.lower()}.")
        icon = _style_icon(icon_name)
        if icon is not None:
            self.toggle_button.setIcon(icon)
        self.toggle_button.clicked.connect(self._on_toggled)

        layout.addWidget(self.toggle_button)
        layout.addWidget(child)

    def _on_toggled(self, checked: bool):
        self.child.setVisible(checked)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )


class ResultsPanel(QGroupBox):
    """Permanent sidebar panel showing overall stats and per-pixel details."""

    def __init__(self, parent=None):
        super().__init__("Results", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.overall_stats = OverallStatsWidget(self)
        self.pixel_details = PixelDetailsWidget(self)
        self.overall_section = CollapsibleSection(
            "Overall Statistics",
            QStyle.StandardPixmap.SP_FileDialogDetailedView,
            self.overall_stats,
            self,
        )
        self.pixel_section = CollapsibleSection(
            "Selected Pixel Details",
            QStyle.StandardPixmap.SP_DialogHelpButton,
            self.pixel_details,
            self,
        )

        layout.addWidget(self.overall_section)
        layout.addWidget(self.pixel_section)

    def clear(self) -> None:
        self.overall_stats.clear_stats()
        self.pixel_details.clear()

    def set_loading(self, loading: bool, message: str = "Computing statistics...") -> None:
        self.overall_stats.set_loading(loading, message)
