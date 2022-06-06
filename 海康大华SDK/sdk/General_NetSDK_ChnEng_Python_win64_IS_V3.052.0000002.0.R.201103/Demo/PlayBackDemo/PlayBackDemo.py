# coding=utf-8
import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from ctypes import *

from PlayBackUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Enum import EM_USEDEV_MODE, EM_QUERY_RECORD_TYPE, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import NET_TIME, NET_RECORDFILE_INFO, NET_IN_PLAY_BACK_BY_TIME_INFO, NET_OUT_PLAY_BACK_BY_TIME_INFO, \
    C_LLONG, C_DWORD, C_LDWORD, NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY, CB_FUNCTYPE, sys_platform
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect

if sys_platform == 'windows':
    import tkinter as tk
    from tkinter import filedialog

# 继承QThread

class Mythread(QThread):
    # 定义信号,定义参数为int, int类型
    breakSignal = pyqtSignal(int, int)

    def __init__(self, parent=None, dwTotalSize = 1, dwDownLoadSize = 0):
        super().__init__(parent)
        self.dwTotalSize = dwTotalSize
        self.dwDownLoadSize = dwDownLoadSize

    def run(self):
        self.breakSignal.emit(self.dwTotalSize, self.dwDownLoadSize)

    def update_data(self, total_size, download_size):
        self.breakSignal.emit(total_size, download_size)

global wnd

@CB_FUNCTYPE(None, C_LLONG, C_DWORD, C_DWORD, C_LDWORD)
def DownLoadPosCallBack(lLoginID, pchDVRIP, nDVRPort, dwUser):
    pass


@CB_FUNCTYPE(c_int, C_LLONG, C_DWORD, POINTER(c_ubyte), C_DWORD, C_LDWORD)
def DownLoadDataCallBack(lPlayHandle, dwDataType, pBuffer, dwBufSize, dwUser):
    # buf_data = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
    # with open('./buffer.dav', 'ab+') as buf_file:
    #     buf_file.write(buf_data)
    return 1


