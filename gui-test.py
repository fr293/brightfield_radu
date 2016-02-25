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
from button_class import *

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

        self.create_ps_group()
        self.create_current_group()
        self.create_position_group()
        
        #create layouts
        main_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.ps_group)
        right_layout.addWidget(self.current_group)
        right_layout.addWidget(self.position_group)
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
        self.statusBar()
        
    def create_current_group(self):        
        #vbox containing spin box widgets
        vbox = QVBoxLayout()

        hbox = QHBoxLayout()#
        hbox.addStretch(1)
        label = QLabel('Set Curr.')
        hbox.addWidget(label)
        hbox.addStretch(1)
        label = QLabel('PS Curr.')
        hbox.addWidget(label)
        vbox.addLayout(hbox)

        self.current_list = []
        for i in range(4):
            self.current_list.append(DoubleSpinBoxWidget('Current ' + str(i+1) ,0.0,[-2.5,0.05,2.5,5,3],self.set_current_changed,'A'))
            vbox.addWidget(self.current_list[i])

        #add everything to group box
        self.current_group = QGroupBox('CURRENT CONTROL')
        self.current_group.setLayout(vbox)

    def create_ps_group(self):
        self.ps_group = QGroupBox('POWER SUPPLY')

        self.ps_cont_widget = QWidget()
        self.ps_cont_toggle = DoubleToggleButtonWidget('Power ON','Power OFF',self.ps_power_on,self.ps_power_off)
        cont_vbox = QVBoxLayout()
        cont_vbox.addWidget(self.ps_cont_toggle)
        self.ps_cont_widget.setLayout(cont_vbox)

        self.ps_pulse_widget = QWidget()
        pulse_momentary = MomentaryButtonWidget('Pulse ON',self.ps_power_on,self.ps_power_off)
        pulse_vbox = QVBoxLayout()
        pulse_vbox.addWidget(pulse_momentary)
        self.ps_pulse_widget.setLayout(pulse_vbox)

        self.ps_mode_tab = QTabWidget()
        self.ps_mode_tab.addTab(self.ps_cont_widget,'Continuous')
        self.ps_mode_tab.addTab(self.ps_pulse_widget,'Pulse')
        self.ps_mode_tab.currentChanged.connect(self.ps_mode_changed)

        vbox = QVBoxLayout()
        vbox.addWidget(self.ps_mode_tab)
        self.ps_group.setLayout(vbox)

    def create_position_group(self):        
        #vbox containing spin box widgets
        vbox = QVBoxLayout()

        hbox = QHBoxLayout()#
        hbox.addStretch(1)
        label = QLabel('Set Pos.')
        hbox.addWidget(label)
        hbox.addStretch(1)
        label = QLabel('Act. Pos.')
        hbox.addWidget(label)
        vbox.addLayout(hbox)

        self.position_list = []
        self.position_list.append(DoubleSpinBoxWidget('x-axis ',0,[0,0.005,50,6,3],self.position_changed,'mm'))
        self.position_list.append(DoubleSpinBoxWidget('y-axis ',0,[0,0.005,50,6,3],self.position_changed,'mm'))
        self.position_list.append(DoubleSpinBoxWidget('z-axis ',0,[0,0.005,50,6,3],self.position_changed,'mm'))
        for widget in self.position_list:
            vbox.addWidget(widget)

        #add everything to group box
        self.position_group = QGroupBox('POSITION CONTROL')
        self.position_group.setLayout(vbox)

    def ps_power_on(self):
        print('ps power on')
        self.thread_ps.power_is_set_on = True

    def ps_power_off(self):
        print('ps power off')
        self.thread_ps.power_is_set_off = True

    def ps_mode_changed(self,tab_index):
        #turn off power supply on mode change
        if self.ps_cont_toggle.toggleFlag == 1:
                self.ps_cont_toggle.toggle()
        #continuous mode
        if tab_index == 0:
            print('cont mode')
        #pulse mode
        if tab_index == 1:
            print('pulse mode')

    def set_current_changed(self):
        for i in range(4):
            if self.thread_ps.current_value[i] != self.current_list[i].set_value:
                self.thread_ps.current_value[i] = self.current_list[i].set_value
                self.thread_ps.current_changed[i] = True
                self.thread_ps.current_refresh[i] = 1
                print('current '+ str(i) +' changed: '+str(self.current_list[i].set_value))
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