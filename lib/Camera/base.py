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
from urllib.parse import quote

os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rw_timeout;5000000")

import cv2
from PIL import Image, ImageTk

from lib.OnvifClient import OnvifClient
from utils.tool import is_port_open

logger = logging.getLogger('camera_logger')

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


class Camera:
    """
    一个摄像头的类
    可以捕捉支持rtsp协议的网络摄像头，或者是电脑的摄像头
    或者通过onvif协议获取rtsp的地址
    """
    RTSP_PORT = 554  # RTSP默认端口
    PORT_CHECK_TIMEOUT = 0.5
    VIDEO_OPEN_TIMEOUT_MS = 3000
    VIDEO_READ_TIMEOUT_MS = 5000

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
        # 延迟赋值，确保self.file_name属性加载完成后再拼接路径，避免控制
        self.file_full_path = None

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
        :return: tuple （状态码，文件路径/错误信息）
        """
        # 构造摄像头描述信息
        if self.camera_type == "computer":
            cam_desc = f"电脑摄像头（索引{self.cam_index}）"
        else:
            cam_desc = self.ip or "未指定IP的网络摄像头"

        logger.debug("ip:%s开始截图", cam_desc)
        cam = None
        try:
            if self.camera_type != "computer" and not self.check_camera():
                err_msg = f"{cam_desc} 554端口不可达/摄像头离线"
                logger.debug(err_msg)
                return -1, err_msg

            if self.file_full_path is None:
                self.file_full_path = os.path.join(self.folder_path, self.file_name)

            # 获取摄像头视频帧
            camera_path = self.camera_path
            if self.camera_type == "computer":
                cam = cv2.VideoCapture(camera_path)
            else:
                cam = cv2.VideoCapture(
                    camera_path,
                    cv2.CAP_FFMPEG,
                    [
                        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                        self.VIDEO_OPEN_TIMEOUT_MS,
                        cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                        self.VIDEO_READ_TIMEOUT_MS,
                    ],
                )
            # 优化：摄像头添加缓冲区设置，提高截图质量
            if self.camera_type == "computer":
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                # 丢弃前两帧，使用摄像头稳定后的画面。
                for _ in range(2):
                    ret, _ = cam.read()
                    if not ret:
                        raise RuntimeError("读取摄像头预热帧失败")
            if not cam.isOpened():
                raise RuntimeError("视频对象读取失败")
            logger.debug("%s 摄像头打开成功", cam_desc)

            ret, self.frame = cam.read()
            if not ret or self.frame is None:
                raise RuntimeError("读取摄像头桢数据失败，画面为空")

            if self.is_water_mark:
                self.watermark()

            encoded_ok, encoded_image = cv2.imencode('.jpg', self.frame)
            if not encoded_ok or encoded_image is None:
                return -2, "JPEG 图像编码失败"

            encoded_image.tofile(self.file_full_path)
            if not os.path.isfile(self.file_full_path) or os.path.getsize(self.file_full_path) == 0:
                return -2, "截图保存失败或文件为空"

            logger.debug("截图成功,文件路径：%s", self.file_full_path)
            return 1, self.file_full_path

        except Exception as e:
            err_info = f"捕获图像时发生错误：{e}"
            logger.error(err_info)
            return -3, err_info

        finally:
            if cam is not None:
                try:
                    cam.release()
                except Exception:
                    logger.exception("释放摄像头资源失败: %s", cam_desc)
            self.frame = None

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
            if not is_port_open(
                self.ip,
                self.RTSP_PORT,
                timeout=self.PORT_CHECK_TIMEOUT,
            ):
                logger.warning(f"摄像头 {self.ip} 的554端口不可达")
                return False

            logger.debug(f"摄像头 {self.ip} 检测正常")
            return True

        except Exception as e:
            logger.error(f"检测摄像头 {self.ip} 时发生异常: {str(e)}")
            return False

    def watermark(self):
        """
        在截图左上角添加白色文件名水印。
        :return:
        """
        if self.frame is None:
            raise RuntimeError("截图失败或未打开摄像头，无法添加水印信息！")
        text = self.file_name
        img_height, img_width = self.frame.shape[:2]
        margin = max(12, round(img_width * 0.02))
        available_width = max(1, img_width - margin * 2)
        font_scale = max(0.3, min(img_width / 1200, 2.0))
        thickness = max(round(font_scale * 2), 1)
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(
            text,
            font_face,
            font_scale,
            thickness
        )
        if text_width > available_width:
            font_scale *= available_width / text_width
            thickness = max(round(font_scale * 2), 1)
            (text_width, text_height), baseline = cv2.getTextSize(
                text,
                font_face,
                font_scale,
                thickness
            )
        x = margin
        y = min(text_height + margin, img_height - baseline - 1)
        y = max(text_height, y)

        cv2.putText(
            self.frame,
            text,
            (x, y),
            font_face,
            font_scale,
            (0, 0, 0),
            thickness + 4,
            cv2.LINE_AA
        )
        cv2.putText(
            self.frame,
            text,
            (x, y),
            font_face,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )

    @property
    def camera_path(self):
        """
        获取可供 OpenCV 使用的单个摄像头地址。
        """
        if self.camera_type == "computer":
            logger.debug("当前Camera实例返回电脑摄像头索引:%s", self.cam_index)
            return self.cam_index

        if not self.ip:
            raise ValueError("网络摄像头 IP 地址不能为空")

        username = quote(str(self.username or "admin"), safe="")
        password = quote(str(self.password or ""), safe="")
        credentials = f"{username}:{password}@"

        if self.camera_type == "dahua":
            return (
                f"rtsp://{credentials}{self.ip}:554/"
                "cam/realmonitor?channel=1&subtype=0"
            )

        if self.camera_type == "hik":
            return f"rtsp://{credentials}{self.ip}:554/h264/ch34/main/av_stream"

        if self.camera_type == "onvif":
            try:
                client = OnvifClient(
                    ip=self.ip,
                    port=int(self.onvif_port),
                    username=self.username,
                    password=self.password,
                )
                stream_uris = client.GetStreamUri()
                if isinstance(stream_uris, str):
                    stream_uris = [stream_uris]
                stream_uri = next(
                    (
                        uri.strip()
                        for uri in stream_uris
                        if isinstance(uri, str)
                        and uri.strip().lower().startswith("rtsp://")
                    ),
                    None,
                )
                if stream_uri is None:
                    raise ValueError("ONVIF 未返回有效的 RTSP 地址")
                return stream_uri
            except Exception as e:
                raise RuntimeError(f"获取ONVIF流地址失败：{e}") from e

        raise ValueError(
            f"不支持的摄像头类型: {self.camera_type}，"
            "仅支持 dahua、hik、computer、onvif"
        )

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
