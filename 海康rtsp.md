### 海康rtsp取流url地址规则

1、1预览取流

2012年前的设备支持老的取流格式，之后的设备新老取流格式都支持

```
rtsp://username:password@<ipaddress>/<videotype>/ch<number>/<streamtype>
```

详细描述：

- username 设备用户名
- password 密码
- <ipaddress> 设备ip地址：RTSP端口号
- <videotype> 视频编码格式：h264或者mpeg4
- ch<number>通道号 ch1:模拟通道1，ch2：模拟通道2 ch33:IP通道1，ch34：IP通道2
- <streamtype>码流类型 main/av_stream主码流 sub/av_stream子码流

**举例说明：**

DS-9016HF-ST的IP通道01主码流：

rtsp://admin:12345@172.6.22.106:554/h264/ch33/main/av_stream

DS-9016HF-ST的模拟通道01子码流：

rtsp://admin:12345@172.6.22.106:554/h264/ch1/sub/av_stream

DS-9016HF-ST的零通道主码流（零通道无子码流）：

rtsp://admin:12345@172.6.22.106:554/h264/ch0/main/av_stream

DS-2DF7274-A的第三码流：

 rtsp://admin:12345@172.6.10.11:554/h264/ch1/stream3/av_stream

新版本：

```
rtsp://username:password@<address>:<port>/Streaming/Channels/<id>(?parm1=value1&parm2-=value2…)
```

- username设备用户名
- password密码
- < address >:< port >设备ip地址：RTSP端口   
- <id>通道号&码流类型 101：通道1主码流 102：通道1子码流 103:通道1第三码流

举例说明：**

DS-9632N-ST的IP通道01主码流：

rtsp://admin:12345@172.6.22.234:554/Streaming/Channels/101?transportmode=unicast

DS-9016HF-ST的IP通道01主码流：

rtsp://admin:12345@172.6.22.106:554/Streaming/Channels/1701?transportmode=unicast

DS-9016HF-ST的模拟通道01子码流：

rtsp://admin:12345@172.6.22.106:554/Streaming/Channels/102?transportmode=unicast  (单播)

rtsp://admin:12345@172.6.22.106:554/Streaming/Channels/102?transportmode=multicast (多播)

rtsp://admin:12345@172.6.22.106:554/Streaming/Channels/102 (?后面可省略，默认单播)

DS-9016HF-ST的零通道主码流（零通道无子码流）：

rtsp://admin:12345@172.6.22.106:554/Streaming/Channels/001

DS-2DF7274-A的第三码流：

rtsp://admin:12345@172.6.10.11:554/Streaming/Channels/103

>  注：**前面老URL，N**[**VR**](https://cloud.tencent.com/developer/tools/blog-entry?target=https%3A%2F%2Fjavaforall.cn%2Ftag%2Fvr&source=article&objectId=2036458)**（>=64路的除外）的IP通道从33开始；新URL，通道号全部按顺序从1开始。**