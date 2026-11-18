import unittest
from unittest.mock import patch

import requests
import numpy as np
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from lib.Camera.base import Camera, _load_chinese_font
from utils.dahua_device_info import _request_text, get_dahua_device_info
from utils.watermark import normalize_watermark_style


def response_with_text(text, status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response._content = text.encode("utf-8")
    response.encoding = "utf-8"
    return response


class DahuaDeviceInfoTests(unittest.TestCase):
    @patch("utils.dahua_device_info.requests.get")
    def test_reads_model_serial_and_mac(self, get):
        get.side_effect = [
            response_with_text(
                "deviceType=IPC-TEST\nserialNumber=SN-123"
            ),
            response_with_text(
                "table.Network.eth0.MAC=00:11:22:33:44:55"
            ),
        ]

        info = get_dahua_device_info(
            "192.0.2.10", "admin", "secret", port=8080
        )

        self.assertEqual(info, {
            "model": "IPC-TEST",
            "mac": "00:11:22:33:44:55",
            "serial_number": "SN-123",
        })
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args_list[0].args[0], "http://192.0.2.10:8080/cgi-bin/magicBox.cgi")

    @patch("utils.dahua_device_info.requests.get")
    def test_reads_macaddr_key_variant(self, get):
        get.side_effect = [
            response_with_text(
                "deviceType=IPC-TEST\nserialNumber=SN-123"
            ),
            response_with_text(
                "table.Network.eth0.MACAddr=AA:BB:CC:DD:EE:FF"
            ),
        ]

        info = get_dahua_device_info(
            "192.0.2.10", "admin", "secret"
        )

        self.assertEqual(info["mac"], "AA:BB:CC:DD:EE:FF")

    @patch("utils.dahua_device_info.requests.get")
    def test_falls_back_to_individual_magicbox_values(self, get):
        get.side_effect = [
            response_with_text("systemInfo=unsupported"),
            response_with_text("type=IPC-FALLBACK"),
            response_with_text("sn=SN-FALLBACK"),
            response_with_text(
                "Network.eth0.MacAddress=AA:BB:CC:DD:EE:FF"
            ),
        ]

        info = get_dahua_device_info("192.0.2.11", "admin", "secret")

        self.assertEqual(info["model"], "IPC-FALLBACK")
        self.assertEqual(info["serial_number"], "SN-FALLBACK")
        self.assertEqual(info["mac"], "AA:BB:CC:DD:EE:FF")

    @patch("utils.dahua_device_info.requests.get")
    def test_retries_basic_auth_when_digest_is_rejected(self, get):
        get.side_effect = [
            response_with_text("", status_code=401),
            response_with_text("type=IPC-TEST"),
        ]

        result = _request_text(
            "192.0.2.12", 80, "/cgi-bin/magicBox.cgi",
            {"action": "getDeviceType"}, "admin", "secret",
        )

        self.assertEqual(result, "type=IPC-TEST")
        self.assertIsInstance(get.call_args_list[0].kwargs["auth"], HTTPDigestAuth)
        self.assertIsInstance(get.call_args_list[1].kwargs["auth"], HTTPBasicAuth)

    @patch("lib.Camera.base.cv2.putText")
    @patch("lib.Camera.base.get_dahua_device_info")
    def test_metadata_placeholders_fetch_and_render_dahua_info(
        self, get_info, put_text
    ):
        get_info.return_value = {
            "model": "IPC-TEST",
            "mac": "00:11:22:33:44:55",
            "serial_number": "SN-123",
        }
        camera = self.make_camera(
            "dahua", "mac:{mac}\nip:{ip}\nserial:{serial}"
        )

        camera.watermark()

        get_info.assert_called_once_with(
            "192.0.2.13", "admin", "secret", port=80
        )
        rendered_lines = [
            put_text.call_args_list[index].args[1]
            for index in (0, 2, 4)
        ]
        line_baselines = [
            put_text.call_args_list[index].args[2][1]
            for index in (0, 2, 4)
        ]
        self.assertEqual(
            rendered_lines,
            ["mac:00:11:22:33:44:55", "ip:192.0.2.13", "serial:SN-123"],
        )
        self.assertEqual(line_baselines, sorted(line_baselines))
        self.assertEqual(len(set(line_baselines)), 3)

    @patch("lib.Camera.base.get_dahua_device_info")
    def test_default_watermark_does_not_query_device_info(self, get_info):
        camera = self.make_camera("dahua", "{filename}")

        camera.watermark()

        get_info.assert_not_called()

    @patch("lib.Camera.base.get_dahua_device_info")
    def test_multiline_watermark_draws_separate_rows(self, get_info):
        get_info.return_value = {
            "model": "IPC-TEST",
            "mac": "00:11:22:33:44:55",
            "serial_number": "SN-123",
        }
        camera = self.make_camera(
            "dahua", "mac:{mac}\nip:{ip}\nserial:{serial}"
        )

        camera.watermark()

        nonempty_rows = np.flatnonzero(camera.frame.any(axis=(1, 2)))
        row_groups = np.split(
            nonempty_rows,
            np.flatnonzero(np.diff(nonempty_rows) > 2) + 1,
        )
        self.assertEqual(len(row_groups), 3)

    @patch("lib.Camera.base.cv2.putText")
    def test_chinese_watermark_uses_unicode_renderer(self, put_text):
        try:
            _load_chinese_font(12)
        except OSError:
            self.skipTest("No Chinese font is installed")
        camera = self.make_camera("hik", "设备型号: 测试摄像头")

        camera.watermark()

        put_text.assert_not_called()
        self.assertTrue(np.any(camera.frame))

    @staticmethod
    def make_camera(camera_type, text):
        camera = Camera.__new__(Camera)
        camera.frame = np.zeros((180, 320, 3), dtype=np.uint8)
        camera.watermark_style = normalize_watermark_style({"text": text})
        camera._file_name = "snapshot.jpg"
        camera.ip = "192.0.2.13"
        camera.username = "admin"
        camera.password = "secret"
        camera.camera_type = camera_type
        camera.cam_index = 0
        camera.device_info_port = 80
        return camera


if __name__ == "__main__":
    unittest.main()
