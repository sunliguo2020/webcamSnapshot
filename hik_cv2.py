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


def hik_cv2(cam_ip="192.168.1.200", cam_pwd='admin', dir_pre=''):
    """
    文件名保存的格式：ip_password_hik_timestr.jpg

    :param cam_ip: 摄像头ip地址
    :param cam_pwd:摄像头密码
    :param dir_pre: 保存目录前缀
    :return:
            -1:网络不通或者端口554没有打开

    """
    if not portisopen(cam_ip, 554):
        print(f"{cam_ip}:554 端口没有打开")
        logging.debug(f'{cam_ip} 554端口没开放或者网络不通！')
        return -1

    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 保存截图的目录
    pic_dir = dir_pre + "_" + time.strftime('%Y-%m-%d', time.localtime())

    if not os.path.isdir(pic_dir):
        os.makedirs(os.path.join('./', pic_dir))

    pic_file_name = f"{cam_ip}_{cam_pwd}_hik_{str_time}.jpg"
    # 保存文件的路径名
    pic_full_path = os.path.join(pic_dir, pic_file_name)

    logging.debug(f'要保存的文件路名为：{pic_full_path}')

    try:
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(cam_pwd, cam_ip))
        ret, frame = cam.read()
        retval = cv2.imwrite(pic_full_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        # if not retval:
        #     logging.debug(f'{ip}保存图像失败')
    except Exception as e:
        logging.debug(f'{cam_ip} cv2 失败{e}')
    finally:
        cam.release()
        cv2.destroyAllWindows()

        if not os.path.isfile(pic_full_path):
            logging.info(f'{cam_ip}保存截图失败')
            return -2
        else:
            logging.info(f"{cam_ip}保存截图成功")
            return 1


def gen_ip_password_from_csv(file_path, line_count=0):
    """
    读取csv文件，返回ip，password
    :param file_path: 要读取的csv文件
    :param line_count: 跳过前几行
    :return: ip,password
    """
    with open(file_path, encoding='utf-8') as f:
        # 跳过前几行
        for i in range(line_count):
            next(f)  # 跳过一行

        csv_read = csv.reader(f)
        for cam_ip, cam_pwd in csv_read:
            yield cam_ip, cam_pwd


if __name__ == "__main__":
    # 包含ip和密码的csv文件
    csv_file = r'./txt/ruizhi.csv'
    # 截图失败的IP地址
    failed_ip = []

    for count, (ip, password) in enumerate(gen_ip_password_from_csv(csv_file, 0), start=1):

        print(count, ":", ip)
        try:
            result = hik_cv2(ip, password, dir_pre=os.path.basename(csv_file).split('.')[0])

        except Exception as e:
            print(e)
        # 统计下载失败的IP地址
        if result < 0:
            print(f"{ip}下载失败")
            failed_ip.append(ip)

    print(f"总共有{len(failed_ip)}个ip截图失败")
    print(failed_ip)
