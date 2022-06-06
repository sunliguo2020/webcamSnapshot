from PyQt5.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QAbstractItemView, QApplication, QGroupBox, QMenu,QTableWidgetItem
from PyQt5.QtCore import Qt,QThread,pyqtSignal
import sys
import datetime
import types
import time

from AlarmListenUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE

global hwnd

class VideoMotionCallBackAlarmInfo:
    def __init__(self):
        self.time_str = ""
        self.channel_str = ""
        self.alarm_type = ""
        self.status_str = ""

    def get_alarm_info(self, alarm_info):
        self.time_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        self.channel_str = str(alarm_info.nChannelID)
        self.alarm_type = '动检事件（VideoMotion event)'
        if (alarm_info.nEventAction == 0):
            self.status_str = '脉冲(Pulse)'
        elif (alarm_info.nEventAction == 1):
            self.status_str = '开始(Start)'
        elif (alarm_info.nEventAction == 2):
            self.status_str = '结束(Stop)'

class BackUpdateUIThread(QThread):
    # 通过类成员对象定义信号
    update_date = pyqtSignal(int, object)

    # 处理业务逻辑
    def run(self):
        pass

@CB_FUNCTYPE(None, c_long, C_LLONG, POINTER(c_char), C_DWORD, POINTER(c_char), c_long, c_int, c_long, C_LDWORD)
def MessCallback(lCommand, lLoginID, pBuf, dwBufLen ,pchDVRIP, nDVRPort, bAlarmAckFlag, nEventID, dwUser):
    if(lLoginID != hwnd.loginID):
        return
    if(lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT):
        print('Enter MessCallback')
        alarm_info = cast(pBuf, POINTER(ALARM_MOTIONDETECT_INFO)).contents
        show_info = VideoMotionCallBackAlarmInfo()
        show_info.get_alarm_info(alarm_info)
        hwnd.backthread.update_date.emit(lCommand, show_info)

class StartListenWnd(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(StartListenWnd, self).__init__()
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

        #设置报警回调函数
        self.sdk.SetDVRMessCallBackEx1(MessCallback,0)

        # 创建线程
        self.backthread = BackUpdateUIThread()
        # 连接信号
        self.backthread.update_date.connect(self.update_ui)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        # 开始线程
        self.thread.started.connect(self.backthread.run)
        self.thread.start()


    def init_ui(self):
        self.IP_lineEdit.setText('172.23.8.95')
        self.Port_lineEdit.setText('37777')
        self.Username_lineEdit.setText('admin')
        self.Password_lineEdit.setText('admin123')
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)

        self.Alarmlisten_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Stopalarmlisten_pushButton.clicked.connect(self.detach_btn_onclick)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.row = 0
        self.column = 0

    def login_btn_onclick(self):
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['序号(No.)', '时间（Time)', '通道(Channel)', '报警类型(Alarm Type)', '状态(Status)'])
        ip = self.IP_lineEdit.text()
        port = int(self.Port_lineEdit.text())
        username = self.Username_lineEdit.text()
        password = self.Password_lineEdit.text()
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
            self.setWindowTitle('报警监听(Alarm Listen)-在线(OnLine)')
            self.Login_pushButton.setEnabled(False)
            self.Logout_pushButton.setEnabled(True)
            if (int(device_info.nChanNum) > 0):
                self.Alarmlisten_pushButton.setEnabled(True)
        else:
            QMessageBox.about(self, '提示(prompt)', error_msg)

    def logout_btn_onclick(self):
        # 登出
        if (self.loginID == 0):
            return
        # 停止报警监听
        self.sdk.StopListen(self.loginID)
        #登出
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.setWindowTitle("报警监听(Alarm Listen)-离线(OffLine)")
        self.loginID = 0
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['序号(No.)', '时间（Time)', '通道(Channel)', '报警类型(Alarm Type)', '状态(Status)'])

    def attach_btn_onclick(self):
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['序号(No.)', '时间（Time)', '通道(Channel)', '报警类型(Alarm Type)', '状态(Status)'])
        result = self.sdk.StartListenEx(self.loginID)
        if result:
            QMessageBox.about(self, '提示(prompt)', "报警监听成功(Subscribe alarm success)")
            self.Stopalarmlisten_pushButton.setEnabled(True)
            self.Alarmlisten_pushButton.setEnabled(False)
        else:
            QMessageBox.about(self, '提示(prompt)', 'error:' + str(self.sdk.GetLastError()))

    def detach_btn_onclick(self):
        if (self.loginID > 0):
            self.sdk.StopListen(self.loginID)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(True)

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.StopListen(self.loginID)
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Alarmlisten_tableWidget.clear()


    def update_ui(self, lCommand, show_info):
        if (lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT):
            if (self.row > 499):
                self.Alarmlisten_tableWidget.clear()
                self.Alarmlisten_tableWidget.setRowCount(0)
                self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(
                    ['序号(No.)', '时间（Time)', '通道(Channel)', '报警类型(Alarm Type)', '状态(Status)'])
                self.row = 0
                self.Alarmlisten_tableWidget.viewport().update()
            self.Alarmlisten_tableWidget.setRowCount(self.row + 1)
            item = QTableWidgetItem(str(self.row + 1))
            self.Alarmlisten_tableWidget.setItem(self.row, self.column, item)
            item1 = QTableWidgetItem(show_info.time_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 1, item1)
            item2 = QTableWidgetItem(show_info.channel_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 2, item2)
            item3 = QTableWidgetItem(show_info.alarm_type)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 3, item3)
            item4 = QTableWidgetItem(show_info.status_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 4, item4)
            self.row += 1
                # ui更新
            self.Alarmlisten_tableWidget.update()
            self.Alarmlisten_tableWidget.viewport().update()


    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("报警监听(Alarm Listen)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('报警监听(Alarm Listen)-在线(OnLine)')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = StartListenWnd()
    hwnd = wnd
    wnd.show()
    sys.exit(app.exec_())
