# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QLabel,QMessageBox
from PyQt5.QtGui import QPixmap, QImage
import Ui_ImageProcess
import cv2 
import matplotlib.pyplot as plt
import numpy as np 
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ImageProcess.Ui_ImageProcess()
        self.ui.setupUi(self)
        
        # ��ʼ����Ա��������ͼ������
        self.current_image = None  # ����OpenCV��ʽ��ͼ��
        self.current_pixmap = None  # ����QPixmap��ʽ��ͼ��


        # ���Ӱ�ť����¼�
       
        self.ui.Btn_select_pic.clicked.connect(self.On_Btn_select_pic_clicked)
        self.ui.Btn_Mean_Filter.clicked.connect(self.On_Btn_Mean_Filter_clicked)
        self.ui.Btn_Gaussian_Filter.clicked.connect(self.On_Btn_Gaussian_Filter_clicked)
    #��ʾԭͼ��
    def On_Btn_select_pic_clicked(self):
        self.current_image = cv2.imread("fengjing.jpg")
        if self.current_image is None:
            return
        height, width, channel = self.current_image.shape
        bytes_per_line = 3 * width
        q_img = QImage(self.current_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.current_pixmap = QPixmap.fromImage(q_img)
        self.ui.pic_src.setPixmap(self.current_pixmap)
    #��ֵ�˲�������ʾͼ��
    def On_Btn_Mean_Filter_clicked(self):
         if self.current_image is None:
            return
         blurred_image = cv2.blur(self.current_image, (5, 5))

         # ת��ΪQPixmap����ʾ
         height, width, channel = blurred_image.shape
         bytes_per_line = 3 * width
         q_img = QImage(blurred_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
         filtered_pixmap = QPixmap.fromImage(q_img)
         self.ui.pic_dst.setPixmap(filtered_pixmap)
    #��˹�˲�������ʾͼ��
    def On_Btn_Gaussian_Filter_clicked(self):
        if self.current_image is None:
            return
        gaussian_image = cv2.GaussianBlur(self.current_image, (5,5), 0, 0)
        height, width, channel = gaussian_image.shape
        bytes_per_line = 3 * width
        q_img = QImage(gaussian_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        filtered_pixmap = QPixmap.fromImage(q_img)
        self.ui.pic_dst.setPixmap(filtered_pixmap)

         






if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


