# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/2/17 22:31
"""
from dahua_cv2 import dahua_cv2
import csv
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from threading import Thread

if __name__ == '__main__':
    ip_passwd_list=[]
    pool = Pool()
    with open('./csv/shixunlou.csv') as fp:

        csv_reader = csv.reader(fp)
        with ThreadPoolExecutor(10) as t:
            for ip,password in csv_reader:
                # t = Thread(target=dahua_cv2,args=(ip,password))
                t.submit(dahua_cv2,ip,password)

