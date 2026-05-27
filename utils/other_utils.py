# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2026/1/16 15:19

通用工具方法抽离 - 图片预览、打开文件夹、路径处理等
"""
import os
import time
import tkinter as tk

from PIL import ImageTk, Image


def display_image(image_path, main_window=None):
    """
    # img = Image.open("a.jpg").resize((160, 90))  # 打开图片
    # photo = ImageTk.PhotoImage(img)  # 使用ImageTk的PhotoImage方法
    # # tk.Label(master=root,image=photo).grid(row=0, column=4)
    @param main_window:
    @param image_path:
    @return:
    """
    # 1、创建Toplevel子窗口(替换Tk珠串口感）
    # 若传入主窗口，则子窗口依附于主窗口；若未传入自动关联默认主窗口
    sub_window = tk.Toplevel(main_window)
    # 设置子窗口标题（显示文件名，更容易区分）
    file_name = os.path.basename(image_path)
    sub_window.title(f"截图预览-{file_name}")

    try:
        # 打开图像文件并等比例缩放，避免窗口过大
        img = Image.open(image_path)
        # 按照比例缩放，避免窗口过大
        img.thumbnail((700, 600), Image.Resampling.LANCZOS)

        # 将 PIL 图像转换为 PhotoImage
        photo = ImageTk.PhotoImage(img)

        # 3. 创建 Label 显示图片，并强制保留图片引用（避免垃圾回收导致图片不显示）
        label = tk.Label(sub_window, image=photo)
        label.image = photo  # 关键：保留引用
        label.pack(padx=10, pady=10)  # 增加内边距，优化显示效果

        # 4. 可选：设置子窗口大小自适应图片，或固定大小
        sub_window.geometry(f"{img.width + 20}x{img.height + 20}")  # 20是内边距补偿

    except Exception as e:
        # 异常处理：图片打开失败时，在子窗口显示错误信息
        error_label = tk.Label(sub_window, text=f"图片打开失败：{str(e)}", fg="red")
        error_label.pack(padx=20, pady=20)
        sub_window.title(f"错误 - {file_name}")

        # 5. 关键：无需在子窗口调用 mainloop()，由主窗口统一管理，避免阻塞
        # 若你的程序无主窗口（纯命令行），可注释下面的代码，并在函数末尾添加 sub_window.mainloop()
    return sub_window


def open_folder(jpg_dir, logger, gui_queue):
    """
    打开截图的文件夹
    Returns:

    """
    logger.debug(f'要打开截图保存路径：{jpg_dir}')
    if not jpg_dir or not os.path.exists(jpg_dir):
        gui_queue.put(("show_warning", ("提示", "截图目录不存在!")))
        return
    try:
        if os.name == 'nt':  # windows
            os.startfile(jpg_dir)
        else:
            import subprocess
            subprocess.run(['xdg-open' if os.name == 'posix' else 'open', jpg_dir])
    except Exception as e:
        gui_queue.put(("show_error", ("打开失败", f"无法打开目录：{str(e)}")))


def build_save_dir(client_type, csv_file, base_dir):
    """
    构建保存文件的目录
    截图保存路径 或 保存截图的文件夹默认是 csv文件名 + 当前日期
    保存截图的文件夹默认是 csv文件名 + 当前日期,设置保存截图的文件夹的默认值
    @param client_type: 摄像头类型（"电脑" 或其他）
    @param csv_file: CSV文件路径
    @param base_dir: 用户指定的基础目录（可为空）
    @return: 完整的保存目录路径
    """
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
