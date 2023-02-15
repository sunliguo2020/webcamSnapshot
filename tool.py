# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-02-15 18:13
将通用的函数放在一起。
"""
import os
import socket


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
