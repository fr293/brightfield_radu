import random
import time
import serial

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadActuator(QThread):

    def __init__(self,UI,axis_GUI_list):
        super(ThreadActuator, self).__init__()
        self.ser = serial.Serial('COM8', 115200,timeout=0.05)
        self.UI = UI
        self.axis_GUI_list = axis_GUI_list
        self.axis_dict = {}
        self.axis_GUI_dict = {}
        self.axis_list = []

        for axis_GUI in self.axis_GUI_list:
            axis = Axis(axis_GUI.axis_name,axis_GUI.axis_address)
            self.axis_list.append(axis)

        for axis,axis_GUI,i in zip(self.axis_list,self.axis_GUI_list,range(0,4)):
            self.axis_dict[axis.axis_address] = self.axis_list[i]
            self.axis_GUI_dict[axis.axis_address] = self.axis_GUI_list[i]

            axis.update_trigger.connect(axis_GUI.update_handle)
            axis.rx_trigger.connect(axis_GUI.rx_handle)
            axis.tx_trigger.connect(axis_GUI.tx_handle)
            axis.start_tbutton_trigger.connect(axis_GUI.start_tbutton.set_toggle)

            axis_GUI.absrel_trigger.connect(axis.absrel_toggle)
            axis_GUI.start_trigger.connect(axis.start_toggle)
            axis_GUI.home_trigger.connect(axis.home)
            axis_GUI.lock_trigger.connect(axis.lock_toggle)
            axis_GUI.set_position_trigger.connect(axis.set_position_changed)
            axis_GUI.jogp_trigger.connect(axis.jogp_toggle)
            axis_GUI.jogm_trigger.connect(axis.jogm_toggle)
            axis_GUI.feed_vel_trigger.connect(axis.feed_vel_changed)
            axis_GUI.feed_trigger.connect(axis.feed_toggle)

        self.last_tx_time = 0

    def run(self):
        mutex = self.UI.mutex
        #mutex = QMutex()
        initFlag = False
        rx_last = ''
        while True:
            #Get tx from arduino
            rx = self.ser.readline()
            time.sleep(0.005)
            cmd_address = 0
            if rx_last != rx:
                rx_last = rx
                if rx[0:11] == 'Initialised':
                    initFlag = True

            #Check Arduino is initialised
            if initFlag:
                #Get axis address
                if rx[0:2].isdigit():
                    cmd_address = int(rx[0:2])
                    #Check axis address is valid
                    if cmd_address in self.axis_dict:
                        #Print rx in axis text bar
                        dt = 1000*(time.clock() - self.axis_dict[cmd_address].last_rx_time)
                        self.axis_dict[cmd_address].last_rx_time = time.clock()
                        self.axis_dict[cmd_address].rx_trigger.emit(rx + ' dt: {0}'.format(dt))
                        #Check if rx is encoder position
                        if rx[2] == '+' or rx[2] == '-':
                            self.axis_dict[cmd_address].update_positions(int(rx[2:]))
                        #Check if rx is home/end stop
                        elif rx[2:4] == 'HO':
                            print 'still homing'
                        #elif rx[2:5] == 'EN':
                        elif rx[2:4] == 'HD':
                            self.axis_dict[cmd_address].home_status = 0
                            print 'finished homing'
                #If rx does not contain axis address
                else:
                    #Print rx in text bar
                    mutex.lock()
                    self.UI.act_textbar.setText('rx:'+rx)
                    mutex.unlock()

                #Axis movement
                for _axis in self.axis_list:
                    #Command to be transmitted
                    cmd = ''
                    #Start movement
                    if _axis.move_status == 1:
                        if _axis.move_type == 'jog+':
                            cmd = self.jog(_axis.axis_address,_axis.jog_speed)
                        elif _axis.move_type == 'jog-':
                            cmd = self.jog(_axis.axis_address,-_axis.jog_speed)
                        elif _axis.move_type == 'pos':
                            cmd = self.jog(_axis.axis_address,_axis.pid(time.clock()))
                        _axis.move_status = 2

                    #Continue movement
                    elif _axis.move_status == 2:
                        if _axis.move_type == 'pos':
                            if _axis.position_update_flag:
                                cmd = self.jog(_axis.axis_address,_axis.pid(time.clock()))
                                _axis.position_update_flag = False
                                _axis.check_move_done()

                    #Check movement actually done
                    elif _axis.move_status == 3:
                        if _axis.position_update_flag:
                            _axis.check_move_done()
                    #Stop movement
                    elif _axis.move_status == 4:
                        if _axis.move_type[0:3] == 'jog':
                            cmd = self.jog(_axis.axis_address,0)
                        elif _axis.move_type == 'pos':
                            cmd = self.jog(_axis.axis_address,0)
                            print 'position reached'
                        _axis.move_status = 0

                    #Start homing sequence
                    if _axis.home_status == 1:
                        cmd = '{0:02}JG-{1}\n'.format(_axis.axis_address,100)
                        _axis.home_status = 2

                    if cmd != '':
                        self.ser.write(cmd)
                        dt = 1000*(time.clock() - self.last_tx_time)
                        self.last_tx_time = time.clock()
                        _axis.tx_trigger.emit(cmd + 'dt: {0}'.format(dt))



    def do_read(self):
        line = self.ser.readline()
        return line

    def estop(self):
        for _axis in self.axis_list:
            cmd = self.jog(_axis.axis_address,0)
            self.ser.write(cmd)
            _axis.txbar.setText('ESTOPtx:'+cmd)

    def jog(self,addr,speed):
        if speed > 0:
            cmd = '{0:02}JG+{1}\n'.format(addr,speed)
        else:
            cmd = '{0:02}JG{1}\n'.format(addr,speed)
        return cmd



