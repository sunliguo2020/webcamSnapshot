import base64
import datetime
from itertools import groupby

import pytz
import requests
from onvif import ONVIFCamera
from requests.auth import HTTPDigestAuth
# from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import WSDiscovery
from zeep.helpers import serialize_object


# import logging
#
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)


def checkPwdAndGetCam(ip, port, usr, pwd):
    try:
        cam = ONVIFCamera(ip, port, usr, pwd)
        media = cam.create_media_service()
        profiles = media.GetProfiles()
    except Exception as e:
        if 'timed out' in str(e):
            raise Exception("连接超时，请检查地址以及端口是否正确")
        elif 'HTTPConnectionPool' in str(e):
            raise Exception(
                "连接失败，请检查地址以及端口是否正确。"
                "<br/><br/><front style='color: #aaa;'>异常信息：%s</front>" % str(e))
        else:
            raise Exception(
                "请检查账号密码是否正确。"
                "<br/><br/><front style='color: #aaa;'>异常信息：%s</front>" % str(e))
    return {
        'cam': cam,
        'media': media,
        'profiles': profiles
    }


class OnvifClient:
    """

    """

    def __init__(self, ip, port: int, usr, pwd,
                 token=None,
                 sourceToken=None,
                 nodeToken=False,
                 needSnapImg=True,
                 needPtz=True):
        """
        初始化参数
        :param ip:
        :param port:
        :param usr:
        :param pwd:
        :param token: 每个码流都会有一个独立的token，通常一个画面会有2个或更多码流，例如主码流&辅码流
        :param sourceToken: 每个画面会有一个独立的sourceToken，通常一个摄像头只有一个画面，有些红外、双摄之类的摄像头会有多个画面
        :param nodeToken: 用于获取PTZ控制信息的token，因为nodeToken有可能为None，所以用False表示没传
        :param needSnapImg: 是否需要截图，选否会加快速度
        :param needPtz: 是否需要PTZ控制，选否会加快速度，一般查摄像头列表时可以传False
        """
        self.usr = usr
        self.pwd = pwd
        result = checkPwdAndGetCam(ip, port, usr, pwd)
        self.profiles = result['profiles']
        self.cam = result['cam']
        self.media = result['media']
        self.needSnapImg = needSnapImg
        # 如果没传token，默认使用第一个token
        self.token = token if token is not None else self.profiles[0].token
        # 如果没传sourceToken，默认使用第一个sourceToken
        self.sourceToken = sourceToken if sourceToken is not None \
            else self.profiles[0].VideoSourceConfiguration.SourceToken
        # 如果没传nodeToken，默认使用第一个nodeToken
        PTZConfiguration = self.profiles[0].PTZConfiguration
        self.nodeToken = nodeToken if nodeToken is not False \
            else (PTZConfiguration.NodeToken if PTZConfiguration is not None else None)

        if needPtz:
            self.ptz = self.cam.create_ptz_service() if bool(self.cam.devicemgmt.GetCapabilities().PTZ) else None
            self.imaging = self.cam.create_imaging_service()
            self.ptzNode = self.ptz.GetNode({
                'NodeToken': self.nodeToken
            }) if self.ptz is not None and self.nodeToken is not None else None
            self.MoveOption = self.imaging.GetMoveOptions({'VideoSourceToken': self.sourceToken})
        else:
            self.cam = self.ptz = self.imaging = self.ptzNode = self.MoveOption = None

        if self.ptzNode is not None:
            SupportedPTZSpaces = self.ptzNode.SupportedPTZSpaces
            # PTZ云台移动速度峰值
            if len(SupportedPTZSpaces.PanTiltSpeedSpace) > 0:
                PanTiltSpeedSpace = SupportedPTZSpaces.PanTiltSpeedSpace
            elif len(SupportedPTZSpaces.ContinuousPanTiltVelocitySpace) > 0:
                PanTiltSpeedSpace = SupportedPTZSpaces.ContinuousPanTiltVelocitySpace
            else:
                PanTiltSpeedSpace = None
            self.PanTiltSpeedMax = PanTiltSpeedSpace[0].XRange.Max if PanTiltSpeedSpace is not None else None
            # PTZ缩放速度峰值
            if len(SupportedPTZSpaces.ZoomSpeedSpace) > 0:
                ZoomSpeedSpace = SupportedPTZSpaces.ZoomSpeedSpace
            elif len(SupportedPTZSpaces.ContinuousZoomVelocitySpace) > 0:
                ZoomSpeedSpace = SupportedPTZSpaces.ContinuousZoomVelocitySpace
            else:
                ZoomSpeedSpace = None
            self.ZoomSpeedMax = ZoomSpeedSpace[0].XRange.Max if ZoomSpeedSpace is not None else None
        else:
            self.PanTiltSpeedMax = self.ZoomSpeedMax = None
        # 聚焦移动速度峰值
        self.MoveSpeedMax = self.MoveOption.Continuous.Speed.Max \
            if self.MoveOption is not None else None

    def get_rtsp(self):
        """
        获取RTSP地址等
        参考文档：https://www.onvif.org/onvif/ver10/media/wsdl/media.wsdl#op.GetStreamUri
        """
        result = []
        StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
        for profile in self.profiles:
            obj = self.media.create_type('GetStreamUri')
            obj.StreamSetup = StreamSetup
            obj.ProfileToken = profile.token
            res_uri = self.media.GetStreamUri(obj)['Uri']
            if 'rtsp://' in res_uri and '@' not in res_uri:
                res_uri = res_uri.replace('rtsp://', 'rtsp://%s:%s@' % (self.usr, self.pwd))
            result.append({
                'source': profile.VideoSourceConfiguration.SourceToken,
                'node': profile.PTZConfiguration.NodeToken if profile.PTZConfiguration is not None else None,
                'uri': res_uri,
                'token': profile.token,
                'videoEncoding': profile.VideoEncoderConfiguration.Encoding,
                'Resolution': serialize_object(profile.VideoEncoderConfiguration.Resolution),
                'img': self.snip_image(profile.token) if self.needSnapImg else None
            })
        sortedResult = sorted(result, key=lambda d: d['source'])
        groupData = groupby(sortedResult, key=lambda x: x['source'])
        return [{'source': key, 'data': [item for item in group]} for key, group in groupData]

    def snip_image(self, token=None):
        """
        截图，如果在浏览器上访问，可在img的src填入[data:image/jpeg;base64,%s]，%s处填写return值
        参考文档：https://www.onvif.org/onvif/ver10/media/wsdl/media.wsdl#op.GetSnapshotUri
        :param token:
        :return: base64转码之后的图片
        """
        token = token if token is not None else self.token
        res = self.media.GetSnapshotUri({'ProfileToken': token})
        auth = HTTPDigestAuth(self.usr, self.pwd)
        rsp = requests.get(res.Uri, auth=auth)
        return base64.b64encode(rsp.content).decode('utf-8')

    def get_deviceInfo(self):
        """
        获取设备信息
        参考文档：https://www.onvif.org/onvif/ver10/device/wsdl/devicemgmt.wsdl#op.GetDeviceInformation
        :return: 设备信息，包括名称-Model、厂家-Manufacturer、固件版本-FirmwareVersion、序列号-SerialNumber、硬件ID-HardwareId
        """
        return serialize_object(self.cam.devicemgmt.GetDeviceInformation())

    def ptz_move(self, Velocity=None, token=None):
        """
        PTZ控制移动
        参考文档：https://www.onvif.org/onvif/ver20/ptz/wsdl/ptz.wsdl#op.ContinuousMove
        :param token: 移动设备的token
        :param Velocity: 可选参数，不传表示停止移动
        """
        token = token if token is not None else self.token
        if self.ptz is None:
            if Velocity is not None:
                # 只在移动时展示不支持，以免频繁打扰
                raise Exception("该设备不支持PTZ控制")
        else:
            if Velocity is None:
                self.ptz.Stop({'ProfileToken': token})
            else:
                request = self.ptz.create_type('ContinuousMove')
                request.ProfileToken = token
                request.Velocity = Velocity
                self.ptz.ContinuousMove(request)

    def focus_move(self, speed=None, token=None):
        """
        聚焦
        参考文档：https://www.onvif.org/onvif/ver20/imaging/wsdl/imaging.wsdl#op.Move
        :param token: VideoSourceToken
        :param speed: 正数：聚焦+，拉近；负数：聚焦-，拉远；None：停止聚焦
        """
        token = token if token is not None else self.sourceToken
        if speed is not None:
            request = self.imaging.create_type('Move')
            request.VideoSourceToken = token
            request.Focus = {'Continuous': {'Speed': speed}}
            try:
                self.imaging.Move(request)
            except Exception as e:
                raise Exception(
                    "该设备不支持该功能！"
                    "<br/><br/><front style='color: #aaa;'>异常信息：%s</front>" % str(e))
        else:
            self.imaging.Stop({'VideoSourceToken': token})

    def set_cam_time(self, timeStamp=None):
        """
        设置时间
        参考文档：https://www.onvif.org/onvif/ver10/device/wsdl/devicemgmt.wsdl#op.SetSystemDateAndTime
        :param timeStamp: 秒级时间戳，不传则使用当前时间
        """
        if timeStamp is None:
            timeNow = datetime.datetime.now()
        else:
            timeNow = datetime.datetime.fromtimestamp(int(timeStamp))
        utc_now = timeNow.astimezone(pytz.utc)
        self.cam.devicemgmt.SetSystemDateAndTime({
            'DateTimeType': 'Manual',
            'DaylightSavings': False,
            'TimeZone': {
                'TZ': 'CST-8'
            },
            'UTCDateTime': {
                'Time': {
                    'Hour': utc_now.hour,
                    'Minute': utc_now.minute,
                    'Second': utc_now.second
                },
                'Date': {
                    'Year': utc_now.year,
                    'Month': utc_now.month,
                    'Day': utc_now.day
                }
            }
        })


