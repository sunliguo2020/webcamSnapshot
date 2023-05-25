# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面
pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图

"""
import logging
import os.path
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext

from cv2Snapshot import cams_capture


def select_file():
    # 单个文件选择
    selected_file_path = filedialog.askopenfilename()  # 使用askopenfilename函数选择单个文件
    select_path.set(selected_file_path)


def select_files():
    # 多个文件选择
    selected_files_path = filedialog.askopenfilenames()  # askopenfilenames函数选择多个文件
    select_path.set('\n'.join(selected_files_path))  # 多个文件的路径用换行符隔开


def select_folder():
    # 文件夹选择
    selected_folder = filedialog.askdirectory()  # 使用askdirectory函数选择文件夹
    select_dir.set(selected_folder)


def start_cap():
    """
    开始采集的按钮绑定的程序
    :return:
    """
    # 清空日志区
    # log_data_text.delete(0.0, 'end')
    # csv 文件的路径
    csv_file = csv_entry.get()
    # 摄像头类型
    client_type = numberChosen.get()

    # 截图保存路径
    save_dir = dir_entry.get()

    if not os.path.isfile(csv_file):
        logging.error(f'请重新选择包含ip,password的文件!')
        raise ValueError('请重新选择包含ip,password的文件!')

    logging.info(f'摄像头类型：{client_type}')
    logging.info(f'截图保存路径：{save_dir}')

    if client_type == '海康':
        cams_capture(csv_file, client='hik', save_dir=save_dir)
    elif client_type == '大华':
        cams_capture(csv_file, client='dahua', save_dir=save_dir)


class LoggerBox(scrolledtext.ScrolledText):
    """
    思路一：以tk.Text为父类创建一个新的类，增加相关的功能以适配 StreamHandler。
    在创建StreamHandler时作为参数传入。
    实现：参考sys.stdout，因为StreamHandler(stream) 常规用法是把sys.stdout作为参数传进去的，
    查看StreamHandler源码见到其实就是在里面调用了sys.stdout的write()方法，即相当于print()。
    给新的类添加write()方法就可以了

    """

    def write(self, message):
        self.insert("end", message)


root = tk.Tk()
root.title('摄像头截图采集小工具')

root.geometry('500x400+300+200')  # 定义窗口显示大小和显示位置

# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()
select_dir = tk.StringVar()

# 布局空间
csv_file_label = tk.Label(root, text='文件路径:', font='微软雅黑 12')
csv_file_label.grid(column=0, row=0, padx=(10, 0), sticky='w')

csv_entry = tk.Entry(root, textvariable=select_path)
csv_entry.grid(column=1, row=0)

tk.Button(root, text="浏览", command=select_file).grid(row=0, column=3)
# tk.Button(root, text="选择多个文件", command=select_files).grid(row=1, column=2)
# tk.Button(root, text="选择文件夹", command=select_folder).grid(row=2, column=2)

# 创建一个下拉列表
tk.Label(root, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=1)
number = tk.StringVar()
numberChosen = ttk.Combobox(root, state='readonly', width=12, height=12, textvariable=number)
numberChosen['values'] = ('海康', '大华')  # 设置下拉列表的值
numberChosen.grid(column=1, row=1, sticky='w')  # 设置其在界面中出现的位置  column代表列   row 代表行
numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

# 截图保存目录
cap_dir_label = tk.Label(root, text='截图保存位置:', font='微软雅黑 12')
cap_dir_label.grid(row=2, column=0, sticky='w', padx=(10, 0))

dir_entry = tk.Entry(root, textvariable=select_dir)
dir_entry.grid(column=1, row=2, sticky='e')
tk.Button(root, text="浏览", command=select_folder).grid(row=2, column=3)

# 采集按钮
capture_button = tk.Button(root, text='开始采集', bg='lightblue', width=10, command=start_cap)
capture_button.grid(row=8, column=3)


# 日志框

# log_data_text = LoggerBox(root, width=66, height=20)
# log_data_text.grid(row=10, column=0, columnspan=10, rowspan=4, padx=(10, 10), pady=(10, 10))
#
# log1 = logging.getLogger()
# log1.setLevel(logging.DEBUG)
# handler = logging.StreamHandler(log_data_text)
# formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d]-%(levelname)s:%(message)s')
# handler.setFormatter(formatter)
# log1.addHandler(handler)


# 从网上搜到的代码
# 思路二：构造一个新的Handler类，可以支持直接把tk.Text控件作为参数传入。
#
# 查了一下，发现各种handler最核心就是里面的 def emit(self, record) 这个函数，它确定了在哪里输出。重写emit函数即可。
# Define a new logging handler class which inherits the logging.Handler class

class widgetLogger(logging.Handler):
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
        self.widget.insert('insert', str(self.format(record) + '\n'))

        # Scroll down to the bottom of the ScrolledText box to ensure the latest log message
        # is visible
        self.widget.see("end")

        # Re-disable the widget to prevent users from entering text
        self.widget.config(state='disabled')


logWidget = scrolledtext.ScrolledText(root, width=66, height=20)
logWidget.grid(row=10, column=0, columnspan=10, rowspan=4, padx=(10, 10), pady=(10, 10))

logFormatStr = '%(asctime)s - %(threadName)s - %(funcName)s  - %(levelname)-8s %(message)s'
guiLogger = widgetLogger(logWidget, logging.DEBUG, format=logFormatStr)
logging.getLogger().addHandler(guiLogger)

root.mainloop()
