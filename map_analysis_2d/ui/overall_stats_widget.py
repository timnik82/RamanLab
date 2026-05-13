"""Widget for displaying overall peak fitting statistics."""

from __future__ import annotations

from typing import Optional, Sequence

from PySide6.QtCore import Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)
import numpy as np

from ..core.statistics import OverallStatistics, compute_overall_statistics


def _style_icon(name):
    app = QApplication.instance()
    if app is None:
        return None
    return app.style().standardIcon(name)


class MiniHistogramWidget(QFrame):
    """Compact bar histogram for fitted total-area distribution."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bin_count = 0
        self._bar_layout = QHBoxLayout(self)
        self._bar_layout.setContentsMargins(2, 2, 2, 2)
        self._bar_layout.setSpacing(1)
        self.setFixedHeight(42)
        self.setToolTip("Distribution of total integrated area across fitted pixels.")
        self.setStyleSheet("QFrame { border: 1px solid #d0d7de; background: #f8f9fa; }")

    def set_values(self, values: Sequence[float]):
        while self._bar_layout.count():
            item = self._bar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        finite_values = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
        if finite_values.size == 0:
            self.bin_count = 0
            self.hide()
            return

        bins = min(10, finite_values.size, max(3, int(np.sqrt(finite_values.size))))
        counts, _ = np.histogram(finite_values, bins=bins)
        max_count = int(np.max(counts)) if counts.size else 0
        self.bin_count = int(np.count_nonzero(counts))

        for count in counts:
            if count == 0:
                continue
            bar = QFrame()
            bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            height = 4 if max_count == 0 else max(4, int(34 * (count / max_count)))
            bar.setFixedHeight(height)
            bar.setToolTip(f"{int(count)} fitted pixels")
            bar.setStyleSheet("QFrame { background: #4f8cc9; border: none; }")
            self._bar_layout.addWidget(bar, 1)

        self.show()


class OverallStatsWidget(QWidget):
    """Display per-peak and grand total integrated areas after fitting."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._stats: Optional[OverallStatistics] = None
        self._placeholder_text = "Run map peak fitting to see overall statistics."

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(4)

        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)
        self.scientific_toggle = QCheckBox("Sci")
        self.scientific_toggle.setToolTip("Show numeric results in scientific notation.")
        self.scientific_toggle.toggled.connect(self._render_stats)
        options_layout.addWidget(self.scientific_toggle)
        options_layout.addStretch(1)
        self._main_layout.addLayout(options_layout)

        self.loading_label = QLabel("Computing statistics...")
        self.loading_label.setToolTip("Statistics are being computed after map fitting.")
        self.loading_label.setStyleSheet("color: #555; font-style: italic;")
        self.loading_label.hide()
        self._main_layout.addWidget(self.loading_label)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        self._main_layout.addWidget(self.loading_bar)

        self.fitted_pixels_label = QLabel("Fitted Pixels: --")
        self.fitted_pixels_label.setToolTip("Pixels with all required fitted peak parameters.")
        self.success_rate_label = QLabel("Success Rate: --")
        self.success_rate_label.setToolTip("Percentage of map pixels with complete successful fits.")
        for label in (self.fitted_pixels_label, self.success_rate_label):
            self._main_layout.addWidget(label)

        self._mean_area_row = QWidget()
        self._mean_area_layout = QHBoxLayout(self._mean_area_row)
        self._mean_area_layout.setContentsMargins(0, 0, 0, 0)
        self._mean_area_layout.setSpacing(6)
        self.mean_area_label = QLabel("Mean Area: --")
        self.mean_area_label.setToolTip("Average total integrated area over successfully fitted pixels.")
        self._copy_mean_button = QPushButton("Copy")
        icon = _style_icon(QStyle.StandardPixmap.SP_DialogSaveButton)
        if icon is not None:
            self._copy_mean_button.setIcon(icon)
        self._copy_mean_button.setToolTip("Copy the mean area to the clipboard.")
        self._copy_mean_button.setEnabled(False)
        self._copy_mean_button.clicked.connect(self._copy_mean_area)
        self._mean_area_layout.addWidget(self.mean_area_label)
        self._mean_area_layout.addStretch(1)
        self._mean_area_layout.addWidget(self._copy_mean_button)
        self._main_layout.addWidget(self._mean_area_row)

        self._median_area_row = QWidget()
        self._median_area_layout = QHBoxLayout(self._median_area_row)
        self._median_area_layout.setContentsMargins(0, 0, 0, 0)
        self._median_area_layout.setSpacing(6)
        self.median_area_label = QLabel("Median Area: --")
        self.median_area_label.setToolTip("Median total integrated area over successfully fitted pixels.")
        self._copy_median_button = QPushButton("Copy")
        if icon is not None:
            self._copy_median_button.setIcon(icon)
        self._copy_median_button.setToolTip("Copy the median area to the clipboard.")
        self._copy_median_button.setEnabled(False)
        self._copy_median_button.clicked.connect(self._copy_median_area)
        self._median_area_layout.addWidget(self.median_area_label)
        self._median_area_layout.addStretch(1)
        self._median_area_layout.addWidget(self._copy_median_button)
        self._main_layout.addWidget(self._median_area_row)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(2)
        self._main_layout.addLayout(self._rows_layout)

        self._grand_total_row = QWidget()
        self._grand_total_layout = QHBoxLayout(self._grand_total_row)
        self._grand_total_layout.setContentsMargins(0, 0, 0, 0)
        self._grand_total_layout.setSpacing(6)

        self.grand_total_label = QLabel()
        self.grand_total_label.setToolTip("Sum of integrated intensity across all fitted peaks and pixels.")
        self._copy_button = QPushButton("Copy")
        icon = _style_icon(QStyle.StandardPixmap.SP_DialogSaveButton)
        if icon is not None:
            self._copy_button.setIcon(icon)
        self._copy_button.setToolTip("Copy the grand total area to the clipboard.")
        self._copy_button.setEnabled(False)
        self._copy_button.clicked.connect(self._copy_grand_total)
        self._grand_total_layout.addWidget(self.grand_total_label)
        self._grand_total_layout.addStretch(1)
        self._grand_total_layout.addWidget(self._copy_button)

        self._main_layout.addWidget(self._grand_total_row)
        self.histogram_widget = MiniHistogramWidget()
        self.histogram_widget.hide()
        self._main_layout.addWidget(self.histogram_widget)
        self.clear_stats()

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def clear_stats(self):
        self._clear_rows()
        self._stats = None
        self.set_loading(False)
        self.grand_total_label.setText(self._placeholder_text)
        self.fitted_pixels_label.setText("Fitted Pixels: --")
        self.success_rate_label.setText("Success Rate: --")
        self.success_rate_label.setStyleSheet("color: #777;")
        self.mean_area_label.setText("Mean Area: --")
        self.median_area_label.setText("Median Area: --")
        self.histogram_widget.set_values([])
        self._copy_button.setEnabled(False)
        self._copy_mean_button.setEnabled(False)
        self._copy_median_button.setEnabled(False)

    def set_loading(self, loading: bool, message: str = "Computing statistics..."):
        self.loading_label.setText(message)
        self.loading_label.setVisible(loading)
        self.loading_bar.setVisible(loading)

    @Slot(dict)
    def update_from_fitting_results(self, fitting_results: dict):
        stats = compute_overall_statistics(fitting_results)
        if stats is None:
            self.clear_stats()
            return

        self._stats = stats
        self._render_stats()

    def _render_stats(self):
        if self._stats is None:
            return

        self._clear_rows()

        for index, total in enumerate(self._stats.per_peak_total_areas, start=1):
            label = QLabel(f"Peak {index} total area: {self._format_number(total)}")
            label.setToolTip(f"Total integrated intensity for fitted peak {index}.")
            self._rows_layout.addWidget(label)

        self.fitted_pixels_label.setText(
            f"Fitted Pixels: {self._stats.fitted_count:,} / {self._stats.total_count:,}"
        )
        self.success_rate_label.setText(f"Success Rate: {self._stats.success_rate:.1f}%")
        self.success_rate_label.setStyleSheet(
            f"color: {self._quality_color(self._stats.success_rate)}; font-weight: bold;"
        )
        self.mean_area_label.setText(
            f"Mean Area: {self._format_number(self._stats.mean_area)} +/- {self._format_number(self._stats.std_area)}"
        )
        self.median_area_label.setText(f"Median Area: {self._format_number(self._stats.median_area)}")
        self.grand_total_label.setText(f"Grand total area: {self._format_number(self._stats.grand_total_area)}")
        self.histogram_widget.set_values(self._stats.total_areas)
        self._copy_button.setEnabled(True)
        self._copy_mean_button.setEnabled(True)
        self._copy_median_button.setEnabled(True)

    def _copy_grand_total(self):
        if self._stats is None:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(f"{self._stats.grand_total_area:.2f}")

    def _copy_mean_area(self):
        if self._stats is None:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(f"{self._stats.mean_area:.2f}")

    def _copy_median_area(self):
        if self._stats is None:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(f"{self._stats.median_area:.2f}")

    def _format_number(self, value: float) -> str:
        if not np.isfinite(value):
            return "--"
        if self.scientific_toggle.isChecked():
            return f"{value:.2e}"
        return f"{value:,.2f}"

    @staticmethod
    def _quality_color(success_rate: float) -> str:
        if success_rate >= 90.0:
            return "green"
        if success_rate >= 70.0:
            return "#b7791f"
        return "#c53030"
