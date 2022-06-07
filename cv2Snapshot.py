# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/28 12:26
"""
import os
import socket
import time
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import csv

try:
    import cv2
except Exception as e:
    os.system('pip install opencv-python')
    import cv2

logging.basicConfig(filename='cv2.log',
                    level=logging.DEBUG,
                    filemode='a',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')

# python实战练手项目---使用socket探测主机开放的端口 | 酷python
# http://www.coolpython.net/python_senior/miny_pro/find_open_port.html
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


def cv2_video_capture(ip, password, client):
    """

    :param ip:摄像头IP地址
    :param password:摄像头密码
    :param client: 摄像头类型，这里是hik和dahua
    :return:
    """
    #判断rtsp协议的554有没有打开。
    if not portisopen(ip, 554):
        logging.info(f"{ip} 554 端口没有打开")
        return -1

    # 保存截图的目录  运行程序的日期为目录名
    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    pic_dic = time.strftime('%Y-%m-%d', time.localtime())
    if not os.path.isdir(pic_dic):
        os.mkdir(pic_dic)

    # 判断是海康还是大华的摄像头
    if client == 'dahua':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(password, ip))
    elif client == 'hik':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(password, ip))
    else:
        logging.error("设备类型参数不正确")
        return -1

    if cam.isOpened():
        ret, frame = cam.read()
        try:
            file_name = ip + '_' + password + '_' + client + "_rtsp_" + str_time
            cv2.imwrite('./{}/{}.jpg'.format(pic_dic, file_name), frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 95])

            logging.info(f"ip：{ip}下载完成")
        except Exception as e:
            logging.error(f"{ip}下载过程中错误！")
            logging.error(f"{ip}"+traceback.format_exc())
        finally:
            cam.release()
            cv2.destroyAllWindows()

    else:
        logging.error(f"打开摄像头{ip}失败！")


if __name__ == '__main__':
    #前两列包含ip和密码的csv文件
    csv_file =r'C:\Users\sunliguo\Desktop\xiandai.csv'
    client_type = 'dahua'
    result = []
    futures = []
    with ThreadPoolExecutor(10) as executor:
        with open(csv_file) as fp:

            csv_reader = csv.reader(fp)

            for line in csv_reader:
                ip,passwd = line[:2]
                futures.append(executor.submit(cv2_video_capture, ip, passwd, client_type))
        for future in as_completed(futures):
            result.append(future.result())
    print(result[:20])
