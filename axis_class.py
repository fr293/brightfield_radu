import time
import numpy as np

from PySide.QtCore import *
from PySide.QtGui import *

from spin_box_widget_class import *
from thread_power_supply_class import *
from button_widget_class import *
from thread_detection_class import *

class Axis:
    def __init__(self,axis_name):
        self.axis_name = axis_name
        self.encoder_resolution = 0.05101E-3 #mm

        #0 ready
        #1 action start
        #2 action in progress
        #3 action stop
        self.move_status = 0
        self.pos_type = 'abs'
        self.move_type = 'jog'
        self.feed_vel = 0

        self.position = 0
        self.position_l = 0
        self.encoder_position = 0
        self.encoder_position_l = 0
        self.set_position = 0
        self.encoder_set_position = 0
        self.lock_encoder_position = 0

        self.value = ValueDisplayWidget(['Position','mm'],[6,3])
        self.abs_value = ValueDisplayWidget(['Abs','mm'],[6,3])
        self.sbox = SpinBoxWidget(['Set Position','mm'],0,[0,0.005,50],[6,3],self.set_position_changed,False)
        self.zero_button = PushButtonWidget('Zero',self.zero)
        self.home_button = PushButtonWidget('Home',self.home)
        self.lock_tbutton = DoubleToggleButtonWidget(['Lock','Unlock'],self.lock_toggle)
        self.absrel_tbutton = DoubleToggleButtonWidget(['Absolute','Relative'],self.absrel_toggle,'radio')
        self.start_tbutton = DoubleToggleButtonWidget(['Start','Stop'],self.start_toggle)
        self.jogp_mbutton = MomentaryButtonWidget('Jog +',self.jogp_toggle)
        self.jogm_mbutton = MomentaryButtonWidget('Jog -',self.jogm_toggle)
        self.feed_sbox = SpinBoxWidget(['Feed Velocity','mm/s'],0,[-10,0.5,10],[4,1],self.feed_vel_changed,False)
        self.feed_tbutton = DoubleToggleButtonWidget(['Start','Stop','Feed Axis'],self.feed_toggle)

        #tabs
        self.tab = QTabWidget()

        self.functions_widget = QWidget()
        vbox_ = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.home_button)
        hbox.addWidget(self.zero_button)
        vbox_.addLayout(hbox)
        vbox_.addWidget(self.lock_tbutton)
        vbox_.addStretch(1)
        self.functions_widget.setLayout(vbox_)

        self.move_widget = QWidget()
        vbox_ = QVBoxLayout()
        vbox_.addWidget(self.sbox)
        vbox_.addWidget(self.absrel_tbutton)
        vbox_.addWidget(self.start_tbutton)
        vbox_.addStretch(1)
        self.move_widget.setLayout(vbox_)

        self.manual_widget = QWidget()
        vbox_ = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.jogm_mbutton)
        hbox.addWidget(self.jogp_mbutton)
        vbox_.addLayout(hbox)
        vbox_.addWidget(self.feed_tbutton)
        vbox_.addWidget(self.feed_sbox)
        self.manual_widget.setLayout(vbox_)

        self.tab.addTab(self.functions_widget,'Functions')
        self.tab.addTab(self.move_widget,'Move')
        self.tab.addTab(self.manual_widget,'Manual')

        self.vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.value)
        hbox.addStretch(1)
        hbox.addWidget(self.abs_value)
        self.vbox.addLayout(hbox)
        self.vbox.addWidget(self.tab)
        self.widget = QWidget()
        self.widget.setLayout(self.vbox)

    def set_position_changed(self,value):
        print(self.axis_name + ': set position changed' + str(value))
        self.set_position = value
        self.calculate_positions()

    def absrel_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.pos_type = 'abs'
            print(self.axis_name + ': move type abs')
        else:
            self.pos_type = 'rel'
            print(self.axis_name + ': move type rel')

        self.calculate_positions()

    def start_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.move_flag = 1
            print(self.axis_name + ': start movement')
        else:
            self.move_flag = 3
            self.home_flag = 0
            print(self.axis_name + ': stop movement')

    def lock_toggle(self,toggle_flag):
        if toggle_flag == True:
            print(self.axis_name + ': lock')
        else:
            print(self.axis_name + ': unlock')

    def jogp_toggle(self,toggle_flag):
        if toggle_flag == True:
            print(self.axis_name + ': jog+')

    def jogm_toggle(self,toggle_flag):
        if toggle_flag == True:
            print(self.axis_name + ': jog-')

    def zero(self):
        print(self.axis_name + ': zero')

    def home(self):
        print(self.axis_name + ': home')

    def feed_toggle(self,toggle_flag):
        print(self.axis_name + ': feed' + str(self.feed_vel))

    def feed_vel_changed(self,feed_vel):
        self.feed_vel = feed_vel

    def calculate_positions(self):
        self.position = 0
        self.position_l = 0
        self.encoder_position = 0
        self.encoder_position_l = 0
        self.set_position = 0
        self.encoder_set_position = 0