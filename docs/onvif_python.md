### 一、安装

1、python2.x

```
pip install onvif
```

2、python 3.x

```
pip  install onvif_zeep
```

### 二、onvif控制

函数使用流程：

- 创建对象：ptz,imaging,media
- 调用对象方法
- 设置参数：
  - 字典形式，无需初始化
  - 属性形式，部分需要初始化
- 使用函数

初始化ONVIFCamera对象camera

创建媒体对象

media = camera.create_media_service()



profiles = media.GetPRofiles()

### IPC图像抓拍的两种方式

- 对RTSP视频流进行视频截图
- 使用HTTP的GET方式获取图片

获取抓拍的URL，使用media模块的GetSnapshotUri接口可获取图像抓拍的URL。

编码流程

1. 通过「设备发现」，得到 「设备服务地址」。
2. 使用「设备服务地址」调用GetCapabilities接口，得到「媒体服务地址」。
3. 使用「媒体服务地址」调用GetProfiles接口，得到主次码流的「媒体配置信息」，其中包含ProfileToken。
4. 使用ProfileToken 调用GetSnapshotUri接口，得到主次码图像抓拍的URI地址。
5. 根据URI地址，使用HTTP的GET方式获取图片。****

代码示例：

```python
cam = ONVIFCamera(ip, port, usr, pwd)
media = cam.create_media_service()
# 获取媒体配置信息
profiles = media.GetProfiles()

# 主码流
self.media_profile = self.profiles[0]

res = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})
# 登录认证截图
response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password))
with open(file_path, 'wb') as f:  # 保存截图
     f.write(response.content)
```



```python
from onvif import ONVIFCamera

class myONVIF():
    def __init__(self, ip, usr, pwd):
        self.usr = usr
        self.pwd = pwd
        self.cam = ONVIFCamera(ip, 80, usr, pwd)
        self.ptz = self.cam.create_ptz_service()
        self.media = self.cam.create_media_service()
        self.imaging = self.cam.create_imaging_service()
        self.profile = self.cam.media.GetProfiles()[0]

    def get_ptz_status(self):
        # 获取PTZ状态
        request = self.cam.ptz.create_type('GetStatus')
        request.ProfileToken = self.profile.token
        status = self.cam.ptz.GetStatus(request)
        return {'pan': status.Position.PanTilt.x, 'tilt': status.Position.PanTilt.y, 'zoom': status.Position.Zoom.x}

    def set_home(self):
        # 设置归位点
        request = self.cam.ptz.create_type('SetHomePosition')  # 设置当前位置为原点位置
        request.ProfileToken = self.profile.token
        self.cam.ptz.SetHomePosition(request)

    def move_home(self):
        # 归位
        request = self.cam.ptz.create_type('GotoHomePosition')  # 回到原点位置
        request.ProfileToken = self.profile.token
        if request.Speed is None:  # 设置归位的速度
            request.Speed = self.cam.ptz.GetStatus({'ProfileToken': self.profile.token}).Position
        self.cam.ptz.GotoHomePosition(request)

    def abs_move(self, pan, tilt, zoom):
        # 绝对移动
        request = self.ptz.create_type('AbsoluteMove')
        request.ProfileToken = self.profile.token
        request.Position = {'PanTilt':{'x':pan, 'y':tilt}, 'Zoom':zoom}
        request.Speed = {'PanTilt':{'x':1, 'y':1}, 'Zoom':1}    # default speed
        self.ptz.AbsoluteMove(request)

    def continue_move(self, speed_pan, speed_tilt, speed_zoom):
        # 持续移动
        request = self.ptz.create_type("ContinuousMove")
        request.ProfileToken =  self.profile.token
        request.Velocity = {'PanTilt':{'x':speed_pan, 'y':speed_tilt}, 'Zoom':speed_zoom}
        self.ptz.ContinuousMove(request)

    def relative_move(self, pan, tilt, zoom):
        # 相对移动
        request = self.cam.ptz.create_type('RelativeMove')
        request.ProfileToken = self.profile.token
        request.Translation = {'PanTilt':{'x':pan, 'y':tilt}, 'Zoom':zoom}
        request.Speed = {'PanTilt':{'x':1, 'y':1}, 'Zoom':1}
        self.ptz.RelativeMove(request)

    def stop_move(self):
        # 停止
        self.ptz.Stop({'ProfileToken': self.profile.token})

    def snap_image(self, path):
        # 抓拍图像
        import requests, os
        res = self.media.GetSnapshotUri({'ProfileToken': self.profile.token})
        auth = requests.auth.HTTPDigestAuth(self.usr, self.pwd)
        response = requests.get(url=res.Uri, auth=auth)
        path_out = os.path.join(path, 'tmp.jpg')
        with open(path_out, 'wb') as fp:
            fp.write(response.content)

    def get_rtsp(self):
        # 获取rtsp
        obj = self.media.create_type('GetStreamUri')
        obj.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
        obj.ProfileToken = self.profile.token
        res_uri = self.media.GetStreamUri(obj)['Uri']
        return res_uri

    def get_image_status(self):
        # 获取焦距不起作用？？？
        request = self.imaging.create_type('GetStatus')
        request.VideoSourceToken = self.profile.VideoSourceConfiguration.SourceToken
        return self.imaging.GetStatus(request)

    def abs_move_image(self, pos, speed=1):
        # 焦距绝对移动
        request = self.imaging.create_type('Move')
        request.VideoSourceToken = self.profile.VideoSourceConfiguration.SourceToken
        request.Focus = {'Absolute': {'Position': pos, 'Speed': speed}}
        self.imaging.Move(request)

    def continue_move_image(self, speed=1):
        # 焦距持续移动
        request = self.imaging.create_type('Move')
        request.VideoSourceToken = self.profile.VideoSourceConfiguration.SourceToken
        request.Focus = {'Continuous':{'Speed':0.5}}
        self.imaging.Move(request)

    def relative_move_image(self, dist, speed=1):
        # 焦距相对移动
        request = self.imaging.create_type('Move')
        request.VideoSourceToken = self.profile.VideoSourceConfiguration.SourceToken
        request.Focus = {'Relative': {'Distance':dist, 'Speed':speed}}
        self.imaging.Move(request)

    def stop_move_image(self):
        # 焦距停止移动
        self.imaging.Stop({'VideoSourceToken': self.profile.VideoSourceConfiguration.token})

if __name__ == "__main__":
    pass

```

