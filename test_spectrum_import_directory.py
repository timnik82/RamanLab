from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from raman_analysis_app_qt6 import RamanAnalysisAppQt6


class FakeConfig:
    def __init__(self, saved_directory):
        self.saved_directory = saved_directory
        self.updates = []

    def get(self, key, default=None):
        if key == "last_spectrum_import_directory":
            return self.saved_directory
        return default

    def set(self, key, value):
        self.updates.append((key, value))


def test_import_spectrum_reuses_and_updates_last_directory():
    config = FakeConfig("/mnt/c/Users/timni/OneDrive - Universidade de Coimbra/+Projects")
    loaded_paths = []
    status_messages = []
    window = SimpleNamespace(
        config=config,
        load_spectrum_file=loaded_paths.append,
        status_bar=SimpleNamespace(showMessage=status_messages.append),
    )
    chosen_file = "/mnt/c/Users/timni/OneDrive - Universidade de Coimbra/+Projects/sample.txt"

    with patch("raman_analysis_app_qt6.Path.is_dir", return_value=True), patch(
        "raman_analysis_app_qt6.QFileDialog.getOpenFileName",
        return_value=(chosen_file, ""),
    ) as open_dialog:
        RamanAnalysisAppQt6.import_spectrum(window)

    assert open_dialog.call_args.args[2] == config.saved_directory
    assert loaded_paths == [chosen_file]
    assert config.updates == [
        ("last_spectrum_import_directory", str(Path(chosen_file).parent))
    ]
