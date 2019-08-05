import random
import time
import serial
import os
import csv
import atexit

from PySide.QtCore import *
from PySide.QtGui import *


class ThreadActuator(QThread):
    rx_tigger = Signal(str)

    def __init__(self, UI, axis_GUI_list):
        super(ThreadActuator, self).__init__()

        self.ser = serial.Serial('COM4', 115200, timeout=0.05)
        atexit.register(self.ser.close)

        self.UI = UI
        self.axis_GUI_list = axis_GUI_list
        self.axis_dict = {}
        self.axis_GUI_dict = {}
        self.axis_list = []

        for axis_GUI in self.axis_GUI_list:
            axis = Axis(axis_GUI.axis_name, axis_GUI.axis_address)
            self.axis_list.append(axis)

        for axis, axis_GUI, i in zip(self.axis_list, self.axis_GUI_list, range(0, 4)):
            self.axis_dict[axis.axis_address] = self.axis_list[i]
            self.axis_GUI_dict[axis.axis_address] = self.axis_GUI_list[i]

            axis.update_trigger.connect(axis_GUI.update_handle)
            axis.rx_trigger.connect(axis_GUI.rx_handle)
            axis.tx_trigger.connect(axis_GUI.tx_handle)
            axis.start_tbutton_trigger.connect(axis_GUI.start_tbutton.set_toggle)

            axis_GUI.absrel_trigger.connect(axis.absrel_toggle)
            axis_GUI.start_trigger.connect(axis.start_toggle)
            axis_GUI.home_trigger.connect(axis.home)
            axis_GUI.zero_trigger.connect(axis.zero)
            axis_GUI.lock_trigger.connect(axis.lock_toggle)
            axis_GUI.set_position_trigger.connect(axis.set_position_changed)
            axis_GUI.jogp_trigger.connect(axis.jogp_toggle)
            axis_GUI.jogm_trigger.connect(axis.jogm_toggle)
            axis_GUI.feed_velocity_trigger.connect(axis.feed_velocity_changed)
            axis_GUI.feed_trigger.connect(axis.feed_toggle)

        self.rx_tigger.connect(UI.act_textbar.setText)

        self.last_tx_time = 0
        self.exit_flag = False

    def run(self):
        # Load saved positions
        self.save_positions('load')

        init_flag = False
        rx_last = ''

        # Main Loop
        while not self.exit_flag:
            # Get tx from arduino
            rx = self.ser.readline()
            # print(self.ser.inWaiting())
            # time.sleep(0.005)
            if rx_last != rx:
                rx_last = rx
                if rx[0:11] == 'Initialised':
                    init_flag = True

            # Check Arduino is initialised
            if init_flag:
                # Get axis address
                if rx[0:2].isdigit():
                    cmd_address = int(rx[0:2])
                    # Check axis address is valid
                    if cmd_address in self.axis_dict:
                        # Print rx in axis text bar
                        dt = 1000 * (time.clock() - self.axis_dict[cmd_address].last_rx_time)
                        self.axis_dict[cmd_address].last_rx_time = time.clock()
                        self.axis_dict[cmd_address].rx_trigger.emit(rx + ' dt: {0:4.1f}'.format(dt))
                        # Check if rx is encoder position
                        if rx[2] == '+' or rx[2] == '-':
                            self.axis_dict[cmd_address].update_positions(int(rx[2:]), time.clock())
                        # Check if rx is home/end stop
                        elif rx[2:4] == 'HO':
                            print 'still homing'
                        # elif rx[2:5] == 'EN':
                        elif rx[2:4] == 'HD':
                            self.axis_dict[cmd_address].home_status = 0
                            print 'finished homing'
                # If rx does not contain axis address
                else:
                    # Print rx in text bar
                    self.rx_tigger.emit('rx:' + rx)

                # Axis movement
                for _axis in self.axis_list:
                    # Command to be transmitted
                    cmd = ''
                    # Start movement
                    if _axis.move_status == 1:
                        if _axis.move_type == 'jog+':
                            cmd = self.jog(_axis.axis_address, _axis.jog_speed)
                        elif _axis.move_type == 'jog-':
                            cmd = self.jog(_axis.axis_address, -_axis.jog_speed)
                        elif _axis.move_type == 'pos':
                            cmd = self.jog(_axis.axis_address, _axis.pid(time.clock()))
                        elif _axis.move_type == 'feed':
                            cmd = self.jog(_axis.axis_address, _axis.cvel())
                        _axis.move_status = 2

                    # Continue movement
                    elif _axis.move_status == 2:
                        if _axis.move_type == 'pos':
                            if _axis.position_update_flag:
                                cmd = self.jog(_axis.axis_address, _axis.pid(time.clock()))
                                _axis.position_update_flag = False
                                _axis.check_move_done()
                        elif _axis.move_type == 'feed':
                            if _axis.position_update_flag:
                                cmd = self.jog(_axis.axis_address, _axis.cvel())
                                _axis.position_update_flag = False

                    # Check movement actually done
                    elif _axis.move_status == 3:
                        if _axis.position_update_flag:
                            _axis.check_move_done()
                    # Stop movement
                    elif _axis.move_status == 4:
                        if _axis.move_type[0:3] == 'jog':
                            cmd = self.jog(_axis.axis_address
                                           , 0)
                        elif _axis.move_type == 'pos':
                            cmd = self.jog(_axis.axis_address, 0)
                            print 'position reached'
                        elif _axis.move_type == 'feed':
                            cmd = self.jog(_axis.axis_address, 0)
                        _axis.move_status = 0

                    # Start homing sequence
                    if _axis.home_status == 1:
                        cmd = self.jog(_axis.axis_address, -100)
                        _axis.home_status = 2

                    if cmd != '':
                        self.ser.write(cmd)
                        dt = 1000 * (time.clock() - self.last_tx_time)
                        self.last_tx_time = time.clock()
                        _axis.tx_trigger.emit(cmd + ' dt: {0:4.1f}'.format(dt))

                    self.save_positions()

    def exit(self):
        self.exit_flag = True

    def estop(self):
        for _axis in self.axis_list:
            cmd = self.jog(_axis.axis_address, 0)
            self.ser.write(cmd)
            _axis.txbar.setText('tx:' + cmd + 'ESTOP')
        self.rx_tigger.emit('ESTOP')

    def jog(self, addr, speed):
        if speed > 0:
            cmd = '{0:02}JG+{1}\n'.format(addr, speed)
        else:
            cmd = '{0:02}JG{1}\n'.format(addr, speed)
        return cmd

    def save_positions(self, mode='save'):
        # file name
        f_path = os.getcwd() + '\\save\\'
        f_name = 'actuator_positions'
        f_path = f_path + f_name + '.csv'
        # open file
        with open(f_path, 'r+') as f:
            if mode == 'load':
                reader = csv.reader(f)
                positions = []
                for position in reader.next():
                    positions.append(position)
                for axis, i in zip(self.axis_list, range(len(self.axis_list))):
                    axis.position_offset = -float(positions[i])
            elif mode == 'save':
                writer = csv.writer(f)
                positions = []
                for axis in self.axis_list:
                    positions.append('{0:7.4f}'.format(axis.position))
                writer.writerow(positions)


