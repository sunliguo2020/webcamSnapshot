# coding=utf-8
import sys

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt

from FaceRecognitionUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Struct import *

global wnd
callback_face_recognition_num = 0
detect_object_id = 0


class CallBackAlarmInfo:
    def __init__(self):
        self.face_time_str = ""
        self.face_sex_str = ""
        self.face_age_str = ""
        self.face_race_str = ""
        self.face_eye_str = ""
        self.face_mouth_str = ""
        self.face_mask_str = ""
        self.face_bread_str = ""

        self.candidate_name_str = ""
        self.candidate_sex_str = ""
        self.candidate_birth_str = ""
        self.candidate_id_str = ""
        self.candidate_library_no_str = ""
        self.candidate_library_name_str = ""
        self.candidate_similarity_str = ""

    def get_detect_info(self, alarm_info, is_face):
        if is_face:
            self.face_time_str = '{}-{}-{} {}:{}:{}'.format(alarm_info.UTC.dwYear, alarm_info.UTC.dwMonth, alarm_info.UTC.dwDay, alarm_info.UTC.dwHour, alarm_info.UTC.dwMinute, alarm_info.UTC.dwSecond)

            if alarm_info.emSex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.MAN):
                self.face_sex_str = '男(Male)'
            elif alarm_info.emSex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.WOMAN):
                self.face_sex_str = '女(Female)'
            else:
                self.face_sex_str = '未知(Unknown)'

            if alarm_info.nAge == 0xff:
                self.face_age_str = '未知(Unknown)'
            else:
                self.face_age_str = str(alarm_info.nAge)

            if alarm_info.emRace == int(EM_RACE_TYPE.YELLOW):
                self.face_race_str = '黄肤色(YELLOW)'
            elif alarm_info.emRace == int(EM_RACE_TYPE.WHITE):
                self.face_race_str = '白肤色(WHITE)'
            elif alarm_info.emRace == int(EM_RACE_TYPE.BLACK):
                self.face_race_str = '黑肤色(BLACK)'
            else:
                self.face_race_str = '未知(UNKNOWN)'

            if alarm_info.emEye == int(EM_EYE_STATE_TYPE.OPEN):
                self.face_eye_str = '睁眼(OPEN)'
            elif alarm_info.emEye == int(EM_EYE_STATE_TYPE.CLOSE):
                self.face_eye_str = '闭眼(CLOSE)'
            elif alarm_info.emEye == int(EM_EYE_STATE_TYPE.NODISTI):
                self.face_eye_str = '未识别(NODISTI)'
            else:
                self.face_eye_str = '未知(UNKNOWN)'

            if alarm_info.emMouth == int(EM_MOUTH_STATE_TYPE.OPEN):
                self.face_mouth_str = '张嘴(OPEN)'
            elif alarm_info.emMouth == int(EM_EYE_STATE_TYPE.CLOSE):
                self.face_mouth_str = '闭嘴(CLOSE)'
            elif alarm_info.emMouth == int(EM_EYE_STATE_TYPE.NODISTI):
                self.face_mouth_str = '未识别(NODISTI)'
            else:
                self.face_mouth_str = '未知(UNKNOWN)'

            if alarm_info.emMask == int(EM_MASK_STATE_TYPE.NOMASK):
                self.face_mask_str = '没戴口罩(NOMASK)'
            elif alarm_info.emMask == int(EM_MASK_STATE_TYPE.WEAR):
                self.face_mask_str = '戴口罩(WEAR)'
            elif alarm_info.emMask == int(EM_MASK_STATE_TYPE.NODISTI):
                self.face_mask_str = '未识别(NODISTI)'
            else:
                self.face_mask_str = '未知(UNKNOWN)'

            if alarm_info.emBeard == int(EM_BEARD_STATE_TYPE.NOBEARD):
                self.face_bread_str = '没胡子(NOBEARD)'
            elif alarm_info.emBeard == int(EM_BEARD_STATE_TYPE.HAVEBEARD):
                self.face_bread_str = '有胡子(HAVEBEARD)'
            elif alarm_info.emBeard == int(EM_BEARD_STATE_TYPE.NODISTI):
                self.face_bread_str = '未识别(NODISTI)'
            else:
                self.face_bread_str = '未知(UNKNOWN)'

    def get_recognition_info(self, alarm_info, is_face, is_candidate):
        if is_face:
            self.face_time_str = '{}-{}-{} {}:{}:{}'.format(alarm_info.UTC.dwYear, alarm_info.UTC.dwMonth, alarm_info.UTC.dwDay,
                                                  alarm_info.UTC.dwHour, alarm_info.UTC.dwMinute,
                                                  alarm_info.UTC.dwSecond)

            if alarm_info.stuFaceData.emSex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.MAN):
                self.face_sex_str = '男(Male)'
            elif alarm_info.stuFaceData.emSex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.WOMAN):
                self.face_sex_str = '女(Female)'
            else:
                self.face_sex_str = '未知(Unknown)'

            if alarm_info.stuFaceData.nAge == 0xff:
                self.face_age_str = '未知(Unknown)'
            else:
                self.face_age_str = str(alarm_info.stuFaceData.nAge)

            if alarm_info.stuFaceData.emRace == int(EM_RACE_TYPE.YELLOW):
                self.face_race_str = '黄肤色(YELLOW)'
            elif alarm_info.stuFaceData.emRace == int(EM_RACE_TYPE.WHITE):
                self.face_race_str = '白肤色(WHITE)'
            elif alarm_info.stuFaceData.emRace == int(EM_RACE_TYPE.BLACK):
                self.face_race_str = '黑肤色(BLACK)'
            else:
                self.face_race_str = '未知(UNKNOWN)'

            if alarm_info.stuFaceData.emEye == int(EM_EYE_STATE_TYPE.OPEN):
                self.face_eye_str = '睁眼(OPEN)'
            elif alarm_info.stuFaceData.emEye == int(EM_EYE_STATE_TYPE.CLOSE):
                self.face_eye_str = '闭眼(CLOSE)'
            elif alarm_info.stuFaceData.emEye == int(EM_EYE_STATE_TYPE.NODISTI):
                self.face_eye_str = '未识别(NODISTI)'
            else:
                self.face_eye_str = '未知(UNKNOWN)'

            if alarm_info.stuFaceData.emMouth == int(EM_MOUTH_STATE_TYPE.OPEN):
                self.face_mouth_str = '张嘴(OPEN)'
            elif alarm_info.stuFaceData.emMouth == int(EM_EYE_STATE_TYPE.CLOSE):
                self.face_mouth_str = '闭嘴(CLOSE)'
            elif alarm_info.stuFaceData.emMouth == int(EM_EYE_STATE_TYPE.NODISTI):
                self.face_mouth_str = '未识别(NODISTI)'
            else:
                self.face_mouth_str = '未知(UNKNOWN)'

            if alarm_info.stuFaceData.emMask == int(EM_MASK_STATE_TYPE.NOMASK):
                self.face_mask_str = '没戴口罩(NOMASK)'
            elif alarm_info.stuFaceData.emMask == int(EM_MASK_STATE_TYPE.WEAR):
                self.face_mask_str = '戴口罩(WEAR)'
            elif alarm_info.stuFaceData.emMask == int(EM_MASK_STATE_TYPE.NODISTI):
                self.face_mask_str = '未识别(NODISTI)'
            else:
                self.face_mask_str = '未知(UNKNOWN)'

            if alarm_info.stuFaceData.emBeard == int(EM_BEARD_STATE_TYPE.NOBEARD):
                self.face_bread_str = '没胡子(NOBEARD)'
            elif alarm_info.stuFaceData.emBeard == int(EM_BEARD_STATE_TYPE.HAVEBEARD):
                self.face_bread_str = '有胡子(HAVEBEARD)'
            elif alarm_info.stuFaceData.emBeard == int(EM_BEARD_STATE_TYPE.NODISTI):
                self.face_bread_str = '未识别(NODISTI)'
            else:
                self.face_bread_str = '未知(UNKNOWN)'

        if is_candidate:
            candidate_info = CANDIDATE_INFO()
            for index in range(alarm_info.nCandidateNum):
                if candidate_info.bySimilarity < alarm_info.stuCandidates[index].bySimilarity:
                    candidate_info = alarm_info.stuCandidates[index]

            self.candidate_name_str = str(candidate_info.stPersonInfo.szPersonNameEx, 'utf-8')

            if candidate_info.stPersonInfo.bySex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.MAN):
                self.candidate_sex_str = '男(Male)'
            elif candidate_info.stPersonInfo.bySex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.WOMAN):
                self.candidate_sex_str = '女(Female)'
            else:
                self.candidate_sex_str = '未知(Unknown)'

            self.candidate_birth_str = '{}-{}-{}'.format(candidate_info.stPersonInfo.wYear, candidate_info.stPersonInfo.byMonth, candidate_info.stPersonInfo.byDay)
            self.candidate_id_str = str(candidate_info.stPersonInfo.szID, 'utf-8')
            if None != candidate_info.stPersonInfo.pszGroupID:
                self.candidate_library_no_str = str(candidate_info.stPersonInfo.pszGroupID, 'utf-8')
            if None != candidate_info.stPersonInfo.pszGroupName:
                self.candidate_library_name_str = str(candidate_info.stPersonInfo.pszGroupName, 'utf-8')
            self.candidate_similarity_str = str(candidate_info.bySimilarity)
        else:
            self.candidate_similarity_str = '陌生人(Stranger)'

