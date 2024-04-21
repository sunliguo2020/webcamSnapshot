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


def cv2_cap(ip=None, user='admin', password='shiji123'):
    """

    @param password:
    @param user:
    @param ip:
    @return:
    """
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    floder = f"{date_str}"
    if not os.path.exists(floder):
        os.makedirs(floder)

    file_name = f"{ip}_{user}_{password}_{datetime_str}.jpg"

    file_full_path = os.path.join(floder, file_name)

    # 0.sdp主码流 1次码流
    rtsp_url = f"rtsp://{ip}:554/user={user}&password={quote(password)}&channel=1&stream=0.sdp?real_stream"
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return
    ret, frame = cap.read()
    # while ret:
    #     ret, frame = cap.read()
    #     cv2.imshow("frame", frame)
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    cv2.imencode('.jpg', frame)[1].tofile(file_full_path)

    cv2.destroyAllWindows()
    cap.release()


if __name__ == '__main__':
    cv2_cap(ip="172.30.189.78")
