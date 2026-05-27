# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面

pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图

"""

import csv
import logging
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, W, filedialog, DISABLED, NORMAL, messagebox
from tkinter.ttk import Label

# 导入抽离的工具类
from lib.Camera import Camera
from utils.capture_pool import capture_pool, onvif_pool, batch_capture_computer_cameras
from utils.log_config import setup_logging
from utils.log_utils import LogWidget, gui_queue, is_capturing, poll_gui_queue  # noqa: F401
from utils.other_utils import open_folder, display_image, build_save_dir
from utils.tool import validate_csv_file

# 初始化日志
logger = setup_logging()

# ====================== 常量定义 ======================
WINDOW_TITLE = "网络摄像头截图小工具"
WINDOW_GEOMETRY = "650x450+300+200"
FONT_NORMAL = ("微软雅黑", 12)
FONT_LOG = ("宋体", 10)
CSV_FILE_TYPES = [("CSV文件", "*.csv"), ("所有文件", "*.*")]
CAMERA_TYPES = ("海康", "大华", "onvif", "电脑")
REQUIRED_CSV_HEADERS = ("ip", "password")
IMAGE_DISPLAY_SIZE = (100, 50)

# 保存目录
save_dir = None


# ====================== 文件选择函数 ======================
def select_file():
    """选择单个CSV文件"""
    selected_file_path = filedialog.askopenfilename(
        filetypes=[('csv files', '*.csv'), ("All Files", "*.*")]
    )
    if selected_file_path:
        select_path.set(selected_file_path)
        csv_entry.xview_moveto(1.0)


def select_files():
    """选择多个CSV文件"""
    selected_files_path = filedialog.askopenfilenames()
    select_path.set('\n'.join(selected_files_path))


def select_folder():
    """选择保存图片的文件夹"""
    selected_folder = filedialog.askdirectory()
    select_dir.set(selected_folder)


# ====================== 回调函数 ======================
def callbackFunc(event):
    """设备类型选择后的回调函数"""
    if numberChosen.get() == '电脑':
        csv_entry['state'] = 'disable'
        csv_button['state'] = DISABLED
    else:
        csv_entry['state'] = NORMAL
        csv_button['state'] = NORMAL


# ====================== 控件状态管理 ======================
def disable_widgets():
    """禁用关键按钮"""
    capture_button.config(state=DISABLED)
    if numberChosen.get() != "电脑":
        csv_button.config(state=DISABLED)


def restore_widgets():
    """恢复按钮状态"""
    capture_button.config(state=NORMAL)
    if numberChosen.get() != "电脑":
        csv_button.config(state=NORMAL)


def get_capture_config():
    """获取配置"""
    return {
        "client_type": numberChosen.get(),
        "watermark": watermark_var.get(),
        "csv_file": csv_entry.get(),
        "save_base_dir": dir_entry.get()
    }


# ====================== 核心业务逻辑 ======================
def start_cap():
    """开始采集按钮绑定的函数"""
    global save_dir, is_capturing
    if is_capturing:
        gui_queue.put(("show_warning", ("提示", "截图任务正在进行中，请稍后！")))
        return
    is_capturing = True

    # 禁用关键按钮
    disable_widgets()

    try:
        # 清空日志区
        console.clear_log()

        # 清空select_dir
        select_dir.set('')

        # 获取配置
        config = get_capture_config()
        client_type = config['client_type']
        watermark_flag = config['watermark']
        csv_file = config["csv_file"]

        logger.debug(f"采集的摄像头类型为：{client_type}")
        logger.debug(f"是否添加水印：{watermark_flag}")

        # 判断csv_file的合法性（电脑摄像头不用考虑csv）
        if client_type != '电脑':
            validate_csv_file(csv_file)

        save_dir = build_save_dir(client_type, csv_file, config["save_base_dir"])
        select_dir.set(save_dir)

        # 生成打开该路径的按钮
        open_button.configure(command=lambda: open_folder(save_dir, logger, gui_queue))

        logger.info(f'摄像头类型：{client_type}')
        logger.info(f'截图保存路径：{save_dir}')
        logger.info(f'是否添加水印：{"是" if watermark_flag else "否"}')

        gui_queue.put(("show_info", ("开始截图", f"已启动{client_type}摄像头截图，保存路径：{save_dir}")))

        # 如果是电脑摄像头，直接截图
        if client_type == '电脑':
            result = batch_capture_computer_cameras(folder_path=save_dir)
            logger.info(f"电脑多摄像头批量截图结果：{result}")
            for cam_index, (status, file_path) in result.items():
                if status == 1:
                    logger.debug(f"显示摄像头{cam_index}的截图:{file_path}")
                    display_image(file_path, main_window=root)
            return

        # 其余为海康、大华的rtsp协议 / onvif
        if client_type == '海康':
            capture_pool(csv_file, camera_type="hik", is_water_mark=watermark_flag, folder_path=save_dir)
        elif client_type == '大华':
            capture_pool(csv_file, camera_type='dahua', is_water_mark=watermark_flag, folder_path=save_dir)
        elif client_type == 'onvif':
            onvif_pool(csv_file, folder_path=save_dir)

    except Exception as e:
        logger.error(f"截图任务异常:{str(e)}")
        gui_queue.put(("show_error", ("错误", str(e))))
    finally:
        # 恢复状态
        is_capturing = False
        restore_widgets()


# ====================== GUI 布局 ======================
root = tk.Tk()
root.title(WINDOW_TITLE)
root.geometry(WINDOW_GEOMETRY)

# 提前初始化图像显示Label
image_label = Label(root)
image_label.grid(row=9, column=1, sticky=W, padx=20)

frame1 = tk.Frame(root)
console = LogWidget(frame1)
frame1.grid(row=10, column=0, columnspan=5, padx=20)

# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()
select_dir = tk.StringVar()
watermark_var = tk.BooleanVar(value=True)  # 添加水印复选框变量，默认选中

# 摄像头类型下拉列表
tk.Label(root, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=0, sticky=tk.W, padx=20)
number = tk.StringVar()
numberChosen = ttk.Combobox(root, state='readonly', width=12, height=12, textvariable=number)
numberChosen['values'] = CAMERA_TYPES
numberChosen.grid(column=1, row=0, sticky=tk.W)
numberChosen.current(0)
numberChosen.bind("<<ComboboxSelected>>", callbackFunc)

# CSV文件路径
csv_file_label = tk.Label(root, text='包含ip和密码的csv文件路径:', font='微软雅黑 12', fg='green')
csv_file_label.grid(column=0, row=1, sticky=tk.W, padx=20)
csv_entry = tk.Entry(root, textvariable=select_path, justify=tk.RIGHT, width=30)
csv_entry.grid(column=1, row=1, sticky=tk.W)
csv_button = tk.Button(root, text="浏览", command=select_file)
csv_button.grid(row=1, column=3)

# 截图保存目录
cap_dir_label = tk.Label(root, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 12')
cap_dir_label.grid(row=2, column=0, sticky=tk.W, padx=20)
dir_entry = tk.Entry(root, textvariable=select_dir, justify=tk.RIGHT, width=30)
dir_entry.grid(row=2, column=1, sticky=tk.W)
tk.Button(root, text="浏览", command=select_folder).grid(row=2, column=3)

# 添加水印复选框
watermark_check = tk.Checkbutton(root, text="添加水印", variable=watermark_var, font='微软雅黑 12')
watermark_check.grid(row=3, column=0, sticky=tk.W, padx=20)


# 采集按钮（启动线程）
def run_capture_thread():
    threading.Thread(target=start_cap, daemon=True).start()


capture_button = tk.Button(root,
                           text='开始截图',
                           font='宋体 12',
                           bg='lightblue',
                           width=20,
                           command=run_capture_thread)
capture_button.grid(row=8, column=0, columnspan=2, padx=(2, 10), pady=10, sticky=tk.W)

# 打开截图目录
open_button = tk.Button(root, text='打开截图路径')
open_button.grid(row=8, column=2, padx=5, pady=10, sticky='ew')

# 清空日志按钮
clear_button = tk.Button(root, text='清空日志', command=console.clear_log)
clear_button.grid(row=8, column=3, padx=5, pady=10, sticky='ew')

if __name__ == '__main__':
    root.after(100, lambda: poll_gui_queue(root))
    root.mainloop()
