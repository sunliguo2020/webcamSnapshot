import unittest
from unittest.mock import Mock, patch

import cv2
from lib.Camera.base import Camera
from utils.capture_pool import (
    _capture_one_impl,
    capture_hikvision_recorder_channels,
    expand_hikvision_channel_numbers,
    expand_hikvision_channels,
)


class HikvisionChannelExpansionTests(unittest.TestCase):
    @patch("lib.Camera.base.cv2.VideoCapture")
    def test_recorder_opens_with_legacy_default_backend_first(self, video_capture):
        camera = Camera.__new__(Camera)
        camera.camera_type = "hik"
        camera.channel_no = 1
        video_capture.return_value.isOpened.return_value = True

        result = camera._open_video_stream("rtsp://192.0.2.1/Streaming/Channels/101")

        self.assertIs(result, video_capture.return_value)
        video_capture.assert_called_once_with(
            "rtsp://192.0.2.1/Streaming/Channels/101"
        )

    @patch("lib.Camera.base.cv2.VideoCapture")
    def test_recorder_falls_back_to_ffmpeg_after_default_backend_fails(
        self, video_capture
    ):
        camera = Camera.__new__(Camera)
        camera.camera_type = "hik"
        camera.channel_no = 2
        camera.ip = "192.0.2.1"
        failed_capture = video_capture.return_value
        failed_capture.isOpened.return_value = False
        fallback_capture = Mock()
        video_capture.side_effect = [failed_capture, fallback_capture]
        fallback_capture.isOpened.return_value = True

        result = camera._open_video_stream("rtsp://192.0.2.1/Streaming/Channels/201")

        self.assertIs(result, fallback_capture)
        failed_capture.release.assert_called_once_with()
        self.assertEqual(video_capture.call_count, 2)
        self.assertEqual(video_capture.call_args.args[1], cv2.CAP_FFMPEG)

    def test_expands_each_recorder_into_requested_channels(self):
        cameras = [
            {"ip": "192.0.2.1", "password": "one"},
            {"ip": "192.0.2.2", "password": "two"},
        ]

        expanded = expand_hikvision_channels(cameras, 2, 3)

        self.assertEqual(
            expanded,
            [
                {"ip": "192.0.2.1", "password": "one", "channel_no": 2},
                {"ip": "192.0.2.1", "password": "one", "channel_no": 3},
                {"ip": "192.0.2.2", "password": "two", "channel_no": 2},
                {"ip": "192.0.2.2", "password": "two", "channel_no": 3},
            ],
        )
        self.assertNotIn("channel_no", cameras[0])

    def test_rejects_invalid_channel_range(self):
        for start, end in ((0, 2), (3, 2), ("invalid", 4)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ValueError):
                    expand_hikvision_channels([], start, end)

    def test_expands_only_detected_recorder_channels(self):
        expanded = expand_hikvision_channel_numbers(
            [{"ip": "192.0.2.1"}],
            [16, 2, 2],
        )

        self.assertEqual(
            [camera["channel_no"] for camera in expanded],
            [2, 16],
        )

    @patch("utils.capture_pool._capture_camera_records")
    def test_recorder_capture_uses_default_transport_and_serial_workers(
        self, capture_records
    ):
        result = capture_hikvision_recorder_channels(
            [{"ip": "192.0.2.1", "channel_no": 1}],
            "recorder.csv",
        )

        self.assertIs(result, capture_records.return_value)
        capture_records.assert_called_once()
        self.assertEqual(capture_records.call_args.kwargs["max_workers"], 1)
        self.assertEqual(capture_records.call_args.kwargs["camera_type"], "hik")

    @patch("utils.capture_pool.Camera")
    def test_capture_pipeline_passes_channel_to_camera(self, camera_class):
        camera_class.return_value.capture.return_value = (1, "snapshot.jpg")

        result = _capture_one_impl(
            0,
            {"ip": "192.0.2.1", "password": "secret", "channel_no": 5},
            "hik",
            "output",
            False,
        )

        self.assertEqual(result, (0, "192.0.2.1", 1, "snapshot.jpg"))
        self.assertEqual(camera_class.call_args.kwargs["channel_no"], 5)


if __name__ == "__main__":
    unittest.main()
