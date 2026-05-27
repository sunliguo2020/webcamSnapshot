# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2026-05-27

日志配置模块 - 从 logging.conf 文件加载日志配置
支持 PyInstaller 打包环境和开发环境
"""
import logging.config
import os
import sys


def setup_logging():
    """
    初始化日志配置
    在 PyInstaller 打包环境中，配置文件在 sys._MEIPASS 目录下
    在开发环境中，配置文件在当前目录
    """
    os.makedirs("logs", exist_ok=True)

    # 判断是否在 PyInstaller 打包的环境中运行
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 如果 logger 尚未配置，则从文件配置
    if not logging.getLogger('camera_logger').handlers:
        log_config_path = os.path.join(base_path, 'logging.conf')
        if os.path.exists(log_config_path):
            logging.config.fileConfig(log_config_path)
        else:
            # 如果 logging.conf 不存在，使用基本配置
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler('logs/camera.log', encoding='utf-8')
                ]
            )

    return logging.getLogger('camera_logger')
