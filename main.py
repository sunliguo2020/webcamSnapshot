# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 21:07
"""
import logging
import os
import sys

# 判断是否在 PyInstaller 打包的环境中运行
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，配置文件在 _MEIPASS 目录下
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# 配置日志（使用绝对导入）
from utils.log_config import setup_logging

logger = setup_logging()

# 导入 GUI 应用
import capture_tk

if __name__ == '__main__':
    app = capture_tk.CameraSnapshotApp()
    app.run()
