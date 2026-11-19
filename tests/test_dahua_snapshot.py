import os
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np
import requests
from requests.auth import HTTPDigestAuth

from lib.Camera.base import Camera
from utils.dahua_snapshot import get_dahua_snapshot


class DahuaSnapshotTests(unittest.TestCase):
    @patch("utils.dahua_snapshot.requests.get")
    def test_fetches_snapshot_through_authenticated_cgi(self, get):
        response = requests.Response()
        response.status_code = 200
        response._content = b"\xff\xd8jpeg-data"
        get.return_value = response

        snapshot = get_dahua_snapshot(
            "192.0.2.20",
            "admin",
            "secret",
            port=8080,
            timeout=(10, 20),
        )

        self.assertEqual(snapshot, b"\xff\xd8jpeg-data")
        self.assertEqual(
            get.call_args.args[0],
            "http://192.0.2.20:8080/cgi-bin/snapshot.cgi",
        )
        self.assertEqual(get.call_args.kwargs["params"], {"channel": 1})
        self.assertIsInstance(get.call_args.kwargs["auth"], HTTPDigestAuth)
        self.assertEqual(get.call_args.kwargs["timeout"], (10, 20))

    @patch("lib.Camera.base.get_dahua_snapshot")
    @patch.object(Camera, "_open_video_stream")
    def test_retry_captures_dahua_image_without_rtsp(
        self, open_stream, get_snapshot
    ):
        encoded, jpeg = cv2.imencode(
            ".jpg", np.zeros((24, 32, 3), dtype=np.uint8)
        )
        self.assertTrue(encoded)
        get_snapshot.return_value = jpeg.tobytes()

        with tempfile.TemporaryDirectory() as folder:
            camera = Camera(
                ip="192.0.2.20",
                username="admin",
                password="secret",
                camera_type="dahua",
                folder_path=folder,
                is_water_mark=False,
                use_dahua_cgi_snapshot=True,
            )
            status, file_path = camera.capture()

        self.assertEqual(status, 1)
        self.assertTrue(os.path.isfile(file_path))
        get_snapshot.assert_called_once_with(
            "192.0.2.20",
            "admin",
            "secret",
            port=80,
            timeout=(10, 20),
        )
        open_stream.assert_not_called()


if __name__ == "__main__":
    unittest.main()
