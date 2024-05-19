import pprint
import time
import json

from onvifBase import ws_discovery, OnvifClient, ptzChangeByClient


# 设备发现
print(ws_discovery())

client = OnvifClient('192.168.1.50', 80, 'admin', 'shiji123', needSnapImg=False)
# 如果要控制特定摄像头，可以下边这样写
# client = OnvifClient('192.168.1.10', 80, 'admin', '123456', token="ProfileToken002", sourceToken= "VideoSourceToken002", nodeToken="NodeToken002", needSnapImg=False)

# 获取所有画面所有码流的RTSP地址、token(即ProfileToken)、sourceToken、nodeToken等信息
pprint.pprint(client.get_rtsp())

# 获取设备信息
# print(json.dumps(client.get_deviceInfo()))

# 设置时间
# client.set_cam_time()

# 云台与聚焦控制
# 云台上移
# ptzChangeByClient(client, 'Up', 1)
# 移动一秒
time.sleep(1)
# 然后停止
# ptzChangeByClient(client, 'Up', 0)
