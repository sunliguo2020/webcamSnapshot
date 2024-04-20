import os
from mylogger import logger
from OnvifClient.CameraClient import CameraClient


# from OnvifClient.PTZ import PTZ
#
#
# def test_ptz(client: Client):
#     ptz = PTZ(client)
#
#     while True:
#         # zoom in
#         # ptz.zoom(1.0, 2)
#         # zoom out
#         print("开始缩小")
#         ptz.zoom(-1.0, 2)
#         ptz.zoom(-1.0, 2)
#         ptz.zoom(-1.0, 2)
#
#         print("开始放大")
#         ptz.zoom(1.0, 2)
#
#     # move down
#     ptz.move_x(val=-1.0, timeout=2)
#
#     time.sleep(10)
#     ptz.move_x(val=1.0, timeout=2)
#     time.sleep(10)
#
#     exit(0)
#     # Set preset
#     # ptz.move_x(x=1.0, timeout=1)
#     # ptz.set_preset('home')
#
#     # move right -- (velocity, duration of move)
#     ptz.move_x(val=1.0, timeout=2)
#
#     # move left
#     ptz.move_x(val=-1.0, timeout=2)
#
#     # move down
#     ptz.move_y(val=-1.0, timeout=2)
#
#     # Move up
#     ptz.move_y(val=1.0, timeout=2)
#
#     # Absolute pan-tilt (pan position, tilt position, velocity)
#     # DOES NOT RESULT IN CAMERA MOVEMENT
#     ptz.move_absolute(x=-1.0, y=1.0, velocity=1.0)
#     ptz.move_absolute(x=1.0, y=-1.0, velocity=1.0)
#
#     # Relative move (pan increment, tilt increment, velocity)
#     # DOES NOT RESULT IN CAMERA MOVEMENT
#     # ptz.move_relative(0.5, 0.5, 8.0)
#
#     # Get presets
#     ptz.get_preset()
#     # Go back to preset
#     ptz.goto_preset('home')


def test_client():
    client = CameraClient(ip='192.168.1.64', username='test', password='shiji123')

    if not client.connect():
        exit(0)
    # 截图
    root_dir = os.path.dirname(os.path.abspath(__file__))
    client.Snapshot(file_dir=os.path.join(root_dir, "data"))

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
    test_client()
