"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面
"""

import logging
import os
import threading
import time
import tkinter as tk
from tkinter import DISABLED, NORMAL, filedialog, messagebox, ttk

import requests

# 导入抽离的工具类
from gui.csv_preview import show_csv_preview
from gui.image_preview import show_preview_image
from gui.watermark_settings import edit_watermark_style
from utils.capture_pool import (
    batch_capture_computer_cameras,
    capture_hikvision_recorder_channels,
    capture_cameras,
    expand_hikvision_channel_numbers,
    expand_hikvision_channels,
)
from utils.hikvision_device_info import (
    get_hikvision_streaming_channel_numbers,
)
from utils.log_config import setup_logging
from utils.log_utils import (
    LogWidget,
    gui_queue,
    pause_event,
    poll_gui_queue,
)
from utils.other_utils import build_save_dir, open_folder
from utils.tool import get_cam_list, is_ipv4
from utils.watermark import (
    load_watermark_style,
    normalize_watermark_style,
)

logger = logging.getLogger("camera_logger")


class CameraSnapshotApp:
    """摄像头批量截图图形界面主类"""

    WINDOW_TITLE = "网络摄像头截图小工具"
    WINDOW_GEOMETRY = "500x680+200+40"
    CAMERA_TYPES = ("海康", "海康录像机", "大华", "onvif", "电脑")

    # 字体定义
    FONT_TITLE = ("微软雅黑", 11, "bold")
    FONT_LABEL = ("微软雅黑", 10)
    FONT_BUTTON = ("微软雅黑", 10)
    FONT_CAPTURE_BTN = ("微软雅黑", 11, "bold")
    FONT_LOG = ("宋体", 10)

    # 颜色定义
    COLOR_BG = "#F0F0F0"
    COLOR_BUTTON = "#4A90D9"
    COLOR_BUTTON_TEXT = "white"
    COLOR_CAPTURE_BG = "#5CB85C"
    COLOR_LABEL_GREEN = "#2E7D32"
    COLOR_FRAME_BG = "#FFFFFF"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_GEOMETRY)
        self.root.configure(bg=self.COLOR_BG)
        self.root.resizable(False, False)  # 禁止调整窗口大小

        # 状态变量
        self.save_dir = None
        self.select_path = tk.StringVar()
        self.select_dir = tk.StringVar()
        self.watermark_var = tk.BooleanVar(value=True)
        try:
            self.watermark_style = load_watermark_style()
        except (OSError, ValueError, TypeError) as error:
            logger.exception("读取水印样式配置失败")
            self.watermark_style = normalize_watermark_style()
            messagebox.showwarning(
                "水印设置",
                f"读取水印样式失败，将使用默认样式：{error}",
                parent=self.root,
            )
        self.temp_ip = tk.StringVar()
        self.temp_password = tk.StringVar()
        self.channel_start = tk.StringVar(value="1")
        self.channel_end = tk.StringVar(value="64")
        self.recorder_ip = tk.StringVar()
        self.recorder_password = tk.StringVar()
        self.capture_running = False

        # 控件引用
        self.csv_entry = None
        self.csv_button = None
        self.preview_button = None
        self.capture_button = None
        self.pause_button = None
        self.open_button = None
        self.console = None
        self.numberChosen = None

        # 创建 GUI 控件
        self._create_widgets()

        # 启动 GUI 队列轮询
        self.root.after(100, lambda: poll_gui_queue(self.root))

    # ====================== 辅助方法 ======================

    def _create_label(self, parent, text, row, column, **kwargs):
        """创建统一风格的标签"""
        label = tk.Label(
            parent, text=text, font=self.FONT_LABEL,
            bg=self.COLOR_BG, anchor="w", **kwargs
        )
        label.grid(row=row, column=column, sticky="w", padx=(20, 5), pady=8)
        return label

    # ====================== CSV 预览功能 ======================

    def _preview_csv(self):
        """预览 CSV 文件内容"""
        show_csv_preview(self.root, self.select_path.get())

    # ====================== 临时截图 ======================

    def _temp_capture(self):
        """临时截图：对单个IP摄像头截图并显示"""
        ip = self.temp_ip.get().strip()
        password = self.temp_password.get().strip()

        if not ip:
            gui_queue.put(("show_warning", ("提示", "请输入摄像头 IP 地址")))
            return
        if not password:
            gui_queue.put(("show_warning", ("提示", "请输入摄像头密码")))
            return

        # 根据当前选择的摄像头类型确定 camera_type
        client_type = self.numberChosen.get()
        camera_type_map = {
            "海康": "hik",
            "海康录像机": "hik",
            "大华": "dahua",
            "onvif": "onvif",
            "电脑": "computer"
        }
        camera_type = camera_type_map.get(client_type, "hik")

        def do_capture():
            try:
                from lib.Camera import Camera
                logger.info(f"临时截图 - IP: {ip}, 类型: {client_type}")
                result = Camera(
                    ip=ip,
                    password=password,
                    camera_type=camera_type,
                    channel_no=(
                        1 if client_type == "海康录像机" else None
                    ),
                    watermark_style=self.watermark_style,
                ).capture()
                status, info = result
                if status == 1:
                    logger.info(f"临时截图成功: {info}")
                    gui_queue.put((
                        "call",
                        (lambda: show_preview_image(self.root, info),),
                    ))
                else:
                    logger.warning(f"临时截图失败: {info}")
                    gui_queue.put(("show_warning", ("截图失败", str(info))))
            except Exception as e:
                logger.error(f"临时截图异常: {e}")
                gui_queue.put(("show_error", ("错误", str(e))))

        threading.Thread(target=do_capture, daemon=True).start()

    # ====================== GUI 控件创建 ======================

    def _create_widgets(self):
        """创建所有 GUI 控件"""
        # ---- 标题 ----
        title_label = tk.Label(
            self.root, text="📷 网络摄像头批量截图",
            font=("微软雅黑", 14, "bold"),
            bg=self.COLOR_BG, fg="#333333"
        )
        title_label.pack(pady=(15, 5), padx=20, anchor="w")
        tk.Label(
            self.root, text="支持海康、大华、ONVIF协议摄像头及本地USB摄像头",
            font=("微软雅黑", 9), bg=self.COLOR_BG, fg="#888888"
        ).pack(pady=(0, 10), padx=20, anchor="w")

        # ==================== 中间内容区域 ====================
        content_frame = tk.Frame(self.root, bg=self.COLOR_BG)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ---- 摄像头类型 + 水印复选框 ----
        type_frame = tk.Frame(content_frame, bg=self.COLOR_BG)
        self.type_frame = type_frame
        type_frame.pack(fill="x", padx=10, pady=5, anchor="w")
        tk.Label(
            type_frame, text="摄像头类型:", font=self.FONT_LABEL,
            bg=self.COLOR_BG, anchor="w"
        ).pack(side="left")
        number = tk.StringVar()
        self.numberChosen = ttk.Combobox(
            type_frame, state='readonly', width=14, height=12,
            textvariable=number, font=("微软雅黑", 10)
        )
        self.numberChosen['values'] = self.CAMERA_TYPES
        self.numberChosen.pack(side="left", padx=(5, 20))
        self.numberChosen.current(0)
        self.numberChosen.bind("<<ComboboxSelected>>", self._on_camera_type_changed)

        self.channel_frame = tk.Frame(content_frame, bg=self.COLOR_BG)
        tk.Label(
            self.channel_frame, text="通道筛选范围:", font=self.FONT_LABEL,
            bg=self.COLOR_BG
        ).pack(side="left", padx=(20, 5))
        tk.Entry(
            self.channel_frame, textvariable=self.channel_start,
            font=("微软雅黑", 9), width=5, relief="solid", bd=1
        ).pack(side="left")
        tk.Label(
            self.channel_frame, text="至", font=self.FONT_LABEL,
            bg=self.COLOR_BG
        ).pack(side="left", padx=5)
        tk.Entry(
            self.channel_frame, textvariable=self.channel_end,
            font=("微软雅黑", 9), width=5, relief="solid", bd=1
        ).pack(side="left")

        self.recorder_frame = tk.Frame(content_frame, bg=self.COLOR_BG)
        tk.Label(
            self.recorder_frame, text="录像机 IP:", font=self.FONT_LABEL,
            bg=self.COLOR_BG
        ).pack(side="left", padx=(20, 5))
        tk.Entry(
            self.recorder_frame, textvariable=self.recorder_ip,
            font=("微软雅黑", 9), width=16, relief="solid", bd=1
        ).pack(side="left")
        tk.Label(
            self.recorder_frame, text="密码:", font=self.FONT_LABEL,
            bg=self.COLOR_BG
        ).pack(side="left", padx=(10, 5))
        tk.Entry(
            self.recorder_frame, textvariable=self.recorder_password,
            font=("微软雅黑", 9), width=16, relief="solid", bd=1, show="*"
        ).pack(side="left")

        # 水印复选框
        watermark_check = tk.Checkbutton(
            type_frame, text="添加水印",
            variable=self.watermark_var,
            font=self.FONT_LABEL,
            bg=self.COLOR_BG,
            activebackground=self.COLOR_BG,
            selectcolor="white"
        )
        watermark_check.pack(side="left")
        tk.Button(
            type_frame, text="水印样式",
            command=self._open_watermark_settings,
            font=self.FONT_BUTTON, bg="#5BC0DE", fg="white",
            relief="flat", bd=0, cursor="hand2", padx=8, pady=2
        ).pack(side="left", padx=(8, 0))

        # ---- CSV 文件路径 ----
        csv_row = tk.Frame(content_frame, bg=self.COLOR_BG)
        self.csv_row = csv_row
        csv_row.pack(fill="x", padx=10, pady=5, anchor="w")
        tk.Label(
            csv_row, text="CSV文件路径:", font=self.FONT_LABEL,
            bg=self.COLOR_BG, fg=self.COLOR_LABEL_GREEN, anchor="w",
            width=12
        ).pack(side="left")
        self.csv_entry = tk.Entry(
            csv_row, textvariable=self.select_path,
            font=("微软雅黑", 9), width=30,
            relief="solid", bd=1
        )
        self.csv_entry.pack(side="left", padx=(5, 2))
        self.csv_button = tk.Button(
            csv_row, text="浏览", command=self._select_file,
            font=self.FONT_BUTTON, bg=self.COLOR_BUTTON, fg=self.COLOR_BUTTON_TEXT,
            relief="flat", bd=0, cursor="hand2", padx=10, pady=3, width=5
        )
        self.csv_button.pack(side="left", padx=2)
        self.preview_button = tk.Button(
            csv_row, text="预览", command=self._preview_csv,
            font=self.FONT_BUTTON, bg="#5BC0DE", fg="white",
            relief="flat", bd=0, cursor="hand2", padx=10, pady=3, width=5
        )
        self.preview_button.pack(side="left", padx=2)

        # ---- 截图保存目录 ----
        dir_row = tk.Frame(content_frame, bg=self.COLOR_BG)
        self.dir_row = dir_row
        dir_row.pack(fill="x", padx=10, pady=5, anchor="w")
        tk.Label(
            dir_row, text="保存位置:", font=self.FONT_LABEL,
            bg=self.COLOR_BG, anchor="w",
            width=12
        ).pack(side="left")
        dir_entry = tk.Entry(
            dir_row, textvariable=self.select_dir,
            font=("微软雅黑", 9), width=30,
            relief="solid", bd=1
        )
        dir_entry.pack(side="left", padx=(5, 2))
        tk.Button(
            dir_row, text="浏览", command=self._select_folder,
            font=self.FONT_BUTTON, bg=self.COLOR_BUTTON, fg=self.COLOR_BUTTON_TEXT,
            relief="flat", bd=0, cursor="hand2", padx=10, pady=3, width=5
        ).pack(side="left", padx=2)

        # ---- 临时截图区域 ----
        temp_frame = tk.Frame(content_frame, bg=self.COLOR_BG)
        self.temp_frame = temp_frame
        temp_frame.pack(fill="x", padx=10, pady=5, anchor="w")

        tk.Label(
            temp_frame, text="临时截图:", font=self.FONT_LABEL,
            bg=self.COLOR_BG, fg="#D9534F"
        ).pack(side="left")

        tk.Label(
            temp_frame, text="IP:", font=("微软雅黑", 9),
            bg=self.COLOR_BG
        ).pack(side="left", padx=(10, 2))

        tk.Entry(
            temp_frame, textvariable=self.temp_ip,
            font=("微软雅黑", 9), width=14,
            relief="solid", bd=1
        ).pack(side="left")

        tk.Label(
            temp_frame, text="密码:", font=("微软雅黑", 9),
            bg=self.COLOR_BG
        ).pack(side="left", padx=(10, 2))

        tk.Entry(
            temp_frame, textvariable=self.temp_password,
            font=("微软雅黑", 9), width=14,
            relief="solid", bd=1, show="*"
        ).pack(side="left")

        tk.Button(
            temp_frame, text="截图", command=self._temp_capture,
            font=self.FONT_BUTTON, bg="#D9534F", fg="white",
            relief="flat", bd=0, cursor="hand2",
            padx=10, pady=2
        ).pack(side="left", padx=(10, 0))

        # ---- 分隔线 ----
        self.action_separator = ttk.Separator(
            content_frame, orient='horizontal'
        )
        self.action_separator.pack(fill="x", padx=20, pady=10)

        # ---- 操作按钮区域 ----
        button_frame = tk.Frame(content_frame, bg=self.COLOR_BG)
        button_frame.pack(pady=5, padx=10, anchor="w")

        # 开始截图按钮
        self.capture_button = tk.Button(
            button_frame,
            text='▶ 开始截图',
            font=self.FONT_CAPTURE_BTN,
            bg=self.COLOR_CAPTURE_BG,
            fg="white",
            relief="flat", bd=0,
            cursor="hand2",
            padx=20, pady=6,
            command=self._run_capture_thread
        )
        self.capture_button.pack(side="left", padx=(0, 5))

        # 暂停/继续按钮
        self.pause_button = tk.Button(
            button_frame,
            text='⏸ 暂停',
            font=self.FONT_BUTTON,
            bg="#F0AD4E",
            fg="white",
            relief="flat", bd=0,
            cursor="hand2",
            padx=10, pady=6,
            state=DISABLED,
            command=self._toggle_pause
        )
        self.pause_button.pack(side="left", padx=3)

        # 打开截图目录按钮
        self.open_button = tk.Button(
            button_frame,
            text='📂 打开截图目录',
            font=self.FONT_BUTTON,
            bg="#F0AD4E",
            fg="white",
            relief="flat", bd=0,
            cursor="hand2",
            padx=10, pady=6
        )
        self.open_button.pack(side="left", padx=3)

        # 清空日志按钮
        clear_button = tk.Button(
            button_frame,
            text='🗑 清空日志',
            font=self.FONT_BUTTON,
            bg="#D9534F",
            fg="white",
            relief="flat", bd=0,
            cursor="hand2",
            padx=10, pady=6,
            command=lambda: self.console.clear_log() if self.console else None
        )
        clear_button.pack(side="left", padx=3)

        # ==================== 日志区域（在底部） ====================
        log_frame = tk.Frame(self.root, bg=self.COLOR_FRAME_BG,
                             relief="solid", bd=1)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # 日志标题
        tk.Label(
            log_frame, text="运行日志",
            font=("微软雅黑", 9, "bold"),
            bg=self.COLOR_FRAME_BG, fg="#555555"
        ).pack(anchor="w", padx=8, pady=(5, 0))

        self.console = LogWidget(log_frame)
        self.console.scrolled_text.pack(fill="both", expand=True,
                                        padx=8, pady=(3, 8))

    # ====================== 事件回调 ======================

    def _on_camera_type_changed(self, event):
        """摄像头类型选择回调"""
        is_recorder = self.numberChosen.get() == "海康录像机"
        if is_recorder:
            self.channel_frame.pack(
                fill="x",
                padx=10,
                pady=2,
                anchor="w",
                after=self.type_frame,
            )
        else:
            self.channel_frame.pack_forget()
        if is_recorder:
            self.recorder_frame.pack(
                fill="x",
                padx=10,
                pady=2,
                anchor="w",
                after=self.channel_frame,
            )
            self.csv_row.pack_forget()
            self.temp_frame.pack_forget()
        else:
            self.recorder_frame.pack_forget()
            self.csv_row.pack(
                fill="x",
                padx=10,
                pady=5,
                anchor="w",
                before=self.dir_row,
            )
            self.temp_frame.pack(
                fill="x",
                padx=10,
                pady=5,
                anchor="w",
                before=self.action_separator,
            )
        if self.numberChosen.get() == '电脑':
            self.csv_entry['state'] = 'disabled'
            self.csv_button['state'] = DISABLED
            self.preview_button['state'] = DISABLED
        else:
            self.csv_entry['state'] = NORMAL
            self.csv_button['state'] = NORMAL
            self.preview_button['state'] = NORMAL

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

    def _toggle_pause(self):
        """切换暂停/继续状态"""
        if pause_event.is_set():
            pause_event.clear()
            self.pause_button.config(text='▶ 继续', bg="#5CB85C")
            logger.info("截图任务已暂停，等待当前任务完成后暂停")
        else:
            pause_event.set()
            self.pause_button.config(text='⏸ 暂停', bg="#F0AD4E")
            logger.info("截图任务已恢复")

    def _disable_widgets(self):
        """禁用关键按钮"""
        self.capture_button.config(state=DISABLED, bg="#A5D6A7")
        self.pause_button.config(state=NORMAL)
        if self.numberChosen.get() != "电脑":
            self.csv_button.config(state=DISABLED)
            # 预览按钮保持可用

    def _restore_widgets(self):
        """恢复按钮状态"""
        self.capture_button.config(state=NORMAL, bg=self.COLOR_CAPTURE_BG)
        self.pause_button.config(state=DISABLED, text='⏸ 暂停', bg="#F0AD4E")
        if self.numberChosen.get() != "电脑":
            self.csv_button.config(state=NORMAL)

    def _get_capture_config(self):
        """获取截图配置"""
        return {
            "client_type": self.numberChosen.get(),
            "watermark": self.watermark_var.get(),
            "watermark_style": dict(self.watermark_style),
            "csv_file": self.csv_entry.get(),
            "save_base_dir": self.select_dir.get(),
            "channel_start": self.channel_start.get(),
            "channel_end": self.channel_end.get(),
            "recorder_ip": self.recorder_ip.get().strip(),
            "recorder_password": self.recorder_password.get(),
        }

    def _open_watermark_settings(self):
        style = edit_watermark_style(self.root, self.watermark_style)
        if style is not None:
            self.watermark_style = style

    # ====================== 核心业务逻辑 ======================

    def _start_capture(self, config):
        """开始截图（在子线程中执行）"""
        task_started = time.perf_counter()
        client_type = 'unknown'
        try:
            client_type = config['client_type']
            watermark_flag = config['watermark']
            csv_file = config["csv_file"]

            # 校验摄像头类型
            if not client_type:
                gui_queue.put(("show_warning", ("提示", "请选择摄像头类型")))
                return

            logger.debug(f"采集的摄像头类型为：{client_type}")
            logger.debug(f"是否添加水印：{watermark_flag}")

            camera_records = None
            if client_type == "海康录像机":
                ip = config["recorder_ip"]
                password = config["recorder_password"]
                if not is_ipv4(ip):
                    raise ValueError("请输入有效的录像机 IPv4 地址")
                if not password:
                    raise ValueError("请输入录像机密码")
                camera_records = [{"ip": ip, "password": password}]
                csv_file = f"{ip}.csv"
                manual_channel_records = expand_hikvision_channels(
                    camera_records,
                    config["channel_start"],
                    config["channel_end"],
                )
                channel_start = int(config["channel_start"])
                channel_end = int(config["channel_end"])
                try:
                    detected_channels = (
                        get_hikvision_streaming_channel_numbers(
                            ip,
                            "admin",
                            password,
                        )
                    )
                except (
                    PermissionError,
                    requests.RequestException,
                    ValueError,
                ) as error:
                    logger.warning(
                        "无法自动读取录像机通道列表，使用手动范围 %s-%s：%s",
                        channel_start,
                        channel_end,
                        error,
                    )
                    camera_records = manual_channel_records
                else:
                    selected_channels = [
                        channel
                        for channel in detected_channels
                        if channel_start <= channel <= channel_end
                    ]
                    if not selected_channels:
                        raise ValueError(
                            f"录像机检测到的通道 {detected_channels} "
                            f"不在所选范围 {channel_start}-{channel_end} 内"
                        )
                    logger.info(
                        "自动识别到录像机流通道：%s；本次采集 %d 个通道",
                        ", ".join(map(str, detected_channels)),
                        len(selected_channels),
                    )
                    camera_records = expand_hikvision_channel_numbers(
                        [{"ip": ip, "password": password}],
                        selected_channels,
                    )
            elif client_type != '电脑':
                if not csv_file or not os.path.isfile(csv_file):
                    raise FileNotFoundError("CSV文件不存在，请重新选择")
                if not csv_file.lower().endswith('.csv'):
                    raise ValueError("请选择 CSV 文件")
                csv_started = time.perf_counter()
                camera_records = list(get_cam_list(csv_file))
                logger.info(
                    "[耗时] CSV读取 文件=%s 有效记录=%d 耗时=%.3fs",
                    csv_file,
                    len(camera_records),
                    time.perf_counter() - csv_started,
                )
                if not camera_records:
                    raise ValueError("CSV 中没有有效的摄像头记录")

            # 构建保存目录
            directory_started = time.perf_counter()
            self.save_dir = build_save_dir(
                client_type, csv_file, config["save_base_dir"]
            )
            logger.info(
                "[耗时] 创建保存目录 类型=%s 耗时=%.3fs",
                client_type,
                time.perf_counter() - directory_started,
            )
            # 在 GUI 线程更新保存目录和打开目录按钮
            save_dir = self.save_dir
            gui_queue.put(("call", (lambda: self._set_save_dir(save_dir),)))

            logger.info(f'摄像头类型：{client_type}')
            logger.info(f'截图保存路径：{self.save_dir}')
            logger.info(f'是否添加水印：{"是" if watermark_flag else "否"}')

            # 电脑摄像头直接截图
            if client_type == '电脑':
                result = batch_capture_computer_cameras(
                    folder_path=self.save_dir,
                    is_water_mark=watermark_flag,
                    watermark_style=config["watermark_style"],
                )
                logger.info(f"电脑多摄像头批量截图结果：{result}")
                for cam_index, (status, file_path) in result.items():
                    if status == 1:
                        logger.debug(f"显示摄像头{cam_index}的截图:{file_path}")
                        gui_queue.put((
                            "call",
                            (lambda fp=file_path: show_preview_image(
                                self.root, fp
                            ),),
                        ))
                return

            # 网络摄像头截图
            if client_type == "海康录像机":
                result, statistics = capture_hikvision_recorder_channels(
                    camera_records,
                    csv_file=csv_file,
                    folder_path=self.save_dir,
                    is_water_mark=watermark_flag,
                    watermark_style=config["watermark_style"],
                )
            elif client_type == '海康':
                result, statistics = capture_cameras(
                    camera_records,
                    camera_type="hik",
                    csv_file=csv_file,
                    is_water_mark=watermark_flag,
                    folder_path=self.save_dir,
                    watermark_style=config["watermark_style"],
                )
            elif client_type == '大华':
                result, statistics = capture_cameras(
                    camera_records,
                    camera_type='dahua',
                    csv_file=csv_file,
                    is_water_mark=watermark_flag,
                    folder_path=self.save_dir,
                    watermark_style=config["watermark_style"],
                )
            elif client_type == 'onvif':
                result, statistics = capture_cameras(
                    camera_records,
                    camera_type='onvif',
                    csv_file=csv_file,
                    is_water_mark=watermark_flag,
                    folder_path=self.save_dir,
                    watermark_style=config["watermark_style"],
                )

            if client_type != '电脑':
                unit = "通道" if client_type == "海康录像机" else "台"
                summary = (
                    f"批量截图完成：共 {statistics['total']} {unit}，"
                    f"成功 {statistics['success']} {unit}，"
                    f"失败 {statistics['failed']} {unit}。"
                )
                if statistics['fail_log_file']:
                    summary += f"\n失败清单：{statistics['fail_log_file']}"
                if statistics['errors']:
                    summary += f"\n异常：{statistics['errors'][0]}"
                logger.info(summary.replace('\n', ' '))
                if statistics['failed'] or statistics['errors']:
                    gui_queue.put(("show_warning", ("截图完成", summary)))
                else:
                    gui_queue.put(("show_info", ("截图完成", summary)))

        except Exception as e:
            logger.error(f"截图任务异常:{str(e)}")
            gui_queue.put(("show_error", ("错误", str(e))))
        finally:
            logger.info(
                "[耗时] 截图任务结束 类型=%s 总耗时=%.3fs",
                client_type,
                time.perf_counter() - task_started,
            )
            pause_event.set()
            gui_queue.put(("call", (self._finish_capture,)))

    def _set_save_dir(self, save_dir):
        """在 GUI 线程更新本次实际保存目录和打开目录按钮"""
        self.save_dir = save_dir
        self.open_button.configure(
            command=lambda: open_folder(save_dir, logger, gui_queue)
        )

    def _finish_capture(self):
        """在 GUI 线程恢复截图控件"""
        self.capture_running = False
        self._restore_widgets()

    def _run_capture_thread(self):
        """在子线程中启动截图"""
        if self.capture_running:
            gui_queue.put(("show_warning", ("提示", "截图任务正在进行中，请稍后！")))
            return

        config = self._get_capture_config()
        self.capture_running = True
        self._disable_widgets()
        self.console.clear_log()
        pause_event.set()
        threading.Thread(
            target=self._start_capture,
            args=(config,),
            daemon=True
        ).start()

    def run(self):
        """运行主循环"""
        self.root.mainloop()


if __name__ == '__main__':
    setup_logging()
    app = CameraSnapshotApp()
    app.run()
