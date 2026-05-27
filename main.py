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

# 配置日志
from mylogger import setlogger

setlogger.configure_logger()
logger = logging.getLogger('camera_logger')
from capture_tk import root

if __name__ == '__main__':
    # cam1 = Camera(camera_type="computer")
    # cam1.is_water_mark = True
    # print(cam1.xm_capture())
    root.mainloop()
