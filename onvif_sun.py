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
import socket
import time
import requests
import zeep
from onvif import ONVIFCamera
from requests.auth import HTTPDigestAuth

import csv


def zeep_pythonvalue(self, xmlvalue):
    return xmlvalue



class Onvif_sun(object):
    """

    """

    def __init__(self, ip, port=80, username="admin", password="admin"):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue
        # print(self.password)
        self.save_path = "./{}_{}_{}_onvif_{}.jpg". \
            format(self.ip, self.password, self.port, str(time.strftime("%Y%m%d%H%M%S", time.localtime())))  # 截图保存路径

    # python实战练手项目---使用socket探测主机开放的端口 | 酷python
    # http://www.coolpython.net/python_senior/miny_pro/find_open_port.html
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
            print(f'{self.ip}:{self.port} 打开失败！')
            return False
        else:
            print(f'{self.ip}:{self.port} {self.password} 打开！')
        try:
            print("正在创建媒体")
            self.mycam = ONVIFCamera(self.ip, self.port, self.username, self.password)
            self.media = self.mycam.create_media_service()  # 创建媒体服务
            self.media_profile = self.media.GetProfiles()[0]  # 获取配置信息
            # self.ptz = self.mycam.create_ptz_service()  # 创建控制台服务
            flag = True
        except Exception as e:
            print("发生错误!", e)
            flag = False

        return flag

    def Snapshot(self):
        """
        截图
        :return:
        """
        res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})
        print("response:")
        response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password), timeout=1)
        print(f'正在保存{self.ip}的截图')
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

    with open('./txt/dv.txt') as f:
        csv_reader = csv.reader(f)
        count = 0
        for ip, port, user, password in csv_reader:

            count = count + 1

            print(count, ip, ":")
            if count < 0:
                continue

            result = Onvif_sun(ip, port, user, password)  # ip,port,user,password
            if result.content_cam():
                result.Snapshot()
            else:
                print('error')
