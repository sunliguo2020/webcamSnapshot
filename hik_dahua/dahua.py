# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/2/17 22:31
"""
import csv
from concurrent.futures import ThreadPoolExecutor

from dahua_cv2 import dahua_cv2

if __name__ == '__main__':

    with open('./test.csv') as fp:

        csv_reader = csv.reader(fp)
        with ThreadPoolExecutor(10) as t:
            for ip, password in csv_reader:
                t.submit(dahua_cv2, ip, password)
