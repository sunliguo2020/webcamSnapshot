"""Read-only Dahua CGI device information helpers."""

import logging
import re

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

logger = logging.getLogger("camera_logger")

REQUEST_TIMEOUT = (2, 4)


def _request_text(ip, port, path, params, username, password):
    url = f"http://{ip}:{port}{path}"
    for auth in (
        HTTPDigestAuth(username, password),
        HTTPBasicAuth(username, password),
    ):
        response = requests.get(
            url,
            params=params,
            auth=auth,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 401:
            continue
        response.raise_for_status()
        text = response.text.strip()
        if text.lower() in {"error", "failed"}:
            raise ValueError(f"设备接口返回错误：{text}")
        return text
    raise PermissionError("设备信息接口认证失败")


def _parse_fields(response_text):
    fields = []
    for line in response_text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields.append((key.strip(), value.strip()))
    return fields


def _find_field(fields, aliases):
    aliases = set(aliases)
    for key, value in fields:
        normalized_key = re.sub(r"[^a-z0-9]", "", key.lower())
        if normalized_key in aliases or any(
            normalized_key.endswith(alias) for alias in aliases
        ):
            if value:
                return value
    return ""


def _read_fields(ip, port, path, params, username, password, label):
    try:
        response_text = _request_text(
            ip, port, path, params, username, password
        )
    except (PermissionError, requests.RequestException, ValueError) as error:
        logger.warning("读取大华设备%s失败 IP=%s：%s", label, ip, error)
        return []
    return _parse_fields(response_text)


def get_dahua_device_info(ip, username, password, port=80):
    """Return model, MAC address, and serial number from Dahua CGI."""
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError("大华 HTTP 端口必须在 1 到 65535 之间")

    system_fields = _read_fields(
        ip,
        port,
        "/cgi-bin/magicBox.cgi",
        {"action": "getSystemInfo"},
        username,
        password,
        "系统信息",
    )
    model = _find_field(system_fields, {"devicetype", "type", "model"})
    serial_number = _find_field(
        system_fields, {"serialnumber", "serialno", "sn"}
    )

    if not model:
        model_fields = _read_fields(
            ip,
            port,
            "/cgi-bin/magicBox.cgi",
            {"action": "getDeviceType"},
            username,
            password,
            "型号",
        )
        model = _find_field(model_fields, {"devicetype", "type", "model"})

    if not serial_number:
        serial_fields = _read_fields(
            ip,
            port,
            "/cgi-bin/magicBox.cgi",
            {"action": "getSerialNo"},
            username,
            password,
            "序列号",
        )
        serial_number = _find_field(
            serial_fields, {"serialnumber", "serialno", "sn"}
        )

    network_fields = _read_fields(
        ip,
        port,
        "/cgi-bin/configManager.cgi",
        {"action": "getConfig", "name": "Network"},
        username,
        password,
        "MAC 地址",
    )
    mac_address = _find_field(
        network_fields, {"mac", "macaddress", "hardwareaddress"}
    )
    if not model:
        logger.warning("大华设备未返回型号 IP=%s", ip)
    if not serial_number:
        logger.warning("大华设备未返回序列号 IP=%s", ip)
    if not mac_address:
        logger.warning("大华设备网络配置未返回 MAC 地址 IP=%s", ip)

    return {
        "model": model,
        "mac": mac_address,
        "serial_number": serial_number,
    }
