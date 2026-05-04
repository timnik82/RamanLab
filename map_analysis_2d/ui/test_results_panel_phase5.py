import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from map_analysis_2d.ui.pixel_details_widget import PixelDetailsWidget
from map_analysis_2d.ui.results_panel import ResultsPanel


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
