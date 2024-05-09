# -*- coding: utf-8 -*-
"""
 @Time : 2024/5/8 21:39
 @Author : sunliguo
 @Email : sunliguo2006@qq.com
"""
import tkinter as tk
from tkinter import scrolledtext


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


window = tk.Tk()
window.geometry('600x400')
window.resizable(False, False)

window.title('ONVIF设备搜索')

t1 = scrolledtext.ScrolledText(window, height=20, width=80)
t1.pack(pady=20)

b1 = tk.Button(window, text='搜索', command=lambda: onvif_find(t1))  # 将文本框作为参数传递给函数
b1.pack(pady=10)
window.mainloop()
