# -*- coding: utf-8 -*-
"""
项目全局logger配置
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 20:55
"""
import logging
import logging.config
import os
import sys


def configure_logger():
    """
    配置日志
    注意：此函数可能在 setup_logging() 之前被调用，
    但最终日志路径由 utils/log_config.py 中的 setup_logging() 统一管理。
    这里仅做基础配置，避免创建多余的 log 目录。

    @return:
    """
    # 使用 exe 所在目录（或当前工作目录）的 logs/ 目录
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.getcwd()

    log_file = os.path.join(app_dir, 'logs', 'camera.log')

    if not os.path.isfile(log_file):
        dir_name = os.path.dirname(log_file)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
    # 日志配置
    log_config = {
        'version': 1,
        'formatters': {
            'default': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            }
        },
        'handlers': {
            'file_handler': {
                'class': 'logging.FileHandler',
                'filename': log_file,
                'formatter': 'default',
                'encoding': 'utf-8'
            },
            'console_handler': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            }
            # You can add more handlers if needed
        },
        'loggers': {
            'camera_logger': {
                'level': 'DEBUG',
                'handlers': ['file_handler', 'console_handler'],
                'propagate': False,
            }
        }
    }

    logging.config.dictConfig(log_config)


if __name__ == '__main__':
    # 配置 logger
    configure_logger()
    logger = logging.getLogger('camera_logger')
    logger.debug('debug')
