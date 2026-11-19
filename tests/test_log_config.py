import os
import unittest
from tempfile import TemporaryDirectory

from utils.log_config import DailyArchiveFileHandler


class LoggerConfigurationTests(unittest.TestCase):
    def test_daily_archive_name_and_retention(self):
        with TemporaryDirectory() as directory:
            log_file = os.path.join(directory, "camera.log")
            handler = DailyArchiveFileHandler(
                log_file,
                when="D",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            )
            try:
                rotated_name = handler.rotation_filename(
                    f"{log_file}.2026-11-18"
                )
                self.assertEqual(
                    rotated_name,
                    os.path.join(directory, "camera-2026-11-18.log"),
                )

                archive_names = [
                    "camera-2026-11-16.log",
                    "camera-2026-11-17.log",
                    "camera-2026-11-18.log",
                    "camera-unrelated.log",
                ]
                for archive_name in archive_names:
                    open(
                        os.path.join(directory, archive_name),
                        "w",
                    ).close()

                self.assertEqual(
                    handler.getFilesToDelete(),
                    [os.path.join(directory, "camera-2026-11-16.log")],
                )
            finally:
                handler.close()


if __name__ == "__main__":
    unittest.main()
