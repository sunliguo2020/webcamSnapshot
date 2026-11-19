import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from lib.Camera.base import Camera
from utils.hikvision_device_info import (
    _request_text,
    get_hikvision_channel_snapshot,
    get_hikvision_device_info,
    get_hikvision_streaming_channel_numbers,
)
from utils.watermark import normalize_watermark_style


def response_with_text(text, status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response._content = text.encode("utf-8")
    response.encoding = "utf-8"
    return response


def response_with_content(content, status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response._content = content
    return response


class HikvisionDeviceInfoTests(unittest.TestCase):
    def test_recorder_channel_uses_channel_stream_and_filename(self):
        camera = Camera.__new__(Camera)
        camera.ip = "192.0.2.20"
        camera.username = "admin"
        camera.password = "secret"
        camera.camera_type = "hik"
        camera.channel_no = 3
        camera._file_name = None

        self.assertEqual(
            camera.camera_path,
            "rtsp://admin:secret@192.0.2.20:554/Streaming/Channels/301",
        )
        self.assertRegex(
            camera.file_name,
            r"^192\.0\.2\.20_hik_channel3_\d{14}\.jpg$",
        )

    @patch("lib.Camera.base.cv2.putText")
    @patch("lib.Camera.base.get_hikvision_device_info")
    def test_watermark_reads_and_renders_hikvision_info(
        self, get_info, put_text
    ):
        get_info.return_value = {
            "model": "DS-TEST",
            "mac": "00:11:22:33:44:55",
            "serial_number": "SN-123",
        }
        camera = Camera.__new__(Camera)
        camera.frame = np.zeros((180, 320, 3), dtype=np.uint8)
        camera.watermark_style = normalize_watermark_style({
            "text": "model:{model}\nmac:{mac}\nserial:{serial}"
        })
        camera._file_name = "snapshot.jpg"
        camera.ip = "192.0.2.13"
        camera.username = "admin"
        camera.password = "secret"
        camera.camera_type = "hik"
        camera.cam_index = 0
        camera.device_info_port = 8080

        camera.watermark()

        get_info.assert_called_once_with(
            "192.0.2.13", "admin", "secret", port=8080
        )
        rendered_lines = [
            call.args[1] for call in put_text.call_args_list[::2]
        ]
        self.assertEqual(
            rendered_lines,
            [
                "model:DS-TEST",
                "mac:00:11:22:33:44:55",
                "serial:SN-123",
            ],
        )

    @patch("utils.hikvision_device_info.requests.get")
    def test_reads_model_serial_and_mac_from_device_info(self, get):
        get.return_value = response_with_text(
            "<DeviceInfo>"
            "<model>DS-TEST</model>"
            "<serialNumber>SN-123</serialNumber>"
            "<macAddress>00:11:22:33:44:55</macAddress>"
            "</DeviceInfo>"
        )

        info = get_hikvision_device_info(
            "192.0.2.10", "admin", "secret", port=8080
        )

        self.assertEqual(info, {
            "model": "DS-TEST",
            "mac": "00:11:22:33:44:55",
            "serial_number": "SN-123",
        })
        self.assertEqual(get.call_count, 1)
        self.assertEqual(
            get.call_args.args[0],
            "http://192.0.2.10:8080/ISAPI/System/deviceInfo",
        )

    @patch("utils.hikvision_device_info.requests.get")
    def test_reads_mac_from_network_info_when_missing(self, get):
        get.side_effect = [
            response_with_text(
                '<DeviceInfo xmlns="urn:test">'
                "<model>DS-TEST</model><serialNumber>SN-123</serialNumber>"
                "</DeviceInfo>"
            ),
            response_with_text(
                "<NetworkInterface><MACAddress>AA:BB:CC:DD:EE:FF"
                "</MACAddress></NetworkInterface>"
            ),
        ]

        info = get_hikvision_device_info("192.0.2.11", "admin", "secret")

        self.assertEqual(info["mac"], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(get.call_count, 2)
        self.assertTrue(
            get.call_args_list[1].args[0].endswith(
                "/ISAPI/System/Network/interfaces/1"
            )
        )

    @patch("utils.hikvision_device_info.requests.get")
    def test_retries_basic_auth_when_digest_is_rejected(self, get):
        get.side_effect = [
            response_with_text("", status_code=401),
            response_with_text("<DeviceInfo />"),
        ]

        result = _request_text(
            "192.0.2.12", 80, "/ISAPI/System/deviceInfo", "admin", "secret"
        )

        self.assertEqual(result, "<DeviceInfo />")
        self.assertIsInstance(get.call_args_list[0].kwargs["auth"], HTTPDigestAuth)
        self.assertIsInstance(get.call_args_list[1].kwargs["auth"], HTTPBasicAuth)

    def test_rejects_invalid_port(self):
        with self.assertRaises(ValueError):
            get_hikvision_device_info("192.0.2.13", "admin", "secret", port=0)

    @patch("utils.hikvision_device_info.requests.get")
    def test_reads_recorder_channel_snapshot_with_digest_auth(self, get):
        image_bytes = b"\xff\xd8test-jpeg\xff\xd9"
        get.return_value = response_with_content(image_bytes)

        result = get_hikvision_channel_snapshot(
            "192.0.2.14", 2, "admin", "secret", port=8080
        )

        self.assertEqual(result, image_bytes)
        self.assertEqual(
            get.call_args.args[0],
            "http://192.0.2.14:8080/ISAPI/Streaming/channels/201/picture",
        )
        self.assertIsInstance(get.call_args.kwargs["auth"], HTTPDigestAuth)

    @patch("utils.hikvision_device_info.requests.get")
    def test_discovers_unique_recorder_channels_from_stream_ids(self, get):
        get.return_value = response_with_text(
            "<StreamingChannelList>"
            "<StreamingChannel><id>101</id></StreamingChannel>"
            "<StreamingChannel><id>102</id></StreamingChannel>"
            "<StreamingChannel><id>201</id></StreamingChannel>"
            "<StreamingChannel><id>1601</id></StreamingChannel>"
            "</StreamingChannelList>"
        )

        channels = get_hikvision_streaming_channel_numbers(
            "192.0.2.17", "admin", "secret"
        )

        self.assertEqual(channels, [1, 2, 16])
        self.assertEqual(
            get.call_args.args[0],
            "http://192.0.2.17:80/ISAPI/Streaming/channels",
        )

    @patch("utils.hikvision_device_info.requests.get")
    def test_rejects_stream_list_without_channel_ids(self, get):
        get.return_value = response_with_text("<StreamingChannelList />")

        with self.assertRaisesRegex(ValueError, "未返回可识别的流通道列表"):
            get_hikvision_streaming_channel_numbers(
                "192.0.2.18", "admin", "secret"
            )

    @patch("lib.Camera.base.Camera._open_video_stream")
    def test_recorder_uses_isapi_snapshot_before_rtsp(self, open_stream):
        image_ok, image = cv2.imencode(
            ".jpg", np.zeros((16, 16, 3), dtype=np.uint8)
        )
        self.assertTrue(image_ok)

        with tempfile.TemporaryDirectory() as folder:
            camera = Camera(
                ip="192.0.2.15",
                username="admin",
                password="secret",
                camera_type="hik",
                channel_no=2,
                folder_path=folder,
                is_water_mark=False,
            )
            with patch.object(camera, "check_camera", return_value=True):
                with patch(
                    "lib.Camera.base.get_hikvision_channel_snapshot",
                    return_value=image.tobytes(),
                ) as get_snapshot:
                    status, result = camera.capture()
                    self.assertTrue(os.path.isfile(result))

        self.assertEqual(status, 1)
        open_stream.assert_not_called()
        get_snapshot.assert_called_once_with(
            "192.0.2.15", 2, "admin", "secret", port=80
        )

    @patch("lib.Camera.base.Camera._open_video_stream")
    def test_recorder_falls_back_to_rtsp_when_isapi_fails(self, open_stream):
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        capture = Mock()
        capture.isOpened.return_value = True
        capture.read.return_value = (True, frame)
        open_stream.return_value = capture

        with tempfile.TemporaryDirectory() as folder:
            camera = Camera(
                ip="192.0.2.16",
                username="admin",
                password="secret",
                camera_type="hik",
                channel_no=2,
                folder_path=folder,
                is_water_mark=False,
            )
            with patch.object(camera, "check_camera", return_value=True):
                with patch(
                    "lib.Camera.base.get_hikvision_channel_snapshot",
                    side_effect=ValueError("snapshot unsupported"),
                ):
                    status, result = camera.capture()
                    self.assertTrue(os.path.isfile(result))

        self.assertEqual(status, 1)
        open_stream.assert_called_once()
        capture.release.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
