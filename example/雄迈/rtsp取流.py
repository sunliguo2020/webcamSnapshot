# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 9:56
"""
import os
from datetime import datetime
from urllib.parse import quote

import cv2


def xm_cv2_cap(ip=None, user='admin', password='shiji123'):
    """
    通过雄迈rtsp截图
    @param password:
    @param user:
    @param ip:
    @return:
    """
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 保存的目录
    folder = f"{date_str}"
    if not os.path.exists(folder):
        os.makedirs(folder)
    # 截图文件名
    file_name = f"{ip}_{user}_{password}_{datetime_str}.jpg"

    file_full_path = os.path.join(folder, file_name)

    # 雄迈rtsp 格式 0.sdp主码流 1次码流
    # quote 处理密码中的特殊字符如@
    rtsp_url = f"rtsp://{ip}:554/user={user}&password={quote(password)}&channel=1&stream=0.sdp?real_stream"
    print("rtsp_url：", rtsp_url)
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return
    ret, frame = cap.read()

    cv2.imencode('.jpg', frame)[1].tofile(file_full_path)

    cv2.destroyAllWindows()
    cap.release()


if __name__ == '__main__':
    xm_cv2_cap(ip="172.30.188.55", password='dcxx188@55')
