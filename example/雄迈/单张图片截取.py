# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 7:55
"""
import concurrent
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

from utils.tool import get_cam_list


def capture(ip=None, folder=None):
    """
    雄迈摄像头抓拍
    @param folder: 截图保存目录
    @param ip:  摄像头ip
    @return:
    """
    if ip is None:
        return
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    if folder is None:
        folder = f'{date_str}'
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_name = f'{ip}_xm_{datetime_str}.jpg'

    file_full_path = os.path.join(folder, file_name)

    url = f'http://{ip}/webcapture.jpg?command=snap&channel=1'
    try:
        response = requests.get(url, timeout=1)
    except ConnectionError as e:
        print(f"{ip}连接失败：{e}")
    except Exception as e:
        print(f'{ip} 打开失败：{e}')
    else:
        if response.status_code == 200:
            with open(file_full_path, 'wb') as f:
                f.write(response.content)
            print(f'{ip} 抓取成功')
        else:
            print(f'{ip} 抓取失败')


if __name__ == '__main__':
    # capture('172.30.189.82')
    for item in get_cam_list('../../txt/世纪东城-雄迈.csv'):
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(capture, item['ip'])
