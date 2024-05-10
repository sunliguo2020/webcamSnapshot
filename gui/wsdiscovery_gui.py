# -*- coding: utf-8 -*-
"""
 @Time : 2024/5/8 21:39
 @Author : sunliguo
 @Email : sunliguo2006@qq.com
"""
import logging
import os
import re
import tkinter as tk
from tkinter import scrolledtext

import netifaces

from CameraDiscovery import ws_discovery

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def get_netmask_through_nicip(nicip):
    """
        Get the netmask through give a ipaddr
        Args:
            nicip: ip addr
        Returns:
            netmask
    """
    netmask = ''
    nicfaces = netifaces.interfaces()

    for faces in nicfaces:
        message = netifaces.ifaddresses(faces)
        iface_addr = message.get(netifaces.AF_INET)
        if iface_addr:
            iface_dict = iface_addr[0]
            ipaddr = iface_dict.get('addr')
            if ipaddr == nicip:
                netmask = iface_dict.get('netmask')
    return netmask


def get_ip():
    ip_addrs = []
    # 返回一个列表，包含了系统上所有网络接口的名称
    # ['{1B3DB804-3D22-4B53-B758-004C996C2CA6}',
    # '{1616801F-2737-443F-905C-E2CB8D2F490D}',
    # '{E1A2F8FD-49E7-4768-AF4C-70B92B571104}',
    # '{5164289D-3514-4633-BA7A-0A491ED7FF6D}',
    # '{3D6A7E8B-F04D-11EC-BADD-806E6F6E6963}']
    nicfaces = netifaces.interfaces()
    logger.debug(f'nicfaces:{nicfaces}')
    for faces in nicfaces:
        # 通过网络接口名称获取网卡信息
        """
        {
            -1000: [{'addr': '00:c2:c6:80:f8:4f'}], 
             2: [{'addr': '192.168.1.157', 'netmask': '255.255.255.0', 'broadcast': '192.168.1.255'}]
        }
        """
        message = netifaces.ifaddresses(faces)
        logger.debug(f"message:{message}")
        # 获取IPv4地址 netifaces.AF_INET =2
        iface_addr = message.get(netifaces.AF_INET)
        logger.debug(f"iface_addr:{iface_addr}")
        if iface_addr:
            iface_dict = iface_addr[0]
            ipaddr = iface_dict.get('addr')
            ip_addrs.append(ipaddr)

    return ip_addrs


def onvif_find(t1: tk.Text):
    """
    查找onvif设备并更新文本框
    @return:
    """
    # http://www.onvif.org/onvif/ver10/network/wsdl/remotediscovery.wsdl

    # from wsdiscovery.threaded import NetworkingThread, MULTICAST_PORT
    from wsdiscovery import WSDiscovery

    clients = []

    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices()

    for service in services:
        get_ip = str(service.getXAddrs())
        get_types = str(service.getTypes())
        clients.append(get_ip)

    wsd.stop()
    clients.sort()
    # 清除文本框的当前内容
    t1.delete('1.0', tk.END)

    # 在文本框中插入搜索到的设备IP
    for client in clients:
        t1.insert(tk.END, client + '\n')


def onvif_discovery(scope, t1: scrolledtext.ScrolledText):
    result = ws_discovery(scope)
    # 清除文本框的当前内容
    t1.delete('1.0', tk.END)

    # 在文本框中插入搜索到的设备IP
    for client in result:
        t1.insert(tk.END, client + '\n')


def get_iface():
    result = os.popen('ipconfig')
    res = result.read()
    logger.debug(res)
    resultlist = re.findall('''(?<=以太网适配器 ).*?(?=:)|(?<=无线局域网适配器 ).*?(?=:)''', res)
    logger.debug(resultlist)
    num = 0
    while True:
        if num >= len(resultlist):
            return resultlist
        elif '本地连接' in resultlist[num]:
            resultlist.remove(resultlist[num])
        else:
            num = num + 1


def show_gui():
    window = tk.Tk()
    window.geometry('600x400')
    window.resizable(False, False)

    window.title('ONVIF设备搜索')

    t1 = scrolledtext.ScrolledText(window, height=20, width=80)
    t1.pack(pady=20)

    ip = tk.StringVar()
    options = get_ip()
    menu = tk.OptionMenu(window, ip, *options)
    menu.pack()

    b1 = tk.Button(window, text='搜索',
                   command=lambda: onvif_discovery(ip.get(), t1)
                   # command=lambda: onvif_find(t1)
                   )  # 将文本框作为参数传递给函数
    b1.pack(pady=10)
    window.mainloop()


if __name__ == '__main__':
    # print(get_ip())

    show_gui()
