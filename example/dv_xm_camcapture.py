# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2025/12/29 15:38
"""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import requests
from utils.tool import get_cam_list


def cam_capture(ip=None, folder=None, cam_type=None):
    """
    通用摄像头抓拍函数（支持dv/雄迈xm摄像头）
    @param ip: 摄像头ip
    @param folder: 截图保存目录
    @param cam_type: 摄像头类型（必须是'dv'或'xm'）
    @return:
    """
    # 合法性校验
    if ip is None or cam_type not in ('dv', 'xm'):
        print(f"IP为空或摄像头类型不支持，跳过抓拍")
        return

    # 1. 公共逻辑：生成时间字符串和保存目录
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 确定保存文件夹
    if folder is None:
        folder = f'{date_str}'
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)  # exist_ok=True 避免多线程创建目录冲突

    # 2. 参数化差异项：根据摄像头类型生成文件名和截图URL
    if cam_type == 'dv':
        file_suffix = 'dv'
        url = f'http://{ip}/cgi-bin/snapshot.cgi?stream=0'
    else:  # 'xm'
        file_suffix = 'xm'
        url = f'http://{ip}/webcapture.jpg?command=snap&channel=1'

    # 生成完整文件名和路径
    file_name = f'{ip}_{file_suffix}_{datetime_str}.jpg'
    file_full_path = os.path.join(folder, file_name)

    # 3. 公共逻辑：发送请求并保存截图
    try:
        response = requests.get(url, timeout=1)
        response.raise_for_status()  # 主动抛出HTTP错误状态码异常
    except requests.exceptions.ConnectionError as e:
        print(f"{ip}（{cam_type}）连接失败：{e}")
    except requests.exceptions.RequestException as e:
        print(f'{ip}（{cam_type}）抓取异常：{e}')
    else:
        # 保存截图文件
        with open(file_full_path, 'wb') as f:
            f.write(response.content)
        print(f'{ip}（{cam_type}）抓取成功，文件保存至：{file_full_path}')


def batch_capture(csv_file, cam_type, max_workers=5, folder=None):
    """
    批量抓拍指定类型的摄像头
    @param csv_file: 摄像头IP列表CSV文件路径
    @param cam_type: 摄像头类型（'dv'或'xm'）
    @param max_workers: 最大线程数
    @param folder: 统一保存目录
    @return:
    """
    # 获取摄像头IP列表
    cam_list = get_cam_list(csv_file)
    if not cam_list:
        print(f"CSV文件{csv_file}中未读取到摄像头信息")
        return

    # 批量提交任务（仅创建1次线程池，优化原代码冗余问题）
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for item in cam_list:
            ip = item.get('ip')  # 避免键不存在报错
            if ip:
                executor.submit(cam_capture, ip, folder, cam_type)
            else:
                print(f"无效的摄像头信息：{item}，缺少IP字段")


if __name__ == '__main__':
    # --------------------------
    # 按需调用：dv摄像头批量抓拍
    # --------------------------
    dv_csv_file = r'D:\github\webcamSnapshot\txt\dv.csv'
    # batch_capture(dv_csv_file, cam_type='dv', max_workers=5)

    # --------------------------
    # 按需调用：雄迈xm摄像头批量抓拍
    # --------------------------
    xm_csv_file = r'D:\github\webcamSnapshot\txt\世纪东城-雄迈.csv'
    batch_capture(xm_csv_file, cam_type='xm', max_workers=5)
