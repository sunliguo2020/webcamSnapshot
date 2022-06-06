import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGroupBox, QMenu, QMessageBox
from PyQt5.QtGui import QPixmap

from CapturePictureUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Enum import EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE

@CB_FUNCTYPE(None, C_LLONG, POINTER(c_ubyte), c_uint, c_uint, C_DWORD, C_LDWORD)
def CaptureCallBack(lLoginID,pBuf,RevLen,EncodeType,CmdSerial,dwUser):
    if lLoginID == 0:
        return
    print('Enter CaptureCallBack')
    wnd.update_ui(pBuf, RevLen, EncodeType)

class CaptureWnd(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(CaptureWnd, self).__init__()
        self.setupUi(self)
        # 界面初始化
        self.init_ui()

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

    def init_ui(self):
        self.IP_lineEdit.setText('172.23.8.94')
        self.Port_lineEdit.setText('37777')
        self.User_lineEdit.setText('admin')
        self.Pwd_lineEdit.setText('admin123')
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)

        self.Capture_pushButton.clicked.connect(self.capture_btn_onclick)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Capture_pushButton.setEnabled(False)

    def login_btn_onclick(self):
        ip = self.IP_lineEdit.text()
        port = int(self.Port_lineEdit.text())
        username = self.User_lineEdit.text()
        password = self.Pwd_lineEdit.text()
        stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stuInParam.szIP = ip.encode()
        stuInParam.nPort = port
        stuInParam.szUserName = username.encode()
        stuInParam.szPassword = password.encode()
        stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
        stuInParam.pCapParam = None

        stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
        if self.loginID != 0:
            self.setWindowTitle('抓图(Capture)-在线(OnLine)')
            self.Login_pushButton.setEnabled(False)
            self.Logout_pushButton.setEnabled(True)
            if(int(device_info.nChanNum) > 0):
                self.Capture_pushButton.setEnabled(True)
            for i in range(int(device_info.nChanNum)):
                self.Channel_comboBox.addItem(str(i))
        else:
            QMessageBox.about(self, '提示(prompt)', error_msg)

    def logout_btn_onclick(self):
        # 登出
        if (self.loginID == 0):
            return
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Capture_pushButton.setEnabled(False)
        self.setWindowTitle("抓图(Capture)-离线(OffLine)")
        self.loginID = 0
        self.Channel_comboBox.clear()
        self.Picture_label.clear()

    def capture_btn_onclick(self):
        # 设置抓图回调
        dwUser = 0
        self.sdk.SetSnapRevCallBack(CaptureCallBack, dwUser)
        channel = self.Channel_comboBox.currentIndex()
        snap = SNAP_PARAMS()
        snap.Channel = channel
        snap.Quality = 1
        snap.mode = 0
        # 抓图
        self.sdk.SnapPictureEx(self.loginID, snap)


    def update_ui(self, pBuf, RevLen, EncodeType):
        pic_buf = cast(pBuf, POINTER(c_ubyte*RevLen)).contents
        with open('./capture.jpg', 'wb+') as f:
            f.write(pic_buf)
        image = QPixmap('./capture.jpg').scaled(self.Picture_label.width(),
                                                        self.Picture_label.height())
        self.Picture_label.setPixmap(image)
	
	# 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("抓图(Capture)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('抓图(Capture)-在线(OnLine)')

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Picture_label.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = CaptureWnd()
    wnd.show()
    sys.exit(app.exec_())
