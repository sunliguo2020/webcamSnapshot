# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面


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
    log_data_text.delete(0.0, 'end')
    # csv 文件的路径
    csv_file = csv_entry.get()
    # 摄像头类型
    client_type = numberChosen.get()

    # 截图保存路径
    save_dir = dir_entry.get()

    if not os.path.isfile(csv_file):
        log1.error(f'请重新选择包含ip,password的文件!')
        raise ValueError('请重新选择包含ip,password的文件!')

    log1.info(f'摄像头类型：{client_type}')
    log1.info(f'截图保存路径：{save_dir}')

    if client_type == '海康':
        cams_capture(csv_file, client='hik', save_dir=save_dir)
    elif client_type == '大华':
        cams_capture(csv_file, client='dahua', save_dir=save_dir)


class LoggerBox(scrolledtext.ScrolledText):

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

log_data_text = LoggerBox(root, width=50, height=80)
log_data_text.grid(row=10, column=0, columnspan=4, rowspan=4, padx=(10, 0))
# log1 = logging.getLogger('log1')
log1 = logging.getLogger()
log1.setLevel(logging.DEBUG)
handler = logging.StreamHandler(log_data_text)
log1.addHandler(handler)

root.mainloop()
