# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-06-16 12:14
图形界面生成exe文件
"""
import os
import sys
import time

# 判断是否在 PyInstaller 打包的环境中运行
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# 打包 main.py（推荐，因为 main.py 中先配置了日志再导入 capture_tk）
os.system(
    f'pyinstaller --clean -F -w --noupx '
    f'-i cam_capture.ico '
    f'--add-data "logging.conf;." '
    f'-n 摄像头批量截图_{time.strftime("%Y%m%d", time.localtime())} '
    f'main.py'
)

# 如果需要直接打包 capture_tk.py，取消下面的注释
# os.system(f'pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图_{time.strftime("%Y%m%d", time.localtime())}')
