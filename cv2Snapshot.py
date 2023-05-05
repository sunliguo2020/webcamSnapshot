# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2022/5/28 12:26
遗留问题：
        水印有可能超出图片大小
"""
import csv
import logging
import os
import time
import traceback

from tool import portisopen, gen_ip_password_from_csv

try:
    import cv2
except ImportError as e:
    os.system('pip install opencv-python')
    import cv2

logging.basicConfig(filename='cv2.log',
                    level=logging.DEBUG,
                    filemode='w',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')


def cv2_video_capture(cam_ip, cam_pwd, cam_client=None, dir_pre=None):
    """
    :param dir_pre: 截图目录的前缀
    :param cam_ip:摄像头IP地址
    :param cam_pwd:摄像头密码
    :param cam_client: 摄像头类型，这里是hik和dahua
    :return:
    """

    if not os.path.isdir(dir_pre):
        os.mkdir(dir_pre)

    # 判断rtsp协议的554端口有没有打开。
    port_isopen_result = portisopen(cam_ip, 554)
    logging.debug(f"判断{cam_ip}端口是否打开{type(port_isopen_result)},{port_isopen_result}")
    if not port_isopen_result:
        logging.debug(f"{cam_ip} 554 端口没有打开或者网络不通")
        return -1

    # 保存截图的目录  运行程序的日期为目录名
    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    pic_dir = os.path.join(dir_pre, time.strftime('%Y-%m-%d', time.localtime()))

    # 截图的文件名和路径
    snapshot_file_name = cam_ip + '_' + cam_pwd + '_' + cam_client + "_rtsp_" + str_time + ".jpg"
    snapshot_full_path = os.path.join(pic_dir, snapshot_file_name)

    if not os.path.isdir(pic_dir):
        os.mkdir(pic_dir)
    logging.debug(f"保存截图的目录:{pic_dir}")

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"
    # 判断是海康还是大华的摄像头
    if cam_client == 'dahua':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(cam_pwd, cam_ip),
                               cv2.CAP_FFMPEG)
    elif cam_client == 'hik':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(cam_pwd, cam_ip),
                               cv2.CAP_FFMPEG)
    else:
        logging.error("设备类型参数不正确")
        return -1
    # logging.debug(cam)
    if cam.isOpened():  # 判断视频对象是否成功读取成功
        # 按帧读取视频，返回值ret是布尔型，正确读取则返回True，读取失败或读取视频结尾则会返回False。
        # frame为每一帧的图像，这里图像是三维矩阵，即frame.shape = (640,480,3)，读取的图像为BGR格式。
        ret, frame = cam.read()
        try:
            # 添加水印信息
            text = snapshot_file_name.replace('.jpg', '')
            fontFace = cv2.FONT_HERSHEY_SIMPLEX  # 字体
            line_type = cv2.LINE_AA
            '''
            如果对大小约为1000 x 1000的图像使用fontScale = 1，则此代码应正确缩放字体
            fontScale = (imageWidth * imageHeight) / (1000 * 1000) # Would work best for almost square images
            '''
            font_scale = 2  # 比例因子
            thickness = 2  # 线的粗细

            # 计算文本的宽高 baseline
            # retval 返回值，元组，字体的宽高 (width, height)
            retval, base_line = cv2.getTextSize(text, fontFace=fontFace, fontScale=font_scale, thickness=thickness)
            print(f'retval:{retval},baseLine:{base_line}')
            print(f'frame.shape:{frame.shape}')
            img_width = frame.shape[1]
            text_width = retval[0]
            # 如果文字的宽带大于图片的宽度，则缩小比例因子
            if text_width > img_width:
                font_scale = font_scale * (img_width / text_width) * 0.8

            # cv2.putText(图像,需要添加字符串,需要绘制的坐标,字体类型,字号,字体颜色,字体粗细)
            # def putText(img, text, org, fontFace, fontScale, color, thickness=None, lineType=None, bottomLeftOrigin=None):
            # real signature unknown; restored from __doc__
            # 各参数依次是：图片，添加的文字，左上角坐标，字体，字体大小，颜色，字体粗细
            # 字体大小，数值越大，字体越大
            # 字体粗细，越大越粗，数值表示描绘的线条占有的直径像素个数
            img2 = cv2.putText(frame, text, (0, 200), fontFace, font_scale, (100, 255, 0),
                               thickness, line_type)

            retval = cv2.imwrite(snapshot_full_path, img2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

            logging.debug(f"ip：{cam_ip},file_name:{snapshot_file_name}下载完成")

        except Exception as e:
            logging.error(f"{cam_ip}下载过程中错误！")
            logging.error(f"{cam_ip}" + traceback.format_exc())
        finally:
            cam.release()
            cv2.destroyAllWindows()
            # 判断是否下载成功
            if not os.path.isfile(snapshot_full_path):
                logging.info(f'{cam_ip}保存截图失败')
                return -2
            else:
                logging.info(f"{cam_ip}保存截图成功")
                return 1

    else:
        logging.debug(f"打开摄像头{cam_ip}失败！")
        return -3


if __name__ == '__main__':
    # 包含ip和密码的csv文件
    csv_file = r'./txt/ruizhi.csv'
    # hik or dahua
    client = 'hik'

    success_ip = []
    # 列表的格式
    # ip,password,截取的次数(初始为0)
    # 成功的剔除,失败的增加次数。次数超过一定的数则退出。
    # [[ip,password,number of time],[],...]
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
            print(count, ":", ip)
            try:
                result = cv2_video_capture(ip, password, client, dir_pre=os.path.basename(csv_file).split('.')[0])

            except Exception as e:
                print(e)
            # 统计下载失败的IP地址
            if result < 0:
                print(f"{ip}下载失败{item[2]}次")
                item[2] += 1
            elif result == 1:
                print('截图成功，准备删除', item)
                if ip not in success_ip:
                    success_ip.append(ip)

                # 删除这条ip
                ip_passwd.remove(item)

    print(f'总共成功{len(success_ip)}个ip截图')

    print(f'最后还有{len(ip_passwd)}个ip截图失败')
    print(ip_passwd)

    # 保存失败的ip记录到文件中
    failed_file = os.path.basename(csv_file).replace('.csv', '') + '_failed_' + time.strftime("%Y%m%d%H%M%S",
                                                                                              time.localtime()) + '.csv'
    with open(failed_file, 'w', newline='') as fp:
        csv_writer = csv.writer(fp)
        csv_writer.writerows(ip_passwd)
