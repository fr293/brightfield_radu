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
from button_widget_class import *
from thread_display_class import *

import pyqtgraph as pg

# ****************************************************
# ******* CLASS - THREAD FOR GUI (main thread) *******
class GUIWindow(QMainWindow):
    #constructor
    def __init__(self):
        super(GUIWindow,self).__init__()
        
        #serial power supply
        serial_ps = serial.Serial('COM3', 19200,timeout=0.05)
        atexit.register(serial_ps.close)   # to be sure that serial communication is closed
        print "serial ps open"
        
        self.thread_ps = ThreadPowerSupply(serial_ps)
        self.thread_ps.start()

        self.thread_disp = ThreadDisplay(self)
        self.thread_disp.start()

        self.initUI()
        
    def __del__(self):
        self.thread_ps.done_ps=True
        self.thread_ps.wait()
        print "Exit"             

    # Initialisation of GUI interface
    def initUI(self):
        
        #window characteristics
        dimx = 800
        dimy = 800
        self.setGeometry(200, 50, dimx, dimy)   # Coordinates of the window on the screen, dimension of window
        self.setWindowTitle('Magnetic Bead Tracking')
        self.setWindowIcon(QIcon('icon.png'))

        self.create_ps_group()
        self.create_current_group()
        self.create_pos_group()
        self.create_disp_group()
        self.create_bead_group()

        #create layouts
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.disp_group)

        #create widgets/dock widgets from group boxes
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        ps_dock = QDockWidget()
        ps_dock.setWidget(self.ps_group)
        current_dock = QDockWidget()
        current_dock.setWidget(self.current_group)
        pos_dock = QDockWidget()
        pos_dock.setWidget(self.pos_group)
        bead_dock = QDockWidget()
        bead_dock.setWidget(self.bead_group)

        #set widgets to main window
        self.setCentralWidget(main_widget)
        self.addDockWidget(Qt.RightDockWidgetArea,ps_dock)
        self.addDockWidget(Qt.RightDockWidgetArea,current_dock)
        self.addDockWidget(Qt.RightDockWidgetArea,pos_dock)
        self.addDockWidget(Qt.BottomDockWidgetArea,bead_dock)
        #status bar
        self.statbar = QStatusBar()
        self.statbar.showMessage('Init UI Complete')
        self.setStatusBar(self.statbar)

    def create_disp_group(self):
        self.disp_group = QWidget

    def create_bead_group(self):
        #display settings group
        vbox = QVBoxLayout()
        self.bead_zoom_sbox = SpinBoxWidget('Zoom',6,[1,1,25],[4,1],self.bead_changed)
        vbox.addWidget(self.bead_zoom_sbox)
        self.bead_grid_size_sbox = SpinBoxWidget('Grid Size',1100,[0,100,1300],[4,0],self.bead_changed)
        vbox.addWidget(self.bead_grid_size_sbox)

        #FPS sub group
        group = QGroupBox()
        vbox_ = QVBoxLayout()
        self.bead_fps_sbox = SpinBoxWidget('FPS',10,[0,1,20],[2,0],self.bead_changed)
        vbox_.addWidget(self.bead_fps_sbox)
        self.bead_fps = ValueDisplayWidget('Actual FPS',[4,1],10)
        vbox_.addWidget(self.bead_fps)
        self.bead_deltat = ValueDisplayWidget('Delta t',[5,1],100)
        vbox_.addWidget(self.bead_deltat)
        group.setLayout(vbox_)
        vbox.addWidget(group)

        vbox.addStretch(1)

        display_group = QGroupBox('DISPLAY SETTINGS')
        display_group.setLayout(vbox)
        display_group.setFixedWidth(200)

        #bead detection settings group
        vbox = QVBoxLayout()
        dict = {'area':['Area       ',[600,1500],[0,100],[10,100],[10000,10000],5,0],
             'circ':['Circularity',[0.8,1.23],[0.5,0.5],[0.01,0.01],[1.5,1.5],4,2],
             'thresh1':['Threshold 1',[80,250],[1,1],[1,10],[255,255],3,0],
             'thresh2':['Threshold 2',[80,250],[1,1],[1,10],[255,255],3,0]}

        for key in ['area','circ','thresh1','thresh2']:
            val = dict[key]
            label = QLabel(val[0])
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addStretch(2)

            widget_str = 'self.bead_'+key+'min_sbox'
            vars()[widget_str] = SpinBoxWidget('min',val[1][0],[val[2][0],val[3][0],val[4][0]],[val[5],val[6]],self.bead_changed)
            hbox.addWidget(vars()[widget_str])
            widget_str = 'self.bead_'+key+'max_sbox'
            vars()[widget_str] = SpinBoxWidget('max',val[1][1],[val[2][1],val[3][1],val[4][1]],[val[5],val[6]],self.bead_changed)
            hbox.addWidget(vars()[widget_str])

            vbox.addLayout(hbox)

        detection_group = QGroupBox('BEAD DETECTION')
        detection_group.setLayout(vbox)
        detection_group.setFixedWidth(250)

        #camera groups
        for i in range(1,3):
            vbox = QVBoxLayout()
            dict = {'focus':['Focus',[4,2],1.31],
                    'round':['Round',[4,2],1.31],
                    'nbead':['No. of Beads',[1,0],1],
                    'centerx':['Center x',[4,0],991],
                    'centery':['Center y',[4,0],1040],
                    'width':['Width',[4,0],85],
                    'height':['Height',[4,0],84],
                    }
            for key in ['focus','round','nbead','centerx','centery','width','height']:
                val = dict[key]
                widget_str = 'self.bead_'+key+str(i)
                vars()[widget_str] = ValueDisplayWidget(val[0],val[1],val[2])
                vbox.addWidget(vars()[widget_str])

            if i == 1:
                cam1_group = QGroupBox('CAMERA 1')
                cam1_group.setLayout(vbox)
                cam1_group.setFixedWidth(150)
            elif i == 2:
                cam2_group = QGroupBox('CAMERA 2')
                cam2_group.setLayout(vbox)
                cam2_group.setFixedWidth(150)

        #z tracking
        vbox = QVBoxLayout()
        self.bead_zact_tbutton = DoubleToggleButtonWidget(['Start','Stop','z Actuator Pooling'],self.bead_zact_toggle)
        vbox.addWidget(self.bead_zact_tbutton)
        self.bead_ztrack_tbutton = DoubleToggleButtonWidget(['Start','Stop','z Tracking'],self.bead_ztrack_toggle)
        vbox.addWidget(self.bead_ztrack_tbutton)
        vbox.addStretch(1)

        ztracking_group = QGroupBox('Z TRACKING')
        ztracking_group.setLayout(vbox)
        ztracking_group.setFixedWidth(250)

        hbox = QHBoxLayout()
        hbox.addWidget(display_group)
        hbox.addWidget(detection_group)
        hbox.addWidget(cam1_group)
        hbox.addWidget(cam2_group)
        hbox.addWidget(ztracking_group)
        hbox.addStretch(1)

        self.bead_group = QGroupBox('BEAD CONTROL PANEL')
        self.bead_group.setLayout(hbox)

    def create_current_group(self):
        #vbox containing spin box widgets
        vbox = QVBoxLayout()

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        label = QLabel('Set Curr.')
        hbox.addWidget(label)
        hbox.addStretch(1)
        label = QLabel('PS Curr.')
        hbox.addWidget(label)
        vbox.addLayout(hbox)

        self.set_current_list = []
        for i in range(4):
            self.set_current_list.append(DoubleSpinBoxWidget('Current ' + str(i+1) ,0.0,[-2.5,0.05,2.5],[5,3],self.set_current_changed,'A'))
            vbox.addWidget(self.set_current_list[i])
        vbox.addStretch(1)

        #add everything to group box
        self.current_group = QGroupBox('CURRENT CONTROL')
        self.current_group.setLayout(vbox)
        self.current_group.setFixedWidth(250)

    def create_ps_group(self):
        self.ps_cont_widget = QWidget()
        self.ps_cont_tbutton = DoubleToggleButtonWidget(['Power ON','Power OFF'],self.ps_power_toggle)
        cont_vbox = QVBoxLayout()
        cont_vbox.addWidget(self.ps_cont_tbutton)
        self.ps_cont_widget.setLayout(cont_vbox)

        self.ps_pulse_widget = QWidget()
        self.ps_pulse_mbutton = MomentaryButtonWidget('Pulse ON',self.ps_power_toggle)
        pulse_vbox = QVBoxLayout()
        pulse_vbox.addWidget(self.ps_pulse_mbutton)
        self.ps_pulse_widget.setLayout(pulse_vbox)

        self.ps_mode_tab = QTabWidget()
        self.ps_mode_tab.addTab(self.ps_cont_widget,'Continuous')
        self.ps_mode_tab.addTab(self.ps_pulse_widget,'Pulse')
        self.ps_mode_tab.currentChanged.connect(self.ps_mode_changed)

        self.ps_led_tbutton = DoubleToggleButtonWidget(['LED ON','LED OFF'],self.ps_led_toggle)

        vbox = QVBoxLayout()
        vbox.addWidget(self.ps_mode_tab)
        vbox.addWidget(self.ps_led_tbutton)

        self.ps_group = QGroupBox('POWER SUPPLY')
        self.ps_group.setLayout(vbox)
        self.ps_group.setFixedWidth(250)

    def create_pos_group(self):
        vbox = QVBoxLayout()
        #labels
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        label = QLabel('Set Pos.')
        hbox.addWidget(label)
        hbox.addStretch(1)
        label = QLabel('Act. Pos.')
        hbox.addWidget(label)
        vbox.addLayout(hbox)
        #spin boxes
        self.set_position_list = []
        self.set_position_list.append(DoubleSpinBoxWidget('x-axis ',0,[0,0.005,50],[6,3],self.position_changed,'mm'))
        self.set_position_list.append(DoubleSpinBoxWidget('y-axis ',0,[0,0.005,50],[6,3],self.position_changed,'mm'))
        self.set_position_list.append(DoubleSpinBoxWidget('z-axis ',0,[0,0.005,50],[6,3],self.position_changed,'mm'))
        for widget in self.set_position_list:
            vbox.addWidget(widget)
        vbox.addStretch(1)
        #add everything to group box
        self.pos_group = QGroupBox('POSITION CONTROL')
        self.pos_group.setLayout(vbox)
        self.pos_group.setFixedWidth(250)

    def ps_power_toggle(self,toggleFlag):
        if toggleFlag == True:
            print('ps power on')
            self.thread_ps.power_is_set_on = True
        elif toggleFlag == False:
            print('ps power off')
            self.thread_ps.power_is_set_off = True

    def ps_mode_changed(self,tab_index):
        #turn off power supply on mode change
        if self.ps_cont_tbutton.toggleFlag == 1:
                self.ps_cont_tbutton.toggle()
        #continuous mode
        if tab_index == 0:
            print('cont mode')
        #pulse mode
        if tab_index == 1:
            print('pulse mode')

    def ps_led_toggle(self,toggleFlag):
        if toggleFlag == True:
            print('LED power on')
            self.thread_ps.led_is_set_on = True
        elif toggleFlag == False:
            print('LED power off')
            self.thread_ps.led_is_set_off = True

    def set_current_changed(self):
        for i in range(4):
            if self.thread_ps.current_value[i] != self.set_current_list[i].set_value:
                self.thread_ps.current_value[i] = self.set_current_list[i].set_value
                self.thread_ps.current_changed[i] = True
                self.thread_ps.current_refresh[i] = 1
                print('current '+ str(i) +' changed: '+str(self.set_current_list[i].set_value))
        return

    def bead_changed(self,bead_zoom):
        self.thread_disp.bead_zoom = bead_zoom

    def bead_zact_toggle(self,toggleFlag):
        if toggleFlag == True:
            print('z actuator pooling')
        elif toggleFlag == False:
            print('z actuator stopped')

    def bead_ztrack_toggle(self,toggleFlag):
        if toggleFlag == True:
            print('z tracking on')
        elif toggleFlag == False:
            print('z tracking off')

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