def ptzChangeByClient(client, codeStr, status, speed=50.0):
    """
        PTZ控制
        :param client: onvif客户端
        :param speed: 相对速度，1-100
        :param status:  状态，1-开始，0-停止
        :param codeStr: 标志字符串
        """
    ptzList = ['Up', 'Right', 'Down', 'Left', 'LeftUp', 'RightUp', 'LeftDown', 'RightDown', 'ZoomWide', 'ZoomTele']
    focusList = ['FocusFar', 'FocusNear']
    if codeStr in ptzList:
        if client.ptz is None:
            if status == 1:
                raise Exception("当前设备不支持PTZ控制")
            else:
                return
        if status == 0:
            if 'Zoom' not in codeStr:
                if client.PanTiltSpeedMax is None:
                    return
            else:
                if client.ZoomSpeedMax is None:
                    return
            client.ptz_move()
        else:
            PanTiltSpeed = 0
            ZoomSpeed = 0
            if 'Zoom' not in codeStr:
                if client.PanTiltSpeedMax is None:
                    raise Exception("当前设备不支持云台控制")
                PanTiltSpeed = client.PanTiltSpeedMax * float(speed) / 100.0
                speedTilt = PanTiltSpeed if 'Up' in codeStr else (
                    PanTiltSpeed * -1.0 if 'Down' in codeStr else 0)
                speedPan = PanTiltSpeed if 'Right' in codeStr else (
                    PanTiltSpeed * -1.0 if 'Left' in codeStr else 0)
                params = {
                    'PanTilt': {
                        'x': speedPan,
                        'y': speedTilt
                    }
                }
            else:
                if client.ZoomSpeedMax is None:
                    raise Exception("当前设备不支持缩放控制")
                ZoomSpeed = client.ZoomSpeedMax * float(speed) / 100.0
                speedZoom = 0 if 'Zoom' not in codeStr else (
                    ZoomSpeed * -1.0 if 'Wide' in codeStr else ZoomSpeed)
                params = {
                    'Zoom': speedZoom
                }
            client.ptz_move(params)
    elif codeStr in focusList:
        if client.MoveSpeedMax is None:
            if status == 1:
                raise Exception("当前设备不支持聚焦控制")
            else:
                return
        if status == 0:
            client.focus_move()
        else:
            MoveSpeed = client.MoveSpeedMax * float(speed) / 100.0
            client.focus_move(MoveSpeed if 'FocusNear' == codeStr else MoveSpeed * -1.0)
    else:
        if status == 1:
            raise Exception("该方式暂不支持")


def ws_discovery():
    """
    发现设备
    :return: 返回支持onvif协议的设备ip以及onvif端口号
    """
    result = []
    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices()
    # logger.debug(f"services:{services}")
    for service in services:
        # logger.debug(f"service:{service}")
        url = service.getXAddrs()[0]
        if 'onvif' in url and '//' in url:
            uri = url.split('//')[1]
            ipAddr = uri.split('/')[0] if '/' in uri else uri
            result.append({
                'ip': ipAddr.split(':')[0] if ':' in ipAddr else ipAddr,
                'port': int(ipAddr.split(':')[1]) if ':' in ipAddr else 80
            })
    wsd.stop()
    return result


if __name__ == '__main__':
    print(ws_discovery())
