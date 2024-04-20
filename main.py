# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 21:07
"""
import logging

# 配置日志
from mylogger.setlogger import configure_logger

configure_logger()

from capture_tk import root

# logger = logging.getLogger('camera_logger')


def main():
    print('Hello World!')


if __name__ == '__main__':
    # main()
    # logger.warning('我是谁')
    # cam1 = Camera(camera_type="computer")
    # cam1.is_water_mark = True
    # print(cam1.capture())
    root.mainloop()
