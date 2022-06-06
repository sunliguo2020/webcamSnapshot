# coding=utf-8
import sys
from PyQt5.QtWidgets import QMainWindow,QApplication, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread,pyqtSignal

from IntelligentTrafficUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import EM_LOGIN_SPAC_CAP_TYPE, EM_EVENT_IVS_TYPE
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE
import time
from queue import Queue

global wnd
callback_num = 0


class TrafficCallBackAlarmInfo:
    def __init__(self):
        self.time_str = ""
        self.plate_number_str = ""
        self.plate_color_str = ""
        self.object_subType_str = ""
        self.vehicle_color_str = ""

    def get_alarm_info(self, alarm_info):
        self.time_str = '{}-{}-{} {}:{}:{}'.format(alarm_info.UTC.dwYear, alarm_info.UTC.dwMonth, alarm_info.UTC.dwDay,
                                                   alarm_info.UTC.dwHour, alarm_info.UTC.dwMinute, alarm_info.UTC.dwSecond)
        self.plate_number_str = str(alarm_info.stTrafficCar.szPlateNumber.decode('gb2312'))
        self.plate_color_str = str(alarm_info.stTrafficCar.szPlateColor, 'utf-8')
        self.object_subType_str = str(alarm_info.stuVehicle.szObjectSubType, 'utf-8')
        self.vehicle_color_str = str(alarm_info.stTrafficCar.szVehicleColor, 'utf-8')

class BackUpdateUIThread(QThread):
    # 通过类成员对象定义信号
    update_date = pyqtSignal(int, object, int, bool, bool)

    # 处理业务逻辑
    def run(self):
        pass



@CB_FUNCTYPE(None, C_LLONG, C_DWORD, c_void_p, POINTER(c_ubyte), C_DWORD, C_LDWORD, c_int, c_void_p)
def AnalyzerDataCallBack(lAnalyzerHandle, dwAlarmType, pAlarmInfo, pBuffer, dwBufSize, dwUser, nSequence, reserved):
    print('Enter AnalyzerDataCallBack')
    # 当报警类型是交通卡口事件时在界面上进行显示相关信息
    if(lAnalyzerHandle == wnd.attachID)and(dwAlarmType == EM_EVENT_IVS_TYPE.TRAFFICJUNCTION):
        global callback_num
        local_path = os.path.abspath('.')
        is_global = False
        is_small = False
        show_info = TrafficCallBackAlarmInfo()
        callback_num += 1
        alarm_info = cast(pAlarmInfo, POINTER(DEV_EVENT_TRAFFICJUNCTION_INFO)).contents
        show_info.get_alarm_info(alarm_info)
        if alarm_info.stuObject.bPicEnble:
            is_global = True
            GlobalScene_buf = cast(pBuffer,POINTER(c_ubyte * alarm_info.stuObject.stPicInfo.dwOffSet)).contents
            if not os.path.isdir(os.path.join(local_path, 'Global')):
                os.mkdir(os.path.join(local_path, 'Global'))
            with open('./Global/Global_Img' + str(callback_num) + '.jpg', 'wb+') as global_pic:
                global_pic.write(bytes(GlobalScene_buf))
            if (alarm_info.stuObject.stPicInfo.dwFileLenth > 0):
                is_small = True
                small_buf = pBuffer[alarm_info.stuObject.stPicInfo.dwOffSet:alarm_info.stuObject.stPicInfo.dwOffSet +
                                                                        alarm_info.stuObject.stPicInfo.dwFileLenth]
                if not os.path.isdir(os.path.join(local_path, 'Small')):
                    os.mkdir(os.path.join(local_path, 'Small'))
                with open('./Small/Small_Img' + str(callback_num) + '.jpg', 'wb+') as small_pic:
                    small_pic.write(bytes(small_buf))
        elif (dwBufSize > 0):
            is_global = True
            GlobalScene_buf = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
            if not os.path.isdir(os.path.join(local_path, 'Global')):
                os.mkdir(os.path.join(local_path, 'Global'))
            with open('./Global/Global_Img' + str(callback_num) + '.jpg', 'wb+') as global_pic:
                global_pic.write(bytes(GlobalScene_buf))
        wnd.backthread.update_date.emit(dwAlarmType, show_info, callback_num, is_global, is_small)
        return

