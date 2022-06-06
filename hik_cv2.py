# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2021/6/12 10:22
"""
'''
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
'''


import socket
import os
import time
try:
    import cv2
except Exception as e:
    os.system('pip install opencv-python')
    import cv2


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


def hik_cv2(ip="192.168.1.200", password='admin'):
    """

    :param ip: 摄像头ip地址
    :param password:摄像头密码
    :return:
    """
    if not portisopen(ip,554):
        print(f"{ip}:554 端口没有打开")
        return -1

    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    pic_dic = time.strftime('%Y-%m-%d', time.localtime())
    if not os.path.isdir(pic_dic):
        os.mkdir(pic_dic)
    try:
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(password, ip))
        ret, frame = cam.read()
        cv2.imwrite(pic_dic + '/{}.jpg'.format(ip + '_' + password + "_" + str_time), frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cam.release()
        cv2.destroyAllWindows()
        print(f"ip：{ip}下载完成")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    with open('./yangkouzhongying.txt') as f:
        count = 1
        for i in f:
            if count >= 0:
                i = i.replace('\n', '')
                print(count, ":", i)
                try:
                    hik_cv2(i, "hik12345")
                except Exception as e:
                    print(e)
            count += 1
