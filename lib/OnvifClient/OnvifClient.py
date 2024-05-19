import logging
import os
from datetime import datetime

import requests
import zeep
from PIL import Image
from onvif import ONVIFCamera, ONVIFError
from requests.auth import HTTPDigestAuth

from mylogger.setlogger import configure_logger

configure_logger()
logger = logging.getLogger("camera_logger")


def zeep_pythonvalue(self, xmlvalue):
    return xmlvalue


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


class OnvifClient(object):
    """
    ONVIF客户端类
    使用python-onvif基本流程：
    1.创建ONVIFCamera对象，我们可以理解为支持onvif协议的设备。
    2.调用ONVIFCamera对象的create_xxx_service()方法来获取相应服务。
    3.一般我们首先会调用create_media_service()方法来获取media_service()服务，
    然后调用这个服务提供的GetProfiles()来获取配置信息，可以从配置信息里取到Token。
    4.接下来就是通过给onvif接口传递参数，来调用相关接口了。
    """

    def __init__(self,
                 ip: str,
                 port=80,
                 username: str = 'admin',
                 password: str = 'admin',
                 folder_path=None
                 ):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        #  创建 onvif-zeep soap客户端
        # ONVIFCamera instance
        result = checkPwdAndGetCam(self.ip, self.port, self.username, self.password)
        # 获取媒体配置信息 例如：主码流 辅码流  第三码流
        self.profiles = result['profiles']
        logger.debug(f"self.profiles:{self.profiles}")
        self.camera = result['cam']
        self.media = result['media']
        self.media_profile = self.profiles[0]

        zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue
        # zeep.xsd.simple.AnySimpleType.pythonvalue = lambda x:x

        # 默认保存的文件夹
        self.folder_path = folder_path if folder_path else \
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         datetime.now().strftime('%Y-%m-%d'))

    def connect(self):
        """
        连接相机并初始化media属性
        :return:
        """
        try:
            self.camera = ONVIFCamera(self.ip, self.port, self.username, self.password)
            logger.debug(f"wsdl_dir：{self.camera.wsdl_dir}")
            # 创建媒体服务
            self.media = self.camera.create_media_service()
            logger.debug(f"创建媒体服务：{self.media}")

            self.profiles = self.GetProfiles()
            self.media_profile = self.GetProfiles()[0]  # 获取配置信息

            logger.debug(f"slef.GetProfiles:{self.GetProfiles()}")
            logger.debug(f"获取配置信息：{self.media_profile}")
            logger.debug(f'连接相机成功，IP地址：{self.ip}')

            return self.camera

        except Exception as e:
            logger.debug(f"连接相机失败，IP地址：{self.ip},错误信息：{e}")
            return False

    def getFileName(self):
        """
        获取截图文件名
        @return:
        """
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name_list = [self.ip, self.username, self.password, 'onvif', datetime_str]
        file_name = '_'.join([str(i) for i in file_name_list]) + '.jpg'
        return file_name

    def getFilePath(self, folder_path=None):
        """
        获取默认文件路径，并确保目录已经被创建
        @param folder_path:
        @return:
        """
        folder_path = folder_path if folder_path is not None else self.folder_path

        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, self.getFileName())

        return file_path

    def Snapshot(self, file_dir=None):
        """
        截图 拍摄快照
        :param file_dir: 文件保存路径，如果为空，则使用默认路径
        :return:
        @type file_dir: string
        """
        # 在尝试使用media属性之前，确保已经连接到相机
        if not self.media:
            logger.error('无法连接到相机，无法拍摄快照')
            return False
        # 如果没有传入保存的目录，则使用默认的保存目录
        if file_dir is not None:
            if not os.path.isdir(file_dir):
                os.makedirs(file_dir)

            file_path = os.path.join(file_dir, self.getFileName())
        else:
            file_path = self.getFilePath()
        """
        res:
        {
            'Uri': 'http://192.168.1.50/onvif-http/snapshot?Profile_1',
            'InvalidAfterConnect': False,
            'InvalidAfterReboot': False,
            'Timeout': datetime.timedelta(0),
            '_value_1': None,
            '_attr_1': None
        }
        """
        res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})

        logger.debug(f"抓图url res:{res}")

        logger.debug(f"media_profile.token:{self.media_profile.token}")
        logger.debug(f"准备登录res.Uri:{res.Uri}")

        # 登录认证截图
        response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password))

        with open(file_path, 'wb') as f:  # 保存截图
            f.write(response.content)

        logger.debug("保存截图成功：%s" % file_path)

        return file_path

    def Snapshot_resize(self, file_dir='data', size=None):
        """
        截图并调整尺寸
        :param picname: 保存截图的文件名
        :param new_size: 调整后的尺寸，格式为(width, height)
        @param size:
        @param file_dir:
        """
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_path = os.path.join(file_dir, str(datetime.now().strftime("%Y%m%d_%H_%M_%S")) + ".jpg")

        res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})
        response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password))
        with open(file_path, 'wb') as f:
            f.write(response.content)

        if size:
            with Image.open(file_path) as img:
                img = img.resize(size)
                img.save(file_path)

        print("保存截图成功：%s" % file_path)

    def GetStreamUri(self):
        """
        获取RTSP视频流地址
        @return:
        """
        obj = self.media.create_type('GetStreamUri')
        obj.StreamSetup = {'Stream': 'rtp-unicast', 'Transport': {'Protocol': 'RTSP'}}
        obj.ProfileToken = self.media_profile.token
        res = self.media.GetStreamUri(obj)
        url = res['Uri']

        # url示例 rtsp://192.168.1.176:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif

        if url.startswith("rtsp://"):
            url_suffix = url[7:]
            url = "rtsp://%s:%s@%s" % (self.username, self.password, url_suffix)

        return url

    def GetDeviceInformation(self):
        """
        获取设备信息
        {
            'Manufacturer': 'HIKVISION',
            'Model': 'DS-2DE2204IW-D3',
            'FirmwareVersion': 'V5.6.11 build 190426',
            'SerialNumber': 'DS-2DE2204IW-D320170316CCCH731956144W',
            'HardwareId': '88'
        }
        @return:
        """
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
        """

        Returns:

        """
        return self.media.GetVideoSourceConfigurations()

    def GetVideoEncoderConfigurations(self):
        return self.media.GetVideoEncoderConfigurations()

    def GetProfiles(self):
        return self.media.GetProfiles()

    def GetOSDs(self):
        """

        Returns:

        """
        return self.media.GetOSDs()

    def GetOSD(self):
        """
        返回osd
        @return:
        """
        osds = self.media.GetOSDs()
        for item in osds:
            # 检查当前字典中是否包含 'TextString' 这个键
            if 'TextString' in item:
                # logger.debug(f"{type(item['TextString'])}")
                # 如果包含，则进一步获取 'TextString' 字典中的 'PlainText' 值
                # 手动添加 Type为 Plain
                text_string_value = item['TextString']
                if text_string_value['Type'] == 'Plain':
                    return text_string_value['PlainText']
                elif text_string_value['Type'] == 'DateAndTime':
                    logger.debug(f' 这是时间的osd TextString中Type值为：{text_string_value["Type"]}')

            else:
                print("'TextString' 键不存在于当前字典中")

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
        encoderConfig[0]['RateControl']['FrameRateLimit'] = fps
        encoderConfig[0]['RateControl']['BitrateLimit'] = bitrate
        # encoderConfig[0]['GovLength'] = gop

        self.media.SetVideoEncoderConfiguration(
            {
                'Configuration': encoderConfig[0],
                'ForcePersistence': True
            }
        )


if __name__ == '__main__':
    # Onvif对象
    client = OnvifClient(ip='192.168.1.50', username='admin', password='shiji123')

    # 截图
    # root_dir = os.path.dirname(os.path.abspath(__file__))
    client.Snapshot()

    # print(client.getFilePath())
    # profiles = client.GetProfiles()

    # print('测试获取osd')
    # osds = client.GetOSDs()
    # # logger.debug(f'osd:{osds}')
    # osd = client.GetOSD()
    # if osd:
    #     logger.debug(f"osd:{osd}")

    # info = client.GetDeviceInformation()
    # logger.debug(f"测试硬件信息:{info}")

    streamUri = client.GetStreamUri()
    logger.debug(f"rtsp 地址 GetStreamUri:{streamUri}")

    # videoSourceConfig = client.GetVideoSourceConfigurations()
    #
    # encoderConfig1 = client.GetVideoEncoderConfigurations()
    # client.SetVideoEncoderConfiguration()
    # encoderConfig2 = client.GetVideoEncoderConfigurations()

    # test_client(client)

    # print("end")
