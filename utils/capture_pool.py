# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-11-13 20:42
"""
import csv
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from lib.Camera import Camera
from lib.OnvifClient import OnvifClient
from utils.tool import get_cam_list

logger = logging.getLogger('camera_logger')


def capture_pool(csv_file, *args, **kwargs):
    """
    使用线程池截图,摄像头类型 和 保存路径
    @param csv_file:保存ip,port,user,password的csv文件
    @param args: 额外位置参数
    @param kwargs: 额外关键字参数
    @return: tuple(结果列表，统计字典)
    """
    # 准备失败IP保存路径
    fail_log_dir = "fail_logs"
    os.makedirs(fail_log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fail_log_file = os.path.join(fail_log_dir, f"failed_ips_{timestamp}.csv")

    # 1、获取摄像头列表
    try:
        cam_list = list(get_cam_list(csv_file))  # 转换为列表以便复用
    except Exception as e:
        logger.error(f"读取CSV文件失败: {e}", exc_info=True)
        error_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'failed_ips': [],
            'errors': [str(e)],
            'fail_log_file': None
        }
        return [], error_stats

    last_results = []
    statistics = {
        'total': len(cam_list),
        'success': 0,
        'failed': 0,
        'failed_ips': [],  # 存储失败的IP和错误信息
        'errors': [],  # 存储其他错误
        'fail_log_file': fail_log_file  # 失败IP记录文件路径
    }

    # 2、创建线程池
    try:
        with ThreadPoolExecutor() as pool:
            futures = []
            for caminfo in cam_list:
                try:
                    # 为每个任务创建可追踪的上下文
                    task_info = {
                        'ip': caminfo.get('ip', 'unknown'),
                        'kwargs': kwargs,
                        'caminfo': caminfo
                    }
                    future = pool.submit(
                        lambda x: Camera(**x['caminfo'], **x['kwargs']).capture(),
                        task_info
                    )
                    future.task_info = task_info  # 附加任务信息
                    futures.append(future)
                except Exception as e:
                    statistics['failed'] += 1
                    ip = caminfo.get('ip', 'unknown')
                    error_msg = str(e)
                    statistics['failed_ips'].append((ip, error_msg))
                    logger.error(f"任务提交失败 IP: {ip} - {error_msg}")

            # 处理结果
            for future in as_completed(futures):
                try:
                    result = future.result()
                    last_results.append(result)

                    ip = future.task_info['ip']
                    if result[0] == 1:  # 假设result[0]为1表示成功
                        statistics['success'] += 1
                        logger.info(f"截图成功 IP: {ip}")
                    else:
                        statistics['failed'] += 1
                        error_msg = result[1] if len(result) > 1 else 'unknown error'
                        statistics['failed_ips'].append((ip, error_msg))
                        logger.warning(f"截图失败 IP: {ip} - {error_msg}")

                except Exception as e:
                    statistics['failed'] += 1
                    ip = getattr(future, 'task_info', {}).get('ip', 'unknown')
                    error_msg = str(e)
                    statistics['failed_ips'].append((ip, error_msg))
                    logger.error(f"处理异常 IP: {ip} - {error_msg}", exc_info=True)

    except Exception as e:
        logger.error(f"线程池运行异常: {e}", exc_info=True)
        statistics['errors'].append(str(e))

    # 保存失败IP到文件
    if statistics['failed_ips']:
        try:
            with open(fail_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['IP地址', '错误信息', '时间'])
                for ip, error in statistics['failed_ips']:
                    writer.writerow([ip, error, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            logger.info(f"失败IP已保存到文件: {fail_log_file}")
        except Exception as e:
            logger.error(f"保存失败IP记录失败: {e}", exc_info=True)
            statistics['errors'].append(f"保存失败记录失败: {e}")

    # 生成详细统计报告
    log_statistics(statistics)

    return last_results, statistics


def log_statistics(statistics):
    """格式化输出统计信息到日志"""
    logger.info("\n" + "=" * 50 + "\n截图任务统计报告:")
    logger.info(f" 总计摄像头: {statistics['total']}")
    logger.info(f" 成功数量: {statistics['success']}")
    logger.info(f" 失败数量: {statistics['failed']}")

    if statistics['failed_ips']:
        logger.info("\n失败摄像头详情:")
        for idx, (ip, error) in enumerate(statistics['failed_ips'], 1):
            logger.info(f"  {idx}. IP: {ip.ljust(15)} 错误: {error}")

    if statistics['errors']:
        logger.info("\n系统错误:")
        for idx, error in enumerate(statistics['errors'], 1):
            logger.info(f"  {idx}. {error}")

    if statistics.get('fail_log_file'):
        logger.info(f"\n失败IP记录文件: {statistics['fail_log_file']}")

    logger.info("=" * 50 + "\n")


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
    onvif_pool('../dist/世纪凤华.csv')
