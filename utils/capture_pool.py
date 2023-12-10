# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-11-13 20:42
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from Camera import Camera
from utils.tool import convert_ip_list

logger = logging.getLogger('CameraLog')



def capture_pool(csv_file, *args, **kwargs):
    """
    使用线程池截图
    @param csv_file:
    @param args:
    @param kwargs:
    @return:
    """
    # 1、创建参数列表
    cam_list = convert_ip_list(csv_file)
    cam_args = [(item['ip'], item['password']) for item in cam_list]
    # 2、 创建线程池
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(lambda arg: Camera(*arg, *args, **kwargs).capture(),
                           cam_args)
        # 每个ip和结果对应
        results = list(zip(cam_args, results))

        for result in results:
            logger.debug(result)
    # 3、统计结果
    success = 0
    failed = 0
    for _, item in results:
        if item == 1:
            success += 1
        else:
            failed += 1
    logger.debug(f"统计：成功{success}失败{failed}")


if __name__ == '__main__':
    logger.debug('main')
    capture_pool(r"../txt/ruizhi.csv", folder_path="2023-11-13")
