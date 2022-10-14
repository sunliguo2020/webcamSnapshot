# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2021/6/12 10:22

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


import os
import socket
import time
import cv2
import csv

def portisopen(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    state = sock.connect_ex((ip, port))
    if 0 == state:
        # print("port is open")
        return True
    else:
        # print("port is closed")
        return False


def is_reachable(ip):
    response = os.system('ping -c 1' + ip)
    if response == 0:
        print(ip + 'is reachable')
        return 1
    else:
        print(ip + 'is not reachable')
        return 0


def is_ipv4(ip: str) -> bool:
    """
    检查ip是否合法
    :param: ip ip地址
    :return: True 合法 False 不合法
    """
    return True if [1] * 4 == [x.isdigit() and 0 <= int(x) <= 255 for x in ip.split(".")] else False


def dahua_cv2(ip, password):
    """
    :param ip:
    :param password:
    :return:
    """
    # ip, password = params
    print("要下载的摄像头的ip和password:", ip, password)

    if not portisopen(ip, 554):
        print(f"{ip} 554 端口没有打开")
        return -1

    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # print(str_time)
    # cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(password, ip))

    cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(password, ip))
    if cam.isOpened():
        ret, frame = cam.read()
        cv2.imwrite('./{}.jpg'.format(ip + '_' + password + "_dahua_rstp_" + str_time), frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cam.release()
        cv2.destroyAllWindows()

        print(f"ip：{ip}下载完成")
    else:
        print(f"打开摄像头{ip}失败！")


if __name__ == "__main__":
    with open('./tejiao.csv') as f:
        count = 1
        csv_read = csv.reader(f)
        for ip, passwd in csv_read:
            # ip = i[0]
            # passwd = i[1]
            if count >= 0:
                print(count, ":", ip)
                try:
                    dahua_cv2(ip, passwd)
                except Exception as e:
                    print(e)
            count += 1
