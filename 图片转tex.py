"""
从剪切板取出图片资源，OCR识别为对应Latex代码，并放入剪切板中。

@author: Suef、SimpleTex
@date: 2024-08-20
@version: 1.0
"""

import sys
from PIL import Image, ImageGrab
import time
from datetime import datetime
import json
import requests
from random import Random
import hashlib
from pyperclip import copy
import base64
import pytesseract

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDesktopWidget, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class MyWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initial_data()

        font = QFont()
        font.setFamily('微软雅黑')
        font.setBold(True)
        font.setPointSize(15)
        font.setWeight(50)

        desktop = QDesktopWidget().availableGeometry()

        self.setWindowTitle("T")
        self.setFixedSize(270,180)
        self.move(desktop.width() - 350, desktop.height() - 750)

        # 创建标签
        self.label = QLabel("----", self)
        self.label.resize(50,50)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        # 创建按钮
        self.btn = QPushButton("开始识别", self)
        self.btn.resize(50, 50)
        self.btn.setFont(font)
        self.btn.setFlat(True)
        self.btn.clicked.connect(self.on_btn_click_Latex)

        self.combo = QComboBox(self)
        self.combo.resize(50,50)
        self.combo.addItem("Latex模式")
        self.combo.addItem("OCR模式")
        self.combo.addItem("Base64模式")
        self.combo.currentIndexChanged.connect(self.changeButtonAction)


        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.btn)
        layout.addWidget(self.label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def initial_data(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
        self.SIMPLETEX_APP_ID = config["id"]
        self.SIMPLETEX_APP_SECRET = config["pwd"]
        self.base_path = config["path"]
        self.url = config["url"]

    def _random_str(self, randomlength=16):
        str = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlength):
            str += chars[random.randint(0, length)]
        return str

    def _get_req_data(self, req_data, appid, secret):
        header = {}
        header["timestamp"] = str(int(datetime.now().timestamp()))
        header["random-str"] = self._random_str(16)
        header["app-id"] = appid
        pre_sign_string = ""
        sorted_keys = list(req_data.keys()) + list(header)
        sorted_keys.sort()
        for key in sorted_keys:
            if pre_sign_string:
                pre_sign_string += "&"
            if key in header:
                pre_sign_string += key + "=" + str(header[key])
            else:
                pre_sign_string += key + "=" + str(req_data[key])

        pre_sign_string += "&secret=" + secret
        header["sign"] = hashlib.md5(pre_sign_string.encode()).hexdigest()
        return header, req_data

    def on_btn_click_Latex(self):

        im = ImageGrab.grabclipboard()

        if isinstance(im, Image.Image):
            # print(f"Image: size: {im.size}, mode: {im.mode}")
            filename = self.base_path + "\\" + f"{time.time()}.png"
            im.save(filename)
            img_file = {"file": open(filename, 'rb')}
            data = {}  # 请求参数数据（非文件型参数），视情况填入，可以参考各个接口的参数说明
            header, data = self._get_req_data(data, self.SIMPLETEX_APP_ID, self.SIMPLETEX_APP_SECRET)
            res = requests.post(self.url, files=img_file, data=data,
                                headers=header)
            if json.loads(res.text)['status'] is not True:
                self.label.setText("调用失败")
                print("调用失败")
            else:
                copy(json.loads(res.text)['res']["latex"])
                self.label.setText("成功识别")
                print("成功识别")
        else:
            self.label.setText("剪切板没有图片")
            print("剪切板没有图片")

    def on_btn_click_OCR(self):

        im = ImageGrab.grabclipboard()

        if isinstance(im, Image.Image):
            # print(f"Image: size: {im.size}, mode: {im.mode}")
            filename = self.base_path + "\\" + f"{time.time()}.png"
            im.save(filename)
            try:
                ocr_text = pytesseract.image_to_string(im, lang='chi_sim')
                if ocr_text is not None:
                    copy(ocr_text)
                    self.label.setText("成功识别")
                    print("成功识别")
                else:
                    raise Exception()
            except Exception:
                self.label.setText("识别失败")
                print("识别失败")
        else:
            self.label.setText("剪切板没有图片")
            print("剪切板没有图片")

    def on_btn_click_Base64(self):

        im = ImageGrab.grabclipboard()

        if isinstance(im, Image.Image):
            # print(f"Image: size: {im.size}, mode: {im.mode}")
            filename = self.base_path + "\\" + f"{time.time()}.png"
            im.save(filename)
            try:
                with open(filename, 'rb') as f:
                    encode_string = base64.b64encode(f.read()).decode('utf-8')
                if encode_string is not None:
                    copy(encode_string)
                    self.label.setText("成功转化")
                    print("成功转化")
                else:
                    raise Exception()
            except Exception:
                self.label.setText("转化失败")
                print("转化失败")
        else:
            self.label.setText("剪切板没有图片")
            print("剪切板没有图片")

    def changeButtonAction(self):
        current_text = self.combo.currentText()
        if current_text == "Latex模式":
            self.btn.clicked.disconnect()
            self.btn.clicked.connect(self.on_btn_click_Latex)
        elif current_text == "OCR模式":
            self.btn.clicked.disconnect()
            self.btn.clicked.connect(self.on_btn_click_OCR)
        elif current_text == "Base64模式":
            self.btn.clicked.disconnect()
            self.btn.clicked.connect(self.on_btn_click_Base64)


def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()