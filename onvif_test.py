# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/21 7:47
"""
from Onvif_sun import Onvif_sun
import csv

if __name__ == '__main__':

    with open('./dv.csv') as fp:
        csv_reader = csv.reader(fp)
        for ip,port in csv_reader:
            onvif_test = Onvif_sun(ip,port,'admin','admi12345')
            if onvif_test.content_cam():
                onvif_test.Snapshot()

