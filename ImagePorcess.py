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
    """自定义命令类，用于保存图像状态"""
    def __init__(self, old_image, new_image, parent, description=""):
        super().__init__(description)
        self.old_image = old_image.copy() if old_image is not None else None
        self.new_image = new_image.copy() if new_image is not None else None
        self.parent = parent  # 主窗口引用
        
    def undo(self):
        """撤销操作：恢复旧图像"""
        if self.old_image is not None:
            self.parent.current_image = self.old_image.copy()
            self.parent.Show_Pic(self.old_image)
            
    def redo(self):
        """重做操作：应用新图像"""
        if self.new_image is not None:
            self.parent.current_image = self.new_image.copy()
            self.parent.Show_Pic(self.new_image)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ImageProcess.Ui_ImageProcess()
        self.ui.setupUi(self)
        self.setMouseTracking(True)  # 启用全局鼠标跟踪
        self.ui.pic_src.setMouseTracking(True) 
        self.mouse_in_label = False
        self.slider_bright = self.ui.Slider_bright
        self.Slider_contrast = self.ui.Slider_contrast
        # 初始化成员变量保存图像数据
        self.current_image = None  # 保存OpenCV格式的图像
        self.current_pixmap = None  # 保存QPixmap格式的图像
        self.current_comboBox_index = 0 #默认是0，依次是opencv、torch、cuda、openmp
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(20) 
        self.value_bright = 0
        self.value_contrast = 0
        self.mousewheel = 0  # 滚轮累计值（正数放大，负数缩小）
        self.scale_factor = 1.0  # 当前缩放比例
        self.min_scale = 0.1  # 最小缩放比例
        self.max_scale = 10.0  # 最大缩放比例
        self.change_size_enable = False

    def enterEvent(self, event):
        # 鼠标进入控件时设置标志位为True
        self.mouse_in_label = True

    def leaveEvent(self, event):
        # 鼠标离开控件时设置标志位为False
        self.mouse_in_label = False
        # 可以在这里添加清理操作，比如清除显示的RGB值

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.mouse_in_label:
            return
        
        label_pos = self.ui.pic_src.mapFromParent(event.pos())
        if not self.ui.pic_src.rect().contains(label_pos):
            return
        
        pixmap = self.ui.pic_src.pixmap()
        if pixmap is None:
            return
        
        # 处理缩放（如果图像被缩放显示）
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
        """根据当前缩放比例更新图像显示"""
        if self.current_pixmap is None:
            return
        
        # 计算新尺寸
        new_width = int(self.current_pixmap.width() * self.scale_factor)
        new_height = int(self.current_pixmap.height() * self.scale_factor)
        
        # 缩放图像（保持平滑）
        scaled_pixmap = self.current_pixmap.scaled(
            new_width, 
            new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        # 更新显示
        self.ui.pic_src.setPixmap(scaled_pixmap)

    def wheelEvent(self, event):
        if self.change_size_enable == True:
            angle=event.angleDelta() / 8                                           # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
            angleX=angle.x()                                                       # 水平滚过的距离(此处用不上)
            angleY=angle.y()                                                       # 竖直滚过的距离
            if angleY > 0:                                                         # 滚轮上滚
                print("鼠标中键上滚")  # 响应测试语句
                delta = event.angleDelta().y()
                self.mousewheel += delta
                self.mousewheel = max(-2000, min(2000, self.mousewheel))  # 防止溢出
        
                # 计算缩放比例（每120单位增减10%）
                scale_step = 0.1 if delta > 0 else -0.1
                new_scale = self.scale_factor + scale_step
                
                # 限制缩放范围
                self.scale_factor = max(self.min_scale, min(self.max_scale, new_scale))
                
                # 应用缩放
                self.apply_image_zoom(event.pos())  # 传入鼠标位置实现中心缩放
                
                # 阻止事件继续传播
                event.accept()
            else:                                                                  # 滚轮下滚
                print("鼠标中键下滚")  # 响应测试语句
                delta = event.angleDelta().y()
                print(delta)
                self.mousewheel += delta
                self.mousewheel = max(-2000, min(2000, self.mousewheel))  # 防止溢出
        
                # 计算缩放比例（每120单位增减10%）
                scale_step = 0.1 if delta > 0 else -0.1
                new_scale = self.scale_factor + scale_step
                
                # 限制缩放范围
                self.scale_factor = max(self.min_scale, min(self.max_scale, new_scale))
                
                # 应用缩放
                self.apply_image_zoom(event.pos())  # 传入鼠标位置实现中心缩放
                
                # 阻止事件继续传播
                event.accept()

    #显示图像
    def Show_Pic(self,image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.current_pixmap = QPixmap.fromImage(q_img)
        #self.ui.pic_src.setPixmap(self.current_pixmap)
          # 获取QLabel的当前可用尺寸
        label_size = self.ui.pic_src.size()
        
        # 保持宽高比缩放
        scaled_pixmap = self.current_pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.ui.pic_src.setPixmap(scaled_pixmap)
        self.ui.pic_src.setAlignment(Qt.AlignCenter) 


    #显示原图像
    def On_Btn_select_pic_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(None,"选择图片","","图片文件 (*.jpg *.png *.bmp)")  # 2. 如果用户没有选择文件（点击了取消），直接返回
        if not file_path:
            return
        new_image = cv2.imread(file_path)  # 使用 OpenCV 读取图片
        if new_image is None:
            print("图片读取失败！")
            return
    
        # new_image  = cv2.imread("fengjing.jpg")
        # if new_image  is None:
        #     return
        cmd = ImageCommand(self.current_image, new_image, self, "加载图片")
        self.undo_stack.push(cmd)
       
        self.Show_Pic(new_image)
       
    def On_Btn_invertcolor_clicked(self):
        if self.current_image is None:
            return
        if self.current_comboBox_index == 0:
            invertcolor_image = cv2.bitwise_not(self.current_image)
            cmd = ImageCommand(self.current_image, invertcolor_image, self, "反色")
            self.undo_stack.push(cmd)
         
            self.Show_Pic(invertcolor_image)
        

    #均值滤波，并显示图像
    def On_Btn_Mean_Filter_clicked(self):
         if self.current_image is None:
            return
         if self.current_comboBox_index == 0:
            blurred_image = cv2.blur(self.current_image, (5, 5))
            cmd = ImageCommand(self.current_image, blurred_image, self, "均值滤波")
            self.undo_stack.push(cmd)
         
            self.Show_Pic(blurred_image)

         #if self.current_comboBox_index == 2:
      


    #高斯滤波，并显示图像
    def On_Btn_Gaussian_Filter_clicked(self):
        if self.current_image is None:
            return
        if self.current_comboBox_index == 0:
            gaussian_image = cv2.GaussianBlur(self.current_image, (3,3), 0, 0)
            cmd = ImageCommand(self.current_image, gaussian_image, self, "高斯滤波")
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
        # 方法1：直接加减（可能溢出）
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
        print("亮度：",self.value_bright)
        self.adjust_brightness_cv()

    def On_Slider_contrast_changed(self):
        a = self.Slider_contrast.value()/10
        self.value_contrast = a 
        print("亮度：",self.value_contrast)
        self.adjust_contrast_cv()

    def On_Btn_change_size_clicked(self):
        self.change_size_enable = not self.change_size_enable
        print("现在的状态是：",self.change_size_enable)


    def On_Btn_rotate_clicked(self):
        self.current_image = cv2.flip(cv2.transpose(self.current_image), 1)
        self.Show_Pic(self.current_image)


        
    #下拉框选择处理方式，依次是opencv、torch、cuda、openmp
    def On_comboBox_method_changed(self,index):
        current_text = self.ui.comboBox_method.currentText()
        self.current_comboBox_index = index
       
         






if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


