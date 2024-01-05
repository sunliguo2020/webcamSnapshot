# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 20:55
"""
import logging
import logging.config


def configure_logger():
    """
    配置日志

    @return:
    """
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
