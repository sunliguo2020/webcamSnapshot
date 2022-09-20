# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/28 12:26
"""
import csv
import logging
import os
import socket
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

try:
    import cv2
except Exception as e:
    os.system('pip install opencv-python')
    import cv2

logging.basicConfig(filename='cv2.log',
                    level=logging.DEBUG,
                    filemode='w',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')



def portisopen(ip, port):
    """

    :param ip:
    :param port:
    :return:
    """
    flag = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    state = sock.connect_ex((ip, port))

    if 0 == state:
        logging.debug(f"{ip}:{port} is open")
        flag = True
    else:
        logging.debug(f"{ip}:{port} is closed")
        flag = False

    sock.close()
    return flag


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


def cv2_video_capture(ip, password, client=None, base_dir=None):
    """
    :param ip:摄像头IP地址
    :param password:摄像头密码
    :param client: 摄像头类型，这里是hik和dahua
    :return:
    """

    if not os.path.isdir(base_dir):
        os.mkdir(base_dir)
    # 判断rtsp协议的554端口有没有打开。
    port_isopen_result = portisopen(ip, 554)
    logging.debug(f"判断{ip}端口是否打开{type(port_isopen_result)},{port_isopen_result}")
    if not port_isopen_result:
        logging.debug(f"{ip} 554 端口没有打开")
        # return -1

    # 保存截图的目录  运行程序的日期为目录名
    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    pic_dir = os.path.join(base_dir, time.strftime('%Y-%m-%d', time.localtime()))

    if not os.path.isdir(pic_dir):
        os.mkdir(pic_dir)
    logging.debug(f"保存截图的目录:{pic_dir}")

    # 判断是海康还是大华的摄像头
    if client == 'dahua':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(password, ip))
    elif client == 'hik':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(password, ip))
    else:
        logging.error("设备类型参数不正确")
        return -1
    # logging.debug(cam)
    if cam.isOpened():
        ret, frame = cam.read()
        try:
            file_name = ip + '_' + password + '_' + client + "_rtsp_" + str_time + ".jpg"
            cv2.imwrite(os.path.join(pic_dir, file_name), frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 95])

            logging.debug(f"ip：{ip},file_name:{file_name}下载完成")
        except Exception as e:
            logging.error(f"{ip}下载过程中错误！")
            logging.error(f"{ip}" + traceback.format_exc())
        finally:
            cam.release()
            cv2.destroyAllWindows()

    else:
        logging.debug(f"打开摄像头{ip}失败！")


if __name__ == '__main__':
    # 前两列包含ip和密码的csv文件
    csv_file = r'D:\xiandai.csv'
    base_dir = r'd:\监控截图'
    client_type = 'hik'
    result = []
    futures = []
    with ThreadPoolExecutor() as executor:
        with open(csv_file) as fp:
            csv_reader = csv.reader(fp)
            for line in csv_reader:
                ip, passwd = line[:2]
                print(ip, passwd)
                futures.append(executor.submit(cv2_video_capture, ip, passwd, client_type, base_dir))
                # break
        # for future in as_completed(futures):
        #     result.append(future.result())
    # print(result[:20])
