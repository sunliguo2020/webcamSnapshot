# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面

pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图

"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, W, filedialog, DISABLED, NORMAL
from tkinter.ttk import Label

# 导入抽离的工具类
from utils.capture_pool import capture_pool, onvif_pool, batch_capture_computer_cameras
from utils.log_config import setup_logging
from utils.log_utils import LogWidget, gui_queue, is_capturing, poll_gui_queue  # noqa: F401
from utils.other_utils import open_folder, display_image, build_save_dir
from utils.tool import validate_csv_file

# 初始化日志
logger = setup_logging()


class CameraSnapshotApp:
    """摄像头批量截图图形界面主类"""

    # 常量定义
    WINDOW_TITLE = "网络摄像头截图小工具"
    WINDOW_GEOMETRY = "650x450+300+200"
    CAMERA_TYPES = ("海康", "大华", "onvif", "电脑")

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_GEOMETRY)

        # 状态变量
        self.save_dir = None
        self.select_path = tk.StringVar()
        self.select_dir = tk.StringVar()
        self.watermark_var = tk.BooleanVar(value=True)

        # 控件引用（在 _create_widgets 中初始化）
        self.csv_entry = None
        self.csv_button = None
        self.capture_button = None
        self.open_button = None
        self.console = None
        self.numberChosen = None

        # 创建 GUI 控件
        self._create_widgets()

        # 启动 GUI 队列轮询
        self.root.after(100, lambda: poll_gui_queue(self.root))

    # ====================== GUI 控件创建 ======================

    def _create_widgets(self):
        """创建所有 GUI 控件"""
        # 图像显示 Label
        image_label = Label(self.root)
        image_label.grid(row=9, column=1, sticky=W, padx=20)

        # 日志区域
        frame1 = tk.Frame(self.root)
        self.console = LogWidget(frame1)
        frame1.grid(row=10, column=0, columnspan=5, padx=20)

        # 摄像头类型下拉列表
        tk.Label(self.root, text='摄像头类型:', font='微软雅黑 12').grid(
            column=0, row=0, sticky=tk.W, padx=20
        )
        number = tk.StringVar()
        self.numberChosen = ttk.Combobox(
            self.root, state='readonly', width=12, height=12, textvariable=number
        )
        self.numberChosen['values'] = self.CAMERA_TYPES
        self.numberChosen.grid(column=1, row=0, sticky=tk.W)
        self.numberChosen.current(0)
        self.numberChosen.bind("<<ComboboxSelected>>", self._on_camera_type_changed)

        # CSV 文件路径
        csv_file_label = tk.Label(
            self.root, text='包含ip和密码的csv文件路径:', font='微软雅黑 12', fg='green'
        )
        csv_file_label.grid(column=0, row=1, sticky=tk.W, padx=20)
        self.csv_entry = tk.Entry(
            self.root, textvariable=self.select_path, justify=tk.RIGHT, width=30
        )
        self.csv_entry.grid(column=1, row=1, sticky=tk.W)
        self.csv_button = tk.Button(self.root, text="浏览", command=self._select_file)
        self.csv_button.grid(row=1, column=3)

        # 截图保存目录
        cap_dir_label = tk.Label(
            self.root, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 12'
        )
        cap_dir_label.grid(row=2, column=0, sticky=tk.W, padx=20)
        dir_entry = tk.Entry(
            self.root, textvariable=self.select_dir, justify=tk.RIGHT, width=30
        )
        dir_entry.grid(row=2, column=1, sticky=tk.W)
        tk.Button(self.root, text="浏览", command=self._select_folder).grid(
            row=2, column=3
        )

        # 添加水印复选框
        watermark_check = tk.Checkbutton(
            self.root, text="添加水印", variable=self.watermark_var, font='微软雅黑 12'
        )
        watermark_check.grid(row=3, column=0, sticky=tk.W, padx=20)

        # 开始截图按钮
        self.capture_button = tk.Button(
            self.root,
            text='开始截图',
            font='宋体 12',
            bg='lightblue',
            width=20,
            command=self._run_capture_thread
        )
        self.capture_button.grid(
            row=8, column=0, columnspan=2, padx=(2, 10), pady=10, sticky=tk.W
        )

        # 打开截图目录按钮
        self.open_button = tk.Button(self.root, text='打开截图路径')
        self.open_button.grid(row=8, column=2, padx=5, pady=10, sticky='ew')

        # 清空日志按钮
        clear_button = tk.Button(
            self.root, text='清空日志', command=self.console.clear_log
        )
        clear_button.grid(row=8, column=3, padx=5, pady=10, sticky='ew')

    # ====================== 事件回调 ======================

    def _on_camera_type_changed(self, event):
        """摄像头类型选择回调"""
        if self.numberChosen.get() == '电脑':
            self.csv_entry['state'] = 'disable'
            self.csv_button['state'] = DISABLED
        else:
            self.csv_entry['state'] = NORMAL
            self.csv_button['state'] = NORMAL

    def _select_file(self):
        """选择单个CSV文件"""
        selected_file_path = filedialog.askopenfilename(
            filetypes=[('csv files', '*.csv'), ("All Files", "*.*")]
        )
        if selected_file_path:
            self.select_path.set(selected_file_path)
            self.csv_entry.xview_moveto(1.0)

    def _select_folder(self):
        """选择保存图片的文件夹"""
        selected_folder = filedialog.askdirectory()
        self.select_dir.set(selected_folder)

    # ====================== 控件状态管理 ======================

    def _disable_widgets(self):
        """禁用关键按钮"""
        self.capture_button.config(state=DISABLED)
        if self.numberChosen.get() != "电脑":
            self.csv_button.config(state=DISABLED)

    def _restore_widgets(self):
        """恢复按钮状态"""
        self.capture_button.config(state=NORMAL)
        if self.numberChosen.get() != "电脑":
            self.csv_button.config(state=NORMAL)

    def _get_capture_config(self):
        """获取截图配置"""
        return {
            "client_type": self.numberChosen.get(),
            "watermark": self.watermark_var.get(),
            "csv_file": self.csv_entry.get(),
            "save_base_dir": self.select_dir.get()
        }

    # ====================== 核心业务逻辑 ======================

    def _start_capture(self):
        """开始截图（在子线程中执行）"""
        global is_capturing
        if is_capturing:
            gui_queue.put(("show_warning", ("提示", "截图任务正在进行中，请稍后！")))
            return
        is_capturing = True

        self._disable_widgets()

        try:
            # 清空日志区和保存目录
            self.console.clear_log()
            self.select_dir.set('')

            # 获取配置
            config = self._get_capture_config()
            client_type = config['client_type']
            watermark_flag = config['watermark']
            csv_file = config["csv_file"]

            logger.debug(f"采集的摄像头类型为：{client_type}")
            logger.debug(f"是否添加水印：{watermark_flag}")

            # 校验 CSV 文件（电脑摄像头不用）
            if client_type != '电脑':
                validate_csv_file(csv_file)

            # 构建保存目录
            self.save_dir = build_save_dir(
                client_type, csv_file, config["save_base_dir"]
            )
            self.select_dir.set(self.save_dir)

            # 设置打开目录按钮
            self.open_button.configure(
                command=lambda: open_folder(self.save_dir, logger, gui_queue)
            )

            logger.info(f'摄像头类型：{client_type}')
            logger.info(f'截图保存路径：{self.save_dir}')
            logger.info(f'是否添加水印：{"是" if watermark_flag else "否"}')

            gui_queue.put((
                "show_info",
                ("开始截图", f"已启动{client_type}摄像头截图，保存路径：{self.save_dir}")
            ))

            # 电脑摄像头直接截图
            if client_type == '电脑':
                result = batch_capture_computer_cameras(folder_path=self.save_dir)
                logger.info(f"电脑多摄像头批量截图结果：{result}")
                for cam_index, (status, file_path) in result.items():
                    if status == 1:
                        logger.debug(f"显示摄像头{cam_index}的截图:{file_path}")
                        display_image(file_path, main_window=self.root)
                return

            # 网络摄像头截图
            if client_type == '海康':
                capture_pool(
                    csv_file, camera_type="hik",
                    is_water_mark=watermark_flag, folder_path=self.save_dir
                )
            elif client_type == '大华':
                capture_pool(
                    csv_file, camera_type='dahua',
                    is_water_mark=watermark_flag, folder_path=self.save_dir
                )
            elif client_type == 'onvif':
                onvif_pool(csv_file, folder_path=self.save_dir)

        except Exception as e:
            logger.error(f"截图任务异常:{str(e)}")
            gui_queue.put(("show_error", ("错误", str(e))))
        finally:
            is_capturing = False
            self._restore_widgets()

    def _run_capture_thread(self):
        """在子线程中启动截图"""
        threading.Thread(target=self._start_capture, daemon=True).start()

    def run(self):
        """运行主循环"""
        self.root.mainloop()


if __name__ == '__main__':
    app = CameraSnapshotApp()
    app.run()
