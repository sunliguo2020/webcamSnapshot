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

from lib.OnvifClient import OnvifClient
from utils.tool import is_port_open

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
    或者通过onvif协议获取rtsp的地址
    2025-12-31：
        支持：电脑多摄像头枚举、单个截图、批量截图
    """
    RTSP_PORT = 554  # RTSP默认端口

    def __init__(
            self,
            # ip地址
            ip=None,
            # 用户名
            username="admin",
            # 默认密码
            password="admin",
            # 摄像头类型
            camera_type="hik",
            # onvif port
            onvif_port=80,
            # 保存截图的文件名
            file_name=None,
            # 截图保存路径
            folder_path=None,
            # 是否添加水印
            is_water_mark=True,
            # 新增：电脑摄像头索引（默认为0，对应第一个摄像头，1对应第2个，以此类推）
            cam_index=0,
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
        #
        logger.debug(f"__init__参数:ip:{ip},"
                     f"username:{username},"
                     f"password:{password},"
                     f"onvif_port:{onvif_port},"
                     f"cam_index:{cam_index}")

        self.onvif_port = onvif_port
        self.username = username
        self.ip = ip or ""
        self.password = password
        self.camera_type = camera_type
        self.frame = None
        # 是否添加水印
        self.is_water_mark = is_water_mark

        # 截图的保存文件名是ip_password_camear_type_strftime.jpg
        self._file_name = file_name or None

        self.folder_path = folder_path or time.strftime("%Y-%m-%d", time.localtime())

        # 新增：电脑摄像头索引
        self.cam_index = cam_index

        # 默认保存的目录是 年份-月份-日期
        if not os.path.exists(self.folder_path):
            try:
                os.makedirs(self.folder_path)
            except OSError as e:
                if e.errno != errno.EEXIST:  # 如果不是 "文件已存在" 错误
                    raise  # 如果不是文件已存在的错误，则抛出异常

        self.file_full_path = os.path.join(self.folder_path, self.file_name)

    @staticmethod
    def enum_computer_cameras(max_index=10):
        """
        静态方法：枚举电脑上可用的摄像头（返回可用索引列表）
        @param max_index: 最大检测索引（默认检测0-9，足够日常使用）
        @return: list 可用的摄像头索引（如[0,1]表示有2个摄像头）
        """
        available_cams = []
        for index in range(max_index):
            # 尝试打开摄像头
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # CAP_DSHOW解决Windows下释放摄像头卡顿问题
            if cap.isOpened():
                available_cams.append(index)
                # 立即释放资源
                cap.release()
            # 释放所有窗口
            cv2.destroyAllWindows()
        logger.debug(f"枚举电脑可用摄像头：{available_cams}")
        return available_cams

    def capture(self):
        """
        截图
        返回 1 表示截图成功。
        返回 0 表示未进行截图操作。
        返回 -1、-2 或其他负数表示截图失败或出现错误。
        :return: 返回1 截图成功
        假设这个函数返回了一个元组（status, file_path）
        """
        # 构造摄像头描述信息
        if self.camera_type == "computer":
            cam_desc = f"电脑摄像头（索引{self.cam_index}"
        else:
            cam_desc = self.ip or "未指定IP的网络摄像头"

        logger.debug(f"ip:{cam_desc}开始截图")
        # 检查摄像头是否可用
        if not self.check_camera():
            if self.camera_type == "computer":
                err_msg = f"{cam_desc}不可用（未连接或者被占用）"
            logger.debug(err_msg)
            return -1, err_msg
        try:
            # 获取摄像头视频帧
            cam = cv2.VideoCapture(self.camera_path)
            # 优化：摄像头添加缓冲区设置，提高截图质量
            if self.camera_type == "commputer":
                cam.set(cv2.CAP_PROP_FRAME_WIDTH,1920)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT,1080)
                # 读取2帧（丢弃第一帧模糊帧）
                for _ in range(2):
                    cam.read()
            if not cam.isOpened():
                raise RuntimeError("视频对象读取失败")
            else:
                logger.debug(f"{f'电脑摄像头(索引{self.cam_index})' if self.camera_type == 'computer' else self.ip} 摄像头打开成功")
            # 读取摄像头
            ret, self.frame = cam.read()

            # 添加水印
            if self.is_water_mark:
                self.watermark()

            # 保存截图
            cv2.imencode('.jpg', self.frame)[1].tofile(self.file_full_path)
            # 判断是否保存成功
            if os.path.isfile(self.file_full_path):
                logger.debug(f'截图成功,文件路径：{self.file_full_path}')
                return 1, self.file_full_path
            else:
                logger.debug('截图保存失败！')
                return -2, '截图保存失败！'

        except Exception as e:
            logger.error(f"捕获图像时发生错误：{e}")
            return -3, f"捕获图像时发生错误：{e}"

        finally:
            # 释放资源
            if 'cam' in locals() and cam and cam.isOpened():
                cam.release()
                # 新增：强制清空缓存，避免句柄残留
                cv2.VideoCapture(self.camera_path).release()
            if self.frame is not None:
                del self.frame

            cv2.destroyAllWindows()

    def check_camera(self) -> bool:
        """
        检查摄像头是否可用
        @return:
            bool:True 表示摄像头可用，False表示不可用
        Note:
             - 当camera_path为0时，表示使用本地摄像头，直接返回True
            - 对于网络摄像头，检查554端口是否开放
        """
        # 新增：电脑摄像头可用性检查
        if self.camera_type == "computer":
            logger.debug(f"检测电脑摄像头（索引{self.cam_index}）可用性")
            cap = cv2.VideoCapture(self.cam_index, cv2.CAP_ANY)
            is_available = cap.isOpened()
            cap.release()
            cv2.destroyAllWindows()
            return is_available

        logger.debug(f"开始检测网络摄像头可用性，IP: {self.ip}")

        try:
            if not is_port_open(self.ip, self.RTSP_PORT):
                logger.warning(f"摄像头 {self.ip} 的554端口不可达")
                return False

            logger.debug(f"摄像头 {self.ip} 检测正常")
            return True

        except Exception as e:
            logger.error(f"检测摄像头 {self.ip} 时发生异常: {str(e)}")
            return False

    def watermark(self):
        """
        截图添加水印信息：图片的名字
        :return:
        """
        if self.frame is None:
            raise Exception("截图失败或未打开摄像头，无法添加水印信息！")
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
        """
        rtsp 视频流地址
        电脑摄像头为 0
        海康和大华为默认的，
        onvif需要请求获取

        @return:
        """
        # camera_type 类型 dahua hik computer
        if self.camera_type == "dahua" and self.ip:
            return f"rtsp://admin:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0"
        # 电脑摄像头
        # TODO 多个摄像头的情况
        elif self.camera_type == "computer" or not self.ip:
            # 新增日志：确认返回的索引是否正确
            logger.debug(f"当前Camera实例返回电脑摄像头索引:{self.cam_index}")

            return self.cam_index
        # 海康威视
        elif self.camera_type == "hik" and self.ip:
            return f"rtsp://admin:{self.password}@{self.ip}:554/h264/ch34/main/av_stream"

        # onvif 判断
        elif self.camera_type == "onvif" and self.ip and self.onvif_port:
            client = OnvifClient(ip=self.ip,
                                 port=self.onvif_port,
                                 username=self.username,
                                 password=self.password)
            # 先连接摄像机
            if not client.connect():
                raise ConnectionError
            return client.GetStreamUri()
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
            # 格式：computer_索引_时间戳.jpg
            return f"computer_{self.cam_index}_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.jpg"
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

    # 测试电脑
    cam1 = Camera(camera_type="computer")
    result = cam1.capture()
    print(result)

    # 测试网络摄像头
    # cam1 = Camera(camera_type="onvif",
    #               ip="192.168.1.201",
    #               username="admin",
    #               password="qazwsx123",
    #               onvif_port=80)
    # cam1.is_water_mark = True
    # print(cam1.capture())