class Axis(QObject):
    update_trigger = Signal(float, float)
    rx_trigger = Signal(str)
    tx_trigger = Signal(str)
    start_tbutton_trigger = Signal(bool)

    def __init__(self, axis_name, axis_address):

        super(Axis, self).__init__()

        self.last_rx_time = 0

        self.axis_name = axis_name
        self.axis_address = axis_address
        self.encoder_resolution = 0.05101E-3  # mm
        self.encoder_set_position_threshold = 1
        self.jog_speed = 100

        # 0 ready
        # 1 action start
        # 2 action in progress
        # 3 action stop
        self.move_status = 0
        # 0 ready
        # 1 move to home
        # 2 feeding home
        # 3 home triggered, feeding out
        self.home_status = 0
        self.end_status = 0
        self.pos_type = 'rel'
        self.move_type = ''
        self.feed_velocity = 0

        self.position = 0
        self.position_l = 0
        self.encoder_position = 0
        self.encoder_position_l = 0
        self.set_position = 0
        self.encoder_set_position = [0, 0, 0]
        self.lock_encoder_position = 0
        self.position_update_flag = False
        self.position_update_time = 0
        self.position_offset = 0

        self.kP = 12
        self.kI = 1
        self.kD = 1700
        self.error = 0
        self.last_error = 0
        self.integral = 0
        self.derivative = 0
        self.velocity = 0
        self.last_pid_time = 0
        self.integral_threshold = 100
        self.drive_scale_factor = 0.01
        self.motor_speed = 0

    def set_position_changed(self, value):
        print(self.axis_name + ': set position changed' + str(value))
        self.set_position = value

    def absrel_toggle(self, toggle_flag):
        if toggle_flag:
            self.pos_type = 'abs'
            print(self.axis_name + ': move type abs')
        else:
            self.pos_type = 'rel'
            print(self.axis_name + ': move type rel')

    def start_toggle(self, toggle_flag):
        self.move_type = 'pos'
        if toggle_flag == True:
            self.update_set_positions()
            self.move_status = 1
            print(self.axis_name + ': start movement')
        else:
            self.move_status = 4
            print(self.axis_name + ': stop movement')

    def lock_toggle(self, toggle_flag):
        if toggle_flag == True:
            print(self.axis_name + ': lock')
        else:
            print(self.axis_name + ': unlock')

    def jogp_toggle(self, toggle_flag):
        self.move_type = 'jog+'
        if toggle_flag == True:
            self.move_status = 1
            print(self.axis_name + ': jog+')
        elif toggle_flag == False:
            self.move_status = 4
            print(self.axis_name + ': jog+ stop')

    def jogm_toggle(self, toggle_flag):
        self.move_type = 'jog-'
        if toggle_flag == True:
            self.move_status = 1
            print(self.axis_name + ': jog-')
        else:
            self.move_status = 4

    def zero(self):
        self.position_offset = self.position
        print(self.axis_name + ': zero')

    def home(self):
        self.home_status = 1
        print(self.axis_name + ': home')

    def feed_toggle(self, toggle_flag):
        self.move_type = 'feed'
        self.motor_speed = 0
        if toggle_flag == True:
            self.move_status = 1
            print(self.axis_name + ': feed' + str(self.feed_velocity))
        elif toggle_flag == False:
            self.move_status = 4
            print(self.axis_name + ': feed stop')

    def feed_velocity_changed(self, feed_velocity):
        self.feed_velocity = feed_velocity

    def update_positions(self, encoder_position, t=0):
        dt = t - self.position_update_time
        self.position_update_time = t

        # update encoder positions and positions in mm
        self.encoder_position_l = self.encoder_position
        self.encoder_position = encoder_position
        self.position_l = self.position
        self.position = self.encoder_position * self.encoder_resolution - self.position_offset

        # calculate velocity in mm/s
        if dt != 0:
            self.velocity = (self.position - self.position_l) / dt
        else:
            self.velocity = 0

        # set position update flag (for pid loop)
        self.position_update_flag = True
        # change display in GUI
        self.update_trigger.emit(self.position, self.velocity)

    def update_set_positions(self):
        if self.pos_type == 'rel':
            self.encoder_set_position[0] = int(
                (self.position + self.position_offset + self.set_position) / self.encoder_resolution)
            self.encoder_set_position[1] = self.encoder_set_position[0] - self.encoder_set_position_threshold
            self.encoder_set_position[2] = self.encoder_set_position[0] + self.encoder_set_position_threshold
        elif self.pos_type == 'abs':
            self.encoder_set_position[0] = int((self.set_position + self.position_offset) / self.encoder_resolution)
            self.encoder_set_position[1] = self.encoder_set_position[0] - self.encoder_set_position_threshold
            self.encoder_set_position[2] = self.encoder_set_position[0] + self.encoder_set_position_threshold
        print 'encoder set pos{0},{1},{2}'.format(self.encoder_set_position[0], self.encoder_set_position[1],
                                                  self.encoder_set_position[2])

    def pid(self, t):
        dt = 1000 * (t - self.last_pid_time)
        self.last_pid_time = t

        self.last_error = self.error
        self.error = self.encoder_set_position[0] - self.encoder_position

        if abs(self.error) < self.integral_threshold:
            self.integral += self.error
        derivative = (self.error - self.last_error) / dt
        drive = self.error * self.kP + self.integral * self.kI + derivative * self.kD

        if drive * self.drive_scale_factor > 255:
            motor_speed = 255
        elif drive * self.drive_scale_factor < -255:
            motor_speed = -255
        else:
            motor_speed = int(drive * self.drive_scale_factor)
        print 'encoder pos: {4} error: {0} int: {1} diff: {2} drive: {3} dt: {5}'.format(self.error, self.integral,
                                                                                         derivative, drive,
                                                                                         self.encoder_position, dt)

        self.motor_speed = motor_speed
        return motor_speed

    def cvel(self):
        if self.velocity < self.feed_velocity and self.motor_speed <= 255:
            self.motor_speed += 15 * (self.feed_velocity - self.velocity)
        elif self.velocity > self.feed_velocity and self.motor_speed >= -255:
            self.motor_speed += 15 * (self.feed_velocity - self.velocity)

        return int(self.motor_speed)

    def check_move_done(self):
        if self.move_type == 'pos':
            if self.encoder_position >= self.encoder_set_position[1] and self.encoder_position <= \
                    self.encoder_set_position[2]:
                if self.move_status == 2:
                    self.move_status = 3
                elif self.move_status == 3:
                    self.move_status = 4
                    self.integral = 0
                    self.start_tbutton_trigger.emit(False)
            else:
                if self.move_status == 3:
                    self.move_status = 2


