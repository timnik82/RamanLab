import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from map_analysis_2d.ui.main_window import MapAnalysisMainWindow


class _DummyProgress:
    def show_progress(self, _message):
        pass

    def hide_progress(self):
        pass


class _DummyStatusBar:
    def __init__(self):
        self.messages = []
        self.permanent_widgets = []

    def showMessage(self, message, *_args):
        self.messages.append(message)

    def addPermanentWidget(self, widget):
        self.permanent_widgets.append(widget)


class _DummyLabel:
    def __init__(self, text=""):
        self.text = text
        self.tooltip = ""

    def setText(self, text):
        self.text = text

    def setToolTip(self, tooltip):
        self.tooltip = tooltip


class LastMapRestoreTest(unittest.TestCase):
    def _make_window(self):
        window = MapAnalysisMainWindow.__new__(MapAnalysisMainWindow)
        window.progress_status = _DummyProgress()
        window.cosmic_ray_config = object()
        window.tab_widget = SimpleNamespace(currentIndex=lambda: 0)
        window._reset_peak_fitting_state = MagicMock()
        window._clear_map_cache = MagicMock()
        window._initialize_integration_slider = MagicMock()
        window.update_map = MagicMock()
        window.on_tab_changed = MagicMock()
        status_bar = _DummyStatusBar()
        window.statusBar = lambda: status_bar
        window.loaded_map_label = _DummyLabel("Map: none")
        return window

    def test_loaded_map_indicator_shows_empty_state(self):
        window = self._make_window()

        window._set_loaded_map_indicator()

        self.assertEqual(window.loaded_map_label.text, "Map: none")
        self.assertEqual(window.loaded_map_label.tooltip, "No map loaded")

    def test_loaded_map_indicator_shows_file_name_and_full_path_tooltip(self):
        window = self._make_window()

        window._set_loaded_map_indicator("/tmp/example.pkl")

        self.assertEqual(window.loaded_map_label.text, "Map: example.pkl")
        self.assertEqual(window.loaded_map_label.tooltip, "/tmp/example.pkl")

    def test_loaded_map_indicator_shows_directory_name_and_full_path_tooltip(self):
        window = self._make_window()

        window._set_loaded_map_indicator("/tmp/my_map_folder")

        self.assertEqual(window.loaded_map_label.text, "Map: my_map_folder")
        self.assertEqual(window.loaded_map_label.tooltip, "/tmp/my_map_folder")

    def test_restore_last_map_treats_legacy_single_file_pkl_as_pickle(self):
        window = self._make_window()

        with tempfile.TemporaryDirectory() as temp_dir:
            pkl_path = Path(temp_dir) / "saved_map.pkl"
            pkl_path.write_bytes(b"placeholder")

            cfg = SimpleNamespace(
                get=lambda key, default=None: {
                    "map_analysis.last_map_path": str(pkl_path),
                    "map_analysis.last_map_type": "single_file",
                }.get(key, default),
                set=MagicMock(),
            )
            restored_map = SimpleNamespace(spectra={(0, 0): object()})

            with patch("core.config_manager.ConfigManager", return_value=cfg), \
                 patch("pkl_utils.safe_pickle_load", return_value={"map_data": restored_map}) as safe_load, \
                 patch("map_analysis_2d.core.single_file_map_loader.SingleFileRamanMapData") as single_file_loader:
                window._restore_last_map()

        safe_load.assert_called_once_with(str(pkl_path))
        single_file_loader.assert_not_called()
        self.assertIs(window.map_data, restored_map)
        cfg.set.assert_any_call("map_analysis.last_map_type", "pkl")
        self.assertEqual(window.loaded_map_label.text, "Map: saved_map.pkl")
        self.assertEqual(window.loaded_map_label.tooltip, str(pkl_path))

    def test_load_map_from_pkl_persists_pkl_type(self):
        window = self._make_window()
        window.cosmic_ray_manager = object()

        restored_map = SimpleNamespace(
            spectra={(0, 0): SimpleNamespace(wavenumbers=[100.0, 200.0], intensities=[1.0, 2.0], processed_intensities=None)},
            target_wavenumbers=[100.0, 200.0],
            wavenumbers=[100.0, 200.0],
        )
        cfg = MagicMock()

        with patch("map_analysis_2d.ui.main_window.QFileDialog.getOpenFileName", return_value=("/tmp/test-map.pkl", "")), \
             patch("pkl_utils.safe_pickle_load", return_value={"map_data": restored_map}), \
             patch("core.config_manager.ConfigManager", return_value=cfg), \
             patch("map_analysis_2d.ui.main_window.QMessageBox.information"):
            window.load_map_from_pkl()

        cfg.set.assert_any_call("map_analysis.last_map_path", "/tmp/test-map.pkl")
        cfg.set.assert_any_call("map_analysis.last_map_type", "pkl")
        self.assertEqual(window.loaded_map_label.text, "Map: test-map.pkl")
        self.assertEqual(window.loaded_map_label.tooltip, "/tmp/test-map.pkl")

    def test_internal_pkl_loader_updates_loaded_map_indicator(self):
        window = self._make_window()
        window.cosmic_ray_manager = object()

        restored_map = SimpleNamespace(
            spectra={(0, 0): SimpleNamespace(wavenumbers=[100.0, 200.0], intensities=[1.0, 2.0], processed_intensities=None)},
            target_wavenumbers=[100.0, 200.0],
            wavenumbers=[100.0, 200.0],
        )

        with patch("pkl_utils.safe_pickle_load", return_value={"map_data": restored_map}):
            window._load_pkl_file("/tmp/imported-map.pkl")

        self.assertEqual(window.loaded_map_label.text, "Map: imported-map.pkl")
        self.assertEqual(window.loaded_map_label.tooltip, "/tmp/imported-map.pkl")


if __name__ == "__main__":
    unittest.main()
