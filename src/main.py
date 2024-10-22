import json
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QGridLayout,QVBoxLayout,QHBoxLayout, QWidget, QTableWidget,
                             QTableWidgetItem,QLabel, QLineEdit,QComboBox, QTextEdit,QMessageBox,QTabWidget)
from PyQt5.QtCore import QThread, pyqtSignal,Qt,QCoreApplication, QStandardPaths
from PyQt5.QtGui import QIcon
import serial
import serial.tools.list_ports
from Send_alarm import SendAlarm
from editor_container import EditorContainer
from AC_config import ac_config
from Switch_config import switch_config
from Router_config import router_config
from telnet_class import TelnetClient
from  socket import *
from threading import Thread


tr = QCoreApplication.translate

class serialCom(QThread):
    # 定义一个信号，用于传递接收到的数据
    data_received = pyqtSignal(bytes)

    def __init__(self,comname,baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbit=serial.STOPBITS_ONE):
        super().__init__()
        # 打开串口
        try:
            self.ser = serial.Serial(comname, baudrate=baudrate, bytesize=bytesize, parity=parity,stopbits=stopbit,timeout=1)
            QMessageBox.information(None, "com", "打开串口成功！")
        except:
            QMessageBox.information(None, "com", "打开串口失败！")
            self.ser=None
    def senddata(self,databyte):
        try:
            # 发送数据
            self.ser.write(databyte)
            print("发送：",databyte)
        except:
            QMessageBox.information(None, "com", "发送失败")

    def run(self):
        if self.ser is not None and self.ser.isOpen():
            print("串口已打开")
        else:
            print("串口打开失败！")
            return -1

        try:
            while True:
                if self.ser.in_waiting > 0:
                    try:
                        line = self.ser.read(255)#.decode()  # 添加strip()去除尾随的换行符或空格
                        print("收到:", line)
                        self.data_received.emit(line)
                    except serial.SerialException as e:
                        print(f"串口异常: {e}")
                        # 可以选择在这里重连串口或执行其他错误处理
                        break  # 或者根据需要退出循环
        except serial.SerialException as e:
            print(f"串口异常: {e}")
            self.ser.close()
            print("串口已关闭")
            # 可以选择在这里重新打开串口或退出程序
        except Exception as e:
            print(f"发生未预料的异常: {e}")
            self.ser.close()
            # 根据需要处理其他类型的异常


class tcp_task(QThread):
    # 定义一个信号，用于传递接收到的数据
    data_received = pyqtSignal(bytes)
    connect_status = pyqtSignal(str)

    def __init__(self,ip_str="0.0.0.0",port=19926):
        super().__init__()
        # 打开串口
        self.client_socket = None

        try:
            self.server_socket =socket(AF_INET,SOCK_STREAM)    #连接端口
            self.server_socket.bind((ip_str,port))  #ip可以不写
            self.server_socket.listen(1)
            QMessageBox.information(None, "net", "打开网络成功！")
        except:
            QMessageBox.information(None, "net", "打开网络失败！")
    def senddata(self,msg):
        try:
            # 发送数据
            # data= msg.encode('utf-8')
            self.client_socket.send(msg)
            print("发送：",msg)
        except:
            QMessageBox.information(None, "net", "发送失败")


    def run(self):
        self.client_socket, self.host = self.server_socket.accept()
        self.connect_status.emit(str(self.host))
        try:
            while True:
                # print("---->")
                recv_data = self.client_socket.recv(1024)
                recv_connt = recv_data.decode('utf-8')
                self.data_received.emit(recv_data)
                # print(recv_data,recv_connt)
        except serial.SerialException as e:
            print(f"网络异常: {e}")
            self.client_socket.close()

