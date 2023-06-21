# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-02-15 18:13
将通用的函数放在一起。
"""
import csv
import logging
import os
import socket

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def portisopen(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    state = sock.connect_ex((ip, port))
    if 0 == state:
        # print("port is open")
        return True
    else:
        # print("port is closed")
        return False


def is_reachable(ip):
    response = os.system('ping -c 1' + ip)
    if response == 0:
        print(ip + 'is reachable')
        return 1
    else:
        print(ip + 'is not reachable')
        return 0


def is_ipv4(ip: str) -> bool:
    """
    检查ip是否合法
    :param: ip ip地址
    :return: True 合法 False 不合法
    """
    return True if [1] * 4 == [x.isdigit() and 0 <= int(x) <= 255 for x in ip.split(".")] else False


def gen_ip_password_from_csv(file_path, line_count=0):
    """
    读取csv文件，返回ip，password
    :param file_path: 要读取的csv文件
    :param line_count: 跳过前几行
    :return: ip,password
    """
    # 判断是否是csv文件
    with open(file_path, encoding='utf-8') as f:
        # 跳过前几行
        for i in range(line_count):
            next(f)  # 跳过一行

        try:
            csv_read = csv.reader(f)
            for row in csv_read:
                # 读取每行的前两列
                cam_ip = row[0].strip()
                cam_pwd = row[1].strip()
                yield cam_ip, cam_pwd
        except UnicodeDecodeError as e:
            logger.error(e)
            return -1
        except Exception as e:
            logger.debug(e)
            return -1
