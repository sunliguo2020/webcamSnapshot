# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 7:55
"""
def capture(ip):
    """

    @param ip:
    @return:
    """
    url = f'http://{ip}/webcapture.jpg?command=snap&channel=1'
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        with open(f'{ip}.jpg', 'wb') as f:
            f.write(response.content)
        print(f'{ip} 抓取成功')
    else:
        print(f'{ip} 抓取失败')

if __name__ == '__main__':
    capture('172.21.67.251')
    # capture('172.21.65.169')