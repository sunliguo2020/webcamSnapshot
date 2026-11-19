"""Read-only Hikvision ISAPI device information helpers."""

import argparse
import getpass
import json
import logging
import re
import xml.etree.ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

logger = logging.getLogger("camera_logger")

REQUEST_TIMEOUT = (2, 4)


def _request_text(ip, port, path, username, password):
    url = f"http://{ip}:{port}{path}"
    for auth in (
        HTTPDigestAuth(username, password),
        HTTPBasicAuth(username, password),
    ):
        response = requests.get(url, auth=auth, timeout=REQUEST_TIMEOUT)
        if response.status_code == 401:
            continue
        response.raise_for_status()
        return response.text.strip()
    raise PermissionError("设备信息接口认证失败")


def _parse_xml(response_text):
    try:
        return ET.fromstring(response_text)
    except ET.ParseError as error:
        raise ValueError(f"设备返回的 XML 无法解析：{error}") from error


def _find_value(root, aliases):
    aliases = set(aliases)
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        normalized_tag = re.sub(r"[^a-z0-9]", "", tag.lower())
        if normalized_tag in aliases and element.text and element.text.strip():
            return element.text.strip()
    return ""


def _read_xml(ip, port, path, username, password, label):
    try:
        response_text = _request_text(ip, port, path, username, password)
        return _parse_xml(response_text)
    except (
        PermissionError,
        requests.RequestException,
        ValueError,
    ) as error:
        logger.warning("读取海康设备%s失败 IP=%s：%s", label, ip, error)
        return None


def get_hikvision_device_info(ip, username, password, port=80):
    """Return model, MAC address, and serial number from Hikvision ISAPI."""
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError("海康 HTTP 端口必须在 1 到 65535 之间")

    device_info = _read_xml(
        ip,
        port,
        "/ISAPI/System/deviceInfo",
        username,
        password,
        "设备信息",
    )
    model = ""
    serial_number = ""
    mac_address = ""
    if device_info is not None:
        model = _find_value(device_info, {"model", "productclass"})
        serial_number = _find_value(device_info, {"serialnumber", "serialno"})
        mac_address = _find_value(device_info, {"macaddress", "mac"})

    if not mac_address:
        network_info = _read_xml(
            ip,
            port,
            "/ISAPI/System/Network/interfaces/1",
            username,
            password,
            "MAC 地址",
        )
        if network_info is not None:
            mac_address = _find_value(network_info, {"macaddress", "mac"})

    if not model:
        logger.warning("海康设备未返回型号 IP=%s", ip)
    if not serial_number:
        logger.warning("海康设备未返回序列号 IP=%s", ip)
    if not mac_address:
        logger.warning("海康设备未返回 MAC 地址 IP=%s", ip)

    return {
        "model": model,
        "mac": mac_address,
        "serial_number": serial_number,
    }


def main():
    parser = argparse.ArgumentParser(
        description="读取海康摄像头型号、序列号和 MAC 地址"
    )
    parser.add_argument("ip", help="摄像头 IP 地址")
    parser.add_argument("--username", default="admin", help="登录用户名")
    parser.add_argument("--port", type=int, default=80, help="HTTP 管理端口")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    password = getpass.getpass("摄像头密码: ")
    info = get_hikvision_device_info(
        args.ip, args.username, password, port=args.port
    )
    print(json.dumps(info, ensure_ascii=False, indent=2))
    if not any(info.values()):
        parser.exit(1, "未能读取到设备信息，请检查设备地址、端口和账号密码。\n")


if __name__ == "__main__":
    main()
