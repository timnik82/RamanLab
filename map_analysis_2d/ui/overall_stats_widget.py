"""Widget for displaying overall peak fitting statistics."""

from __future__ import annotations

from functools import partial
from typing import Optional, Sequence

from PySide6.QtCore import Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
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
        self.failed_fits_label = QLabel("Failed Fits: --")
        self.failed_fits_label.setToolTip(
            "Pixels where fitting did not succeed. These are counted as not detected / no Si."
        )
        for label in (self.fitted_pixels_label, self.success_rate_label, self.failed_fits_label):
            self._main_layout.addWidget(label)

        snr_row = QHBoxLayout()
        snr_row.setContentsMargins(0, 0, 0, 0)
        snr_row.setSpacing(4)
        snr_row.addWidget(QLabel("SNR threshold:"))
        self.snr_threshold_spin = QDoubleSpinBox()
        self.snr_threshold_spin.setRange(0.1, 100.0)
        self.snr_threshold_spin.setSingleStep(0.5)
        self.snr_threshold_spin.setValue(3.0)
        self.snr_threshold_spin.setSuffix(" SNR")
        self.snr_threshold_spin.setToolTip(
            "Pixels with fitted peak SNR at or above this value are counted as signal-rich."
        )
        self.snr_threshold_spin.valueChanged.connect(self._render_stats)
        snr_row.addWidget(self.snr_threshold_spin)
        snr_row.addStretch(1)
        self._main_layout.addLayout(snr_row)

        self.meaningful_pixels_label = QLabel(f"Detected (SNR ≥ {self.snr_threshold_spin.value():.1f}): --")
        self.meaningful_pixels_label.setToolTip(
            "Pixels whose fitted peak SNR meets or exceeds the threshold — phase is detectable at this spot."
        )
        self.no_signal_label = QLabel("Not detected: --")
        self.no_signal_label.setToolTip(
            "Pixels below the SNR threshold or where fitting failed — treated as no Si detected at this spot."
        )
        for label in (self.meaningful_pixels_label, self.no_signal_label):
            self._main_layout.addWidget(label)

        icon = _style_icon(QStyle.StandardPixmap.SP_DialogSaveButton)

        self.mean_area_label, self._copy_mean_button = self._create_stat_row(
            "Mean Area: --",
            "Average total integrated area over successfully fitted pixels.",
            "Copy the mean area to the clipboard.",
            partial(self._copy_stat_value, "mean_area"),
            icon,
        )
        self.median_area_label, self._copy_median_button = self._create_stat_row(
            "Median Area: --",
            "Median total integrated area over successfully fitted pixels.",
            "Copy the median area to the clipboard.",
            partial(self._copy_stat_value, "median_area"),
            icon,
        )

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(2)
        self._main_layout.addLayout(self._rows_layout)

        self.grand_total_label, self._copy_button = self._create_stat_row(
            "",
            "Sum of integrated intensity across all fitted peaks and pixels.",
            "Copy the grand total area to the clipboard.",
            partial(self._copy_stat_value, "grand_total_area"),
            icon,
        )

        self.histogram_widget = MiniHistogramWidget()
        self.histogram_widget.hide()
        self._main_layout.addWidget(self.histogram_widget)
        self.clear_stats()

    def _create_stat_row(
        self,
        label_text: str,
        label_tooltip: str,
        button_tooltip: str,
        copy_slot,
        icon,
    ) -> tuple[QLabel, QPushButton]:
        """Create a label + Copy button row and append it to the main layout."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(label_text)
        label.setToolTip(label_tooltip)
        button = QPushButton("Copy")
        if icon is not None:
            button.setIcon(icon)
        button.setToolTip(button_tooltip)
        button.setEnabled(False)
        button.clicked.connect(copy_slot)
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(button)
        self._main_layout.addWidget(row)
        return label, button

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
        self.failed_fits_label.setText("Failed Fits: --")
        self.failed_fits_label.setStyleSheet("color: #777;")
        self.meaningful_pixels_label.setText(f"Detected (SNR ≥ {self.snr_threshold_spin.value():.1f}): --")
        self.meaningful_pixels_label.setStyleSheet("color: #777;")
        self.no_signal_label.setText("Not detected: --")
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
        self.set_loading(False)
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
        self.failed_fits_label.setText(f"Failed Fits: {self._stats.failed_count:,}")
        self.failed_fits_label.setStyleSheet(
            "color: #777;" if self._stats.failed_count == 0 else "color: #c53030; font-weight: bold;"
        )

        threshold = self.snr_threshold_spin.value()
        meaningful = sum(1 for v in self._stats.snr_values if v >= threshold)
        no_signal = self._stats.total_count - meaningful
        total = self._stats.total_count
        meaningful_pct = (meaningful / total * 100.0) if total else 0.0
        no_signal_pct = (no_signal / total * 100.0) if total else 0.0
        self.meaningful_pixels_label.setText(
            f"Detected (SNR ≥ {threshold:.1f}): {meaningful:,} / {total:,}  ({meaningful_pct:.1f}%)"
        )
        self.meaningful_pixels_label.setStyleSheet(
            f"color: {self._quality_color(meaningful_pct)}; font-weight: bold;"
        )
        self.no_signal_label.setText(f"Not detected: {no_signal:,} / {total:,}  ({no_signal_pct:.1f}%)")

        self.mean_area_label.setText(
            f"Mean Area: {self._format_number(self._stats.mean_area)} +/- {self._format_number(self._stats.std_area)}"
        )
        self.median_area_label.setText(f"Median Area: {self._format_number(self._stats.median_area)}")
        self.grand_total_label.setText(f"Grand total area: {self._format_number(self._stats.grand_total_area)}")
        self.histogram_widget.set_values(self._stats.total_areas)
        self._copy_button.setEnabled(bool(np.isfinite(self._stats.grand_total_area)))
        self._copy_mean_button.setEnabled(bool(np.isfinite(self._stats.mean_area)))
        self._copy_median_button.setEnabled(bool(np.isfinite(self._stats.median_area)))

    def _copy_stat_value(self, attr_name: str, *_) -> None:
        """Copy a named statistics value to the clipboard if finite."""
        if self._stats is None:
            return
        value = getattr(self._stats, attr_name, None)
        if value is not None and np.isfinite(value):
            QGuiApplication.clipboard().setText(f"{value:.2f}")

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
