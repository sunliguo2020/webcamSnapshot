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
import traceback

from tool import portisopen, gen_ip_password_from_csv

try:
    import cv2
except Exception as e:
    os.system('pip install opencv-python')
    import cv2

logging.basicConfig(filename='cv2.log',
                    level=logging.DEBUG,
                    filemode='w',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')


def cv2_video_capture(cam_ip, password, client=None, dir_pre=None):
    """
    :param dir_pre: 截图目录的前缀
    :param cam_ip:摄像头IP地址
    :param password:摄像头密码
    :param client: 摄像头类型，这里是hik和dahua
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

    if not os.path.isdir(pic_dir):
        os.mkdir(pic_dir)
    logging.debug(f"保存截图的目录:{pic_dir}")

    # 判断是海康还是大华的摄像头
    if client == 'dahua':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/cam/realmonitor?channel=1&subtype=0".format(password, cam_ip))
    elif client == 'hik':
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(password, cam_ip))
    else:
        logging.error("设备类型参数不正确")
        return -1
    # logging.debug(cam)
    if cam.isOpened():
        ret, frame = cam.read()
        try:
            snapshot_file_name = cam_ip + '_' + password + '_' + client + "_rtsp_" + str_time + ".jpg"
            snapshot_full_path = os.path.join(pic_dir, snapshot_file_name)
            # 添加水印信息
            # cv2.putText(图像,需要添加字符串,需要绘制的坐标,字体类型,字号,字体颜色,字体粗细)
            img2 = cv2.putText(frame, snapshot_file_name.replace('.jpg', ''), (50, 200), cv2.LINE_AA, 2, (100, 255, 0),
                               5)
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
    while ip_passwd[0][2] < 5:
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
