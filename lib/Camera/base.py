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
from functools import lru_cache
from string import Formatter
from urllib.parse import quote

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk

from lib.OnvifClient import OnvifClient
from utils.dahua_device_info import get_dahua_device_info
from utils.hikvision_device_info import (
    get_hikvision_channel_snapshot,
    get_hikvision_device_info,
)
from utils.tool import is_port_open
from utils.watermark import normalize_watermark_style

logger = logging.getLogger('camera_logger')


@lru_cache(maxsize=8)
def _load_chinese_font(font_size):
    """Load an installed Windows font that includes Chinese glyphs."""
    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for filename in ("msyh.ttc", "simhei.ttf", "simsun.ttc"):
        font_path = os.path.join(fonts_dir, filename)
        if os.path.isfile(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except OSError:
                continue
    raise OSError(
        "未找到支持中文水印的字体，请安装微软雅黑、黑体或宋体"
    )


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
            # 水印样式配置
            watermark_style=None,
            # 大华设备 HTTP 管理端口
            device_info_port=80,
            # 海康录像机通道号（从 1 开始）
            channel_no=None,
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
        logger.debug(
            "__init__参数:ip:%s,username:%s,password_set:%s,"
            "onvif_port:%s,cam_index:%s",
            ip,
            username,
            bool(password),
            onvif_port,
            cam_index,
        )

        self.onvif_port = onvif_port
        self.username = username
        self.ip = ip or ""
        self.password = password
        self.camera_type = camera_type
        self.frame = None
        self.last_timings = {}
        # 是否添加水印
        self.is_water_mark = is_water_mark
        self.watermark_style = normalize_watermark_style(watermark_style)
        self.device_info_port = device_info_port
        self.channel_no = (
            int(channel_no) if channel_no not in (None, "") else None
        )
        if self.channel_no is not None and self.channel_no < 1:
            raise ValueError("海康录像机通道号必须大于 0")

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
        elif self.camera_type == "hik" and self.channel_no is not None:
            cam_desc = f"{self.ip} 通道{self.channel_no}"
        else:
            cam_desc = self.ip or "未指定IP的网络摄像头"

        capture_started = time.perf_counter()
        stage_started = capture_started
        stage_name = (
            "RTSP端口检测"
            if self.camera_type != "computer"
            else "本地设备检测"
        )
        timings = {}
        logger.debug("ip:%s开始截图", cam_desc)
        cam = None
        recorder_channel = (
            self.camera_type == "hik" and self.channel_no is not None
        )
        try:
            if self.camera_type != "computer" and not recorder_channel:
                if not self.check_camera():
                    err_msg = f"{cam_desc} 554端口不可达/摄像头离线"
                    logger.debug(err_msg)
                    return -1, err_msg
                timings[stage_name] = time.perf_counter() - stage_started
            elif self.camera_type == "computer":
                timings[stage_name] = time.perf_counter() - stage_started

            stage_name = "准备流地址"
            stage_started = time.perf_counter()
            if self.file_full_path is None:
                self.file_full_path = os.path.join(self.folder_path, self.file_name)

            # 获取摄像头视频帧
            camera_path = self.camera_path
            timings[stage_name] = time.perf_counter() - stage_started

            open_stage_name = (
                "打开本地设备"
                if self.camera_type == "computer"
                else "打开视频流"
            )
            stage_name = open_stage_name
            stage_started = time.perf_counter()
            if self.camera_type == "computer":
                cam = cv2.VideoCapture(camera_path, cv2.CAP_DSHOW)
                if not cam.isOpened():
                    cam.release()
                    logger.debug(
                        "%s DirectShow 打开失败，回退默认视频后端",
                        cam_desc,
                    )
                    cam = cv2.VideoCapture(camera_path)
                if not cam.isOpened():
                    raise RuntimeError("无法打开本地摄像头")
                timings[stage_name] = time.perf_counter() - stage_started

                stage_name = "设置分辨率"
                stage_started = time.perf_counter()
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                actual_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
                logger.debug(
                    "%s 实际采集分辨率：%sx%s",
                    cam_desc,
                    actual_width,
                    actual_height,
                )
                timings[stage_name] = time.perf_counter() - stage_started

                stage_name = "预热帧"
                stage_started = time.perf_counter()
                for _ in range(2):
                    ret, _ = cam.read()
                    if not ret:
                        raise RuntimeError("读取摄像头预热帧失败")
                timings[stage_name] = time.perf_counter() - stage_started
            elif recorder_channel:
                stage_name = "ISAPI通道快照"
                stage_started = time.perf_counter()
                try:
                    snapshot = get_hikvision_channel_snapshot(
                        self.ip,
                        self.channel_no,
                        self.username,
                        self.password,
                        port=self.device_info_port,
                    )
                    self.frame = cv2.imdecode(
                        np.frombuffer(snapshot, dtype=np.uint8),
                        cv2.IMREAD_COLOR,
                    )
                    if self.frame is None:
                        raise ValueError("ISAPI 返回的数据不是有效图像")
                    timings[stage_name] = time.perf_counter() - stage_started
                except (
                    cv2.error,
                    PermissionError,
                    requests.RequestException,
                    ValueError,
                ) as snapshot_error:
                    logger.warning(
                        "%s ISAPI 快照失败，回退 RTSP：%s",
                        cam_desc,
                        snapshot_error,
                    )
                    stage_name = "RTSP端口检测"
                    stage_started = time.perf_counter()
                    if not self.check_camera():
                        raise RuntimeError(
                            f"ISAPI 通道快照失败：{snapshot_error}；"
                            "RTSP 554 端口不可达"
                        ) from snapshot_error
                    timings[stage_name] = time.perf_counter() - stage_started

                    stage_name = open_stage_name
                    stage_started = time.perf_counter()
                    cam = self._open_video_stream(camera_path)
                    if cam is None or not cam.isOpened():
                        if cam is not None:
                            cam.release()
                            cam = None
                        raise RuntimeError(
                            f"ISAPI 通道快照失败：{snapshot_error}；"
                            "RTSP 视频流也无法打开"
                        ) from snapshot_error
                    timings[stage_name] = time.perf_counter() - stage_started
            else:
                cam = self._open_video_stream(camera_path)
            if cam is not None:
                if not cam.isOpened():
                    open_elapsed = time.perf_counter() - stage_started
                    backend = (
                        "FFMPEG"
                        if self.camera_type != "computer"
                        else "DirectShow/默认后端"
                    )
                    raise RuntimeError(
                        "视频对象读取失败 "
                        f"(backend={backend}, is_opened=False, "
                        f"open_elapsed={open_elapsed:.3f}s, "
                        f"open_timeout_ms={self.VIDEO_OPEN_TIMEOUT_MS})"
                    )
                logger.debug("%s 摄像头打开成功", cam_desc)
                timings[stage_name] = time.perf_counter() - stage_started
            else:
                logger.debug("%s ISAPI 通道快照获取成功", cam_desc)

            if cam is not None:
                stage_name = "读取首帧"
                stage_started = time.perf_counter()
                ret, self.frame = cam.read()
                if not ret or self.frame is None:
                    read_elapsed = time.perf_counter() - stage_started
                    is_opened = cam.isOpened()
                    backend = cam.getBackendName() if is_opened else "closed"
                    width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cam.get(cv2.CAP_PROP_FPS)
                    fourcc = int(cam.get(cv2.CAP_PROP_FOURCC))
                    codec = "".join(
                        chr((fourcc >> (8 * index)) & 0xFF)
                        for index in range(4)
                    ).strip("\x00 ")
                    if not codec or not codec.isprintable():
                        codec = f"0x{fourcc:08x}" if fourcc else "unknown"
                    diagnostics = (
                        f"ret={ret}, frame_is_none={self.frame is None}, "
                        f"is_opened={is_opened}, backend={backend}, "
                        f"stream_size={width:.0f}x{height:.0f}, fps={fps:.2f}, "
                        f"fourcc={codec}, "
                        f"open_elapsed={timings.get(open_stage_name, 0.0):.3f}s, "
                        f"read_elapsed={read_elapsed:.3f}s, "
                        f"open_timeout_ms={self.VIDEO_OPEN_TIMEOUT_MS}, "
                        f"read_timeout_ms={self.VIDEO_READ_TIMEOUT_MS}"
                    )
                    logger.warning(
                        "读取摄像头首帧失败诊断 IP=%s 类型=%s %s",
                        cam_desc,
                        self.camera_type,
                        diagnostics,
                    )
                    raise RuntimeError(
                        f"读取摄像头桢数据失败，画面为空 ({diagnostics})"
                    )
                timings[stage_name] = time.perf_counter() - stage_started

            if self.is_water_mark:
                stage_name = "添加水印"
                stage_started = time.perf_counter()
                self.watermark()
                timings[stage_name] = time.perf_counter() - stage_started

            stage_name = "JPEG编码"
            stage_started = time.perf_counter()
            encoded_ok, encoded_image = cv2.imencode('.jpg', self.frame)
            if not encoded_ok or encoded_image is None:
                return -2, "JPEG 图像编码失败"
            timings[stage_name] = time.perf_counter() - stage_started

            stage_name = "写入文件"
            stage_started = time.perf_counter()
            encoded_image.tofile(self.file_full_path)
            if not os.path.isfile(self.file_full_path) or os.path.getsize(self.file_full_path) == 0:
                return -2, "截图保存失败或文件为空"
            timings[stage_name] = time.perf_counter() - stage_started

            logger.debug("截图成功,文件路径：%s", self.file_full_path)
            return 1, self.file_full_path

        except Exception as e:
            err_info = f"捕获图像时发生错误：{e}"
            logger.error(err_info)
            return -3, err_info

        finally:
            if stage_name not in timings:
                timings[stage_name] = time.perf_counter() - stage_started
            if cam is not None:
                release_started = time.perf_counter()
                try:
                    cam.release()
                except Exception:
                    logger.exception("释放摄像头资源失败: %s", cam_desc)
                timings["释放视频流"] = time.perf_counter() - release_started
            self.frame = None
            timings["总耗时"] = time.perf_counter() - capture_started
            self.last_timings = timings
            stage_details = " ".join(
                f"{name}={elapsed:.3f}s"
                for name, elapsed in timings.items()
            )
            logger.info(
                "[耗时] 摄像头截图 IP=%s 类型=%s %s",
                cam_desc,
                self.camera_type,
                stage_details,
            )

    def _open_video_stream(self, camera_path):
        """Open Hikvision recorder streams like the legacy capture path first."""
        if self.camera_type == "hik" and self.channel_no is not None:
            cam = cv2.VideoCapture(camera_path)
            if cam.isOpened():
                return cam
            cam.release()
            logger.warning(
                "%s 默认视频后端打开失败，回退到 FFmpeg",
                f"{self.ip} 通道{self.channel_no}",
            )

        return cv2.VideoCapture(
            camera_path,
            cv2.CAP_FFMPEG,
            [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                self.VIDEO_OPEN_TIMEOUT_MS,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                self.VIDEO_READ_TIMEOUT_MS,
            ],
        )

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
        按已配置的样式在截图上添加水印。
        :return:
        """
        if self.frame is None:
            raise RuntimeError("截图失败或未打开摄像头，无法添加水印信息！")
        style = self.watermark_style
        values = {
            "filename": self.file_name,
            "ip": self.ip or f"computer_{self.cam_index}",
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "camera_type": self.camera_type,
            "camera_index": str(self.cam_index),
            "model": "N/A",
            "mac": "N/A",
            "serial_number": "N/A",
            "serial": "N/A",
        }
        template_fields = {
            field_name.split(".", 1)[0].split("[", 1)[0]
            for _, field_name, _, _ in Formatter().parse(style["text"])
            if field_name
        }
        device_info_fields = {"model", "mac", "serial", "serial_number"}
        if (
            self.camera_type in {"dahua", "hik"}
            and template_fields & device_info_fields
        ):
            try:
                get_device_info = (
                    get_dahua_device_info
                    if self.camera_type == "dahua"
                    else get_hikvision_device_info
                )
                info = get_device_info(
                    self.ip,
                    self.username,
                    self.password,
                    port=getattr(self, "device_info_port", 80),
                )
            except (TypeError, ValueError) as error:
                logger.warning(
                    "读取设备信息配置失败 IP=%s 类型=%s：%s",
                    self.ip,
                    self.camera_type,
                    error,
                )
                info = {}
            values.update({
                key: info.get(key) or "N/A"
                for key in ("model", "mac", "serial_number")
            })
            values["serial"] = values["serial_number"]
        text = style["text"].format_map(values)
        if not text:
            return

        lines = text.splitlines()
        if not any(lines):
            return

        img_height, img_width = self.frame.shape[:2]
        margin = round(img_width * style["margin"] / 100)
        available_width = max(1, img_width - margin * 2)
        available_height = max(1, img_height - margin * 2)
        font_scale = max(0.3, min(img_width / 1200, 2.0))
        font_scale *= style["font_scale"]
        use_pillow = any(not line.isascii() for line in lines)
        font_face = None if use_pillow else getattr(cv2, style["font"])

        def measure_lines():
            thickness = max(round(font_scale * 2), 1)
            pillow_font = None
            if use_pillow:
                pillow_font = _load_chinese_font(
                    max(8, round(font_scale * 24))
                )
                sizes = []
                ascent = 0
                descent = 0
                for line in lines:
                    bounds = pillow_font.getbbox(line or " ", anchor="ls")
                    width = bounds[2] - bounds[0]
                    line_ascent = max(0, -bounds[1])
                    line_descent = max(0, bounds[3])
                    ascent = max(ascent, line_ascent)
                    descent = max(descent, line_descent)
                    sizes.append(
                        (
                            (width, line_ascent + line_descent),
                            line_descent,
                        )
                    )
                text_height = ascent
                baseline = descent
            else:
                sizes = [
                    cv2.getTextSize(
                        line or " ", font_face, font_scale, thickness
                    )
                    for line in lines
                ]
                text_height = max(size[0][1] for size in sizes)
                baseline = max(size[1] for size in sizes)
            max_width = max(
                (size[0][0] for line, size in zip(lines, sizes) if line),
                default=0,
            )
            line_spacing = (
                text_height
                + baseline
                + max(2, round(font_scale * 2))
                + thickness
                + 3
            )
            block_height = (
                text_height + (len(lines) - 1) * line_spacing + baseline
            )
            return (
                thickness,
                sizes,
                max_width,
                text_height,
                baseline,
                line_spacing,
                block_height,
                pillow_font,
            )

        for _ in range(2):
            (
                thickness,
                line_sizes,
                max_width,
                text_height,
                baseline,
                line_spacing,
                block_height,
                pillow_font,
            ) = measure_lines()
            scale_factor = min(
                1.0,
                available_width / max_width if max_width else 1.0,
                available_height / block_height if block_height else 1.0,
            )
            if scale_factor >= 1.0:
                break
            font_scale *= scale_factor

        (
            thickness,
            line_sizes,
            _,
            text_height,
            baseline,
            line_spacing,
            block_height,
            pillow_font,
        ) = measure_lines()

        vertical_position, horizontal_position = style["position"].split("_")
        if vertical_position == "top":
            block_top = margin
        elif vertical_position == "middle":
            block_top = (img_height - block_height) // 2
        else:
            block_top = img_height - margin - block_height
        block_top = max(0, min(block_top, max(0, img_height - block_height)))

        def bgr_color(hex_color):
            return tuple(
                int(hex_color[index:index + 2], 16)
                for index in (5, 3, 1)
            )

        def rgb_color(hex_color):
            return tuple(
                int(hex_color[index:index + 2], 16)
                for index in (1, 3, 5)
            )

        if use_pillow:
            pillow_image = Image.fromarray(
                cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            )
            pillow_draw = ImageDraw.Draw(pillow_image)

        for line_index, line in enumerate(lines):
            if not line:
                continue
            line_width = line_sizes[line_index][0][0]
            if horizontal_position == "left":
                x = margin
            elif horizontal_position == "center":
                x = (img_width - line_width) // 2
            else:
                x = img_width - margin - line_width
            x = max(0, min(x, max(0, img_width - line_width)))
            y = block_top + text_height + line_index * line_spacing
            y = max(
                text_height,
                min(y, max(text_height, img_height - baseline)),
            )

            if use_pillow:
                pillow_draw.text(
                    (x, y),
                    line,
                    font=pillow_font,
                    fill=rgb_color(style["color"]),
                    anchor="ls",
                    stroke_width=thickness + 1,
                    stroke_fill=rgb_color(style["outline_color"]),
                )
            else:
                cv2.putText(
                    self.frame,
                    line,
                    (x, y),
                    font_face,
                    font_scale,
                    bgr_color(style["outline_color"]),
                    thickness + 4,
                    cv2.LINE_AA
                )
                cv2.putText(
                    self.frame,
                    line,
                    (x, y),
                    font_face,
                    font_scale,
                    bgr_color(style["color"]),
                    thickness,
                    cv2.LINE_AA
                )

        if use_pillow:
            self.frame[:] = cv2.cvtColor(
                np.asarray(pillow_image), cv2.COLOR_RGB2BGR
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
            if self.channel_no is not None:
                return (
                    f"rtsp://{credentials}{self.ip}:554/"
                    f"Streaming/Channels/{self.channel_no}01"
                )
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
        elif self.camera_type == "hik" and self.channel_no is not None:
            return (
                f"{self.ip}_hik_channel{self.channel_no}_"
                f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}.jpg"
            )
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