@CB_FUNCTYPE(None, C_LLONG, C_DWORD, C_DWORD, c_int, NET_RECORDFILE_INFO, C_LDWORD)
def TimeDownLoadPosCallBack(lPlayHandle, dwTotalSize, dwDownLoadSize, index, recordfileinfo, dwUser):
    try:
        wnd.update_download_progress_thread(dwTotalSize, dwDownLoadSize)
    except Exception as e:
        print(e)


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        # 界面初始化
        self._init_ui()

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.playbackID = C_LLONG()
        self.downloadID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        self.thread = Mythread()
        self.thread.breakSignal.connect(self.update_download_progress)
        self.thread.start()

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        # demo内需要用到的变量
        self.pause_state = False
        self.record_count = 0
        self.record_infos = NET_RECORDFILE_INFO * 5000

    # 初始化界面
    def _init_ui(self):
        self.Login_pushButton.setText('登录(Login)')
        self.PlayBack_pushbutton.setText('回放(PlayBack)')
        self.PlayBack_pushbutton.setEnabled(False)

        self.IP_lineEdit.setText('172.23.12.231')
        self.Port_lineEdit.setText('37777')
        self.Name_lineEdit.setText('admin')
        self.Pwd_lineEdit.setText('admin123')

        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())

        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.PlayBack_pushbutton.clicked.connect(self.playback_btn_onclick)
        self.Pause_pushbutton.clicked.connect(self.pause_btn_onclick)
        self.Download_pushButton.clicked.connect(self.download_btn_onclick)
        self.SelectDate_calendarWidget.selectionChanged.connect(self.selectdate_calendar_onselectionChanged)
        self.StreamTyp_comboBox.currentIndexChanged.connect(self.stream_comboBox_oncurrentIndexChanged)

    def login_btn_onclick(self):
        if not self.loginID:
            ip = self.IP_lineEdit.text()
            port = int(self.Port_lineEdit.text())
            username = self.Name_lineEdit.text()
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
                self.setWindowTitle('回放(PlayBack)-在线(OnLine)')
                self.Login_pushButton.setText('登出(Logout)')
                self.Download_pushButton.setEnabled(True)
                self.Channel_comboBox.setEnabled(True)
                self.StreamTyp_comboBox.setEnabled(True)
                self.SelectDate_calendarWidget.setEnabled(True)
                self.SelectDate_calendarWidget.setSelectedDate(QDate.currentDate())
                self.set_stream_type(0)
                for i in range(int(device_info.nChanNum)):
                    self.Channel_comboBox.addItem(str(i))
            else:
                QMessageBox.about(self, '提示(prompt)', error_msg)
        else:
            if self.playbackID:
                self.sdk.StopPlayBack(self.playbackID)
                self.playbackID = 0
            if self.downloadID:
                self.sdk.StopDownload(self.downloadID)
                self.downloadID = 0
            result = self.sdk.Logout(self.loginID)
            if result:
                self.setWindowTitle("回放(PlayBack)-离线(OffLine)")
                self.Login_pushButton.setText("登录(Login)")
                self.loginID = 0
                self.StreamTyp_comboBox.setEnabled(False)
                self.PlayBack_pushbutton.setEnabled(False)
                self.Pause_pushbutton.setEnabled(False)
                self.Download_pushButton.setEnabled(False)
                self.Channel_comboBox.setEnabled(False)
                self.StreamTyp_comboBox.setEnabled(False)
                self.SelectDate_calendarWidget.setEnabled(False)
                self.exist_radioButton.setChecked(False)
                self.PlayBack_pushbutton.setText("回放(PlayBack)")
                self.Pause_pushbutton.setText("暂停(Pause)")
                self.Download_pushButton.setText("下载(download)")
                self.PlayBackWnd.repaint()
                self.Channel_comboBox.clear()
                self.Download_progressBar.setValue(0)
                self.thread.update_data(1, 0)

    def stream_comboBox_oncurrentIndexChanged(self):
        stream_type = self.StreamTyp_comboBox.currentIndex()
        self.set_stream_type(stream_type)

    def selectdate_calendar_onselectionChanged(self):
        if not self.loginID:
            return
        if self.playbackID:
            return
        self.exist_radioButton.setChecked(False)
        self.PlayBack_pushbutton.setEnabled(False)
        date = QDate(self.SelectDate_calendarWidget.selectedDate())
        startTime = NET_TIME()
        startTime.dwYear = date.year()
        startTime.dwMonth = date.month()
        startTime.dwDay = date.day()
        startTime.dwHour = 0
        startTime.dwMinute = 0
        startTime.dwSecond = 0

        endTime = NET_TIME()
        endTime.dwYear = date.year()
        endTime.dwMonth = date.month()
        endTime.dwDay = date.day()
        endTime.dwHour = 23
        endTime.dwMinute = 59
        endTime.dwSecond = 59

        result, fileCount, self.record_infos = self.query_file(startTime, endTime)
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
            return 0
        if fileCount > 0:
            self.record_count = fileCount
            self.exist_radioButton.setChecked(True)
            self.PlayBack_pushbutton.setEnabled(True)

    def playback_btn_onclick(self):
        if not self.playbackID:
            start_time = self.record_infos[0].starttime
            if self.record_count >= 2:
                end_time = self.record_infos[self.record_count - 2].endtime  # 最后一个录像，也就是self.record_infos[self.record_count-1]的endtime可能是0：0:0，所以取倒数第二个的结束时间
            else:
                end_time = self.record_infos[0].endtime

            inParam = NET_IN_PLAY_BACK_BY_TIME_INFO()
            inParam.hWnd = c_long(self.PlayBackWnd.winId())
            inParam.cbDownLoadPos = DownLoadPosCallBack
            inParam.dwPosUser = 0
            inParam.fDownLoadDataCallBack = DownLoadDataCallBack
            inParam.dwDataUser = 0
            inParam.nPlayDirection = 0
            inParam.nWaittime = 5000
            inParam.stStartTime.dwYear = start_time.dwYear
            inParam.stStartTime.dwMonth = start_time.dwMonth
            inParam.stStartTime.dwDay = start_time.dwDay
            inParam.stStartTime.dwHour = start_time.dwHour
            inParam.stStartTime.dwMinute = start_time.dwMinute
            inParam.stStartTime.dwSecond = start_time.dwSecond
            inParam.stStopTime.dwYear = end_time.dwYear
            inParam.stStopTime.dwMonth = end_time.dwMonth
            inParam.stStopTime.dwDay = end_time.dwDay
            inParam.stStopTime.dwHour = end_time.dwHour
            inParam.stStopTime.dwMinute = end_time.dwMinute
            inParam.stStopTime.dwSecond = end_time.dwSecond
            outParam = NET_OUT_PLAY_BACK_BY_TIME_INFO()

            nchannel = self.Channel_comboBox.currentIndex()
            self.playbackID = self.sdk.PlayBackByTimeEx2(self.loginID, nchannel, inParam, outParam)
            if self.playbackID != 0:
                self.PlayBack_pushbutton.setText("停止(Stop)")
                self.Pause_pushbutton.setEnabled(True)
                self.Channel_comboBox.setEnabled(False)
                self.StreamTyp_comboBox.setEnabled(False)
                self.SelectDate_calendarWidget.setEnabled(False)
                self.Channel_comboBox.repaint()
                self.StreamTyp_comboBox.repaint()
                self.PlayBackWnd.repaint()
            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
            result = self.sdk.StopPlayBack(self.playbackID)
            if result:
                self.PlayBack_pushbutton.setText("回放(PlayBack)")
                self.playbackID = 0
                self.PlayBackWnd.repaint()
                self.Pause_pushbutton.setText("暂停(Pause)")
                self.Pause_pushbutton.setEnabled(False)
                self.Channel_comboBox.setEnabled(True)
                self.StreamTyp_comboBox.setEnabled(True)
                self.SelectDate_calendarWidget.setEnabled(True)
            else:
                    QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())

    def pause_btn_onclick(self):
        if self.playbackID:
            self.pause_state = not self.pause_state
            result = self.sdk.PausePlayBack(self.playbackID, self.pause_state)
            if not result:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
                return
            if self.pause_state:
                self.Pause_pushbutton.setText("恢复(Resume)")
            else:
                self.Pause_pushbutton.setText("暂停(Pause)")
        else:
            pass

    def download_btn_onclick(self):
        if not self.downloadID:
            if sys_platform == 'windows':
                application_window = tk.Tk()
                application_window.withdraw()

                # 设置文件对话框会显示的文件类型
                save_filetypes = [('data', '.dav')]

                # 请求选择一个用以保存的文件
                save_file_name = filedialog.asksaveasfilename(parent=application_window,
															  initialdir=os.getcwd(),
															  title="Please select a file name for saving:",
															  filetypes=save_filetypes)
            else:
                save_file_name = os.path.dirname(__file__) + 'data.dav'

            stream_type = self.StreamTyp_comboBox.currentIndex()
            self.set_stream_type(stream_type)

            start_date = self.Start_dateTimeEdit.date()
            start_time = self.Start_dateTimeEdit.time()
            startDateTime = NET_TIME()
            startDateTime.dwYear = start_date.year()
            startDateTime.dwMonth = start_date.month()
            startDateTime.dwDay = start_date.day()
            startDateTime.dwHour = start_time.hour()
            startDateTime.dwMinute = start_time.minute()
            startDateTime.dwSecond = start_time.second()

            end_date = self.End_dateTimeEdit.date()
            end_time = self.End_dateTimeEdit.time()
            enddateTime = NET_TIME()
            enddateTime.dwYear = end_date.year()
            enddateTime.dwMonth = end_date.month()
            enddateTime.dwDay = end_date.day()
            enddateTime.dwHour = end_time.hour()
            enddateTime.dwMinute = end_time.minute()
            enddateTime.dwSecond = end_time.second()

            nchannel = self.Channel_comboBox.currentIndex()
            self.downloadID = self.sdk.DownloadByTimeEx(self.loginID, nchannel, int(EM_QUERY_RECORD_TYPE.ALL),
                                                        startDateTime, enddateTime, save_file_name,
                                                        TimeDownLoadPosCallBack, 0,
                                                        DownLoadDataCallBack, 0)
            if self.downloadID:
                self.Download_pushButton.setText("停止(Stop)")
            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
            result = self.sdk.StopDownload(self.downloadID)
            if result:
                self.downloadID = 0
                self.Download_pushButton.setText("下载(download)")
                self.Download_progressBar.setValue(0)
                self.thread.update_data(1, 0)
            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())

    def set_stream_type(self, stream_type):
        # set stream type;设置码流类型
        stream_type = c_int(stream_type)
        result = self.sdk.SetDeviceMode(self.loginID, int(EM_USEDEV_MODE.RECORD_STREAM_TYPE), stream_type)
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
            return 0, 0, None

    def query_file(self, startTime, endTime):
        # query record file 查询录像文件
        result, fileCount, infos = self.sdk.QueryRecordFile(self.loginID, 0, int(EM_QUERY_RECORD_TYPE.ALL), startTime,
                                                            endTime, None, 5000, False)
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
            return 0, 0, None
        return result, fileCount, infos

    def update_download_progress_thread(self, totalsize, downloadsize):
        try:
            self.thread.update_data(totalsize, downloadsize)
        except Exception as e:
            print(e)

    def update_download_progress(self, total_size, download_size):
        try:
            if download_size == -1:
                self.downloadID = 0
                self.Download_progressBar.setValue(0)
                self.sdk.StopDownload(self.downloadID)
                self.Download_pushButton.setText("下载(download)")
                QMessageBox.about(self, '提示(prompt)', "Download End(下载结束)!")
            elif download_size == -2:
                self.downloadID = 0
                self.Download_progressBar.setValue(0)
                self.Download_pushButton.setText("下载(download)")
                QMessageBox.about(self, '提示(prompt)', "Download Failed(下载失败)!")
            else:
                if download_size >= total_size:
                    self.Download_progressBar.setValue(100)
                else:
                    percentage = int(download_size * 100 / total_size)
                    self.Download_progressBar.setValue(percentage)
        except Exception as e:
            print(e)

    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("回放(PlayBack)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('回放(PlayBack)-在线(OnLine)')

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_wnd = MyMainWindow()
    wnd = my_wnd
    my_wnd.show()
    sys.exit(app.exec_())
