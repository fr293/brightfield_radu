# -*- coding: utf-8 -*-
sandbox = False

import sys
from math import *
import time
import atexit
import serial

# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *
#from PySide import QtGui, QtCore

from spin_box_widget_class import *
from thread_power_supply_class import *
from button_widget_class import *
if sandbox == False:
    from display_widget_class import *
from thread_detection_class import *
from axis_class import *
from thread_control_class import *
from thread_actuator_class import *

import pyqtgraph as pg

mutex = QMutex()

# ****************************************************
# ******* CLASS - THREAD FOR GUI (main thread) *******
class GUIWindow(QMainWindow):
    #constructor
    def __init__(self):
        super(GUIWindow,self).__init__()
        self.init_flag = False

        #serial power supply
        if sandbox == True:
            serial_ps = serial.Serial('COM3', 19200,timeout=0.05)
        else:
            serial_ps = serial.Serial('COM5', 19200,timeout=0.05)
        atexit.register(serial_ps.close)   # to be sure that serial communication is closed
        print "serial ps open"
        
        self.thread_ps = ThreadPowerSupply(serial_ps)
        self.thread_ps.start()
        self.thread_cont = ThreadControl(self)
        self.thread_cont.start()
        self.thread_det = ThreadDetection(self)
        self.thread_det.start()

        if sandbox == False:
            self.disp_widget = DisplayWidget(self.thread_det)

        self.initUI()
        self.mutex = QMutex()
        self.thread_act = ThreadActuator(self,self.axis_list)
        self.thread_act.start()

        self.init_flag = True

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
        self.setWindowTitle('Magnetic Bead Experiment')
        self.setWindowIcon(QIcon('icon.png'))

        self.bead_dict = {}
        self.create_ps_group()
        self.create_magnet_group()
        self.create_act_group()
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
        magnet_dock = QDockWidget()
        magnet_dock.setWidget(self.magnet_group)
        act_dock = QDockWidget()
        act_dock.setWidget(self.act_group)
        bead_dock = QDockWidget()
        bead_dock.setWidget(self.bead_group)

        #set widgets to main window
        self.setCentralWidget(main_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,ps_dock)
        self.addDockWidget(Qt.LeftDockWidgetArea,magnet_dock)
        self.addDockWidget(Qt.RightDockWidgetArea,act_dock)
        self.addDockWidget(Qt.BottomDockWidgetArea,bead_dock)

        #status bar
        self.statbar = QStatusBar()
        self.statbar.showMessage('Init UI Complete')
        self.setStatusBar(self.statbar)

    def create_disp_group(self):
        self.disp_group = QGroupBox('VIDEO DISPLAY')

        vbox = QVBoxLayout()
        if sandbox == False:
            vbox.addWidget(self.disp_widget)

        self.disp_group.setLayout(vbox)

    def create_bead_group(self):
        #display settings group
        vbox = QVBoxLayout()
        self.bead_zoom_sbox = SpinBoxWidget(['Zoom','','zoom'],6,[1,1,25],[4,1],self.thread_det.value_changed,False)
        vbox.addWidget(self.bead_zoom_sbox)
        self.bead_grid_size_sbox = SpinBoxWidget(['Grid Size','','grid_size'],1100,[0,100,1300],[4,0],self.thread_det.value_changed,False)
        vbox.addWidget(self.bead_grid_size_sbox)

        #FPS sub group
        group = QGroupBox()
        vbox_ = QVBoxLayout()
        self.bead_fps_sbox = SpinBoxWidget(['FPS','','set_fps'],10,[0,1,20],[2,0],self.thread_det.value_changed,False)
        vbox_.addWidget(self.bead_fps_sbox)
        self.bead_dict['max_fps'] = ValueDisplayWidget('Max FPS',[2,0],0)
        vbox_.addWidget(self.bead_dict['max_fps'])
        self.bead_dict['fps'] = ValueDisplayWidget('Actual FPS',[2,0],0)
        vbox_.addWidget(self.bead_dict['fps'])
        self.bead_dict['dt_fps'] = ValueDisplayWidget(['Delta t','ms'],[2,0],0)
        vbox_.addWidget(self.bead_dict['dt_fps'])
        group.setLayout(vbox_)
        vbox.addWidget(group)

        vbox.addStretch(1)

        display_group = QGroupBox('DISPLAY SETTINGS')
        display_group.setLayout(vbox)
        display_group.setFixedWidth(200)

        #bead detection settings group
        vbox = QVBoxLayout()
        self.bead_size_sbox = SpinBoxWidget(['Bead Size','um','bead_size'],41.13,[20,0.01,60],[5,2],self.thread_det.value_changed,False)
        vbox.addWidget(self.bead_size_sbox)
        dict = {'area':['Area',[700,9900],[0,100],[10,100],[10000,10000],5,0],
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
            vars()[widget_str] = SpinBoxWidget(['min','',key+'_min'],val[1][0],[val[2][0],val[3][0],val[4][0]],[val[5],val[6]],self.thread_det.value_changed,False)
            hbox.addWidget(vars()[widget_str])
            widget_str = 'self.bead_'+key+'max_sbox'
            vars()[widget_str] = SpinBoxWidget(['max','',key+'_max'],val[1][1],[val[2][1],val[3][1],val[4][1]],[val[5],val[6]],self.thread_det.value_changed,False)
            hbox.addWidget(vars()[widget_str])

            vbox.addLayout(hbox)
        vbox.addStretch(1)

        detection_group = QGroupBox('BEAD DETECTION')
        detection_group.setLayout(vbox)
        detection_group.setFixedWidth(250)

        #camera groups
        for i in [1,2]:
            vbox = QVBoxLayout()
            dict = {'focus':['Focus',[4,2],1.31],
                    'round':['Round',[4,2],1.31],
                    'nbead':['No. of Beads',[1,0],1],
                    'centerx':[['Center x','px'],[4,0],991],
                    'centery':[['Center y','px'],[4,0],1040],
                    'width':[['Width','px'],[4,0],85],
                    'height':[['Height','px'],[4,0],84],
                    }
            for key in ['focus','round','nbead','centerx','centery','width','height']:
                val = dict[key]
                widget_str = key+str(i)
                self.bead_dict[widget_str] = ValueDisplayWidget(val[0],val[1],val[2])
                vbox.addWidget(self.bead_dict[widget_str])
            vbox.addStretch(1)
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

    def create_magnet_group(self):
        vbox = QVBoxLayout()

        #current display subgroup
        group = QGroupBox('CURRENTS')
        vbox_ = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        label = QLabel('Set Curr.')
        hbox.addWidget(label)
        hbox.addStretch(1)
        label = QLabel('PS Curr.')
        hbox.addWidget(label)
        vbox_.addLayout(hbox)
        self.set_current_sbox = []
        for i in range(4):
            self.set_current_sbox.append(SpinBoxWidget(['Current '+str(i+1),'A',str(i+1)],0.0,[-2.5,0.05,2.5],[5,3],self.set_current_changed,True))
            vbox_.addWidget(self.set_current_sbox[i])
        group.setLayout(vbox_)
        vbox.addWidget(group)

        #control subgroup
        group = QGroupBox('BEAD MANIPULATION')
        #manual direction tab
        magnet_manual_widget = QWidget()
        grid = QGridLayout()
        names = ['z-', 'y+', 'z+',
                 'x-', '', 'x+',
                '', 'y-', '']
        positions = [(i,j) for i in range(3) for j in range(3)]
        for position, name in zip(positions, names):
            if name == '':
                continue
            button = PushButtonWidget(name,self.thread_cont.manual_direction,name)
            grid.addWidget(button, *position)
        self.magnet_manual_base_current_sbox = SpinBoxWidget(['Base Current','A'],0.5,[-2.5,0.05,2.5],[5,3],self.thread_cont.manual_base_current_changed,False)
        grid.addWidget(self.magnet_manual_base_current_sbox,3,0,1,3)
        grid.setRowStretch(4,1)
        magnet_manual_widget.setLayout(grid)
        #hold tab
        magnet_hold_widget = QWidget()
        vbox_ = QVBoxLayout()
        self.magnet_hold_tbutton = DoubleToggleButtonWidget(['Hold','Release'],self.thread_cont.hold_toggle)
        vbox_.addWidget(self.magnet_hold_tbutton)
        vbox_.addStretch(1)
        magnet_hold_widget.setLayout(vbox_)
        #move tab
        magnet_move_widget = QWidget()
        vbox_ = QVBoxLayout()
        self.magnet_set_pos_sbox = []
        self.magnet_set_pos_sbox.append(SpinBoxWidget(['x','mm','x'],0,[-50,0.002,50],[6,3],self.thread_cont.magnet_set_changed,False))
        self.magnet_set_pos_sbox.append(SpinBoxWidget(['y','mm','y'],0,[-50,0.002,50],[6,3],self.thread_cont.magnet_set_changed,False))
        self.magnet_set_pos_sbox.append(SpinBoxWidget(['z','mm','z'],0,[-50,0.002,50],[6,3],self.thread_cont.magnet_set_changed,False))
        self.magnet_absrel_tbutton = DoubleToggleButtonWidget(['Absolute','Relative'],self.thread_cont.absrel_toggle,'radio')
        self.magnet_start_tbutton = DoubleToggleButtonWidget(['Start','Stop'],self.thread_cont.start_toggle)
        vbox_.addWidget(self.magnet_set_pos_sbox[0])
        vbox_.addWidget(self.magnet_set_pos_sbox[1])
        vbox_.addWidget(self.magnet_set_pos_sbox[2])
        vbox_.addWidget(self.magnet_absrel_tbutton)
        vbox_.addWidget(self.magnet_start_tbutton)
        vbox_.addStretch(1)
        magnet_move_widget.setLayout(vbox_)
        #tabs
        self.magnet_tab = QTabWidget()
        self.magnet_tab.addTab(magnet_manual_widget,'Manual')
        self.magnet_tab.addTab(magnet_hold_widget,'Hold')
        self.magnet_tab.addTab(magnet_move_widget,'Move')
        self.magnet_tab.currentChanged.connect(self.magnet_mode_changed)


        vbox_ = QVBoxLayout()
        self.bead_dict['position'] = []
        self.bead_dict['position'].append(ValueDisplayWidget(['Bead Position x','mm'],[6,3]))
        vbox_.addWidget(self.bead_dict['position'][0])
        self.bead_dict['position'].append(ValueDisplayWidget(['Bead Position y','mm'],[6,3]))
        vbox_.addWidget(self.bead_dict['position'][1])
        self.bead_dict['position'].append(ValueDisplayWidget(['Bead Position z','mm'],[6,3]))
        vbox_.addWidget(self.bead_dict['position'][2])
        vbox_.addWidget(self.magnet_tab)
        vbox_.addStretch(1)
        group.setLayout(vbox_)
        vbox.addWidget(group)

        #add everything to group box
        self.magnet_group = QGroupBox('MAGNET CONTROL PANEL')
        self.magnet_group.setLayout(vbox)
        self.magnet_group.setFixedWidth(250)

    def create_ps_group(self):
        self.ps_cont_widget = QWidget()
        self.ps_cont_tbutton = DoubleToggleButtonWidget(['Power ON','Power OFF'],self.thread_ps.power_toggle)
        cont_vbox = QVBoxLayout()
        cont_vbox.addWidget(self.ps_cont_tbutton)
        self.ps_cont_widget.setLayout(cont_vbox)

        self.ps_pulse_widget = QWidget()
        self.ps_pulse_mbutton = MomentaryButtonWidget('Pulse ON',self.thread_ps.power_toggle)
        pulse_vbox = QVBoxLayout()
        pulse_vbox.addWidget(self.ps_pulse_mbutton)
        self.ps_pulse_widget.setLayout(pulse_vbox)

        self.ps_mode_tab = QTabWidget()
        self.ps_mode_tab.addTab(self.ps_cont_widget,'Continuous')
        self.ps_mode_tab.addTab(self.ps_pulse_widget,'Pulse')
        self.ps_mode_tab.currentChanged.connect(self.ps_mode_changed)

        self.ps_led_tbutton = DoubleToggleButtonWidget(['LED ON','LED OFF'],self.thread_ps.led_toggle)

        vbox = QVBoxLayout()
        vbox.addWidget(self.ps_mode_tab)
        vbox.addWidget(self.ps_led_tbutton)
        vbox.addStretch(1)

        self.ps_group = QGroupBox('POWER SUPPLY')
        self.ps_group.setLayout(vbox)
        self.ps_group.setFixedWidth(250)

    def create_act_group(self):
        vbox = QVBoxLayout()
        self.act_estop_button = PushButtonWidget('Emergency Stop',self.act_estop)
        vbox.addWidget(self.act_estop_button)
        self.axis_list = []
        for axis_label,axis_address in zip(['x-axis','y-axis','y2-axis'],[1,2,3]):
            #create axis object
            axis = Axis(axis_label,axis_address)
            self.axis_list.append(axis)
            #group box
            gbox = QGroupBox(axis_label)
            gbox.setLayout(axis.vbox)
            vbox.addWidget(gbox)
        vbox.addStretch(1)
        self.act_textbar = QLineEdit()
        self.act_textbar.setReadOnly(True)
        vbox.addWidget(self.act_textbar)
        #add everything to group box
        self.act_group = QGroupBox('ACTUATOR CONTROL PANEL')
        self.act_group.setLayout(vbox)
        self.act_group.setFixedWidth(300)

    def act_estop(self):
        self.thread_act.estop()
        print('EMERGENCY STOP')


    def ps_mode_changed(self,tab_index):
        #turn off power supply on mode change
        self.ps_cont_tbutton.set_toggle(False)
        #continuous mode
        if tab_index == 0:
            print('cont mode')
        #pulse mode
        if tab_index == 1:
            print('pulse mode')

    def set_current_changed(self,value,ref_text):
        i = int(ref_text)-1
        self.thread_ps.current_value[i] = value
        self.thread_ps.current_changed[i] = True
        self.thread_ps.current_refresh[i] = 1
        print('current '+ str(i) +' changed: '+str(value))

    def magnet_mode_changed(self,tab_index):
        #turn off hold on mode change
        if self.magnet_hold_tbutton.toggle_flag == 1:
                self.magnet_hold_tbutton.toggle()
        #continuous mode
        if tab_index == 0:
            print('manual direction mode')
        #pulse mode
        if tab_index == 1:
            print('hold mode')

    def bead_changed(self,value,ref_text):
        print('bead changed')

        widget_str = 'self.thread_det.'+ref_text
        vars()[widget_str] = value

    def disp_changed(self,value,ref_text):
        print('disp changed')

        widget_str = 'self.thread_det.'+ref_text
        vars()[widget_str] = value

    def bead_zact_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('z actuator pooling')
        elif toggle_flag == False:
            print('z actuator stopped')

    def bead_ztrack_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('z tracking on')
        elif toggle_flag == False:
            print('z tracking off')

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