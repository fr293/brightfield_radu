# -*- coding: utf-8 -*-

import sys
from math import *
import time
import atexit
import serial

# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *
#from PySide import QtGui, QtCore

from double_spin_box_widget_class import *
from thread_power_supply_class import *

import pyqtgraph as pg

# ****************************************************
# ******* CLASS - THREAD FOR GUI (main thread) *******
class GUIWindow(QMainWindow):
    #constructor
    def __init__(self):
        super(GUIWindow,self).__init__()
        
        #serial power supply
        ser_ps =serial.Serial('COM3', 19200,timeout=0.05)
        atexit.register(ser_ps.close)   # to be sure that serial communication is closed
        print "serial ps open"
        
        self.thread_ps = ThreadPowerSupply(ser_ps)
        self.thread_ps.start()
        self.initUI()
        
    def __del__(self):
        self.thread_ps.done_ps=True
        self.thread_ps.wait()
        print "Exit"             

    # Initialisation of GUI interface
    def initUI(self):
        
        #window characteristics
        dimx = 500
        dimy = 500
        self.setGeometry(200, 50, dimx, dimy)   # Coordinates of the window on the screen, dimension of window
        self.setWindowTitle('Magnetic Bead Tracking')
        self.setWindowIcon(QIcon('icon.png'))
        
        self.create_manual_current_group()
        self.create_manual_position_group()
        
        #create layouts
        main_layout = QVBoxLayout()
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.manual_current_group)
        right_layout.addWidget(self.manual_position_group)
        right_layout.setSizeConstraint(QLayout.SetFixedSize)      

        
        #create widgets/dock widgets from layouts
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_dock_widget = QDockWidget()
        right_dock_widget.setWidget(right_widget)
        
        #set widgets to main window
        self.setCentralWidget(main_widget)
        self.addDockWidget(Qt.RightDockWidgetArea,right_dock_widget)
        
    def create_manual_current_group(self):        
        #vbox containing spin box widgets
        vbox = QVBoxLayout()
        self.manual_current_list = []
        for i in range(4):
            self.manual_current_list.append(DoubleSpinBoxWidget('Current ' + str(i+1) ,0.1,[-2.5,0.1,2.5],self.current_changed))
            vbox.addWidget(self.manual_current_list[i]) 

        #add everything to group box
        self.manual_current_group = QGroupBox('MANUAL CURRENT CONTROL')
        self.manual_current_group.setLayout(vbox)
        
    def create_manual_position_group(self):        
        #vbox containing spin box widgets
        vbox = QVBoxLayout()
        self.manual_position_list = []
        for i in range(4):
            self.manual_position_list.append(DoubleSpinBoxWidget('Position ' + str(i+1) ,0,[0,0.01,50],self.position_changed))
            vbox.addWidget(self.manual_position_list[i])

        #add everything to group box
        self.manual_position_group = QGroupBox('MANUAL POSITION CONTROL')
        self.manual_position_group.setLayout(vbox)
        
    def current_changed(self):
        self.thread_ps.power_is_set_on=True
        print('current changed'+str(self.manual_current_list[0].value))
        self.thread_ps.curr_1_value = self.manual_current_list[0].value
        self.thread_ps.curr_1_changed = True
        self.thread_ps.i_1_refresh = 1
        return

    def position_changed(self):
        print('position changed')
        return

# ******** MAIN
def main():
    app = QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
         app = QApplication(sys.argv)
         
    GUIObject = GUIWindow()
    GUIObject.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()