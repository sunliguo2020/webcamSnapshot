# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-20 21:14
"""
import os
import sys

# 假设当前脚本在项目根目录下的某个子目录中
# 获取当前脚本的绝对路径
current_script_dir = os.path.abspath(os.path.dirname(__file__))

# 获取项目根目录的路径，这里假设项目根目录是当前脚本目录的上级目录
project_root_dir = os.path.dirname(current_script_dir)

# 将项目根目录添加到sys.path中
sys.path.append(project_root_dir)