class ThreadActuatorZ(QThread):
    rx_trigger = Signal(str)

    def __init__(self, UI, axis_GUI):
        super(ThreadActuatorZ, self).__init__()
        self.ser = serial.Serial('COM10', 57600, timeout=1)
        self.ser.setXonXoff(True)
        atexit.register(self.ser.close)
        print "Z Actuator Serial Open"

        self.axis = Axis('z', 0)

        self.axis.update_trigger.connect(axis_GUI.update_handle)
        self.axis.rx_trigger.connect(axis_GUI.rx_handle)
        self.axis.tx_trigger.connect(axis_GUI.tx_handle)
        self.axis.start_tbutton_trigger.connect(axis_GUI.start_tbutton.set_toggle)

        axis_GUI.absrel_trigger.connect(self.axis.absrel_toggle)
        axis_GUI.start_trigger.connect(self.axis.start_toggle)
        axis_GUI.home_trigger.connect(self.axis.home)
        # self.axis_GUI.zero_trigger.connect(axis.zero)
        # self.axis_GUI.lock_trigger.connect(axis.lock_toggle)
        axis_GUI.set_position_trigger.connect(self.axis.set_position_changed)
        axis_GUI.jogp_trigger.connect(self.axis.jogp_toggle)
        axis_GUI.jogm_trigger.connect(self.axis.jogm_toggle)
        # self.axis_GUI.feed_velocity_trigger.connect(axis.feed_velocity_changed)
        # self.axis_GUI.feed_trigger.connect(axis.feed_toggle)

        self.exit_flag = False

        self.track = False
        self.focus_act_1 = 1.0
        self.focus_act_2 = 1.0
        limits_f1 = False
        limits_f2 = False

    def run(self):
        while not self.exit_flag:
            time.sleep(0.02)
            out_error = self.do_and_reply('1TS\r\n')  # get error code [0:3]  and status[4:5]
            # self.axis.rx_trigger.emit(out_error)
            # if out_error[:-2] != '0000':     # each TS call, erase the previous error
            #     self.axis.rx_tigger.emit(out_error[:-2])

            status = out_error[4:]  # select the status of actuator
            if status == '32' or status == '33' or status == '34' or status == '35':
                out_status = 'READY'
            elif status == '0A' or status == '0B' or status == '0C' or status == '0D' or status == '0E' or status == '0F' or status == '10' or status == '11':
                out_status = 'NOT REF.'
            elif status == '1E' or status == '1F':
                out_status = 'HOMING'
            elif status == '28':
                out_status = 'MOVING'
            elif status == '3C' or status == '3D' or status == '3E':
                out_status = 'DISABLE'
            elif status == '46' or status == '47':
                out_status = 'JOGGING'
            elif status == '14':
                out_status = 'CONFIG.'
            else:
                out_status = 'Other state'
            # self.emit(SIGNAL("status_send(QString)"),out_status)  # send to main thread a signal with a parameter
            # status of actuator
            # print 'Z Act Status:' + out_status
            self.axis.rx_trigger.emit(out_status)

            out_z_coord = self.do_and_reply('1TP?\r\n')
            self.axis.update_positions(float(out_z_coord) / self.axis.encoder_resolution, time.clock())

            # Start movement
            if self.axis.move_status == 1:
                if self.axis.move_type == 'pos':
                    if self.axis.pos_type == 'abs':
                        self.do_and_nowait('1PA{0}\r\n'.format(self.axis.set_position))
                    elif self.axis.pos_type == 'rel':
                        self.do_and_nowait('1PR{0}\r\n'.format(self.axis.set_position))
                    self.axis.start_tbutton_trigger.emit(False)
                    self.axis.move_status = 0
                elif self.axis.move_type == 'jog+':
                    self.do_and_nowait('1PR0.1\r\n')
                elif self.axis.move_type == 'jog-':
                    self.do_and_nowait('1PR-0.1\r\n')

            if self.axis.move_status == 4:
                self.do_and_nowait('1ST\r\n')

            if self.axis.home_status == 1:
                self.do_and_nowait('1OR\r\n')
                self.axis.home_status = 0

            # if self.absolute == True:                    # Change absolute position if it's required from GUI
            #     abs_txt = str(self.val_abs)             # convert to string the value of z coordinate
            #     self.do_and_nowait('1PA'+abs_txt+'\r\n')
            #     self.absolute = False                   # next iteration does not - produce a movement
            #                                             # eliminates unnecessary serial communication
            #
            #
            # if self.relative == True:                    # Change relative position if it's required from GUI
            #     rel_txt = str(self.val_rel)             # convert to string the relative value
            #     if self.sign=='p':
            #         self.do_and_nowait('1PR'+rel_txt+'\r\n')
            #         self.relative = False
            #     elif self.sign =='n':                   # a '-' is added to the relative value
            #         self.do_and_nowait('1PR-'+rel_txt+'\r\n')
            #         self.relative = False
            #     else:
            #         print 'error'
            #
            #
            # if self.reset_act ==True:                  # Change the status from Non Referenced to Ready
            #     self.do_and_nowait('1OR\r\n')          # by passing through HOMING
            #     self.reset_act = False

            '''limits_f1 = self.focus_act_1 > 0.95  and self.focus_act_1 < 1.5
            limits_f2 = self.focus_act_2 > 0.84  and self.focus_act_2 < 1.37

            if self.track ==True:
                if limits_f1 and limits_f2:
                    z_average = bead_z_evaluate(self.focus_act_1, self.focus_act_2)
                    bool_move, rel_move = follow_bead(z_average )
                    if bool_move ==True:
                        mutex.lock()
                        rel_txt = str(rel_move)
                        self.do_and_nowait('1PR'+rel_txt+'\r\n')
                        mutex.unlock()
                    #self.emit(SIGNAL("adj_manual_z_for_tracking()"))
                else:
                    self.emit(SIGNAL("adj_manual_z_for_tracking()"))'''

            if self.track == True:
                focus_ratio = self.focus_act_1 / self.focus_act_2
                bool_move, rel_move = self.follow_bead_new(focus_ratio)
                if bool_move == True:
                    rel_txt = str(rel_move)
                    # print '1PR'+rel_txt+'\r\n'
                    self.do_and_nowait('1PR' + rel_txt + '\r\n')

        # The thread is not started with its initialization. From main thread (GUI), method start must be called.
        # Everything contained in method "run" will be executed only once. To send serial commands periodically, a
        # while loop must be used. Parameters from main thread to "ThActuator" thread are sent by accessing variables
        # belonging to ThActuator thread (ex: self.absolute).
        # Values from secondary thread to main thread are passed using signals and slots. Custom signals, similar to
        # checkedBox, valueChanged , etc ..., are created by us (e.g. z_coord_send(QString)). These signals can
        # generate a change in the GUI. The signal can be transmitted without any parameter.
        # To avoid errors, we instruct the GUI thread to first wait and finish the ThActuator thread before exiting
        # itself.

        print "Done with Actuator thread"  # to be converted into a comment

    def do_and_reply(self, to_do):  # method - to get answer from controller
        self.ser.write(to_do)  # write to serial a command
        # self.axis.tx_trigger.emit(to_do)
        reply_1 = self.ser.readline()  # read from serial the answer
        reply_2 = reply_1[3:-2]  # remove command and \r\n from the answer
        # self.axis.rx_trigger.emit(reply_2)
        return reply_2

    def do_and_nowait(self, to_do):  # method - no answer expected from actuator
        self.ser.write(to_do)
        self.axis.tx_trigger.emit(to_do)
        print('spog')
        return

    def track_toggle(self, toggle_flag):
        if toggle_flag == True:
            self.track = True
            print('Z axis start tracking')
        else:
            self.track = False
            print('Z axis stop tracking')

    def update_focus(self, f1, f2):
        self.focus_act_1 = f1
        self.focus_act_2 = f2

    def follow_bead_new(self, f_1_over_f_2):
        # f_11 = 1.15    # intial - default
        # f_22 = 1.05    # intial - default

        f_11 = 1.15
        f_22 = 1.05

        x11 = 7.60268
        x22 = 7.64864
        y11 = 1.38048
        y22 = 0.71469

        slope = (y11 - y22) / (x11 - x22)
        inters = y11 - slope * x11

        z_actual = (f_1_over_f_2 - inters) / slope
        z_desired = (1.1 - inters) / slope

        # x_half = (x_1+x_2)/2

        if f_1_over_f_2 > f_11 or f_1_over_f_2 < f_22:
            go_act = True
            delta_z_for_limit = z_actual - z_desired
            logic_test = delta_z_for_limit > 0
            if abs(delta_z_for_limit) > 0.005:
                if logic_test:
                    rel_z_go = -0.005
                else:
                    rel_z_go = 0.005
            else:
                rel_z_go = -(z_actual - z_desired)
        else:
            go_act = False
            rel_z_go = 0.0

        return go_act, rel_z_go
