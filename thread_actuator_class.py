import random
import time
import serial

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadActuator(QThread):
    update_trigger = Signal(int,int)
    pid_trigger = Signal(int,float)
    check_trigger = Signal(int)
    def __init__(self,UI,axis_list):
        super(ThreadActuator, self).__init__()
        self.ser = serial.Serial('COM8', 57600,timeout=0.05)
        self.UI = UI
        self.axis_list = axis_list
        self.axis_dict = {}
        for axis in axis_list:
            self.axis_dict[axis.axis_address] = axis
            self.update_trigger.connect(axis.update_handle)
            self.pid_trigger.connect(axis.pid)
            self.check_trigger.connect(axis.check_move_done)

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
                        mutex.lock()
                        self.axis_dict[cmd_address].rxbar.setText('rx:'+rx)
                        mutex.unlock()
                        #Check if rx is encoder position
                        if rx[2] == '+' or rx[2] == '-':
                            #mutex.lock()
                            #self.axis_dict[cmd_address].update_encoder(int(rx[2:]))
                            #mutex.unlock()
                            self.update_trigger.emit(cmd_address,int(rx[2:]))
                        #Check if rx is home/end stop
                        elif rx[2:4] == 'HO':
                            print 'still homing'
                        #elif rx[2:5] == 'EN':
                        elif rx[2:4] == 'HD':
                            mutex.lock()
                            self.axis_dict[cmd_address].home_status = 0
                            mutex.unlock()
                            print 'finished homing'
                #If rx does not contain axis address
                else:
                    #Print rx in text bar
                    mutex.lock()
                    self.UI.act_textbar.setText('rx:'+rx)
                    mutex.unlock()

                #Axis movement
                for _axis in self.axis_list:
                    #Loop timer
                    mutex.lock()
                    dt = 1000*(time.clock() - _axis.last_pid_time)
                    _axis.last_pid_time = time.clock()
                    mutex.unlock()
                    #Command to be transmitted
                    cmd = ''
                    #Start movement
                    if _axis.move_status == 1:
                        if _axis.move_type == 'jog+':
                            cmd = self.jog(_axis.axis_address,_axis.jog_speed)
                        elif _axis.move_type == 'jog-':
                            cmd = self.jog(_axis.axis_address,-_axis.jog_speed)
                        elif _axis.move_type == 'pos':
                            self.pid_trigger.emit(_axis.axis_address,dt)
                            cmd = self.jog(_axis.axis_address,_axis.pid_motor_speed)
                        mutex.lock()
                        _axis.move_status = 2
                        mutex.unlock()

                    #Continue movement
                    elif _axis.move_status == 2:
                        if _axis.move_type == 'pos':
                            self.pid_trigger.emit(_axis.axis_address,dt)
                            cmd = self.jog(_axis.axis_address,_axis.pid_motor_speed)
                        self.check_trigger.emit(_axis.axis_address)

                    #Check movement actually done
                    elif _axis.move_status == 3:
                        self.check_trigger.emit(_axis.axis_address)
                    #Stop movement
                    elif _axis.move_status == 4:
                        if _axis.move_type[0:3] == 'jog':
                            cmd = self.jog(_axis.axis_address,0)
                        elif _axis.move_type == 'pos':
                            cmd = self.jog(_axis.axis_address,0)
                            print 'position reached'
                        mutex.lock()
                        _axis.move_status = 0
                        mutex.unlock()

                    #Start homing sequence
                    if _axis.home_status == 1:
                        cmd = '{0:02}JG-{1}\n'.format(_axis.axis_address,100)
                        mutex.lock()
                        _axis.home_status = 2
                        mutex.unlock()

                    if cmd != '':
                        self.ser.write(cmd)
                        _axis.txbar.setText('tx:'+cmd)



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
