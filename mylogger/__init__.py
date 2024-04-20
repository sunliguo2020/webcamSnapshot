# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-20 17:46
"""
import logging

from .setlogger import configure_logger

configure_logger()
# 配置全局使用的logger对象
logger = logging.getLogger("camera_logger")