class Axis(QObject):
    update_trigger = Signal(float)
    rx_trigger = Signal(str)
    tx_trigger = Signal(str)
    start_tbutton_trigger = Signal(bool)
    def __init__(self,axis_name,axis_address):

        super(Axis,self).__init__()

        self.last_rx_time = 0

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
        self.position_update_flag = False

        self.kP = 2.7
        self.kI = 0.08
        self.kD = 0
        self.error = 0
        self.last_error = 0
        self.integral = 0
        self.derivative = 0
        self.velocity = 0
        self.last_pid_time = 0
        self.integral_threshold = 700
        self.drive_scale_factor = 0.01
        self.pid_motor_speed = 0

    def set_position_changed(self,value):
        print(self.axis_name + ': set position changed' + str(value))
        self.set_position = value

    def absrel_toggle(self,toggle_flag):
        if toggle_flag:
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

    def update_positions(self,encoder_position):
        self.encoder_position_l = self.encoder_position
        self.encoder_position = encoder_position
        self.position = self.encoder_position*self.encoder_resolution
        self.position_l = self.encoder_position_l*self.encoder_resolution
        self.position_update_flag = True
        self.update_trigger.emit(self.position)


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


    def pid(self,t):
        dt = 1000*(t-self.last_pid_time)
        self.last_pid_time = t

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
        print 'encoder pos: {3} error: {0} int: {1} drive: {2} dt: {4}'.format(self.error,self.integral,drive,self.encoder_position,dt)

        self.pid_motor_speed = motor_speed
        return motor_speed

    def check_move_done(self):
        if self.move_type == 'pos':
            if self.encoder_position>=self.encoder_set_position[1] and self.encoder_position<=self.encoder_set_position[2]:
                if self.move_status == 2:
                    self.move_status = 3
                elif self.move_status == 3:
                    self.move_status = 4
                    self.integral = 0
                    self.start_tbutton_trigger.emit(False)
            else:
                if self.move_status == 3:
                    self.move_status = 2