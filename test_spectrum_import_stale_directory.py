from types import SimpleNamespace
from unittest.mock import patch

from raman_analysis_app_qt6 import RamanAnalysisAppQt6


class StaleConfig:
    def get(self, key, default=None):
        if key == "last_spectrum_import_directory":
            return "/mnt/c/Users/timni/missing-folder"
        return default


def test_import_spectrum_ignores_a_stale_saved_directory():
    window = SimpleNamespace(config=StaleConfig())
    documents_directory = "/home/test/Documents"

    with patch(
        "raman_analysis_app_qt6.QStandardPaths.writableLocation",
        return_value=documents_directory,
    ), patch("raman_analysis_app_qt6.Path.glob", return_value=[]), patch(
        "raman_analysis_app_qt6.Path.is_dir", return_value=False
    ), patch(
        "raman_analysis_app_qt6.QFileDialog.getOpenFileName",
        return_value=("", ""),
    ) as open_dialog:
        RamanAnalysisAppQt6.import_spectrum(window)

    assert open_dialog.call_args.args[2] == documents_directory
