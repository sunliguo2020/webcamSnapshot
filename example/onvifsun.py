# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2021/11/23 12:56

onvif抓图大致流程：
1、发送GetSnapshotUri获取到对应token的抓图路径。
2、通过get方式请求这个路径
3、返回的数据就是图片的数据，直接保存下来
我的做法就是用onvif获取到抓图路径，然后用http直接下载下来即可
"""

import csv
import logging

logging.basicConfig(filename='onvif.log',
                    level=logging.INFO,
                    filemode='a',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')

import os
import socket
import time
import requests
from onvif import ONVIFCamera
from requests.auth import HTTPDigestAuth


class OnvifSun(object):
    """
    onvif协议的实现
    """

    def __init__(self, ip='192.168.1.1', port=80, username="admin", password="admin", base_dir=''):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port

        # 保存截图的目录  运行程序的日期为目录名
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        pic_dir = os.path.join(base_dir, time.strftime('%Y-%m-%d', time.localtime()))

        if not os.path.isdir(pic_dir):
            os.makedirs(pic_dir)
        logging.debug(f"保存截图的目录:{pic_dir}")

        self.file_name = "{}_{}_{}_onvif_{}.jpg". \
            format(self.ip, self.password, self.port, str_time)

        self.save_path = os.path.join(pic_dir, self.file_name)  # 截图保存路径

    def portisopen(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        state = sock.connect_ex((ip, port))
        if 0 == state:
            # print("port is open")
            return True
        else:
            # print("port is closed")
            return False

    def content_cam(self):
        """
        链接相机地址
        :return:
        """
        flag = ""
        if not self.portisopen(self.ip, int(self.port)):
            logging.info(f'{self.ip}:{self.port} 打开失败！')
            return False
        else:
            logging.debug(f'{self.ip}:{self.port} {self.password} 打开！')
        try:
            logging.info(f"{self.ip}正在创建媒体")
            self.mycam = ONVIFCamera(self.ip, self.port, self.username, self.password)
            self.media = self.mycam.create_media_service()  # 创建媒体服务
            self.media_profile = self.media.GetProfiles()[0]  # 获取配置信息
            # self.ptz = self.mycam.create_ptz_service()  # 创建控制台服务
            flag = True
        except Exception as e:
            logging.info(f"发生错误!{e}")
            flag = False

        return flag

    def Snapshot(self):
        """
        截图
        :return:
        """
        try:
            res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})
            response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password), timeout=1)
        except Exception as e:
            logging.info(f'try to requests.get {e}')
        else:
            logging.info(f'正在保存{self.ip}的截图')
            with open(self.save_path, 'wb') as fp:  # 保存截图
                fp.write(response.content)

    def get_presets(self):
        """
        获取预置点列表
        :return:预置点列表--所有的预置点
        """
        presets = self.ptz.GetPresets({'ProfileToken': self.media_profile.token})  # 获取所有预置点,返回值：list
        return presets

    def goto_preset(self, presets_token: int):
        """
        移动到指定预置点
        :param presets_token: 目的位置的token，获取预置点返回值中
        :return:
        """
        try:
            self.ptz.GotoPreset(
                {'ProfileToken': self.media_profile.token, "PresetToken": presets_token})  # 移动到指定预置点位置
        except Exception as e:
            print(e)

    def zoom(self, zoom: str, timeout: int = 0.1):
        """
        变焦
        :param zoom: 拉近或远离
        :param timeout: 生效时间
        :return:
        """
        request = self.ptz.create_type('ContinuousMove')
        request.ProfileToken = self.media_profile.token
        request.Velocity = {"Zoom": zoom}
        self.ptz.ContinuousMove(request)
        time.sleep(timeout)
        self.ptz.Stop({'ProfileToken': request.ProfileToken})


if __name__ == "__main__":

    # csv文件格式 ip,port,username,password
    csv_file = r'./txt/test.csv'
    base_dir = r'd:\监控截图'
    row_count = 0

    with open(csv_file) as fp:
        csv_reader = csv.reader(fp)
        for line in csv_reader:
            row_count += 1
            ip, port, username, password = line[:4]

            print(row_count, ip, port)

            onvif_test = OnvifSun(ip, port, 'admin', password, base_dir=base_dir)
            if onvif_test.content_cam():
                logging.info(f'开始截图{ip}')
                onvif_test.Snapshot()
            else:
                logging.info(f'{ip}:链接相机失败')
