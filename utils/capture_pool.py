# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-11-13 20:42
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from lib.Camera import Camera
from utils.tool import convert_ip_list

logger = logging.getLogger('camera_log')


def capture_pool(csv_file, *args, **kwargs):
    """
    使用线程池截图
    @param csv_file:
    @param args:
    @param kwargs:
    @return:
    """
    # 1、创建参数列表
    # 返回值为包含ip,password等的字典列表
    cam_list = convert_ip_list(csv_file)
    cam_args = [(item['ip'], item['password']) for item in cam_list]
    # 2、 创建线程池
    with ThreadPoolExecutor() as pool:
        # results 是返回的结果列表
        results = pool.map(lambda arg: Camera(*arg, *args, **kwargs).capture(),
                           cam_args, timeout=20)
    # 每个ip和结果对应
    # (('172.24.99.101', 'admin'), (-1, None))
    last_results = list(zip(cam_args, results))
    # [(('192.168.1.101', 'admi12345'), (-1, None)), (('192.168.1.103', 'admi12345'), (-1, None)), (('192.168.1.105', 'OIBLDQ'), (-1, None)), (('192.168.1.107', 'admi12345'), (-1, None)), (('192.168.1.109', 'admin123'), (-1, None)), (('192.168.1.111', 'FYKWXY'), (-1, None)), (('192.168.1.113', 'admi12345'), (-1, None))]
    # logger.debug(last_results)

    for result in last_results:
        logger.debug(f"截图结果:{result}")
    # 3、统计结果
    success = 0
    failed = 0
    for item in last_results:
        # logger.debug(item)
        if item[1][0] == 1:
            success += 1
        else:
            failed += 1
    logger.debug(f"统计：成功{success}失败{failed}")


if __name__ == '__main__':
    logger.debug('main')
    capture_pool(r"../txt/ruizhi.csv", folder_path="2023-11-13")
