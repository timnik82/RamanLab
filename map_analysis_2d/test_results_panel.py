import numpy as np

from map_analysis_2d.core.statistics import compute_overall_statistics


def test_compute_overall_statistics_excludes_partial_invalid_pixels_from_all_totals():
    results = {
        "peak_shapes": ["Lorentzian", "Gaussian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0, (1, 0): 11.0},
            "P1_Wid": {(0, 0): 3.0, (1, 0): 13.0},
            "P2_Amp": {(0, 0): 5.0},
            "P2_Wid": {(0, 0): 7.0},
        },
        "fit_errors": {},
    }

    stats = compute_overall_statistics(results)

    p1_valid_pixel_only = 2.0 * 3.0 * np.pi
    p2_valid_pixel_only = 5.0 * 7.0 * np.sqrt(np.pi)
    assert stats is not None
    assert stats.fitted_count == 1
    assert stats.total_count == 2
    assert stats.success_rate == 50.0
    assert np.isclose(stats.per_peak_total_areas[0], p1_valid_pixel_only)
    assert np.isclose(stats.per_peak_total_areas[1], p2_valid_pixel_only)
    assert np.isclose(stats.grand_total_area, p1_valid_pixel_only + p2_valid_pixel_only)
    assert len(stats.total_areas) == 1


def test_compute_overall_statistics_reports_area_distribution_values():
    results = {
        "peak_shapes": ["Lorentzian"],
        "map_parameters": {
            "P1_Amp": {(0, 0): 2.0, (1, 0): 4.0},
            "P1_Wid": {(0, 0): 3.0, (1, 0): 5.0},
        },
        "fit_errors": {},
    }

    stats = compute_overall_statistics(results)

    first_area = 2.0 * 3.0 * np.pi
    second_area = 4.0 * 5.0 * np.pi
    assert stats is not None
    assert np.allclose(stats.total_areas, [first_area, second_area])
    assert np.isclose(stats.mean_area, np.mean([first_area, second_area]))
    assert np.isclose(stats.median_area, np.median([first_area, second_area]))
    assert np.isclose(stats.std_area, np.std([first_area, second_area]))
