"""Dahua CGI snapshot helper."""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

DEFAULT_TIMEOUT = (5, 10)


def get_dahua_snapshot(
    ip, username, password, port=80, channel=1, timeout=DEFAULT_TIMEOUT
):
    """Fetch a JPEG snapshot through Dahua's HTTP CGI interface."""
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError("大华 HTTP 端口必须在 1 到 65535 之间")
    try:
        channel = int(channel)
    except (TypeError, ValueError) as error:
        raise ValueError("大华摄像头通道号必须是整数") from error
    if channel < 1:
        raise ValueError("大华摄像头通道号必须大于 0")

    url = f"http://{ip}:{port}/cgi-bin/snapshot.cgi"
    for auth in (
        HTTPDigestAuth(username, password),
        HTTPBasicAuth(username, password),
    ):
        response = requests.get(
            url,
            params={"channel": channel},
            auth=auth,
            timeout=timeout,
        )
        if response.status_code == 401:
            continue
        response.raise_for_status()
        if not response.content.startswith(b"\xff\xd8"):
            raise ValueError("大华快照接口未返回有效 JPEG 图像")
        return response.content

    raise PermissionError("大华快照接口认证失败")
