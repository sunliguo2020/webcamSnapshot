# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-11-10 7:43
根据 csv文件，截图目录， 开始截图
"""
import csv
import logging
import os.path

from Camera import Camera
from utils.tool import convert_ip_list

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def capture_from_csv(csv_file, save_path=None):
    """

    @param csv_file:
    @type save_path: object
    @return:
    """
    # 1、分析csv文件,得到保存ip地址，密码，和次数的列表
    cam_list = convert_ip_list(csv_file)
    # print(cam_list)
    # 2、遍历列表，调用Camera.caputer()
    for _ in range(1):
        for item in cam_list:
            # 如果截图状态为成功，跳过
            if item['status']:
                break
            my_camera = Camera(item['ip'], item['password'])
            logger.debug(my_camera)
            print(my_camera)
            try:
                result = my_camera.capture()
                # 截图成功
                if result == 1:
                    item['status'] = True
            except Exception as e:
                logger.debug(e)
            finally:
                item['time'] += 1

    # 3、统计截图失败的ip
    # print(cam_list)
    failedIpFileName = os.path.splitext(os.path.basename(csv_file))[0] + '_failed_ip.csv'
    print(failedIpFileName)
    with open(failedIpFileName, 'w', newline="") as fp:
        csv_write = csv.DictWriter(fp, fieldnames=list(cam_list[0].keys()))
        csv_write.writeheader()
        for item in cam_list:
            print(item)
            csv_write.writerow(item)


if __name__ == '__main__':
    capture_from_csv('../txt/ruizhi.csv')
