"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-06-16 12:14
图形界面生成exe文件
"""
import os
import subprocess
import sys
import time

project_dir = os.path.dirname(os.path.abspath(__file__))

def select_build_mode():
    """Prompt for a PyInstaller build mode."""
    while True:
        print("请选择打包模式：")
        print("1. 单文件版（运行时会解压依赖）")
        print("2. 目录版（推荐，需交付整个文件夹）")
        choice = input("请输入 1 或 2: ").strip()
        if choice == "1":
            return "--onefile", "单文件版"
        if choice == "2":
            return "--onedir", "目录版"
        print("输入无效，请输入 1 或 2。\n")


build_option, build_suffix = select_build_mode()

subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        build_option,
        "--noupx",
        "-w",
        "-i",
        os.path.join(project_dir, "cam_capture.ico"),
        "--paths",
        project_dir,
        "-n",
        (
            f'摄像头批量截图_'
            f'{time.strftime("%Y%m%d", time.localtime())}_{build_suffix}'
        ),
        os.path.join(project_dir, "main.py"),
    ],
    cwd=project_dir,
    check=True,
)

# 如果需要直接打包 capture_tk.py，取消下面的注释
# os.system(f'pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图_{time.strftime("%Y%m%d", time.localtime())}')
