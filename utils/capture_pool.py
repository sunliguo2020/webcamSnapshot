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
from utils.log_utils import pause_event
from utils.tool import get_cam_list

logger = logging.getLogger('camera_logger')
DEFAULT_MAX_WORKERS = 8


def batch_capture_computer_cameras(folder_path=None,
                                   is_water_mark=True,
                                   max_index=3):
    """
    电脑所有可用摄像头批量截图
    @param folder_path: 统一保存文件夹路径
    @param is_water_mark: 是否添加水印
    @param max_index: 最大摄像头索引
    @return: dict 键：摄像头索引，值：截图结果（status, file_path/error_msg）
    """
    capture_results = {}
    found_camera = False

    for cam_index in range(max_index):
        cam = Camera(
            camera_type="computer",
            cam_index=cam_index,
            folder_path=folder_path,
            is_water_mark=is_water_mark
        )
        result = cam.capture()
        status, info = result

        if status == 1:
            found_camera = True
            logger.info(f"摄像头{cam_index}截图成功")
            capture_results[cam_index] = result
        else:
            logger.debug(f"摄像头{cam_index}不可用:{info}")

    if not found_camera:
        logger.warning("未检测到可用电脑摄像头")

    return capture_results


def _capture_one(index, camera_info, camera_type, folder_path, is_water_mark):
    """Capture one camera and return a normalized result tuple."""
    pause_event.wait()
    ip = str(camera_info.get('ip', 'unknown'))
    logger.info("开始截图 IP: %s", ip)

    if camera_type == 'onvif':
        port = camera_info.get('port') or camera_info.get('onvif_port') or 80
        client = OnvifClient(
            ip=ip,
            port=int(port),
            username=camera_info.get('username') or 'admin',
            password=camera_info.get('password', ''),
            folder_path=folder_path,
        )
        file_path = client.Snapshot(file_dir=folder_path)
        if file_path:
            return index, ip, 1, file_path
        return index, ip, 0, "ONVIF 快照失败"

    camera = Camera(
        ip=ip,
        username=camera_info.get('username') or 'admin',
        password=camera_info.get('password', ''),
        camera_type=camera_type,
        onvif_port=int(camera_info.get('onvif_port') or camera_info.get('port') or 80),
        folder_path=folder_path,
        is_water_mark=is_water_mark,
    )
    status, result = camera.capture()
    return index, ip, status, result


