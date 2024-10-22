import http.client
import sys
import threading
import urllib
from http.client import HTTPConnection
from http.client import HTTPResponse
import time
import re
import json
import socket
import urllib.parse

from PyQt5.QtCore import pyqtSignal, QObject
#from tqdm import tqdm
import requests

class SendAlarm(QObject):
    # 定义一个信号来更新进度
    progress_signal = pyqtSignal(int)
    def __init__(self,initstr='qmk vial start',hostip= '39.107.228.114',url='/teset/bmc'):
        super().__init__()
        self.hostip='39.107.228.114'
        self.url='/teset/bmc'
        #根据不同操作系统修改名字
        if sys.platform.startswith("MacOS"):
            self.setup_pack_url = "/download/YueHPeri_setup.mac"
        elif sys.platform.startswith("win"):
            self.setup_pack_url = "/download/YueHPeri_setup.exe"
        elif sys.platform.startswith("Linux"):
            self.setup_pack_url = "/download/YueHPeri_setup.linux"

        self.headers2 = {"User-Agent":"my python program",\
                         "Content-type": "application/json", "Accept": "*/*"}
        self.body_param={'subject':"",\
            'content':"",\
            "id":"bmc"}
        self.body_param['subject']=initstr


    def start_alarm(self,sendstr):
        try:
            # return
            #获取主机名
            hostname = socket.gethostname()
            # 获取IP地址
            ip_address = socket.gethostbyname(hostname)
            msgdata="{}-{}#{}".format(hostname,ip_address,sendstr)
            self.body_param['content']= msgdata;
            
            conn = HTTPConnection(self.hostip,80,timeout=10)
            body_str=json.dumps(self.body_param)
            print(body_str)
        
            #发送请求，URL地址不带HOST信息
            conn.request('POST',self.url,body_str.encode('utf-8'),self.headers2)
            #获取该请求的响应
            resp = conn.getresponse().read().decode()
            print("resp:"+resp)
             
            #关闭连接
            conn.close()
            return 0
        except Exception as e:
            print(e)
            return -1

    def get_new_version(self):
        str=""
        return str

    def get_para(self):
        try:
            conn = HTTPConnection(self.hostip, 80, timeout=10)
            #conn = HTTPConnection("127.0.0.1", 8090, timeout=10)
            body_str = json.dumps(self.body_param)
            print(body_str)

            # 发送请求，URL地址不带HOST信息
            conn.request('GET', self.url, body_str.encode('utf-8'), self.headers2)
            # 获取该请求的响应
            resp = conn.getresponse().read().decode()
            print("resp:" + resp)
            return resp
        except:
            print("cant get para from server!")
            return None

    def get_check_valid(self):
        try:
            resp_para = self.get_para()
            if resp_para is not None and len(resp_para) > 0:
                para_data = json.loads(resp_para)
                print(type(para_data), para_data)
                # 将字符串转换为datetime对象
                from datetime import datetime
                date_end = datetime.strptime(para_data['enddate'], "%Y-%m-%d %H:%M:%S.%f")
                # 获取当前时间
                date_now = datetime.now()
                print(f"now={date_now},end={date_end}")

                if para_data['allow_use'] == '1':
                    print("allow_use =1,ok")
                    return True

                # 比较日期
                elif date_now < date_end:
                    print(f"{date_end} is later than {date_now}")
                    print("ok")
                    return True
                else:
                    print("expire date!")
                    # QMessageBox.information(None, "失败", "使用已过期")
                    return False


            else:
                # QMessageBox.information(None, "失败", "请连接互联网")
                return False
        except:
            return False

    def download_file(self,url, save_path):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        #progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)
        write_data=0;
        with open(save_path, 'wb') as f:
            for data in response.iter_content(1024):
                if data:
                    f.write(data)
                    write_data= write_data+len(data)
                    percentage = write_data/total_size*100
                    #progress_bar.update(len(data))

                    #percentage = (progress_bar.n / progress_bar.total) * 100
                    print(f"当前进度: {percentage:.2f}%")
                    self.progress_signal.emit(int(percentage))
        self.progress_signal.emit(999)
        #progress_bar.close()

    def download_file_bak(self,url="http://39.107.228.114:8090/download/YueHPeri_setup.exe",
                       save_path="C:\\ProgramData\\YueHPeri\\new_setup.exe"):
        # 解析URL
        parsed_url = urllib.parse.urlsplit(url)
        host = parsed_url.netloc
        path = parsed_url.path
        if parsed_url.query:
            # 如果URL包含查询参数，添加到路径中
            path += '?' + parsed_url.query

            # 判断是否使用HTTPS
        if parsed_url.scheme == 'https':
            conn = http.client.HTTPSConnection(host)
        else:
            conn = http.client.HTTPConnection(host)

        try:
            # 发送GET请求
            conn.request("GET", path)

            # 获取响应
            resp = conn.getresponse()

            # 检查响应状态码
            if resp.status == 200:
                # 创建一个文件来保存内容
                with open(save_path, 'wb') as f:
                    # 读取并写入响应内容到文件
                    f.write(resp.read())
                print(f"File downloaded successfully to {save_path}")
            else:
                print(f"Failed to download file, status code: {resp.status}")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # 关闭连接
            conn.close()

    def down_load_thread(self,url,save_path):
        # 创建一个线程来执行下载任务
        download_thread_obj = threading.Thread(target=self.download_file, args=(url, save_path))

        # 设置守护线程（可选，如果主线程结束，守护线程也会结束）
        # download_thread_obj.setDaemon(True)

        # 启动线程
        download_thread_obj.start()

if __name__=="__main__":
    s=SendAlarm()
    s.start_alarm("qmk start")

    #start_program()


    