class TrafficWnd(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(TrafficWnd, self).__init__(parent)
        self.setupUi(self)
        # 界面初始化
        self._init_ui()

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.playID = C_LLONG()
        self.attachID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        # 创建线程
        self.backthread = BackUpdateUIThread()
        # 连接信号
        self.backthread.update_date.connect(self.update_UItable)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        # 开始线程
        self.thread.started.connect(self.backthread.run)
        self.thread.start()


    # 初始化界面
    def _init_ui(self):
        self.row = 0
        self.column = 0
        self.Login_pushButton.setEnabled(True)
        self.Play_pushButton.setEnabled(False)
        self.Logout_pushButton.setEnabled(False)
        self.StopPlay_pushButton.setEnabled(False)
        self.Attach_pushButton.setEnabled(False)
        self.Detach_pushButton.setEnabled(False)

        self.IP_lineEdit.setText('192.168.128.61')
        self.Port_lineEdit.setText('37777')
        self.User_lineEdit.setText('admin')
        self.Pwd_lineEdit.setText('admin123')

        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())

        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)
        self.Play_pushButton.clicked.connect(self.play_btn_onclick)
        self.StopPlay_pushButton.clicked.connect(self.stop_play_btn_onclick)
        self.Attach_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Detach_pushButton.clicked.connect(self.detach_btn_onclick)

    # 登录设备
    def login_btn_onclick(self):
        self.Attach_tableWidget.setHorizontalHeaderLabels(['时间(Time)', '事件(Event)', '车牌号(Plate No.)', '车牌颜色(Plate Color)', '车型类型(Vehicle Type)', '车身颜色(Vehicle Color)'])
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
        if self.loginID:
            self.setWindowTitle('智能交通(IntelligentTraffic)-在线(OnLine)')
            self.Logout_pushButton.setEnabled(True)
            self.Login_pushButton.setEnabled(False)
            self.Play_pushButton.setEnabled(True)
            self.Attach_pushButton.setEnabled(True)
            for i in range(int(device_info.nChanNum)):
                self.Channel_comboBox.addItem(str(i))
        else:
            QMessageBox.about(self, '提示(prompt)', error_msg)

    # 登出设备
    def logout_btn_onclick(self):
        # 停止拉流
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
            self.playID = 0
        # 停止订阅
        if self.attachID:
            self.sdk.StopLoadPic(self.attachID)
            self.attachID = 0
        # 登出
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Play_pushButton.setEnabled(False)
        self.StopPlay_pushButton.setEnabled(False)
        self.Attach_pushButton.setEnabled(False)
        self.Detach_pushButton.setEnabled(False)
        self.setWindowTitle("智能交通(IntelligentTraffic)-离线(OffLine)")
        self.loginID = C_LLONG(0)
        self.Channel_comboBox.clear()
        self.Attach_tableWidget.clear()
        self.Attach_tableWidget.setRowCount(0)
        self.Video_label.clear()
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        self.row = 0
        self.column = 0
        self.Attach_tableWidget.setHorizontalHeaderLabels(['时间(Time)', '事件(Event)', '车牌号(Plate No.)', '车牌颜色(Plate Color)', '车型类型(Vehicle Type)', '车身颜色(Vehicle Color)'])

    # 开始实施监视
    def play_btn_onclick(self):
        channel = self.Channel_comboBox.currentIndex()
        self.playID = self.sdk.RealPlayEx(self.loginID, channel, self.Video_label.winId())
        if self.playID:
            self.Play_pushButton.setEnabled(False)
            self.StopPlay_pushButton.setEnabled(True)
        else:
            QMessageBox.about(self, '提示(prompt)', 'error:' + str(self.sdk.GetLastError()))

    # 停止拉流
    def stop_play_btn_onclick(self):
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
        self.Play_pushButton.setEnabled(True)
        self.StopPlay_pushButton.setEnabled(False)
        self.playID = 0
        self.Video_label.repaint()

    # 智能交通卡口事件订阅
    def attach_btn_onclick(self):
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        self.Attach_tableWidget.setHorizontalHeaderLabels(['时间(Time)', '事件(Event)', '车牌号(Plate No.)', '车牌颜色(Plate Color)', '车型类型(Vehicle Type)', '车身颜色(Vehicle Color)'])
        channel = self.Channel_comboBox.currentIndex()
        bNeedPicFile = 1
        dwUser = 0
        self.attachID = self.sdk.RealLoadPictureEx(self.loginID, channel, EM_EVENT_IVS_TYPE.TRAFFICJUNCTION, bNeedPicFile, AnalyzerDataCallBack, dwUser, None)
        if not self.attachID:
            QMessageBox.about(self, '提示(prompt)', 'error:' + str(self.sdk.GetLastError()))
        else:
            self.Attach_pushButton.setEnabled(False)
            self.Detach_pushButton.setEnabled(True)
            QMessageBox.about(self, '提示(prompt)', "订阅成功(Subscribe success)")

    # 取消订阅
    def detach_btn_onclick(self):
        if (self.attachID == 0):
            return
        self.sdk.StopLoadPic(self.attachID)
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        self.attachID = 0
        self.Attach_pushButton.setEnabled(True)
        self.Detach_pushButton.setEnabled(False)
        self.Attach_tableWidget.setHorizontalHeaderLabels(['时间(Time)', '事件(Event)', '车牌号(Plate No.)', '车牌颜色(Plate Color)', '车型类型(Vehicle Type)', '车身颜色(Vehicle Color)'])


    def update_UItable(self, dwAlarmType, show_info,detect_object_id, is_global, is_small):
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        if(dwAlarmType == EM_EVENT_IVS_TYPE.TRAFFICJUNCTION):
            if(self.row > 499):
                self.Attach_tableWidget.clear()
                self.Attach_tableWidget.setRowCount(0)
                self.Attach_tableWidget.setHorizontalHeaderLabels(
                    ['时间(Time)', '事件(Event)', '车牌号(Plate No.)', '车牌颜色(Plate Color)', '车型类型(Vehicle Type)',
                    '车身颜色(Vehicle Color)'])
                self.row = 0
                # ui更新
                self.Attach_tableWidget.viewport().update()
            self.Attach_tableWidget.setRowCount(self.row + 1)
            item1 = QTableWidgetItem(show_info.time_str)
            self.Attach_tableWidget.setItem(self.row, self.column, item1)
            item2 = QTableWidgetItem('交通路口事件(Traffic junction event)')
            self.Attach_tableWidget.setItem(self.row, self.column + 1, item2)
            item3 = QTableWidgetItem(show_info.plate_number_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 2, item3)
            item4 = QTableWidgetItem(show_info.plate_color_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 3, item4)
            item5 = QTableWidgetItem(show_info.object_subType_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 4, item5)
            item6 = QTableWidgetItem(show_info.vehicle_color_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 5, item6)
            if (self.attachID != 0):
                if is_global:
                    image = QPixmap('./Global/Global_Img' + str(detect_object_id) + '.jpg').scaled(self.GlobalScene_label.width(),
                                                                                      self.GlobalScene_label.height())
                    self.GlobalScene_label.setPixmap(image)
                if is_small:
                    image = QPixmap('./Small/Small_Img' + str(detect_object_id) + '.jpg').scaled(self.SmallScene_label.width(),
                                                                                  self.SmallScene_label.height())
                    self.SmallScene_label.setPixmap(image)
            self.row += 1
            self.Attach_tableWidget.viewport().update()


    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("智能交通(IntelligentTraffic)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('智能交通(IntelligentTraffic)-在线(OnLine)')

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if self.attachID:
            self.sdk.StopLoadPic(self.attachID)
            self.attachID = 0
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
            self.playID = 0
        if self.loginID:
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Video_label.repaint()
        self.Attach_tableWidget.clear()
        self.Attach_tableWidget.setRowCount(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_wnd = TrafficWnd()
    wnd = my_wnd
    my_wnd.show()
    sys.exit(app.exec_())