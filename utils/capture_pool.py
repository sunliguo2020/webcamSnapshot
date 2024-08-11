# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-11-13 20:42
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from lib.Camera import Camera
from lib.OnvifClient import OnvifClient
from utils.tool import get_cam_list

logger = logging.getLogger('camera_logger')


def capture_pool(csv_file, *args, **kwargs):
    """
    使用线程池截图,摄像头类型 和 保存路径
    @param csv_file:保存ip,port,user,password的csv文件
    @param args:
    @param kwargs:
    @return:
    """
    # 1、包含ip,password等的字典的生成式
    cam_list = get_cam_list(csv_file)

    # 2、 创建线程池
    try:
        with ThreadPoolExecutor() as pool:
            # results 是返回的结果列表
            results = pool.map(lambda caminfo: Camera(**caminfo, **kwargs).capture(), cam_list)
    except Exception as e:
        logger.error(f"在线程池执行中发生错误：{e}")

    # 每个ip和结果对应
    # (('172.24.99.101', 'admin'), (-1, None))
    list_results = list(results)
    logger.debug(f"list_results:{list_results}")
    # last_results = list(zip(cam_list, list_results))
    last_results = list_results
    logger.debug(f"last_results:{last_results}")

    # for result in last_results:
    #     logger.debug(f"截图结果:{result}")
    # 截图结果:(1, '2024-08-11\\192.168.1.50_shiji123_hik_20240811124515.jpg')

    # 3、统计结果
    success = 0
    failed = 0
    for item in last_results:
        logger.debug(f"item:{item}")
        if item[0] == 1:
            logger.debug(f"截图成功:{item}")
            success += 1
        else:
            logger.debug(f"摄像头{item[0]}截图失败:{item[1][1]}")
            failed += 1
    logger.debug(f"统计：成功{success}失败{failed}")


def onvif_pool(csv_file, *arg, **kwargs):
    """
    使用线程池onvif截图
    @param csv_file: ip,password的csv文件
    @param arg:
    @param kwargs:
    @return:
    """
    cam_list = get_cam_list(csv_file)
    logger.debug(f"csv文件：{cam_list}")
    try:
        futures_list = []
        with ThreadPoolExecutor() as pool:
            # results 是返回的结果列表
            # results = pool.map(lambda inkwargs: OnvifClient(**inkwargs, **kwargs).Snapshot(), cam_list)
            # futures_list = [pool.submit(lambda inkwargs: OnvifClient(**inkwargs, **kwargs).Snapshot()) for inkwargs in
            #                 cam_list]
            for item in cam_list:
                future = pool.submit(lambda inkwargs: OnvifClient(**inkwargs, **kwargs).Snapshot(), item)
                futures_list.append(future)
    except Exception as e:
        logger.error(f"在线程池执行中发生错误：{e}")

    pool.shutdown()
    success = 0
    for future in futures_list:
        logger.debug(future.result())
        if future.result():
            success += 1
    logger.debug(f"统计：成功{success}失败{len(futures_list) - success}")


if __name__ == '__main__':
    logger.debug('main')
    # capture_pool(r"../txt/ruizhi.csv", folder_path="2023-11-13")
    onvif_pool('../txt/test.csv')
