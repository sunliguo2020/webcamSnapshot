# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面
pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图

"""
import datetime
import logging
import os.path
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, scrolledtext
from tkinter import ttk, N, S, E, W
from tkinter.scrolledtext import ScrolledText


logger = logging.getLogger()
logger.setLevel(level=logging.DEBUG)


class QueueHandler(logging.Handler):
    """
    Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class LogWidget:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=20)
        self.scrolled_text.grid(row=10, column=0, sticky=(N, S, W, E))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        # formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d]-%(levelname)s:%(message)s')
        formatter = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)

        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


class Clock(threading.Thread):
    """Class to display the time every seconds

    Every 5 seconds, the time is displayed using the logging.ERROR level
    to show that different colors are associated to the log levels
    """

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        logger.debug('Clock started')
        previous = -1
        while not self._stop_event.is_set():
            now = datetime.datetime.now()
        while not self._stop_event.is_set():
            now = datetime.datetime.now()
            if previous != now.second:
                previous = now.second
                if now.second % 5 == 0:
                    level = logging.ERROR
                else:
                    level = logging.INFO
                logger.log(level, now)
            time.sleep(0.2)

    def stop(self):
        self._stop_event.set()


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


root = tk.Tk()
root.title('摄像头截图采集小工具')
root.geometry('650x550+300+200')  # 定义窗口显示大小和显示位置

frame1 = tk.Frame(root)
console = LogWidget(frame1)
frame1.grid(row=10, column=0, columnspan=5, padx=20)

# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()
select_dir = tk.StringVar()

# 布局空间
csv_file_label = tk.Label(root, text='文件路径:', font='微软雅黑 12')
csv_file_label.grid(column=0, row=0, sticky=tk.W, padx=20)

csv_entry = tk.Entry(root, textvariable=select_path)
csv_entry.grid(column=1, row=0, )

tk.Button(root, text="浏览", command=select_file).grid(row=0, column=3)

# 创建一个下拉列表
tk.Label(root, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=1, sticky=tk.W, padx=20)
number = tk.StringVar()
numberChosen = ttk.Combobox(root, state='readonly', width=12, height=12, textvariable=number)
numberChosen['values'] = ('海康', '大华')  # 设置下拉列表的值
numberChosen.grid(column=1, row=1, sticky=tk.W)  # 设置其在界面中出现的位置  column代表列   row 代表行
numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

# 截图保存目录
cap_dir_label = tk.Label(root, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 10')
cap_dir_label.grid(row=2, column=0, sticky=tk.W, padx=20)

dir_entry = tk.Entry(root, textvariable=select_dir)
dir_entry.grid(column=1, row=2, sticky=tk.W)
# 截图保存路径浏览按钮
tk.Button(root, text="浏览", command=select_folder).grid(row=2, column=3)

# from cv2Snapshot import cams_capture
import cv2Snapshot


def start_cap():
    """
    开始采集的按钮绑定的程序
    :return:
    """
    # 清空日志区
    # log_data_text.delete(0.0, 'end')
    console.scrolled_text.delete(0.0, 'end')
    # csv 文件的路径
    csv_file = csv_entry.get()
    # 摄像头类型
    client_type = numberChosen.get()

    # 截图保存路径
    save_dir = dir_entry.get()

    if not os.path.isfile(csv_file):
        logger.error(f'请重新选择包含ip,password的文件!')
        raise ValueError('请重新选择包含ip,password的文件!')

    logger.info(f'摄像头类型：{client_type}')
    logger.info(f'截图保存路径：{save_dir}')

    if client_type == '海康':
        cv2Snapshot.cams_capture(csv_file, client='hik', save_dir=save_dir)
    elif client_type == '大华':
        cv2Snapshot.cams_capture(csv_file, client='dahua', save_dir=save_dir)


# 采集按钮
capture_button = tk.Button(root, text='开始截图', font='宋体 12', bg='lightblue', width=20,
                           command=lambda: threading.Thread(target=start_cap).start())
capture_button.grid(row=8, columnspan=4, padx=10, pady=10)

# clock = Clock()
# clock.start()
root.mainloop()
