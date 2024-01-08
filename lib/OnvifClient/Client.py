import os

from onvif import ONVIFCamera,ONVIFError
import zeep
import time
from datetime import datetime
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image

def zeep_pythonvalue(self, xmlvalue):
    return xmlvalue

class Client(object):
    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username
        self.password = password
        zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue
        # zeep.xsd.simple.AnySimpleType.pythonvalue = lambda x:x

    def connect(self):
        """
        连接相机
        :return:
        """

        try:
            self.camera = ONVIFCamera(self.ip, 80, self.username, self.password)
            self.media = self.camera.create_media_service()

            profiles = self.GetProfiles()
            self.media_profile = profiles[0]  # 获取配置信息


            print("连接成功")

            return True
        except Exception as e:
            print("连接失败")
            print(e)
            return False
    def Snapshot(self,file_dir='data'):
        """
        截图
        :return:
        """
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_path = os.path.join(file_dir,str(datetime.now().strftime("%Y%m%d_%H_%M_%S"))+".jpg")

        res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})

        # response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password))
        response = requests.get(res.Uri)

        with open(file_path, 'wb') as f:  # 保存截图
            f.write(response.content)

        print("保存截图成功：%s"%file_path)

    def Snapshot_resize(self, file_dir='data', size=None):
        """
        截图并调整尺寸
        :param picname: 保存截图的文件名
        :param new_size: 调整后的尺寸，格式为(width, height)
        """
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_path = os.path.join(file_dir,str(datetime.now().strftime("%Y%m%d_%H_%M_%S"))+".jpg")

        res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})
        response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password))
        with open(file_path, 'wb') as f:
            f.write(response.content)

        if size:
            with Image.open(file_path) as img:
                img = img.resize(size)
                img.save(file_path)

        print("保存截图成功：%s"%file_path)

    def GetStreamUri(self):
        obj = self.media.create_type('GetStreamUri')
        obj.StreamSetup = {'Stream': 'rtp-unicast', 'Transport': {'Protocol': 'RTSP'}}
        obj.ProfileToken = self.media_profile.token
        res = self.media.GetStreamUri(obj)
        url = res['Uri']

        # url示例 rtsp://192.168.1.176:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif

        if url.startswith("rtsp://"):
            url_suffix = url[7:]
            url = "rtsp://%s:%s@%s"%(self.username,self.password,url_suffix)

        return url

    def GetDeviceInformation(self):
        # https://www.onvif.org/onvif/ver10/device/wsdl/devicemgmt.wsdl

        devicemgmt = self.camera.devicemgmt
        capabilities = devicemgmt.GetCapabilities()
        services = devicemgmt.GetServices(True)

        hostname1 = devicemgmt.GetHostname()
        devicemgmt.SetHostname("hh")
        hostname2 = devicemgmt.GetHostname()

        # 查看设备支持的范围
        scopes1 = devicemgmt.GetScopes()
        devicemgmt.SetScopes([
            "onvif://www.onvif.org/name/qj92122",
            "onvif://www.onvif.org/location/city/hs22"
        ])
        scopes2 = devicemgmt.GetScopes()


        info = devicemgmt.GetDeviceInformation()
        interfaces = devicemgmt.GetNetworkInterfaces()

        return info

    def GetVideoSourceConfigurations(self):
        return self.media.GetVideoSourceConfigurations()

    def GetVideoEncoderConfigurations(self):
        return self.media.GetVideoEncoderConfigurations()

    def GetProfiles(self):
        return self.media.GetProfiles()

    def GetOSDs(self):
        return self.media.GetOSDs()

    def SetVideoEncoderConfiguration(self, ratio=(1920, 1080), Encoding='H264', bitrate=2044, fps=30, gop=50):

        videoSourceConfig = self.GetVideoSourceConfigurations()
        encoderConfig = self.GetVideoEncoderConfigurations()

        if ratio[0] > videoSourceConfig[0]['Bounds']['width']:
            raise ONVIFError(f'ratio Error: max width should less then {videoSourceConfig[0]["Bounds"]["width"]}')
        if ratio[1] > videoSourceConfig[0]['Bounds']['height']:
            raise ONVIFError(f'ratio Error: max height should less then {videoSourceConfig[0]["Bounds"]["height"]}')

        if Encoding.upper() not in ('H265', 'H264'):
            raise ONVIFError(f'encoding Error: enconding format should be "H265" or "H264"')

        encoderConfig[0]['Resolution']['Width'] = ratio[0]
        encoderConfig[0]['Resolution']['Height'] = ratio[1]
        encoderConfig[0]['Encoding'] = Encoding.upper()
        encoderConfig[0]['RateControl']['FrameRateLimit'] =fps
        encoderConfig[0]['RateControl']['BitrateLimit'] = bitrate
        # encoderConfig[0]['GovLength'] = gop

        self.media.SetVideoEncoderConfiguration(
            {
                'Configuration':encoderConfig[0],
                'ForcePersistence':True
            }
        )
