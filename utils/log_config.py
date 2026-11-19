"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2026-05-27

日志配置模块 - 配置应用日志
支持 PyInstaller 打包环境和开发环境
"""
import logging.config
import os
import re
import sys
from logging.handlers import TimedRotatingFileHandler


class DailyArchiveFileHandler(TimedRotatingFileHandler):
    """Rotate daily logs to camera-YYYY-MM-DD.log and retain old archives."""

    def rotation_filename(self, default_name):
        prefix = f"{self.baseFilename}."
        if not default_name.startswith(prefix):
            return default_name

        date_suffix = default_name[len(prefix):]
        filename, extension = os.path.splitext(self.baseFilename)
        return f"{filename}-{date_suffix}{extension}"

    def getFilesToDelete(self):
        if self.backupCount <= 0:
            return []

        directory, base_name = os.path.split(self.baseFilename)
        filename, extension = os.path.splitext(base_name)
        prefix = f"{filename}-"
        archives = []
        for entry in os.listdir(directory):
            if not entry.startswith(prefix) or not entry.endswith(extension):
                continue
            date_suffix = entry[len(prefix):-len(extension)]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_suffix):
                archives.append(os.path.join(directory, entry))

        archives.sort()
        excess_count = len(archives) - self.backupCount
        return archives[:excess_count] if excess_count > 0 else []


def setup_logging() -> logging.Logger:
    """
    初始化应用日志配置。
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

    log_file = os.path.join(logs_dir, 'camera.log')

    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
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
                'class': 'utils.log_config.DailyArchiveFileHandler',
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
