import sys
from PyQt5.QtWidgets import QWidget,QApplication,QMainWindow,QLabel,QMessageBox,QFileDialog,QUndoStack, QUndoCommand  
from PyQt5.QtGui import QPixmap, QImage,QMouseEvent,QTransform
import Designer.Ui_ImageProcess as Ui_ImageProcess
import cv2 
import matplotlib.pyplot as plt
import numpy as np 
from PyQt5.QtCore import Qt
from PyQt5 import QtCore,QtWidgets
import Static_Process
import Three_Dimension

#撤销 还原
class ImageCommand(QUndoCommand):
    
    def __init__(self, old_image, new_image, parent, description=""):
        super().__init__(description)
        self.old_image = old_image.copy() if old_image is not None else None
        self.new_image = new_image.copy() if new_image is not None else None
        self.parent = parent 
    def undo(self):
        if self.old_image is not None:
            self.parent.current_image = self.old_image.copy()
            self.parent.Show_Pic(self.old_image)
    def redo(self):
        if self.new_image is not None:
            self.parent.current_image = self.new_image.copy()
            self.parent.Show_Pic(self.new_image)


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
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ImageProcess.Ui_ImageProcess()
        self.ui.setupUi(self)
        self.setMouseTracking(True) 
        self.listwidget = self.ui.listWidget #ListWidget
        self.stackedWidget = self.ui.stackedWidget #StackedWidget
      
        
       
      
        self.original_image = None
        self.current_image = None  


     
        
 
        while self.stackedWidget.count() > 0:
            self.stackedWidget.removeWidget(self.stackedWidget.widget(0))
        

        self.static_process_page = Static_Process.Static_Process_Widget()  
        self.three_dimensional_page = Three_Dimension.Three_Dimension_Widget() 

        self.stackedWidget.addWidget(self.static_process_page) 
        self.stackedWidget.addWidget(self.three_dimensional_page)  
        #self.stackedWidget.addWidget(QWidget())  
        



    def On_ListWidget_currentrowchanged(self):
        index = self.listwidget.currentRow()
        print(self.listwidget.currentRow())
        self.stackedWidget.setCurrentIndex(index)
        if index == 0:
            print("")
            self.stackedWidget.setCurrentIndex(0)
        elif index == 1:
            print("")
            self.stackedWidget.setCurrentIndex(1) 
        
       

    def On_comboBox_method_changed(self,index):
        current_text = self.ui.comboBox_method.currentText()
        self.current_comboBox_index = index
       
         
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


