# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
"""
import tkinter as tk
from tkinter import filedialog,ttk


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
    select_path.set(selected_folder)


root = tk.Tk()
root.title('采集摄像头截图')

root.geometry('500x300+300+200')  # 定义窗口显示大小和显示位置


# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()

# 布局空间
tk.Label(root, text='文件路径:').grid(column=0, row=0, rowspan=3)
tk.Entry(root, textvariable=select_path).grid(column=1, row=0, rowspan=3)
tk.Button(root, text="选择单个文件", command=select_file).grid(row=0, column=2)
# tk.Button(root, text="选择多个文件", command=select_files).grid(row=1, column=2)
# tk.Button(root, text="选择文件夹", command=select_folder).grid(row=2, column=2)

# 创建一个下拉列表
tk.Label(root, text='摄像头类型:').grid(column=0, row=2)
number = tk.StringVar()
numberChosen = ttk.Combobox(root, width=12, textvariable=number)
numberChosen['values'] = ('海康','大华')     # 设置下拉列表的值
numberChosen.grid(column=1, row=2)      # 设置其在界面中出现的位置  column代表列   row 代表行
numberChosen.current(0)    # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

root.mainloop()
