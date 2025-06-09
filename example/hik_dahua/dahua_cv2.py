# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2021/6/12 10:22
RTSP全称实时流协议(Real Time Streaming Protocol)，它是一个网络控制协议，设计用于娱乐、会议系统
中控制流媒体服务器。RTSP用于在希望通讯的两端建立并控制媒体会话(session)，客户端通过发出VCR-style
命令如play、record和pause等来实时控制媒体流。

// 说明：
// username：用户名，例如admin
// passwd：密码，例如12345
// ip：设备的ip地址，例如192.0.0.64
// port：端口号默认554，若为默认可以不写
// codec：有h264、MPEG-4、mpeg4这几种
// channel：通道号，起始为1
// subtype：码流类型，主码流为main，子码流为sub
rtsp://[username]:[passwd]@[ip]:[port]/[codec]/[channel]/[subtype]/av_stream

在 OpenCV 中，很简单就能读取 IP 摄像头。

大华
协议地址格式
rtsp://username:password@ip:port/cam/realmonitor?channel=1&subtype=0
协议说明
username: 用户名。例如admin。
password: 密码。例如admin。
ip: 为设备IP。例如 10.7.8.122。
port: 端口号默认为554，若为默认可不填写。
channel: 通道号，起始为1。例如通道2，则为channel=2。
subtype: 码流类型，主码流为0（即subtype=0），辅码流为1（即subtype=1）。
使用举例
rtsp://admin:admin@10.12.4.84:554/cam/realmonitor?channel=2&subtype=1

2022-05-18:添加判断摄像头是否打开成功。
            添加探测ip端口是否打开

"""
import logging

logging.basicConfig(filename='dahua_cv2.log',
                    level=logging.DEBUG,
                    filemode='a',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')
import os
import time
import cv2
from tool import portisopen


def dahua_cv2(ip, password, dir_pre=''):
    """
    :param ip:摄像头ip地址
    :param password:摄像头密码
    :param pre :保存文件夹前缀
    :return:
    """

    print("要下载的摄像头的ip和password:", ip, password)

    if not portisopen(ip, 554):
        print(f"{ip} 554 端口没有打开")
        return -1

    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 保存截图的目录
    pic_dir = dir_pre + "_" + time.strftime('%Y-%m-%d', time.localtime())

    if not os.path.isdir(pic_dir):
        os.makedirs(os.path.join('/', pic_dir))

    pic_file_name = f"{ip}_{password}_dahua_{str_time}.jpg"
    # 保存文件的路径名
    pic_full_path = os.path.join(pic_dir, pic_file_name)

    logging.debug(f'要保存的文件路名为：{pic_full_path}')

    cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(password, ip))
    if cam.isOpened():
        ret, frame = cam.read()
        cv2.imwrite(pic_full_path, frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cam.release()
        cv2.destroyAllWindows()
        print(f"ip：{ip}下载完成")
    else:
        print(f"打开摄像头{ip}失败！")


def dahua_channel(ip, password, channel_no=65):
    """
    抓取多通道截图（一般是录像机）
    @param ip: 录像机的ip
    @param password: 录像机的密码
    @param channel_no: 录像机的最大通道号
    @return:
    """
    # print("要下载的摄像头的ip和password:", ip, password)

    # if not is_port_open(ip, 554):
    #     print(f"{ip} 554 端口没有打开")
    #     return -1
    for i in range(1, channel_no):
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        cam = cv2.VideoCapture(f"rtsp://admin:{password}@{ip}:554/cam/realmonitor?channel={i}&subtype=0")
        if cam.isOpened():
            ret, frame = cam.read()
            cv2.imwrite('./{}_channel_{}.jpg'.format(ip + '_' + password + "_dahua_rstp_" + str_time, i), frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            cam.release()
            cv2.destroyAllWindows()

            print(f"录像机：{ip}通道号：{i}下载完成")
        else:
            print(f"截取录像机：{ip}通道号：{i}失败")


if __name__ == "__main__":
    dahua_channel('172.21.67.251', '5222429', 65)
    # dahua_channel('172.21.65.169','admin',65)
