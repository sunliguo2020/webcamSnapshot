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
import time

from lib.Camera import Camera
from utils.tool import convert_ip_list

logger = logging.getLogger('Camera')


def capture_from_csv(csv_file, *args, **kwargs):
    """

    @type csv_file: object
    @param csv_file:
    @return:
    """
    # 1、分析csv文件,得到保存ip地址，密码，和次数的列表
    cam_list = convert_ip_list(csv_file)
    # 2、遍历列表，调用Camera.caputer()
    for _ in range(1):
        for item in cam_list:
            # 如果截图状态为成功，跳过
            if item['status']:
                break
            my_camera = Camera(item['ip'], item['password'], *args, **kwargs)
            logger.debug(my_camera)
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
    failedIpFileName = os.path.splitext(os.path.basename(csv_file))[0] + \
                       '_failed_ip_' + time.strftime("%Y%m%d_%H%M%S", time.localtime()) + \
                       '.csv'
    with open(failedIpFileName, 'w', newline="") as fp:
        csv_write = csv.DictWriter(fp, fieldnames=list(cam_list[0].keys()))
        csv_write.writeheader()
        for item in cam_list:
            logger.debug(item)
            csv_write.writerow(item)
    # 4、总结输出
    success_total = 0
    failed_total = 0
    for item in cam_list:
        if item['status']:
            success_total += 1
        else:
            failed_total += 1
    logger.info(f'本次共成功截图{success_total}个，失败{failed_total}个')


if __name__ == '__main__':
    capture_from_csv('../txt/ruizhi.csv')
