import numpy as np


from map_analysis_2d.core.statistics import compute_overall_statistics


class _Spectrum:
    def __init__(self, x_pos, y_pos):
        self.x_pos = x_pos
        self.y_pos = y_pos


class _MapData:
    def __init__(self, positions):
        self.spectra = {i: _Spectrum(x, y) for i, (x, y) in enumerate(positions)}


def test_compute_overall_statistics_single_pixel_one_peak_success():
    map_data = _MapData([(0, 0)])
    results = {
        "peak_shapes": ["Lorentzian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0},
            "P1_Wid": {(0, 0): 3.0},
        },
    }

    stats = compute_overall_statistics(map_data, results)

    assert stats["total_count"] == 1
    assert stats["fitted_count"] == 1
    assert stats["success_rate"] == 100.0
    assert np.isclose(stats["total_area"], 2.0 * 3.0 * np.pi)
    assert np.isclose(stats["per_peak_totals"]["Peak 1"], stats["total_area"])


def test_compute_overall_statistics_two_peaks_per_peak_and_grand_totals():
    map_data = _MapData([(0, 0)])
    results = {
        "peak_shapes": ["Lorentzian", "Gaussian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0},
            "P1_Wid": {(0, 0): 3.0},
            "P2_Amp": {(0, 0): 5.0},
            "P2_Wid": {(0, 0): 7.0},
        },
    }

    stats = compute_overall_statistics(map_data, results)

    p1 = 2.0 * 3.0 * np.pi
    p2 = 5.0 * 7.0 * np.sqrt(np.pi)
    assert np.isclose(stats["per_peak_totals"]["Peak 1"], p1)
    assert np.isclose(stats["per_peak_totals"]["Peak 2"], p2)
    assert np.isclose(stats["total_area"], p1 + p2)


def test_compute_overall_statistics_all_failed_map_placeholder_values():
    map_data = _MapData([(0, 0), (1, 0), (0, 1), (1, 1)])
    results = {
        "peak_shapes": ["Lorentzian"],
        "map_parameters": {
            "P1_Amp": {},
            "P1_Wid": {},
        },
        "fit_errors": {(0, 0): "boom", (1, 0): "boom", (0, 1): "boom", (1, 1): "boom"},
    }

    stats = compute_overall_statistics(map_data, results)

    assert stats["total_count"] == 4
    assert stats["fitted_count"] == 0
    assert stats["success_rate"] == 0.0
    assert stats["total_area"] == 0.0
    assert stats["per_peak_totals"]["Peak 1"] == 0.0


def test_compute_overall_statistics_mixed_success_failure_only_counts_success():
    map_data = _MapData([(0, 0), (1, 0)])
    results = {
        "peak_shapes": ["Lorentzian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0, (1, 0): 9.0},
            "P1_Wid": {(0, 0): 3.0, (1, 0): 10.0},
        },
        "fit_errors": {(1, 0): "failed"},
    }

    stats = compute_overall_statistics(map_data, results)

    assert stats["total_count"] == 2
    assert stats["fitted_count"] == 1
    assert stats["success_rate"] == 50.0
    assert np.isclose(stats["total_area"], 2.0 * 3.0 * np.pi)

