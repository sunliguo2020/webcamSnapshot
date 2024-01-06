# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 20:55
"""
import logging
import logging.config
import os

def configure_logger():
    """
    配置日志

    @return:
    """
    # 检查日志文件是否存在，不存在则创建
    log_file = 'log/camera.log'
    if not os.path.isfile(log_file):
        dir_name = os.path.dirname(log_file)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)

            
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
                'filename': 'log/camera.log',
                'formatter': 'default',
                'encoding': 'utf-8'
            },
            # You can add more handlers if needed
        },
        'loggers': {
            'camera_logger': {
                'level': 'DEBUG',
                'handlers': ['file_handler'],
                'propagate': False,
            }
        }
    }

    logging.config.dictConfig(log_config)


configure_logger()
if __name__ == '__main__':
    # 配置 logger
    configure_logger()
