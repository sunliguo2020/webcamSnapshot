### webcamSnapshot



##### 项目背景：

维护着很多摄像头，资料一直很不准确。某天一个摄像头故障，通道名称描述不是很准确，无法很快找到这个摄像头。我想，在摄像头正常的时候，每个摄像头都能截一张图。那么维护的时候不是就很容易找到它了吗？手工截图很慢，就可以用python来解决这个问题。

一开始用摄像头厂商的sdk来截图，发现比较复杂。后来从网上找到了可以用rstp协议，还可以用onvif协议来截图。 

更新：

2020-10-14： 1、实现抓取大华录像机的多通道截图。

