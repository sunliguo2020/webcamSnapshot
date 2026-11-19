import unittest
from unittest.mock import patch

import requests
import numpy as np
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from lib.Camera.base import Camera
from utils.hikvision_device_info import (
    _request_text,
    get_hikvision_device_info,
)
from utils.watermark import normalize_watermark_style


def response_with_text(text, status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response._content = text.encode("utf-8")
    response.encoding = "utf-8"
    return response


class HikvisionDeviceInfoTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
