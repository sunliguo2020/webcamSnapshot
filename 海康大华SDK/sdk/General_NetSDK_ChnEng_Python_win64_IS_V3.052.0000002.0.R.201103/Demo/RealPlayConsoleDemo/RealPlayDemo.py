# coding=utf-8
import sys
from ctypes import *

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, fDecCBFun, fRealDataCallBackEx2
from NetSDK.SDK_Enum import SDK_RealPlayType, EM_LOGIN_SPAC_CAP_TYPE, EM_REALDATA_FLAG
from NetSDK.SDK_Struct import C_LLONG, sys_platform, NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY, PLAY_FRAME_INFO


class RealPlayDemo:
    def __init__(self):

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.playID = C_LLONG()
        self.freePort = c_int()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)
        self.m_RealDataCallBack = fRealDataCallBackEx2(self.RealDataCallBack)

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        self.ip = ''
        self.port = 0
        self.username = ''
        self.password = ''
        self.channel = 0
        self.streamtype = 0

    def get_login_info(self):
        print("请输入登录信息(Please input login info)")
        print("")
        self.ip = input('地址(IP address):')
        self.port = int(input('端口(port):'))
        self.username = input('用户名(username):')
        self.password = input('密码(password):')

    def login(self):
        if not self.loginID:
            stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
            stuInParam.szIP = self.ip.encode()
            stuInParam.nPort = self.port
            stuInParam.szUserName = self.username.encode()
            stuInParam.szPassword = self.password.encode()
            stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
            stuInParam.pCapParam = None

            stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

            self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
            if self.loginID != 0:
                print("登录成功(Login succeed). 通道数量(Channel num):" + str(device_info.nChanNum))
                return True
            else:
                print("登录失败(Login failed). " + error_msg)
                return False

    def logout(self):
        if self.loginID:
            if self.playID:
                self.sdk.StopRealPlayEx(self.playID)
                self.playID = 0

            self.sdk.Logout(self.loginID)
            self.loginID = 0
        print("登出成功(Logout succeed)")

    def get_realplay_info(self):
        print("")
        print("请输入实时监视信息(Please input realplay info)")
        print("")
        self.channel = int(input('通道(channel):'))
        self.streamtype = int(input('码流类型(0:主码流; 1:辅码流)(stream type(0:Main Stream; 1:Extra Stream)):'))

    def realplay(self):
        if not self.playID:
            if self.streamtype == 0:
                stream_type = SDK_RealPlayType.Realplay
            else:
                stream_type = SDK_RealPlayType.Realplay_1
            self.playID = self.sdk.RealPlayEx(self.loginID, self.channel, 0, stream_type)
            if self.playID != 0:
                self.sdk.SetRealDataCallBackEx2(self.playID, self.m_RealDataCallBack, None, EM_REALDATA_FLAG.RAW_DATA)
                print("实时监视成功(RealPlay succeed).")
                return True
            else:
                print("实时监视失败(RealPlay fail). "+ self.sdk.GetLastErrorMessage())
                return False

    def stop_realplay(self):
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
            self.playID = 0
        print("停止实时监视成功(Stop RealPlay succeed).")

    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        print("实时监视(RealPlay)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        print("实时监视(RealPlay)-在线(OnLine)")

    # 拉流回调函数功能
    def RealDataCallBack(self, lRealHandle, dwDataType, pBuffer, dwBufSize, param, dwUser):
        if lRealHandle == self.playID:
            if dwDataType == 0:
                print("码流大小(Stream size):" + str(dwBufSize) + ". 码流类型:原始未加密码流(Stream type:original unencrypted stream)")

    # 关闭主窗口时清理资源
    def quit_demo(self):
        if  self.loginID:
            self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()
        print("程序结束(Demo finish)")

if __name__ == '__main__':
    my_demo = RealPlayDemo()
    my_demo.get_login_info()
    result = my_demo.login()
    if not result:
        my_demo.quit_demo()
    else:
        my_demo.get_realplay_info()
        result = my_demo.realplay()
        if not result:
            my_demo.quit_demo()
        else:
            temp = input('输入任意键停止实时监视(Enter any key to stop realplay):')
            my_demo.stop_realplay()
            my_demo.logout()
            my_demo.quit_demo()