class MainWindow(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.data_dtu=dict()
        self.initUI()
        self.receiver = None
        self.net_receiver=None
        self.alarm = SendAlarm("net visual config")
        self.alarm.start_alarm("net visual config app start!")
  
    def initUI(self):  
        self.setWindowTitle('网络可视化配置')
        self.setGeometry(300, 100, 800, 600)
        self.setWindowIcon(QIcon('icon.ico'))
        layout = QVBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QHBoxLayout()

        # 创建标签
        label = QLabel('选择串口参数：')
        # 创建下拉列表
        self.comboBox = QComboBox(self)
        self.baudrate_comboBox=QComboBox(self)
        self.databit_comboBox=QComboBox(self)
        self.checkbit_comboBox=QComboBox(self)
        self.stopbit_comboBox=QComboBox(self)
        self.btopen_usbcom = QPushButton('console串口连接', self)
        self.btopen_usbcom.setStyleSheet("QPushButton {"
                                       "  color: white;"
                                       "  background-color: blue;"  # 使用预定义的颜色名称
                                       "}")
        self.btopen_usbcom.clicked.connect(self.open_usbcom)
        layout2.addWidget(label)
        layout2.addWidget(self.comboBox)
        layout2.addWidget(self.baudrate_comboBox)
        layout2.addWidget(self.databit_comboBox)
        layout2.addWidget(self.checkbit_comboBox)
        layout2.addWidget(self.stopbit_comboBox)
        layout2.addWidget(self.btopen_usbcom)

        self.labelnet = QLabel('网络端口：')
        self.net_status= QLabel('网络状态：')
        self.bind_ip_textedit = QLineEdit()
        self.bind_ip_textedit.setFixedWidth(200)
        self.bind_ip_textedit.setText("192.168.1.99")
        self.bind_port_textedit=QLineEdit()
        # self.bind_port_textedit.setFixedWidth(200)
        self.bind_port_textedit.setText("23")

        self.username_textedit = QLineEdit()
        # self.username_textedit.setFixedWidth(200)
        self.username_textedit.setText("huawei")

        self.password_textedit = QLineEdit()
        # self.password_textedit.setFixedWidth(200)
        self.password_textedit.setText("a1234567")
        self.btopen_netlisten = QPushButton('telnet连接', self)
        self.btopen_netlisten.setStyleSheet("QPushButton {"
                                         "  color: white;"
                                         "  background-color: blue;"  # 使用预定义的颜色名称
                                         "}")
        self.btopen_netlisten.clicked.connect(self.open_telnet)
        layout3.addWidget(self.labelnet)
        layout3.addWidget(self.bind_ip_textedit)
        layout3.addWidget(self.bind_port_textedit)
        layout3.addWidget(self.username_textedit)
        layout3.addWidget(self.password_textedit)
        layout3.addWidget(self.net_status)
        layout3.addStretch()
        layout3.addWidget(self.btopen_netlisten)
        # 填充下拉列表
        self.populatePorts()
        layout.addLayout(layout2)
        layout.addLayout(layout3)

        self.label1 = QLabel("-------------------------------------------------------------数据信息-------------------------------------------------------------")
        layout.addWidget(self.label1,alignment=Qt.AlignCenter)

        # 设置布局
        container = QWidget()  
        container.setLayout(layout)  
        self.setCentralWidget(container)


        self.route_config = router_config()
        self.ac_config = ac_config()
        self.switch_config = switch_config()
        self.editors = [(self.switch_config, "交换机"),
                        (self.route_config, "路由器"),
                        (self.ac_config, "AC")
            ]

        self.current_tab = None
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_tabs()


        # layout.addLayout(layout_combobox)
        layout.addWidget(self.tabs, 1)
        self.btn_ok = QPushButton('发送')
        self.btn_ok.clicked.connect(self.on_data_ok)
        # self.btn_cancel = QPushButton('取消')
        # self.btn_cancel.clicked.connect(self.on_data_cancel)

        layout3 = QHBoxLayout()
        layout3.addStretch()
        # layout3.addWidget(self.btn_cancel)
        layout3.addWidget(self.btn_ok)
        layout.addLayout(layout3)

    def on_data_ok(self):
        json_str='hello'
        QMessageBox.information(None, "发送", json_str)
        self.write_data(json_str)

        return

    def open_telnet(self):
        host_ip=self.bind_ip_textedit.text()
        port=self.bind_port_textedit.text()
        username=self.username_textedit.text()
        password=self.password_textedit.text()
        telnet_client = TelnetClient()
        # 如果登录结果返加True，则执行命令，然后退出
        if telnet_client.login_host(host_ip, port, username, password) ==False:
            QMessageBox.information(None, "失败", "telnet连接失败")
        else:
            QMessageBox.information(None, "成功", "telnet连接成功")

    def open_net_listen(self):
        print("net listen run!")
        self.net_receiver = tcp_task()
        self.net_receiver.data_received.connect(self.recv_net)  # 连接信号到槽
        self.net_receiver.connect_status.connect(self.recv_connect)  # 连接信号到槽
        # 启动接收线程
        self.net_receiver.start()
        return;
    def on_data_cancel(self):
        return

    def on_tab_changed(self, index):
        # TabbedKeycodes.close_tray()
        old_tab = self.current_tab
        new_tab = None
        if index >= 0:
            new_tab = self.tabs.widget(index)

        if old_tab is not None:
            old_tab.editor.deactivate()
        if new_tab is not None:
            new_tab.editor.activate()

        self.current_tab = new_tab

    def refresh_tabs(self):
        self.tabs.clear()
        for container, lbl in self.editors:
            if not container.valid():
                continue
            # if lbl!="Kmap Display setting" : #luzi add for temp
            #     continue
            c = EditorContainer(container)
            self.tabs.addTab(c, tr("MainWindow", lbl))

    def populatePorts(self):
        # 使用pyserial的list_ports函数来获取所有串口
        ports = list(serial.tools.list_ports.comports())
        # 清除旧项（如果有的话）
        self.comboBox.clear()
        # 遍历串口列表并添加到下拉列表中
        for port, desc, hwid in ports:
            self.comboBox.addItem(f"{desc} [{port}]")


        self.baudrate_comboBox.addItem("1200")
        self.baudrate_comboBox.addItem("2400")
        self.baudrate_comboBox.addItem("4800")
        self.baudrate_comboBox.addItem("9600")
        self.baudrate_comboBox.addItem("14400")
        self.baudrate_comboBox.addItem("19200")
        self.baudrate_comboBox.addItem("38400")
        self.baudrate_comboBox.addItem("57600")
        self.baudrate_comboBox.addItem("115200")
        self.baudrate_comboBox.setCurrentIndex(3)

        self.databit_comboBox.addItem("6")
        self.databit_comboBox.addItem("7")
        self.databit_comboBox.addItem("8")
        self.databit_comboBox.setCurrentIndex(2)

        self.checkbit_comboBox.addItem("Even")
        self.checkbit_comboBox.addItem("Odd")
        self.checkbit_comboBox.addItem("None")
        self.checkbit_comboBox.setCurrentIndex(2)

        self.stopbit_comboBox.addItem("1")
        self.stopbit_comboBox.addItem("1.5")
        self.stopbit_comboBox.addItem("2")

    def open_usbcom(self):
        id =self.comboBox.currentIndex()
        comname=self.comboBox.currentText().split('[')
        print(self.comboBox.currentText())
        print(comname)
        comname=comname[-1][:-1]
        print(comname)
        self.receiver = serialCom(comname)
        self.receiver.data_received.connect(self.recv_usb)  # 连接信号到槽
        # 启动接收线程
        self.receiver.start()


    def recv_usb(self,databytes):
        print("串口接收到数据：",databytes,"\n len=",len(databytes))
        pass
    def recv_net(self,databytes):
        print("网络接收到数据：",databytes,"\n len=",len(databytes))
        pass

    def recv_connect(self,hoststr):
        print(f"收到连接：{hoststr}")
        self.net_status.setText(f"收到客户端连接！{hoststr}")

    def write_data(self,data_str):
        ret = self.alarm.get_check_valid()
        print(ret)
        if 1:
            try:
                if self.receiver is not None:
                    self.receiver.senddata(data_str.encode())
                    QMessageBox.information(None, "com", "串口发送成功")
                else:
                    QMessageBox.information(None, "com", "串口未打开")

                if self.net_receiver is not None:
                    self.net_receiver.senddata(data_str.encode())
                    QMessageBox.information(None, "net", "网络发送成功")
                else:
                    QMessageBox.information(None, "net", "网络未连接")

                self.alarm.start_alarm(f"write data:{data_str}")
            except:
                print("error!")
        else:
            print("check fail!")
            QMessageBox.information(None, "失败", "未连接互联网或者使用已过期")
  
if __name__ == '__main__':  
    app = QApplication(sys.argv)  
    ex = MainWindow()  
    ex.show()  
    sys.exit(app.exec_())
