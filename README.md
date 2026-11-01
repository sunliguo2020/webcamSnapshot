# webcamSnapshot

网络摄像头批量截图工具，可从 CSV 读取设备信息并批量采集画面，帮助快速核对摄像头与实际监控场景。

## 支持的设备

- 海康威视摄像头
- 大华摄像头
- 支持 ONVIF 协议的网络摄像头
- 电脑连接的 USB 摄像头

## 功能

- 选择并预览摄像头 CSV 文件
- 自定义截图保存目录
- 选择是否添加时间水印
- 批量截图期间可暂停或继续
- 在界面中查看运行日志
- 查看任务结果，并打开截图目录

## 运行

项目使用 Python 和 Tkinter 图形界面。安装依赖后，从项目根目录启动：

```bash
python -m pip install -r requirements.txt
python main.py
```

## 摄像头 CSV 格式

网络摄像头列表使用 CSV 文件。首行必须包含 `ip` 和 `password` 两列，列名不区分大小写；其他列可按需添加。

```csv
ip,password
192.168.1.100,admin123
192.168.1.101,password456
```

## 截图保存位置

截图保存到界面中选择的目录，并按日期和时间建立子目录。未指定保存目录时，网络摄像头截图默认按 CSV 文件名归类。

## 常见 ONVIF 端口参考

| 厂商 | 常见端口 |
| --- | ---: |
| 雄迈 | 8899 |
| 大华 | 80 |
| 海康威视 | 80 |

实际端口请以设备配置为准。

## 打包为 EXE

在项目根目录运行：

```bash
python make.py
```

如需减小 EXE 体积，可在打包环境中安装 UPX 并将其加入 `PATH`。未安装 UPX 不影响打包；使用 UPX 压缩可能触发部分杀毒软件误报。

## 依赖

依赖列表见 [requirements.txt](requirements.txt)。

## 更新日志

参见 [CHANGELOG.md](CHANGELOG.md)。
