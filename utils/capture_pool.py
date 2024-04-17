# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-11-13 20:42
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from lib.Camera import Camera
from utils.tool import get_cam_list

logger = logging.getLogger('camera_logger')


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
    cam_list = get_cam_list(csv_file)
    logger.debug(cam_list)
    # 2、 创建线程池
    try:
        with ThreadPoolExecutor() as pool:
            # results 是返回的结果列表
            results = pool.map(lambda inkwargs: Camera(**inkwargs, **kwargs).capture(), cam_list)
    except Exception as e:
        logger.error(f"在线程池执行中发生错误：{e}")

    # 每个ip和结果对应
    # (('172.24.99.101', 'admin'), (-1, None))
    last_results = list(zip(cam_list, results))
    logger.debug(f"last_results:{last_results}")

    for result in last_results:
        logger.debug(f"截图结果:{result}")
    # 3、统计结果
    success = 0
    failed = 0
    for item in last_results:
        # logger.debug(item)
        if item[1][0] == 1:
            logger.debug(f"截图成功:{item}")
            success += 1
        else:
            logger.debug(f"摄像头{item[0]}截图失败:{item[1][1]}")
            failed += 1
    logger.debug(f"统计：成功{success}失败{failed}")


if __name__ == '__main__':
    logger.debug('main')
    capture_pool(r"../txt/ruizhi.csv", folder_path="2023-11-13")
