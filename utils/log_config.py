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

    日志文件始终创建在 exe 所在目录（或当前工作目录）的 logs/ 下
    """
    # 获取 exe 所在目录（而不是当前工作目录）
    if getattr(sys, 'frozen', False):
        # 打包环境：exe 所在目录
        app_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：项目根目录
        app_dir = os.getcwd()

    # 确保 logs 目录在 exe 所在目录下创建
    logs_dir = os.path.join(app_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # 先清除 camera_logger 的所有已有 handlers（防止 mylogger 等模块提前配置了其他路径）
    camera_logger = logging.getLogger('camera_logger')
    for handler in list(camera_logger.handlers):
        camera_logger.removeHandler(handler)

    log_file = os.path.join(logs_dir, 'camera.log')

    # 直接使用 dictConfig 配置，避免 logging.conf 中相对路径的问题
    log_config = {
        'version': 1,
        'formatters': {
            'simpleFormatter': {
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            }
        },
        'handlers': {
            'consoleHandler': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'simpleFormatter',
                'stream': 'ext://sys.stdout',
            },
            'fileHandler': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'simpleFormatter',
                'filename': log_file,
                'when': 'D',
                'interval': 1,
                'backupCount': 30,
                'encoding': 'utf-8',
            }
        },
        'loggers': {
            'camera_logger': {
                'level': 'DEBUG',
                'handlers': ['consoleHandler', 'fileHandler'],
                'propagate': False,
            }
        }
    }

    logging.config.dictConfig(log_config)

    return logging.getLogger('camera_logger')
