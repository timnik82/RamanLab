import csv
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from map_analysis_2d.ui.main_window import MapAnalysisMainWindow


class PeakFittingResultsCsvExportTest(unittest.TestCase):
    def test_writer_exports_parameters_integrated_intensities_and_fit_status(self):
        window = MapAnalysisMainWindow.__new__(MapAnalysisMainWindow)
        window.peak_fitting_config = None
        window.map_data = SimpleNamespace(
            spectra={
                (3, 4): SimpleNamespace(x_pos=3, y_pos=4),
                (1, 2): SimpleNamespace(x_pos=1, y_pos=2),
            }
        )
        window.peak_fitting_results = {
            "peak_shapes": ["Lorentzian", "Pseudo-Voigt"],
            "param_names": [
                "P1_Amp",
                "P1_Cen",
                "P1_Wid",
                "P2_Amp",
                "P2_Cen",
                "P2_Wid",
                "P2_Eta",
            ],
            "map_parameters": {
                "P1_Amp": {(1, 2): 2.0, (3, 4): math.nan},
                "P1_Cen": {(1, 2): 100.0, (3, 4): math.nan},
                "P1_Wid": {(1, 2): 3.0, (3, 4): math.nan},
                "P2_Amp": {(1, 2): 5.0, (3, 4): math.nan},
                "P2_Cen": {(1, 2): 200.0, (3, 4): math.nan},
                "P2_Wid": {(1, 2): 7.0, (3, 4): math.nan},
                "P2_Eta": {(1, 2): 0.25, (3, 4): math.nan},
            },
            "r_squared": {(1, 2): 0.98, (3, 4): math.nan},
            "fit_errors": {(3, 4): "fit failed"},
            "fit_warnings": {(1, 2): "uncertain covariance"},
            "config": {"num_peaks": 2},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.csv"
            window._write_peak_fitting_results_csv(str(output_path))

            with output_path.open(newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(
            list(rows[0].keys()),
            [
                "X_um",
                "Y_um",
                "P1_Amp",
                "P1_Cen",
                "P1_Wid",
                "P1_IntInt",
                "P2_Amp",
                "P2_Cen",
                "P2_Wid",
                "P2_Eta",
                "P2_IntInt",
                "Total_IntInt",
                "R2",
                "status",
                "Fit Error",
                "Fit Warning",
            ],
        )
        self.assertEqual(
            [(row["X_um"], row["Y_um"]) for row in rows],
            [("1", "2"), ("3", "4")],
        )
        self.assertAlmostEqual(float(rows[0]["P1_IntInt"]), 2.0 * 3.0 * math.pi)
        self.assertAlmostEqual(
            float(rows[0]["P2_IntInt"]),
            5.0 * 7.0 * ((1.0 - 0.25) * math.sqrt(math.pi) + 0.25 * math.pi),
        )
        self.assertEqual(rows[0]["status"], "success")
        self.assertEqual(rows[0]["Fit Warning"], "uncertain covariance")
        self.assertEqual(rows[1]["status"], "failed")
        self.assertEqual(rows[1]["Fit Error"], "fit failed")
        self.assertEqual(rows[1]["Total_IntInt"], "nan")


if __name__ == "__main__":
    unittest.main()
