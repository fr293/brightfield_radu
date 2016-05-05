import random
import time
import serial

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadActuator(QThread):
    def __init__(self,UI,axis_list):
        super(ThreadActuator, self).__init__()
        self.ser = serial.Serial('COM8', 115200,timeout=0.05)
        self.UI = UI
        self.axis_list = axis_list
        self.axis_dict = {}
        for axis in axis_list:
            self.axis_dict[axis.axis_address] = axis

    def run(self):
        mutex = QMutex()
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
                        mutex.lock()
                        self.axis_dict[cmd_address].rxbar.setText('rx:'+rx)
                        mutex.unlock()
                        #Check if rx is encoder position
                        if rx[2] == '+' or rx[2] == '-':
                            mutex.lock()
                            self.axis_dict[cmd_address].update_encoder(int(rx[2:]))
                            mutex.unlock()
                        #Check if rx is home/end stop
                        elif rx[2:4] == 'HO':
                            self.axis_dict[cmd_address].home_status = 3
                            print 'still homing'
                        elif rx[2:5] == 'EN':
                            self.axis_dict[cmd_address].end_status = 3
                        elif rx[2:4] == 'HD':
                            self.axis_dict[cmd_address].home_status = 0
                            print 'finished homing'
                #If rx does not contain axis address
                else:
                    #Print rx in text bar
                    self.UI.act_textbar.setText('rx:'+rx)

                #Axis movement
                for _axis in self.axis_list:
                    dt = 1000*(time.clock - _axis.last_pid_time)
                    _axis.last_pid_time = time.clock()
                    cmd = ''
                    if _axis.move_status == 1:
                        if _axis.move_type == 'jog+':
                            cmd = self.jog(_axis.axis_address,_axis.jog_speed)
                        elif _axis.move_type == 'jog-':
                            cmd = self.jog(_axis.axis_address,-_axis.jog_speed)
                        if _axis.move_type == 'pos':
                            cmd = self.jog(_axis.axis_address,_axis.pid(dt))
                        _axis.move_status = 2
                    elif _axis.move_status == 3:
                        if _axis.move_type[0:3] == 'jog':
                            cmd = self.jog(_axis.axis_address,0)
                        _axis.move_status = 0
                    #Start homing sequence
                    if _axis.home_status == 1:
                        cmd = '{0:02}JG-{1}\n'.format(_axis.axis_address,50)
                        _axis.home_status = 2

                    if cmd != '':
                        self.ser.write(cmd)
                        _axis.txbar.setText('tx:'+cmd)



    def do_read(self):
        line = self.ser.readline()
        return line

    def jog(self,addr,speed):
        if speed > 0:
            cmd = '{0:02}JG+{1}\n'.format(addr,speed)
        else:
            cmd = '{0:02}JG-{1}\n'.format(addr,speed)
        return cmd
