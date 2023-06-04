# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2021/6/12 10:22

// 说明：
// username：用户名，例如admin
// passwd：密码，例如12345
// ip：设备的ip地址，例如192.0.0.64
// port：端口号默认554，若为默认可以不写
// codec：有h264、MPEG-4、mpeg4这几种
// channel：通道号，起始为1
// subtype：码流类型，主码流为main，子码流为sub
rtsp://[username]:[passwd]@[ip]:[port]/[codec]/[channel]/[subtype]/av_stream
在 OpenCV 中，很简单就能读取 IP 摄像头。

"""
import csv
import logging
import os
import time

from tool import portisopen, gen_ip_password_from_csv

try:
    import cv2
except ImportError as e:
    os.system('pip install opencv-python')
    import cv2

logging.basicConfig(filename='hik_cv2.log',
                    level=logging.INFO,
                    filemode='a',
                    format='%(asctime)s-%(filename)s[line:%(lineno)d]-%(message)s')


def hik_cv2(cam_ip="192.168.1.200", cam_pwd='admin', dir_pre=''):
    """
    文件名保存的格式：ip_password_hik_timestr.jpg

    :param cam_ip: 摄像头ip地址
    :param cam_pwd:摄像头密码
    :param dir_pre: 保存目录前缀
    :return:
            -1:网络不通或者端口554没有打开

    """
    if not portisopen(cam_ip, 554):
        print(f"{cam_ip}:554 端口没有打开")
        logging.debug(f'{cam_ip} 554端口没开放或者网络不通！')
        return -1

    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 保存截图的目录
    pic_dir = dir_pre + "_" + time.strftime('%Y-%m-%d', time.localtime())

    if not os.path.isdir(pic_dir):
        os.makedirs(os.path.join('./', pic_dir))

    pic_file_name = f"{cam_ip}_{cam_pwd}_hik_{str_time}.jpg"
    # 保存文件的路径名
    pic_full_path = os.path.join(pic_dir, pic_file_name)

    logging.debug(f'要保存的文件路名为：{pic_full_path}')

    try:
        cam = cv2.VideoCapture("rtsp://admin:{}@{}:554/h264/ch34/main/av_stream".format(cam_pwd, cam_ip))
        ret, frame = cam.read()
        # 添加水印信息
        # cv2.putText(图像,需要添加字符串,需要绘制的坐标,字体类型,字号,字体颜色,字体粗细)
        img2 = cv2.putText(frame, pic_file_name.replace('.jpg', ''), (50, 200), cv2.LINE_AA, 2, (100, 255, 0), 5)
        retval = cv2.imwrite(pic_full_path, img2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        # if not retval:
        #     logging.debug(f'{ip}保存图像失败')
    except Exception as e:
        logging.debug(f'{cam_ip} cv2 失败{e}')
    finally:
        cam.release()
        cv2.destroyAllWindows()

        if not os.path.isfile(pic_full_path):
            logging.info(f'{cam_ip}保存截图失败')
            return -2
        else:
            logging.info(f"{cam_ip}保存截图成功")
            return 1


if __name__ == "__main__":
    # 包含ip和密码的csv文件
    csv_file = r'./txt/ruizhi.csv'
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
                result = hik_cv2(ip, password, dir_pre=os.path.basename(csv_file).split('.')[0])

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
    failed_file = os.path.basename(csv_file).replace('.csv', '') + '_' + time.strftime("%Y%m%d%H%M%S",
                                                                                       time.localtime()) + '.csv'
    with open(failed_file, 'w', newline='') as fp:
        csv_writer = csv.writer(fp)
        csv_writer.writerows(ip_passwd)
