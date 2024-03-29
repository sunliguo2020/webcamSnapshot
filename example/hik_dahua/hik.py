# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/2/7 13:52
"""

import csv
from concurrent.futures import ThreadPoolExecutor

from hik_cv2 import hik_cv2


def csv2jpg(file_path, password='admin', count=0):
    """
    :param file_path: 包含ip和 密码 的 csv文件
    :param count: 从第几行开始抓取
    :param password:
    :return: 
    """
    incount = 0
    with open(file_path) as fp:
        reader = csv.reader(fp)
        with ThreadPoolExecutor(10) as t:
            for i in reader:
                incount += 1
                # 跳过前几行
                if incount < count:
                    continue
                # 如果只有ip这1列
                if len(i) == 1:
                    ip = i[0]
                    passwd = password
                elif len(i) >= 2:
                    ip = i[0]
                    passwd = i[1]
                print(incount, ":", ip, passwd)
                # hik_cv2(ip, passwd)
                t.submit(hik_cv2, ip, passwd)


if __name__ == '__main__':
    csv2jpg('./shijidongcheng-hik.csv', count=0)
