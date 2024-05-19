# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-05-15 18:09
"""
import tkinter as tk
from tkinter import messagebox


def check_ip():
    ip_parts = [entry.get() for entry in entries]
    if all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
        messagebox.showinfo("IP Address", "IP Address is valid: {}".format(".".join(ip_parts)))
    else:
        messagebox.showerror("IP Address", "Invalid IP Address")


root = tk.Tk()
root.geometry('500x600+300+200')
root.title("Enter IP Address")

# 创建四个 Entry 控件来输入 IP 地址的四个部分
entries = [tk.Entry(root, width=5) for _ in range(4)]
for i, entry in enumerate(entries):
    entry.grid(row=0, column=i, padx=5)

# 创建一个检查 IP 地址的按钮
check_button = tk.Button(root, text="Check IP", command=check_ip)
check_button.grid(row=1, column=0, columnspan=4, pady=10)

root.mainloop()