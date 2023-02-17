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

"""
import csv
import logging
import os
import time

from tool import portisopen

try:
    import cv2
except ImportError as e:
    os.system('pip install opencv-python')
    import cv2

logging.basicConfig(filename='hik_cv2.log',
                    level=logging.INFO,
                    filemode='a',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')


def hik_cv2(ip="192.168.1.200", password='admin'):
    """
    文件名保存的格式：ip_password_hik_timestr.jpg

    :param ip: 摄像头ip地址
    :param password:摄像头密码
    :return:
    """
    if not portisopen(ip, 554):
        print(f"{ip}:554 端口没有打开")
        logging.debug(f'{ip} 554端口没开放或者网络不通！')
        return -1

    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 保存截图的目录
    pic_dir = time.strftime('%Y-%m-%d', time.localtime())

    if not os.path.isdir(pic_dir):
        os.mkdir(os.path.join('./', pic_dir))
    pic_file_name = f"{ip}_{password}_hik_{str_time}.jpg"
    # 保存文件的路径名
    pic_full_path = os.path.join(pic_dir, pic_file_name)

    logging.debug(f'要保存的文件路名为：{pic_full_path}')

    try:
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(password, ip))
        ret, frame = cam.read()
        retval = cv2.imwrite(pic_full_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        # if not retval:
        #     logging.debug(f'{ip}保存图像失败')
    except Exception as e:
        logging.debug(f'{ip} cv2 失败{e}')
    finally:
        cam.release()
        cv2.destroyAllWindows()
        if not os.path.isfile(pic_full_path):
            logging.info(f'{ip}保存截图失败')


if __name__ == "__main__":
    csv_file = r'./csv_file/ruizhi.csv'

    with open(csv_file, encoding='utf-8') as f:
        count = 1
        f_read = csv.reader(f)
        for i in f_read:
            if count >= 0:
                ip, password = i
                print(count, ":", ip)
                try:
                    hik_cv2(ip, password)
                except Exception as e:
                    print(e)
            count += 1
