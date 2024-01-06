# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-25 7:48
"""
import errno
import logging
import os
import time
import tkinter as tk

import cv2
from PIL import ImageTk, Image

from utils.tool import portisopen

logger = logging.getLogger('camera_logger')

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;50"


def display_image(image_path):
    """
    显示截图
    @param image_path:
    @return:
    """
    root = tk.Tk()
    root.title("显示截图")

    # 打开图像文件
    img = Image.open(image_path)

    # 将图像调整为合适的大小
    # img.thumbnail((500, 600), Image.ANTIALIAS)
    img.thumbnail((700, 600))

    # 将 PIL 图像转换为 PhotoImage
    photo = ImageTk.PhotoImage(img)

    # 创建 Label 组件以显示图像
    label = tk.Label(root, image=photo)
    label.image = photo  # 保持对图片的引用，避免被垃圾回收

    # 将 Label 放置到窗口中
    label.pack()
    root.mainloop()


# 调用函数显示图片
# display_image("path/to/your/saved/screenshot.png")  # 替换为实际的截图路径

class Camera:
    """
    一个摄像头的类
    可以捕捉支持rtsp协议的网络摄像头，或者是电脑的摄像头
    """

    def __init__(
            self,
            # ip地址
            ip=None,
            # 默认密码
            password="admin",
            # 摄像头类型
            camera_type="hik",
            # 保存截图的文件名
            file_name=None,
            # 截图保存路径
            folder_path=None,
            # 是否添加水印
            is_water_mark=True,
    ):
        """
        初始化摄像头
        @param ip:
        @param password:
        @param camera_type:
        @param file_name:
        @param folder_path:
        @param is_water_mark:
        """
        self.ip = ip or ""
        self.password = password
        self.camera_type = camera_type
        self.frame = None
        self.is_water_mark = is_water_mark

        # 截图的保存文件名是ip_password_camear_type_strftime.jpg
        self._file_name = file_name or None

        self.folder_path = folder_path or time.strftime("%Y-%m-%d", time.localtime())

        # 默认保存的目录是 年份-月份-日期
        if not os.path.exists(self.folder_path):
            try:
                os.makedirs(self.folder_path)
            except OSError as e:
                if e.errno != errno.EEXIST:  # 如果不是 "文件已存在" 错误
                    raise  # 如果不是文件已存在的错误，则抛出异常
        else:
            logger.debug(f"目录 {self.folder_path} 已经存在")

        self.file_full_path = os.path.join(self.folder_path, self.file_name)

    def capture(self):
        """
        截图
        返回 1 表示截图成功。
        返回 0 表示未进行截图操作。
        返回 -1、-2 或其他负数表示截图失败或出现错误。
        :return: 返回1 截图成功
        假设这个函数返回了一个元组（status, file_path）
        """
        # 检查摄像头是否可用
        if not self.check_camera():
            logger.debug(f"{self.ip} 554 端口没有打开或者网络不通")
            return -1, None
        try:
            # 获取摄像头视频帧
            cam = cv2.VideoCapture(self.camera_path)
            if not cam.isOpened():
                raise RuntimeError("视频对象读取失败")

            ret, self.frame = cam.read()

            # 添加水印
            if self.is_water_mark:
                self.watermark()

            # 保存截图
            # cv2.imencode(保存格式,保存图片)[1].tofile('保存路径')
            # cv2.imwrite(self.file_full_path, self.frame)
            # 保存截图
            cv2.imencode('.jpg', self.frame)[1].tofile(self.file_full_path)
            # 判断是否保存成功
            if os.path.isfile(self.file_full_path):
                logger.debug(f'截图成功,文件路径：{self.file_full_path}')
                return 1, self.file_full_path
            else:
                logger.debug('截图保存失败！')
                return -2, None

        except Exception as e:
            logger.error(f"捕获图像时发生错误：{e}")
            return -3, None

        finally:
            # 释放资源
            if 'cam' in locals() and cam and cam.isOpened():
                cam.release()
            cv2.destroyAllWindows()

    def check_camera(self):
        """
        检查摄像头是否可用
        """
        if self.camera_path != 0 and not portisopen(self.ip, 554):
            return False
        return True

    def watermark(self):
        """
        截图添加水印信息：图片的名字
        :param frame:
        :return:
        """
        # 添加水印信息
        text_watermark_x = 0
        text_watermark_y = 200
        text = self.file_name.replace(".jpg", "")
        font_face = cv2.FONT_HERSHEY_SIMPLEX  # 字体
        line_type = cv2.LINE_AA
        font_scale = 2  # 比例因子
        thickness = 2  # 线的粗细

        retval, base_line = cv2.getTextSize(
            text, fontFace=font_face, fontScale=font_scale, thickness=thickness
        )

        img_width = self.frame.shape[1]
        img_hight = self.frame.shape[0]

        text_width = retval[0]

        # 如果文字的宽带大于图片的宽度，则缩小比例因子
        if text_width > img_width:
            font_scale = font_scale * (img_width / text_width) * 0.8
            text_watermark_y = int(img_width * 0.1)  # 水印的新y坐标

            # 声明文字的坐标位置和参数
        text_position = (text_watermark_x, text_watermark_y)
        font_color = (100, 255, 0)

        # 在图像上绘制文字水印
        self.frame = cv2.putText(
            self.frame,
            text,
            text_position,
            font_face,
            font_scale,
            font_color,
            thickness,
            line_type,
        )

    @property
    def camera_path(self):
        # camera_type 类型 dahua hik computer
        if self.camera_type == "dahua" and self.ip:
            return f"rtsp://admin:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0"
        # 电脑摄像头
        elif self.camera_type == "computer" or not self.ip:
            return 0
        # 海康威视
        elif self.camera_type == "hik" and self.ip:
            return (
                f"rtsp://admin:{self.password}@{self.ip}:554/h264/ch34/main/av_stream"
            )
        else:
            raise ValueError("camera type error!only dahua hik computer")

    # @property装饰器的作用：1、让函数可以向普通遍历一样使用2、对要读取的数据进行预处理
    @property
    def file_name(self):
        """
        截图文件名
        :return:
        """
        if self._file_name:
            return self._file_name
        elif self.camera_type == "computer":
            return f"{self.camera_type}_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.jpg"
        else:
            return (
                f"{self.ip}_{self.password}_{self.camera_type}_"
                f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}.jpg"
            )

    @file_name.setter
    def file_name(self, value):
        self._file_name = value


if __name__ == "__main__":
    # # 测试海康摄像头
    # cam1 = Camera('192.168.1.111', password='FYKWXY', camera_type='hik')
    # # print(cam1)
    # result = cam1.capture()
    # print(result)

    cam1 = Camera(camera_type="computer")
    cam1.is_water_mark = True
    print(cam1.capture())
