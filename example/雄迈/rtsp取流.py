# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 9:56
"""
import cv2


def cv2_cap(ip=None):
    """

    @param ip:
    @return:
    """
    # 0.sdp主码流 1次码流
    rtsp_url = f"rtsp://{ip}:554/user=admin&password=&channel=1&stream=0.sdp?"
    cap = cv2.VideoCapture(rtsp_url)
    ret, frame = cap.read()
    while ret:
        ret, frame = cap.read()
        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
    cap.release()


if __name__ == '__main__':
    cv2_cap(ip="172.30.189.78")
