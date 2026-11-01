"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-06-16 12:14
图形界面生成exe文件
"""
import os
import subprocess
import sys
import time

project_dir = os.path.dirname(os.path.abspath(__file__))

# 打包 main.py（推荐，因为 main.py 中先配置了日志再导入 capture_tk）
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "-F",
        "-w",
        "-i",
        os.path.join(project_dir, "cam_capture.ico"),
        "--add-data",
        f'{os.path.join(project_dir, "logging.conf")};.',
        "--paths",
        project_dir,
        "-n",
        f'摄像头批量截图_{time.strftime("%Y%m%d", time.localtime())}',
        os.path.join(project_dir, "main.py"),
    ],
    cwd=project_dir,
    check=True,
)

# 如果需要直接打包 capture_tk.py，取消下面的注释
# os.system(f'pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图_{time.strftime("%Y%m%d", time.localtime())}')
