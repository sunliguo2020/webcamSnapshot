# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/28 12:26

"""
import csv
import logging


import os
import time

from utils.tool import is_port_open, gen_ip_password_from_csv

try:
    import cv2
except ImportError as e:
    os.system('pip install opencv-python')
    import cv2

logger = logging.getLogger('NVR')

# logger.setLevel(logging.DEBUG)
#
# handler_control = logging.StreamHandler()
# logger.addHandler(handler_control)


def water_mark(frame, water_text):
    """
    给图片添加水印
    :param water_text: 水印信息
    :param frame:
    :return:
    """
    # 添加水印信息
    text_watermark_x = 0
    text_watermark_y = 200
    water_text = water_text.replace('.jpg', '')
    font_face = cv2.FONT_HERSHEY_SIMPLEX  # 字体
    line_type = cv2.LINE_AA
    '''
    如果对大小约为1000 x 1000的图像使用fontScale = 1，则此代码应正确缩放字体
    fontScale = (imageWidth * imageHeight) / (1000 * 1000) # Would work best for almost square images
    '''
    font_scale = 2  # 比例因子
    thickness = 2  # 线的粗细

    # 计算文本的宽高 baseline
    # retval 返回值，元组，字体的宽高 (width, height)
    retval, base_line = cv2.getTextSize(water_text, fontFace=font_face, fontScale=font_scale, thickness=thickness)

    img_width = frame.shape[1]
    img_hight = frame.shape[0]

    logger.debug(f"截图的宽x高:{img_width}x{img_hight}")
    text_width = retval[0]
    # 如果文字的宽带大于图片的宽度，则缩小比例因子
    if text_width > img_width:
        font_scale = font_scale * (img_width / text_width) * 0.8
        text_watermark_y = int(img_width * 0.1)  # 水印的新y坐标
        logger.debug(f"水印Y坐标值为:{text_watermark_y}")

    # cv2.putText(图像,需要添加字符串,需要绘制的坐标,字体类型,字号,字体颜色,字体粗细)
    # def putText(img, water_text, org, fontFace, fontScale, color, thickness=None, lineType=None, bottomLeftOrigin=None):
    # real signature unknown; restored from __doc__
    # 各参数依次是：图片，添加的文字，左上角坐标，字体，字体大小，颜色，字体粗细
    # 字体大小，数值越大，字体越大
    # 字体粗细，越大越粗，数值表示描绘的线条占有的直径像素个数
    img2 = cv2.putText(frame, water_text, (text_watermark_x, text_watermark_y), font_face, font_scale,
                       (100, 255, 0),
                       thickness, line_type)
    return img2


def cv2_video_capture(cam_ip, cam_pwd, cam_client='hik', channel_no=1, save_dir='.'):
    """
    根据提供的ip,password 采集摄像机某个通道的截图
    :param channel_no: 通道号
    :param save_dir: 截图保存目录
    :param cam_ip:摄像头IP地址
    :param cam_pwd:摄像头密码
    :param cam_client: 摄像头类型，这里是hik和dahua,computer
    :return: < 0 : 报错退出
    """
    # 判断rtsp协议的554端口有没有打开。
    port_open_result = is_port_open(cam_ip, 554)
    logger.debug(f"判断{cam_ip}端口是否打开:{port_open_result}")

    if not port_open_result:
        logger.debug(f"{cam_ip} 554 端口没有打开或者网络不通")
        return -1

    # 判断截图根目录是否存在
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    logger.debug(f"最后保存截图的根目录save_dir:{save_dir}")

    # 保存截图的目录  运行程序的日期为目录名
    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    pic_dir = os.path.join(save_dir, time.strftime('%Y-%m-%d', time.localtime()))

    if not os.path.isdir(pic_dir):
        os.makedirs(pic_dir)
    logger.debug(f"保存截图的目录:{pic_dir}")
    # 截图的文件名和路径
    snapshot_file_name = "_".join([cam_ip, cam_pwd, cam_client, "rtsp", "channel" + str(channel_no), str_time]) + ".jpg"
    snapshot_full_path = os.path.join(pic_dir, snapshot_file_name)

    logger.debug(snapshot_full_path)

    # os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"

    # 判断是海康还是大华的摄像头
    if cam_client == 'dahua':
        cam = cv2.VideoCapture(f"rtsp://admin:{cam_pwd}@{cam_ip}:554/cam/realmonitor?channel={channel_no}&subtype=0",
                               cv2.CAP_FFMPEG)
    elif cam_client == 'hik':
        try:
            # logger.debug(f"rtsp://admin:{cam_pwd}@{cam_ip}:554/h264/ch{channel_no}/main/av_stream")
            logger.debug(f"rtsp://admin:{cam_pwd}@{cam_ip}:554/Streaming/Channels/{channel_no}01")
            # cam = cv2.VideoCapture(f"rtsp://admin:{cam_pwd}@{cam_ip}:554/h264/ch{channel_no}/main/av_stream",
            cam = cv2.VideoCapture(f"rtsp://admin:{cam_pwd}@{cam_ip}:554/Streaming/Channels/{channel_no}01")
        except Exception as e:
            logger.debug(f"cv2.VideoCapture failed{e}")
    else:
        logger.error("设备类型参数不正确")
        return -2

    # logger.debug(f'摄像头类型{cam_client}')

    # 判断视频对象是否成功读取成功
    if not cam.isOpened():
        raise ValueError("打开摄像头失败.")
        return -3

    # 按帧读取视频，返回值ret是布尔型，正确读取则返回True，读取失败或读取视频结尾则会返回False。
    # frame为每一帧的图像，这里图像是三维矩阵，即frame.shape = (640,480,3)，读取的图像为BGR格式。
    ret, frame = cam.read()
    if not ret:
        return -3
    try:
        # 添加水印信息
        img2 = water_mark(frame, snapshot_file_name)
        # 保存路径中包含中文的问题
        # retval = cv2.imwrite(snapshot_full_path+'.jpg', img2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        retval = cv2.imencode(".jpg", img2)[1].tofile(snapshot_full_path)

    except Exception as e:
        logger.error(f"{cam_ip}下载过程中错误！")
        # logger.error(f"{cam_ip}" + traceback.format_exc())
    finally:
        cam.release()
        cv2.destroyAllWindows()
        # 判断是否下载成功
        if not os.path.isfile(snapshot_full_path):
            logger.info(f'{cam_ip}保存截图失败')
            return -2
        else:
            logger.info(f"{cam_ip}保存截图成功")
            return 1


def save_failed_ip(csv_file_name, failed_ip):
    """
    保存采集失败的ip,password到csv文件中
    :param csv_file_name: 要保存的csv文件
    :param failed_ip: 包含采集失败的ip,password的列表
    :return:
    """
    # 保存失败的ip记录到文件中
    failed_file = os.path.basename(csv_file_name).replace('.csv', '') + '_failed_' + time.strftime("%Y%m%d%H%M%S",
                                                                                                   time.localtime()) + '.csv'
    with open(failed_file, 'w', newline='') as fp:
        csv_writer = csv.writer(fp)
        csv_writer.writerows(failed_ip)


def cams_capture(csv_file, *args, **kwargs):
    """
    根据csv文件中保存的ip，password来采集截图
    :param csv_file: # 包含ip和密码的csv文件
    :return:
    """
    logger.debug(f"根据csv文件截图函数的参数：args:{args},kwargs:{kwargs}")
    if not os.path.isfile(csv_file) or os.path.splitext(csv_file)[1] != '.csv':
        logger.error('必须是csv格式的文件！')
        return -1

    success_ip = []  # 采集成功的ip
    ip_passwd = []

    # 初始化要截图的ip,passwd,密码
    for i in gen_ip_password_from_csv(csv_file, 0):
        temp = list(i)
        temp.append(0)
        ip_passwd.append(temp)

    count = 0
    while ip_passwd and ip_passwd[0][2] < 5:
        for item in ip_passwd[:]:
            ip, password = item[:2]
            count += 1
            logger.debug(f"{count}:{ip}")
            try:
                # 截图并保存
                result = cv2_video_capture(cam_ip=ip, cam_pwd=password)
            except Exception as e:
                logger.error(f"截图过程中出错:{e}")
                item[2] += 1
            else:
                # 统计下载失败的IP地址
                if result < 0:
                    logger.info(f"{ip}下载失败{item[2]}次")
                    item[2] += 1
                elif result == 1:
                    logger.debug(f'截图成功，准备删除{item}', )
                    if ip not in success_ip:
                        success_ip.append(ip)
                    # 删除这条ip
                    ip_passwd.remove(item)
            finally:
                pass

    logger.debug(f'总共成功{len(success_ip)}个ip截图,{len(ip_passwd)}个ip截图失败')
    # 保存截图失败的ip，password
    save_failed_ip(csv_file, ip_passwd)


def cams_channel_capture(ip, password, start_channel_no=1, end_channel_no=64, **kwargs):
    """
    按照录像机通道截图
    :param end_channel_no:      结束通道号
    :param start_channel_no:    开始通道号
    :param ip:                  录像机ip地址
    :param password:            录像机密码
    :return:
    """
    # 分析参数
    logger.debug(f"ip:{ip}, password:{password}, start_channel_no:{start_channel_no},"
                 f" end_channel_no:{end_channel_no}, kwargs：{kwargs}")

    # 如果没有save_dir参数，则设置为当前录像机的ip地址
    if "save_dir" not in kwargs or kwargs.get('save_dir') == '':
        logger.debug(f"没有传递save_dir参数,我要自己加把当前录像机的ip作为这个参数的值")
        kwargs.update({'save_dir': str(ip)})
        logger.debug(f"修改后的kwarg：{kwargs}")

    for channel in range(start_channel_no, end_channel_no + 1):
        logger.debug(f'{ip}开始通道:{channel}截图')
        try:
            cv2_video_capture(cam_ip=ip, cam_pwd=password, channel_no=channel, **kwargs)
        except Exception as e:
            logger.debug(f'截图失败:{e}')


if __name__ == '__main__':
    # cams_capture('./txt/ruizhi.csv', 'hik')
    # cams_channel_capture('192.168.1.200', 'admin123', end_channel_no=10)
    for i in range(100):
        cv2_video_capture('192.168.1.200', 'admin123', channel_no=5)
