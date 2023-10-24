# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/18 18:54

统计下载的图片中包含的摄像头的密码，也就是正确的密码

先统计出文件名，用"_"分割后，得到ip地址，密码，时间等信息,保存为csv文件。

"""
import csv
import os

# 要统计的目录
dir_name = r'D:\睿智\监控截图\现代中学\2023-05-30'

with open("ip_pass.csv", 'w', newline='') as fp:
    csv_write = csv.writer(fp)
    csv_rows = []

    for root, dirs, files in os.walk(dir_name):
        for file in files:
            print(file.split('_'))
            csv_rows.append(file.split("_"))

    csv_write.writerows(csv_rows)