def _capture_camera_records(
    cameras,
    csv_file,
    camera_type,
    folder_path=None,
    is_water_mark=True,
    max_workers=DEFAULT_MAX_WORKERS,
):
    """Capture parsed camera records with bounded concurrency."""
    statistics = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'failed_ips': [],
        'errors': [],
        'fail_log_file': None,
    }

    statistics['total'] = len(cameras)
    if not cameras:
        statistics['errors'].append("CSV 中没有有效的摄像头记录")
        log_statistics(statistics)
        return [], statistics

    results = [None] * len(cameras)
    worker_count = max(1, min(int(max_workers), len(cameras)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                _capture_one,
                index,
                camera_info,
                camera_type,
                folder_path,
                is_water_mark,
            ): index
            for index, camera_info in enumerate(cameras)
        }

        for future in as_completed(futures):
            index = futures[future]
            camera_info = cameras[index]
            ip = str(camera_info.get('ip', 'unknown'))
            try:
                result_index, ip, status, info = future.result()
            except Exception as error:
                result_index, status, info = index, 0, str(error)
                logger.exception("截图任务异常 IP: %s", ip)

            results[result_index] = (status, info)
            if status == 1:
                statistics['success'] += 1
                logger.info("截图成功 IP: %s", ip)
            else:
                statistics['failed'] += 1
                statistics['failed_ips'].append((ip, info))
                logger.warning("截图失败 IP: %s - %s", ip, info)

    if statistics['failed_ips']:
        try:
            report_dir = folder_path or os.path.join(os.getcwd(), 'fail_logs')
            os.makedirs(report_dir, exist_ok=True)
            csv_name = os.path.splitext(os.path.basename(csv_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            fail_log_file = os.path.join(
                report_dir, f"{csv_name}_failed_{timestamp}.csv"
            )
            with open(fail_log_file, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(['IP地址', '错误信息', '时间'])
                for ip, error in statistics['failed_ips']:
                    writer.writerow([
                        ip,
                        error,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ])
            statistics['fail_log_file'] = fail_log_file
            logger.info("失败IP已保存到文件: %s", fail_log_file)
        except OSError as error:
            logger.exception("保存失败IP记录失败")
            statistics['errors'].append(f"保存失败记录失败: {error}")

    log_statistics(statistics)
    return results, statistics


def _capture_csv_cameras(
    csv_file,
    camera_type,
    folder_path=None,
    is_water_mark=True,
    max_workers=DEFAULT_MAX_WORKERS,
):
    """Read a CSV once and capture its cameras."""
    try:
        if not str(csv_file).lower().endswith('.csv'):
            raise ValueError("请选择 CSV 文件")
        cameras = list(get_cam_list(csv_file))
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        logger.exception("读取摄像头 CSV 失败")
        statistics = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'failed_ips': [],
            'errors': [str(error)],
            'fail_log_file': None,
        }
        log_statistics(statistics)
        return [], statistics

    return _capture_camera_records(
        cameras,
        csv_file,
        camera_type,
        folder_path=folder_path,
        is_water_mark=is_water_mark,
        max_workers=max_workers,
    )


def capture_cameras(
    cameras,
    camera_type,
    csv_file,
    folder_path=None,
    is_water_mark=True,
    max_workers=DEFAULT_MAX_WORKERS,
):
    """Capture already-parsed CSV records using the shared batch pipeline."""
    if camera_type not in {'hik', 'dahua', 'onvif'}:
        raise ValueError(f"不支持的摄像头类型: {camera_type}")
    return _capture_camera_records(
        cameras,
        csv_file,
        camera_type,
        folder_path=folder_path,
        is_water_mark=is_water_mark,
        max_workers=max_workers,
    )


def capture_pool(csv_file, *args, **kwargs):
    """Capture Hikvision or Dahua cameras listed in a CSV file."""
    camera_type = kwargs.pop('camera_type', args[0] if args else 'hik')
    folder_path = kwargs.pop('folder_path', None)
    is_water_mark = kwargs.pop('is_water_mark', True)
    max_workers = kwargs.pop('max_workers', DEFAULT_MAX_WORKERS)
    if camera_type not in {'hik', 'dahua'}:
        raise ValueError(f"不支持的摄像头类型: {camera_type}")
    return _capture_csv_cameras(
        csv_file,
        camera_type,
        folder_path=folder_path,
        is_water_mark=is_water_mark,
        max_workers=max_workers,
    )


def log_statistics(statistics):
    """格式化输出统计信息到日志"""
    logger.info("\n" + "=" * 50 + "\n截图任务统计报告:")
    logger.info(f" 总计摄像头: {statistics['total']}")
    logger.info(f" 成功数量: {statistics['success']}")
    logger.info(f" 失败数量: {statistics['failed']}")

    if statistics['failed_ips']:
        logger.info("\n失败摄像头详情:")
        for idx, (ip, error) in enumerate(statistics['failed_ips'], 1):
            logger.info(f"  {idx}. IP: {str(ip).ljust(15)} 错误: {error}")

    if statistics['errors']:
        logger.info("\n系统错误:")
        for idx, error in enumerate(statistics['errors'], 1):
            logger.info(f"  {idx}. {error}")

    if statistics.get('fail_log_file'):
        logger.info(f"\n失败IP记录文件: {statistics['fail_log_file']}")

    logger.info("=" * 50 + "\n")


def onvif_pool(csv_file, *args, **kwargs):
    """Capture ONVIF cameras using the shared CSV batch pipeline."""
    folder_path = kwargs.pop('folder_path', None)
    max_workers = kwargs.pop('max_workers', DEFAULT_MAX_WORKERS)
    return _capture_csv_cameras(
        csv_file,
        'onvif',
        folder_path=folder_path,
        max_workers=max_workers,
    )


if __name__ == '__main__':
    logger.debug('main')
    # capture_pool(r"../txt/ruizhi.csv", folder_path="2023-11-13")
