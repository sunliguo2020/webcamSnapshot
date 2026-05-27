# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-02-15 18:13
将通用的函数放在一起。
"""
import csv
import logging
import os
import socket
from typing import Dict, Iterator, Optional

logger = logging.getLogger('camera_logger')


def is_port_open(ip, port):
    """
    检测某个ip地址的端口是否开启
    :param ip:
    :param port:
    :return:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    state = sock.connect_ex((ip, port))
    if 0 == state:
        # print("port is open")
        return True
    else:
        # print("port is closed")
        return False


def is_reachable(ip):
    """检测某个ip是否通

    Args:
        ip (_type_): IP地址

    Returns:
        _type_: 0 或 1
    """
    response = os.system('ping -c 1' + ip)
    if response == 0:
        print(ip + 'is reachable')
        return 1
    else:
        print(ip + 'is not reachable')
        return 0


def is_ipv4(ip: str) -> bool:
    """
    检查ip是否合法
    :param: ip ip地址
    :return: True 合法 False 不合法
    """
    return True if [1] * 4 == [x.isdigit() and 0 <= int(x) <= 255 for x in ip.split(".")] else False


def gen_ip_password_from_csv(file_path, start_line=0):
    """
    读取csv文件，返回ip，password
    :param file_path: 要读取的csv文件
    :param start_line: 跳过前几行
    :return: ip,password
    """
    # 判断文件是否存在
    if not os.path.isfile(file_path):
        raise FileNotFoundError
    # 判断是否是csv文件
    # 读取文件
    with open(file_path, encoding='utf-8') as f:
        # 跳过前几行
        for i in range(start_line):
            next(f)  # 跳过一行
        try:
            csv_read = csv.reader(f)
            for row in csv_read:
                # 读取每行的前两列
                cam_ip = row[0].strip()
                cam_pwd = row[1].strip()
                yield cam_ip, cam_pwd
        except UnicodeDecodeError as e:
            logger.error(e)
            return -1
        except Exception as e:
            logger.debug(e)
            return -1


def convert_ip_list(csv_file):
    """
    读取csv文件的前2字段，转换为 ip和密码的字典
    @param csv_file:
    @return: 包含ip，password，状态等字典的列表
    """
    cam_list = []
    # 将csv文件转为 摄像头对象的列表
    with open(csv_file) as fp:
        for item in csv.reader(fp):
            cam_list.append({'ip': item[0],
                             'password': item[1],
                             'time': 0,
                             'status': False})
    return cam_list


def get_cam_list(csv_file: str, required_fields: Optional[list] = None) -> Iterator[Dict[str, str]]:
    """
    读取csv文件并转换为字典生成器
    csv文件第一行为字典的键
    读取csv文件的，转换为 字典
    @param required_fields: 必须包含的字段列表，如果缺少会抛出异常
    @param csv_file: csv文件路径
    @return: 生成器，每次产生一行数据的字典
    异常：
        ValueError
    """
    # 默认必要字段
    if required_fields is None:
        required_fields = ['ip', 'password']

    try:
        with open(csv_file, 'r', encoding='utf-8') as fp:
            # 检查文件是否为空
            first_line = fp.readline()
            if not first_line:
                raise ValueError(f"CSV文件 '{csv_file}' 是空的")
            fp.seek(0)  # 重置文件指针

            reader = csv.DictReader(fp)

            # 检查是否有表头
            if not reader.fieldnames:
                logger.debug(f"CSV文件 '{csv_file}' 缺少表头")
                raise ValueError(f"CSV文件 '{csv_file}' 缺少表头")
            else:
                logger.debug(f"CSV文件 '{csv_file}' 表头: {reader.fieldnames}")

            # 检查必要字段
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            if missing_fields:
                raise ValueError(f"CSV文件 '{csv_file}' 缺少必要字段: {missing_fields}")

            line_num = 1  # 第一行是header，从第二行开始计数
            for line_num, row in enumerate(reader, 2):  # 从第2行开始计数
                # 检查必要字段是否有值
                missing_values = [field for field in required_fields if not row.get(field)]
                if missing_values:
                    logger.warning(f"第 {line_num} 行缺少值: {missing_values}")
                    continue

                # 清理数据：去除字符串两端的空格
                cleaned_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}

                yield cleaned_row

    except FileNotFoundError:
        logger.error(f"文件不存在: {csv_file}")
        raise
    except UnicodeDecodeError:
        logger.error(f"文件编码错误，请确保使用UTF-8编码: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"处理CSV文件时发生意外错误: {e}")
        raise


def validate_csv_file(csv_file):
    """
    检验csv文件的合法性
    @param csv_file: csv文件路径
    @return: None
    @raises FileNotFoundError: 文件不存在
    @raises ValueError: 文件格式错误
    """
    logger.info(f"开始校验csv文件：{csv_file}")
    # 1、判断文件是否存在
    if not os.path.isfile(csv_file):
        logger.error('csv文件不存在')
        raise FileNotFoundError("CSV文件不存在，请重新选择")
    # 2、判断扩展名
    if not csv_file.lower().endswith(".csv"):
        logger.error("选择的不是csv文件")
        raise ValueError("请选择csv文件")
    # 3、校验头部
    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # 空文件
            if reader.fieldnames is None:
                raise ValueError("CSV为空")

            headers = [h.strip().lower() for h in reader.fieldnames]

            logger.debug(f"csv表头：{headers}")

            required_headers = {"ip", "password"}

            if not required_headers.issubset(headers):
                logger.error(
                    "csv缺少必要字段：ip,password"
                )
                raise ValueError("CSV首行必须包含 ip,password")

    except UnicodeDecodeError:
        logger.exception("csv编码错误")
        raise ValueError("CSV编码错误，请使用UTF-8")
    except Exception:
        logger.exception("读取csv文件失败")
        raise

    logger.info('csv文件校验通过')


if __name__ == '__main__':
    for item in get_cam_list(r'd:/寿光泽润.csv'):
        print(item)
