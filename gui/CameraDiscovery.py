"""This module is used to get the ip and the information related to
each camera on the same network."""

__version__ = '1.0.11'

import logging
import re
import subprocess
import sys
from typing import List

from onvif import ONVIFCamera
# import WSDiscovery
from wsdiscovery import WSDiscovery

logger = logging.getLogger('onvif')
logger.setLevel(logging.DEBUG)


def get_local_ip_windows():
    """Get local IP address on Windows."""
    result = subprocess.run(['ipconfig', 'getifaddr', '以太网'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
    # 注意：'以太网' 可能需要根据您的网络接口名称进行修改
    if result.returncode != 0:
        # 尝试其他方法或返回默认IP（例如 '127.0.0.1'）
        return '127.0.0.1'
    match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', result.stdout)
    if match:
        return match.group()
    else:
        return None


def ws_discovery(scope=None) -> List[str]:
    """Discover cameras on network using onvif discovery.

    Returns:
        List: List of ips found in network.
    """
    lst = list()
    # 搜索哪个网段的设备
    if scope is None:
        # 检查操作系统
        if sys.platform.startswith('win'):
            scope = get_local_ip_windows()
        else:
            cmd = 'hostname -I'
            scope = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    logger.debug(f"{scope}")
    scopes = scope.split() if isinstance(scope, str) else [scope]

    wsd = WSDiscovery()
    wsd.start()
    ret = wsd.searchServices()
    for service in ret:
        logger.debug(f"开始遍历ret：{service}")
        get_ip = str(service.getXAddrs())
        logger.debug(f"get_ip：{get_ip}")
        get_types = str(service.getTypes())
        logger.debug(f"get_types：{get_types}")
        for ip_scope in scope.split():
            # result 是一个整数，它表示 get_ip 字符串中第一次出现 ip_scope.split('.')[0] + '.' + ip_scope.split('.')[1] 这个子字符串的起始位置（索引）
            result = get_ip.find(ip_scope.split('.')[0] + '.' + ip_scope.split('.')[1])
            logger.debug(f"result：{result}")
            # 只显示onvif设备
            if result > 0 and get_types.find('onvif') > 0:
                string_result = get_ip[result:result + 13]
                string_result = string_result.split('/')[0]
                lst.append(string_result)
    wsd.stop()
    lst.sort()
    return lst


class CameraONVIF:
    """This class is used to get the information from all cameras discovered on this specific
    network."""

    def __init__(self, ip, user, password):
        """Constructor.

        Args:
            ip (str): Ip of the camera.
            user (str): Onvif login.
            password (str): Onvif password.
        """
        self.cam_ip = ip
        self.cam_user = user
        self.cam_password = password

    def camera_start(self):
        """Start module.
        """
        mycam = ONVIFCamera(self.cam_ip, 80, self.cam_user, self.cam_password, no_cache=True)
        media = mycam.create_media_service()
        media_profile = media.GetProfiles()[0]
        self.mycam = mycam
        self.camera_media = media
        self.camera_media_profile = media_profile

    def get_hostname(self) -> str:
        """Find hostname of camera.

        Returns:
            str: Hostname.
        """
        resp = self.mycam.devicemgmt.GetHostname()
        return resp.Name

    def get_manufacturer(self) -> str:
        """Find manufacturer of camera.

        Returns:
            str: Manufacturer.
        """
        resp = self.mycam.devicemgmt.GetDeviceInformation()
        return resp.Manufacturer

    def get_model(self) -> str:
        """Find model of camera.

        Returns:
            str: Model.
        """
        resp = self.mycam.devicemgmt.GetDeviceInformation()
        return resp.Model

    def get_firmware_version(self) -> str:
        """Find firmware version of camera.

        Returns:
            str: Firmware version.
        """
        resp = self.mycam.devicemgmt.GetDeviceInformation()
        return resp.FirmwareVersion

    def get_mac_address(self) -> str:
        """Find serial number of camera.

        Returns:
            str: Serial number.
        """
        resp = self.mycam.devicemgmt.GetDeviceInformation()
        return resp.SerialNumber

    def get_hardware_id(self) -> str:
        """Find hardware id of camera.

        Returns:
            str: Hardware Id.
        """
        resp = self.mycam.devicemgmt.GetDeviceInformation()
        return resp.HardwareId

    def get_resolutions_available(self) -> List:
        """Find all resolutions of camera.

        Returns:
            tuple: List of resolutions (Width, Height).
        """
        request = self.camera_media.create_type('GetVideoEncoderConfigurationOptions')
        request.ProfileToken = self.camera_media_profile.token
        config = self.camera_media.GetVideoEncoderConfigurationOptions(request)
        return [(res.Width, res.Height) for res in config.H264.ResolutionsAvailable]

    def get_frame_rate_range(self) -> int:
        """Find the frame rate range of camera.

        Returns:
            int: FPS min.
            int: FPS max.
        """
        request = self.camera_media.create_type('GetVideoEncoderConfigurationOptions')
        request.ProfileToken = self.camera_media_profile.token
        config = self.camera_media.GetVideoEncoderConfigurationOptions(request)
        return config.H264.FrameRateRange.Min, config.H264.FrameRateRange.Max

    def get_date(self) -> str:
        """Find date configured on camera.

        Returns:
            str: Date in string.
        """
        datetime = self.mycam.devicemgmt.GetSystemDateAndTime()
        return datetime.UTCDateTime.Date

    def get_time(self) -> str:
        """Find local hour configured on camera.

        Returns:
            str: Hour in string.
        """
        datetime = self.mycam.devicemgmt.GetSystemDateAndTime()
        return datetime.UTCDateTime.Time

    def is_ptz(self) -> bool:
        """Check if camera is PTZ or not.

        Returns:
            bool: Is PTZ or not.
        """
        resp = self.mycam.devicemgmt.GetCapabilities()
        return bool(resp.PTZ)


if __name__ == '__main__':
    print(get_local_ip_windows())
    print(ws_discovery('192.168.1.21'))
