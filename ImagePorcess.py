#coding=gbk
import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QLabel,QMessageBox,QFileDialog,QUndoStack, QUndoCommand  
from PyQt5.QtGui import QPixmap, QImage,QMouseEvent,QTransform
import Ui_ImageProcess
import cv2 
import matplotlib.pyplot as plt
import numpy as np 
from PyQt5.QtCore import Qt


class ImageCommand(QUndoCommand):
    """�Զ��������࣬���ڱ���ͼ��״̬"""
    def __init__(self, old_image, new_image, parent, description=""):
        super().__init__(description)
        self.old_image = old_image.copy() if old_image is not None else None
        self.new_image = new_image.copy() if new_image is not None else None
        self.parent = parent  # ����������
        
    def undo(self):
        """�����������ָ���ͼ��"""
        if self.old_image is not None:
            self.parent.current_image = self.old_image.copy()
            self.parent.Show_Pic(self.old_image)
            
    def redo(self):
        """����������Ӧ����ͼ��"""
        if self.new_image is not None:
            self.parent.current_image = self.new_image.copy()
            self.parent.Show_Pic(self.new_image)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ImageProcess.Ui_ImageProcess()
        self.ui.setupUi(self)
        self.setMouseTracking(True)  # ����ȫ��������
        self.ui.pic_src.setMouseTracking(True) 
        self.mouse_in_label = False
        self.slider_bright = self.ui.Slider_bright
        self.Slider_contrast = self.ui.Slider_contrast
        # ��ʼ����Ա��������ͼ������
        self.current_image = None  # ����OpenCV��ʽ��ͼ��
        self.current_pixmap = None  # ����QPixmap��ʽ��ͼ��
        self.current_comboBox_index = 0 #Ĭ����0��������opencv��torch��cuda��openmp
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(20) 
        self.value_bright = 0
        self.value_contrast = 0
        self.mousewheel = 0  # �����ۼ�ֵ�������Ŵ󣬸�����С��
        self.scale_factor = 1.0  # ��ǰ���ű���
        self.min_scale = 0.1  # ��С���ű���
        self.max_scale = 10.0  # ������ű���
        self.change_size_enable = False

    def enterEvent(self, event):
        # ������ؼ�ʱ���ñ�־λΪTrue
        self.mouse_in_label = True

    def leaveEvent(self, event):
        # ����뿪�ؼ�ʱ���ñ�־λΪFalse
        self.mouse_in_label = False
        # �������������������������������ʾ��RGBֵ

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.mouse_in_label:
            return
        
        label_pos = self.ui.pic_src.mapFromParent(event.pos())
        if not self.ui.pic_src.rect().contains(label_pos):
            return
        
        pixmap = self.ui.pic_src.pixmap()
        if pixmap is None:
            return
        
        # �������ţ����ͼ��������ʾ��
        scale_x = pixmap.width() / self.ui.pic_src.width()
        scale_y = pixmap.height() / self.ui.pic_src.height()
        img_x = int(label_pos.x() * scale_x)
        img_y = int(label_pos.y() * scale_y)
        
        img = pixmap.toImage()
        if img_x >= img.width() or img_y >= img.height():
            return
        
        pixel = img.pixel(img_x, img_y)
        rgb = (pixel & 0xff0000) >> 16, (pixel & 0xff00) >> 8, (pixel & 0xff)

    
        self.ui.lineEdit_xy.setText(f"{img_x},{img_y}")
        self.ui.lineEdit_rgb.setText(f"{rgb[0]},{rgb[1]},{rgb[2]}")

    def apply_image_zoom(self, mouse_pos=None):
        """���ݵ�ǰ���ű�������ͼ����ʾ"""
        if self.current_pixmap is None:
            return
        
        # �����³ߴ�
        new_width = int(self.current_pixmap.width() * self.scale_factor)
        new_height = int(self.current_pixmap.height() * self.scale_factor)
        
        # ����ͼ�񣨱���ƽ����
        scaled_pixmap = self.current_pixmap.scaled(
            new_width, 
            new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        # ������ʾ
        self.ui.pic_src.setPixmap(scaled_pixmap)

    def wheelEvent(self, event):
        if self.change_size_enable == True:
            angle=event.angleDelta() / 8                                           # ����QPoint����Ϊ����ת������ֵ����λΪ1/8��
            angleX=angle.x()                                                       # ˮƽ�����ľ���(�˴��ò���)
            angleY=angle.y()                                                       # ��ֱ�����ľ���
            if angleY > 0:                                                         # �����Ϲ�
                print("����м��Ϲ�")  # ��Ӧ�������
                delta = event.angleDelta().y()
                self.mousewheel += delta
                self.mousewheel = max(-2000, min(2000, self.mousewheel))  # ��ֹ���
        
                # �������ű�����ÿ120��λ����10%��
                scale_step = 0.1 if delta > 0 else -0.1
                new_scale = self.scale_factor + scale_step
                
                # �������ŷ�Χ
                self.scale_factor = max(self.min_scale, min(self.max_scale, new_scale))
                
                # Ӧ������
                self.apply_image_zoom(event.pos())  # �������λ��ʵ����������
                
                # ��ֹ�¼���������
                event.accept()
            else:                                                                  # �����¹�
                print("����м��¹�")  # ��Ӧ�������
                delta = event.angleDelta().y()
                print(delta)
                self.mousewheel += delta
                self.mousewheel = max(-2000, min(2000, self.mousewheel))  # ��ֹ���
        
                # �������ű�����ÿ120��λ����10%��
                scale_step = 0.1 if delta > 0 else -0.1
                new_scale = self.scale_factor + scale_step
                
                # �������ŷ�Χ
                self.scale_factor = max(self.min_scale, min(self.max_scale, new_scale))
                
                # Ӧ������
                self.apply_image_zoom(event.pos())  # �������λ��ʵ����������
                
                # ��ֹ�¼���������
                event.accept()

    #��ʾͼ��
    def Show_Pic(self,image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.current_pixmap = QPixmap.fromImage(q_img)
        #self.ui.pic_src.setPixmap(self.current_pixmap)
          # ��ȡQLabel�ĵ�ǰ���óߴ�
        label_size = self.ui.pic_src.size()
        
        # ���ֿ�߱�����
        scaled_pixmap = self.current_pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.ui.pic_src.setPixmap(scaled_pixmap)
        self.ui.pic_src.setAlignment(Qt.AlignCenter) 


    #��ʾԭͼ��
    def On_Btn_select_pic_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(None,"ѡ��ͼƬ","","ͼƬ�ļ� (*.jpg *.png *.bmp)")  # 2. ����û�û��ѡ���ļ��������ȡ������ֱ�ӷ���
        if not file_path:
            return
        new_image = cv2.imread(file_path)  # ʹ�� OpenCV ��ȡͼƬ
        if new_image is None:
            print("ͼƬ��ȡʧ�ܣ�")
            return
    
        # new_image  = cv2.imread("fengjing.jpg")
        # if new_image  is None:
        #     return
        cmd = ImageCommand(self.current_image, new_image, self, "����ͼƬ")
        self.undo_stack.push(cmd)
       
        self.Show_Pic(new_image)
       
    def On_Btn_invertcolor_clicked(self):
        if self.current_image is None:
            return
        if self.current_comboBox_index == 0:
            invertcolor_image = cv2.bitwise_not(self.current_image)
            cmd = ImageCommand(self.current_image, invertcolor_image, self, "��ɫ")
            self.undo_stack.push(cmd)
         
            self.Show_Pic(invertcolor_image)
        

    #��ֵ�˲�������ʾͼ��
    def On_Btn_Mean_Filter_clicked(self):
         if self.current_image is None:
            return
         if self.current_comboBox_index == 0:
            blurred_image = cv2.blur(self.current_image, (5, 5))
            cmd = ImageCommand(self.current_image, blurred_image, self, "��ֵ�˲�")
            self.undo_stack.push(cmd)
         
            self.Show_Pic(blurred_image)

         #if self.current_comboBox_index == 2:
      


    #��˹�˲�������ʾͼ��
    def On_Btn_Gaussian_Filter_clicked(self):
        if self.current_image is None:
            return
        if self.current_comboBox_index == 0:
            gaussian_image = cv2.GaussianBlur(self.current_image, (3,3), 0, 0)
            cmd = ImageCommand(self.current_image, gaussian_image, self, "��˹�˲�")
            self.undo_stack.push(cmd)
            self.Show_Pic(gaussian_image)
            
    def On_Btn_undo_clicked(self):
        self.undo_stack.undo()

    def On_Btn_redo_clicked(self):
        self.undo_stack.redo()

    def adjust_brightness_cv(self):
        if self.current_image is None:
            return
        brightness = int(self.value_bright)
        # ����1��ֱ�ӼӼ������������
        bright_image = cv2.add(self.current_image, brightness)
        self.Show_Pic(bright_image)

    def adjust_contrast_cv(self):
        if self.current_image is None:
            return
        contrast = self.value_contrast
        contrasted_image = cv2.convertScaleAbs(self.current_image, alpha=contrast, beta=0)
        self.Show_Pic(contrasted_image)

    def On_Slider_bright_changed(self):
        a = self.slider_bright.value()
        self.value_bright = a 
        print("���ȣ�",self.value_bright)
        self.adjust_brightness_cv()

    def On_Slider_contrast_changed(self):
        a = self.Slider_contrast.value()/10
        self.value_contrast = a 
        print("���ȣ�",self.value_contrast)
        self.adjust_contrast_cv()

    def On_Btn_change_size_clicked(self):
        self.change_size_enable = not self.change_size_enable
        print("���ڵ�״̬�ǣ�",self.change_size_enable)


    def On_Btn_rotate_clicked(self):
        self.current_image = cv2.flip(cv2.transpose(self.current_image), 1)
        self.Show_Pic(self.current_image)


        
    #������ѡ����ʽ��������opencv��torch��cuda��openmp
    def On_comboBox_method_changed(self,index):
        current_text = self.ui.comboBox_method.currentText()
        self.current_comboBox_index = index
       
         






if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


