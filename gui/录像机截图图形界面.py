# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-07-03 20:34
"""
import logging
import os.path
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

from cv2Snapshot import cams_capture
from cv2Snapshot import cams_channel_capture
from utils.guis import WidgetLogger
from utils.tool import is_ipv4

logger = logging.getLogger('NVR')


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__()
        self.master = master
        self.pack()
        self.ip = tk.StringVar()
        self.password = tk.StringVar()
        self.number = tk.StringVar()
        self.select_dir = tk.StringVar()
        self.endChannel = tk.IntVar()
        self.create_widget()

    def create_widget(self):
        """
        创建界面
        @return:
        """

        self.ip_label = tk.Label(self, text='IP地址:', font='微软雅黑 12')
        self.ip_label.grid(column=0, row=0, sticky=tk.W, padx=20)

        self.ip_entry = tk.Entry(self, textvariable=self.ip)
        self.ip_entry.grid(column=1, row=0, sticky=tk.W)

        self.password_label = tk.Label(self, text='密码:', font='微软雅黑 12')
        self.password_label.grid(column=0, row=1, sticky=tk.W, padx=20)

        self.password_entry = tk.Entry(self, show='*', textvariable=self.password)
        self.password_entry.grid(column=1, row=1, sticky=tk.W)

        # 录像机截至通道号
        # 创建一个下拉列表
        tk.Label(self, text='截至通道号:', font='微软雅黑 12').grid(column=0, row=2, sticky=tk.W, padx=20)

        self.endchanelChosen = ttk.Combobox(self, state='readonly', width=3, height=12, textvariable=self.endChannel)
        self.endchanelChosen['values'] = [i for i in range(1, 65)]  # 设置下拉列表的值
        self.endchanelChosen.grid(column=1, row=2, sticky=tk.W)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.endchanelChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

        # 创建一个下拉列表
        tk.Label(self, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=3, sticky=tk.W, padx=20)

        self.numberChosen = ttk.Combobox(self, state='readonly', width=12, height=12, textvariable=self.number)
        self.numberChosen['values'] = ('海康', '大华')  # 设置下拉列表的值
        self.numberChosen.grid(column=1, row=3, sticky=tk.W)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

        # 截图保存目录
        self.cap_dir_label = tk.Label(self, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 10')
        self.cap_dir_label.grid(row=4, column=0, sticky=tk.W, padx=20)

        self.dir_entry = tk.Entry(self, textvariable=self.select_dir)
        self.dir_entry.grid(column=1, row=4, sticky=tk.W)
        # 截图保存路径浏览按钮
        tk.Button(self, text="浏览", command=self.select_folder).grid(row=4, column=3, sticky=tk.W)

        # 采集按钮
        self.capture_button = tk.Button(self, text='开始截图', font='宋体 12', bg='lightblue', width=20,
                                        command=lambda: threading.Thread(target=self.start_cap).start())
        self.capture_button.grid(row=8, columnspan=4, padx=10, pady=10)

        # 日志框
        self.logWidget = scrolledtext.ScrolledText(self, width=66, height=25)
        self.logWidget.grid(row=10, column=0, columnspan=10, rowspan=4, padx=(10, 10), pady=(10, 10))

        logFormatStr = '%(asctime)s - %(threadName)s - %(funcName)s  - %(levelname)-8s %(message)s'
        guiLogger = WidgetLogger(self.logWidget, logging.DEBUG, format=logFormatStr)
        logger.addHandler(guiLogger)

    def select_folder(self):
        # 文件夹选择
        selected_folder = filedialog.askdirectory()  # 使用askdirectory函数选择文件夹
        self.select_dir.set(selected_folder)

    def start_cap(self):
        """
        开始采集的按钮绑定的程序
        :return:
        """
        # 清空日志区
        # log_data_text.delete(0.0, 'end')
        # 录像机IP地址
        ip = self.ip.get()
        # 检查ip password 的合法性
        if not is_ipv4(ip) or ip == '':
            logging.critical(f"ip:{ip}的格式不正确，请重新输入！")
            return -1

        # 录像机密码
        password = self.password.get()
        # 摄像头类型
        client_type = self.numberChosen.get()

        # 截图保存路径
        save_dir = self.dir_entry.get()

        # 截图路径为空，则直接保存到程序运行的目录,以当前ip为目录
        if save_dir == "":
            save_dir = os.path.split(os.path.realpath(__file__))[0]
            save_dir = os.path.join(save_dir, ip)

        logger.info(f'摄像头类型w：{client_type}')
        logger.info(f'截图保存路径w：{save_dir}')

        if client_type == '海康':
            cams_channel_capture(ip, password, end_channel_no=self.endChannel.get(), cam_client='hik',
                                 save_dir=save_dir)
        elif client_type == '大华':
            cams_capture(ip, password, client='dahua', save_dir=save_dir)


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('500x600+300+200')
    root.title('录像机截图采集小工具')

    app = Application(master=root)

    root.mainloop()
