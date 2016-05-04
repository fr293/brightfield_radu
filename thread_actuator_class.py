import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadActuator(QThread):
    def __init__(self,UI,axis_list,serial_act):
        super(ThreadActuator, self).__init__()
        self.UI = UI
        self.axis_list = axis_list
        self.serial = serial_act
        self.axis_dict = {}
        for axis in axis_list:
            self.axis_dict[axis.axis_address] = axis

    def run(self):
        initFlag = False
        rx_last = ''
        while True:
            #Get tx from arduino
            rx = self.serial.readline()
            #Check it's new
            if rx_last != rx:
                cmd_address = 0
                rx_last = rx
                if rx[0:11] == 'Initialised':
                    initFlag = True
            if initFlag == True:
                #Get axis address
                if rx[0:2].isdigit():
                    cmd_address = int(rx[0:2])
                if cmd_address in self.axis_dict:
                    #echo rx
                    self.axis_dict[cmd_address].textbar.setText('rx:'+rx)
                    print(rx)
                    #Check if encoder position
                    if rx[2] == '+' or rx[2] == '-':
                        self.axis_dict[cmd_address].update_encoder(int(rx[2:]))
                    #Check if home/end stop
                    elif rx[2:6] == 'home':
                        self.axis_dict[cmd_address].home_status = 2
                        print rx[2:6]
                        print "home"
                    elif rx[2:5] == 'end':
                        self.axis_dict[cmd_address].end_status = 2
                        print "end"
                else:
                    #echo rx
                    self.UI.act_textbar.setText('rx:'+rx)
                    print(rx)

            for _axis in self.axis_list:
                if _axis.move_status == 1:
                    if _axis.move_type == 'jog+':
                        buf = '{0:02}JG+{1}\n'.format(_axis.axis_address,_axis.jog_speed)
                        self.serial.write(buf)
                        _axis.textbar.setText('tx:'+buf)
                    elif _axis.move_type == 'jog-':
                        buf = '{0:02}JG-{1}\n'.format(_axis.axis_address,_axis.jog_speed)
                        self.serial.write(buf)
                        _axis.textbar.setText('tx:'+buf)
                    _axis.move_status = 2
                elif _axis.move_status == 3:
                    if _axis.move_type[0:3] == 'jog':
                        buf = '{0:02}JG0\n'.format(_axis.axis_address)
                        self.serial.write(buf)
                        _axis.textbar.setText('tx:'+buf)
                    _axis.move_status = 1


