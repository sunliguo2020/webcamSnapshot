# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
"""
import tkinter as tk
from tkinter import filedialog, ttk

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
    # print(type(csv_entry.get()))
    csv_file = csv_entry.get()
    client_type = numberChosen.get()
    print(client_type)
    if client_type == '海康':
        cams_capture(csv_file, client='hik', save_dir=dir_entry.get())
    elif client_type == '大华':
        cams_capture(csv_file,client='dahua',save_dir=dir_entry.get())


root = tk.Tk()
root.title('摄像头截图采集小工具')

root.geometry('800x700+300+200')  # 定义窗口显示大小和显示位置

# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()
select_dir = tk.StringVar()

# 布局空间
csv_file_label = tk.Label(root, text='文件路径:')
csv_file_label.grid(column=0, row=0, rowspan=3)

csv_entry = tk.Entry(root, textvariable=select_path)
csv_entry.grid(column=1, row=0, rowspan=3)

tk.Button(root, text="选择csv文件", command=select_file).grid(row=0, column=2)
# tk.Button(root, text="选择多个文件", command=select_files).grid(row=1, column=2)
# tk.Button(root, text="选择文件夹", command=select_folder).grid(row=2, column=2)

# 创建一个下拉列表
tk.Label(root, text='摄像头类型:').grid(column=0, row=5, rowspan=3)
number = tk.StringVar()
numberChosen = ttk.Combobox(root,state='readonly', width=12, textvariable=number)
numberChosen['values'] = ('海康', '大华')  # 设置下拉列表的值
numberChosen.grid(column=1, row=5)  # 设置其在界面中出现的位置  column代表列   row 代表行
numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

# 截图保存目录
cap_dir_label = tk.Label(root,text='截图保存位置:')
cap_dir_label.grid(row=6,column=0,rowspan=3)

dir_entry = tk.Entry(root, textvariable=select_dir)
dir_entry.grid(column=1, row=7, rowspan=3)
tk.Button(root, text="浏览", command=select_folder).grid(row=7, column=2)

# 采集按钮
capture_button = tk.Button(root, text='开始采集', bg='lightblue', width=10, command=start_cap)
capture_button.grid(row=8, column=4)

# 日志框
log_data_text = tk.Text(root)
log_data_text.grid(row=10, column=0, columnspan=10)

root.mainloop()
