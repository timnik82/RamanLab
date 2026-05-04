import pathlib
import io
import os
import pickle
import tempfile
import unittest

from pkl_utils import CrossPlatformUnpickler, safe_pickle_load


class CrossPlatformPickleTests(unittest.TestCase):
    def test_safe_pickle_load_handles_windows_path_on_non_windows(self):
        payload = b"cpathlib\nWindowsPath\np0\n(VC:/data/map/source.txt\np1\ntp2\nRp3\n."

        with tempfile.TemporaryDirectory() as tmp_dir:
            pkl_file = pathlib.Path(tmp_dir) / "windows_path.pkl"
            pkl_file.write_bytes(payload)

            loaded = safe_pickle_load(pkl_file)

        self.assertEqual(loaded, pathlib.PureWindowsPath("C:/data/map/source.txt"))

    @unittest.skipIf(os.name == "nt", "PosixPath is only native on POSIX systems")
    def test_safe_pickle_load_preserves_native_posix_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pkl_file = pathlib.Path(tmp_dir) / "posix_path.pkl"
            expected = pathlib.Path("/tmp/map/source.txt")
            pkl_file.write_bytes(pickle.dumps(expected))

            loaded = safe_pickle_load(pkl_file)

        self.assertIs(type(loaded), pathlib.PosixPath)
        self.assertEqual(loaded, expected)

    def test_cross_platform_unpickler_redirects_legacy_map_classes(self):
        try:
            from map_analysis_2d.core.file_io import RamanMapData
        except ModuleNotFoundError as e:
            if e.name == "numpy":
                self.skipTest("RamanMapData import requires numpy")
            raise

        unpickler = CrossPlatformUnpickler(io.BytesIO())

        loaded_class = unpickler.find_class("raman_map_data", "RamanMapData")

        self.assertIs(loaded_class, RamanMapData)


if __name__ == "__main__":
    unittest.main()
