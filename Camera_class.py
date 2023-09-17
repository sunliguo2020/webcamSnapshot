# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-25 7:48
"""
import logging
import os
import time

logging.basicConfig(filename='Camera.log', level=logging.DEBUG)
import cv2

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;50"


class Camera:
    """
    一个摄像头的类
    可以捕捉支持rtsp协议的网络摄像头，或者是电脑的摄像头

    """

    def __init__(self, ip=None, password='admin', camera_type='hik', file_name=None,
                 folder_path=None, is_water_mark=True):
        self.ip = ip
        self.password = password
        self.camera_type = camera_type
        self.frame = None
        self.is_water_mark = is_water_mark

        if self.camera_type == 'dahua':
            self.path = f"rtsp://admin:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0"
        elif self.camera_type == 'hik':
            self.path = f"rtsp://admin:{self.password}@{self.ip}:554/h264/ch34/main/av_stream"
        elif self.camera_type == 'computer':
            self.path = 0
        else:
            raise ValueError("camera type error!")

        # 截图的保存文件名是ip_password_camear_type_strftime.jpg
        if file_name:
            self._file_name = file_name
        else:
            self._file_name = None

        if folder_path:
            self.folder_path = folder_path
        else:
            self.folder_path = time.strftime('%Y-%m-%d', time.localtime())

        # 默认保存的目录是 年份-月份-日期
        if not os.path.isdir(self.folder_path):
            os.mkdir(self.folder_path)

        self.file_full_path = os.path.join(self.folder_path, self.file_name)

    def capture(self):
        """
        截图
        :return:
        """
        # opencv自带的VideoCapture()函数定义摄像头对象，其参数0表示第一个摄像头
        cam = cv2.VideoCapture(self.path)
        if not cam.isOpened():
            raise IOError("视频对象读取失败!~")
        ret, self.frame = cam.read()

        # 添加水印信息
        if self.is_water_mark:
            self.watermark()

        # 文件路径中不包含中文
        # cv2.imwrite(self.file_name, frame)  # 存储为图像
        img_write = cv2.imencode(".jpg", self.frame)[1].tofile(self.file_full_path)
        logging.debug(f"img_write 类型：{img_write}")
        cam.release()
        cv2.destroyAllWindows()

    def watermark(self):
        """
        截图添加水印信息：图片的名字
        :param frame:
        :return:
        """
        # 添加水印信息
        text_watermark_x = 0
        text_watermark_y = 200
        text = self.file_name.replace('.jpg', '')
        font_face = cv2.FONT_HERSHEY_SIMPLEX  # 字体
        line_type = cv2.LINE_AA
        font_scale = 2  # 比例因子
        thickness = 2  # 线的粗细

        retval, base_line = cv2.getTextSize(text, fontFace=font_face, fontScale=font_scale, thickness=thickness)

        img_width = self.frame.shape[1]
        img_hight = self.frame.shape[0]

        text_width = retval[0]

        # 如果文字的宽带大于图片的宽度，则缩小比例因子
        if text_width > img_width:
            font_scale = font_scale * (img_width / text_width) * 0.8
            text_watermark_y = int(img_width * 0.1)  # 水印的新y坐标

        self.frame = cv2.putText(self.frame, text, (text_watermark_x, text_watermark_y),
                                 font_face, font_scale,
                                 (100, 255, 0),
                                 thickness, line_type)
        # return water_mark_img

    @property
    def file_name(self):
        """
        截图文件名
        :return:
        """
        if self._file_name:
            return self._file_name
        else:
            return f"{self.ip}_{self.password}_{self.camera_type}_" \
                   f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}.jpg"

    @file_name.setter
    def file_name(self, value):
        self._file_name = value


if __name__ == '__main__':
    # cam1 = Camera('192.168.1.111', password='FYKWXY', camera_type='hik')
    # cam1.capture()
    # print(dir(cam1))
    # print(id(cam1.ip))
    # print(id('192.168.1.111'))
    cam1 = Camera('192.168.1.1', camera_type='computer')
    print(dir(cam1))
    cam1.capture()
    print(type(cam1.frame))  # <class 'numpy.ndarray'>
    # 保存numpy.ndarray 保存为图片

    # from PIL import Image
    # im = Image.fromarray(cam1.frame)
    # im.save("your_file.jpg")
