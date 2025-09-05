
import sys
from PyQt5.QtWidgets import QWidget,QApplication,QUndoCommand,QUndoStack
from PyQt5.QtGui import QPixmap, QImage,QMouseEvent,QTransform
from PyQt5.QtCore import Qt,pyqtSignal, QObject
from PyQt5 import QtCore
import Designer.Ui_Static_Process as Ui_Static_Process
import cv2 
import matplotlib.pyplot as plt
import numpy as np 
import vtk

from PyQt5.QtWidgets import QLabel, QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# pylint: disable=invalid-name,missing-class-docstring,too-few-public-methods
#撤销 还原功能
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

#鼠标实时显示坐标 RGB
class MouseTracker(QtCore.QObject):
    positionChanged = QtCore.pyqtSignal(QtCore.QPoint)
 
    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)
 
    @property
    def widget(self):
        return self._widget
 
    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QtCore.QEvent.MouseMove:
            self.positionChanged.emit(e.pos())
        return super().eventFilter(o, e)

class Static_Process_Widget(QWidget):
   
    def __init__(self):
        super().__init__() 
        self.ui = Ui_Static_Process.Ui_Static_Process()
        self.ui.setupUi(self)

        self.current_pixmap = None
        self.current_image = None
        self.pic_label =self.ui.pic_label

        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(20) 
        self.mousewheel = 0  # 滚轮累计值（正数放大，负数缩小）
        self.scale_factor = 1.0  # 当前缩放比例
        self.min_scale = 0.1  # 最小缩放比例
        self.max_scale = 10.0  # 最大缩放比例
        self.change_size_enable = False #是否进行缩放
        self.pic_label.setMouseTracking(True) 
        self.slider_bright = self.ui.Slider_bright
        self.slider_contrast = self.ui.Slider_contrast
        self.img_x = 0 #鼠标在控件的实时坐标
        self.img_y = 0
        self.rgb = []

        tracker = MouseTracker(self.pic_label)
        tracker.positionChanged.connect(self.on_positionChanged)


    def Show_Pic(self,image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.current_pixmap = QPixmap.fromImage(q_img)
      
          # 获取QLabel的当前可用尺寸
        label_size = self.pic_label.size()
        
        # 保持宽高比缩放
        scaled_pixmap = self.current_pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.pic_label.setPixmap(scaled_pixmap)
        self.pic_label.setAlignment(Qt.AlignCenter) 

   
    def On_Btn_select_pic_clicked(self):
        new_image  = cv2.imread("fengjing.jpg")
        if new_image  is None:
            return
        cmd = ImageCommand(self.current_image, new_image, self, "加载图片")
        self.current_image = new_image
        Static_Process_Widget.current_image_global = new_image
        
        self.undo_stack.push(cmd)
        self.Show_Pic(new_image)

    

    def On_Btn_Mean_Filter_clicked(self):
        if self.current_image is None:
            return
        blurred_image = cv2.blur(self.current_image, (5, 5))
        cmd = ImageCommand(self.current_image, blurred_image, self, "均值滤波")
        self.undo_stack.push(cmd)

        self.Show_Pic(blurred_image)

    def On_Btn_invertcolor_clicked(self):
        if self.current_image is None:
            return
        
        invertcolor_image = cv2.bitwise_not(self.current_image)
        cmd = ImageCommand(self.current_image, invertcolor_image, self, "反色")
        self.undo_stack.push(cmd)
        
        self.Show_Pic(invertcolor_image)
        
    #高斯滤波，并显示图像
    def On_Btn_Gaussian_Filter_clicked(self):
        if self.current_image is None:
            return
        
        gaussian_image = cv2.GaussianBlur(self.current_image, (3,3), 0, 0)
        cmd = ImageCommand(self.current_image, gaussian_image, self, "高斯滤波")
        self.undo_stack.push(cmd)
        self.Show_Pic(gaussian_image)

    #撤销        
    def On_Btn_undo_clicked(self):
        self.undo_stack.undo()

    #还原    
    def On_Btn_redo_clicked(self):
        self.undo_stack.redo()
        
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
        self.pic_label.setPixmap(scaled_pixmap)

    def wheelEvent(self, event):
        if self.change_size_enable == True:
            angle=event.angleDelta() / 8                                           # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
            print("angle:",angle)
            angleX=angle.x()                                                       # 水平滚过的距离(此处用不上)
            angleY=angle.y()  
            print(angleY)                                                     # 竖直滚过的距离
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

    
    #缩放
    def On_Btn_change_size_clicked(self):
        self.change_size_enable = not self.change_size_enable
        print("缩放：",self.change_size_enable)

    #旋转
    def On_Btn_rotate_clicked(self):
        if self.current_image is None:
            return
        flip_image = cv2.flip(cv2.transpose(self.current_image), 1)
        cmd = ImageCommand(self.current_image, flip_image, self, "旋转")
        self.undo_stack.push(cmd)
        self.Show_Pic(flip_image)

    #膨胀
    def On_Btn_dilate_clicked(self):
        if self.current_image is None:
            return
        kernel = np.ones((5, 5), np.uint8)
        dilate_image =cv2.dilate(self.current_image,kernel,iterations=1)
        cmd = ImageCommand(self.current_image, dilate_image, self, "膨胀")
        self.undo_stack.push(cmd)
        self.Show_Pic(dilate_image)

    #腐蚀
    def On_Btn_erode_clicked(self):
        if self.current_image is None:
            return
        kernel = np.ones((5, 5), np.uint8)
        erode_image =cv2.erode(self.current_image,kernel,iterations=1)
        cmd = ImageCommand(self.current_image, erode_image, self, "腐蚀")
        self.undo_stack.push(cmd)
        self.Show_Pic(erode_image)

    #改变亮度
    def adjust_brightness_cv(self):
        if self.current_image is None:
            return
        brightness = int(self.value_bright)
        print("brightness: ",brightness)
        bright_img = cv2.add(self.current_image, brightness)
        self.Show_Pic(bright_img)

    #改变对比度
    def adjust_contrast_cv(self):
        if self.current_image is None:
            return
        contrast = self.value_contrast
        print("contrast: ",contrast)
        contrast_img= cv2.convertScaleAbs(self.current_image, alpha=contrast, beta=0)
        self.Show_Pic(contrast_img)

    #亮度条改变
    def On_Slider_bright_changed(self):
        self.value_bright = self.slider_bright.value()
        self.adjust_brightness_cv()


    #对比度条改变
    def On_Slider_contrast_changed(self):
        self.value_contrast = self.slider_contrast.value()/10
        self.adjust_contrast_cv()

    #显示坐标和RGB
    def on_positionChanged(self, pos):
        self.img_x = pos.x()
        self.img_y = pos.y()
        pixmap = self.current_pixmap  
        if pixmap is None:
            return
        img = pixmap.toImage()
        if self.img_x >= img.width() or self.img_y >= img.height():
            return
        
        pixel = img.pixel(self.img_x, self.img_y)
        self.rgb = (pixel & 0xff0000) >> 16, (pixel & 0xff00) >> 8, (pixel & 0xff)
        self.ui.lineEdit_xy.setText(f"{self.img_x},{self.img_y}")
        self.ui.lineEdit_rgb.setText(f"{self.rgb[0]},{self.rgb[1]},{self.rgb[2]}")


    def vtk_render(self):
        reader1 = vtk.vtkDICOMImageReader()
        reader1.SetDirectoryName("3.000000-TRI LIVER C--55249")
        reader1.Update()
        reader = vtk.vtkImageFlip()
        reader.SetInputData(reader1.GetOutput())
        reader.Update()
        dimensions = reader.GetOutput().GetDimensions()
        print("dimensions:",dimensions)
        volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
        volumeMapper.SetInputConnection(reader.GetOutputPort())
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)

        volumeProperty = vtk.vtkVolumeProperty()

        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOn()
        volumeProperty.SetAmbient(0.4)
        volumeProperty.SetDiffuse(0.6)
        volumeProperty.SetSpecular(0.2)

        compositeOpacity = vtk.vtkPiecewiseFunction()
        compositeOpacity.AddPoint(70,0.00)
        compositeOpacity.AddPoint(90,0.40)
        compositeOpacity.AddPoint(180,0.60)
        volumeProperty.SetScalarOpacity(compositeOpacity)

        volumeGradientOpacity = vtk.vtkPiecewiseFunction()
        volumeGradientOpacity.AddPoint(10,0.00)
        volumeGradientOpacity.AddPoint(90,0.50)
        volumeGradientOpacity.AddPoint(100,1.0)
        volumeProperty.SetGradientOpacity(volumeGradientOpacity)

        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(0.000, 0.00, 0.00, 0.00)
        color.AddRGBPoint(64.00, 1.00, 0.52, 0.30)
        color.AddRGBPoint(190.0, 1.00, 1.00, 1.00)
        color.AddRGBPoint(220.0, 0.20, 0.20, 0.20)
        volumeProperty.SetColor(color)

        volume.SetProperty(volumeProperty)

        renderer = vtk.vtkRenderer()
        renderer.AddVolume(volume)

        # renderWindow = vtk.vtkRenderWindow()
        # renderWindow.AddRenderer(renderer)
        # renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        # renderWindowInteractor.SetRenderWindow(renderWindow)
        # style = vtk.vtkInteractorStyleTrackballCamera()
        # renderWindowInteractor.SetInteractorStyle(style)
        # renderWindowInteractor.Initialize()
        # renderer.ResetCamera()
        # renderWindow.Render()
        # renderWindowInteractor.Start()

        # self.vtk_widget.GetRenderWindow().AddRenderer(renderer)
        # renderer.ResetCamera()
        

        # style = vtk.vtkInteractorStyleTrackballCamera()
        # self.vtk_widget.SetInteractorStyle(style)

        # self.vtk_widget.GetRenderWindow().Render()



