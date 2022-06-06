# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2021/6/12 15:33
"""
import urllib.request

file = urllib.request.urlopen('http://www.baidu.com')
data = file.read()
#print(data)
print(file.info())
print(file.getcode())