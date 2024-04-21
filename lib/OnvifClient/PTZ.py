from time import sleep

from lib import OnvifClient


class PTZ:
    def __init__(self, client: OnvifClient):

        self.media = client.media

        self.media_profile = self.media.GetProfiles()[0]
        token = self.media_profile.token
        self.ptz = self.media.create_ptz_service()

        # Get available PTZ services
        request = self.ptz.create_type('GetServiceCapabilities')
        Service_Capabilities = self.ptz.GetServiceCapabilities(request)

        # Get PTZ status
        status = self.ptz.GetStatus({'ProfileToken': token})

        # Get PTZ configuration options for getting option ranges
        request = self.ptz.create_type('GetConfigurationOptions')
        request.ConfigurationToken = self.media_profile.PTZConfiguration.token
        ptz_configuration_options = self.ptz.GetConfigurationOptions(request)

        self.requestc = self.ptz.create_type('ContinuousMove')
        self.requestc.ProfileToken = self.media_profile.token

        self.requesta = self.ptz.create_type('AbsoluteMove')
        self.requesta.ProfileToken = self.media_profile.token

        self.requestr = self.ptz.create_type('RelativeMove')
        self.requestr.ProfileToken = self.media_profile.token

        self.requests = self.ptz.create_type('Stop')
        self.requests.ProfileToken = self.media_profile.token

        self.requestp = self.ptz.create_type('SetPreset')
        self.requestp.ProfileToken = self.media_profile.token

        self.requestg = self.ptz.create_type('GotoPreset')
        self.requestg.ProfileToken = self.media_profile.token

        # self.stop()

    def __del__(self):
        self.stop()

    def stop(self):
        self.requests.PanTilt = True
        self.requests.Zoom = True

        self.ptz.Stop(self.requests)

    # Continuous move functions
    def perform_move(self, timeout, x, y):
        # Start continuous move
        # ret = self.ptz.ContinuousMove(self.requestc)

        self.ptz.ContinuousMove({
            'ProfileToken': self.media_profile.token,
            'Velocity': {
                'PanTilt': {'x': x, 'y': y}
                # 'Zoom': {'x': 1.0}
            }
        })

        sleep(timeout)
        self.stop()

    def move_absolute(self, x, y, velocity):
        # self.requesta.Position.PanTilt._x = pan
        # self.requesta.Position.PanTilt._y = tilt
        # self.requesta.Speed.PanTilt._x = velocity
        # self.requesta.Speed.PanTilt._y = velocity
        # ret = self.ptz.AbsoluteMove(self.requesta)

        self.ptz.AbsoluteMove({
            'ProfileToken': self.media_profile.token,
            'Position': {
                'PanTilt': {'x': x, 'y': y}
            },
            'Speed': {
                'PanTilt': {'x': velocity, 'y': velocity}
            }
        })

        # ret = self.ptz.AbsoluteMove(self.requesta, Position={
        #     'PanTilt': {'x': pan, 'y': tilt}
        # })

        sleep(2)

        # Relative move functions --NO ERRORS BUT CAMERA DOES NOT MOVE

    def move_relative(self, pan, tilt, velocity):
        # self.requestr.Translation.PanTilt._x = pan
        # self.requestr.Translation.PanTilt._y = tilt
        # self.requestr.Speed.PanTilt._x = velocity
        # ret = self.requestr.Speed.PanTilt._y = velocity
        # self.ptz.RelativeMove(self.requestr)

        self.ptz.RelativeMove({
            'ProfileToken': self.media_profile.token,
            'Translation': {'PanTilt': {'x': pan, 'y': tilt}}
        })
        sleep(2.0)

    def zoom(self, zoom, timeout):
        pass
        # self.requestc.Velocity.Zoom._x = velocity
        # self.perform_move(timeout)
        self.ptz.ContinuousMove({
            'ProfileToken': self.media_profile.token,
            'Velocity': {
                'PanTilt': {'x': 0, 'y': 0},
                'Zoom': {'x': zoom}
            }
        })

        sleep(timeout)
        self.stop()

    def move_y(self, val, timeout):
        # self.requestc.Velocity.PanTilt._x = 0.0
        # self.requestc.Velocity.PanTilt._y = velocity
        self.perform_move(timeout, x=0.0, y=val)

    def move_x(self, val, timeout):
        # self.requestc.Velocity.PanTilt._x = velocity
        # self.requestc.Velocity.PanTilt._y = 0.0
        self.perform_move(timeout, x=val, y=0.0)

    # Sets preset set, query and and go to
    def set_preset(self, name):
        self.requestp.PresetName = name
        self.requestp.PresetToken = '1'
        self.preset = self.ptz.SetPreset(self.requestp)  # returns the PresetToken

    def get_preset(self):
        presets = self.ptz.GetPresets({'ProfileToken': self.media_profile.token})
        print("presets:", presets)

    def goto_preset(self, name):
        try:
            self.ptz.GotoPreset(
                {'ProfileToken': self.media_profile.token, "PresetToken": name})  # 移动到指定预置点位置
        except Exception as e:
            print("云台控制失败：%s" % str(e))
