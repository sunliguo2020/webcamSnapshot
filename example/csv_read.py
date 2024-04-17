# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-01-10 17:35
"""
import csv

with open('../txt/test.csv', 'r', encoding='utf-8') as fp:
    # csv.DictReader(fp)
    for row in csv.DictReader(fp):
        print(row)
