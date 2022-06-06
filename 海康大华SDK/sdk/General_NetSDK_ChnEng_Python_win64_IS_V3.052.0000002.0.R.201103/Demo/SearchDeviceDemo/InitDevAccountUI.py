# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'InitDevAccountUI.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_InitDevAccount(object):
    def setupUi(self, InitDevAccount):
        InitDevAccount.setObjectName("InitDevAccount")
        InitDevAccount.resize(407, 275)
        self.username_lineEdit = QtWidgets.QLineEdit(InitDevAccount)
        self.username_lineEdit.setGeometry(QtCore.QRect(260, 40, 113, 20))
        self.username_lineEdit.setObjectName("username_lineEdit")
        self.username_label = QtWidgets.QLabel(InitDevAccount)
        self.username_label.setGeometry(QtCore.QRect(150, 40, 101, 20))
        self.username_label.setObjectName("username_label")
        self.confirm_password_label = QtWidgets.QLabel(InitDevAccount)
        self.confirm_password_label.setGeometry(QtCore.QRect(90, 130, 161, 20))
        self.confirm_password_label.setObjectName("confirm_password_label")
        self.way_lineEdit = QtWidgets.QLineEdit(InitDevAccount)
        self.way_lineEdit.setEnabled(False)
        self.way_lineEdit.setGeometry(QtCore.QRect(160, 170, 91, 20))
        self.way_lineEdit.setObjectName("way_lineEdit")
        self.confirm_password_lineEdit = QtWidgets.QLineEdit(InitDevAccount)
        self.confirm_password_lineEdit.setGeometry(QtCore.QRect(260, 130, 113, 20))
        self.confirm_password_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_password_lineEdit.setObjectName("confirm_password_lineEdit")
        self.reset_way_lineEdit = QtWidgets.QLineEdit(InitDevAccount)
        self.reset_way_lineEdit.setGeometry(QtCore.QRect(260, 170, 113, 20))
        self.reset_way_lineEdit.setObjectName("reset_way_lineEdit")
        self.reser_way_label = QtWidgets.QLabel(InitDevAccount)
        self.reser_way_label.setGeometry(QtCore.QRect(40, 170, 121, 20))
        self.reser_way_label.setObjectName("reser_way_label")
        self.password_lineEdit = QtWidgets.QLineEdit(InitDevAccount)
        self.password_lineEdit.setGeometry(QtCore.QRect(260, 80, 113, 20))
        self.password_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_lineEdit.setObjectName("password_lineEdit")
        self.password_label = QtWidgets.QLabel(InitDevAccount)
        self.password_label.setGeometry(QtCore.QRect(160, 80, 91, 20))
        self.password_label.setObjectName("password_label")
        self.pushButton = QtWidgets.QPushButton(InitDevAccount)
        self.pushButton.setGeometry(QtCore.QRect(150, 210, 121, 31))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(InitDevAccount)
        self.pushButton.clicked.connect(InitDevAccount.accept)
        QtCore.QMetaObject.connectSlotsByName(InitDevAccount)

    def retranslateUi(self, InitDevAccount):
        _translate = QtCore.QCoreApplication.translate
        InitDevAccount.setWindowTitle(_translate("InitDevAccount", "初始化(Initialization)"))
        self.username_label.setText(_translate("InitDevAccount", "用户名(Username)"))
        self.confirm_password_label.setText(_translate("InitDevAccount", "确认密码(Confirm Password)"))
        self.reser_way_label.setText(_translate("InitDevAccount", "重置方式(Reset Way)"))
        self.password_label.setText(_translate("InitDevAccount", "密码(Password)"))
        self.pushButton.setText(_translate("InitDevAccount", "确定(OK)"))

