# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面


"""

import csv
import logging
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, DISABLED, NORMAL
from PIL import Image, ImageTk

# 导入抽离的工具类
from utils.capture_pool import capture_pool, onvif_pool, batch_capture_computer_cameras
from utils.log_config import setup_logging
from utils.log_utils import LogWidget, gui_queue, is_capturing, is_paused, pause_event, poll_gui_queue  # noqa: F401
from utils.other_utils import open_folder, display_image, build_save_dir
from utils.tool import validate_csv_file

# 初始化日志
logger = setup_logging()


class CameraSnapshotApp:
    """摄像头批量截图图形界面主类"""

    WINDOW_TITLE = "网络摄像头截图小工具"
    WINDOW_GEOMETRY = "500x600+200+150"
    CAMERA_TYPES = ("海康", "大华", "onvif", "电脑")

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
        self.temp_ip = tk.StringVar()
        self.temp_password = tk.StringVar()

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

    # ====================== 预览图片弹窗 ======================

    def show_preview_image(self, image_path):
        """在新窗口中显示截图预览"""
        try:
            img = Image.open(image_path)
            # 计算弹窗大小，最大 800x600
            win_width = min(img.width + 40, 800)
            win_height = min(img.height + 80, 600)

            preview_win = tk.Toplevel(self.root)
            preview_win.title(f"截图预览 - {os.path.basename(image_path)}")
            preview_win.geometry(f"{win_width}x{win_height}+400+200")
            preview_win.configure(bg=self.COLOR_BG)
            preview_win.resizable(True, True)

            # 图片显示区域
            canvas_frame = tk.Frame(preview_win, bg=self.COLOR_FRAME_BG,
                                    relief="solid", bd=1)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

            canvas = tk.Canvas(canvas_frame, bg="#FAFAFA",
                               highlightthickness=0)
            canvas.pack(fill="both", expand=True, padx=5, pady=5)

            # 等比例缩放显示
            display_width = win_width - 60
            display_height = win_height - 120
            img_copy = img.copy()
            img_copy.thumbnail((display_width, display_height),
                               Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_copy)
            canvas.delete("all")
            x = (display_width - img_copy.width) // 2
            y = (display_height - img_copy.height) // 2
            canvas.create_image(max(x, 0), max(y, 0), anchor="nw",
                                image=photo)
            canvas.image = photo  # 保留引用

            # 底部信息
            info_frame = tk.Frame(preview_win, bg=self.COLOR_BG)
            info_frame.pack(fill="x", padx=10, pady=(0, 10))

            tk.Label(
                info_frame,
                text=f"{os.path.basename(image_path)}  ({img.width}x{img.height})",
                font=("微软雅黑", 9), bg=self.COLOR_BG, fg="#555555"
            ).pack(side="left")

            tk.Button(
                info_frame, text="关闭",
                font=self.FONT_BUTTON,
                bg=self.COLOR_BUTTON, fg=self.COLOR_BUTTON_TEXT,
                relief="flat", bd=0, cursor="hand2",
                padx=15, pady=3,
                command=preview_win.destroy
            ).pack(side="right")

        except Exception as e:
            logger.error(f"预览图片失败: {e}")

    # ====================== CSV 预览功能 ======================

    def _preview_csv(self):
        """预览 CSV 文件内容"""
        csv_path = self.select_path.get()
        if not csv_path:
            gui_queue.put(("show_warning", ("提示", "请先选择 CSV 文件")))
            return

        if not csv_path.lower().endswith('.csv'):
            gui_queue.put(("show_warning", ("提示", "请选择 CSV 格式的文件")))
            return

        try:
            # 读取 CSV 文件
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                gui_queue.put(("show_warning", ("提示", "CSV 文件为空")))
                return

            headers = rows[0]
            data_rows = rows[1:]

            # 创建预览窗口
            preview_win = tk.Toplevel(self.root)
            preview_win.title(f"CSV 预览 - {os.path.basename(csv_path)}")
            preview_win.geometry("600x400+350+250")
            preview_win.configure(bg=self.COLOR_BG)
            preview_win.resizable(True, True)

            # 顶部信息
            info_frame = tk.Frame(preview_win, bg=self.COLOR_BG)
            info_frame.pack(fill="x", padx=10, pady=(10, 5))

            tk.Label(
                info_frame,
                text=f"文件: {csv_path}",
                font=("微软雅黑", 9),
                bg=self.COLOR_BG,
                fg="#555555",
                anchor="w"
            ).pack(fill="x")

            tk.Label(
                info_frame,
                text=f"共 {len(data_rows)} 条记录，{len(headers)} 列",
                font=("微软雅黑", 9, "bold"),
                bg=self.COLOR_BG,
                fg="#333333",
                anchor="w"
            ).pack(fill="x")

            # 表格区域 - 使用 Canvas 绘制带边框的表格
            tree_frame = tk.Frame(preview_win, bg=self.COLOR_FRAME_BG)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

            # 创建 Canvas 和滚动条
            canvas = tk.Canvas(tree_frame, bg='white', highlightthickness=0)
            v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=canvas.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=canvas.xview)
            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
            canvas.pack(side="left", fill="both", expand=True)

            # 计算列宽 - 根据数据内容动态调整
            col_widths = [45]  # 序号列
            for ci, col in enumerate(headers):
                # 计算该列所有数据的最大长度
                max_len = len(col)
                for row in data_rows:
                    if ci < len(row):
                        # 中文字符算2个宽度
                        cell_len = sum(2 if ord(c) > 127 else 1 for c in row[ci])
                        max_len = max(max_len, cell_len)
                col_widths.append(max(70, max_len * 7 + 24))
            total_width = sum(col_widths)
            row_height = 26

            # 计算画布大小
            canvas_width = total_width + 4
            canvas_height = (len(data_rows) + 1) * row_height + 4
            canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

            # 绘制表头
            x = 2
            y = 2
            for ci, (col_name, cw) in enumerate(zip(['序号'] + headers, col_widths)):
                canvas.create_rectangle(x, y, x + cw, y + row_height,
                                        outline='#999999', fill='#E8E8E8')
                canvas.create_text(x + cw // 2, y + row_height // 2,
                                   text=col_name, font=('微软雅黑', 9, 'bold'),
                                   anchor='center')
                x += cw

            # 绘制数据行
            y += row_height
            for ri, row in enumerate(data_rows):
                x = 2
                # 补齐行
                padded_row = row + [''] * (len(headers) - len(row))
                values = [str(ri + 1)] + padded_row[:len(headers)]
                for ci, (val, cw) in enumerate(zip(values, col_widths)):
                    # 绘制单元格边框（留1像素内边距避免重叠）
                    canvas.create_rectangle(x + 1, y + 1, x + cw - 1, y + row_height - 1,
                                            outline='#CCCCCC', fill='white')
                    # 文字居中显示
                    canvas.create_text(x + cw // 2, y + row_height // 2,
                                       text=val, font=('微软雅黑', 9),
                                       anchor='center')
                    x += cw
                y += row_height

            # 底部关闭按钮
            btn_frame = tk.Frame(preview_win, bg=self.COLOR_BG)
            btn_frame.pack(fill="x", padx=10, pady=10)

            tk.Button(
                btn_frame,
                text="关闭",
                font=self.FONT_BUTTON,
                bg=self.COLOR_BUTTON,
                fg=self.COLOR_BUTTON_TEXT,
                relief="flat", bd=0,
                cursor="hand2",
                padx=20, pady=5,
                command=preview_win.destroy
            ).pack(side="right")

        except UnicodeDecodeError:
            gui_queue.put(("show_error", ("错误", "CSV 文件编码错误，请使用 UTF-8 编码")))
        except Exception as e:
            gui_queue.put(("show_error", ("错误", f"读取 CSV 文件失败: {str(e)}")))

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
            "大华": "dahua",
            "onvif": "onvif",
            "电脑": "computer"
        }
        camera_type = camera_type_map.get(client_type, "hik")

        def do_capture():
            try:
                from lib.Camera import Camera
                logger.info(f"临时截图 - IP: {ip}, 类型: {client_type}")
                result = Camera(ip=ip, password=password, camera_type=camera_type).capture()
                status, info = result
                if status == 1:
                    logger.info(f"临时截图成功: {info}")
                    # 弹窗显示截图
                    self.root.after(0, lambda: self.show_preview_image(info))
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

        # 水印复选框
        watermark_check = tk.Checkbutton(
            type_frame, text="添加时间水印",
            variable=self.watermark_var,
            font=self.FONT_LABEL,
            bg=self.COLOR_BG,
            activebackground=self.COLOR_BG,
            selectcolor="white"
        )
        watermark_check.pack(side="left")

        # ---- CSV 文件路径 ----
        csv_row = tk.Frame(content_frame, bg=self.COLOR_BG)
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
        ttk.Separator(content_frame, orient='horizontal').pack(fill="x", padx=20, pady=10)

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
        if self.numberChosen.get() == '电脑':
            self.csv_entry['state'] = 'disable'
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
        global is_paused
        if is_paused:
            # 继续
            is_paused = False
            pause_event.set()
            self.pause_button.config(text='⏸ 暂停', bg="#F0AD4E")
            logger.info("截图任务已恢复")
        else:
            # 暂停
            is_paused = True
            pause_event.clear()  # 清除事件，使 wait() 阻塞
            self.pause_button.config(text='▶ 继续', bg="#5CB85C")
            logger.info("截图任务已暂停，等待当前任务完成后暂停")

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

            # 校验摄像头类型
            if not client_type:
                gui_queue.put(("show_warning", ("提示", "请选择摄像头类型")))
                return

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

            # 电脑摄像头直接截图
            if client_type == '电脑':
                result = batch_capture_computer_cameras(folder_path=self.save_dir)
                logger.info(f"电脑多摄像头批量截图结果：{result}")
                for cam_index, (status, file_path) in result.items():
                    if status == 1:
                        logger.debug(f"显示摄像头{cam_index}的截图:{file_path}")
                        self.root.after(0, lambda fp=file_path: self.show_preview_image(fp))
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
