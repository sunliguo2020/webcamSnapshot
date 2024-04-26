# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 21:07
"""
import logging

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