class BackUpdateUIThread(QThread):
    # 通过类成员对象定义信号
    update_date = pyqtSignal(int, object, int, bool, bool, bool)

    # 处理业务逻辑
    def run(self):
        pass

@CB_FUNCTYPE(None, C_LLONG, C_DWORD, c_void_p, POINTER(c_ubyte), C_DWORD, C_LDWORD, c_int, c_void_p)
def AnalyzerDataCallBack(lAnalyzerHandle, dwAlarmType, pAlarmInfo, pBuffer, dwBufSize, dwUser, nSequence, reserved):
    if lAnalyzerHandle == wnd.realloadID:
        global callback_face_recognition_num
        global detect_object_id
        local_path = os.path.abspath('.')
        is_global = False
        is_face = False
        is_candidate = False

        show_info = CallBackAlarmInfo()
        if dwAlarmType == EM_EVENT_IVS_TYPE.FACERECOGNITION:
            callback_face_recognition_num = callback_face_recognition_num + 1
            alarm_info = cast(pAlarmInfo, POINTER(DEV_EVENT_FACERECOGNITION_INFO)).contents
            if alarm_info.bGlobalScenePic:
                if pBuffer != 0 and dwBufSize > 0:
                    if alarm_info.bGlobalScenePic:
                        if alarm_info.stuGlobalScenePicInfo.dwFileLenth > 0:
                            is_global = True
                            Global_buf = pBuffer[alarm_info.stuGlobalScenePicInfo.dwOffSet: alarm_info.stuGlobalScenePicInfo.dwOffSet + alarm_info.stuGlobalScenePicInfo.dwFileLenth]
                            if not os.path.isdir(os.path.join(local_path,'Global_Recogn')):
                                os.mkdir(os.path.join(local_path,'Global_Recogn'))
                            with open('./Global_Recogn/Global_Img'+ str(callback_face_recognition_num) + '.jpg', 'wb+') as global_pic:
                                global_pic.write(bytes(Global_buf))
            if alarm_info.stuObject.stPicInfo.dwFileLenth > 0:
                is_face = True
                Face_buf = pBuffer[alarm_info.stuObject.stPicInfo.dwOffSet:alarm_info.stuObject.stPicInfo.dwOffSet + alarm_info.stuObject.stPicInfo.dwFileLenth]
                if not os.path.isdir(os.path.join(local_path, 'Face_Recogn')):
                    os.mkdir(os.path.join(local_path, 'Face_Recogn'))
                with open('./Face_Recogn/Face_Img'+str(callback_face_recognition_num)+ '.jpg', 'wb+') as face_pic:
                    face_pic.write(bytes(Face_buf))
            if alarm_info.nCandidateNum > 0:
                maxSimilarityPersonInfo = CANDIDATE_INFO()
                for index in range(alarm_info.nCandidateNum):
                    if maxSimilarityPersonInfo.bySimilarity < alarm_info.stuCandidates[index].bySimilarity:
                        maxSimilarityPersonInfo = alarm_info.stuCandidates[index]
                if maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwFileLenth > 0:
                    is_candidate = True
                    Candidate_buf = pBuffer[maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwOffSet:
                                            maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwOffSet +
                                            maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwFileLenth]
                    if not os.path.isdir(os.path.join(local_path, 'Candidate_Recogn')):
                        os.mkdir(os.path.join(local_path, 'Candidate_Recogn'))
                    with open('./Candidate_Recogn/Candidate_Img'+str(callback_face_recognition_num)+ '.jpg', 'wb+') as  candidate_pic:
                        candidate_pic.write(bytes(Candidate_buf))

            show_info.get_recognition_info(alarm_info,is_face,is_candidate)
            wnd.backthread.update_date.emit(dwAlarmType, show_info, callback_face_recognition_num, is_global, is_face, is_candidate)
            return
        if dwAlarmType == EM_EVENT_IVS_TYPE.FACEDETECT:
            alarm_info = cast(pAlarmInfo, POINTER(DEV_EVENT_FACEDETECT_INFO)).contents
            if detect_object_id != alarm_info.stuObject.nRelativeID:
                if alarm_info.stuFileInfo.bFileType == 0:
                    is_global = True
                    detect_object_id = alarm_info.stuObject.nRelativeID
                    Global_Img = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
                    if not os.path.isdir(os.path.join(local_path, 'Global_Detect')):
                        os.mkdir(os.path.join(local_path, 'Global_Detect'))
                    with open('./Global_Detect/Global_Img'+str(detect_object_id) + '.jpg', 'wb+') as global_pic:
                        global_pic.write(Global_Img)
                        wnd.backthread.update_date.emit(dwAlarmType, show_info, detect_object_id, is_global, is_face, is_candidate)
            else:
                if alarm_info.stuFileInfo.bFileType == 2:
                    is_global = True
                    is_face = True
                    Face_Img = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
                    if not os.path.isdir(os.path.join(local_path, 'Face_Detect')):
                        os.mkdir(os.path.join(local_path, 'Face_Detect'))
                    with open('./Face_Detect/Face_Img'+str(detect_object_id) + '.jpg', 'wb+') as face_pic:
                        face_pic.write(Face_Img)
                    show_info.get_detect_info(alarm_info, is_face)
                    wnd.backthread.update_date.emit(dwAlarmType, show_info, detect_object_id, is_global, is_face, is_candidate)
            return

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        # 界面初始化
        self._init_ui()

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.playID = C_LLONG()
        self.realloadID = C_LLONG()
        self.m_AnalyzerDataCallBack = AnalyzerDataCallBack
        self.detect_object_id = 0
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        # 创建线程
        self.backthread = BackUpdateUIThread()
        # 连接信号
        self.backthread.update_date.connect(self.update_UIShow)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        # 开始线程
        self.thread.started.connect(self.backthread.run)
        self.thread.start()

    # 初始化界面
    def _init_ui(self):
        self.Login_pushButton.setText('登录(Login)')
        self.Play_pushButton.setText('监视(Play)')
        self.Play_pushButton.setEnabled(False)

        self.IP_lineEdit.setText('10.34.3.73')
        self.Port_lineEdit.setText('37777')
        self.Name_lineEdit.setText('admin')
        self.Pwd_lineEdit.setText('admin')

        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())

        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Play_pushButton.clicked.connect(self.play_btn_onclick)
        self.ListenEvent_pushButton.clicked.connect(self.listenevent_btn_onclick)

        self.clear_img_ui()

    def login_btn_onclick(self):
        self.Play_pushButton.setText("监视(Play)")
        self.ListenEvent_pushButton.setText("订阅事件(ListenEvent)")

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
                self.setWindowTitle('人脸识别(FaceRecognition)-在线(OnLine)')
                self.Login_pushButton.setText('登出(Logout)')
                self.Play_pushButton.setEnabled(True)
                self.ListenEvent_pushButton.setEnabled(True)
                for i in range(int(device_info.nChanNum)):
                    self.Channel_comboBox.addItem(str(i))
            else:
                QMessageBox.about(self, '提示(prompt)', error_msg)
        else:
            if self.playID:
                self.sdk.StopRealPlayEx(self.playID)
                self.playID = 0
            if self.realloadID:
                self.sdk.StopLoadPic(self.realloadID)
                self.realloadID = 0
            result = self.sdk.Logout(self.loginID)
            if result:
                self.setWindowTitle("人脸识别(FaceRecognition)-离线(OffLine)")
                self.Login_pushButton.setText("登录(Login)")
                self.loginID = 0
                self.Play_pushButton.setEnabled(False)
                self.ListenEvent_pushButton.setEnabled(False)
                self.Play_wnd.repaint()
                self.Channel_comboBox.clear()
                self.clear_img_ui()

    def play_btn_onclick(self):
        if not self.playID:
            channel = self.Channel_comboBox.currentIndex()
            self.playID = self.sdk.RealPlayEx(self.loginID, channel, self.Play_wnd.winId())
            if self.playID != 0:
                self.Play_pushButton.setText("停止(Stop)")
                result = self.sdk.RenderPrivateData(self.playID, True)
                if not result:
                    QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
            result = self.sdk.RenderPrivateData(self.playID, False)
            if not result:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
            result = self.sdk.StopRealPlayEx(self.playID)
            if result:
                self.Play_pushButton.setText("监视(Play)")
                self.playID = 0
                self.Play_wnd.repaint()
            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())

    def listenevent_btn_onclick(self):
        if not self.realloadID:
            channel = self.Channel_comboBox.currentIndex()
            self.realloadID = self.sdk.RealLoadPictureEx(self.loginID, channel, EM_EVENT_IVS_TYPE.ALL, True, self.m_AnalyzerDataCallBack)
            if self.realloadID != 0:
                self.ListenEvent_pushButton.setText("取消订阅(Detach Listen)")

            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
            result = self.sdk.StopLoadPic(self.realloadID)
            if result:
                self.ListenEvent_pushButton.setText("订阅事件(Listen Event)")
                self.realloadID = 0
                self.clear_img_ui()
            else:
                QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())

    def update_UIShow(self, dwAlarmType, show_info,detect_object_id, is_global, is_face, is_candidate):
        if dwAlarmType == EM_EVENT_IVS_TYPE.FACERECOGNITION:
            wnd.show_recognition_info(show_info, detect_object_id, is_global, is_face, is_candidate)
        if dwAlarmType == EM_EVENT_IVS_TYPE.FACEDETECT:
            wnd.show_detect_info(show_info, detect_object_id, is_global, is_face)

    def show_recognition_info(self, show_info, num, is_global, is_face, is_candidate):
        self.clear_img_ui()
        if not self.realloadID:
            return
        if is_global:
            self.GlobalImg_groupBox.setTitle('全景图(Global Picture)--人脸识别(FaceRecognition)')
            image = QPixmap('./Global_Recogn/Global_Img'+str(num)+ '.jpg').scaled(self.GlobalImg_wnd.width(), self.GlobalImg_wnd.height())
            self.GlobalImg_wnd.setPixmap(image)

        if is_face:
            self.FaceImg_groupBox.setTitle('人脸图(Face Picture)--人脸识别(FaceRecognition)')
            image = QPixmap('./Face_Recogn/Face_Img'+str(num)+ '.jpg').scaled(self.FaceImg_wnd.width(), self.FaceImg_wnd.height())
            self.FaceImg_wnd.setPixmap(image)
            self.update_face_ui(show_info)

        if is_candidate:
            self.CandidateImg_groupBox.setTitle('候选图(Candidate Picture)--人脸识别(FaceRecognition)')
            image = QPixmap('./Candidate_Recogn/Candidate_Img'+str(num)+ '.jpg').scaled(self.CandidateImg_wnd.width(), self.CandidateImg_wnd.height())
            self.CandidateImg_wnd.setPixmap(image)
            self.update_candidate_ui(show_info)

        else:
            self.update_candidate_ui(None)

    def show_detect_info(self, show_info, num, is_global, is_face):
        if not self.realloadID:
            return
        if is_global:
            self.GlobalImg_groupBox.setTitle('全景图(Global Picture)--人脸检测(FaceDetect)')
            image = QPixmap('./Global_Detect/Global_Img'+str(num)+ '.jpg').scaled(self.GlobalImg_wnd.width(), self.GlobalImg_wnd.height())
            self.GlobalImg_wnd.setPixmap(image)
        if is_face:
            self.FaceImg_groupBox.setTitle('人脸图(Face Picture)--人脸检测(FaceDetect)')
            image = QPixmap('./Face_Detect/Face_Img'+str(num)+ '.jpg').scaled(self.FaceImg_wnd.width(), self.FaceImg_wnd.height())
            self.FaceImg_wnd.setPixmap(image)
            self.update_face_ui(show_info)

    def clear_img_ui(self):
        self.GlobalImg_groupBox.setTitle('全景图(Global Picture)')
        self.FaceImg_groupBox.setTitle('人脸图(Face Picture)')
        self.CandidateImg_groupBox.setTitle('候选图(Candidate Picture)')
        self.GlobalImg_wnd.clear()
        self.FaceImg_wnd.clear()
        self.CandidateImg_wnd.clear()

        self.face_time_label.setText('')
        self.face_sex_label.setText('')
        self.face_age_label.setText('')
        self.face_race_label.setText('')
        self.face_eye_label.setText('')
        self.face_mouth_label.setText('')
        self.face_mask_label.setText('')
        self.face_beard_label.setText('')

        self.candidate_name_label.setText('')
        self.candidate_sex_label.setText('')
        self.candidate_birth_label.setText('')
        self.candidate_id_label.setText('')
        self.candidate_library_no_label.setText('')
        self.candidate_library_name_label.setText('')
        self.candidate_similarity_label.setText('')

    def update_face_ui(self, show_info):
        self.face_time_label.setText(show_info.face_time_str)
        self.face_sex_label.setText(show_info.face_sex_str)
        self.face_age_label.setText(show_info.face_age_str)
        self.face_race_label.setText(show_info.face_race_str)
        self.face_eye_label.setText(show_info.face_eye_str)
        self.face_mouth_label.setText(show_info.face_mouth_str)
        self.face_mask_label.setText(show_info.face_mask_str)
        self.face_beard_label.setText(show_info.face_bread_str)

    def update_candidate_ui(self, show_info):
        if show_info:
            self.candidate_name_label.setText(show_info.candidate_name_str)
            self.candidate_sex_label.setText(show_info.candidate_sex_str)
            self.candidate_birth_label.setText(show_info.candidate_birth_str)
            self.candidate_id_label.setText(show_info.candidate_id_str)
            self.candidate_library_no_label.setText(show_info.candidate_library_no_str)
            self.candidate_library_name_label.setText(show_info.candidate_library_name_str)
            self.candidate_similarity_label.setText(show_info.candidate_similarity_str)
        else:
            self.candidate_similarity_label.setText("陌生人(Stranger)")

    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("人脸识别(FaceRecognition)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('人脸识别(FaceRecognition)-在线(OnLine)')

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if  self.loginID:
            self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_wnd = MyMainWindow()
    wnd = my_wnd
    my_wnd.show()
    sys.exit(app.exec_())
