# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 12:01
"""
from OnvifClient import OnvifClient
from utils.tool import get_cam_list

if __name__ == '__main__':
    for item in get_cam_list('../txt/dv.csv'):
        print(item)
        onvif_client = OnvifClient(ip=item['ip'],
                                   port=item['port'],
                                   username=item['username'],
                                   password=item['password'])
        onvif_client.Snapshot()
