### onvif开发流程

发现设备 ==》 获取能力 ==》 获取媒体信息 ==》 获取[视频编码](https://so.csdn.net/so/search?q=视频编码&spm=1001.2101.3001.7020)配置 ==》 设置视频编码配置 ==》 获取URI ==》 ONVIF完成 ==》 RTSP播放 ==》 解码

### ONVIF搜索设备

1、设备搜索原理

设备服务器监听239.255.255.250的3702端口。所以，如果要实现跨网段搜索onvif设备需要路由的支持。只要组播数据包能收到，设备就能被搜到。

当ONVIF客户端向同意网段内的多播地址239.255.255.2550，端口3702发送多播消息，接收到消息的ONVIF服务会返回自己的IP，UUID，DeviceServiceAddress，而DeviceServiceAddress就是设备提供ONVIF服务的地址。

2、设备搜索实现

ONVIF客户端首先发起ws-discovery，查找同一网段内的所有设备，设备在接收到ws-discovery之后进行响应：

- 创建组播的udp socket
- socket加入多播组239.255.255.250，端口3702
- socket发送搜索数据，Probe类型的数据探测包

#### python开发onvif客户端

1、原理简介

onvif协议接口由多个模块组成，每个模块分别对应不同的WSDL文件。

### ONVIF 获取RTSP地址

#### 流程总览：

- **搜索：Probe**： 发现网络摄像头，获取webserver地址：http://192.168.15.240/onvif/device_service
- **能力获取：GetCapabilities**：获取设备能力文件，从中识别出媒体信息地址URI： http://192.168.15.240/onvif/Media
- **媒体信息获取：GetProfiles**： 获取媒体信息文件，识别主通道、子通道的视频编码分辨率
- **RTSP地址获取：GetStreamUri**：获取指定通道的流媒体地址 rtsp://192.168.15.240:554/Streaming/Channels/2?transportmode=unicast