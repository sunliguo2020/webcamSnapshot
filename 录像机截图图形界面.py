# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-07-03 20:34
"""
import logging
import os.path
import threading
from tkinter import *
from tkinter import ttk, filedialog, scrolledtext

from cv2Snapshot import cams_capture
from cv2Snapshot import cams_channel_capture
from tool import is_ipv4


class WidgetLogger(logging.Handler):
    # The init function needs the widget which will hold the log messages passed to it as
    # well as other basic information (log level, format, etc.)

    def __init__(self, widget, logLevel, format):
        logging.Handler.__init__(self)

        # Basic logging configuration
        self.setLevel(logLevel)
        self.setFormatter(logging.Formatter(format))
        self.widget = widget

        # The ScrolledText box must be disabled so users can't enter their own text
        self.widget.config(state='disabled')

    # This function is called when a log message is to be handled
    def emit(self, record):
        # Enable the widget to allow new text to be inserted
        self.widget.config(state='normal')

        # Append log message to the widget
        # self.widget.insert('insert', str(self.format(record) + '\n'))

        msg = self.format(record)
        self.widget.insert("end", msg + "\n")

        # Scroll down to the bottom of the ScrolledText box to ensure the latest log message
        # is visible
        self.widget.see("end")

        # Re-disable the widget to prevent users from entering text
        self.widget.config(state='disabled')


class Application(Frame):
    def __init__(self, master=None):
        super().__init__()
        self.master = master
        self.pack()
        self.ip = StringVar()
        self.password = StringVar()
        self.number = StringVar()
        self.select_dir = StringVar()
        self.endChannel = IntVar()
        self.create_widget()

    def create_widget(self):

        self.ip_label = Label(self, text='IP地址:', font='微软雅黑 12')
        self.ip_label.grid(column=0, row=0, sticky=W, padx=20)

        self.ip_entry = Entry(self, textvariable=self.ip)
        self.ip_entry.grid(column=1, row=0, sticky=W)

        self.password_label = Label(self, text='密码:', font='微软雅黑 12')
        self.password_label.grid(column=0, row=1, sticky=W, padx=20)

        self.password_entry = Entry(self, textvariable=self.password)
        self.password_entry.grid(column=1, row=1, sticky=W)

        # 录像机截至通道号
        # 创建一个下拉列表
        Label(self, text='截至通道号:', font='微软雅黑 12').grid(column=0, row=2, sticky=W, padx=20)

        self.endchanelChosen = ttk.Combobox(self, state='readonly', width=3, height=12, textvariable=self.endChannel)
        self.endchanelChosen['values'] = [i for i in range(1, 65)]  # 设置下拉列表的值
        self.endchanelChosen.grid(column=1, row=2, sticky=W)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.endchanelChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

        # 创建一个下拉列表
        Label(self, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=3, sticky=W, padx=20)

        self.numberChosen = ttk.Combobox(self, state='readonly', width=12, height=12, textvariable=self.number)
        self.numberChosen['values'] = ('海康', '大华')  # 设置下拉列表的值
        self.numberChosen.grid(column=1, row=3, sticky=W)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

        # 截图保存目录
        self.cap_dir_label = Label(self, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 10')
        self.cap_dir_label.grid(row=4, column=0, sticky=W, padx=20)

        self.dir_entry = Entry(self, textvariable=self.select_dir)
        self.dir_entry.grid(column=1, row=4, sticky=W)
        # 截图保存路径浏览按钮
        Button(self, text="浏览", command=self.select_folder).grid(row=4, column=3, sticky=W)

        # 采集按钮
        self.capture_button = Button(self, text='开始截图', font='宋体 12', bg='lightblue', width=20,
                                     command=lambda: threading.Thread(target=self.start_cap).start())
        self.capture_button.grid(row=8, columnspan=4, padx=10, pady=10)

        # 日志框
        self.logWidget = scrolledtext.ScrolledText(self, width=66, height=20)
        self.logWidget.grid(row=10, column=0, columnspan=10, rowspan=4, padx=(10, 10), pady=(10, 10))

        logFormatStr = '%(asctime)s - %(threadName)s - %(funcName)s  - %(levelname)-8s %(message)s'
        guiLogger = WidgetLogger(self.logWidget, logging.DEBUG, format=logFormatStr)
        logging.getLogger().addHandler(guiLogger)

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

        logging.info(f'摄像头类型：{client_type}')
        logging.info(f'截图保存路径：{save_dir}')

        if client_type == '海康':
            cams_channel_capture(ip, password, end_channel_no=self.endChannel.get(), cam_client='hik',
                                 save_dir=save_dir)
        elif client_type == '大华':
            cams_capture(ip, password, client='dahua', save_dir=save_dir)


if __name__ == '__main__':
    root = Tk()
    root.geometry('500x600+300+200')
    root.title('录像机截图采集小工具')

    app = Application(master=root)

    root.mainloop()
