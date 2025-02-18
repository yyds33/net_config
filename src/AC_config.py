# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ac_config.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
# -*- coding: utf-8 -*-
import os
import struct
import time

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject, QSize,Qt,QCoreApplication
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QGridLayout, QLabel, QSlider, \
    QComboBox, QColorDialog, QCheckBox, QLineEdit, QButtonGroup, QRadioButton, QFileDialog, QMessageBox
from PyQt5.QtGui import QColor,QImage,QPixmap
from basic_editor import BasicEditor
from Send_alarm import SendAlarm
from PIL import Image
import cv2
tr = QCoreApplication.translate


class BasicHandler(QObject):
    update = pyqtSignal()

    def __init__(self, container):
        super().__init__()
        self.device = self.keyboard = None
        self.widgets = []

    def set_device(self, device):
        self.device = device
        if self.valid():
            # self.keyboard = self.device.keyboard
            self.show()
        else:
            self.hide()

    def show(self):
        for w in self.widgets:
            w.show()

    def hide(self):
        for w in self.widgets:
            w.hide()

    def block_signals(self):
        for w in self.widgets:
            w.blockSignals(True)

    def unblock_signals(self):
        for w in self.widgets:
            w.blockSignals(False)

    # def update_from_keyboard(self):
    #     raise NotImplementedError
    #
    # def valid(self):
    #     raise NotImplementedError

class NetConfigSetHandler(BasicHandler):

    def __init__(self, container):
        super().__init__(container)

    def valid(self):
        return 1
        # return isinstance(self.device, VialKeyboard) #and self.device.keyboard.lighting_qmk_rgblight

    def send_cmd(self,strmsg):
        byte_array = strmsg.encode()
        print(type(byte_array),len(byte_array))  # <class 'bytes'>
        print(byte_array)  #
        #hex_data = byte_array.hex()
        return self.device.keyboard.set_custom_setting(byte_array)


    def send_cmd_str(self,strmsg):
        byte_array = strmsg.encode()
        print(type(byte_array),len(byte_array))  # <class 'bytes'>
        print(byte_array)  #
        try:
            return self.device.keyboard.set_custom_setting(byte_array)
        except:
            return None
    def send_cmd_hex(self,byte_array):
        #bytes_array是bytes,入参要转换为bytes传入进来
        ret =self.device.keyboard.set_custom_setting(byte_array)
        return ret

    def recv_cmd_hex(self):
        ret = self.device.keyboard.recv_custom_setting()
        return ret

class ac_config(BasicEditor):
    def __init__(self):
        super().__init__()
        self.data = dict()
        self.mode = 1

        w = QWidget()
        w.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.container = QVBoxLayout()

        w.setLayout(self.container)
        self.addWidget(w)
        self.setupUi(w,self.container)

        self.handlers = [NetConfigSetHandler(self.container)]

    def setupUi(self,Form,contain):

        self.label = QLabel("模式")
        self.radioButton = QRadioButton("单选模式1")
        self.radioButton_2 = QRadioButton("单选模式2")
        self.radioModeGrp = QButtonGroup()
        self.radioModeGrp.addButton(self.radioButton, 1)
        self.radioModeGrp.addButton(self.radioButton_2, 0)
        self.radioModeGrp.buttonClicked.connect(self.on_radiobtn_Mode_clicked)
        self.radioButton.setChecked(1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.addWidget(self.label)
        self.horizontalLayout.addWidget(self.radioButton)
        self.horizontalLayout.addWidget(self.radioButton_2)
        contain.addLayout(self.horizontalLayout)

    def on_radiobtn_Mode_clicked(self,button):
        id = self.radioModeGrp.id(button)
        self.mode=id;
        print(f"id={id}")

 # layout 移除所有控件
    def remove_all_controls(self,layout):
        while layout.count():
            child = layout.takeAt(0)
            if child is not None:
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clear_layout(child.layout())

    def clear_layout(self,layout):
        while layout is not None and layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())


    def valid(self):
        # return isinstance(self.device, VialKeyboard)
        return 1

    def rebuild(self, device):
        super().rebuild(device)

        for h in self.handlers:
            h.set_device(device)

        if not self.valid():
            return