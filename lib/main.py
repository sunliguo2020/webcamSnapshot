import os
import sys

# 假设当前脚本在项目根目录下的某个子目录中
# 获取当前脚本的绝对路径
current_script_dir = os.path.abspath(os.path.dirname(__file__))

# 获取项目根目录的路径，这里假设项目根目录是当前脚本目录的上级目录
project_root_dir = os.path.dirname(current_script_dir)

# 将项目根目录添加到sys.path中
sys.path.append(project_root_dir)

from OnvifClient import OnvifClient
from mylogger import logger


def test_client(ip='192.168.1.64',
                port=80,
                username="admin",
                password="admin",
                *args,
                **kwargs):
    """

    @param ip:
    @param port:
    @param username:
    @param password:
    @param base_dir:
    @param args:
    @param kwargs:
    @return:
    """
    client = OnvifClient(ip=ip,
                         port=port,
                         username=username,
                         password=password)

    if not client.connect():
        exit(0)
    # 截图
    client.Snapshot()

    # 获取视频流地址
    streamUri = client.GetStreamUri()
    print(streamUri)
    # profiles = client.GetProfiles()
    # osds = client.GetOSDs()
    # # print(osds)
    # # info = client.GetDeviceInformation()
    # videoSourceConfig = client.GetVideoSourceConfigurations()
    #
    # encoderConfig1 = client.GetVideoEncoderConfigurations()
    # # client.SetVideoEncoderConfiguration()
    # encoderConfig2 = client.GetVideoEncoderConfigurations()
    #
    # # test_client(client)

    print("end")


def test_find():
    """
    查找onvif设备
    @return:
    """
    # http://www.onvif.org/onvif/ver10/network/wsdl/remotediscovery.wsdl

    # from wsdiscovery.threaded import NetworkingThread, MULTICAST_PORT
    from wsdiscovery import WSDiscovery

    clients = []

    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices()

    for service in services:
        get_ip = str(service.getXAddrs())
        get_types = str(service.getTypes())
        clients.append(get_ip)

    wsd.stop()
    clients.sort()

    print("------------------start------------------------")
    for client in clients:
        print(client)
        logger.debug(client)


if __name__ == '__main__':
    logger.debug("ONVIFClientManager")

    # test_find()
    test_client(ip='172.30.189.68',
                port=8899,
                username='admin',
                password='')
