### ONVIF搜索设备

1、设备搜索原理

当ONVIF客户端向同意网段内的多播地址239.255.255.2550，端口3702发送多播消息，接收到消息的ONVIF服务会返回自己的IP，UUID，DeviceServiceAddress，而DeviceServiceAddress就是设备提供ONVIF服务的地址。

2、设备搜索实现

ONVIF客户端首先发起ws-discovery，查找同一网段内的所有设备，设备在接收到ws-discovery之后进行响应：

- 创建组播的udp socket
- socket加入多播组239.255.255.250，端口3702
- socket发送搜索数据，Probe类型的数据探测包

#### python开发onvif客户端

1、原理简介

onvif协议接口由多个模块组成，每个模块分别对应不同的WSDL文件。