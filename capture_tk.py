# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面

pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图

"""

import csv
# ====================== 日志配置：从配置文件加载 ======================
import logging.config
import os
import os.path
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, W, filedialog, DISABLED, NORMAL, messagebox
from tkinter.ttk import Label

# 导入抽离的工具类
from lib.Camera import Camera
from utils.capture_pool import capture_pool, onvif_pool
from utils.log_utils import LogWidget, gui_queue, is_capturing  # noqa: F401
from utils.other_utils import open_folder, display_image

os.makedirs("logs", exist_ok=True)

# 判断是否在 PyInstaller 打包的环境中运行
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，配置文件在 _MEIPASS 目录下
    base_path = sys._MEIPASS
else:
    # 如果是开发环境，配置文件在当前目录
    base_path = os.path.dirname(os.path.abspath(__file__))

# 如果 logger 尚未配置（例如从 main.py 直接运行时已由 setlogger 配置），则从文件配置
if not logging.getLogger('camera_logger').handlers:
    log_config_path = os.path.join(base_path, 'logging.conf')
    if os.path.exists(log_config_path):
        logging.config.fileConfig(log_config_path)
    else:
        # 如果 logging.conf 不存在，使用基本配置
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/camera.log', encoding='utf-8')
            ]
        )
logger = logging.getLogger('camera_logger')
# ====================================================================

# 新增：常量定义区
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


# GUI队列轮询，处理子线程的GUI操作请求（弹窗、图片显示等）
def poll_gui_queue():
    while True:
        try:
            task, args = gui_queue.get(block=False)
            if task == "show_error":
                messagebox.showerror(*args)
            elif task == "show_info":
                messagebox.showinfo(*args)
            elif task == "show_warning":
                messagebox.showwarning(*args)
            elif task == "display_image":
                display_image(*args)
        except queue.Empty:
            break
    root.after(100, poll_gui_queue)


def select_file():
    # 单个文件选择
    selected_file_path = filedialog.askopenfilename(
        filetypes=[('csv files', '*.csv'), ("All Files", "*.*")]  # 设置文件类型
    )  # 使用askopenfilename函数选择单个文件
    if selected_file_path:
        select_path.set(selected_file_path)  # 设置文本变量
        csv_entry.xview_moveto(1.0)


def select_files():
    # 多个文件选择
    selected_files_path = filedialog.askopenfilenames()  # askopenfilenames函数选择多个文件
    select_path.set('\n'.join(selected_files_path))  # 多个文件的路径用换行符隔开


def select_folder():
    """
    保存图片的文件夹选择
    @return:
    """
    selected_folder = filedialog.askdirectory()  # 使用askdirectory函数选择文件夹
    select_dir.set(selected_folder)


def callbackFunc(event):
    """
    设备类型选择后的回调函数
    @param event:
    @return:
    """
    # print(f"New Element Selected{event}")
    # print(numberChosen.current(), numberChosen.get())

    # 如果用户选择电脑，则下面的csv为不可选择状态
    if numberChosen.get() == '电脑':
        csv_entry['state'] = 'disable'
        csv_button['state'] = DISABLED
    else:
        csv_entry['state'] = NORMAL
        csv_button['state'] = NORMAL


def batch_capture_computer_cameras(folder_path=None,
                                   is_water_mark=True,
                                   max_index=3):
    """
    辅助函数：电脑所有可用摄像头批量截图
    @param max_index:
    @param folder_path: 统一保存文件夹路径
    @param is_water_mark: 是否添加水印
    @return: dict 键：摄像头索引，值：截图结果（status, file_path/error_msg）
    """
    # 1. 枚举所有可用摄像头
    # available_cams = Camera.enum_computer_cameras()
    # if not available_cams:
    #     logger.warning("未检测到可用电脑摄像头")
    #     return {}

    # 2. 遍历每个摄像头，分别截图
    capture_results = {}
    found_camera = False

    for cam_index in range(max_index):
        # 创建摄像头实例
        cam = Camera(
            camera_type="computer",
            cam_index=cam_index,
            folder_path=folder_path,
            is_water_mark=is_water_mark
        )
        result = cam.capture()

        status, info = result

        # 成功
        if status == 1:

            found_camera = True

            logger.info(
                f"摄像头{cam_index}截图成功"
            )

            capture_results[cam_index] = result

        else:

            logger.debug(
                f"摄像头{cam_index}不可用:{info}"
            )

    if not found_camera:
        logger.warning("未检测到可用电脑摄像头")

    return capture_results


def disable_widgets():
    """
    禁用csv_button
    @return:
    """
    capture_button.config(state=DISABLED)

    if numberChosen.get() != "电脑":
        csv_button.config(state=DISABLED)


def restore_widgets():
    """
    启动csv_button
    @return:
    """
    capture_button.config(state=NORMAL)

    # 只有非电脑摄像头时，才恢复csv_button状态

    if numberChosen.get() != "电脑":
        csv_button.config(state=NORMAL)


def get_capture_config():
    """
    获取配置
    @return:
    """
    return {
        "client_type": numberChosen.get(),
        "watermark": watermark_var.get(),
        "csv_file": csv_entry.get(),
        "save_base_dir": dir_entry.get()
    }


def validate_csv_file(csv_file):
    """
    检验csv文件的合法性
    @param csv_file:
    @return:
    """
    logger.info(f"开始校验csv文件：{csv_file}")
    # 1、判断文件是否存在
    if not os.path.isfile(csv_file):
        logger.error('csv文件不存在')
        raise FileNotFoundError("CSV文件不存在，请重新选择")
    # 2、判断扩展名
    if not csv_file.lower().endswith(".csv"):
        logger.error("选择的不是csv文件")
        raise ValueError("请选择csv文件")
    # 3、校验头部
    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as f:

            reader = csv.DictReader(f)
            # 空文件
            if reader.fieldnames is None:
                raise ValueError("CSV为空")

            headers = [h.strip().lower() for h in reader.fieldnames]

            logger.debug(f"csv表头：{headers}")

            required_headers = {"ip", "password"}

            if not required_headers.issubset(headers):
                logger.error(
                    "csv缺少必要字段：ip,password"
                )
                raise ValueError("CSV首行必须包含 ip,password")

    except UnicodeDecodeError:
        logger.exception("csv编码错误")
        raise ValueError("CSV编码错误，请使用UTF-8")
    except Exception:
        logger.exception("读取csv文件失败")
        raise

    logger.info('csv文件校验通过')


def build_save_dir(config):
    """
    构建保存文件的目录
    截图保存路径 或 保存截图的文件夹默认是 csv文件名 + 当前日期
    保存截图的文件夹默认是 csv文件名 + 当前日期,设置保存截图的文件夹的默认值
    @param config:
    @return:
    """

    client_type = config["client_type"]

    csv_file = config["csv_file"]

    base_dir = config["save_base_dir"]

    basename = ""

    if client_type != "电脑" and csv_file:
        basename = os.path.splitext(
            os.path.basename(csv_file)
        )[0]

    default_base_dir = (
            base_dir or os.path.join(os.getcwd(), basename)
    )

    date_dir = time.strftime('%Y-%m-%d')

    time_dir = time.strftime('%Y-%m-%d_%H-%M-%S')

    save_dir = os.path.join(
        default_base_dir,
        date_dir,
        time_dir
    )

    os.makedirs(save_dir, exist_ok=True)

    return save_dir


def start_cap():
    """
    开始采集按钮绑定的函数
    :return:
    """
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
        # 获取摄像头类型
        client_type = config['client_type']
        logger.debug(f"采集的摄像头类型为：{client_type}")

        # 获取是否添加水印
        watermark_flag = config['watermark']
        logger.debug(f"是否添加水印：{watermark_flag}")

        # 网络摄像头截图csv 文件的路径
        csv_file = config["csv_file"]

        # 判断csv_file的合法性
        # 如果是电脑摄像头的话，不用考虑csv
        if client_type != '电脑':
            validate_csv_file(csv_file)

        save_dir = build_save_dir(config)

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
                # 截图成功
                if status == 1:
                    logger.debug(f"显示摄像头{cam_index}的截图:{file_path}")
                    display_image(file_path, main_window=root)
            return

        # 其余为海康 大华的rtsp协议
        # onvif也是先获取rtsp地址，再截图

        if client_type == '海康':
            capture_pool(csv_file, camera_type="hik", is_water_mark=watermark_flag, folder_path=save_dir)

        elif client_type == '大华':
            capture_pool(csv_file, camera_type='dahua', is_water_mark=watermark_flag, folder_path=save_dir)

        elif client_type == 'onvif':
            # capture_pool(csv_file, camera_type='onvif', folder_path=save_dir)
            onvif_pool(csv_file, folder_path=save_dir)
    except Exception as e:
        logger.error(f"截图任务异常:{str(e)}")
        # 异常时也要确保状态充值
        gui_queue.put((
            "show_error",
            ("错误",str(e))
        ))
    finally:
        # 恢复状态:标记为未在截图
        is_capturing = False
        # 恢复按钮状态
        restore_widgets()


root = tk.Tk()
# 标题
root.title(WINDOW_TITLE)
# 定义窗口显示大小和显示位置
root.geometry(WINDOW_GEOMETRY)

# 提前初始化图像显示Label，避免重复创建
image_label = Label(root)
image_label.grid(row=9, column=1, sticky=W, padx=20)

frame1 = tk.Frame(root)
console = LogWidget(frame1)
frame1.grid(row=10, column=0, columnspan=5, padx=20)

# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()
select_dir = tk.StringVar()
watermark_var = tk.BooleanVar(value=True)  # 添加水印复选框变量，默认选中

# 布局空间

# 截图的类型 电脑摄像头  海康  大华 onvif
# 创建一个下拉列表
tk.Label(root, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=0, sticky=tk.W, padx=20)
number = tk.StringVar()
numberChosen = ttk.Combobox(root, state='readonly', width=12, height=12, textvariable=number)
numberChosen['values'] = ('海康', '大华', 'onvif', '电脑')  # 设置下拉列表的值
numberChosen.grid(column=1, row=0, sticky=tk.W)  # 设置其在界面中出现的位置  column代表列   row 代表行
numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

# 绑定改变值的回调函数
numberChosen.bind("<<ComboboxSelected>>", callbackFunc)

# 保存 ip地址和密码的csv文件
# 标签组件
csv_file_label = tk.Label(root, text='包含ip和密码的csv文件路径:', font='微软雅黑 12', fg='green')
csv_file_label.grid(column=0, row=1, sticky=tk.W, padx=20)
# 输入框
# 优化输入框宽度，添加水平滚动条
csv_entry = tk.Entry(root, textvariable=select_path, justify=tk.RIGHT, width=30)  # 明确宽度
csv_entry.grid(column=1, row=1, sticky=tk.W)

csv_button = tk.Button(root, text="浏览", command=select_file)
csv_button.grid(row=1, column=3)

# 截图保存目录 标签
cap_dir_label = tk.Label(root, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 12')
cap_dir_label.grid(row=2, column=0, sticky=tk.W, padx=20)

# 截图保存目录
dir_entry = tk.Entry(root, textvariable=select_dir, justify=tk.RIGHT, width=30)
dir_entry.grid(row=2, column=1, sticky=tk.W)

# 截图保存路径浏览按钮
tk.Button(root, text="浏览", command=select_folder).grid(row=2, column=3)

# 添加水印复选框
watermark_check = tk.Checkbutton(root, text="添加水印", variable=watermark_var, font='微软雅黑 12')
watermark_check.grid(row=3, column=0, sticky=tk.W, padx=20)


# 采集按钮
def run_capture_thread():
    threading.Thread(
        target=start_cap,
        daemon=True
    ).start()


capture_button = tk.Button(root,
                           text='开始截图',
                           font='宋体 12',
                           bg='lightblue',
                           width=20,
                           command=run_capture_thread)
#
capture_button.grid(row=8, column=0, columnspan=2, padx=(2, 10), pady=10, sticky=tk.W)

# 打开截图目录
open_button = tk.Button(root, text='打开截图路径')
open_button.grid(row=8, column=2, padx=5, pady=10, sticky='ew')

# 清空日志按钮
clear_button = tk.Button(root, text='清空日志', command=console.clear_log)
clear_button.grid(row=8, column=3, padx=5, pady=10, sticky='ew')

if __name__ == '__main__':
    root.after(100, poll_gui_queue)
    root.mainloop()
