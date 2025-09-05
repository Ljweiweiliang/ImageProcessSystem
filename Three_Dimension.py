import sys
from PyQt5.QtWidgets import QWidget,QApplication,QUndoCommand,QUndoStack
from PyQt5.QtGui import QPixmap, QImage,QMouseEvent,QTransform
from PyQt5.QtCore import Qt,pyqtSignal, QObject
from PyQt5 import QtCore
import Designer.Ui_Three_Dimension as Ui_Three_Dimension
import cv2 
import matplotlib.pyplot as plt
import numpy as np 
import vtk
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# pylint: disable=invalid-name,missing-class-docstring,too-few-public-methods
class Three_Dimension_Widget(QWidget):
   
    def __init__(self):
        super().__init__() 
        self.ui = Ui_Three_Dimension.Ui_Three_Dimension()
        self.ui.setupUi(self)

        self.vtk_widget = QVTKRenderWindowInteractor(self.ui.pic_label)
        layout = QVBoxLayout()
        layout.addWidget(self.vtk_widget)
        self.ui.pic_label.setLayout(layout)
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    def On_Btn_Volume_Clicked(self):
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

        self.vtk_widget.GetRenderWindow().AddRenderer(renderer)
        renderer.ResetCamera()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(style)
        self.vtk_widget.GetRenderWindow().Render()


