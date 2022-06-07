# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/21 7:47
"""
from onvif_sun import Onvif_sun
import csv

if __name__ == '__main__':

    with open(r'd:\监控截图\csv_file\xiandai.csv') as fp:
        csv_reader = csv.reader(fp)
        for line in csv_reader:
            ip = line[0]
            port = 80
            onvif_test = Onvif_sun(ip,port,'admin','admin123')
            if onvif_test.content_cam():
                onvif_test.Snapshot()

