# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 7:55
"""
import os
from datetime import datetime

import requests


def capture(ip, folder=None):
    """

    @param folder:
    @param ip:
    @return:
    """
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    if folder is None:
        folder = f'{date_str}'
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_name = f'{ip}_xm_{datetime_str}.jpg'

    file_full_path = os.path.join(folder, file_name)
    url = f'http://{ip}/webcapture.jpg?command=snap&channel=1'
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        with open(file_full_path, 'wb') as f:
            f.write(response.content)
        print(f'{ip} 抓取成功')
    else:
        print(f'{ip} 抓取失败')


if __name__ == '__main__':
    capture('172.30.189.82')
