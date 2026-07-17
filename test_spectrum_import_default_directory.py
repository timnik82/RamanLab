from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from raman_analysis_app_qt6 import RamanAnalysisAppQt6


class EmptyConfig:
    def get(self, key, default=None):
        return default


def test_import_spectrum_prefers_windows_projects_folder_on_first_use():
    window = SimpleNamespace(config=EmptyConfig())
    preferred_directory = "/mnt/c/Users/timni/OneDrive - Universidade de Coimbra/+Projects"

    with patch(
        "raman_analysis_app_qt6.Path.glob", return_value=[Path(preferred_directory)]
    ), patch("raman_analysis_app_qt6.Path.is_dir", return_value=True), patch(
        "raman_analysis_app_qt6.QFileDialog.getOpenFileName",
        return_value=("", ""),
    ) as open_dialog:
        RamanAnalysisAppQt6.import_spectrum(window)

    assert open_dialog.call_args.args[2] == preferred_directory
