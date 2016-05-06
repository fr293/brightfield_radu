import time
import numpy as np

from PySide.QtCore import *
from PySide.QtGui import *

from spin_box_widget_class import *
from button_widget_class import *

class Axis(QObject):
    def __init__(self,axis_name,axis_address):
        super(Axis,self).__init__()

        self.axis_name = axis_name
        self.axis_address = axis_address
        self.encoder_resolution = 0.05101E-3 #mm
        self.encoder_set_position_threshold = 1
        self.jog_speed = 100

        #0 ready
        #1 action start
        #2 action in progress
        #3 action stop
        self.move_status = 0
        #0 ready
        #1 move to home
        #2 feeding home
        #3 home triggered, feeding out
        self.home_status = 0
        self.end_status = 0
        self.pos_type = 'rel'
        self.move_type = ''
        self.feed_vel = 0

        self.position = 0
        self.position_l = 0
        self.encoder_position = 0
        self.encoder_position_l = 0
        self.set_position = 0
        self.encoder_set_position = [0,0,0]
        self.lock_encoder_position = 0

        self.kP = 8
        self.kI = 0.7
        self.kD = 0
        self.error = 0
        self.last_error = 0
        self.integral = 0
        self.derivative = 0
        self.velocity = 0
        self.last_pid_time = 0
        self.integral_threshold = 50
        self.drive_scale_factor = 0.04
        self.pid_motor_speed = 0


        self.value = ValueDisplayWidget(['Position','mm'],[7,4])
        self.abs_value = ValueDisplayWidget(['Abs','mm'],[7,4])
        self.sbox = SpinBoxWidget(['Set Position','mm'],0,[0,0.005,50],[7,4],self.set_position_changed,False)
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

        self.rxbar = QLineEdit()
        self.rxbar.setReadOnly(True)
        self.txbar = QLineEdit()
        self.txbar.setReadOnly(True)

        self.vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.value)
        hbox.addStretch(1)
        hbox.addWidget(self.abs_value)
        self.vbox.addLayout(hbox)
        self.vbox.addWidget(self.tab)
        self.vbox.addWidget(self.rxbar)
        self.vbox.addWidget(self.txbar)
        self.widget = QWidget()
        self.widget.setLayout(self.vbox)

    def set_position_changed(self,value):
        print(self.axis_name + ': set position changed' + str(value))
        self.set_position = value

    def absrel_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.pos_type = 'abs'
            print(self.axis_name + ': move type abs')
        else:
            self.pos_type = 'rel'
            print(self.axis_name + ': move type rel')

    def start_toggle(self,toggle_flag):
        self.move_type = 'pos'
        if toggle_flag == True:
            self.update_set_positions()
            self.move_status = 1
            print(self.axis_name + ': start movement')
        else:
            self.move_status = 4
            print(self.axis_name + ': stop movement')

    def lock_toggle(self,toggle_flag):
        if toggle_flag == True:
            print(self.axis_name + ': lock')
        else:
            print(self.axis_name + ': unlock')

    def jogp_toggle(self,toggle_flag):
        self.move_type = 'jog+'
        if toggle_flag == True:
            self.move_status = 1
            print(self.axis_name + ': jog+')
        elif toggle_flag == False:
            self.move_status = 4
            print(self.axis_name + ': jog+ stop')

    def jogm_toggle(self,toggle_flag):
        self.move_type = 'jog-'
        if toggle_flag == True:
            self.move_status = 1
            print(self.axis_name + ': jog-')
        else:
            self.move_status = 4

    def zero(self):
        print(self.axis_name + ': zero')

    def home(self):
        self.home_status = 1
        print(self.axis_name + ': home')

    def feed_toggle(self,toggle_flag):
        print(self.axis_name + ': feed' + str(self.feed_vel))

    def feed_vel_changed(self,feed_vel):
        self.feed_vel = feed_vel

    def update_handle(self,encoder_position):
        self.encoder_position_l = self.encoder_position
        self.encoder_position = encoder_position
        self.position = self.encoder_position*self.encoder_resolution
        self.position_l = self.encoder_position_l*self.encoder_resolution
        self.value.set_value(self.position)

    #def update_handle(self):

        #self.value.set_value(self.position)

    def update_set_positions(self):
        if self.pos_type == 'rel':
            self.encoder_set_position[0] = int((self.position+self.set_position)/self.encoder_resolution)
            self.encoder_set_position[1] = self.encoder_set_position[0]-self.encoder_set_position_threshold
            self.encoder_set_position[2] = self.encoder_set_position[0]+self.encoder_set_position_threshold
        elif self.pos_type == 'abs':
            self.encoder_set_position[0] = int(self.set_position/self.encoder_resolution)
            self.encoder_set_position[1] = self.encoder_set_position[0]-self.encoder_set_position_threshold
            self.encoder_set_position[2] = self.encoder_set_position[0]+self.encoder_set_position_threshold
        print 'encoder set pos{0},{1},{2}'.format(self.encoder_set_position[0],self.encoder_set_position[1],self.encoder_set_position[2])


    def pid(self,dt):
        self.error = self.encoder_set_position[0] - self.encoder_position
        self.last_error = self.error
        if abs(self.error) < self.integral_threshold:
            self.integral += self.error
        derivative = (self.error-self.last_error)/dt
        drive = self.error*self.kP + self.integral*self.kI

        if drive*self.drive_scale_factor > 255:
            motor_speed = 255
        elif drive*self.drive_scale_factor < -255:
            motor_speed = -255
        else:
            motor_speed = int(drive*self.drive_scale_factor)
        print '{3}error: {0} int: {1} drive: {2}'.format(self.error,self.integral,drive,self.encoder_position)

        self.pid_motor_speed = motor_speed
        # return motor_speed

    def check_move_done(self):
        if self.move_type == 'pos':
            if self.encoder_position>=self.encoder_set_position[1] and self.encoder_position<=self.encoder_set_position[2]:
                if self.move_status == 2:
                    self.move_status = 3
                elif self.move_status == 3:
                    self.move_status = 4
                    self.integral = 0
                    self.start_tbutton.set_toggle(False)
            else:
                if self.move_status == 3:
                    self.move_status = 2