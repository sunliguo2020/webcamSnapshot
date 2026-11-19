import tempfile
import unittest
from unittest.mock import patch

from utils.capture_pool import (
    RETRY_PORT_CHECK_TIMEOUT_SECONDS,
    RETRY_VIDEO_OPEN_TIMEOUT_MS,
    RETRY_VIDEO_READ_TIMEOUT_MS,
    _capture_camera_records,
    _capture_one_impl,
)


class CaptureRetryTests(unittest.TestCase):
    @patch("utils.capture_pool.Camera")
    def test_retry_uses_longer_video_timeouts(self, camera_class):
        camera_class.return_value.capture.return_value = (1, "image.jpg")

        _capture_one_impl(
            0,
            {"ip": "192.0.2.1"},
            "hik",
            "output",
            False,
            retry=True,
        )

        camera = camera_class.return_value
        self.assertTrue(camera_class.call_args.kwargs["force_timeout_options"])
        self.assertEqual(
            camera.PORT_CHECK_TIMEOUT, RETRY_PORT_CHECK_TIMEOUT_SECONDS
        )
        self.assertEqual(
            camera.VIDEO_OPEN_TIMEOUT_MS, RETRY_VIDEO_OPEN_TIMEOUT_MS
        )
        self.assertEqual(
            camera.VIDEO_READ_TIMEOUT_MS, RETRY_VIDEO_READ_TIMEOUT_MS
        )

    @patch("utils.capture_pool.Camera")
    def test_dahua_retry_selects_cgi_snapshot(self, camera_class):
        camera_class.return_value.capture.return_value = (1, "image.jpg")

        _capture_one_impl(
            0,
            {"ip": "192.0.2.1"},
            "dahua",
            "output",
            False,
            retry=True,
        )

        self.assertTrue(
            camera_class.call_args.kwargs["use_dahua_cgi_snapshot"]
        )

    @patch("utils.capture_pool._capture_one")
    def test_retries_failed_camera_and_uses_retry_result(self, capture_one):
        capture_one.side_effect = [
            (0, "192.0.2.1", 0, "initial failure", 1.0, {}),
            (0, "192.0.2.1", 1, "image.jpg", 2.0, {}),
        ]

        with tempfile.TemporaryDirectory() as folder:
            results, statistics = _capture_camera_records(
                [{"ip": "192.0.2.1"}],
                "cameras.csv",
                "hik",
                folder_path=folder,
            )

        self.assertEqual(results, [(1, "image.jpg")])
        self.assertEqual(statistics["success"], 1)
        self.assertEqual(statistics["failed"], 0)
        self.assertEqual(statistics["failed_ips"], [])
        self.assertEqual(capture_one.call_count, 2)
        self.assertTrue(capture_one.call_args_list[1][0][-1])

    @patch("utils.capture_pool._capture_one")
    def test_records_failure_only_after_retry_also_fails(self, capture_one):
        capture_one.side_effect = [
            (0, "192.0.2.1", 0, "initial failure", 1.0, {}),
            (0, "192.0.2.1", 0, "retry failure", 2.0, {}),
        ]

        with tempfile.TemporaryDirectory() as folder:
            results, statistics = _capture_camera_records(
                [{"ip": "192.0.2.1"}],
                "cameras.csv",
                "hik",
                folder_path=folder,
            )
            with open(
                statistics["fail_log_file"], encoding="utf-8-sig"
            ) as file:
                failure_report = file.read()

        self.assertEqual(results, [(0, "retry failure")])
        self.assertEqual(statistics["success"], 0)
        self.assertEqual(statistics["failed"], 1)
        self.assertIn("retry failure", failure_report)
        self.assertNotIn("initial failure", failure_report)

    @patch("utils.capture_pool._capture_one")
    def test_does_not_retry_successful_camera(self, capture_one):
        capture_one.return_value = (
            0, "192.0.2.1", 1, "image.jpg", 1.0, {}
        )

        results, statistics = _capture_camera_records(
            [{"ip": "192.0.2.1"}],
            "cameras.csv",
            "hik",
        )

        self.assertEqual(results, [(1, "image.jpg")])
        self.assertEqual(statistics["success"], 1)
        self.assertEqual(statistics["failed"], 0)
        capture_one.assert_called_once()


if __name__ == "__main__":
    unittest.main()
