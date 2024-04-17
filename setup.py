# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-05 21:08
"""
from setuptools import setup, find_packages

setup(
    name='camera',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/sunliguo/camera',
    license='MIT',
    author='sunliguo',
    author_email='sunliguo2006@qq.com',
    description='网络摄像头截图工具',
    install_requires=[
        'opencv-python',
        'numpy',
        'Pillow',
        'pyyaml',
        'tqdm',
        'tensorflow',
        'tensorflow-gpu',
        'tensorflow-estimator',
        'tensorflow-probability',
        'tensorflow-datasets',
        'tensorflow-estimator', ],
    entry_points={
        "console_scripts": [
            "camera=camera.__main__:main",
        ]

    }
)
