# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-05-18 13:23
"""
import tkinter as tk

from lib.OnvifClient import OnvifClient

window = tk.Tk()
window.title('通过onvif查询rtsp地址')
window.geometry('400x300')

var_ip = tk.StringVar()
var_password = tk.StringVar()

label_ip = tk.Label(window, text='IP地址:')
label_ip.grid(row=0, column=0)

label_password = tk.Label(window, text='密码:')
label_password.grid(row=1, column=0)

entry_ip = tk.Entry(window, show=None, bd=2, textvariable=var_ip)
entry_password = tk.Entry(window, show='*', bd=2, textvariable=var_password)
entry_ip.grid(row=0, column=1)
entry_password.grid(row=1, column=1)


def onvif_query(param, param1):
    text_widget.delete('0.0', tk.END)
    text_widget.insert('0.0', f'IP地址: {param}\n密码: {param1}\n')

    onvif_client = OnvifClient(ip=param, password=param1)
    onvif_client.connect()
    rtsp_url = onvif_client.GetStreamUri()
    for url in rtsp_url:
        text_widget.insert(tk.END, f'rtsp地址: {url}\n')


btn = tk.Button(window, text='查询', command=lambda: onvif_query(var_ip.get(), var_password.get()))
btn.grid(row=2, column=0)

text_widget = tk.Text(window, height=10, width=50)
text_widget.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

window.mainloop()
