from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from map_analysis_2d.core.math_models import compute_integrated_intensity


Position = Tuple[float, float]


@dataclass(frozen=True)
class OverallStatistics:
    total_area: float
    mean_area: float
    median_area: float
    std_area: float
    fitted_count: int
    total_count: int
    success_rate: float
    per_peak_totals: Dict[str, float]


def compute_overall_statistics(
    map_data: Any,
    peak_fitting_results: Mapping[str, Any],
) -> Dict[str, Any]:
    """Compute overall results-panel statistics from map peak fitting output.

    The function is deliberately defensive: it tolerates missing fit entries,
    partially filled parameter maps, and explicit failures recorded via
    ``fit_errors``. Only pixels with all required per-peak parameters and no
    fit error contribute to totals.
    """

    shapes: Sequence[str] = peak_fitting_results.get("peak_shapes", [])
    map_params: Mapping[str, Mapping[Position, float]] = peak_fitting_results.get(
        "map_parameters", {}
    )
    fit_errors: Mapping[Position, str] = peak_fitting_results.get("fit_errors", {})

    total_count = len(getattr(map_data, "spectra", {}) or {})
    fitted_count = 0
    total_areas: list[float] = []
    per_peak_totals: Dict[str, float] = {f"Peak {i}": 0.0 for i in range(1, len(shapes) + 1)}

    for spectrum in (getattr(map_data, "spectra", {}) or {}).values():
        pos_key: Position = (getattr(spectrum, "x_pos", None), getattr(spectrum, "y_pos", None))
        if pos_key in fit_errors and fit_errors.get(pos_key):
            continue

        total_int = 0.0
        all_valid = True
        for i, shape in enumerate(shapes, 1):
            amp = (map_params.get(f"P{i}_Amp", {}) or {}).get(pos_key, np.nan)
            wid = (map_params.get(f"P{i}_Wid", {}) or {}).get(pos_key, np.nan)
            eta = (map_params.get(f"P{i}_Eta", {}) or {}).get(pos_key, 0.5)

            if not (np.isfinite(amp) and np.isfinite(wid)):
                all_valid = False
                break

            ii = compute_integrated_intensity(amp, wid, shape, eta)
            if not np.isfinite(ii):
                all_valid = False
                break
            total_int += ii
            per_peak_totals[f"Peak {i}"] = per_peak_totals.get(f"Peak {i}", 0.0) + float(ii)

        if all_valid and shapes:
            fitted_count += 1
            total_areas.append(total_int)

    if total_areas:
        total_area = float(np.sum(total_areas))
        mean_area = float(np.mean(total_areas))
        median_area = float(np.median(total_areas))
        std_area = float(np.std(total_areas))
        success_rate = (fitted_count / total_count) * 100.0 if total_count else 0.0
    else:
        total_area = 0.0
        mean_area = 0.0
        median_area = 0.0
        std_area = 0.0
        success_rate = 0.0

    return {
        "total_area": total_area,
        "mean_area": mean_area,
        "median_area": median_area,
        "std_area": std_area,
        "fitted_count": fitted_count,
        "total_count": total_count,
        "success_rate": success_rate,
        "per_peak_totals": per_peak_totals,
    }

