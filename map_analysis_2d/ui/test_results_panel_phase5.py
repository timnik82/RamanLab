import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from map_analysis_2d.ui.pixel_details_widget import PixelDetailsWidget
from map_analysis_2d.ui.results_panel import ResultsPanel
from map_analysis_2d.ui.control_panels import MapPeakFittingControlPanel
from map_analysis_2d.ui.main_window import MapAnalysisMainWindow


def _app():
    return QApplication.instance() or QApplication([])


def test_results_panel_has_collapsible_sections_and_loading_state():
    _app()
    panel = ResultsPanel()

    assert panel.overall_section.toggle_button.toolTip()
    assert panel.pixel_section.toggle_button.toolTip()

    assert not panel.overall_section.child.isHidden()
    panel.overall_section.toggle_button.click()
    assert panel.overall_section.child.isHidden()
    panel.overall_section.toggle_button.click()
    assert not panel.overall_section.child.isHidden()

    panel.set_loading(True, "Computing statistics...")
    assert not panel.overall_stats.loading_label.isHidden()
    assert "Computing" in panel.overall_stats.loading_label.text()

    panel.set_loading(False)
    assert panel.overall_stats.loading_label.isHidden()


def test_overall_stats_widget_displays_phase5_metrics_and_histogram():
    _app()
    panel = ResultsPanel()
    results = {
        "peak_shapes": ["Lorentzian", "Gaussian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0, (1, 0): 4.0},
            "P1_Wid": {(0, 0): 3.0, (1, 0): 5.0},
            "P2_Amp": {(0, 0): 5.0, (1, 0): 6.0},
            "P2_Wid": {(0, 0): 7.0, (1, 0): 8.0},
        },
        "fit_errors": {},
    }

    panel.overall_stats.update_from_fitting_results(results)

    assert "Fitted Pixels: 2 / 2" in panel.overall_stats.fitted_pixels_label.text()
    assert "Success Rate: 100.0%" in panel.overall_stats.success_rate_label.text()
    assert "green" in panel.overall_stats.success_rate_label.styleSheet()
    assert "Mean Area:" in panel.overall_stats.mean_area_label.text()
    assert "Median Area:" in panel.overall_stats.median_area_label.text()
    assert panel.overall_stats.histogram_widget.bin_count > 0
    assert panel.overall_stats.scientific_toggle.toolTip()

    panel.overall_stats.scientific_toggle.setChecked(True)
    assert "e+" in panel.overall_stats.grand_total_label.text()


def test_overall_stats_counts_failed_fits_as_not_detected():
    _app()
    panel = ResultsPanel()
    results = {
        "peak_shapes": ["Lorentzian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 10.0, (1, 0): 10.0, (2, 0): float("nan")},
            "P1_Wid": {(0, 0): 3.0, (1, 0): 3.0, (2, 0): float("nan")},
        },
        "snr": {(0, 0): 4.0, (1, 0): 1.0},
        "fit_errors": {(2, 0): "fit failed"},
    }

    panel.overall_stats.update_from_fitting_results(results)

    assert "Detected" in panel.overall_stats.meaningful_pixels_label.text()
    assert "1 / 3" in panel.overall_stats.meaningful_pixels_label.text()
    assert "2 / 3" in panel.overall_stats.no_signal_label.text()
    assert "Failed Fits: 1" in panel.overall_stats.failed_fits_label.text()


def test_peak_fitting_panel_emits_config_changed_for_shape_and_parameter_edits():
    _app()
    panel = MapPeakFittingControlPanel()
    emissions = []
    panel.fitting_config_changed.connect(lambda: emissions.append(True))

    panel.shape_combos[0].setCurrentText("Gaussian")
    panel.amp_spins[0]["init"].setValue(panel.amp_spins[0]["init"].value() + 1.0)

    assert len(emissions) >= 2


class _DummyControlsPanel:
    def __init__(self):
        self.sections = {}

    def clear_dynamic_sections(self):
        self.sections.clear()

    def add_section(self, name, widget, permanent=False):
        self.sections[name] = {"widget": widget, "permanent": permanent}

    def add_stretch(self):
        pass


def test_peak_fitting_stats_are_restored_when_recreating_control_panel():
    _app()
    window = MapAnalysisMainWindow.__new__(MapAnalysisMainWindow)
    window.controls_panel = _DummyControlsPanel()
    window._cache_peak_fitting_config_from_panel = lambda: None
    window._cache_map_view_settings_from_panel = lambda: None
    window._get_peak_fitting_tab_index = lambda: 1
    window._get_map_tab_index = lambda: -1
    window._get_template_tab_index = lambda: -1
    window._get_dimensionality_tab_index = lambda: -1
    window._get_ml_tab_index = lambda: -1
    window._get_results_tab_index = lambda: -1
    window._get_microplastic_tab_index = lambda: -1
    window.peak_fitting_config = None
    window._saved_peak_fitting_config = None
    window.map_data = None
    window.peak_fitting_results = {
        "peak_shapes": ["Lorentzian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0},
            "P1_Wid": {(0, 0): 3.0},
        },
        "fit_errors": {},
    }

    window.on_tab_changed(1)

    control_panel = window.controls_panel.sections["peak_fitting_controls"]["widget"]
    assert "Fitted Pixels: 1 / 1" in control_panel.results_panel.overall_stats.fitted_pixels_label.text()


def test_overall_stats_histogram_omits_empty_bins():
    _app()
    panel = ResultsPanel()

    panel.overall_stats.histogram_widget.set_values([1.0, 100.0, 101.0])

    assert panel.overall_stats.histogram_widget.bin_count == 2
    assert panel.overall_stats.histogram_widget._bar_layout.count() == 2


def test_pixel_details_widget_color_codes_status_and_adds_tooltips():
    _app()
    widget = PixelDetailsWidget()

    widget.show_results(
        position_text="Position: X=4, Y=5",
        r_squared=0.95,
        peak_rows=[("P1", 12.3, 520.0, 4.5)],
    )

    assert "green" in widget.status_label.styleSheet()
    assert widget.table.item(0, 1).toolTip()

    widget.show_results(
        position_text="Position: X=4, Y=5",
        r_squared=0.75,
        peak_rows=[("P1", 12.3, 520.0, 4.5)],
    )

    assert "#b7791f" in widget.status_label.styleSheet()

    widget.show_fit_failed("Position: X=4, Y=5")
    assert "#c53030" in widget.status_label.styleSheet()
