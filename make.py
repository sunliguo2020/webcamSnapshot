# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-06-16 12:14
图形界面生成exe文件
"""
import os
import time

# os.system(f'pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图_{time.strftime("%Y%m%d", time.localtime())}')
os.system(f'pyinstaller -F -w -i cam_capture.ico 录像机截图图形界面.py -n 录像机截图_{time.strftime("%Y%m%d", time.localtime())}')