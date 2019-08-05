import sys
import cv2
import cv2.cv as cv
import time
import numpy
import numpy as np
import datetime

# from pylab import *
import cv2
import serial
import atexit
import os
import random

from math import *

from PySide import QtGui
from PySide.QtGui import *
from PySide.QtCore import *

import pyqtgraph as pg

# ************************************
# *********** VIDEO config ***********
try:
    from pymba import *
except ImportError as e:
    print e
    print "Is VimbaC.dll found by the runtime?"
    exit()

vimba = Vimba()
vimba.startup()
system = vimba.getSystem()

camera_ids = vimba.getCameraIds()

for cam_id in camera_ids:
    print "Camera found: ", cam_id
# +++++++++++++++++++++++++++++++++++++++

# ************************************
# ******* OPEN SERIAL TRIGGER *******
ser_trig = serial.Serial('COM4', 19200, timeout=1)
atexit.register(ser_trig.close)  # to be sure that serial communication is closed
print "serial trigger open"
# +++++++++++++++++++++++++++++++++++++++


mutex = QMutex()
# ************************************
# ******* OPEN SERIAL ACTUATOR *******
ser = serial.Serial('COM10', 57600, timeout=1)
ser.setXonXoff(True)
atexit.register(ser.close)  # to be sure that serial communication is closed
print "serial open"
# +++++++++++++++++++++++++++++++++++++++


# ************************************
# ******* OPEN SERIAL POWER SUPPLY *******
ser_ps = serial.Serial('COM5', 19200, timeout=0.05)
atexit.register(ser_ps.close)  # to be sure that serial communication is closed
print "serial ps open"
# +++++++++++++++++++++++++++++++++++++++

# ************************************
# ******* OPEN SERIAL 2nd thermometer *******
# ser_2temp =serial.Serial('COM7', 19200,timeout=0.05)
# atexit.register(ser_2temp.close)   # to be sure that serial communication is closed
# print "serial temperature open"
# +++++++++++++++++++++++++++++++++++++++


# ************************************
# ******* OPEN AND GET VIDEO *********
camcapture = vimba.getCamera(camera_ids[0])  # connect first camera by 'id'
camcapture.openCamera()
cam1_exp_time_dec = camcapture.readRegister("F0F0081C")  # address for Shuter
cam1_exp_time_base_no = int('{0:b}'.format(cam1_exp_time_dec)[20:], 2)
cam1_exp_time_ms = cam1_exp_time_base_no * 0.02
# print 'exp ', cam1_exp_time_base_no, cam1_exp_time_ms
# static_write_register = "10000010000000000000"
# cam1_exp_time_base_no_new = 203
# cam1_exp_time_base_no_new_bin = '{0:012b}'.format(cam1_exp_time_base_no_new)
# write_register = hex(int(static_write_register + cam1_exp_time_base_no_new_bin,2))[2:-1]
# print write_register
# time.sleep(0.5)
# camcapture.writeRegister("F0F0081C",write_register)

frame = camcapture.getFrame()
frame.announceFrame()
camcapture.startCapture()
camcapture.runFeatureCommand("AcquisitionStart")
# +++++++++++++++++++++++++++++++++++++++

# ***************************************
# ******* OPEN AND GET 2nd VIDEO *********
camcapture_2 = vimba.getCamera(camera_ids[1])  # connect first camera by 'id'
camcapture_2.openCamera()
cam2_exp_time_dec = camcapture_2.readRegister("F0F0081C")  # address for Shuter
cam2_exp_time_base_no = int('{0:b}'.format(cam2_exp_time_dec)[20:], 2)
cam2_exp_time_ms = cam2_exp_time_base_no * 0.02

frame_2 = camcapture_2.getFrame()
frame_2.announceFrame()
camcapture_2.startCapture()
camcapture_2.runFeatureCommand("AcquisitionStart")


# +++++++++++++++++++++++++++++++++++++++

# atexit.register(vimba.shutdown())    #prevent errors on script finalization

# atexit.register(camcapture.closeCamera())
# atexit.register(camcapture.revokeAllFrames())
# atexit.register(camcapture.endCapture())
# atexit.register(camcapture.runFeatureCommand("AcquisitionStop"))

# atexit.register(camcapture_2.closeCamera())
# atexit.register(camcapture_2.revokeAllFrames())
# atexit.register(camcapture_2.endCapture())
# atexit.register(camcapture_2.runFeatureCommand("AcquisitionStop"))


# *************************************************
# ******* CLASS to convert NumPy to QImageO *******
class NumPyQImage(QtGui.QImage):
    def __init__(self, numpyImg):

        # print type(numpyImg), len(numpyImg.shape), numpyImg.shape

        # if len(numpyImg.shape) !=2:
        #    raise ValueError("it's not 2D array, i.e. Mono8")

        if type(numpyImg) is not None:
            numpyImg = np.require(numpyImg, np.uint8, 'C')  # rearrange to be C style storage
        else:
            numpyImg = np.zeros((100, 100), np.uint8)
            numpyImg[:] = (255)

        h, w = numpyImg.shape

        result = QImage(numpyImg.data, w, h, QImage.Format_Indexed8)
        result.ndarray = numpyImg
        for i in range(256):
            result.setColor(i, QColor(i, i, i).rgb())
        self._imgData = result
        super(NumPyQImage, self).__init__(self._imgData)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# *************************************************
# ******* CLASS - THREAD FOR VIDEO *******
# class ThVideo(QThread):
#    def __init__(self):
#        super(ThVideo, self).__init__()
#        #self.mutex = QMutex()
#
#    def run(self):  # method which runs the thread
#                    # it will be started from main thread
#        self.trigger=False
#        self.done_video = False
#        self.n_frame_2_th=camcapture_2.getImage(5000)
#        while (not self.done_video):
#            time.sleep(0.01)
#            if (self.trigger==True):
#                self.n_frame_2_th=camcapture_2.getImage(5000)
#                #print "the video while"

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# *************************************************
# ******* CLASS - THREAD FOR ACTUATOR *******
class ThActuator(QThread):
    def __init__(self):
        super(ThActuator, self).__init__()
        # self.mutex = QMutex()

    def run(self):  # method which runs the thread
        # it will be started from main thread

        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.done = False  # controls the exit from while loop and
        # termination of the thread
        self.relative = False  # controls the relative movement
        self.val_rel = 0.01  # relative movement value
        self.sign = 'p'  # direction of rel movement

        self.absolute = False  # controls absolute movement
        self.val_abs = 0.01  # absolute movement value

        self.reset_act = False  # controls the reset of the actuator

        self.track = False

        self.focus_act_1 = 1.0
        self.focus_act_2 = 1.0
        limits_f1 = False
        limits_f2 = False
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        while (not self.done):  # loop for getting data from actuator
            time.sleep(0.02)

            mutex.lock()
            out_error = self.do_and_reply('1TS\r\n')  # get error code [0:3]  and status[4:5]
            mutex.unlock()
            self.emit(SIGNAL("error_status_send(QString)"), out_error)  # the threadAct emits a signal with a parameter
            # to be received by the main thread
            if out_error[:-2] != '0000':  # each TS call, erase the previous error
                self.emit(SIGNAL("error_send(QString)"),
                          out_error[:-2])  # send to main thread to be displayed the last error

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
            self.emit(SIGNAL("status_send(QString)"), out_status)  # send to main thread a signal with a parameter
            # status of actuator

            mutex.lock()
            out_z_coord = self.do_and_reply('1TP?\r\n')  # get the z coordinate of the actuator
            mutex.unlock()

            self.emit(SIGNAL("z_coord_send(QString)"), out_z_coord)  # send to main thread a signal with z coord

            if self.absolute == True:  # Change absolute position if it's required from GUI
                abs_txt = str(self.val_abs)  # convert to string the value of z coordinate
                self.do_and_nowait('1PA' + abs_txt + '\r\n')
                self.absolute = False  # next iteration does not - produce a movement
                # eliminates unnecessary serial communication

            if self.relative == True:  # Change relative position if it's required from GUI
                rel_txt = str(self.val_rel)  # convert to string the relative value
                if self.sign == 'p':
                    self.do_and_nowait('1PR' + rel_txt + '\r\n')
                    self.relative = False
                elif self.sign == 'n':  # a '-' is added to the relative value
                    self.do_and_nowait('1PR-' + rel_txt + '\r\n')
                    self.relative = False
                else:
                    print 'error'

            if self.reset_act == True:  # Change the status from Non Referenced to Ready
                self.do_and_nowait('1OR\r\n')  # by passing through HOMING
                self.reset_act = False

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
                bool_move, rel_move = follow_bead_new(focus_ratio)
                if bool_move == True:
                    mutex.lock()
                    rel_txt = str(rel_move)
                    self.do_and_nowait('1PR' + rel_txt + '\r\n')
                    mutex.unlock()
                    # self.emit(SIGNAL("adj_manual_z_for_tracking()"))
                    # else:
                    #    self.emit(SIGNAL("adj_manual_z_for_tracking()"))

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
        ser.write(to_do)  # write to serial a command
        reply_1 = ser.readline()  # read from serial the answer
        reply_2 = reply_1[3:-2]  # remove command and \r\n from the answer
        return reply_2

    def do_and_nowait(self, to_do):  # method - no answer expected from actuator
        ser.write(to_do)
        return


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# *************************************************
# ******* CLASS - THREAD FOR POWER SUPPLY  *******
class ThPowerSupply(QThread):
    def __init__(self):
        super(ThPowerSupply, self).__init__()

    def run(self):  # method which runs the thread
        # it will be started from main thread

        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.done_ps = False  # controls the exit from while loop and
        # termination of the thread
        self.power_is_set_on = False  # if power is ON, True
        self.power_is_set_off = False

        self.error_1_ps_1_status = False
        self.error_2_ps_1_status = False
        self.error_1_ps_2_status = False
        self.error_2_ps_2_status = False

        self.send_cmd_ps_status = False
        self.send_cmd_ps_index = 1
        self.send_cmd_ps_text = '*IDN?'

        # self.power_reset = False
        self.curr_1_value = 0.001
        self.curr_2_value = 0.001
        self.curr_3_value = 0.001
        self.curr_4_value = 0.001

        self.curr_1_changed = True
        self.curr_2_changed = True
        self.curr_3_changed = True
        self.curr_4_changed = True

        self.i_1_refresh = 1
        self.i_2_refresh = 1
        self.i_3_refresh = 1
        self.i_4_refresh = 1

        time_old_temp = time.clock()
        time_old_update_I = time.clock()
        time_old_psu_1 = time.clock()
        time_old_psu_2 = time.clock()
        d_time = 0.090  # update time for power supply
        channel = 1  # coil

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        while (not self.done_ps):  # loop for getting data from actuator
            time.sleep(0.02)
            kk = random.uniform(0, 4)  # the sequence of change the current to be random not 1,2,3,4 always
            # there are 24 possible permutations; too many; just 4

            # out_flag_ps = self.do_and_reply('Read_flag\r\n') # get status of arduino
            # if out_flag_ps =='0':
            #    out_flag_ps_str = 'Ready Temp OK'
            # elif out_flag_ps =='1':
            #    out_flag_ps_str = 'Error Temp HIGH'
            # else:
            #    out_flag_ps_str ='Error serial link'

            # self.emit(SIGNAL("flag_ps_send(QString)"),out_flag_ps_str) # the threadAct emits a signal with a parameter
            # to be received by the main thread

            # if self.power_reset:
            #    self.do_and_nowait('Set_flag 0\r\n')
            #    self.power_reset = False
            # FIRST VERSION IMPLEMENTATION
            # if (time.clock()-time_old_update_I)>1.0:  # in case current value was not received by PSU
            #    self.curr_1_changed = True
            #    self.curr_2_changed = True
            #    self.curr_3_changed = True
            #    self.curr_4_changed = True
            #    time_old_update_I = time.clock()
            # SECOND VERSION IMPLEMENTATION
            if ((time.clock() - time_old_update_I) > 1.0):
                if ((self.i_1_refresh == 2) and (
                        time.clock() - time_old_psu_1) > d_time):  # in case current value was not received by PSU
                    curr_1_str = str(self.curr_1_value)
                    self.do_and_nowait('PW 1 ' + curr_1_str + '\r\n')
                    self.i_1_refresh = self.i_1_refresh + 1
                    time_old_psu_1 = time.clock()

                if ((self.i_2_refresh == 2) and (
                        time.clock() - time_old_psu_1) > d_time):  # in case current value was not received by PSU
                    curr_2_str = str(self.curr_2_value)
                    self.do_and_nowait('PW 2 ' + curr_2_str + '\r\n')
                    self.i_2_refresh = self.i_2_refresh + 1
                    time_old_psu_1 = time.clock()

                if ((self.i_3_refresh == 2) and (
                        time.clock() - time_old_psu_2) > d_time):  # in case current value was not received by PSU
                    curr_3_str = str(self.curr_3_value)
                    self.do_and_nowait('PW 3 ' + curr_3_str + '\r\n')
                    self.i_3_refresh = self.i_3_refresh + 1
                    time_old_psu_2 = time.clock()

                if ((self.i_4_refresh == 2) and (
                        time.clock() - time_old_psu_2) > d_time):  # in case current value was not received by PSU
                    curr_4_str = str(self.curr_4_value)
                    self.do_and_nowait('PW 4 ' + curr_4_str + '\r\n')
                    self.i_4_refresh = self.i_4_refresh + 1
                    time_old_psu_2 = time.clock()

            if (self.power_is_set_on and ((time.clock() - time_old_psu_1) > d_time) and \
                    ((time.clock() - time_old_psu_2) > d_time)):  # and out_flag_ps =='0':
                self.do_and_nowait('P_ON\r\n')
                self.power_is_set_on = False
                time_old_psu_1 = time.clock()
                time_old_psu_2 = time.clock()

            if (self.power_is_set_off and ((time.clock() - time_old_psu_1) > d_time) and \
                    ((time.clock() - time_old_psu_2) > d_time)):  # and out_flag_ps =='0':
                self.do_and_nowait('P_OFF\r\n')
                self.power_is_set_off = False
                time_old_psu_1 = time.clock()
                time_old_psu_2 = time.clock()

            if (self.error_1_ps_1_status and ((time.clock() - time_old_psu_1) > d_time)):
                self.do_and_reply_ps_error('CMD1 EER?\r\n')
                self.error_1_ps_1_status = False
                time_old_psu_1 = time.clock()

            if (self.error_2_ps_1_status and ((time.clock() - time_old_psu_1) > d_time)):
                self.do_and_reply_ps_error('CMD1 *ESR?\r\n')
                self.error_2_ps_1_status = False
                time_old_psu_1 = time.clock()

            if (self.error_1_ps_2_status and ((time.clock() - time_old_psu_2) > d_time)):
                self.do_and_reply_ps_error('CMD2 EER?\r\n')
                self.error_1_ps_2_status = False
                time_old_psu_2 = time.clock()

            if (self.error_2_ps_2_status and ((time.clock() - time_old_psu_2) > d_time)):
                self.do_and_reply_ps_error('CMD2 *ESR?\r\n')
                self.error_2_ps_2_status = False
                time_old_psu_2 = time.clock()

            if (self.send_cmd_ps_status):
                if ((self.send_cmd_ps_index == 1) and ((time.clock() - time_old_psu_1) > d_time)):
                    self.do_and_reply_ps_error('CMD1 ' + str(self.send_cmd_ps_text) + '\r\n')
                    self.send_cmd_ps_status = False
                    time_old_psu_1 = time.clock()

                if ((self.send_cmd_ps_index == 2) and ((time.clock() - time_old_psu_2) > d_time)):
                    temporal = 'CMD2 ' + str(self.send_cmd_ps_text) + '\r\n'
                    # print temporal
                    self.do_and_reply_ps_error(temporal)
                    self.send_cmd_ps_status = False
                    time_old_psu_2 = time.clock()

            if (kk < 1.0):
                if (self.curr_1_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.curr_1_value)
                    self.do_and_nowait('PW 1 ' + curr_1_str + '\r\n')
                    self.curr_1_changed = False
                    time_old_update_I = time.clock()
                    self.i_1_refresh = self.i_1_refresh + 1
                    time_old_psu_1 = time.clock()
                if (self.curr_3_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.curr_3_value)
                    self.do_and_nowait('PW 3 ' + curr_3_str + '\r\n')
                    self.curr_3_changed = False
                    self.i_3_refresh = self.i_3_refresh + 1
                    time_old_update_I = time.clock()
                    time_old_psu_2 = time.clock()
                if (self.curr_2_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.curr_2_value)
                    self.do_and_nowait('PW 2 ' + curr_2_str + '\r\n')
                    self.curr_2_changed = False
                    time_old_update_I = time.clock()
                    self.i_2_refresh = self.i_2_refresh + 1
                    time_old_psu_1 = time.clock()
                if (self.curr_4_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.curr_4_value)
                    self.do_and_nowait('PW 4 ' + curr_4_str + '\r\n')
                    self.curr_4_changed = False
                    time_old_update_I = time.clock()
                    self.i_4_refresh = self.i_4_refresh + 1
                    time_old_psu_2 = time.clock()

            elif ((kk < 2.0) and (kk >= 1.0)):
                if (self.curr_1_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.curr_1_value)
                    self.do_and_nowait('PW 1 ' + curr_1_str + '\r\n')
                    self.curr_1_changed = False
                    time_old_update_I = time.clock()
                    self.i_1_refresh = self.i_1_refresh + 1
                    time_old_psu_1 = time.clock()
                if (self.curr_3_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.curr_3_value)
                    self.do_and_nowait('PW 3 ' + curr_3_str + '\r\n')
                    self.curr_3_changed = False
                    time_old_update_I = time.clock()
                    self.i_3_refresh = self.i_3_refresh + 1
                    time_old_psu_2 = time.clock()
                if (self.curr_4_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.curr_4_value)
                    self.do_and_nowait('PW 4 ' + curr_4_str + '\r\n')
                    self.curr_4_changed = False
                    time_old_update_I = time.clock()
                    self.i_4_refresh = self.i_4_refresh + 1
                    time_old_psu_2 = time.clock()
                if (self.curr_2_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.curr_2_value)
                    self.do_and_nowait('PW 2 ' + curr_2_str + '\r\n')
                    self.curr_2_changed = False
                    time_old_update_I = time.clock()
                    self.i_2_refresh = self.i_2_refresh + 1
                    time_old_psu_1 = time.clock()

            elif ((kk < 3.0) and (kk >= 2.0)):
                if (self.curr_3_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.curr_3_value)
                    self.do_and_nowait('PW 3 ' + curr_3_str + '\r\n')
                    self.curr_3_changed = False
                    time_old_update_I = time.clock()
                    self.i_3_refresh = self.i_3_refresh + 1
                    time_old_psu_2 = time.clock()
                if (self.curr_1_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.curr_1_value)
                    self.do_and_nowait('PW 1 ' + curr_1_str + '\r\n')
                    self.curr_1_changed = False
                    time_old_update_I = time.clock()
                    self.i_1_refresh = self.i_1_refresh + 1
                    time_old_psu_1 = time.clock()
                if (self.curr_2_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.curr_2_value)
                    self.do_and_nowait('PW 2 ' + curr_2_str + '\r\n')
                    self.curr_2_changed = False
                    time_old_update_I = time.clock()
                    self.i_2_refresh = self.i_2_refresh + 1
                    time_old_psu_1 = time.clock()
                if (self.curr_4_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.curr_4_value)
                    self.do_and_nowait('PW 4 ' + curr_4_str + '\r\n')
                    self.curr_4_changed = False
                    time_old_update_I = time.clock()
                    self.i_4_refresh = self.i_4_refresh + 1
                    time_old_psu_2 = time.clock()

            else:
                if (self.curr_3_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.curr_3_value)
                    self.do_and_nowait('PW 3 ' + curr_3_str + '\r\n')
                    self.curr_3_changed = False
                    time_old_update_I = time.clock()
                    self.i_3_refresh = self.i_3_refresh + 1
                    time_old_psu_2 = time.clock()
                if (self.curr_1_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.curr_1_value)
                    self.do_and_nowait('PW 1 ' + curr_1_str + '\r\n')
                    self.curr_1_changed = False
                    time_old_update_I = time.clock()
                    self.i_1_refresh = self.i_1_refresh + 1
                    time_old_psu_1 = time.clock()
                if (self.curr_4_changed and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.curr_4_value)
                    self.do_and_nowait('PW 4 ' + curr_4_str + '\r\n')
                    self.curr_4_changed = False
                    time_old_update_I = time.clock()
                    self.i_4_refresh = self.i_4_refresh + 1
                    time_old_psu_2 = time.clock()
                if (self.curr_2_changed and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.curr_2_value)
                    self.do_and_nowait('PW 2 ' + curr_2_str + '\r\n')
                    self.curr_2_changed = False
                    time_old_update_I = time.clock()
                    self.i_2_refresh = self.i_2_refresh + 1
                    time_old_psu_1 = time.clock()

            if (time.clock() - time_old_temp) > 1.0:  # 2 sensors was 2.0
                if channel == 1:
                    temp_thermistor = self.do_and_reply_ps('T1\r\n')
                    self.emit(SIGNAL("temp_C_send(QString)"), temp_thermistor)
                    time_old_temp = time.clock()
                    channel = 2
                elif channel == 2:
                    temp_thermistor2 = self.do_and_reply_ps('T2\r\n')
                    self.emit(SIGNAL("temp_C_send2(QString)"), temp_thermistor2)
                    time_old_temp = time.clock()
                    channel = 3
                elif channel == 3:
                    temp_thermistor3 = self.do_and_reply_ps('T3\r\n')
                    self.emit(SIGNAL("temp_C_send3(QString)"), temp_thermistor3)
                    time_old_temp = time.clock()
                    channel = 1
                # elif channel == 4:
                #    temp_thermistor4 = self.do_and_reply_ps('T4\r\n')
                #    self.emit(SIGNAL("temp_C_send4(QString)"),temp_thermistor4)
                #    time_old_temp = time.clock()
                #    channel = 1
                else:
                    print 'error channel'
                    # print channel

        self.do_and_nowait('P_OFF\r\n')
        # self.emit(SIGNAL("flag_ps_send(QString)"),' ')
        self.do_and_nowait('Set_Local\r\n')
        print "Done with Power Supply thread"  # to be converted into a comment

    def do_and_reply_ps(self, to_do):  # method - to get answer from controller
        ser_ps.write(to_do)  # write to serial a command
        time.sleep(0.02)
        reply_1 = ser_ps.readline()  # read from serial the answer
        reply_2 = reply_1[:4]  # remove \r\n from the answer 20.5

        no_ch_buffer = ser_ps.inWaiting()
        # print 'ch_ps ', no_ch_buffer

        if (no_ch_buffer != 0):
            reply_1 = ser_ps.readline()  # read from serial the answer
            reply_2 = reply_1[:4]  # remove \r\n from the answer 20.5
            if (ser_ps.inWaiting() != 0):
                reply_1 = ser_ps.readline()  # read from serial the answer
                reply_2 = reply_1[:4]  # remove \r\n from the answer 20.5
                index_serial = 0
                while (ser_ps.inWaiting() != 0) and (index_serial < 5):
                    reply_1 = ser_ps.readline()  # read from serial the answer
                    reply_2 = reply_1[:4]  # remove \r\n from the answer 20.5
                    index_serial = index_serial + index_serial

        return reply_2

    def do_and_nowait(self, to_do):  # method - no answer expected from actuator
        ser_ps.write(to_do)
        return

    def do_and_reply_ps_error(self, to_do):  # method - to get answer from controller
        # print to_do
        ser_ps.write(to_do)  # write to serial a command
        time.sleep(0.1)
        reply_1 = ser_ps.readline()  # read from serial the answer
        print to_do[:-2] + ' ' + reply_1[:-1]

        no_ch_buffer = ser_ps.inWaiting()
        # print 'ch_ps ', no_ch_buffer

        if (no_ch_buffer != 0):
            reply_1 = ser_ps.readline()  # read from serial the answer
            print to_do[:-2] + ' ' + reply_1[:-1]
            if (ser_ps.inWaiting() != 0):
                reply_1 = ser_ps.readline()  # read from serial the answer
                print to_do[:-2] + ' ' + reply_1[:-1]
                index_serial = 0
                while (ser_ps.inWaiting() != 0) and (index_serial < 5):
                    reply_1 = ser_ps.readline()  # read from serial the answer
                    print to_do[:-2] + ' ' + reply_1[:-1]
                    index_serial = index_serial + index_serial

        return

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
    # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

    # *************************************************
    # ******* CLASS - THREAD FOR 2nd temperature  *******
    # class ThTemperature2(QThread):
    #    def __init__(self):
    #        super(ThTemperature2, self).__init__()

    #    def run(self):  # method which runs the thread
    # it will be started from main thread

    # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
    #        self.done_temp2 = False   # controls the exit from while loop and
    # termination of the thread

    #        time_old_temp = time.clock()
    #        channel = 1

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# while (not self.done_temp2): # loop for getting data from actuator
#            time.sleep(0.02)


#            if (time.clock()-time_old_temp)>2.0:
#                if channel == 1:
#                    temp_thermistor = self.do_and_reply_temp2('Temp_1\r\n')
#                    self.emit(SIGNAL("temp_C_send(QString)"),temp_thermistor)
#                    time_old_temp = time.clock()
#                    channel = 1
#                elif channel == 2:
#                    temp_thermistor2 = self.do_and_reply_temp2('Temp_2\r\n')
#                    self.emit(SIGNAL("temp_C_send2(QString)"),temp_thermistor2)
#                    time_old_temp = time.clock()
#                    channel = 1
#                else:
#                    print 'error channel'
#                #print channel


#        print "Done with 2nd temperature thread"      # to be converted into a comment

#    def do_and_reply_temp2(self, to_do):  # method - to get answer from controller
#        ser_2temp.write(to_do)            # write to serial a command
#        reply_1 = ser_2temp.readline()    # read from serial the answer
#        reply_2 = reply_1[:4]     # remove command and \r\n from the answer
#        return reply_2

#    def do_and_nowait(self,to_do):  # method - no answer expected from actuator
#        ser_2temp.write(to_do)
#        return
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&


# *************************************************
# ******* CLASS - THREAD FOR EXPERIMENTS  *******
class ThExperiments(QThread):
    def __init__(self):
        super(ThExperiments, self).__init__()

        # self.mutex2 = QMutex()

    def run(self):  # method which runs the thread
        # it will be started from main thread

        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.done_exp = False  # controls the exit from while loop and
        # termination of the thread
        self.exp_run = False  # if power is ON, True
        self.exp_move_initial = False
        self.exp_ready_to_sweep = False
        self.exp_idle = False

        self.val_exper_min = 7.17
        self.val_exper_max = 7.6
        self.val_exper_step = 0.004
        self.val_exper_real_time_z = 7.5
        self.name_folder_stack = '__ '
        print self.name_folder_stack

        # self.curr_1_changed = True
        # self.curr_2_changed = True
        # self.curr_3_changed = True
        # self.curr_4_changed = True

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        while (not self.done_exp):  # loop for getting data from actuator
            time.sleep(0.02)

            if self.exp_run and self.exp_move_initial:
                if self.name_folder_stack == '':
                    self.folder_path = os.getcwd() + '\\stack\\' + '_default\\'
                else:
                    self.folder_path = os.getcwd() + '\\stack\\' + self.name_folder_stack + '\\'
                print self.folder_path
                if not os.path.isdir(self.folder_path):
                    os.makedirs(self.folder_path)
                self.folder_path_c1 = self.folder_path + 'cam1\\'
                self.folder_path_c2 = self.folder_path + 'cam2\\'
                if not os.path.isdir(self.folder_path_c1):
                    os.makedirs(self.folder_path_c1)
                if not os.path.isdir(self.folder_path_c2):
                    os.makedirs(self.folder_path_c2)

                mutex.lock()
                self.do_and_nowait('1PA' + str(self.val_exper_min) + '\r\n')
                mutex.unlock()
                self.exp_move_initial = False
                time.sleep(1.5)  # 1.5
                self.emit(SIGNAL("experiment_save_picture()"))
                # self.emit(SIGNAL("plot_f_vs_z_initial()"))
                self.emit(SIGNAL("log_exp_stack_init()"))
                time.sleep(0.5)  # 0.5
                self.exp_ready_to_sweep = True
                # print 'test'

            if self.exp_run and self.exp_ready_to_sweep:
                mutex.lock()
                self.do_and_nowait('1PR' + str(self.val_exper_step) + '\r\n')
                mutex.unlock()
                time.sleep(1.0)
                # self.emit(SIGNAL("plot_f_vs_z_running()"))
                self.emit(SIGNAL("experiment_save_picture()"))
                self.emit(SIGNAL("log_exp_stack_running()"))
                time.sleep(0.5)

            if self.exp_idle or (self.val_exper_real_time_z > self.val_exper_max):
                # print 'stop ', self.exp_idle
                self.emit(SIGNAL("exp_ended()"))
                self.exp_run = False
                self.exp_idle = False
                self.exp_ready_to_sweep = False

                # out_flag_ps = self.do_and_reply('Read_flag\r\n') # get status of arduino
                # if out_flag_ps =='0':
                #    out_flag_ps_str = 'Ready Temp OK'
                # elif out_flag_ps =='1':
                #    out_flag_ps_str = 'Error Temp HIGH'
                # else:
                #    out_flag_ps_str ='Error serial link'

                # self.emit(SIGNAL("flag_ps_send(QString)"),out_flag_ps_str) # the threadAct emits a signal with a parameter
                # to be received by the main thread

                # if self.power_reset:
                #    self.do_and_nowait('Set_flag 0\r\n')
                #    self.power_reset = False

                # if self.curr_4_changed:  # True
                #    curr_4_str = str(self.curr_4_value)
                #    self.do_and_nowait('PSUWrite 4 '+curr_4_str+'\r\n')
                #    self.curr_4_changed = False

        print "Done with Experiment thread"  # to be converted into a comment

    def do_and_reply(self, to_do):  # method - to get answer from controller
        ser_ps.write(to_do)  # write to serial a command
        reply_1 = ser_ps.readline()  # read from serial the answer
        reply_2 = reply_1[5:]  # remove command and \r\n from the answer
        return reply_2

    def do_and_nowait(self, to_do):  # method - no answer expected from actuator
        ser.write(to_do)
        # print 'test2'
        return


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

# *************************************************
# ******* CLASS - THREAD FOR RANDOM WALK BEAD  *******
class ThRandomWalkBead(QThread):
    def __init__(self):
        super(ThRandomWalkBead, self).__init__()

        # self.mutex2 = QMutex()

    def run(self):  # method which runs the thread
        # it will be started from main thread

        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.done_random = False  # controls the exit from while loop and
        # termination of the thread

        # self.val_exper_min = 7.17
        # self.val_exper_max = 7.6
        # self.val_exper_step = 0.004
        # self.val_exper_real_time_z = 7.5

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        while (not self.done_random):  # loop for moving bead

            # if self.exp_idle or (self.val_exper_real_time_z >self.val_exper_max):
            #    #print 'stop ', self.exp_idle
            #    self.emit(SIGNAL("exp_ended()"))
            #    self.exp_run = False
            #    self.exp_idle = False
            #    self.exp_ready_to_sweep = False

            # self.emit(SIGNAL("flag_ps_send(QString)"),out_flag_ps_str) # the threadAct emits a signal with a parameter
            # to be received by the main thread
            print "random"

            # print "Done with Random thread"      # to be converted into a comment


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

# *************************************************
# ******* CLASS - THREAD FOR DEMAG POLES   *******
class ThDemagPoles(QThread):
    def __init__(self):
        super(ThDemagPoles, self).__init__()

        self.current_sweep = 1.0
        self.current_step = 0.05
        self.current_time_wait = 1.5

        # self.mutex2 = QMutex()

    def run(self):  # method which runs the thread
        # it will be started from main thread

        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.done_demag = False  # controls the exit from while loop and
        # termination of the thread

        # self.val_exper_min = 7.17
        # self.val_exper_max = 7.6
        # self.val_exper_step = 0.004
        # self.val_exper_real_time_z = 7.5

        # print "demag"
        # self.current_sweep = 1.0
        # self.current_step = 0.05
        # self.current_time_wait = 1.5
        index = int(self.current_sweep / (2 * self.current_step))
        ii = 0

        current_sweep_old = self.current_sweep
        while (not self.done_demag):  # loop for sweeping current
            ii = ii + 1
            self.emit(SIGNAL("I_demag_send(QString)"), str(current_sweep_old))
            time.sleep(self.current_time_wait)

            current_sweep_old = current_sweep_old - self.current_step
            current_sweep_old = - current_sweep_old

            self.emit(SIGNAL("I_demag_send(QString)"), str(current_sweep_old))
            time.sleep(self.current_time_wait)

            current_sweep_old = current_sweep_old + self.current_step
            current_sweep_old = - current_sweep_old

            if ii >= index:
                self.done_demag = True

        self.emit(SIGNAL("I_demag_send(QString)"), str(0.0))
        self.emit(SIGNAL("demag_ended()"))


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# *************************************************
# ******* CLASS - THREAD FOR I COMBINATION  *******
class ThExpDirection(QThread):
    def __init__(self):
        super(ThExpDirection, self).__init__()
        self.start_index = 1
        self.actual_index = 0
        self.go_away_from_origin = 'F'
        self.flag_running = 'F'

    def run(self):  # method which runs the thread
        # it will be started from main thread

        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.flag_running = 'T'
        self.done_i_direction = False  # controls the exit from while loop and
        # termination of the thread
        self.current_list = [2.5, 1.5, 0.0, -1.5, -2.5]
        self.current_list_2 = [2.5, 2.0, 1.5, 1.0, 0.5]
        # self.current_list = [0.5,0.25, 0.0, -0.25, -0.5]
        # self.configurations = self.generate_current_list(self.current_list)
        self.configurations = self.generate_current_list_scaling(self.current_list_2)
        print len(self.configurations)
        time.sleep(1)  # wait for bead coordinates to be update. The update might occur in the same time with run()
        self.actual_index = self.start_index
        self.emit(SIGNAL("I_exp_actual_index_send(QString)"), str(self.actual_index))
        # time.sleep(4)

        self.go_to_origin = True
        self.go_to_origin_go = True
        self.go_away_from_origin = False
        self.go_away_from_origin_1st = False

        x_mid = 1294
        y_mid = 970
        z_mid = self.z_center_oil

        print 'xyz mid', x_mid, y_mid, z_mid
        iii = 1

        while (not self.done_i_direction):  # loop for sweeping current

            # print 'config curr', self.configurations[self.actual_index-1]
            # print 'boolean', not self.done_i_direction
            # print 'go-to_origin', go_to_origin

            if (self.go_to_origin == True):  # move bead to origin section activate?
                if (self.go_to_origin_go == True):  # move bead
                    # print 'xy real time', self.x_bead, self.y_bead

                    if (abs(self.x_bead - x_mid) < 50):  # normal movement up/down/ left right
                        if (self.y_bead - y_mid) > 4:
                            self.emit(SIGNAL("I_exp_UP()"))
                            # print 'up'
                        elif (self.y_bead - y_mid) < -4:
                            self.emit(SIGNAL("I_exp_DOWN()"))
                            # print 'down'
                        elif (self.x_bead - x_mid) < -10:
                            self.emit(SIGNAL("I_exp_LEFT()"))
                            # print 'left'
                        elif (self.x_bead - x_mid) > 10:
                            self.emit(SIGNAL("I_exp_RIGHT()"))
                            # print 'right'
                        else:
                            # self.emit(SIGNAL("I_exp_zUP()"))
                            self.emit(SIGNAL("I_exp_UP()"))
                            kkk = 7
                            # print 'kkk' , kkk

                    elif (abs(self.x_bead - x_mid) < 500):  # too close to the wall -> left /right and then up/down
                        if (self.x_bead - x_mid) > 10:
                            self.emit(SIGNAL("I_exp_RIGHT()"))
                            # print 'right'
                        elif (self.x_bead - x_mid) < -10:
                            self.emit(SIGNAL("I_exp_LEFT()"))
                            # print 'left'
                        elif (self.y_bead - y_mid) > 4:
                            self.emit(SIGNAL("I_exp_UP()"))
                            # print 'up'
                        elif (self.y_bead - y_mid) < -4:
                            self.emit(SIGNAL("I_exp_DOWN()"))
                            # print 'down'
                        else:
                            # self.emit(SIGNAL("I_exp_zUP()"))
                            self.emit(SIGNAL("I_exp_UP()"))
                            kkk = 6
                            # print 'kkk', kkk
                    else:  # out of confort zone -> using only one pole to pull the bead -. moderate current
                        if (self.x_bead > x_mid):  # it's in the right side
                            if (self.y_bead > y_mid):  # it's in the lower part
                                self.emit(SIGNAL("I_exp_coil_4()"))
                            else:  # it's in the upper part
                                self.emit(SIGNAL("I_exp_coil_3"))
                        else:  # it's in the left side
                            if (self.y_bead > y_mid):  # it's in the lower part
                                self.emit(SIGNAL("I_exp_coil_1()"))
                            else:  # it's in the upper part
                                self.emit(SIGNAL("I_exp_coil_2"))

                cond = ((abs(self.x_bead - x_mid) < 10) and (abs(self.y_bead - y_mid) < 10) and (
                        abs(self.z_bead - z_mid) < 0.010))
                # print 'cond', cond

                if (cond == True):  # bead is in origin
                    # print 'cond', cond
                    self.go_to_origin = False  # stopping this section
                    self.go_to_origin_go = False
                    self.go_away_from_origin = True  # activating next section
                    self.go_away_from_origin_1st = True
                    self.emit(SIGNAL("I_exp_ZERO()"))  # set current to zero
                    time.sleep(1)  # wait for current to stabilize at zero
                elif (self.z_bead <= z_mid + 0.01) and (
                        self.go_to_origin_go == True):  # bead is not in the center and bellow z_center
                    iii = 3  # we go forward
                else:  # bead is not in the center but above the center in z
                    self.emit(SIGNAL("I_exp_ZERO()"))  # set current to zero
                    self.go_to_origin_go = False  # stop moving the bead; let it sink
                    if (self.z_bead - z_mid) < -0.02:  # bead sank more than 20 microns activate the currents
                        self.go_to_origin_go = True

            # print 'go_away_from_origin' , go_away_from_origin

            if (self.go_away_from_origin == True):  # apply one of the configurations
                # print 'go_away_from_origin' , go_away_from_origin
                # print 'go_away_from_origin_first' , go_away_from_origin_1st
                if (self.go_away_from_origin_1st == True):
                    # c1 = self.configurations[self.actual_index-1][0]
                    # c2 = self.configurations[self.actual_index-1][1]
                    # c3 = self.configurations[self.actual_index-1][2]
                    # c4 = self.configurations[self.actual_index-1][3]
                    # print 'c1234', c1,c2,c3,c4
                    # self.emit(SIGNAL("I_exp_CONF(QString,QString,QString,QSting)"), str(c1),str(c2),str(c3),str(c4))
                    self.emit(SIGNAL("I_exp_CONF(QString)"), str(self.actual_index))
                    print 'config curr', self.configurations[self.actual_index - 1]
                    # print 'after signal sent'
                    self.go_away_from_origin_1st = False
                    time_old = time.clock()

                cond2 = ((abs(self.x_bead - x_mid) > 300) or (abs(self.y_bead - y_mid) > 300) or (
                        abs(self.z_bead - z_mid) > 0.11))
                # print 'cond2', cond2

                # if ((cond2 == True) or ((time.clock() - time_old) > 15)): # intitial condition for time
                if ((cond2 == True) or (
                        (time.clock() - time_old) > 600)):  # here we don't care about time. what all traj
                    self.emit(SIGNAL("I_exp_ZERO()"))  # set current to zero
                    self.go_away_from_origin = False
                    self.go_away_from_origin_1st = True
                    self.go_to_origin = True
                    self.go_to_origin_go = True

                    self.actual_index = self.actual_index + 1
                    self.emit(SIGNAL("I_exp_actual_index_send(QString)"), str(self.actual_index))
                    if (self.actual_index > len(self.configurations)):
                        self.done_i_direction = True

            time.sleep(0.3)
        print 'Done with Th Experiment 2'

    def generate_current_list(self, input_list):
        output_list = []
        for k1 in range(len(input_list)):
            for k2 in range(len(input_list)):
                for k3 in range(len(input_list)):
                    for k4 in range(len(input_list)):
                        dumm = []
                        dumm.append(input_list[k1])
                        dumm.append(input_list[k2])
                        dumm.append(input_list[k3])
                        dumm.append(input_list[k4])
                        output_list.append(dumm)

        return output_list

    def generate_current_list_scaling(self, input_list):
        output_list = []
        for k1 in range(len(input_list)):  # to right
            dumm = []
            dumm.append(input_list[k1])
            dumm.append(input_list[k1])
            dumm.append(input_list[k1] / 2.0)
            dumm.append(input_list[k1] / 2.0)
            output_list.append(dumm)

        for k1 in range(len(input_list)):  # to_top
            dumm = []
            dumm.append(0.0)
            dumm.append(input_list[k1])
            dumm.append(input_list[k1])
            dumm.append(0.0)
            output_list.append(dumm)

        for k1 in range(len(input_list)):  # to bottom
            dumm = []
            dumm.append(input_list[k1])
            dumm.append(0.0)
            dumm.append(0.0)
            dumm.append(input_list[k1])
            output_list.append(dumm)

        for k1 in range(len(input_list)):  # left
            dumm = []
            dumm.append(input_list[k1] / 2.0)
            dumm.append(input_list[k1] / 2.0)
            dumm.append(input_list[k1])
            dumm.append(input_list[k1])
            output_list.append(dumm)

        return output_list

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #  ++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # class drawCanny(QtGui.QImage):
    #    def __init__(self, frame_in,threshMin,threshMax):
    # im_gray = cv.CreateImage(cv.GetSize(frame), frame.depth, 1)
    # frame = cv2.threshold(frame,127,255,cv2.THRESH_BINARY)
    # im_gray = cv.CreateImage(cv.GetSize(frame), frame.depth, 1) # only 1 channel, can't convert to qimage
    # cv.CvtColor(frame, im_gray, cv.CV_RGB2GRAY)
    # im_cann = cv.CreateImage(cv.GetSize(im_gray), im_gray.depth, im_gray.channels)
    # cv.Canny(im_gray, im_cann, 10, 100, 3)
    # cv.Threshold(im_gray, im_cann, threshMin,threshMax, cv2.THRESH_BINARY)
    # cv.CvtColor(im_cann, frame, cv.CV_GRAY2RGB)
    # print frame_in


# res, frame1 = cv2.threshold(frame_in, threshMin,threshMax,cv2.THRESH_BINARY)
#        frame_in = frame1

#        print threshMin


# ********************************************************
# ******* FUNCTION - returns picture after threshold *****
def NumThres(frame2, threshMin, threshMax):
    res, frame1 = cv2.threshold(frame2, threshMin, threshMax, cv2.THRESH_BINARY)
    return frame1


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# def Hough_circle(n_frame):
#    circles = cv2.HoughCircles(n_frame, cv.CV_HOUGH_GRADIENT, 1.0, 8,param1=50,param2=30, minRadius=0, maxRadius=0)
#    h1, w1= n_frame.shape
#    img_circle_n = numpy.zeros((h1,w1),numpy.uint8)
#    if circles is None:
#        print 'No circle'
#        x=0
#        y=0
#        r=0

#    else:
#        print len(circles[0])
#        for i in range(0,len(circles[0])):
#            x= circles[0][i][0]
#            y= circles[0][i][1]
#            r= circles[0][i][2]
#            cv2.circle(img_circle_n,(x,y),r,(255,255,255),-1)
#        x= circles[0][0][0]
#        y= circles[0][0][1]
#        r= circles[0][0][2]

#    return img_circle_n, x,y,r


# ********************************************************
# ******* FUNCTION - detects and filter beads ************
def beads_detection(n_frame, th_min, th_max, cround_min, cround_max, area_min, area_max):
    # gray = cv2.cvtColor(n_frame,cv2.COLOR_BGR2GRAY) # might not be necessary
    gray = n_frame.copy()
    gray_contours = gray.copy()

    thresh = NumThres(gray, th_min, th_max)
    thresh_initial = thresh.copy()  # a copy just in case, as it's changed by findContours

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    no_detected = 0
    xr, yr, wr, hr, cx, cy = 0, 0, 0, 0, 0, 0
    ccround = 0.5
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 0.1:  # cround requires area != 0
            length = cv2.arcLength(cnt, closed=True)
            cround = (length * length) / (4.0 * np.pi * area)  # circularity factor
            # area_min, area_max = 100, 1500 # to be transmited as parameters - FUTURE
            # cround_min, cround_max = 0.8, 1.3 # to be transmited as parameters - FUTURE
            if area > area_min and area < area_max:
                if cround > cround_min and cround < cround_max:
                    xr, yr, wr, hr = cv2.boundingRect(cnt)
                    xc = xr + int(wr / 2.0)
                    yc = yr + int(hr / 2.0)
                    # print cround
                    cv2.rectangle(gray, (xc - wr, yc - hr), (xc + wr, yc + hr), (255, 0, 0), 2)
                    M = cv2.moments(cnt)  # finding centroids of cnt
                    cx, cy = int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
                    no_detected = no_detected + 1
                    ccround = cround
                    # print cx,cy, xc,yc

    # print no_detected, wr,hr,xc,yc
    cv2.drawContours(gray_contours, contours, -1, (0, 255, 0))  # all contours detected '-1' //
    return gray, xr, yr, wr, hr, no_detected, cx, cy, ccround  # , gray_contours, thresh, thresh_initial


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ********************************************************
# ******* FUNCTION - crop picture with bead **************
def crop_stack(n_frame, xc, yc):
    y1 = yc - 46
    y2 = yc + 46

    x1 = xc - 46
    x2 = xc + 46

    roi = np.copy(n_frame[y1:y2, x1:x2])

    return roi


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ********************************************************
# ******* FUNCTION - detects and filter beads for stack ************
def beads_detection_stack(n_frame):
    th_min = 80
    th_max = 255
    cround_min = 0.8
    cround_max = 1.3
    area_min = 600
    area_max = 1500

    xc_bead_i = 1495
    yc_bead_i = 970

    xc_bead_f = xc_bead_i
    yc_bead_f = yc_bead_i

    n_frame_crop = crop_stack(n_frame, xc_bead_i, yc_bead_i)

    gray = n_frame_crop.copy()
    thresh = NumThres(gray, th_min, th_max)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:  # only one bead is detected
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 100:  # cround requires area != 0
                length = cv2.arcLength(cnt, closed=True)
                cround = (length * length) / (4.0 * np.pi * area)  # circularity factor
                if area > area_min and area < area_max:
                    if cround > cround_min and cround < cround_max:
                        M = cv2.moments(cnt)  # finding centroids of cnt
                        xxc, yyc = int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
                        xc_bead_f = xc_bead_i - 46 + xxc
                        yc_bead_f = yc_bead_i - 46 + yyc

    n2_frame_crop = crop_stack(n_frame, xc_bead_f, yc_bead_f)

    return n2_frame_crop, xc_bead_f, yc_bead_f  # , gray_contours, thresh, thresh_initial


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ********************************************************
# ******* FUNCTION - crop picture with bead **************
def crop(n_frame, xr, yr, wr, hr, bead_slider):
    if wr % 2 != 0:  # it seems that wr and hr must be an even number to prevent distorsion of the picture
        wr = wr + 1
    if hr % 2 != 0:
        hr = hr + 1

    xc = xr + int(wr / 2.0)
    yc = yr + int(hr / 2.0)

    # y1 = yc-int(1.0*hr)
    # y2 = yc+int(1.0*hr)

    # x1 = xc-int(1.0*wr)
    # x2 = xc+int(1.0*wr)

    y1 = yc - int(bead_slider * 46)
    y2 = yc + int(bead_slider * 46)

    x1 = xc - int(bead_slider * 46)
    x2 = xc + int(bead_slider * 46)

    size_crop = (wr, hr, 1)

    roi = np.copy(n_frame[y1:y2, x1:x2])

    return roi


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# **************************************************************
# ******* FUNCTION - return modified image by SOBEL filter *****
def sobel_edge(n_frame):
    kernel = 3
    ddepth = cv2.CV_16S

    img_sobel_x = cv2.Sobel(n_frame, ddepth, 1, 0, ksize=kernel, borderType=cv2.BORDER_DEFAULT)  # x derivative
    img_sobel_y = cv2.Sobel(n_frame, ddepth, 0, 1, ksize=kernel, borderType=cv2.BORDER_DEFAULT)  # y derivative

    # img_sobel_x = cv2.Scharr(n_frame, ddepth,1,0)
    # img_sobel_y = cv2.Scharr(n_frame, ddepth,0,1)

    img_sobel_x_abs = cv2.convertScaleAbs(img_sobel_x)  # converting all to positive // to uint8
    img_sobel_y_abs = cv2.convertScaleAbs(img_sobel_y)  # converting all to positive // to uint8

    img_sobel_n = cv2.addWeighted(img_sobel_x_abs, 0.5, img_sobel_y_abs, 0.5, 0)  # norm = abs(x) + abs(y)
    # it provides similar results like norm = sqrt(x*x+y*y)
    return img_sobel_n


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# **************************************************************
# ******* FUNCTION - return focus parameter bead reference stack *****
def bead_focus_stack(n_frame):
    s_in_frame, xc, yc = beads_detection_stack(n_frame)
    s_out_frame = sobel_edge(s_in_frame)

    avg, sigma = cv2.meanStdDev(s_out_frame)

    focus_param = round(sigma[0][0] / avg[0][0], 3)

    return focus_param, xc, yc


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# **************************************************************
# ******* FUNCTION - return theoretical focus param s **********
def f1_analytic(x):
    a = -502568.69217
    b = 206443.52808
    c = -28265.96318
    d = 1289.98324
    return a + b * x + c * x * x + d * x * x * x


def f2_analytic(x):
    a = 491477.6662
    b = -201782.91117
    c = 27613.70843
    d = -1259.57454
    return a + b * x + c * x * x + d * x * x * x


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# **************************************************************
# ******* FUNCTION - get z offset of the bead ******************
def bead_z_evaluate(f1, f2):
    tol = 0.001
    x_min = 7.27
    x_max = 7.35
    c = (x_min + x_max) / 2

    while abs(f1_analytic(c) - f1) > tol or (x_max - x_min) / 2 > tol:
        if (f1_analytic(c) - f1 > 0 and f1_analytic(x_min) - f1 > 0) or (
                f1_analytic(c) - f1 < 0 and f1_analytic(x_min) - f1 < 0):
            x_min = c
        else:
            x_max = c
        c = (x_min + x_max) / 2
    x1 = c

    x_min = 7.27
    x_max = 7.35
    c = (x_min + x_max) / 2

    while abs(f2_analytic(c) - f2) > tol or (x_max - x_min) / 2 > tol:
        if (f2_analytic(c) - f2 > 0 and f2_analytic(x_min) - f2 > 0) or (
                f2_analytic(c) - f2 < 0 and f2_analytic(x_min) - f2 < 0):
            x_min = c
        else:
            x_max = c
        c = (x_min + x_max) / 2
    x2 = c

    x_avg = (x1 + x2) / 2
    return x_avg


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# **************************************************************
# ******* FUNCTION - move or not the actuator ******************
def follow_bead(x_av):
    x_1 = 7.25995
    x_2 = 7.35794

    x_half = (x_1 + x_2) / 2

    if abs(x_av - x_half) > 0.015:
        go_act = True
        rel_z_go = -(x_av - x_half)
    else:
        go_act = False
        rel_z_go = 0.0

    return go_act, rel_z_go


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

def follow_bead_new(f_1_over_f_2):
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


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# **************************************************************
# ******* FUNCTION - move or not the actuator ******************
def delta_z_bead(x_av):
    x_1 = 7.25995

    return x_av - x_1


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ****************************************************
# ******* CLASS - THREAD FOR GUI (main thread) *******
class PySideCam(QtGui.QWidget):
    def __init__(self):
        super(PySideCam, self).__init__()
        # self.th_video = ThVideo()
        self.th_actuator = ThActuator()  # create an instance of the class which will run into a different
        self.th_power_supp = ThPowerSupply()  # thread. The thread is not started here. This class will be called
        self.th_experiments = ThExperiments()  # into the initUI(). It has to be created before initUi.
        self.th_random_walk = ThRandomWalkBead()
        self.th_demag = ThDemagPoles()
        self.th_exp_dir = ThExpDirection()
        #        self.th_temper_2 = ThTemperature2()
        self.initUI()  # Initialisation of GUI interface and connects SIGNALS with SLOTS
        # SLOTS == methods == functions
        # self.th_video.start()
        random.seed()
        self.time_old_ard = time.clock()
        self.index_m = 1000
        self.index_exp = 1000
        self.time_old_mov = time.clock()
        self.index_letter = 0
        self.index_pct_fps = 0
        self.config_curr = 7
        self.size_focus_avg = 30
        self.max_focus_1_2_avg = 50
        self.storage_focus1 = np.zeros(shape=(self.size_focus_avg))
        self.storage_focus_1_RT = np.zeros(shape=(self.max_focus_1_2_avg))
        self.storage_focus_2_RT = np.zeros(shape=(self.max_focus_1_2_avg))
        self.index_focus_avg = 0
        self.index_focus_avg_1_RT = 0
        self.index_focus_avg_2_RT = 0

    def __del__(self):
        # self.th_video.done_video = True
        # self.th_video.wait()
        #        self.th_temper_2.done_temp2 = True
        #        self.th_temper_2.wait()
        self.th_random_walk.done_random = True
        self.th_experiments.done_exp = True
        self.th_experiments.wait()
        self.th_demag.done_demag = True
        self.th_demag.wait()
        self.th_exp_dir.done_i_direction = True
        self.th_exp_dir.wait()
        self.th_power_supp.done_ps = True
        self.th_power_supp.wait()  # Adding supplementary instruction to the destructor of the class to
        self.th_actuator.done = True  # safely handle the termination of "ThActuator" thread.
        self.th_actuator.wait()  # Send terminate flag of the while loop. Wait "ThActuator" to finish
        ser_trig.write('OFF_Trig' + '\r\n')  # before the GUI thread will exit.
        camcapture.runFeatureCommand("AcquisitionStop")
        camcapture.endCapture()
        camcapture.revokeAllFrames()
        camcapture.closeCamera()

        camcapture_2.runFeatureCommand("AcquisitionStop")
        camcapture_2.endCapture()
        camcapture_2.revokeAllFrames()
        camcapture_2.closeCamera()
        vimba.shutdown()

        print "Exit"  #

    # atexit.register(camcapture.closeCamera())
    # atexit.register(camcapture.revokeAllFrames())
    # atexit.register(camcapture.endCapture())
    # atexit.register(camcapture.runFeatureCommand("AcquisitionStop"))

    # atexit.register(camcapture_2.closeCamera())
    # atexit.register(camcapture_2.revokeAllFrames())
    # atexit.register(camcapture_2.endCapture())
    # atexit.register(camcapture_2.runFeatureCommand("AcquisitionStop"))

    def initUI(self):

        dimx = 1650
        dimy = 910

        self.setGeometry(200, 50, dimx, dimy)  # Coordinates of the window on the screen, dimension of window
        self.setWindowTitle('Magnetic bead tracking')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_plots = QtGui.QGroupBox()
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_plots_static = QtGui.QLabel()
        self.lab_plots_static.setText("        P  L  O  T  S           ")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_plots_reset_clock = QtGui.QPushButton("Reset clock", self)
        self.connect(self.butt_plots_reset_clock, SIGNAL("pressed()"), self.butt_plots_reset_clock_Changed)
        self.time_old = time.clock()

        # =============================================

        self.butt_plots_start = QtGui.QPushButton("Start plot", self)
        self.butt_plots_start.setEnabled(True)
        self.connect(self.butt_plots_start, SIGNAL("pressed()"), self.butt_plots_start_Changed)
        self.do_plot = False

        # =============================================

        self.butt_plots_stop = QtGui.QPushButton("Stop plot", self)
        self.butt_plots_stop.setEnabled(False)
        self.connect(self.butt_plots_stop, SIGNAL("pressed()"), self.butt_plots_stop_Changed)

        # =============================================
        vbox_plots_h_butt_r_s_s = QtGui.QHBoxLayout()
        vbox_plots_h_butt_r_s_s.addWidget(self.butt_plots_reset_clock)
        vbox_plots_h_butt_r_s_s.addWidget(self.butt_plots_start)
        vbox_plots_h_butt_r_s_s.addWidget(self.butt_plots_stop)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_save_img = QtGui.QGroupBox('Save image cam 1')

        # =============================================
        self.txt_plots_name_image1 = QtGui.QLineEdit()
        self.txt_plots_name_image1.setPlaceholderText('name of the picture to be save')

        self.butt_save_img_cam1 = QtGui.QPushButton("Save image", self)
        self.connect(self.butt_save_img_cam1, SIGNAL("pressed()"), self.butt_save_img_cam1_Changed)

        # =============================================

        vbox_plots_h_butt_save_img1 = QtGui.QHBoxLayout()
        # vbox_plots_h_butt_save_img1.addStretch(1)
        vbox_plots_h_butt_save_img1.addWidget(self.butt_save_img_cam1)
        # vbox_plots_h_butt_save_img1.addStretch(1)
        vbox_plots_h_butt_save_img1.addWidget(self.txt_plots_name_image1)

        # =============================================

        # vbox_plots_v_save_img = QtGui.QVBoxLayout()
        # vbox_plots_v_save_img.addWidget(self.txt_plots_name_image1)
        # vbox_plots_v_save_img.addLayout(vbox_plots_h_butt_save_img1)
        # bound_box_save_img.setLayout(vbox_plots_v_save_img)
        bound_box_save_img.setLayout(vbox_plots_h_butt_save_img1)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        self.ctrl_plots_exposure_time_static_1 = QtGui.QLabel()
        self.ctrl_plots_exposure_time_static_1.setText("Exp time (ms) 1 ")

        self.ctrl_plots_exposure_time_1 = QtGui.QDoubleSpinBox()
        self.ctrl_plots_exposure_time_1.setMinimum(0.1)
        self.ctrl_plots_exposure_time_1.setSingleStep(1.0)
        self.ctrl_plots_exposure_time_1.setMaximum(50.0)
        self.ctrl_plots_exposure_time_1.setDecimals(3)
        self.ctrl_plots_exposure_time_1.setProperty("value", cam1_exp_time_ms)
        self.ctrl_plots_exposure_time_1.setKeyboardTracking(False)
        # self.z_bead_bottom = self.ctrl_plots_exposure_time_1.value()
        self.ctrl_plots_exposure_time_1.valueChanged.connect(self.ctrl_plots_exposure_time_1_Changed)

        self.ctrl_plots_exposure_time_static_2 = QtGui.QLabel()
        self.ctrl_plots_exposure_time_static_2.setText("  2  ")

        self.ctrl_plots_exposure_time_2 = QtGui.QDoubleSpinBox()
        self.ctrl_plots_exposure_time_2.setMinimum(0.1)
        self.ctrl_plots_exposure_time_2.setSingleStep(1.0)
        self.ctrl_plots_exposure_time_2.setMaximum(50.0)
        self.ctrl_plots_exposure_time_2.setDecimals(3)
        self.ctrl_plots_exposure_time_2.setProperty("value", cam2_exp_time_ms)
        self.ctrl_plots_exposure_time_2.setKeyboardTracking(False)
        # self.z_bead_bottom = self.ctrl_plots_exposure_time_1.value()
        self.ctrl_plots_exposure_time_2.valueChanged.connect(self.ctrl_plots_exposure_time_2_Changed)

        vbox_plots_h_ctrl_exposure_time = QtGui.QHBoxLayout()
        vbox_plots_h_ctrl_exposure_time.addWidget(self.ctrl_plots_exposure_time_static_1)
        vbox_plots_h_ctrl_exposure_time.addWidget(self.ctrl_plots_exposure_time_1)
        vbox_plots_h_ctrl_exposure_time.addWidget(self.ctrl_plots_exposure_time_static_2)
        vbox_plots_h_ctrl_exposure_time.addWidget(self.ctrl_plots_exposure_time_2)
        vbox_plots_h_ctrl_exposure_time.addStretch(1)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_save_velocity = QtGui.QGroupBox('Save data for velocity')

        # =============================================
        self.txt_plots_name_fileout = QtGui.QLineEdit()
        self.txt_plots_name_fileout.setPlaceholderText('Calibration_1')

        # =============================================

        self.butt_start_rec_fileout = QtGui.QPushButton("Start recording", self)
        # self.connect(self.butt_start_rec_fileout,SIGNAL("pressed()"),self.butt_start_rec_fileout_Changed)
        self.connect(self.butt_start_rec_fileout, SIGNAL("pressed()"), self.butt_start_rec_fileout_Changed_new)
        self.rec_calib = False

        # =============================================

        self.butt_stop_rec_fileout = QtGui.QPushButton("Stop recording", self)
        self.connect(self.butt_stop_rec_fileout, SIGNAL("pressed()"), self.butt_stop_rec_fileout_Changed)
        self.butt_stop_rec_fileout.setEnabled(False)

        # =============================================

        self.butt_save_fileout = QtGui.QPushButton("Save file", self)
        self.connect(self.butt_save_fileout, SIGNAL("pressed()"), self.butt_save_fileout_Changed)
        self.butt_save_fileout.setEnabled(False)

        # =============================================

        vbox_plots_h_butt_rec_fileout = QtGui.QHBoxLayout()
        vbox_plots_h_butt_rec_fileout.addWidget(self.butt_start_rec_fileout)
        vbox_plots_h_butt_rec_fileout.addWidget(self.butt_stop_rec_fileout)
        vbox_plots_h_butt_rec_fileout.addWidget(self.butt_save_fileout)

        # =============================================

        vbox_plots_v_save_velocity = QtGui.QVBoxLayout()
        vbox_plots_v_save_velocity.addWidget(self.txt_plots_name_fileout)
        vbox_plots_v_save_velocity.addLayout(vbox_plots_h_butt_rec_fileout)
        bound_box_save_velocity.setLayout(vbox_plots_v_save_velocity)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.checkbox_center = QtGui.QCheckBox("Move bead to center", self)
        self.checkbox_center.toggle()
        self.checkbox_center.setCheckState(Qt.Unchecked)
        self.connect(self.checkbox_center, SIGNAL("toggled(bool)"), self.butt_pow_zeroOFF_Changed)

        # =============================================

        self.checkbox_m = QtGui.QCheckBox("Save movies", self)
        self.checkbox_m.toggle()
        self.checkbox_m.setCheckState(Qt.Unchecked)

        # =============================================

        self.checkbox_write = QtGui.QCheckBox("Write letters", self)
        self.checkbox_write.toggle()
        self.checkbox_write.setCheckState(Qt.Unchecked)

        # =============================================

        vbox_plots_v_chk_c_m_w = QtGui.QVBoxLayout()
        vbox_plots_v_chk_c_m_w.addWidget(self.checkbox_center)
        vbox_plots_v_chk_c_m_w.addWidget(self.checkbox_m)
        vbox_plots_v_chk_c_m_w.addWidget(self.checkbox_write)

        # =============================================
        bound_box_bead_size = QtGui.QGroupBox()

        self.slider_plots_bead_size_1_static = QtGui.QLabel()
        self.slider_plots_bead_size_1_static.setText("18.82 um")

        self.slider_plots_bead_size = QtGui.QSlider()
        self.slider_plots_bead_size.setMinimum(1)  # bead = 18.82
        self.slider_plots_bead_size.setSingleStep(1)
        self.slider_plots_bead_size.setMaximum(2)  # bead = 41.13
        self.slider_plots_bead_size.setProperty("value", 1)
        self.slider_plots_bead_size.setOrientation(Qt.Horizontal)
        self.slider_plots_bead_size.setMaximumWidth(30)
        self.slider_bead_size_value = self.slider_plots_bead_size.value()
        self.slider_plots_bead_size.valueChanged.connect(self.slider_plots_bead_size_Changed)

        self.slider_plots_bead_size_2_static = QtGui.QLabel()
        self.slider_plots_bead_size_2_static.setText("41.13 um")

        vbox_plots_h_bead_size = QtGui.QHBoxLayout()
        vbox_plots_h_bead_size.addStretch(1)
        vbox_plots_h_bead_size.addWidget(self.slider_plots_bead_size_1_static)
        vbox_plots_h_bead_size.addWidget(self.slider_plots_bead_size)
        vbox_plots_h_bead_size.addWidget(self.slider_plots_bead_size_2_static)
        vbox_plots_h_bead_size.addStretch(1)
        bound_box_bead_size.setLayout(vbox_plots_h_bead_size)

        # =============================================

        vbox_plots_h_chk_cmw_bead_size = QtGui.QHBoxLayout()
        vbox_plots_h_chk_cmw_bead_size.addLayout(vbox_plots_v_chk_c_m_w)
        vbox_plots_h_chk_cmw_bead_size.addWidget(bound_box_bead_size)

        # =============================================
        vbox_plots_tab_letter = QtGui.QTabWidget()
        vbox_plots_tab_letter_1 = QtGui.QWidget()
        vbox_plots_tab_letter_2 = QtGui.QWidget()
        vbox_plots_tab_letter_1.setAutoFillBackground(True)
        vbox_plots_tab_letter_1.setPalette(QColor(240, 240, 240))
        vbox_plots_tab_letter_2.setAutoFillBackground(True)
        vbox_plots_tab_letter_2.setPalette(QColor(240, 240, 240))

        # QTabBar -> for changing the color of the tab as well

        vbox_plots_v_tab_letter_1 = QtGui.QVBoxLayout(vbox_plots_tab_letter_1)
        vbox_plots_v_tab_letter_2 = QtGui.QVBoxLayout(vbox_plots_tab_letter_2)

        # vbox_plots_tab_letter.addTab(vbox_plots_tab_letter_1, "Letters")
        vbox_plots_tab_letter.addTab(vbox_plots_tab_letter_2, "Seq TLaps")
        vbox_plots_tab_letter.addTab(vbox_plots_tab_letter_1, "Letters")

        self.butt_plots_letter_point = QtGui.QPushButton("Point in the letter - to move", self)
        self.connect(self.butt_plots_letter_point, SIGNAL("pressed()"), self.butt_plots_letter_point_Changed)

        self.ctrl_plots_letter_point_x_static = QtGui.QLabel()
        self.ctrl_plots_letter_point_x_static.setText(" x ")

        self.ctrl_plots_letter_point_x = QtGui.QSpinBox()
        self.ctrl_plots_letter_point_x.setMinimum(1)
        self.ctrl_plots_letter_point_x.setSingleStep(1)
        self.ctrl_plots_letter_point_x.setMaximum(5)
        self.ctrl_plots_letter_point_x.setProperty("value", 1)
        self.ctrl_plots_letter_point_x.setKeyboardTracking(False)
        # self.ctrl_plots_letter_point.valueChanged.connect(self.ctrl_pow_zDOWN_Changed)

        self.ctrl_plots_letter_point_y_static = QtGui.QLabel()
        self.ctrl_plots_letter_point_y_static.setText(" y ")

        self.ctrl_plots_letter_point_y = QtGui.QSpinBox()
        self.ctrl_plots_letter_point_y.setMinimum(1)
        self.ctrl_plots_letter_point_y.setSingleStep(1)
        self.ctrl_plots_letter_point_y.setMaximum(7)
        self.ctrl_plots_letter_point_y.setProperty("value", 1)
        self.ctrl_plots_letter_point_y.setKeyboardTracking(False)

        vbox_plots_h_ctrl_plots_letter_point = QtGui.QHBoxLayout()
        vbox_plots_h_ctrl_plots_letter_point.addWidget(self.butt_plots_letter_point)
        vbox_plots_h_ctrl_plots_letter_point.addWidget(self.ctrl_plots_letter_point_x_static)
        vbox_plots_h_ctrl_plots_letter_point.addWidget(self.ctrl_plots_letter_point_x)
        vbox_plots_h_ctrl_plots_letter_point.addWidget(self.ctrl_plots_letter_point_y_static)
        vbox_plots_h_ctrl_plots_letter_point.addWidget(self.ctrl_plots_letter_point_y)
        vbox_plots_h_ctrl_plots_letter_point.addStretch(1)

        # =============================================

        self.lab_let_point_coord_x = QtGui.QLabel()
        self.lab_let_point_coord_x_static = QtGui.QLabel()
        self.lab_let_point_coord_x_static.setText("Lett point coord x")

        self.lab_let_point_coord_y = QtGui.QLabel()
        self.lab_let_point_coord_y_static = QtGui.QLabel()
        self.lab_let_point_coord_y_static.setText("Lett point coord y")

        vbox_plots_h_lab_let_point_coord = QtGui.QHBoxLayout()
        vbox_plots_h_lab_let_point_coord.addWidget(self.lab_let_point_coord_x_static)
        vbox_plots_h_lab_let_point_coord.addStretch(1)
        vbox_plots_h_lab_let_point_coord.addWidget(self.lab_let_point_coord_x)
        vbox_plots_h_lab_let_point_coord.addStretch(1)
        vbox_plots_h_lab_let_point_coord.addWidget(self.lab_let_point_coord_y_static)
        vbox_plots_h_lab_let_point_coord.addStretch(1)
        vbox_plots_h_lab_let_point_coord.addWidget(self.lab_let_point_coord_y)
        vbox_plots_h_lab_let_point_coord.addStretch(1)

        # =============================================

        self.ctrl_plots_letter_x_static = QtGui.QLabel()
        self.ctrl_plots_letter_x_static.setText("Lett x")

        self.ctrl_plots_letter_x = QtGui.QSpinBox()
        self.ctrl_plots_letter_x.setMinimum(1)
        self.ctrl_plots_letter_x.setSingleStep(50)
        self.ctrl_plots_letter_x.setMaximum(3000)
        self.ctrl_plots_letter_x.setProperty("value", 900)
        self.ctrl_plots_letter_x.setKeyboardTracking(False)

        self.ctrl_plots_letter_y_static = QtGui.QLabel()
        self.ctrl_plots_letter_y_static.setText("Lett y")

        self.ctrl_plots_letter_y = QtGui.QSpinBox()
        self.ctrl_plots_letter_y.setMinimum(1)
        self.ctrl_plots_letter_y.setSingleStep(50)
        self.ctrl_plots_letter_y.setMaximum(2000)
        self.ctrl_plots_letter_y.setProperty("value", 600)
        self.ctrl_plots_letter_y.setKeyboardTracking(False)

        self.ctrl_plots_letter_size_static = QtGui.QLabel()
        self.ctrl_plots_letter_size_static.setText("Lett size")

        self.ctrl_plots_letter_size = QtGui.QSpinBox()
        self.ctrl_plots_letter_size.setMinimum(1)
        self.ctrl_plots_letter_size.setSingleStep(10)
        self.ctrl_plots_letter_size.setMaximum(1000)
        self.ctrl_plots_letter_size.setProperty("value", 200)
        self.ctrl_plots_letter_size.setKeyboardTracking(False)

        vbox_plots_h_ctrl_plots_letter = QtGui.QHBoxLayout()
        vbox_plots_h_ctrl_plots_letter.addWidget(self.ctrl_plots_letter_x_static)
        vbox_plots_h_ctrl_plots_letter.addWidget(self.ctrl_plots_letter_x)
        vbox_plots_h_ctrl_plots_letter.addWidget(self.ctrl_plots_letter_y_static)
        vbox_plots_h_ctrl_plots_letter.addWidget(self.ctrl_plots_letter_y)
        vbox_plots_h_ctrl_plots_letter.addWidget(self.ctrl_plots_letter_size_static)
        vbox_plots_h_ctrl_plots_letter.addWidget(self.ctrl_plots_letter_size)
        vbox_plots_h_ctrl_plots_letter.addStretch(1)

        # =============================================

        self.checkbox_diag_move = QtGui.QCheckBox("Move bead on a diagonal", self)
        self.checkbox_diag_move.toggle()
        self.checkbox_diag_move.setCheckState(Qt.Unchecked)
        self.connect(self.checkbox_diag_move, SIGNAL("toggled(bool)"), self.checkbox_diag_move_Changed)

        # =============================================

        self.lab_let_index_diag = QtGui.QLabel()
        self.lab_let_index_diag_static = QtGui.QLabel()
        self.lab_let_index_diag_static.setText("Index points diag")

        self.ctrl_plots_let_index_diag_static = QtGui.QLabel()
        self.ctrl_plots_let_index_diag_static.setText("Total points diag")

        self.ctrl_plots_let_index_diag = QtGui.QSpinBox()
        self.ctrl_plots_let_index_diag.setMinimum(1)
        self.ctrl_plots_let_index_diag.setSingleStep(1)
        self.ctrl_plots_let_index_diag.setMaximum(50)
        self.ctrl_plots_let_index_diag.setProperty("value", 10)
        self.ctrl_plots_let_index_diag.setKeyboardTracking(False)

        vbox_plots_h_ctrl_plots_let_index_diag = QtGui.QHBoxLayout()
        vbox_plots_h_ctrl_plots_let_index_diag.addWidget(self.lab_let_index_diag_static)
        vbox_plots_h_ctrl_plots_let_index_diag.addWidget(self.lab_let_index_diag)
        vbox_plots_h_ctrl_plots_let_index_diag.addWidget(self.ctrl_plots_let_index_diag_static)
        vbox_plots_h_ctrl_plots_let_index_diag.addWidget(self.ctrl_plots_let_index_diag)
        vbox_plots_h_ctrl_plots_let_index_diag.addStretch(1)

        # =============================================

        vbox_plots_v_tab_letter_1.addLayout(vbox_plots_h_ctrl_plots_letter_point)
        vbox_plots_v_tab_letter_1.addLayout(vbox_plots_h_lab_let_point_coord)
        vbox_plots_v_tab_letter_1.addLayout(vbox_plots_h_ctrl_plots_letter)
        vbox_plots_v_tab_letter_1.addWidget(self.checkbox_diag_move)
        vbox_plots_v_tab_letter_1.addLayout(vbox_plots_h_ctrl_plots_let_index_diag)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        self.butt_plots_tab_letter_seq_tlaps_start = QtGui.QPushButton("Start SEQ", self)
        self.connect(self.butt_plots_tab_letter_seq_tlaps_start, SIGNAL("pressed()"),
                     self.butt_plots_tab_letter_seq_tlaps_start_Changed)
        self.seq_time_laps_run = False

        # ==============================================

        self.butt_plots_tab_letter_seq_tlaps_stop = QtGui.QPushButton("Stop SEQ", self)
        self.connect(self.butt_plots_tab_letter_seq_tlaps_stop, SIGNAL("pressed()"),
                     self.butt_plots_tab_letter_seq_tlaps_stop_Changed)
        self.butt_plots_tab_letter_seq_tlaps_stop.setEnabled(False)

        vbox_plots_h_butt_tab_lett_seq_start_stop = QtGui.QHBoxLayout()
        vbox_plots_h_butt_tab_lett_seq_start_stop.addWidget(self.butt_plots_tab_letter_seq_tlaps_start)
        vbox_plots_h_butt_tab_lett_seq_start_stop.addStretch(1)
        vbox_plots_h_butt_tab_lett_seq_start_stop.addWidget(self.butt_plots_tab_letter_seq_tlaps_stop)

        # =============================================

        vbox_plots_v_tab_letter_2.addLayout(vbox_plots_h_butt_tab_lett_seq_start_stop)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.plot_1 = pg.PlotWidget()
        self.plot_1.setMaximumHeight(225)
        self.plot_1.setMaximumWidth(300)
        # self.plot_1.showGrid(x=True, y=True)
        # self.xxx = np.random.normal(size=100)
        # self.yyy = np.random.normal(size=100)
        self.xxx = [0.0]
        self.yyy = [0.0]
        self.yyy_2 = [0.0]
        self.p1 = self.plot_1.plot()
        self.p1.setPen((200, 200, 100))
        # self.p2 = self.plot_1.plot()
        # self.p2.setPen((100,200,100))
        self.p1.setData(x=self.xxx, y=self.yyy)
        # self.p1.setData(x=self.xxx, y=self.yyy_2)

        # =============================================

        # self.plot_2 = pg.PlotWidget()
        # self.plot_2.setMaximumHeight(225)
        # self.plot_2.setMaximumWidth(300)
        # self.p2 = self.plot_2.plot()
        # self.p2.setPen((100,200,100))

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.ctrl_plots_z_bead_bottom_static = QtGui.QLabel()
        self.ctrl_plots_z_bead_bottom_static.setText("z bottom (oil)/mm")

        self.ctrl_plots_z_bead_bottom = QtGui.QDoubleSpinBox()
        self.ctrl_plots_z_bead_bottom.setMinimum(0.0)
        self.ctrl_plots_z_bead_bottom.setSingleStep(0.1)
        self.ctrl_plots_z_bead_bottom.setMaximum(24.0)
        self.ctrl_plots_z_bead_bottom.setDecimals(5)
        self.ctrl_plots_z_bead_bottom.setProperty("value", 5.0)
        self.ctrl_plots_z_bead_bottom.setKeyboardTracking(False)
        self.z_bead_bottom = self.ctrl_plots_z_bead_bottom.value()
        self.ctrl_plots_z_bead_bottom.valueChanged.connect(self.ctrl_plots_z_bead_bottom_Changed)

        self.ctrl_plots_shift_spim_static = QtGui.QLabel()
        self.ctrl_plots_shift_spim_static.setText("Offset SPIM (um)")

        self.ctrl_plots_shift_spim = QtGui.QDoubleSpinBox()
        self.ctrl_plots_shift_spim.setMinimum(0.0)
        self.ctrl_plots_shift_spim.setSingleStep(5.0)
        self.ctrl_plots_shift_spim.setMaximum(500.0)
        self.ctrl_plots_shift_spim.setDecimals(1)
        self.ctrl_plots_shift_spim.setProperty("value", 100.0)
        self.ctrl_plots_shift_spim.setKeyboardTracking(False)
        self.shift_spim = self.ctrl_plots_shift_spim.value()
        self.ctrl_plots_shift_spim.valueChanged.connect(self.ctrl_plots_shift_spim_Changed)
        self.ctrl_plots_z_bead_bottom_static = QtGui.QLabel()
        self.ctrl_plots_z_bead_bottom_static.setText("z bottom (oil)/mm")

        self.ctrl_plots_z_bead_bottom = QtGui.QDoubleSpinBox()
        self.ctrl_plots_z_bead_bottom.setMinimum(0.0)
        self.ctrl_plots_z_bead_bottom.setSingleStep(0.1)
        self.ctrl_plots_z_bead_bottom.setMaximum(24.0)
        self.ctrl_plots_z_bead_bottom.setDecimals(5)
        self.ctrl_plots_z_bead_bottom.setProperty("value", 5.0)
        self.ctrl_plots_z_bead_bottom.setKeyboardTracking(False)
        self.z_bead_bottom = self.ctrl_plots_z_bead_bottom.value()
        self.ctrl_plots_z_bead_bottom.valueChanged.connect(self.ctrl_plots_z_bead_bottom_Changed)

        self.ctrl_plots_shift_spim_static = QtGui.QLabel()
        self.ctrl_plots_shift_spim_static.setText("Offset SPIM (um)")

        self.ctrl_plots_shift_spim = QtGui.QDoubleSpinBox()
        self.ctrl_plots_shift_spim.setMinimum(0.0)
        self.ctrl_plots_shift_spim.setSingleStep(5.0)
        self.ctrl_plots_shift_spim.setMaximum(500.0)
        self.ctrl_plots_shift_spim.setDecimals(1)
        self.ctrl_plots_shift_spim.setProperty("value", 100.0)
        self.ctrl_plots_shift_spim.setKeyboardTracking(False)
        self.shift_spim = self.ctrl_plots_shift_spim.value()
        self.ctrl_plots_shift_spim.valueChanged.connect(self.ctrl_plots_shift_spim_Changed)

        vbox_plots_h_ctrl_plots_z_bottom = QtGui.QHBoxLayout()
        vbox_plots_h_ctrl_plots_z_bottom.addWidget(self.ctrl_plots_z_bead_bottom_static)
        vbox_plots_h_ctrl_plots_z_bottom.addWidget(self.ctrl_plots_z_bead_bottom)
        vbox_plots_h_ctrl_plots_z_bottom.addStretch(1)
        vbox_plots_h_ctrl_plots_z_bottom.addWidget(self.ctrl_plots_shift_spim_static)
        vbox_plots_h_ctrl_plots_z_bottom.addWidget(self.ctrl_plots_shift_spim)

        # =============================================

        self.ctrl_plots_lenght_spim_volume_static = QtGui.QLabel()
        self.ctrl_plots_lenght_spim_volume_static.setText("SPIM half xz(100+532)/sq(2) y(532) (um)")

        self.ctrl_plots_lenght_spim_volume_xz = QtGui.QDoubleSpinBox()
        self.ctrl_plots_lenght_spim_volume_xz.setMinimum(0.0)
        self.ctrl_plots_lenght_spim_volume_xz.setSingleStep(50.0)
        self.ctrl_plots_lenght_spim_volume_xz.setMaximum(500.0)
        self.ctrl_plots_lenght_spim_volume_xz.setDecimals(1)
        self.ctrl_plots_lenght_spim_volume_xz.setProperty("value", 224.0)
        self.ctrl_plots_lenght_spim_volume_xz.setKeyboardTracking(False)
        self.lenght_spim_xz = self.ctrl_plots_lenght_spim_volume_xz.value()
        self.ctrl_plots_lenght_spim_volume_xz.valueChanged.connect(self.ctrl_plots_lenght_spim_volume_Changed)

        self.ctrl_plots_lenght_spim_volume_y = QtGui.QDoubleSpinBox()
        self.ctrl_plots_lenght_spim_volume_y.setMinimum(0.0)
        self.ctrl_plots_lenght_spim_volume_y.setSingleStep(50.0)
        self.ctrl_plots_lenght_spim_volume_y.setMaximum(500.0)
        self.ctrl_plots_lenght_spim_volume_y.setDecimals(1)
        self.ctrl_plots_lenght_spim_volume_y.setProperty("value", 270.0)
        self.ctrl_plots_lenght_spim_volume_y.setKeyboardTracking(False)
        self.lenght_spim_y = self.ctrl_plots_lenght_spim_volume_y.value()
        self.ctrl_plots_lenght_spim_volume_y.valueChanged.connect(self.ctrl_plots_lenght_spim_volume_Changed)

        self.ctrl_plots_lenght_spim_volume_Changed()

        vbox_plots_h_ctrl_plots_l_spim = QtGui.QHBoxLayout()
        vbox_plots_h_ctrl_plots_l_spim.addWidget(self.ctrl_plots_lenght_spim_volume_static)
        vbox_plots_h_ctrl_plots_l_spim.addWidget(self.ctrl_plots_lenght_spim_volume_xz)
        vbox_plots_h_ctrl_plots_l_spim.addStretch(1)
        vbox_plots_h_ctrl_plots_l_spim.addWidget(self.ctrl_plots_lenght_spim_volume_y)
        vbox_plots_h_ctrl_plots_l_spim.addStretch(1)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_plots_z_cent_oil_static = QtGui.QLabel()
        self.lab_plots_z_cent_oil_static.setText("z centre oil (mm)")

        self.lab_plots_z_cent_air_static = QtGui.QLabel()
        self.lab_plots_z_cent_air_static.setText("z centre air (mm)")

        vbox_plots_h_lab_z_o_a_static = QtGui.QHBoxLayout()
        vbox_plots_h_lab_z_o_a_static.addWidget(self.lab_plots_z_cent_oil_static)
        vbox_plots_h_lab_z_o_a_static.addStretch(1)
        vbox_plots_h_lab_z_o_a_static.addWidget(self.lab_plots_z_cent_air_static)

        # ==============================================

        self.lab_plots_z_cent_oil = QtGui.QLabel()

        self.lab_plots_z_cent_air = QtGui.QLabel()

        vbox_plots_h_lab_z_o_a = QtGui.QHBoxLayout()
        vbox_plots_h_lab_z_o_a.addWidget(self.lab_plots_z_cent_oil)
        vbox_plots_h_lab_z_o_a.addStretch(1)
        vbox_plots_h_lab_z_o_a.addWidget(self.lab_plots_z_cent_air)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_plots_z_spim_min_oil_static = QtGui.QLabel()
        self.lab_plots_z_spim_min_oil_static.setText("SPIM (oil) z min")

        self.lab_plots_z_spim_max_oil_static = QtGui.QLabel()
        self.lab_plots_z_spim_max_oil_static.setText("z max")

        self.lab_plots_z_spim_min_air_static = QtGui.QLabel()
        self.lab_plots_z_spim_min_air_static.setText("SPIM (air) z min")

        self.lab_plots_z_spim_max_air_static = QtGui.QLabel()
        self.lab_plots_z_spim_max_air_static.setText("z max")

        vbox_plots_h_lab_z_spim_static = QtGui.QHBoxLayout()
        vbox_plots_h_lab_z_spim_static.addWidget(self.lab_plots_z_spim_min_oil_static)
        vbox_plots_h_lab_z_spim_static.addStretch(1)
        vbox_plots_h_lab_z_spim_static.addWidget(self.lab_plots_z_spim_max_oil_static)
        vbox_plots_h_lab_z_spim_static.addStretch(1)
        vbox_plots_h_lab_z_spim_static.addWidget(self.lab_plots_z_spim_min_air_static)
        vbox_plots_h_lab_z_spim_static.addStretch(1)
        vbox_plots_h_lab_z_spim_static.addWidget(self.lab_plots_z_spim_max_air_static)

        # ==============================================

        self.lab_plots_z_spim_min_oil = QtGui.QLabel()

        self.lab_plots_z_spim_max_oil = QtGui.QLabel()

        self.lab_plots_z_spim_min_air = QtGui.QLabel()

        self.lab_plots_z_spim_max_air = QtGui.QLabel()

        vbox_plots_h_lab_z_spim = QtGui.QHBoxLayout()
        vbox_plots_h_lab_z_spim.addWidget(self.lab_plots_z_spim_min_oil)
        vbox_plots_h_lab_z_spim.addStretch(1)
        vbox_plots_h_lab_z_spim.addWidget(self.lab_plots_z_spim_max_oil)
        vbox_plots_h_lab_z_spim.addStretch(1)
        vbox_plots_h_lab_z_spim.addWidget(self.lab_plots_z_spim_min_air)
        vbox_plots_h_lab_z_spim.addStretch(1)
        vbox_plots_h_lab_z_spim.addWidget(self.lab_plots_z_spim_max_air)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_plots = QtGui.QVBoxLayout()
        vbox_plots.addWidget(self.lab_plots_static)
        # vbox_plots.addWidget(self.butt_reset_clock)
        vbox_plots.addLayout(vbox_plots_h_butt_r_s_s)
        vbox_plots.addWidget(bound_box_save_img)
        vbox_plots.addStretch(1)
        vbox_plots.addLayout(vbox_plots_h_ctrl_exposure_time)
        vbox_plots.addStretch(1)
        vbox_plots.addWidget(bound_box_save_velocity)
        # vbox_plots.addWidget(self.checkbox_center)
        # vbox_plots.addWidget(self.checkbox_m)
        # vbox_plots.addWidget(self.checkbox_write)
        vbox_plots.addLayout(vbox_plots_h_chk_cmw_bead_size)
        vbox_plots.addWidget(vbox_plots_tab_letter)
        # vbox_plots.addLayout(vbox_plots_h_ctrl_plots_letter_point)
        # vbox_plots.addLayout(vbox_plots_h_lab_let_point_coord)
        # vbox_plots.addLayout(vbox_plots_h_ctrl_plots_letter)
        # vbox_plots.addWidget(self.checkbox_diag_move)
        # vbox_plots.addLayout(vbox_plots_h_ctrl_plots_let_index_diag)
        vbox_plots.addStretch(1)
        vbox_plots.addWidget(self.plot_1)
        vbox_plots.addStretch(1)
        # vbox_plots.addWidget(self.ctrl_plots_z_bead_bottom)
        vbox_plots.addLayout(vbox_plots_h_ctrl_plots_z_bottom)
        vbox_plots.addLayout(vbox_plots_h_ctrl_plots_l_spim)
        vbox_plots.addStretch(1)
        vbox_plots.addLayout(vbox_plots_h_lab_z_o_a_static)
        vbox_plots.addLayout(vbox_plots_h_lab_z_o_a)
        vbox_plots.addStretch(1)
        vbox_plots.addLayout(vbox_plots_h_lab_z_spim_static)
        vbox_plots.addLayout(vbox_plots_h_lab_z_spim)

        # vbox_plots.addWidget(self.plot_2)
        # vbox_plots.addStretch(1)
        bound_box_plots.setLayout(vbox_plots)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_vi = QtGui.QGroupBox()
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_video_static = QtGui.QLabel()
        self.lab_video_static.setText("V   I   D   E   O")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.checkbox_trig_on_off = QtGui.QCheckBox("Triggering", self)
        self.checkbox_trig_on_off.toggle()
        self.checkbox_trig_on_off.setCheckState(Qt.Checked)
        self.connect(self.checkbox_trig_on_off, SIGNAL("toggled(bool)"), self.chbox_trig_on_off_Changed)

        # =============================================

        self.ctrl_FPS_static = QtGui.QLabel()
        self.ctrl_FPS_static.setText("FPS ")

        self.ctrl_FPS = QtGui.QDoubleSpinBox()
        self.ctrl_FPS.setMinimum(0.001)
        self.ctrl_FPS.setSingleStep(1.0)
        self.ctrl_FPS.setMaximum(13.0)
        self.ctrl_FPS.setProperty("value", 10.0)
        self.ctrl_FPS.setDecimals(3)
        self.FPS_factor = self.ctrl_FPS.value()
        self.ctrl_FPS.setKeyboardTracking(False)
        self.ctrl_FPS.valueChanged.connect(self.ctrl_FPS_Changed)
        ser_trig.write('FPS ' + str(self.FPS_factor) + '\r\n')
        ser_trig.write('ON_Trig' + '\r\n')

        vbox_vi_h_ctrl_fps = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_fps.addWidget(self.ctrl_FPS_static)
        vbox_vi_h_ctrl_fps.addWidget(self.ctrl_FPS)

        # =============================================

        self.lab_real_FPS = QtGui.QLabel()
        self.lab_real_FPS_static = QtGui.QLabel()
        self.lab_real_FPS_static.setText("Actual FPS ")

        self.real_FPS = round(1000.0 / (2.0 * round(1000.0 / self.FPS_factor / 2.0, 0)), 3)
        self.lab_real_FPS.setText(str(self.real_FPS))

        vbox_vi_h_lab_real_FPS = QtGui.QHBoxLayout()
        vbox_vi_h_lab_real_FPS.addWidget(self.lab_real_FPS_static)
        vbox_vi_h_lab_real_FPS.addWidget(self.lab_real_FPS)

        # =============================================

        self.lab_delta_t = QtGui.QLabel()
        self.lab_delta_t_static = QtGui.QLabel()
        self.lab_delta_t_static.setText("Delta t (ms) ")

        self.delta_t = 2.0 * round(1000.0 / self.FPS_factor / 2.0, 0)
        self.lab_delta_t.setText(str(self.delta_t))

        vbox_vi_h_lab_delta_t = QtGui.QHBoxLayout()
        vbox_vi_h_lab_delta_t.addWidget(self.lab_delta_t_static)
        vbox_vi_h_lab_delta_t.addWidget(self.lab_delta_t)

        # =============================================

        self.lab_measured_fps = QtGui.QLabel()
        self.lab_measured_fps_static = QtGui.QLabel()
        self.lab_measured_fps_static.setText("F P S = ")

        self.measured_fps = self.FPS_factor
        self.lab_measured_fps.setText(str(self.measured_fps))

        vbox_vi_h_lab_measure_fps = QtGui.QHBoxLayout()
        vbox_vi_h_lab_measure_fps.addWidget(self.lab_measured_fps_static)
        vbox_vi_h_lab_measure_fps.addWidget(self.lab_measured_fps)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_light_ON = QtGui.QPushButton("LED ON ", self)
        self.connect(self.butt_light_ON, SIGNAL("pressed()"), self.butt_light_ON_Changed)
        self.butt_light_ON.setEnabled(False)

        # =============================================

        self.butt_light_OFF = QtGui.QPushButton("LED OFF ", self)
        self.connect(self.butt_light_OFF, SIGNAL("pressed()"), self.butt_light_OFF_Changed)
        self.butt_light_OFF.setEnabled(False)

        vbox_vi_h_butt_light = QtGui.QHBoxLayout()
        vbox_vi_h_butt_light.addWidget(self.butt_light_ON)
        vbox_vi_h_butt_light.addWidget(self.butt_light_OFF)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_temperature = QtGui.QLabel()
        self.lab_temperature_static = QtGui.QLabel()
        self.lab_temperature_static.setText("Temp (C)")

        self.lab_temperature3 = QtGui.QLabel()  # 3rd sensor

        vbox_vi_h_lab_temperature = QtGui.QHBoxLayout()
        vbox_vi_h_lab_temperature.addWidget(self.lab_temperature_static)
        vbox_vi_h_lab_temperature.addWidget(self.lab_temperature)
        vbox_vi_h_lab_temperature.addWidget(self.lab_temperature3)  # 3rd sensor

        # =============================================

        self.lab_temperature_coil = QtGui.QLabel()
        self.lab_temperature_coil_static = QtGui.QLabel()
        self.lab_temperature_coil_static.setText("Temp coil (C)")

        # self.lab_temperature4 = QtGui.QLabel()  #  4th sensor

        vbox_vi_h_lab_temperature_coil = QtGui.QHBoxLayout()
        vbox_vi_h_lab_temperature_coil.addWidget(self.lab_temperature_coil_static)
        vbox_vi_h_lab_temperature_coil.addWidget(self.lab_temperature_coil)
        # vbox_vi_h_lab_temperature_coil.addWidget(self.lab_temperature4) # 4th sensor

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.checkbox_p = QtGui.QCheckBox("Show BIG picture", self)
        self.checkbox_p.toggle()
        # self.checkbox_p.setCheckState( Qt.Unchecked )
        self.checkbox_p.setCheckState(Qt.Checked)

        # =============================================

        self.checkbox_t = QtGui.QCheckBox("Show threshold", self)
        self.checkbox_t.toggle()
        self.checkbox_t.setCheckState(Qt.Unchecked)

        # =============================================

        self.checkbox_b = QtGui.QCheckBox("Detect beads", self)
        self.checkbox_b.toggle()
        self.checkbox_b.setCheckState(Qt.Unchecked)

        self.checkbox_ref_bead = QtGui.QCheckBox("Ref b.", self)
        self.checkbox_ref_bead.toggle()
        self.checkbox_ref_bead.setCheckState(Qt.Unchecked)

        vbox_vi_h_b_ref = QtGui.QHBoxLayout()
        vbox_vi_h_b_ref.addWidget(self.checkbox_b)
        vbox_vi_h_b_ref.addStretch()
        vbox_vi_h_b_ref.addWidget(self.checkbox_ref_bead)

        # =============================================

        self.checkbox_diff = QtGui.QCheckBox("Diff images", self)
        self.checkbox_diff.toggle()
        self.checkbox_diff.setCheckState(Qt.Unchecked)

        self.checkbox_XZ_section = QtGui.QCheckBox("XZ slice", self)
        self.checkbox_XZ_section.toggle()
        self.checkbox_XZ_section.setCheckState(Qt.Unchecked)

        vbox_vi_h_diff_xz = QtGui.QHBoxLayout()
        vbox_vi_h_diff_xz.addWidget(self.checkbox_diff)
        vbox_vi_h_diff_xz.addStretch()
        vbox_vi_h_diff_xz.addWidget(self.checkbox_XZ_section)

        # =============================================

        self.checkbox_grid = QtGui.QCheckBox("Show grid", self)
        self.checkbox_grid.toggle()
        self.checkbox_grid.setCheckState(Qt.Checked)

        self.checkbox_spim_box = QtGui.QCheckBox("SPIM box", self)
        self.checkbox_spim_box.toggle()
        self.checkbox_spim_box.setCheckState(Qt.Unchecked)

        vbox_vi_h_chbox_grids = QtGui.QHBoxLayout()
        vbox_vi_h_chbox_grids.addWidget(self.checkbox_grid)
        vbox_vi_h_chbox_grids.addStretch(1)
        vbox_vi_h_chbox_grids.addWidget(self.checkbox_spim_box)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.ctrl_L_grid_static = QtGui.QLabel()
        self.ctrl_L_grid_static.setText("Grid size ")

        self.ctrl_L_grid = QtGui.QSpinBox()
        self.ctrl_L_grid.setMinimum(0)
        self.ctrl_L_grid.setSingleStep(200)
        self.ctrl_L_grid.setMaximum(1300)
        self.ctrl_L_grid.setProperty("value", 1100)
        self.size_grid = self.ctrl_L_grid.value()
        self.ctrl_L_grid.setKeyboardTracking(False)
        self.ctrl_L_grid.valueChanged.connect(self.ctrl_L_grid_Changed)

        vbox_vi_h_ctrl_grid = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_grid.addWidget(self.ctrl_L_grid_static)
        vbox_vi_h_ctrl_grid.addWidget(self.ctrl_L_grid)

        # =============================================

        self.ctrl_zoom_static = QtGui.QLabel()
        self.ctrl_zoom_static.setText("Zoom ")

        self.ctrl_zoom = QtGui.QDoubleSpinBox()
        self.ctrl_zoom.setMinimum(0.8)
        self.ctrl_zoom.setSingleStep(1.0)
        self.ctrl_zoom.setMaximum(25.0)
        self.ctrl_zoom.setProperty("value", 6.0)
        self.ctrl_zoom.setDecimals(2)
        self.zoom_factor = self.ctrl_zoom.value()
        self.ctrl_zoom.setKeyboardTracking(False)
        self.ctrl_zoom.valueChanged.connect(self.ctrl_zoom_Changed)

        vbox_vi_h_ctrl_zoom = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_zoom.addWidget(self.ctrl_zoom_static)
        vbox_vi_h_ctrl_zoom.addWidget(self.ctrl_zoom)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_static_min_max_1 = QtGui.QLabel()
        self.lab_static_min_max_1.setText("        ")
        self.lab_static_min_max_2 = QtGui.QLabel()
        self.lab_static_min_max_2.setText("Min")
        self.lab_static_min_max_3 = QtGui.QLabel()
        self.lab_static_min_max_3.setText("Max")

        vbox_vi_h_lab_min_max = QtGui.QHBoxLayout()  # Horizontal layout
        vbox_vi_h_lab_min_max.addWidget(self.lab_static_min_max_1)
        vbox_vi_h_lab_min_max.addWidget(self.lab_static_min_max_2)
        vbox_vi_h_lab_min_max.addWidget(self.lab_static_min_max_3)

        # ==============================================

        self.ctrl_area_static = QtGui.QLabel()
        self.ctrl_area_static.setText("Area ")

        self.ctrl_area_min = QtGui.QSpinBox()
        self.ctrl_area_min.setMinimum(1)
        self.ctrl_area_min.setSingleStep(10)
        self.ctrl_area_min.setMaximum(10000)
        self.ctrl_area_min.setProperty("value", 600)
        self.area_factor_min = self.ctrl_area_min.value()
        self.ctrl_area_min.setKeyboardTracking(False)
        self.ctrl_area_min.valueChanged.connect(self.ctrl_area_min_Changed)

        self.ctrl_area_max = QtGui.QSpinBox()
        self.ctrl_area_max.setMinimum(100)
        self.ctrl_area_max.setSingleStep(100)
        self.ctrl_area_max.setMaximum(10000)
        self.ctrl_area_max.setProperty("value", 1500)
        self.area_factor_max = self.ctrl_area_max.value()
        self.ctrl_area_max.setKeyboardTracking(False)
        self.ctrl_area_max.valueChanged.connect(self.ctrl_area_max_Changed)

        vbox_vi_h_ctrl_area = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_area.addWidget(self.ctrl_area_static)
        vbox_vi_h_ctrl_area.addWidget(self.ctrl_area_min)
        vbox_vi_h_ctrl_area.addWidget(self.ctrl_area_max)

        # ==============================================

        self.ctrl_circ_static = QtGui.QLabel()
        self.ctrl_circ_static.setText("Circularity ")

        self.ctrl_circ_min = QtGui.QDoubleSpinBox()
        self.ctrl_circ_min.setMinimum(0.5)
        self.ctrl_circ_min.setSingleStep(0.01)
        self.ctrl_circ_min.setMaximum(1.5)
        self.ctrl_circ_min.setProperty("value", 0.8)
        self.c_factor_min = self.ctrl_circ_min.value()
        self.ctrl_circ_min.setKeyboardTracking(False)
        self.ctrl_circ_min.valueChanged.connect(self.ctrl_circ_min_Changed)

        self.ctrl_circ_max = QtGui.QDoubleSpinBox()
        self.ctrl_circ_max.setMinimum(0.5)
        self.ctrl_circ_max.setSingleStep(0.01)
        self.ctrl_circ_max.setMaximum(1.5)
        self.ctrl_circ_max.setProperty("value", 1.23)
        self.c_factor_max = self.ctrl_circ_max.value()
        self.ctrl_circ_max.setKeyboardTracking(False)
        self.ctrl_circ_max.valueChanged.connect(self.ctrl_circ_max_Changed)

        vbox_vi_h_ctrl_circ = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_circ.addWidget(self.ctrl_circ_static)
        vbox_vi_h_ctrl_circ.addWidget(self.ctrl_circ_min)
        vbox_vi_h_ctrl_circ.addWidget(self.ctrl_circ_max)

        # ==============================================

        self.ctrl_ths_static = QtGui.QLabel()
        self.ctrl_ths_static.setText("Threshold 1 ")

        self.ctrl_ths_min = QtGui.QSpinBox()
        self.ctrl_ths_min.setMinimum(1)
        self.ctrl_ths_min.setSingleStep(1)
        self.ctrl_ths_min.setMaximum(255)
        self.ctrl_ths_min.setProperty("value", 80)
        self.threshMin = self.ctrl_ths_min.value()
        self.ctrl_ths_min.setKeyboardTracking(False)
        self.ctrl_ths_min.valueChanged.connect(self.ctrl_ths_min_Changed)

        self.ctrl_ths_max = QtGui.QSpinBox()
        self.ctrl_ths_max.setMinimum(1)
        self.ctrl_ths_max.setSingleStep(10)
        self.ctrl_ths_max.setMaximum(255)
        self.ctrl_ths_max.setProperty("value", 250)
        self.threshMax = self.ctrl_ths_max.value()
        self.ctrl_ths_max.setKeyboardTracking(False)
        self.ctrl_ths_max.valueChanged.connect(self.ctrl_ths_max_Changed)

        vbox_vi_h_ctrl_ths = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_ths.addWidget(self.ctrl_ths_static)
        vbox_vi_h_ctrl_ths.addWidget(self.ctrl_ths_min)
        vbox_vi_h_ctrl_ths.addWidget(self.ctrl_ths_max)

        # ==============================================

        self.ctrl_ths_2_static = QtGui.QLabel()
        self.ctrl_ths_2_static.setText("Threshold 2 ")

        self.ctrl_ths_2_min = QtGui.QSpinBox()
        self.ctrl_ths_2_min.setMinimum(1)
        self.ctrl_ths_2_min.setSingleStep(1)
        self.ctrl_ths_2_min.setMaximum(255)
        self.ctrl_ths_2_min.setProperty("value", 80)
        self.threshMin_2 = self.ctrl_ths_2_min.value()
        self.ctrl_ths_2_min.setKeyboardTracking(False)
        self.ctrl_ths_2_min.valueChanged.connect(self.ctrl_ths_2_min_Changed)

        self.ctrl_ths_2_max = QtGui.QSpinBox()
        self.ctrl_ths_2_max.setMinimum(1)
        self.ctrl_ths_2_max.setSingleStep(10)
        self.ctrl_ths_2_max.setMaximum(255)
        self.ctrl_ths_2_max.setProperty("value", 250)
        self.threshMax_2 = self.ctrl_ths_2_max.value()
        self.ctrl_ths_2_max.setKeyboardTracking(False)
        self.ctrl_ths_2_max.valueChanged.connect(self.ctrl_ths_2_max_Changed)

        vbox_vi_h_ctrl_ths_2 = QtGui.QHBoxLayout()
        vbox_vi_h_ctrl_ths_2.addWidget(self.ctrl_ths_2_static)
        vbox_vi_h_ctrl_ths_2.addWidget(self.ctrl_ths_2_min)
        vbox_vi_h_ctrl_ths_2.addWidget(self.ctrl_ths_2_max)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_focus = QtGui.QLabel()
        self.lab_focus_static = QtGui.QLabel()
        self.lab_focus_static.setText("Focus 1")

        vbox_vi_h_lab_focus = QtGui.QHBoxLayout()
        vbox_vi_h_lab_focus.addWidget(self.lab_focus_static)
        vbox_vi_h_lab_focus.addWidget(self.lab_focus)

        # ==============================================

        self.lab_round_static = QtGui.QLabel()
        self.lab_round_static.setText("Round 1")
        self.lab_round = QtGui.QLabel()

        vbox_vi_h_lab_round = QtGui.QHBoxLayout()
        vbox_vi_h_lab_round.addWidget(self.lab_round_static)
        vbox_vi_h_lab_round.addWidget(self.lab_round)

        # ==============================================

        self.lab_bead = QtGui.QLabel()
        self.lab_bead_static = QtGui.QLabel()
        self.lab_bead_static.setText("No of beads 1")

        vbox_vi_h_lab_bead = QtGui.QHBoxLayout()
        vbox_vi_h_lab_bead.addWidget(self.lab_bead_static)
        vbox_vi_h_lab_bead.addWidget(self.lab_bead)

        # ==============================================

        self.lab_center_x = QtGui.QLabel()
        self.lab_center_x_static = QtGui.QLabel()
        self.lab_center_x_static.setText("Center x 1")

        vbox_vi_h_lab_center_x = QtGui.QHBoxLayout()
        vbox_vi_h_lab_center_x.addWidget(self.lab_center_x_static)
        vbox_vi_h_lab_center_x.addWidget(self.lab_center_x)

        # ==============================================

        self.lab_center_y = QtGui.QLabel()
        self.lab_center_y_static = QtGui.QLabel()
        self.lab_center_y_static.setText("Center y 1")

        vbox_vi_h_lab_center_y = QtGui.QHBoxLayout()
        vbox_vi_h_lab_center_y.addWidget(self.lab_center_y_static)
        vbox_vi_h_lab_center_y.addWidget(self.lab_center_y)

        # ==============================================

        self.lab_width = QtGui.QLabel()
        self.lab_width_static = QtGui.QLabel()
        self.lab_width_static.setText("Width 1")

        vbox_vi_h_lab_width = QtGui.QHBoxLayout()
        vbox_vi_h_lab_width.addWidget(self.lab_width_static)
        vbox_vi_h_lab_width.addWidget(self.lab_width)

        # ==============================================

        self.lab_height = QtGui.QLabel()
        self.lab_height_static = QtGui.QLabel()
        self.lab_height_static.setText("Height 1")

        vbox_vi_h_lab_height = QtGui.QHBoxLayout()
        vbox_vi_h_lab_height.addWidget(self.lab_height_static)
        vbox_vi_h_lab_height.addWidget(self.lab_height)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_focus_2 = QtGui.QLabel()
        self.lab_focus_2_static = QtGui.QLabel()
        self.lab_focus_2_static.setText("Focus 2")

        vbox_vi_h_lab_focus_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_focus_2.addWidget(self.lab_focus_2_static)
        vbox_vi_h_lab_focus_2.addWidget(self.lab_focus_2)

        # ==============================================

        self.lab_round_2_static = QtGui.QLabel()
        self.lab_round_2_static.setText("Round 2")
        self.lab_round_2 = QtGui.QLabel()

        vbox_vi_h_lab_round_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_round_2.addWidget(self.lab_round_2_static)
        vbox_vi_h_lab_round_2.addWidget(self.lab_round_2)

        # ==============================================

        self.lab_bead_2 = QtGui.QLabel()
        self.lab_bead_2_static = QtGui.QLabel()
        self.lab_bead_2_static.setText("No of beads 2")

        vbox_vi_h_lab_bead_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_bead_2.addWidget(self.lab_bead_2_static)
        vbox_vi_h_lab_bead_2.addWidget(self.lab_bead_2)

        # ==============================================

        self.lab_center_x_2 = QtGui.QLabel()
        self.lab_center_x_2_static = QtGui.QLabel()
        self.lab_center_x_2_static.setText("Center x 2")

        vbox_vi_h_lab_center_x_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_center_x_2.addWidget(self.lab_center_x_2_static)
        vbox_vi_h_lab_center_x_2.addWidget(self.lab_center_x_2)

        # ==============================================

        self.lab_center_y_2 = QtGui.QLabel()
        self.lab_center_y_2_static = QtGui.QLabel()
        self.lab_center_y_2_static.setText("Center y 2")

        vbox_vi_h_lab_center_y_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_center_y_2.addWidget(self.lab_center_y_2_static)
        vbox_vi_h_lab_center_y_2.addWidget(self.lab_center_y_2)

        # ==============================================

        self.lab_width_2 = QtGui.QLabel()
        self.lab_width_2_static = QtGui.QLabel()
        self.lab_width_2_static.setText("Width 2")

        vbox_vi_h_lab_width_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_width_2.addWidget(self.lab_width_2_static)
        vbox_vi_h_lab_width_2.addWidget(self.lab_width_2)

        # ==============================================

        self.lab_height_2 = QtGui.QLabel()
        self.lab_height_2_static = QtGui.QLabel()
        self.lab_height_2_static.setText("Height 2")

        vbox_vi_h_lab_height_2 = QtGui.QHBoxLayout()
        vbox_vi_h_lab_height_2.addWidget(self.lab_height_2_static)
        vbox_vi_h_lab_height_2.addWidget(self.lab_height_2)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.dim__text = QtGui.QFont()
        self.dim__text.setPixelSize(16)

        self.lab_delta_x = QtGui.QLabel()
        self.lab_delta_x_static = QtGui.QLabel()
        self.lab_delta_x_static.setText("Delta X")
        self.lab_delta_x_static.setFont(self.dim__text)
        self.lab_delta_x.setFont(self.dim__text)

        vbox_vi_h_lab_delta_x = QtGui.QHBoxLayout()
        vbox_vi_h_lab_delta_x.addWidget(self.lab_delta_x_static)
        vbox_vi_h_lab_delta_x.addWidget(self.lab_delta_x)

        # ==============================================

        self.lab_delta_y = QtGui.QLabel()
        self.lab_delta_y_static = QtGui.QLabel()
        self.lab_delta_y_static.setText("Delta Y")
        self.lab_delta_y_static.setFont(self.dim__text)
        self.lab_delta_y.setFont(self.dim__text)

        vbox_vi_h_lab_delta_y = QtGui.QHBoxLayout()
        vbox_vi_h_lab_delta_y.addWidget(self.lab_delta_y_static)
        vbox_vi_h_lab_delta_y.addWidget(self.lab_delta_y)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_vi_send_cmd = QtGui.QPushButton("SEND CMD", self)
        self.connect(self.butt_vi_send_cmd, SIGNAL("pressed()"), self.butt_vi_send_cmd_Changed)
        self.butt_vi_send_cmd.setEnabled(False)

        self.lab_vi_send_cmd_static = QtGui.QLabel()
        self.lab_vi_send_cmd_static.setText("PS no")

        self.ctrl_vi_send_cmd_index_ps = QtGui.QSpinBox()
        self.ctrl_vi_send_cmd_index_ps.setMinimum(1)
        self.ctrl_vi_send_cmd_index_ps.setSingleStep(1)
        self.ctrl_vi_send_cmd_index_ps.setMaximum(2)
        self.ctrl_vi_send_cmd_index_ps.setProperty("value", 1)
        # self.ps_index_value = self.ctrl_vi_send_cmd_index_ps.value()
        self.ctrl_vi_send_cmd_index_ps.setKeyboardTracking(False)
        # self.ctrl_vi_send_cmd_index_ps.valueChanged.connect(self.ctrl_vi_send_cmd_index_ps_Changed)

        vbox_vi_h_butt_lab_ctrl_send_cmd = QtGui.QHBoxLayout()
        vbox_vi_h_butt_lab_ctrl_send_cmd.addWidget(self.butt_vi_send_cmd)
        vbox_vi_h_butt_lab_ctrl_send_cmd.addWidget(self.lab_vi_send_cmd_static)
        vbox_vi_h_butt_lab_ctrl_send_cmd.addWidget(self.ctrl_vi_send_cmd_index_ps)

        # ==============================================

        self.txt_vi_send_cmd_name = QtGui.QLineEdit()
        self.txt_vi_send_cmd_name.setPlaceholderText('*IDN?')

        vbox_vi_h_txt_send_cmd = QtGui.QHBoxLayout()
        vbox_vi_h_txt_send_cmd.addWidget(self.txt_vi_send_cmd_name)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        vbox_vi = QtGui.QVBoxLayout()
        vbox_vi.addWidget(self.lab_video_static)
        vbox_vi.addStretch(1)
        vbox_vi.addWidget(self.checkbox_trig_on_off)
        vbox_vi.addLayout(vbox_vi_h_ctrl_fps)
        vbox_vi.addLayout(vbox_vi_h_lab_real_FPS)
        vbox_vi.addLayout(vbox_vi_h_lab_delta_t)
        vbox_vi.addLayout(vbox_vi_h_lab_measure_fps)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_butt_light)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_lab_temperature)
        vbox_vi.addLayout(vbox_vi_h_lab_temperature_coil)
        vbox_vi.addStretch(1)
        vbox_vi.addWidget(self.checkbox_p)
        vbox_vi.addWidget(self.checkbox_t)
        # vbox_vi.addWidget(self.checkbox_b)
        vbox_vi.addLayout(vbox_vi_h_b_ref)
        # vbox_vi.addWidget(self.checkbox_diff)
        vbox_vi.addLayout(vbox_vi_h_diff_xz)
        # vbox_vi.addWidget(self.checkbox_grid)
        vbox_vi.addLayout(vbox_vi_h_chbox_grids)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_ctrl_grid)
        vbox_vi.addLayout(vbox_vi_h_ctrl_zoom)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_lab_min_max)
        vbox_vi.addLayout(vbox_vi_h_ctrl_area)
        vbox_vi.addLayout(vbox_vi_h_ctrl_circ)
        vbox_vi.addLayout(vbox_vi_h_ctrl_ths)
        vbox_vi.addLayout(vbox_vi_h_ctrl_ths_2)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_lab_focus)
        vbox_vi.addLayout(vbox_vi_h_lab_round)
        vbox_vi.addLayout(vbox_vi_h_lab_bead)
        vbox_vi.addLayout(vbox_vi_h_lab_center_x)
        vbox_vi.addLayout(vbox_vi_h_lab_center_y)
        vbox_vi.addLayout(vbox_vi_h_lab_width)
        vbox_vi.addLayout(vbox_vi_h_lab_height)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_lab_focus_2)
        vbox_vi.addLayout(vbox_vi_h_lab_round_2)
        vbox_vi.addLayout(vbox_vi_h_lab_bead_2)
        vbox_vi.addLayout(vbox_vi_h_lab_center_x_2)
        vbox_vi.addLayout(vbox_vi_h_lab_center_y_2)
        vbox_vi.addLayout(vbox_vi_h_lab_width_2)
        vbox_vi.addLayout(vbox_vi_h_lab_height_2)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_lab_delta_x)
        vbox_vi.addLayout(vbox_vi_h_lab_delta_y)
        vbox_vi.addStretch(1)
        vbox_vi.addLayout(vbox_vi_h_butt_lab_ctrl_send_cmd)
        vbox_vi.addLayout(vbox_vi_h_txt_send_cmd)

        bound_box_vi.setLayout(vbox_vi)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_ac = QtGui.QGroupBox()
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_actuat_static = QtGui.QLabel()
        self.lab_actuat_static.setText("A  C  T  U  A  T  O  R    ")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_act_start = QtGui.QPushButton("Start polling actuator", self)
        self.connect(self.butt_act_start, SIGNAL("pressed()"), self.butt_act_start_Changed)

        # ==============================================

        self.butt_act_stop = QtGui.QPushButton("Stop polling actuator", self)
        self.connect(self.butt_act_stop, SIGNAL("pressed()"), self.butt_act_stop_Changed)
        self.butt_act_stop.setEnabled(False)

        # ==============================================

        self.butt_act_reset = QtGui.QPushButton("Reset", self)
        self.connect(self.butt_act_reset, SIGNAL("pressed()"), self.butt_act_reset_Changed)
        self.butt_act_reset.setEnabled(False)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_act_track_on = QtGui.QPushButton("Track bead", self)
        self.connect(self.butt_act_track_on, SIGNAL("pressed()"), self.butt_act_track_on_Changed)
        self.butt_act_track_on.setEnabled(False)

        # ==============================================

        self.butt_act_track_off = QtGui.QPushButton("Stop track bead", self)
        self.connect(self.butt_act_track_off, SIGNAL("pressed()"), self.butt_act_track_off_Changed)
        self.butt_act_track_off.setEnabled(False)

        # ==============================================

        self.lab_act_track_error = QtGui.QLabel()
        self.lab_act_track_error.setText('       ')
        self.lab_act_track_error.setFont(self.dim__text)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_bead_z_coord_static = QtGui.QLabel()
        self.lab_bead_z_coord_static.setText('z bead')
        self.lab_bead_z_coord = QtGui.QLabel()

        vbox_ac_h_lab_bead_z_coord = QtGui.QHBoxLayout()
        vbox_ac_h_lab_bead_z_coord.addWidget(self.lab_bead_z_coord_static)
        vbox_ac_h_lab_bead_z_coord.addWidget(self.lab_bead_z_coord)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.ctrl_abs_static = QtGui.QLabel()
        self.ctrl_abs_static.setText("Abs mov")

        self.ctrl_abs = QtGui.QDoubleSpinBox()
        self.ctrl_abs.setMinimum(0.0000)
        self.ctrl_abs.setSingleStep(1.00)
        self.ctrl_abs.setMaximum(25.0)
        self.ctrl_abs.setProperty("value", 7.250)
        self.ctrl_abs.setDecimals(5)
        self.abs_value = self.ctrl_abs.value()
        self.ctrl_abs.setKeyboardTracking(False)

        vbox_ac_h_ctrl_abs = QtGui.QHBoxLayout()
        vbox_ac_h_ctrl_abs.addWidget(self.ctrl_abs_static)
        vbox_ac_h_ctrl_abs.addWidget(self.ctrl_abs)

        # ==============================================

        self.butt_act_abs = QtGui.QPushButton("Move abs", self)
        self.connect(self.butt_act_abs, SIGNAL("pressed()"), self.butt_act_abs_Changed)
        self.butt_act_abs.setEnabled(False)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_act_rel_pos = QtGui.QPushButton("Move up (+)", self)
        self.connect(self.butt_act_rel_pos, SIGNAL("pressed()"), self.butt_act_rel_pos_Changed)
        self.butt_act_rel_pos.setEnabled(False)

        # ==============================================

        self.ctrl_rel_static = QtGui.QLabel()
        self.ctrl_rel_static.setText("Rel mov")

        self.ctrl_rel = QtGui.QDoubleSpinBox()
        self.ctrl_rel.setMinimum(0.0000)
        self.ctrl_rel.setSingleStep(0.001)
        self.ctrl_rel.setMaximum(25.0)
        self.ctrl_rel.setProperty("value", 0.100)
        self.ctrl_rel.setDecimals(5)
        self.rel_value = self.ctrl_rel.value()
        self.ctrl_rel.setKeyboardTracking(False)

        vbox_ac_h_ctrl_rel = QtGui.QHBoxLayout()
        vbox_ac_h_ctrl_rel.addWidget(self.ctrl_rel_static)
        vbox_ac_h_ctrl_rel.addWidget(self.ctrl_rel)

        # ==============================================

        self.butt_act_rel_neg = QtGui.QPushButton("Move down (-)", self)
        self.connect(self.butt_act_rel_neg, SIGNAL("pressed()"), self.butt_act_rel_neg_Changed)
        self.butt_act_rel_neg.setEnabled(False)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_act_pos = QtGui.QLabel()
        self.lab_act_pos_static = QtGui.QLabel()
        self.lab_act_pos_static.setText("Position")

        vbox_ac_h_lab_pos = QtGui.QHBoxLayout()
        vbox_ac_h_lab_pos.addWidget(self.lab_act_pos_static)
        vbox_ac_h_lab_pos.addWidget(self.lab_act_pos)

        # ==============================================

        self.lab_act_err = QtGui.QLabel()
        self.lab_act_err_static = QtGui.QLabel()
        self.lab_act_err_static.setText("Errors")

        vbox_ac_h_lab_err = QtGui.QHBoxLayout()
        vbox_ac_h_lab_err.addWidget(self.lab_act_err_static)
        vbox_ac_h_lab_err.addWidget(self.lab_act_err)

        # ==============================================

        self.lab_act_sta = QtGui.QLabel()
        self.lab_act_sta_static = QtGui.QLabel()
        self.lab_act_sta_static.setText("STATUS")

        vbox_ac_h_lab_sta = QtGui.QHBoxLayout()
        vbox_ac_h_lab_sta.addWidget(self.lab_act_sta_static)
        vbox_ac_h_lab_sta.addWidget(self.lab_act_sta)

        # ==============================================

        self.lab_act_lerr = QtGui.QLabel()
        self.lab_act_lerr_static = QtGui.QLabel()
        self.lab_act_lerr_static.setText("Last error")

        vbox_ac_h_lab_lerr = QtGui.QHBoxLayout()
        vbox_ac_h_lab_lerr.addWidget(self.lab_act_lerr_static)
        vbox_ac_h_lab_lerr.addWidget(self.lab_act_lerr)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_ac = QtGui.QVBoxLayout()
        vbox_ac.addWidget(self.lab_actuat_static)
        vbox_ac.addStretch(2)
        vbox_ac.addWidget(self.butt_act_start)
        vbox_ac.addWidget(self.butt_act_stop)
        vbox_ac.addWidget(self.butt_act_reset)
        vbox_ac.addStretch(2)
        vbox_ac.addWidget(self.butt_act_track_on)
        vbox_ac.addWidget(self.butt_act_track_off)
        vbox_ac.addWidget(self.lab_act_track_error)
        vbox_ac.addStretch(2)
        vbox_ac.addLayout(vbox_ac_h_lab_bead_z_coord)
        vbox_ac.addStretch(2)
        vbox_ac.addLayout(vbox_ac_h_ctrl_abs)
        vbox_ac.addWidget(self.butt_act_abs)
        vbox_ac.addStretch(2)
        vbox_ac.addWidget(self.butt_act_rel_pos)
        vbox_ac.addLayout(vbox_ac_h_ctrl_rel)
        vbox_ac.addWidget(self.butt_act_rel_neg)
        vbox_ac.addStretch(2)
        vbox_ac.addLayout(vbox_ac_h_lab_pos)
        vbox_ac.addLayout(vbox_ac_h_lab_err)
        vbox_ac.addLayout(vbox_ac_h_lab_sta)
        vbox_ac.addLayout(vbox_ac_h_lab_lerr)
        bound_box_ac.setLayout(vbox_ac)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&& RANDOM  &&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_random = QtGui.QGroupBox()
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_random_static = QtGui.QLabel()
        self.lab_random_static.setText("R A N D O M   B E A D")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_random_start = QtGui.QPushButton("Start R.", self)
        self.connect(self.butt_random_start, SIGNAL("pressed()"), self.butt_random_start_Changed)

        # ==============================================

        self.butt_random_stop = QtGui.QPushButton("Stop R.", self)
        self.connect(self.butt_random_stop, SIGNAL("pressed()"), self.butt_random_stop_Changed)
        self.butt_random_stop.setEnabled(False)

        vbox_random_h_butt_start_stop = QtGui.QHBoxLayout()
        vbox_random_h_butt_start_stop.addWidget(self.butt_random_start)
        vbox_random_h_butt_start_stop.addStretch(1)
        vbox_random_h_butt_start_stop.addWidget(self.butt_random_stop)

        # ==============================================
        self.butt_random_current = QtGui.QPushButton("RANDOM Ii (i=1,4)  ", self)
        self.connect(self.butt_random_current, SIGNAL("pressed()"), self.butt_random_current_Changed)

        self.ctrl_random_I_max = QtGui.QDoubleSpinBox()
        self.ctrl_random_I_max.setMinimum(0.0)
        self.ctrl_random_I_max.setSingleStep(0.1)  # 0.1
        self.ctrl_random_I_max.setMaximum(1.5)
        self.ctrl_random_I_max.setDecimals(3)
        self.ctrl_random_I_max.setProperty("value", 0.3)
        self.ctrl_random_I_max.setKeyboardTracking(False)
        self.ctrl_random_I_max.setEnabled(True)

        vbox_random_h_ctrl_I_lim = QtGui.QHBoxLayout()
        vbox_random_h_ctrl_I_lim.addStretch(1)
        vbox_random_h_ctrl_I_lim.addWidget(self.butt_random_current)
        vbox_random_h_ctrl_I_lim.addWidget(self.ctrl_random_I_max)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_random_current_zero = QtGui.QPushButton("SET Ii=0 A", self)
        self.connect(self.butt_random_current_zero, SIGNAL("pressed()"), self.butt_random_current_zero_Changed)

        self.butt_random_current_2p5A = QtGui.QPushButton("2.5 A", self)
        self.connect(self.butt_random_current_2p5A, SIGNAL("pressed()"), self.butt_random_current_2p5A_Changed)

        vbox_random_h_butt_I_zero = QtGui.QHBoxLayout()
        vbox_random_h_butt_I_zero.addWidget(self.butt_random_current_zero)
        vbox_random_h_butt_I_zero.addStretch(1)
        vbox_random_h_butt_I_zero.addWidget(self.butt_random_current_2p5A)

        # ==============================================

        self.checkbox_random_safety = QtGui.QCheckBox("Activate box lim", self)
        self.checkbox_random_safety.toggle()
        self.checkbox_random_safety.setCheckState(Qt.Unchecked)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_random_time_laps_start = QtGui.QPushButton("Start laps", self)
        self.connect(self.butt_random_time_laps_start, SIGNAL("pressed()"), self.butt_random_time_laps_start_Changed)
        self.time_laps_run_flag = False

        self.butt_random_time_laps_stop = QtGui.QPushButton("Stop laps", self)
        self.connect(self.butt_random_time_laps_stop, SIGNAL("pressed()"), self.butt_random_time_laps_stop_Changed)
        self.butt_random_time_laps_stop.setEnabled(False)

        vbox_random_h_butt_t_laps_s_s = QtGui.QHBoxLayout()
        vbox_random_h_butt_t_laps_s_s.addWidget(self.butt_random_time_laps_start)
        vbox_random_h_butt_t_laps_s_s.addStretch(1)
        vbox_random_h_butt_t_laps_s_s.addWidget(self.butt_random_time_laps_stop)

        # ==============================================

        self.txt_random_time_lapse_folder = QtGui.QLineEdit()
        self.txt_random_time_lapse_folder.setPlaceholderText('2015_11_10_tlps_1_E2_')

        # ==============================================

        self.lab_random_time_laps_static_frames_no = QtGui.QLabel()
        self.lab_random_time_laps_static_frames_no.setText("Number frames")
        self.lab_random_time_laps_static_frames_time = QtGui.QLabel()
        self.lab_random_time_laps_static_frames_time.setText("Time frames (s)")

        vbox_random_h_lab_t_laps_frames_no_time_static = QtGui.QHBoxLayout()  # Horizontal layout
        vbox_random_h_lab_t_laps_frames_no_time_static.addWidget(self.lab_random_time_laps_static_frames_no)
        vbox_random_h_lab_t_laps_frames_no_time_static.addWidget(self.lab_random_time_laps_static_frames_time)

        # ==============================================

        self.ctrl_random_timelaps_frame_no = QtGui.QSpinBox()
        self.ctrl_random_timelaps_frame_no.setMinimum(1)
        self.ctrl_random_timelaps_frame_no.setSingleStep(1)
        self.ctrl_random_timelaps_frame_no.setMaximum(1000)
        self.ctrl_random_timelaps_frame_no.setProperty("value", 10)
        self.timelaps_frame_no = self.ctrl_random_timelaps_frame_no.value()
        self.ctrl_random_timelaps_frame_no.setKeyboardTracking(False)
        self.ctrl_random_timelaps_frame_no.setEnabled(True)
        self.ctrl_random_timelaps_frame_no.valueChanged.connect(self.ctrl_random_timelaps_frame_no_Changed)

        self.lab_random_timelaps_frame_index = QtGui.QLabel()

        self.ctrl_random_timelaps_frame_time = QtGui.QSpinBox()
        self.ctrl_random_timelaps_frame_time.setMinimum(1)
        self.ctrl_random_timelaps_frame_time.setSingleStep(1)
        self.ctrl_random_timelaps_frame_time.setMaximum(1000)
        self.ctrl_random_timelaps_frame_time.setProperty("value", 30)
        self.timelaps_frame_time = self.ctrl_random_timelaps_frame_time.value()
        self.ctrl_random_timelaps_frame_time.setKeyboardTracking(False)
        self.ctrl_random_timelaps_frame_time.setEnabled(True)
        self.ctrl_random_timelaps_frame_time.valueChanged.connect(self.ctrl_random_timelaps_frame_time_Changed)

        vbox_random_h_ctrl_t_laps_frames_no_time = QtGui.QHBoxLayout()
        vbox_random_h_ctrl_t_laps_frames_no_time.addWidget(self.ctrl_random_timelaps_frame_no)
        vbox_random_h_ctrl_t_laps_frames_no_time.addStretch(1)
        vbox_random_h_ctrl_t_laps_frames_no_time.addWidget(self.lab_random_timelaps_frame_index)
        vbox_random_h_ctrl_t_laps_frames_no_time.addStretch(1)
        vbox_random_h_ctrl_t_laps_frames_no_time.addWidget(self.ctrl_random_timelaps_frame_time)

        # ==============================================

        self.ctrl_random_timelaps_t_ON_static = QtGui.QLabel()
        self.ctrl_random_timelaps_t_ON_static.setText("t(s)  ON")

        self.ctrl_random_timelaps_t_ON = QtGui.QSpinBox()
        self.ctrl_random_timelaps_t_ON.setMinimum(0)
        self.ctrl_random_timelaps_t_ON.setSingleStep(10)
        self.ctrl_random_timelaps_t_ON.setMaximum(600)
        self.ctrl_random_timelaps_t_ON.setProperty("value", 30)
        self.timelaps_t_ON_value = self.ctrl_random_timelaps_t_ON.value()
        self.ctrl_random_timelaps_t_ON.setKeyboardTracking(False)
        self.ctrl_random_timelaps_t_ON.setEnabled(True)
        # self.ctrl_random_timelaps_t_ON.valueChanged.connect(self.ctrl_random_timelaps_t_ON_Changed)

        self.ctrl_random_timelaps_t_OFF_static = QtGui.QLabel()
        self.ctrl_random_timelaps_t_OFF_static.setText("OFF")

        self.ctrl_random_timelaps_t_OFF = QtGui.QSpinBox()
        self.ctrl_random_timelaps_t_OFF.setMinimum(0)
        self.ctrl_random_timelaps_t_OFF.setSingleStep(10)
        self.ctrl_random_timelaps_t_OFF.setMaximum(1800)
        self.ctrl_random_timelaps_t_OFF.setProperty("value", 180)
        self.timelaps_t_OFF_value = self.ctrl_random_timelaps_t_OFF.value()
        self.ctrl_random_timelaps_t_OFF.setKeyboardTracking(False)
        self.ctrl_random_timelaps_t_OFF.setEnabled(True)
        # self.ctrl_random_timelaps_t_ON.valueChanged.connect(self.ctrl_random_timelaps_t_ON_Changed)

        vbox_random_h_ctrl_t_laps_t_ON_OFF = QtGui.QHBoxLayout()
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addWidget(self.ctrl_random_timelaps_t_ON_static)
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addStretch(1)
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addWidget(self.ctrl_random_timelaps_t_ON)
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addStretch(1)
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addWidget(self.ctrl_random_timelaps_t_OFF_static)
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addStretch(1)
        vbox_random_h_ctrl_t_laps_t_ON_OFF.addWidget(self.ctrl_random_timelaps_t_OFF)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        vbox_random = QtGui.QVBoxLayout()
        vbox_random.addWidget(self.lab_random_static)
        # vbox_random.addStretch(1)
        # vbox_random.addWidget(self.butt_random_start)
        # vbox_random.addWidget(self.butt_random_stop)
        vbox_random.addLayout(vbox_random_h_butt_start_stop)
        # vbox_random.addStretch(1)
        vbox_random.addLayout(vbox_random_h_ctrl_I_lim)
        # vbox_random.addStretch(1)
        vbox_random.addLayout(vbox_random_h_butt_I_zero)
        vbox_random.addWidget(self.checkbox_random_safety)

        vbox_random.addStretch(1)
        vbox_random.addLayout(vbox_random_h_butt_t_laps_s_s)
        vbox_random.addWidget(self.txt_random_time_lapse_folder)
        vbox_random.addLayout(vbox_random_h_lab_t_laps_frames_no_time_static)
        vbox_random.addLayout(vbox_random_h_ctrl_t_laps_frames_no_time)
        vbox_random.addLayout(vbox_random_h_ctrl_t_laps_t_ON_OFF)

        bound_box_random.setLayout(vbox_random)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&& DEMAG CIRCUIT  &&&&&&&&&&&&&&&&&&&&&&&
        bound_box_demag = QtGui.QGroupBox()
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_demag_static = QtGui.QLabel()
        self.lab_demag_static.setText("D E M A G  P O L E S")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_demag_start = QtGui.QPushButton("START", self)
        self.connect(self.butt_demag_start, SIGNAL("pressed()"), self.butt_demag_start_Changed)
        self.butt_demag_start.setEnabled(False)

        # ==============================================

        self.butt_demag_stop = QtGui.QPushButton("STOP", self)
        self.connect(self.butt_demag_stop, SIGNAL("pressed()"), self.butt_demag_stop_Changed)
        self.butt_demag_stop.setEnabled(False)

        vbox_demag_h_butt_SS = QtGui.QHBoxLayout()
        vbox_demag_h_butt_SS.addWidget(self.butt_demag_start)
        vbox_demag_h_butt_SS.addWidget(self.butt_demag_stop)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_demag_static_amp_t_step_1 = QtGui.QLabel()
        self.lab_demag_static_amp_t_step_1.setText("Ampl(A)")
        self.lab_demag_static_amp_t_step_2 = QtGui.QLabel()
        self.lab_demag_static_amp_t_step_2.setText("Step(A)")
        self.lab_demag_static_amp_t_step_3 = QtGui.QLabel()
        self.lab_demag_static_amp_t_step_3.setText("Time(s)")

        vbox_demag_h_lab_amp_t_step = QtGui.QHBoxLayout()  # Horizontal layout
        vbox_demag_h_lab_amp_t_step.addWidget(self.lab_demag_static_amp_t_step_1)
        vbox_demag_h_lab_amp_t_step.addWidget(self.lab_demag_static_amp_t_step_2)
        vbox_demag_h_lab_amp_t_step.addWidget(self.lab_demag_static_amp_t_step_3)

        # ==============================================

        self.ctrl_demag_ampl = QtGui.QDoubleSpinBox()
        self.ctrl_demag_ampl.setMinimum(0.0)
        self.ctrl_demag_ampl.setSingleStep(0.1)
        self.ctrl_demag_ampl.setMaximum(2.5)
        self.ctrl_demag_ampl.setProperty("value", 1.0)
        # self.area_factor_min = self.ctrl_demag_ampl.value()
        self.ctrl_demag_ampl.setKeyboardTracking(False)
        # self.ctrl_demag_ampl.valueChanged.connect(self.ctrl_demag_ampl_Changed)
        self.ctrl_demag_ampl.setEnabled(False)

        self.ctrl_demag_step = QtGui.QDoubleSpinBox()
        self.ctrl_demag_step.setMinimum(0.0)
        self.ctrl_demag_step.setSingleStep(0.05)
        self.ctrl_demag_step.setMaximum(2.5)
        self.ctrl_demag_step.setProperty("value", 0.05)
        # self.area_factor_min = self.ctrl_demag_step.value()
        self.ctrl_demag_step.setKeyboardTracking(False)
        # self.ctrl_demag_step.valueChanged.connect(self.ctrl_demag_step_Changed)
        self.ctrl_demag_step.setEnabled(False)

        self.ctrl_demag_time = QtGui.QDoubleSpinBox()
        self.ctrl_demag_time.setMinimum(0.0)
        self.ctrl_demag_time.setSingleStep(0.2)
        self.ctrl_demag_time.setMaximum(10)
        self.ctrl_demag_time.setProperty("value", 1.5)
        # self.area_factor_min = self.ctrl_demag_time.value()
        self.ctrl_demag_time.setKeyboardTracking(False)
        # self.ctrl_demag_time.valueChanged.connect(self.ctrl_demag_time_Changed)
        self.ctrl_demag_time.setEnabled(False)

        vbox_demag_h_ctrl_ampl_t_step = QtGui.QHBoxLayout()
        vbox_demag_h_ctrl_ampl_t_step.addWidget(self.ctrl_demag_ampl)
        vbox_demag_h_ctrl_ampl_t_step.addWidget(self.ctrl_demag_step)
        vbox_demag_h_ctrl_ampl_t_step.addWidget(self.ctrl_demag_time)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.ctrl_demag_focus_no_frames_static = QtGui.QLabel()
        self.ctrl_demag_focus_no_frames_static.setText("Size")

        self.ctrl_demag_focus_no_frames = QtGui.QSpinBox()
        self.ctrl_demag_focus_no_frames.setMinimum(1)
        self.ctrl_demag_focus_no_frames.setSingleStep(1)
        self.ctrl_demag_focus_no_frames.setMaximum(100)
        self.ctrl_demag_focus_no_frames.setProperty("value", 2)
        self.avg_focus_no_frames = self.ctrl_demag_focus_no_frames.value()
        self.ctrl_demag_focus_no_frames.setKeyboardTracking(False)
        self.ctrl_demag_focus_no_frames.setEnabled(True)
        self.ctrl_demag_focus_no_frames.valueChanged.connect(self.ctrl_demag_focus_no_frames_Changed)

        self.checkbox_demag_avg_focus_RT = QtGui.QCheckBox("GO Avg", self)
        self.checkbox_demag_avg_focus_RT.toggle()
        self.checkbox_demag_avg_focus_RT.setCheckState(Qt.Unchecked)

        vbox_demag_h_avg_focus_RT = QtGui.QHBoxLayout()
        vbox_demag_h_avg_focus_RT.addWidget(self.ctrl_demag_focus_no_frames_static)
        vbox_demag_h_avg_focus_RT.addWidget(self.ctrl_demag_focus_no_frames)
        vbox_demag_h_avg_focus_RT.addWidget(self.checkbox_demag_avg_focus_RT)

        # ==============================================

        self.butt_demag_focus_avg = QtGui.QPushButton("FOCUS 1 (avg 3s)", self)
        self.connect(self.butt_demag_focus_avg, SIGNAL("pressed()"), self.butt_demag_focus_avg_Changed)
        self.butt_demag_focus_avg.setEnabled(True)

        self.lab_demag_focus_avg = QtGui.QLabel()

        vbox_demag_h_focus_avg = QtGui.QHBoxLayout()
        vbox_demag_h_focus_avg.addWidget(self.butt_demag_focus_avg)
        vbox_demag_h_focus_avg.addWidget(self.lab_demag_focus_avg)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_error_1_psu_1 = QtGui.QPushButton("1 - EER?", self)
        self.connect(self.butt_error_1_psu_1, SIGNAL("pressed()"), self.butt_error_1_psu_1_Changed)
        self.butt_error_1_psu_1.setEnabled(False)

        self.butt_error_2_psu_1 = QtGui.QPushButton("1 - *ESR?", self)
        self.connect(self.butt_error_2_psu_1, SIGNAL("pressed()"), self.butt_error_2_psu_1_Changed)
        self.butt_error_2_psu_1.setEnabled(False)

        vbox_demag_h_error_psu_1 = QtGui.QHBoxLayout()
        vbox_demag_h_error_psu_1.addWidget(self.butt_error_1_psu_1)
        vbox_demag_h_error_psu_1.addWidget(self.butt_error_2_psu_1)

        # ==============================================

        self.butt_error_1_psu_2 = QtGui.QPushButton("2 - EER?", self)
        self.connect(self.butt_error_1_psu_2, SIGNAL("pressed()"), self.butt_error_1_psu_2_Changed)
        self.butt_error_1_psu_2.setEnabled(False)

        self.butt_error_2_psu_2 = QtGui.QPushButton("2 - *ESR?", self)
        self.connect(self.butt_error_2_psu_2, SIGNAL("pressed()"), self.butt_error_2_psu_2_Changed)
        self.butt_error_2_psu_2.setEnabled(False)

        vbox_demag_h_error_psu_2 = QtGui.QHBoxLayout()
        vbox_demag_h_error_psu_2.addWidget(self.butt_error_1_psu_2)
        vbox_demag_h_error_psu_2.addWidget(self.butt_error_2_psu_2)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_demag = QtGui.QVBoxLayout()
        vbox_demag.addWidget(self.lab_demag_static)
        vbox_demag.addStretch(1)
        # vbox_demag.addWidget(self.butt_demag_start)
        # vbox_demag.addWidget(self.butt_demag_stop)
        vbox_demag.addLayout(vbox_demag_h_butt_SS)
        vbox_demag.addStretch(1)
        vbox_demag.addLayout(vbox_demag_h_lab_amp_t_step)
        vbox_demag.addLayout(vbox_demag_h_ctrl_ampl_t_step)
        vbox_demag.addStretch(1)
        vbox_demag.addLayout(vbox_demag_h_avg_focus_RT)
        vbox_demag.addLayout(vbox_demag_h_focus_avg)
        vbox_demag.addStretch(1)
        vbox_demag.addLayout(vbox_demag_h_error_psu_1)
        vbox_demag.addLayout(vbox_demag_h_error_psu_2)
        # vbox_demag.addLayout(vbox_random_h_ctrl_I_lim)
        # vbox_demag.addStretch(1)
        # vbox_demag.addLayout(vbox_random_h_butt_I_zero)
        # vbox_demag.addWidget(self.checkbox_random_safety)

        # vbox_demag.addStretch(1)

        bound_box_demag.setLayout(vbox_demag)
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_ac_rand = QtGui.QVBoxLayout()
        vbox_ac_rand.addWidget(bound_box_ac)
        vbox_ac_rand.addWidget(bound_box_random)
        vbox_ac_rand.addWidget(bound_box_demag)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_ps = QtGui.QGroupBox()
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_power_static = QtGui.QLabel()
        self.lab_power_static.setText("     P O W E R   S U P P L Y   ")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_ard_start = QtGui.QPushButton("Start polling arduino", self)
        self.connect(self.butt_ard_start, SIGNAL("pressed()"), self.butt_ard_start_Changed)

        # ==============================================

        self.butt_ard_stop = QtGui.QPushButton("Stop polling arduino", self)
        self.connect(self.butt_ard_stop, SIGNAL("pressed()"), self.butt_ard_stop_Changed)
        self.butt_ard_stop.setEnabled(False)

        # ==============================================

        '''self.butt_ard_reset_temp =QtGui.QPushButton("Reset Temp Err",self)
        self.connect(self.butt_ard_reset_temp,SIGNAL("pressed()"),self.butt_ard_reset_temp_Changed)
        self.butt_ard_reset_temp.setEnabled(False)'''

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_pow_start = QtGui.QPushButton("Power ON", self)
        self.connect(self.butt_pow_start, SIGNAL("pressed()"), self.butt_pow_start_Changed)
        self.butt_pow_start.setEnabled(False)

        # ==============================================

        self.ctrl_curr_1_static = QtGui.QLabel()
        self.ctrl_curr_1_static.setText("I1 = ")

        self.ctrl_curr_1 = QtGui.QDoubleSpinBox()
        self.ctrl_curr_1.setMinimum(-2.5)
        self.ctrl_curr_1.setSingleStep(0.1)
        self.ctrl_curr_1.setMaximum(2.5)
        self.ctrl_curr_1.setDecimals(3)
        self.ctrl_curr_1.setProperty("value", 0.001)
        self.curr_1_value = self.ctrl_curr_1.value()
        self.ctrl_curr_1.setKeyboardTracking(False)
        self.ctrl_curr_1.setEnabled(False)
        self.ctrl_curr_1.valueChanged.connect(self.ctrl_curr_1_Changed)

        vbox_ps_h_ctrl_curr_1 = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_curr_1.addStretch(1)
        vbox_ps_h_ctrl_curr_1.addWidget(self.ctrl_curr_1_static)
        vbox_ps_h_ctrl_curr_1.addWidget(self.ctrl_curr_1)

        # ==============================================

        self.ctrl_curr_2_static = QtGui.QLabel()
        self.ctrl_curr_2_static.setText("I2 = ")

        self.ctrl_curr_2 = QtGui.QDoubleSpinBox()
        self.ctrl_curr_2.setMinimum(-2.5)
        self.ctrl_curr_2.setSingleStep(0.1)
        self.ctrl_curr_2.setMaximum(2.5)
        self.ctrl_curr_2.setDecimals(3)
        self.ctrl_curr_2.setProperty("value", 0.001)
        self.curr_2_value = self.ctrl_curr_2.value()
        self.ctrl_curr_2.setKeyboardTracking(False)
        self.ctrl_curr_2.setEnabled(False)
        self.ctrl_curr_2.valueChanged.connect(self.ctrl_curr_2_Changed)

        vbox_ps_h_ctrl_curr_2 = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_curr_2.addStretch(1)
        vbox_ps_h_ctrl_curr_2.addWidget(self.ctrl_curr_2_static)
        vbox_ps_h_ctrl_curr_2.addWidget(self.ctrl_curr_2)

        # ==============================================

        self.ctrl_curr_3_static = QtGui.QLabel()
        self.ctrl_curr_3_static.setText("I3 = ")

        self.ctrl_curr_3 = QtGui.QDoubleSpinBox()
        self.ctrl_curr_3.setMinimum(-2.5)
        self.ctrl_curr_3.setSingleStep(0.1)
        self.ctrl_curr_3.setMaximum(2.5)
        self.ctrl_curr_3.setDecimals(3)
        self.ctrl_curr_3.setProperty("value", 0.001)
        self.curr_3_value = self.ctrl_curr_3.value()
        self.ctrl_curr_3.setKeyboardTracking(False)
        self.ctrl_curr_3.setEnabled(False)
        self.ctrl_curr_3.valueChanged.connect(self.ctrl_curr_3_Changed)

        vbox_ps_h_ctrl_curr_3 = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_curr_3.addStretch(1)
        vbox_ps_h_ctrl_curr_3.addWidget(self.ctrl_curr_3_static)
        vbox_ps_h_ctrl_curr_3.addWidget(self.ctrl_curr_3)

        # ==============================================

        self.ctrl_curr_4_static = QtGui.QLabel()
        self.ctrl_curr_4_static.setText("I4 = ")

        self.ctrl_curr_4 = QtGui.QDoubleSpinBox()
        self.ctrl_curr_4.setMinimum(-2.5)
        self.ctrl_curr_4.setSingleStep(0.1)
        self.ctrl_curr_4.setMaximum(2.5)
        self.ctrl_curr_4.setDecimals(3)
        self.ctrl_curr_4.setProperty("value", 0.001)
        self.curr_4_value = self.ctrl_curr_4.value()
        self.ctrl_curr_4.setKeyboardTracking(False)
        self.ctrl_curr_4.setEnabled(False)
        self.ctrl_curr_4.valueChanged.connect(self.ctrl_curr_4_Changed)

        vbox_ps_h_ctrl_curr_4 = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_curr_4.addStretch(1)
        vbox_ps_h_ctrl_curr_4.addWidget(self.ctrl_curr_4_static)
        vbox_ps_h_ctrl_curr_4.addWidget(self.ctrl_curr_4)

        # ==============================================

        self.butt_pow_stop = QtGui.QPushButton("Power OFF", self)
        self.connect(self.butt_pow_stop, SIGNAL("pressed()"), self.butt_pow_stop_Changed)
        self.butt_pow_stop.setEnabled(False)

        # ==============================================

        self.butt_pow_pulse = QtGui.QPushButton("Power ON/OFF - pulse", self)
        self.connect(self.butt_pow_pulse, SIGNAL("pressed()"), self.butt_pow_pulse_Changed)
        self.butt_pow_pulse.setEnabled(False)
        self.pulse_current_bool = False

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_pow_UP = QtGui.QPushButton("  UP  ", self)
        self.connect(self.butt_pow_UP, SIGNAL("pressed()"), self.butt_pow_UP_Changed)
        self.butt_pow_UP.setEnabled(False)

        self.ctrl_pow_UP = QtGui.QDoubleSpinBox()
        self.ctrl_pow_UP.setMinimum(-2.5)
        self.ctrl_pow_UP.setSingleStep(0.1)  # 0.1
        self.ctrl_pow_UP.setMaximum(2.5)
        self.ctrl_pow_UP.setDecimals(3)
        self.ctrl_pow_UP.setProperty("value", 0.201)
        self.curr_UP_value = self.ctrl_pow_UP.value()
        self.ctrl_pow_UP.setKeyboardTracking(False)
        self.ctrl_pow_UP.setEnabled(False)
        self.ctrl_pow_UP.valueChanged.connect(self.ctrl_pow_UP_Changed)

        vbox_ps_h_ctrl_pow_UP = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_pow_UP.addStretch(1)
        vbox_ps_h_ctrl_pow_UP.addWidget(self.butt_pow_UP)
        vbox_ps_h_ctrl_pow_UP.addWidget(self.ctrl_pow_UP)

        # ==============================================

        self.butt_pow_RL = QtGui.QPushButton("  <<--  ", self)
        self.connect(self.butt_pow_RL, SIGNAL("pressed()"), self.butt_pow_RL_Changed)
        self.butt_pow_RL.setEnabled(False)

        self.ctrl_pow_RL = QtGui.QDoubleSpinBox()
        self.ctrl_pow_RL.setMinimum(-2.5)
        self.ctrl_pow_RL.setSingleStep(0.1)  # 0.1
        self.ctrl_pow_RL.setMaximum(2.5)
        self.ctrl_pow_RL.setDecimals(3)
        self.ctrl_pow_RL.setProperty("value", 0.201)
        self.curr_RL_value = self.ctrl_pow_RL.value()
        self.ctrl_pow_RL.setKeyboardTracking(False)
        self.ctrl_pow_RL.setEnabled(False)
        self.ctrl_pow_RL.valueChanged.connect(self.ctrl_pow_RL_Changed)

        vbox_ps_h_ctrl_pow_RL = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_pow_RL.addStretch(1)
        vbox_ps_h_ctrl_pow_RL.addWidget(self.butt_pow_RL)
        vbox_ps_h_ctrl_pow_RL.addWidget(self.ctrl_pow_RL)

        # ==============================================

        self.butt_pow_LR = QtGui.QPushButton("  -->>  ", self)
        self.connect(self.butt_pow_LR, SIGNAL("pressed()"), self.butt_pow_LR_Changed)
        self.butt_pow_LR.setEnabled(False)

        self.ctrl_pow_LR = QtGui.QDoubleSpinBox()
        self.ctrl_pow_LR.setMinimum(-2.5)
        self.ctrl_pow_LR.setSingleStep(0.1)  # 0.1
        self.ctrl_pow_LR.setMaximum(2.5)
        self.ctrl_pow_LR.setDecimals(3)
        self.ctrl_pow_LR.setProperty("value", 0.201)
        self.curr_LR_value = self.ctrl_pow_LR.value()
        self.ctrl_pow_LR.setKeyboardTracking(False)
        self.ctrl_pow_LR.setEnabled(False)
        self.ctrl_pow_LR.valueChanged.connect(self.ctrl_pow_LR_Changed)

        vbox_ps_h_ctrl_pow_LR = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_pow_LR.addStretch(1)
        vbox_ps_h_ctrl_pow_LR.addWidget(self.butt_pow_LR)
        vbox_ps_h_ctrl_pow_LR.addWidget(self.ctrl_pow_LR)

        # ==============================================

        self.butt_pow_DOWN = QtGui.QPushButton("  DOWN  ", self)
        self.connect(self.butt_pow_DOWN, SIGNAL("pressed()"), self.butt_pow_DOWN_Changed)
        self.butt_pow_DOWN.setEnabled(False)

        self.ctrl_pow_DOWN = QtGui.QDoubleSpinBox()
        self.ctrl_pow_DOWN.setMinimum(-2.5)
        self.ctrl_pow_DOWN.setSingleStep(0.1)  # 0.1
        self.ctrl_pow_DOWN.setMaximum(2.5)
        self.ctrl_pow_DOWN.setDecimals(3)
        self.ctrl_pow_DOWN.setProperty("value", 0.201)
        self.curr_DOWN_value = self.ctrl_pow_DOWN.value()
        self.ctrl_pow_DOWN.setKeyboardTracking(False)
        self.ctrl_pow_DOWN.setEnabled(False)
        self.ctrl_pow_DOWN.valueChanged.connect(self.ctrl_pow_DOWN_Changed)

        vbox_ps_h_ctrl_pow_DOWN = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_pow_DOWN.addStretch(1)
        vbox_ps_h_ctrl_pow_DOWN.addWidget(self.butt_pow_DOWN)
        vbox_ps_h_ctrl_pow_DOWN.addWidget(self.ctrl_pow_DOWN)

        # ==============================================

        self.butt_pow_zDOWN = QtGui.QPushButton("  Z  down  ", self)
        self.connect(self.butt_pow_zDOWN, SIGNAL("pressed()"), self.butt_pow_zDOWN_Changed)
        self.butt_pow_zDOWN.setEnabled(False)

        self.ctrl_pow_zDOWN = QtGui.QDoubleSpinBox()
        self.ctrl_pow_zDOWN.setMinimum(-2.5)
        self.ctrl_pow_zDOWN.setSingleStep(0.1)  # 0.1
        self.ctrl_pow_zDOWN.setMaximum(2.5)
        self.ctrl_pow_zDOWN.setDecimals(3)
        self.ctrl_pow_zDOWN.setProperty("value", 0.201)
        self.curr_zDOWN_value = self.ctrl_pow_zDOWN.value()
        self.ctrl_pow_zDOWN.setKeyboardTracking(False)
        self.ctrl_pow_zDOWN.setEnabled(False)
        self.ctrl_pow_zDOWN.valueChanged.connect(self.ctrl_pow_zDOWN_Changed)

        vbox_ps_h_ctrl_pow_zDOWN = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_pow_zDOWN.addStretch(1)
        vbox_ps_h_ctrl_pow_zDOWN.addWidget(self.butt_pow_zDOWN)
        vbox_ps_h_ctrl_pow_zDOWN.addWidget(self.ctrl_pow_zDOWN)

        # ==============================================

        self.butt_pow_zUP = QtGui.QPushButton("  Z  up  ", self)
        self.connect(self.butt_pow_zUP, SIGNAL("pressed()"), self.butt_pow_zUP_Changed)
        self.butt_pow_zUP.setEnabled(False)

        self.ctrl_pow_zUP = QtGui.QDoubleSpinBox()
        self.ctrl_pow_zUP.setMinimum(-2.5)
        self.ctrl_pow_zUP.setSingleStep(0.1)  # 0.1
        self.ctrl_pow_zUP.setMaximum(2.5)
        self.ctrl_pow_zUP.setDecimals(3)
        self.ctrl_pow_zUP.setProperty("value", 0.201)
        self.curr_zUP_value = self.ctrl_pow_zUP.value()
        self.ctrl_pow_zUP.setKeyboardTracking(False)
        self.ctrl_pow_zUP.setEnabled(False)
        self.ctrl_pow_zUP.valueChanged.connect(self.ctrl_pow_zUP_Changed)

        vbox_ps_h_ctrl_pow_zUP = QtGui.QHBoxLayout()
        vbox_ps_h_ctrl_pow_zUP.addStretch(1)
        vbox_ps_h_ctrl_pow_zUP.addWidget(self.butt_pow_zUP)
        vbox_ps_h_ctrl_pow_zUP.addWidget(self.ctrl_pow_zUP)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_psu_on_off = QtGui.QLabel()  # ON or OFF
        self.lab_psu_on_off_static = QtGui.QLabel()
        self.lab_psu_on_off_static.setText("Power ->")

        vbox_ps_h_lab_psu_on_off = QtGui.QHBoxLayout()
        vbox_ps_h_lab_psu_on_off.addWidget(self.lab_psu_on_off_static)
        vbox_ps_h_lab_psu_on_off.addWidget(self.lab_psu_on_off)

        # ==============================================

        '''self.lab_ard_status = QtGui.QLabel()                   # Error Temp HIGH  or Ready Temp OK
        self.lab_ard_status_static = QtGui.QLabel()
        self.lab_ard_status_static.setText("Status ->")

        vbox_ps_h_lab_ard_status = QtGui.QHBoxLayout()
        vbox_ps_h_lab_ard_status.addWidget(self.lab_ard_status_static)
        vbox_ps_h_lab_ard_status.addWidget(self.lab_ard_status)'''

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_ps = QtGui.QVBoxLayout()
        vbox_ps.addWidget(self.lab_power_static)
        vbox_ps.addStretch(1)
        vbox_ps.addWidget(self.butt_ard_start)
        vbox_ps.addWidget(self.butt_ard_stop)
        # vbox_ps.addWidget(self.butt_ard_reset_temp)
        vbox_ps.addStretch(1)
        vbox_ps.addWidget(self.butt_pow_start)
        vbox_ps.addLayout(vbox_ps_h_ctrl_curr_1)
        vbox_ps.addLayout(vbox_ps_h_ctrl_curr_2)
        vbox_ps.addLayout(vbox_ps_h_ctrl_curr_3)
        vbox_ps.addLayout(vbox_ps_h_ctrl_curr_4)
        vbox_ps.addWidget(self.butt_pow_stop)
        vbox_ps.addWidget(self.butt_pow_pulse)
        vbox_ps.addStretch(1)
        vbox_ps.addLayout(vbox_ps_h_ctrl_pow_UP)
        vbox_ps.addLayout(vbox_ps_h_ctrl_pow_RL)
        vbox_ps.addLayout(vbox_ps_h_ctrl_pow_LR)
        vbox_ps.addLayout(vbox_ps_h_ctrl_pow_DOWN)
        vbox_ps.addLayout(vbox_ps_h_ctrl_pow_zDOWN)
        vbox_ps.addLayout(vbox_ps_h_ctrl_pow_zUP)
        vbox_ps.addStretch(1)
        vbox_ps.addLayout(vbox_ps_h_lab_psu_on_off)
        # vbox_ps.addLayout(vbox_ps_h_lab_ard_status)
        bound_box_ps.setLayout(vbox_ps)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        bound_box_exp = QtGui.QGroupBox('TEST')
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.lab_exp_static = QtGui.QLabel()
        self.lab_exp_static.setText("     E X P E R I M E N T    ")

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_exp_i_dir_start = QtGui.QPushButton("START I", self)
        self.connect(self.butt_exp_i_dir_start, SIGNAL("pressed()"), self.butt_exp_i_dir_start_Changed)
        self.butt_exp_i_dir_start.setEnabled(False)

        # =============================================

        self.butt_exp_i_dir_stop = QtGui.QPushButton("STOP I", self)
        self.connect(self.butt_exp_i_dir_stop, SIGNAL("pressed()"), self.butt_exp_i_dir_stop_Changed)
        self.butt_exp_i_dir_stop.setEnabled(False)

        # vbox_exp_h_i_dir = QtGui.QHBoxLayout()
        # vbox_exp_h_i_dir.addWidget(self.butt_exp_i_dir_start)
        # vbox_exp_h_i_dir.addWidget(self.butt_exp_i_dir_stop)

        # =============================================

        self.ctrl_exp_i_index_go_static = QtGui.QLabel()
        self.ctrl_exp_i_index_go_static.setText("Go index")

        self.ctrl_exp_i_index_go = QtGui.QSpinBox()
        self.ctrl_exp_i_index_go.setMinimum(1)
        self.ctrl_exp_i_index_go.setSingleStep(1)
        self.ctrl_exp_i_index_go.setMaximum(9999)
        self.ctrl_exp_i_index_go.setProperty("value", 1)
        self.exp_val_index_go = self.ctrl_exp_i_index_go.value()
        self.ctrl_exp_i_index_go.setKeyboardTracking(False)
        self.ctrl_exp_i_index_go.setEnabled(True)
        self.ctrl_exp_i_index_go.valueChanged.connect(self.ctrl_exp_i_index_go_Changed)

        self.lab_exp_i_now_index = QtGui.QLabel("")

        vbox_exp_h_ctrl_i_index = QtGui.QHBoxLayout()
        vbox_exp_h_ctrl_i_index.addStretch(1)
        vbox_exp_h_ctrl_i_index.addWidget(self.ctrl_exp_i_index_go_static)
        vbox_exp_h_ctrl_i_index.addWidget(self.ctrl_exp_i_index_go)
        vbox_exp_h_ctrl_i_index.addStretch(1)
        vbox_exp_h_ctrl_i_index.addWidget(self.lab_exp_i_now_index)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_exp_start = QtGui.QPushButton("Start set-up exp", self)
        self.connect(self.butt_exp_start, SIGNAL("pressed()"), self.butt_exp_start_Changed)
        self.butt_exp_start.setEnabled(False)

        # ==============================================

        self.butt_exp_stop = QtGui.QPushButton("Stop setup exp", self)
        self.connect(self.butt_exp_stop, SIGNAL("pressed()"), self.butt_exp_stop_Changed)
        self.butt_exp_stop.setEnabled(False)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.butt_exp_run = QtGui.QPushButton("Run exp", self)
        self.connect(self.butt_exp_run, SIGNAL("pressed()"), self.butt_exp_run_Changed)
        self.butt_exp_run.setEnabled(False)

        # ==============================================

        self.butt_exp_idle = QtGui.QPushButton("Idle exp", self)
        self.connect(self.butt_exp_idle, SIGNAL("pressed()"), self.butt_exp_idle_Changed)
        self.butt_exp_idle.setEnabled(False)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.txt_exp_name_file = QtGui.QLineEdit()
        self.txt_exp_name_file.setPlaceholderText('f1_f2_vs_z__x0000_y000')
        # self.connect(self.butt_exp_run,SIGNAL("pressed()"),self.butt_exp_run_Changed)
        # self.butt_exp_run.setEnabled(False)

        # ==============================================

        self.butt_exp_save_file = QtGui.QPushButton("Save file", self)
        self.connect(self.butt_exp_save_file, SIGNAL("pressed()"), self.butt_exp_save_file_Changed)
        self.butt_exp_save_file.setEnabled(False)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.ctrl_exp_val_min_static = QtGui.QLabel()
        self.ctrl_exp_val_min_static.setText("Poz initial")

        self.ctrl_exp_val_min = QtGui.QDoubleSpinBox()
        self.ctrl_exp_val_min.setMinimum(0.0)
        self.ctrl_exp_val_min.setSingleStep(0.1000)
        self.ctrl_exp_val_min.setMaximum(25.0)
        self.ctrl_exp_val_min.setDecimals(5)
        self.ctrl_exp_val_min.setProperty("value", 7.16)
        self.exp_val_min_value = self.ctrl_exp_val_min.value()
        self.ctrl_exp_val_min.setKeyboardTracking(False)
        self.ctrl_exp_val_min.setEnabled(False)
        self.ctrl_exp_val_min.valueChanged.connect(self.ctrl_exp_val_min_Changed)

        vbox_exp_h_ctrl_val_min = QtGui.QHBoxLayout()
        vbox_exp_h_ctrl_val_min.addStretch(1)
        vbox_exp_h_ctrl_val_min.addWidget(self.ctrl_exp_val_min_static)
        vbox_exp_h_ctrl_val_min.addWidget(self.ctrl_exp_val_min)

        # ==============================================

        self.ctrl_exp_val_max_static = QtGui.QLabel()
        self.ctrl_exp_val_max_static.setText("Poz final")

        self.ctrl_exp_val_max = QtGui.QDoubleSpinBox()
        self.ctrl_exp_val_max.setMinimum(0.0)
        self.ctrl_exp_val_max.setSingleStep(0.1000)
        self.ctrl_exp_val_max.setMaximum(25.0)
        self.ctrl_exp_val_max.setDecimals(5)
        self.ctrl_exp_val_max.setProperty("value", 7.60)
        self.exp_val_max_value = self.ctrl_exp_val_max.value()
        self.ctrl_exp_val_max.setKeyboardTracking(False)
        self.ctrl_exp_val_max.setEnabled(False)
        self.ctrl_exp_val_max.valueChanged.connect(self.ctrl_exp_val_max_Changed)

        vbox_exp_h_ctrl_val_max = QtGui.QHBoxLayout()
        vbox_exp_h_ctrl_val_max.addStretch(1)
        vbox_exp_h_ctrl_val_max.addWidget(self.ctrl_exp_val_max_static)
        vbox_exp_h_ctrl_val_max.addWidget(self.ctrl_exp_val_max)

        # ==============================================

        self.ctrl_exp_val_step_static = QtGui.QLabel()
        self.ctrl_exp_val_step_static.setText("Step (mm)")

        self.ctrl_exp_val_step = QtGui.QDoubleSpinBox()
        self.ctrl_exp_val_step.setMinimum(0.0)
        self.ctrl_exp_val_step.setSingleStep(0.001)
        self.ctrl_exp_val_step.setMaximum(25.0)
        self.ctrl_exp_val_step.setDecimals(5)
        self.ctrl_exp_val_step.setProperty("value", 0.005)
        self.exp_val_step_value = self.ctrl_exp_val_step.value()
        self.ctrl_exp_val_step.setKeyboardTracking(False)
        self.ctrl_exp_val_step.setEnabled(False)
        self.ctrl_exp_val_step.valueChanged.connect(self.ctrl_exp_val_step_Changed)

        vbox_exp_h_ctrl_val_step = QtGui.QHBoxLayout()
        vbox_exp_h_ctrl_val_step.addStretch(1)
        vbox_exp_h_ctrl_val_step.addWidget(self.ctrl_exp_val_step_static)
        vbox_exp_h_ctrl_val_step.addWidget(self.ctrl_exp_val_step)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_exp = QtGui.QVBoxLayout()
        vbox_exp.addWidget(self.lab_exp_static)
        vbox_exp.addStretch(1)
        # vbox_exp.addLayout(vbox_exp_h_i_dir)
        vbox_exp.addWidget(self.butt_exp_i_dir_start)
        vbox_exp.addWidget(self.butt_exp_i_dir_stop)
        vbox_exp.addLayout(vbox_exp_h_ctrl_i_index)
        vbox_exp.addStretch(1)
        vbox_exp.addWidget(self.butt_exp_start)
        vbox_exp.addWidget(self.butt_exp_stop)
        vbox_exp.addStretch(1)
        vbox_exp.addWidget(self.butt_exp_run)
        vbox_exp.addWidget(self.butt_exp_idle)
        vbox_exp.addStretch(1)
        vbox_exp.addWidget(self.txt_exp_name_file)
        vbox_exp.addWidget(self.butt_exp_save_file)
        vbox_exp.addStretch(1)
        vbox_exp.addLayout(vbox_exp_h_ctrl_val_max)
        vbox_exp.addLayout(vbox_exp_h_ctrl_val_min)
        vbox_exp.addLayout(vbox_exp_h_ctrl_val_step)
        bound_box_exp.setLayout(vbox_exp)
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        vbox_ps_exp = QtGui.QVBoxLayout()
        vbox_ps_exp.addWidget(bound_box_ps)
        vbox_ps_exp.addWidget(bound_box_exp)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        # hbox.addLayout(vbox_plots)
        # hbox.addLayout(vbox_vi)
        # hbox.addLayout(vbox_ac)
        # hbox.addLayout(vbox_ps)
        hbox.addWidget(bound_box_plots)
        hbox.addWidget(bound_box_vi)
        # hbox.addWidget(bound_box_ac)
        hbox.addLayout(vbox_ac_rand)
        # hbox.addWidget(bound_box_ps)
        hbox.addLayout(vbox_ps_exp)

        self.setLayout(hbox)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.focus = 1.0
        self.lab_focus.setText(str(self.focus))
        self.round_factor = 0.5
        self.lab_round.setText(str(self.round_factor))
        self.number_beads = 0
        self.lab_bead.setText(str(self.number_beads))
        self.center_x = 0
        self.lab_center_x.setText(str(self.center_x))
        self.center_y = 0
        self.lab_center_y.setText(str(self.center_y))
        self.width = 0
        self.lab_width.setText(str(self.width))
        self.height = 0
        self.lab_height.setText(str(self.height))

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.focus_2 = 1.0
        self.lab_focus_2.setText(str(self.focus_2))
        self.round_factor_2 = 0.5
        self.lab_round_2.setText(str(self.round_factor_2))
        self.number_beads_2 = 0
        self.lab_bead_2.setText(str(self.number_beads_2))
        self.center_x_2 = 0
        self.lab_center_x_2.setText(str(self.center_x_2))
        self.center_y_2 = 0
        self.lab_center_y_2.setText(str(self.center_y_2))
        self.width_2 = 0
        self.lab_width_2.setText(str(self.width_2))
        self.height_2 = 0
        self.lab_height_2.setText(str(self.height_2))

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.val_coord_z_bead = -1000.0
        self.lab_bead_z_coord.setText(str(self.val_coord_z_bead))

        self.val_act_pos = -1000.0
        self.lab_act_pos.setText(str(self.val_act_pos))
        self.connect(self.th_actuator, SIGNAL("z_coord_send(QString)"), self.z_coord_display, Qt.DirectConnection)
        # self.connect(self.th_actuator,SIGNAL("z_coord_send(QString)"),self.z_coord_display,Qt.DirectConnection)

        self.val_act_err = ' '
        self.lab_act_err.setText(self.val_act_err)
        self.connect(self.th_actuator, SIGNAL("error_status_send(QString)"), self.error_status_display,
                     Qt.DirectConnection)

        self.val_act_sta = ' '
        self.lab_act_sta.setText(self.val_act_sta)
        self.connect(self.th_actuator, SIGNAL("status_send(QString)"), self.status_display, Qt.DirectConnection)

        self.val_act_lerr = ' '
        self.lab_act_lerr.setText(self.val_act_lerr)
        self.connect(self.th_actuator, SIGNAL("error_send(QString)"), self.error_display, Qt.DirectConnection)

        self.connect(self.th_actuator, SIGNAL("adj_manual_z_for_tracking()"), self.error_lim_disable_track,
                     Qt.DirectConnection)

        # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        # The above lines make the link between the signal emitted by th_actuator thread with the slot(method)
        # from main tread. These methods can accept parameters / values from secondary thread. Very important it's
        # the statement of Direct Connection which is used by Qt to link the two threads.
        #  &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

        self.val_ps_on_off = ''
        self.lab_psu_on_off.setText(str(self.val_ps_on_off))

        '''self.val_ard_err = ' '
        self.lab_ard_status.setText(self.val_ard_err)
        self.connect(self.th_power_supp,SIGNAL("flag_ps_send(QString)"),self.flag_ps_display,Qt.DirectConnection)
        '''
        self.curr_1_changed = True
        self.curr_2_changed = True
        self.curr_3_changed = True
        self.curr_4_changed = True

        self.connect(self.th_power_supp, SIGNAL("temp_C_send(QString)"), self.temperature_display, Qt.DirectConnection)
        self.connect(self.th_power_supp, SIGNAL("temp_C_send2(QString)"), self.temperature_display2,
                     Qt.DirectConnection)
        self.connect(self.th_power_supp, SIGNAL("temp_C_send3(QString)"), self.temperature_display3,
                     Qt.DirectConnection)
        # self.connect(self.th_power_supp,SIGNAL("temp_C_send4(QString)"),self.temperature_display4,Qt.DirectConnection)

        # self.connect(self.th_temper_2,SIGNAL("temp_C_send(QString)"),self.temperature_display,Qt.DirectConnection)
        # self.connect(self.th_power_supp,SIGNAL("temp_C_send2(QString)"),self.temperature_display2,Qt.DirectConnection)

        #  &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.connect(self.th_experiments, SIGNAL("exp_ended()"), self.butt_exp_idle_Changed, Qt.DirectConnection)
        # self.connect(self.th_experiments,SIGNAL("plot_f_vs_z_initial()"),self.setup_plot_f_vs_z,Qt.DirectConnection)
        # self.connect(self.th_experiments,SIGNAL("plot_f_vs_z_running()"),self.update_plot_f_vs_z,Qt.DirectConnection)
        self.connect(self.th_experiments, SIGNAL("experiment_save_picture()"), self.update_save_pict,
                     Qt.DirectConnection)
        self.connect(self.th_experiments, SIGNAL("log_exp_stack_init()"), self.log_exp_stack_init, Qt.DirectConnection)
        self.connect(self.th_experiments, SIGNAL("log_exp_stack_running()"), self.log_exp_stack_running,
                     Qt.DirectConnection)

        self.connect(self.th_exp_dir, SIGNAL("I_exp_actual_index_send(QString)"), self.update_index_exp_i_dir,
                     Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_UP()"), self.butt_pow_UP_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_RIGHT()"), self.butt_pow_RL_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_LEFT()"), self.butt_pow_LR_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_DOWN()"), self.butt_pow_DOWN_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_zUP()"), self.butt_pow_zUP_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_ZERO()"), self.butt_pow_zero_Changed, Qt.DirectConnection)
        # self.connect(self.th_exp_dir,SIGNAL("I_exp_CONF(QString,QString,QString,QString)"),
        #             self.butt_pow_config_Changed,Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_CONF(QString)"), self.butt_pow_config_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_coil_1()"), self.butt_pow_coil_1_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_coil_2()"), self.butt_pow_coil_2_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_coil_3()"), self.butt_pow_coil_3_Changed, Qt.DirectConnection)
        self.connect(self.th_exp_dir, SIGNAL("I_exp_coil_4()"), self.butt_pow_coil_4_Changed, Qt.DirectConnection)

        #  &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        self.connect(self.th_demag, SIGNAL("I_demag_send(QString)"), self.current_demag, Qt.DirectConnection)
        self.connect(self.th_demag, SIGNAL("demag_ended()"), self.butt_demag_stop_Changed, Qt.DirectConnection)

        self.save_pict_exp = False
        self.slider_plots_bead_size_Changed()
        # self.run_temperature_2()

        self.show()

    #    def run_temperature_2(self):
    #        self.th_temper_2.start()

    def butt_plots_reset_clock_Changed(self):
        self.time_old = time.clock()
        self.xxx = [time.clock() - self.time_old]
        # self.yyy = [self.focus]
        self.yyy = [self.val_coord_z_bead]
        # self.yyy_2 = [self.focus_2]
        return

    def butt_plots_start_Changed(self):
        self.do_plot = True
        self.butt_plots_start.setEnabled(False)
        self.butt_plots_stop.setEnabled(True)
        return

    def butt_plots_stop_Changed(self):
        self.do_plot = False
        self.butt_plots_start.setEnabled(True)
        self.butt_plots_stop.setEnabled(False)
        return

    def butt_save_img_cam1_Changed(self):
        path_file = os.getcwd() + '\\images\\'
        name_save = self.txt_plots_name_image1.text()
        path_file = path_file + name_save + '.jpeg'
        cv2.imwrite(path_file, self.n_frame_cam1)
        return

    def ctrl_plots_exposure_time_1_Changed(self):
        static_write_register = "10000010000000000000"
        cam1_exp_time_base_no_new = int(floor((self.ctrl_plots_exposure_time_1.value() / 0.02)))
        cam1_exp_time_base_no_new_bin = '{0:012b}'.format(cam1_exp_time_base_no_new)
        write_register = hex(int(static_write_register + cam1_exp_time_base_no_new_bin, 2))[2:-1]
        # print write_register
        camcapture.writeRegister("F0F0081C", write_register)
        return

    def ctrl_plots_exposure_time_2_Changed(self):
        static_write_register = "10000010000000000000"
        cam2_exp_time_base_no_new = int(floor((self.ctrl_plots_exposure_time_2.value() / 0.02)))
        cam2_exp_time_base_no_new_bin = '{0:012b}'.format(cam2_exp_time_base_no_new)
        write_register = hex(int(static_write_register + cam2_exp_time_base_no_new_bin, 2))[2:-1]
        # print write_register
        camcapture_2.writeRegister("F0F0081C", write_register)

        return

    def butt_start_rec_fileout_Changed(self):
        self.rec_calib = True
        self.butt_stop_rec_fileout.setEnabled(True)
        self.butt_start_rec_fileout.setEnabled(False)
        self.time_old_calib = time.clock()
        self.cal_t = [0.0]
        self.cal_z = [self.val_coord_z_bead]
        self.cal_xc1 = [self.center_x]
        self.cal_yc1 = [self.center_y]
        self.cal_foc1 = [self.focus]
        self.cal_xc2 = [self.center_x_2]
        self.cal_yc2 = [self.center_y_2]
        self.cal_foc2 = [self.focus_2]
        self.cal_temp = [self.temp_C]
        self.cal_temp2 = [self.temp2_C]
        self.cal_temp3 = [self.temp3_C]
        # self.cal_temp4=[self.temp4_C]
        self.cal_i1 = [self.ctrl_curr_1.value()]
        self.cal_i2 = [self.ctrl_curr_2.value()]
        self.cal_i3 = [self.ctrl_curr_3.value()]
        self.cal_i4 = [self.ctrl_curr_4.value()]
        self.cal_pws = [self.butt_pow_stop.isEnabled()]
        self.cal_config_psw = [self.config_curr]
        self.cal_xc1_trans = [(self.center_x - self.origin_x) / self.conv_um_pix]
        self.cal_yc1_trans = [(self.center_y - self.origin_y) / self.conv_um_pix]
        self.cal_zb_oil_trans = [(self.z_c_oil - self.val_coord_z_bead) * 1000.0]
        self.cal_zb_air_trans = [(self.z_c_oil - self.val_coord_z_bead) * 1000.0 * self.n_oil]
        self.cal_exp_index = [self.th_exp_dir.actual_index]
        self.cal_exp_go_away = [str(self.th_exp_dir.go_away_from_origin)[0]]

        return

    def calib_fileout_update(self):
        self.cal_t.append(self.time_calib - self.time_old_calib)
        self.cal_z.append(self.val_coord_z_bead)
        self.cal_xc1.append(self.center_x)
        self.cal_yc1.append(self.center_y)
        self.cal_foc1.append(self.focus)
        self.cal_xc2.append(self.center_x_2)
        self.cal_yc2.append(self.center_y_2)
        self.cal_foc2.append(self.focus_2)
        self.cal_temp.append(self.temp_C)
        self.cal_temp2.append(self.temp2_C)
        self.cal_temp3.append(self.temp3_C)
        # self.cal_temp4.append(self.temp4_C)

        self.cal_i1.append(self.ctrl_curr_1.value())
        self.cal_i2.append(self.ctrl_curr_2.value())
        self.cal_i3.append(self.ctrl_curr_3.value())
        self.cal_i4.append(self.ctrl_curr_4.value())
        self.cal_pws.append(self.butt_pow_stop.isEnabled())
        self.cal_config_psw.append(self.config_curr)
        self.cal_xc1_trans.append((self.center_x - self.origin_x) / self.conv_um_pix)
        self.cal_yc1_trans.append((self.center_y - self.origin_y) / self.conv_um_pix)
        self.cal_zb_oil_trans.append((self.z_c_oil - self.val_coord_z_bead) * 1000.0)
        self.cal_zb_air_trans.append((self.z_c_oil - self.val_coord_z_bead) * 1000.0 * self.n_oil)
        self.cal_exp_index.append(self.th_exp_dir.actual_index)
        self.cal_exp_go_away.append(str(self.th_exp_dir.go_away_from_origin)[0])

        return

    def butt_stop_rec_fileout_Changed(self):
        self.rec_calib = False
        self.butt_stop_rec_fileout.setEnabled(False)
        self.butt_start_rec_fileout.setEnabled(True)
        self.txt_plots_name_fileout.setReadOnly(False)
        return

    def butt_start_rec_fileout_Changed_new(self):
        self.rec_calib = True
        self.butt_stop_rec_fileout.setEnabled(True)
        self.butt_start_rec_fileout.setEnabled(False)
        self.txt_plots_name_fileout.setReadOnly(True)

        path_file = os.getcwd() + '\\calibration\\'
        name_save = self.txt_plots_name_fileout.text()

        if name_save == '':
            name_save = '_default'

        path_file_3 = path_file + name_save + '_exp.dat'
        path_file_2 = path_file + name_save + '_mod.dat'
        path_file = path_file + name_save + '_raw.dat'

        if self.th_exp_dir.flag_running == 'T':
            f_name_3 = open(path_file_3, 'w')

        f_name_2 = open(path_file_2, 'w')
        f_name = open(path_file, 'w')

        to_write_2 = 't(sec), t_cor(sec), xb(um), yb(um), zb_oil(um), zb_air(um), focus1, focus2,'
        to_write_2 = to_write_2 + 'temp(C), temp2(C), temp3(C), I1(A), I2(A), I3(A), I4(A),PWS(ON/OFF),config(1-6/7),'
        to_write_2 = to_write_2 + ' spim_box_small(Y/N), spim_box_big(Y/N) ' + str(
            self.z_bead_bottom)  # +' , temp3(C)#, temp4(C)'

        to_write_3 = to_write_2 + ', I_conf_index, Away_origin(True/False)'

        to_write = 't(sec), t_cor(sec), z(mm), xc1(pix), yc1(pix), focus1, xc2(pix), yc2(pix), focus2,'
        to_write = to_write + 'temp(C), temp2(C), temp3(C), I1(A), I2(A), I3(A), I4(A),PWS(ON/OFF) ' + str(
            self.z_bead_bottom)

        if self.th_exp_dir.flag_running == 'T':
            f_name_3.write(to_write_3 + '\n')

        f_name_2.write(to_write_2 + '\n')
        f_name.write(to_write + '\n')

        self.time_old_calib = time.clock()
        cal_t_new = time.clock() - self.time_old_calib
        cal_z_new = self.val_coord_z_bead
        cal_xc1_new = self.center_x
        cal_yc1_new = self.center_y
        cal_foc1_new = self.focus
        cal_xc2_new = self.center_x_2
        cal_yc2_new = self.center_y_2
        cal_foc2_new = self.focus_2
        cal_temp_new = self.temp_C
        cal_temp2_new = self.temp2_C
        cal_temp3_new = self.temp3_C
        # cal_temp4_new       =self.temp4_C
        cal_i1_new = self.ctrl_curr_1.value()
        cal_i2_new = self.ctrl_curr_2.value()
        cal_i3_new = self.ctrl_curr_3.value()
        cal_i4_new = self.ctrl_curr_4.value()
        cal_pws_new = self.butt_pow_stop.isEnabled()
        cal_config_psw_new = self.config_curr
        cal_xc1_trans_new = (self.center_x - self.origin_x) / self.conv_um_pix
        cal_yc1_trans_new = (self.center_y - self.origin_y) / self.conv_um_pix
        cal_zb_oil_trans_new = (self.z_c_oil - self.val_coord_z_bead) * 1000.0
        cal_zb_air_trans_new = (self.z_c_oil - self.val_coord_z_bead) * 1000.0 * self.n_oil
        cal_exp_index_new = self.th_exp_dir.actual_index
        cal_exp_go_away_new = str(self.th_exp_dir.go_away_from_origin)[0]

        theta = -45.0 * np.pi / 180.0

        to_write = str(cal_t_new) + ',' + str(cal_t_new) + ',' + str(cal_z_new) + ',' + str(cal_xc1_new) + ','
        to_write = to_write + str(cal_yc1_new) + ',' + str(cal_foc1_new) + ','
        to_write = to_write + str(cal_xc2_new) + ',' + str(cal_yc2_new) + ','
        to_write = to_write + str(cal_foc2_new) + ',' + str(cal_temp_new) + ',' + str(cal_temp2_new) + ','
        to_write = to_write + str(cal_temp3_new) + ','
        to_write = to_write + str(cal_i1_new) + ',' + str(cal_i2_new) + ','
        to_write = to_write + str(cal_i3_new) + ',' + str(cal_i4_new) + ','
        to_write = to_write + str(cal_pws_new)

        f_name.write(to_write + '\n')

        xxx_spim_air_1 = cal_xc1_trans_new - self.shift_spim
        yyy_spim_air_1 = cal_yc1_trans_new
        zzz_spim_air_1 = cal_zb_air_trans_new + self.shift_spim

        xxx_spim_air_2 = xxx_spim_air_1 * np.cos(theta) - zzz_spim_air_1 * np.sin(theta)
        yyy_spim_air_2 = yyy_spim_air_1
        zzz_spim_air_2 = xxx_spim_air_1 * np.sin(theta) + zzz_spim_air_1 * np.cos(theta)

        if (abs(xxx_spim_air_2) <= 226.0) and (abs(yyy_spim_air_2) <= 226.0) and (abs(zzz_spim_air_2) <= 70.0):
            spim_box = 'YES'
        else:
            spim_box = 'NO'

        if ((abs(xxx_spim_air_2) <= (226.0 + 50.0)) and (abs(yyy_spim_air_2) <= 226.0 + 50.0) and (
                abs(zzz_spim_air_2) <= (50.0 + 40.0))):
            spim_box_2 = 'YES'
        else:
            spim_box_2 = 'NO'

        to_write_2 = str(cal_t_new) + ',' + str(cal_t_new) + ',' \
                     + str(cal_xc1_trans_new) + ',' + str(cal_yc1_trans_new) + ',' \
                     + str(cal_zb_oil_trans_new) + ',' + str(cal_zb_air_trans_new) + ',' \
                     + str(cal_foc1_new) + ',' + str(cal_foc2_new) + ',' + str(cal_temp_new) + ',' \
                     + str(cal_temp2_new) + ',' + str(cal_temp3_new) + ',' \
                     + str(cal_i1_new) + ',' + str(cal_i2_new) + ',' + str(cal_i3_new) + ',' \
                     + str(cal_i4_new) + ',' + str(cal_pws_new) + ',' + str(cal_config_psw_new) + ',' \
                     + spim_box + ',' + spim_box_2

        f_name_2.write(to_write_2 + '\n')

        to_write_3 = to_write_2 + ',' + str(cal_exp_index_new) + ',' + cal_exp_go_away_new

        if self.th_exp_dir.flag_running == 'T':
            f_name_3.write(to_write_3 + '\n')

        f_name.close()
        f_name_2.close()
        if self.th_exp_dir.flag_running == 'T':
            f_name_3.close()

        return

    def calib_fileout_update_new(self):

        path_file = os.getcwd() + '\\calibration\\'
        name_save = self.txt_plots_name_fileout.text()

        if name_save == '':
            name_save = '_default'

        path_file_3 = path_file + name_save + '_exp.dat'
        path_file_2 = path_file + name_save + '_mod.dat'
        path_file = path_file + name_save + '_raw.dat'

        if self.th_exp_dir.flag_running == 'T':
            f_name_3 = open(path_file_3, 'a')

        f_name_2 = open(path_file_2, 'a')
        f_name = open(path_file, 'a')

        cal_t_new = self.time_calib - self.time_old_calib
        cal_z_new = self.val_coord_z_bead
        cal_xc1_new = self.center_x
        cal_yc1_new = self.center_y
        cal_foc1_new = self.focus
        cal_xc2_new = self.center_x_2
        cal_yc2_new = self.center_y_2
        cal_foc2_new = self.focus_2
        cal_temp_new = self.temp_C
        cal_temp2_new = self.temp2_C
        cal_temp3_new = self.temp3_C
        # cal_temp4_new       =self.temp4_C
        cal_i1_new = self.ctrl_curr_1.value()
        cal_i2_new = self.ctrl_curr_2.value()
        cal_i3_new = self.ctrl_curr_3.value()
        cal_i4_new = self.ctrl_curr_4.value()
        cal_pws_new = self.butt_pow_stop.isEnabled()
        cal_config_psw_new = self.config_curr
        cal_xc1_trans_new = (self.center_x - self.origin_x) / self.conv_um_pix
        cal_yc1_trans_new = (self.center_y - self.origin_y) / self.conv_um_pix
        cal_zb_oil_trans_new = (self.z_c_oil - self.val_coord_z_bead) * 1000.0
        cal_zb_air_trans_new = (self.z_c_oil - self.val_coord_z_bead) * 1000.0 * self.n_oil
        cal_exp_index_new = self.th_exp_dir.actual_index
        cal_exp_go_away_new = str(self.th_exp_dir.go_away_from_origin)[0]

        theta = -45.0 * np.pi / 180.0

        to_write = str(cal_t_new) + ',' + str(cal_t_new) + ',' + str(cal_z_new) + ',' + str(cal_xc1_new) + ','
        to_write = to_write + str(cal_yc1_new) + ',' + str(cal_foc1_new) + ','
        to_write = to_write + str(cal_xc2_new) + ',' + str(cal_yc2_new) + ','
        to_write = to_write + str(cal_foc2_new) + ',' + str(cal_temp_new) + ',' + str(cal_temp2_new) + ','
        to_write = to_write + str(cal_temp3_new) + ','
        to_write = to_write + str(cal_i1_new) + ',' + str(cal_i2_new) + ','
        to_write = to_write + str(cal_i3_new) + ',' + str(cal_i4_new) + ','
        to_write = to_write + str(cal_pws_new)

        f_name.write(to_write + '\n')

        xxx_spim_air_1 = cal_xc1_trans_new - self.shift_spim
        yyy_spim_air_1 = cal_yc1_trans_new
        zzz_spim_air_1 = cal_zb_air_trans_new + self.shift_spim

        xxx_spim_air_2 = xxx_spim_air_1 * np.cos(theta) - zzz_spim_air_1 * np.sin(theta)
        yyy_spim_air_2 = yyy_spim_air_1
        zzz_spim_air_2 = xxx_spim_air_1 * np.sin(theta) + zzz_spim_air_1 * np.cos(theta)

        if (abs(xxx_spim_air_2) <= 226.0) and (abs(yyy_spim_air_2) <= 226.0) and (abs(zzz_spim_air_2) <= 70.0):
            spim_box = 'YES'
        else:
            spim_box = 'NO'

        if ((abs(xxx_spim_air_2) <= (226.0 + 50.0)) and (abs(yyy_spim_air_2) <= 226.0 + 50.0) and (
                abs(zzz_spim_air_2) <= (50.0 + 40.0))):
            spim_box_2 = 'YES'
        else:
            spim_box_2 = 'NO'

        to_write_2 = str(cal_t_new) + ',' + str(cal_t_new) + ',' \
                     + str(cal_xc1_trans_new) + ',' + str(cal_yc1_trans_new) + ',' \
                     + str(cal_zb_oil_trans_new) + ',' + str(cal_zb_air_trans_new) + ',' \
                     + str(cal_foc1_new) + ',' + str(cal_foc2_new) + ',' + str(cal_temp_new) + ',' \
                     + str(cal_temp2_new) + ',' + str(cal_temp3_new) + ',' \
                     + str(cal_i1_new) + ',' + str(cal_i2_new) + ',' + str(cal_i3_new) + ',' \
                     + str(cal_i4_new) + ',' + str(cal_pws_new) + ',' + str(cal_config_psw_new) + ',' \
                     + spim_box + ',' + spim_box_2

        f_name_2.write(to_write_2 + '\n')

        to_write_3 = to_write_2 + ',' + str(cal_exp_index_new) + ',' + cal_exp_go_away_new

        if self.th_exp_dir.flag_running == 'T':
            f_name_3.write(to_write_3 + '\n')

        f_name.close()
        f_name_2.close()
        if self.th_exp_dir.flag_running == 'T':
            f_name_3.close()

        return

    def butt_save_fileout_Changed(self):
        path_file = os.getcwd() + '\\calibration\\'
        name_save = self.txt_plots_name_fileout.text()

        path_file_3 = path_file + name_save + '_exp.dat'
        path_file_2 = path_file + name_save + '_mod.dat'
        path_file = path_file + name_save + '_raw.dat'

        if self.th_exp_dir.flag_running == 'T':
            f_name_3 = open(path_file_3, 'w')

        f_name_2 = open(path_file_2, 'w')
        f_name = open(path_file, 'w')

        to_write_2 = 't(sec), t_cor(sec), xb(um), yb(um), zb_oil(um), zb_air(um), focus1, focus2,'
        to_write_2 = to_write_2 + 'temp(C), temp2(C), temp3(C), I1(A), I2(A), I3(A), I4(A),PWS(ON/OFF),config(1-6/7),'
        to_write_2 = to_write_2 + ' spim_box_small(Y/N), spim_box_big(Y/N) ' + str(
            self.z_bead_bottom)  # +' , temp3(C)#, temp4(C)'

        to_write_3 = to_write_2 + ', I_conf_index, Away_origin(True/False)'

        to_write = 't(sec), t_cor(sec), z(mm), xc1(pix), yc1(pix), focus1, xc2(pix), yc2(pix), focus2,'
        to_write = to_write + 'temp(C), temp2(C), temp3(C), I1(A), I2(A), I3(A), I4(A),PWS(ON/OFF) ' + str(
            self.z_bead_bottom)

        if self.th_exp_dir.flag_running == 'T':
            f_name_3.write(to_write_3 + '\n')

        f_name_2.write(to_write_2 + '\n')
        f_name.write(to_write + '\n')

        theta = -45.0 * np.pi / 180.0

        for ii in range(0, 2):
            to_write = str(self.cal_t[ii]) + ',' + str(self.cal_t[ii]) + ',' + str(self.cal_z[ii]) + ',' + str(
                self.cal_xc1[ii]) + ','
            to_write = to_write + str(self.cal_yc1[ii]) + ',' + str(self.cal_foc1[ii]) + ','
            to_write = to_write + str(self.cal_xc2[ii]) + ',' + str(self.cal_yc2[ii]) + ','
            to_write = to_write + str(self.cal_foc2[ii]) + ',' + str(self.cal_temp[ii]) + ',' + str(
                self.cal_temp2[ii]) + ','
            to_write = to_write + str(self.cal_temp3[ii]) + ','
            to_write = to_write + str(self.cal_i1[ii]) + ',' + str(self.cal_i2[ii]) + ','
            to_write = to_write + str(self.cal_i3[ii]) + ',' + str(self.cal_i4[ii]) + ','
            to_write = to_write + str(self.cal_pws[ii])

            f_name.write(to_write + '\n')

            xxx_spim_air_1 = self.cal_xc1_trans[ii] - self.shift_spim
            yyy_spim_air_1 = self.cal_yc1_trans[ii]
            zzz_spim_air_1 = self.cal_zb_air_trans[ii] + self.shift_spim

            xxx_spim_air_2 = xxx_spim_air_1 * np.cos(theta) - zzz_spim_air_1 * np.sin(theta)
            yyy_spim_air_2 = yyy_spim_air_1
            zzz_spim_air_2 = xxx_spim_air_1 * np.sin(theta) + zzz_spim_air_1 * np.cos(theta)

            if (abs(xxx_spim_air_2) <= 226.0) and (abs(yyy_spim_air_2) <= 226.0) and (abs(zzz_spim_air_2) <= 70.0):
                spim_box = 'YES'
            else:
                spim_box = 'NO'

            if ((abs(xxx_spim_air_2) <= (226.0 + 50.0)) and (abs(yyy_spim_air_2) <= 226.0 + 50.0) and (
                    abs(zzz_spim_air_2) <= (50.0 + 40.0))):
                spim_box_2 = 'YES'
            else:
                spim_box_2 = 'NO'

            to_write_2 = str(self.cal_t[ii]) + ',' + str(self.cal_t[ii]) + ',' \
                         + str(self.cal_xc1_trans[ii]) + ',' + str(self.cal_yc1_trans[ii]) + ',' \
                         + str(self.cal_zb_oil_trans[ii]) + ',' + str(self.cal_zb_air_trans[ii]) + ',' \
                         + str(self.cal_foc1[ii]) + ',' + str(self.cal_foc2[ii]) + ',' + str(self.cal_temp[ii]) + ',' \
                         + str(self.cal_temp2[ii]) + ',' + str(self.cal_temp3[ii]) + ',' \
                         + str(self.cal_i1[ii]) + ',' + str(self.cal_i2[ii]) + ',' + str(self.cal_i3[ii]) + ',' \
                         + str(self.cal_i4[ii]) + ',' + str(self.cal_pws[ii]) + ',' + str(self.cal_config_psw[ii]) + ',' \
                         + spim_box + ',' + spim_box_2

            f_name_2.write(to_write_2 + '\n')

            to_write_3 = to_write_2 + ',' + str(self.cal_exp_index[ii]) + ',' + self.cal_exp_go_away[ii]

            if self.th_exp_dir.flag_running == 'T':
                f_name_3.write(to_write_3 + '\n')

        ttime_corect_old = self.cal_t[1]

        for ii in range(2, len(self.cal_t)):
            if (self.cal_t[ii] - self.cal_t[ii - 1]) < 0.15:
                ttime_corect_new = ttime_corect_old + 0.1
                ttime_corect_old = ttime_corect_new
            elif (self.cal_t[ii] - self.cal_t[ii - 1]) >= 0.15 and (self.cal_t[ii] - self.cal_t[ii - 1]) < 0.25:
                ttime_corect_new = ttime_corect_old + 0.2
                ttime_corect_old = ttime_corect_new
            elif (self.cal_t[ii] - self.cal_t[ii - 1]) >= 0.25 and (self.cal_t[ii] - self.cal_t[ii - 1]) < 0.35:
                ttime_corect_new = ttime_corect_old + 0.3
                ttime_corect_old = ttime_corect_new
            else:
                ttime_corect_new = self.cal_t[ii]
                ttime_corect_old = ttime_corect_new

            to_write = str(self.cal_t[ii]) + ',' + str(ttime_corect_new) + ',' + str(self.cal_z[ii]) + ',' + str(
                self.cal_xc1[ii]) + ','
            to_write = to_write + str(self.cal_yc1[ii]) + ',' + str(self.cal_foc1[ii]) + ','
            to_write = to_write + str(self.cal_xc2[ii]) + ',' + str(self.cal_yc2[ii]) + ','
            to_write = to_write + str(self.cal_foc2[ii]) + ',' + str(self.cal_temp[ii]) + ','
            to_write = to_write + str(self.cal_temp2[ii]) + ',' + str(self.cal_temp3[ii]) + ','
            to_write = to_write + str(self.cal_i1[ii]) + ',' + str(self.cal_i2[ii]) + ','
            to_write = to_write + str(self.cal_i3[ii]) + ',' + str(self.cal_i4[ii]) + ','
            to_write = to_write + str(self.cal_pws[ii])

            f_name.write(to_write + '\n')

            xxx_spim_air_1 = self.cal_xc1_trans[ii] - self.shift_spim
            yyy_spim_air_1 = self.cal_yc1_trans[ii]
            zzz_spim_air_1 = self.cal_zb_air_trans[ii] + self.shift_spim

            xxx_spim_air_2 = xxx_spim_air_1 * np.cos(theta) - zzz_spim_air_1 * np.sin(theta)
            yyy_spim_air_2 = yyy_spim_air_1
            zzz_spim_air_2 = xxx_spim_air_1 * np.sin(theta) + zzz_spim_air_1 * np.cos(theta)

            if (abs(xxx_spim_air_2) <= 226.0) and (abs(yyy_spim_air_2) <= 226.0) and (abs(zzz_spim_air_2) <= 70.0):
                spim_box = 'YES'
            else:
                spim_box = 'NO'

            if (abs(xxx_spim_air_2) <= (226.0 + 50.0) and (abs(yyy_spim_air_2) <= 226.0 + 50.0) and (
                    abs(zzz_spim_air_2) <= (50.0 + 40.0))):
                spim_box_2 = 'YES'
            else:
                spim_box_2 = 'NO'

            to_write_2 = str(self.cal_t[ii]) + ',' + str(ttime_corect_new) + ',' \
                         + str(self.cal_xc1_trans[ii]) + ',' + str(self.cal_yc1_trans[ii]) + ',' \
                         + str(self.cal_zb_oil_trans[ii]) + ',' + str(self.cal_zb_air_trans[ii]) + ',' \
                         + str(self.cal_foc1[ii]) + ',' + str(self.cal_foc2[ii]) + ',' + str(self.cal_temp[ii]) + ',' \
                         + str(self.cal_temp2[ii]) + ',' + str(self.cal_temp3[ii]) + ',' \
                         + str(self.cal_i1[ii]) + ',' + str(self.cal_i2[ii]) + ',' + str(self.cal_i3[ii]) + ',' \
                         + str(self.cal_i4[ii]) + ',' + str(self.cal_pws[ii]) + ',' + str(self.cal_config_psw[ii]) + ',' \
                         + spim_box + ',' + spim_box_2

            f_name_2.write(to_write_2 + '\n')

            to_write_3 = to_write_2 + ',' + str(self.cal_exp_index[ii]) + ',' + self.cal_exp_go_away[ii]

            if self.th_exp_dir.flag_running == 'T':
                f_name_3.write(to_write_3 + '\n')

        f_name.close()
        f_name_2.close()
        if self.th_exp_dir.flag_running == 'T':
            f_name_3.close()

        return

    def slider_plots_bead_size_Changed(self):

        self.slider_bead_size_value = self.slider_plots_bead_size.value()

        if (self.slider_bead_size_value == 1):  # bead 18.82
            self.ctrl_area_max.setProperty("value", 1500)
            self.ctrl_area_min.setProperty("value", 600)
            self.diam_bead_value = 18.82
        elif (self.slider_bead_size_value == 2):  # bead 41.13
            self.ctrl_area_max.setProperty("value", 7000)
            self.ctrl_area_min.setProperty("value", 990)
            self.diam_bead_value = 41.13
        else:
            print "ERROR"

        self.ctrl_plots_z_bead_bottom_Changed()

        return

    def butt_plots_letter_point_Changed(self):

        box_letter_x = self.ctrl_plots_letter_x.value()
        box_letter_y = self.ctrl_plots_letter_y.value()
        box_letter_size_x = self.ctrl_plots_letter_size.value()
        box_letter_step = int(box_letter_size_x / (5 - 1))
        no_steps_diag = self.ctrl_plots_let_index_diag.value()

        point_x = self.ctrl_plots_letter_point_x.value()  # 1--5
        point_y = self.ctrl_plots_letter_point_y.value()  # 1--7

        if QtGui.QAbstractButton.isChecked(self.checkbox_diag_move):
            x_bead_ini_diag = self.bead_diag_initial_x
            y_bead_ini_diag = self.bead_diag_initial_y
            x_bead_fin_diag = box_letter_x + (point_x - 1) * box_letter_step
            y_bead_fin_diag = box_letter_y + (point_y - 1) * box_letter_step

            self.index_letter = self.index_letter + 1
            self.x_target = (x_bead_fin_diag - x_bead_ini_diag) / no_steps_diag * self.index_letter + x_bead_ini_diag
            self.y_target = (y_bead_fin_diag - y_bead_ini_diag) / no_steps_diag * self.index_letter + y_bead_ini_diag

        else:
            self.x_target = box_letter_x + (point_x - 1) * box_letter_step
            self.y_target = box_letter_y + (point_y - 1) * box_letter_step

        self.lab_let_point_coord_x.setText(str(self.x_target))
        self.lab_let_point_coord_y.setText(str(self.y_target))
        self.lab_let_index_diag.setText(str(self.index_letter))

        return

    def checkbox_diag_move_Changed(self, param):
        if param == True:
            self.index_letter = 0
            self.lab_let_index_diag.setText(str(self.index_letter))
            self.bead_diag_initial_x = self.center_x
            self.bead_diag_initial_y = self.center_y

        return

    def butt_plots_tab_letter_seq_tlaps_start_Changed(self):
        self.seq_time_laps_run = True
        self.butt_plots_tab_letter_seq_tlaps_start.setEnabled(False)
        self.butt_plots_tab_letter_seq_tlaps_stop.setEnabled(True)

        self.period_seq_tlaps = self.ctrl_random_timelaps_frame_no.value() * self.ctrl_random_timelaps_frame_time.value()
        self.time_seq_tlaps = time.clock()

        self.butt_random_time_laps_start_Changed()

        return

    def butt_plots_tab_letter_seq_tlaps_stop_Changed(self):
        self.seq_time_laps_run = False
        self.butt_plots_tab_letter_seq_tlaps_start.setEnabled(True)
        self.butt_plots_tab_letter_seq_tlaps_stop.setEnabled(False)

        return

    def seq_tlaps_increment_file_name(self):

        folder_name_str = self.txt_random_time_lapse_folder.text()
        pos = folder_name_str.find('laps')
        index = int(folder_name_str[pos + 4:])
        folder_name_str_new = folder_name_str[:pos + 4] + str(index + 1)
        self.txt_random_time_lapse_folder.setText(folder_name_str_new)

        return

    def data_plot_changed(self):
        self.p1.setData(x=self.xxx, y=self.yyy)

    def data_plot_2_changed(self):
        self.p2.setData(x=self.xxx, y=self.yyy_2)

    def setup_plot_f_vs_z(self):
        self.xxx = [self.th_experiments.val_exper_real_time_z]
        self.yyy = [self.focus]
        self.yyy_2 = [self.focus_2]
        self.yyy_x1 = [self.center_x]
        self.yyy_x2 = [self.center_x_2]
        self.yyy_y1 = [self.center_y]
        self.yyy_y2 = [self.center_y_2]
        self.yyy_r1 = [self.round_factor]
        self.yyy_r2 = [self.round_factor_2]
        self.yyy_w1 = [self.width]
        self.yyy_w2 = [self.width_2]
        self.yyy_h1 = [self.height]
        self.yyy_h2 = [self.height_2]
        self.p1.setData(x=self.xxx, y=self.yyy)
        self.p2.setData(x=self.xxx, y=self.yyy_2)

    def update_plot_f_vs_z(self):
        self.xxx.append(self.th_experiments.val_exper_real_time_z)
        self.yyy.append(self.focus)
        self.yyy_2.append(self.focus_2)
        self.yyy_x1.append(self.center_x)
        self.yyy_x2.append(self.center_x_2)
        self.yyy_y1.append(self.center_y)
        self.yyy_y2.append(self.center_y_2)
        self.yyy_r1.append(self.round_factor)
        self.yyy_r2.append(self.round_factor_2)
        self.yyy_w1.append(self.width)
        self.yyy_w2.append(self.width_2)
        self.yyy_h1.append(self.height)
        self.yyy_h2.append(self.height_2)

        self.p1.setData(x=self.xxx, y=self.yyy)
        self.p2.setData(x=self.xxx, y=self.yyy_2)

    def ctrl_plots_z_bead_bottom_Changed(self):
        self.z_bead_bottom = self.ctrl_plots_z_bead_bottom.value()
        self.d_glass = 200.0
        self.d_oil = 1000.0
        self.diam_bead = self.diam_bead_value
        self.n_oil = 1.403
        self.n_glass = 1.474

        self.dist_bott_to_poles_air = (self.d_glass + self.d_oil - self.diam_bead / 2) / 1000.0
        self.dist_bott_to_poles_oil_glass = (self.d_glass / self.n_glass
                                             + (self.d_oil - self.diam_bead / 2) / self.n_oil) / 1000.0

        self.z_top_poles = self.z_bead_bottom + round(self.dist_bott_to_poles_oil_glass, 5)

        self.dist_centre_to_poles_air = (self.d_glass + self.d_oil / 2.0) / 1000.0
        self.dist_centre_to_poles_oil = (self.d_glass / self.n_glass + self.d_oil / 2.0 / self.n_oil) / 1000.0

        self.z_c_oil = round(self.z_top_poles - self.dist_centre_to_poles_oil, 5)
        self.z_c_air = round(self.z_top_poles - self.dist_centre_to_poles_air, 5)

        self.lab_plots_z_cent_oil.setText(str(self.z_c_oil))
        self.lab_plots_z_cent_air.setText(str(self.z_c_air))

        self.z_c_spim_air = self.z_c_air + self.shift_spim / 1000.0
        self.z_c_spim_oil = self.z_c_oil + self.shift_spim / 1000.0 / self.n_oil

        self.z_min_spim_air = round(self.z_c_spim_air - self.lenght_spim_xz / 1000.0, 5)
        self.z_max_spim_air = round(self.z_c_spim_air + self.lenght_spim_xz / 1000.0, 5)
        self.z_min_spim_oil = round(self.z_c_spim_oil - self.lenght_spim_xz / 1000.0 / self.n_oil, 5)
        self.z_max_spim_oil = round(self.z_c_spim_oil + self.lenght_spim_xz / 1000.0 / self.n_oil, 5)

        self.lab_plots_z_spim_min_air.setText(str(self.z_min_spim_air))
        self.lab_plots_z_spim_max_air.setText(str(self.z_max_spim_air))
        self.lab_plots_z_spim_min_oil.setText(str(self.z_min_spim_oil))
        self.lab_plots_z_spim_max_oil.setText(str(self.z_max_spim_oil))

        # print self.dist_bott_to_poles_air
        # print self.dist_bott_to_poles_oil_glass
        # print self.z_top_poles
        # print self.dist_centre_to_poles_air, self.dist_centre_to_poles_oil

        return

    def ctrl_plots_shift_spim_Changed(self):
        self.shift_spim = self.ctrl_plots_shift_spim.value()
        return

    def ctrl_plots_lenght_spim_volume_Changed(self):
        self.lenght_spim_xz = self.ctrl_plots_lenght_spim_volume_xz.value()
        self.lenght_spim_y = self.ctrl_plots_lenght_spim_volume_y.value()

        self.axa_x = 2588
        self.axa_y = 1940
        self.conv_um_pix = 2.008
        self.origin_x = int(round(self.axa_x / 2.0))
        self.origin_y = int(round(self.axa_y / 2.0))

        self.lenght_spim_pix_xz = int(round(self.lenght_spim_xz * self.conv_um_pix, 0))
        self.lenght_spim_pix_y = int(round(self.lenght_spim_y * self.conv_um_pix, 0))
        self.shift_spim_pix = int(round(self.shift_spim * self.conv_um_pix, 0))

        # self.spim_x_center = self.origin_x - int(self.shift_spim_pix)
        self.spim_x_center = self.origin_x + int(self.shift_spim_pix)
        self.spim_y_center = self.origin_y

        self.spim_x_min = self.spim_x_center - self.lenght_spim_pix_xz
        self.spim_x_max = self.spim_x_center + self.lenght_spim_pix_xz

        self.spim_y_min = self.spim_y_center - self.lenght_spim_pix_y
        self.spim_y_max = self.spim_y_center + self.lenght_spim_pix_y

        print self.origin_x, self.origin_y, self.lenght_spim_pix_xz, self.spim_x_center

    def chbox_trig_on_off_Changed(self, param):
        if param == False:
            ser_trig.write('OFF_Trig' + '\r\n')
        if param == True:
            ser_trig.write('ON_Trig' + '\r\n')
        return

    def ctrl_FPS_Changed(self):
        self.FPS_factor = self.ctrl_FPS.value()
        self.lab_real_FPS.setText(str(round(1000.0 / (2.0 * round(1000.0 / self.FPS_factor / 2.0, 0)), 3)))
        ser_trig.write('FPS ' + str(self.FPS_factor) + '\r\n')
        self.lab_delta_t.setText(str(2.0 * round(1000.0 / self.FPS_factor / 2.0, 0)))

    def text_changed_measured_fps(self):
        self.lab_measured_fps.setText(str(round(self.measured_fps, 4)))

    def butt_light_ON_Changed(self):
        ser_ps.write('Light_ON' + '\r\n')
        return

    def butt_light_OFF_Changed(self):
        ser_ps.write('Light_OFF' + '\r\n')
        return

    def temperature_display(self, param_temp):
        self.lab_temperature.setText(param_temp)

        try:
            float(param_temp)
            float_bool = True
        except ValueError:
            float_bool = False

        if float_bool == True:
            self.temp_C = round(float(param_temp), 1)

    def temperature_display2(self, param_temp):
        self.lab_temperature_coil.setText(param_temp)

        try:
            float(param_temp)
            float_bool = True
        except ValueError:
            float_bool = False

        if float_bool == True:
            self.temp2_C = round(float(param_temp), 1)

    def temperature_display3(self, param_temp):
        self.lab_temperature3.setText(param_temp)

        try:
            float(param_temp)
            float_bool = True
        except ValueError:
            float_bool = False

        if float_bool == True:
            self.temp3_C = round(float(param_temp), 1)

    # def temperature_display4(self,param_temp):
    #    self.lab_temperature4.setText(param_temp)

    #    try:
    #        float(param_temp)
    #        float_bool = True
    #    except ValueError:
    #        float_bool = False

    #    if float_bool == True:
    #        self.temp4_C = round(float(param_temp),1)

    def ctrl_L_grid_Changed(self):
        self.size_grid = self.ctrl_L_grid.value()

    def ctrl_zoom_Changed(self):
        self.zoom_factor = self.ctrl_zoom.value()

    def ctrl_area_max_Changed(self):
        self.area_factor_max = self.ctrl_area_max.value()

    def ctrl_area_min_Changed(self):
        self.area_factor_min = self.ctrl_area_min.value()

    def ctrl_circ_max_Changed(self):
        self.c_factor_max = self.ctrl_circ_max.value()

    def ctrl_circ_min_Changed(self):
        self.c_factor_min = self.ctrl_circ_min.value()

    def ctrl_ths_max_Changed(self):
        self.threshMax = self.ctrl_ths_max.value()

    def ctrl_ths_min_Changed(self):
        self.threshMin = self.ctrl_ths_min.value()

    def ctrl_ths_2_max_Changed(self):
        self.threshMax_2 = self.ctrl_ths_2_max.value()

    def ctrl_ths_2_min_Changed(self):
        self.threshMin_2 = self.ctrl_ths_2_min.value()

    def text_changed_focus(self):
        self.lab_focus.setText(str(self.focus))

    def text_changed_round(self):
        self.lab_round.setText(str(self.round_factor))

    def text_changed_bead(self):
        self.lab_bead.setText(str(self.number_beads))

    def text_changed_x_y(self):
        self.lab_center_x.setText(str(self.center_x))
        self.lab_center_y.setText(str(self.center_y))

    def text_changed_w_h(self):
        self.lab_width.setText(str(self.width))
        self.lab_height.setText(str(self.height))

    def text_changed_focus_2(self):
        self.lab_focus_2.setText(str(self.focus_2))

    def text_changed_round_2(self):
        self.lab_round_2.setText(str(self.round_factor_2))

    def text_changed_bead_2(self):
        self.lab_bead_2.setText(str(self.number_beads_2))

    def text_changed_x_y_2(self):
        self.lab_center_x_2.setText(str(self.center_x_2))
        self.lab_center_y_2.setText(str(self.center_y_2))

    def text_changed_w_h_2(self):
        self.lab_width_2.setText(str(self.width_2))
        self.lab_height_2.setText(str(self.height_2))

    def text_changed_delta_x_y(self):
        self.lab_delta_x.setText(str(self.delta_x))
        self.lab_delta_y.setText(str(self.delta_y))

    def butt_vi_send_cmd_Changed(self):
        self.th_power_supp.send_cmd_ps_index = self.ctrl_vi_send_cmd_index_ps.value()
        self.th_power_supp.send_cmd_ps_text = self.txt_vi_send_cmd_name.text()
        self.th_power_supp.send_cmd_ps_status = True
        return

    def text_changed_z_bead_coord(self):
        self.lab_bead_z_coord.setText(str(self.val_coord_z_bead))

    def z_coord_display(self, parameter):
        self.lab_act_pos.setText(parameter)
        if self.th_experiments.isRunning():
            self.th_experiments.val_exper_real_time_z = float(parameter)

    def error_status_display(self, parameter):
        self.lab_act_err.setText(parameter)

    def status_display(self, parameter):
        self.lab_act_sta.setText(parameter)

    def error_display(self, parameter):
        self.lab_act_lerr.setText(parameter)

    def butt_act_start_Changed(self):
        self.th_actuator.start()
        self.butt_act_start.setEnabled(False)
        self.butt_act_stop.setEnabled(True)
        self.butt_act_reset.setEnabled(True)
        self.butt_act_abs.setEnabled(True)
        self.butt_act_rel_pos.setEnabled(True)
        self.butt_act_rel_neg.setEnabled(True)
        self.butt_exp_start.setEnabled(True)
        self.ctrl_exp_val_max.setEnabled(True)
        self.ctrl_exp_val_min.setEnabled(True)
        self.ctrl_exp_val_step.setEnabled(True)
        self.butt_act_track_on.setEnabled(True)

    def butt_act_stop_Changed(self):
        self.butt_act_start.setEnabled(True)
        self.butt_act_stop.setEnabled(False)
        self.butt_act_reset.setEnabled(False)
        self.butt_act_abs.setEnabled(False)
        self.butt_act_rel_pos.setEnabled(False)
        self.butt_act_rel_neg.setEnabled(False)
        self.th_actuator.done = True
        self.butt_exp_start.setEnabled(False)
        self.ctrl_exp_val_max.setEnabled(False)
        self.ctrl_exp_val_min.setEnabled(False)
        self.ctrl_exp_val_step.setEnabled(False)
        self.butt_exp_stop.setEnabled(False)
        self.butt_exp_run.setEnabled(False)
        self.butt_exp_idle.setEnabled(False)
        self.butt_act_track_on.setEnabled(False)
        self.butt_act_track_off.setEnabled(False)

    def butt_act_reset_Changed(self):
        self.th_actuator.reset_act = True

    def butt_act_track_on_Changed(self):
        self.butt_act_abs.setEnabled(False)
        self.butt_act_rel_pos.setEnabled(False)
        self.butt_act_rel_neg.setEnabled(False)
        self.butt_act_track_off.setEnabled(True)
        self.butt_act_track_on.setEnabled(False)
        self.th_actuator.track = True
        self.lab_act_track_error.setText('      ')

    def butt_act_track_off_Changed(self):
        self.butt_act_abs.setEnabled(True)
        self.butt_act_rel_pos.setEnabled(True)
        self.butt_act_rel_neg.setEnabled(True)
        self.butt_act_track_on.setEnabled(True)
        self.butt_act_track_off.setEnabled(False)
        self.th_actuator.track = False

    def error_lim_disable_track(self):
        self.lab_act_track_error.setText('STOP-adj man')
        self.butt_act_abs.setEnabled(True)
        self.butt_act_rel_pos.setEnabled(True)
        self.butt_act_rel_neg.setEnabled(True)
        self.butt_act_track_on.setEnabled(True)
        self.th_actuator.track = False
        # self.butt_act_track_off.setEnabled(False) # creates a warning
        return

    def butt_act_abs_Changed(self):
        self.th_actuator.absolute = True
        self.th_actuator.val_abs = self.ctrl_abs.value()

    def butt_act_rel_pos_Changed(self):
        self.th_actuator.relative = True
        self.th_actuator.sign = 'p'
        self.th_actuator.val_rel = self.ctrl_rel.value()

    def butt_act_rel_neg_Changed(self):
        self.th_actuator.relative = True
        self.th_actuator.sign = 'n'
        self.th_actuator.val_rel = self.ctrl_rel.value()

    def butt_random_start_Changed(self):
        self.th_random_walk.start()
        self.butt_random_start.setEnabled(False)
        self.butt_random_stop.setEnabled(True)

    def butt_random_stop_Changed(self):
        self.th_random_walk.done_random = True
        self.butt_random_start.setEnabled(True)
        self.butt_random_stop.setEnabled(False)

    def butt_random_current_Changed(self):
        lim = self.ctrl_random_I_max.value()
        i1 = random.uniform(-lim, lim)
        i2 = random.uniform(-lim, lim)
        i3 = random.uniform(-lim, lim)
        i4 = random.uniform(-lim, lim)
        self.ctrl_curr_1.setProperty("value", i1)
        self.ctrl_curr_2.setProperty("value", i2)
        self.ctrl_curr_3.setProperty("value", i3)
        self.ctrl_curr_4.setProperty("value", i4)

        return

    def butt_random_current_zero_Changed(self):
        self.ctrl_curr_1.setProperty("value", 0.000)
        self.ctrl_curr_2.setProperty("value", 0.000)
        self.ctrl_curr_3.setProperty("value", 0.000)
        self.ctrl_curr_4.setProperty("value", 0.000)

    def butt_random_current_2p5A_Changed(self):
        self.ctrl_pow_UP.setProperty("value", 2.5)
        self.ctrl_pow_RL.setProperty("value", 2.5)
        self.ctrl_pow_LR.setProperty("value", 2.5)
        self.ctrl_pow_DOWN.setProperty("value", 2.5)
        self.ctrl_pow_zDOWN.setProperty("value", 2.5)
        self.ctrl_pow_zUP.setProperty("value", 2.5)

    def log_data_time_laps(self):
        # path_file = os.getcwd()
        # path_file = path_file + '\\time_lapse\\' + 'log_time_laps.dat'
        # fr293 changed 25/03/19 to save outside of project folder
        path_file = 'D:\time_lapse_data' + 'log_time_laps.dat'
        f_name = open(path_file, 'a')
        # print datetime.datetime.now()
        to_write = str(datetime.datetime.now()) + ',' + str(self.t1_value_laps_PS) + ','
        to_write = to_write + str(self.t2_value_laps_PS) + ',' + str(self.ctrl_random_timelaps_frame_no.value()) + ','
        to_write = to_write + str(self.ctrl_random_timelaps_frame_time.value()) + ','
        to_write = to_write + str(self.ctrl_curr_1.value()) + ',' + str(self.ctrl_curr_2.value()) + ','
        to_write = to_write + str(self.ctrl_curr_3.value()) + ',' + str(self.ctrl_curr_4.value()) + ','
        to_write = to_write + self.lab_act_pos.text() + ',' + self.lab_plots_z_cent_air.text() + ','
        to_write = to_write + self.lab_plots_z_cent_oil.text() + ',' + str(self.ctrl_plots_z_bead_bottom.value()) + ','
        to_write = to_write + self.txt_random_time_lapse_folder.text()

        f_name.write(to_write + '\n')

        f_name.close()

    def butt_random_time_laps_start_Changed(self):
        self.name_folder_time_laps = self.txt_random_time_lapse_folder.text()
        if self.name_folder_time_laps == '':
            self.folder_path_time_laps = os.getcwd() + '\\time_laps\\' + '_default\\'
        else:
            self.folder_path_time_laps = os.getcwd() + '\\time_laps\\' + self.name_folder_time_laps + '\\'
        # print self.folder_path_time_laps
        if not os.path.isdir(self.folder_path_time_laps):
            os.makedirs(self.folder_path_time_laps)
        self.folder_path_time_laps_c1 = self.folder_path_time_laps + 'cam1\\'
        self.folder_path_time_laps_c2 = self.folder_path_time_laps + 'cam2\\'
        if not os.path.isdir(self.folder_path_time_laps_c1):
            os.makedirs(self.folder_path_time_laps_c1)
        if not os.path.isdir(self.folder_path_time_laps_c2):
            os.makedirs(self.folder_path_time_laps_c2)

        self.time_laps_run_flag = True
        self.txt_random_time_lapse_folder.setReadOnly(True)
        self.butt_random_time_laps_stop.setEnabled(True)
        self.butt_random_time_laps_start.setEnabled(False)
        self.ctrl_random_timelaps_frame_no.setEnabled(False)
        self.ctrl_random_timelaps_frame_time.setEnabled(False)
        self.ctrl_random_timelaps_t_ON.setEnabled(False)
        self.ctrl_random_timelaps_t_OFF.setEnabled(False)

        self.time_old_time_laps = time.clock() - self.ctrl_random_timelaps_frame_time.value()
        self.index_time_laps = 0

        self.t_init_laps_PS = time.clock()
        self.flag_t1_laps_PS = True
        self.flag_t2_laps_PS = False
        self.t1_value_laps_PS = self.ctrl_random_timelaps_t_ON.value()
        self.t2_value_laps_PS = self.ctrl_random_timelaps_t_OFF.value()

        self.log_data_time_laps()

        return

    def butt_random_time_laps_stop_Changed(self):
        self.time_laps_run_flag = False
        self.txt_random_time_lapse_folder.setReadOnly(False)
        self.butt_random_time_laps_stop.setEnabled(False)
        self.butt_random_time_laps_start.setEnabled(True)
        self.ctrl_random_timelaps_frame_no.setEnabled(True)
        self.ctrl_random_timelaps_frame_time.setEnabled(True)
        self.ctrl_random_timelaps_t_ON.setEnabled(True)
        self.ctrl_random_timelaps_t_OFF.setEnabled(True)
        self.butt_pow_stop_Changed()

        return

    def ctrl_random_timelaps_frame_no_Changed(self):

        return

    def ctrl_random_timelaps_frame_time_Changed(self):

        return

    def butt_demag_start_Changed(self):
        self.th_demag.current_sweep = self.ctrl_demag_ampl.value()
        self.th_demag.current_step = self.ctrl_demag_step.value()
        self.th_demag.current_time_wait = self.ctrl_demag_time.value()
        self.th_demag.start()
        self.butt_demag_start.setEnabled(False)
        self.butt_demag_stop.setEnabled(True)

    def butt_demag_stop_Changed(self):
        self.th_demag.done_demag = True
        self.butt_demag_start.setEnabled(True)
        self.butt_demag_stop.setEnabled(False)

    def current_demag(self, param):
        # kk = random.uniform(0,4)
        self.ctrl_curr_1.setProperty("value", float(param))
        self.ctrl_curr_2.setProperty("value", float(param))
        self.ctrl_curr_3.setProperty("value", float(param))
        self.ctrl_curr_4.setProperty("value", float(param))

    def ctrl_demag_focus_no_frames_Changed(self):
        self.avg_focus_no_frames = self.ctrl_demag_focus_no_frames.value()
        return

    def butt_demag_focus_avg_Changed(self):
        avg = np.average(self.storage_focus1)
        # print round(avg,3)
        self.lab_demag_focus_avg.setText('     ' + str(round(avg, 3)))

        return

    def butt_error_1_psu_1_Changed(self):
        self.th_power_supp.error_1_ps_1_status = True

        return

    def butt_error_2_psu_1_Changed(self):
        self.th_power_supp.error_2_ps_1_status = True

        return

    def butt_error_1_psu_2_Changed(self):
        self.th_power_supp.error_1_ps_2_status = True

        return

    def butt_error_2_psu_2_Changed(self):
        self.th_power_supp.error_2_ps_2_status = True

        return

    def butt_ard_start_Changed(self):
        self.th_power_supp.start()
        self.butt_ard_start.setEnabled(False)
        self.butt_ard_stop.setEnabled(True)
        # self.butt_ard_reset_temp.setEnabled(True)
        self.butt_pow_start.setEnabled(True)
        self.ctrl_curr_1.setEnabled(True)
        self.ctrl_curr_2.setEnabled(True)
        self.ctrl_curr_3.setEnabled(True)
        self.ctrl_curr_4.setEnabled(True)
        self.butt_pow_stop.setEnabled(False)
        self.butt_pow_pulse.setEnabled(True)
        self.butt_pow_UP.setEnabled(True)
        self.ctrl_pow_UP.setEnabled(True)
        self.butt_pow_RL.setEnabled(True)
        self.ctrl_pow_RL.setEnabled(True)
        self.butt_pow_LR.setEnabled(True)
        self.ctrl_pow_LR.setEnabled(True)
        self.butt_pow_DOWN.setEnabled(True)
        self.ctrl_pow_DOWN.setEnabled(True)
        self.butt_pow_zDOWN.setEnabled(True)
        self.ctrl_pow_zDOWN.setEnabled(True)
        self.butt_pow_zUP.setEnabled(True)
        self.ctrl_pow_zUP.setEnabled(True)
        self.butt_light_ON.setEnabled(True)
        self.butt_light_OFF.setEnabled(True)
        self.butt_demag_start.setEnabled(True)
        self.ctrl_demag_ampl.setEnabled(True)
        self.ctrl_demag_step.setEnabled(True)
        self.ctrl_demag_time.setEnabled(True)
        self.butt_exp_i_dir_start.setEnabled(True)
        self.butt_error_1_psu_1.setEnabled(True)
        self.butt_error_2_psu_1.setEnabled(True)
        self.butt_error_1_psu_2.setEnabled(True)
        self.butt_error_2_psu_2.setEnabled(True)
        self.butt_vi_send_cmd.setEnabled(True)

        return

    def butt_ard_stop_Changed(self):
        self.butt_ard_start.setEnabled(True)
        self.butt_ard_stop.setEnabled(False)
        # self.butt_ard_reset_temp.setEnabled(False)
        self.butt_pow_start.setEnabled(False)
        self.ctrl_curr_1.setEnabled(False)
        self.ctrl_curr_2.setEnabled(False)
        self.ctrl_curr_3.setEnabled(False)
        self.ctrl_curr_4.setEnabled(False)
        self.butt_pow_stop.setEnabled(False)
        self.butt_pow_pulse.setEnabled(False)
        self.butt_pow_UP.setEnabled(False)
        self.ctrl_pow_UP.setEnabled(False)
        self.butt_pow_RL.setEnabled(False)
        self.ctrl_pow_RL.setEnabled(False)
        self.butt_pow_LR.setEnabled(False)
        self.ctrl_pow_LR.setEnabled(False)
        self.butt_pow_DOWN.setEnabled(False)
        self.ctrl_pow_DOWN.setEnabled(False)
        self.butt_pow_zDOWN.setEnabled(False)
        self.ctrl_pow_zDOWN.setEnabled(False)
        self.butt_pow_zUP.setEnabled(False)
        self.ctrl_pow_zUP.setEnabled(False)
        self.butt_light_ON.setEnabled(False)
        self.butt_light_OFF.setEnabled(False)
        self.butt_demag_start.setEnabled(False)
        self.butt_demag_stop.setEnabled(False)
        self.ctrl_demag_ampl.setEnabled(False)
        self.ctrl_demag_step.setEnabled(False)
        self.ctrl_demag_time.setEnabled(False)
        self.butt_exp_i_dir_start.setEnabled(False)
        self.butt_exp_i_dir_stop.setEnabled(False)
        self.butt_error_1_psu_1.setEnabled(False)
        self.butt_error_2_psu_1.setEnabled(False)
        self.butt_error_1_psu_2.setEnabled(False)
        self.butt_error_2_psu_2.setEnabled(False)
        self.butt_vi_send_cmd.setEnabled(False)

        self.th_power_supp.done_ps = True
        return

    '''def butt_ard_reset_temp_Changed(self):
        self.th_power_supp.power_reset =True
        return'''

    def butt_pow_start_Changed(self):
        self.th_power_supp.power_is_set_on = True
        self.butt_pow_start.setEnabled(False)
        self.butt_pow_stop.setEnabled(True)
        self.lab_psu_on_off.setText('ON')
        return

    def ctrl_curr_1_Changed(self):
        self.th_power_supp.curr_1_value = self.ctrl_curr_1.value()
        self.th_power_supp.curr_1_changed = True
        self.th_power_supp.i_1_refresh = 1
        return

    def ctrl_curr_2_Changed(self):
        self.th_power_supp.curr_2_value = self.ctrl_curr_2.value()
        self.th_power_supp.curr_2_changed = True
        self.th_power_supp.i_2_refresh = 1
        return

    def ctrl_curr_3_Changed(self):
        self.th_power_supp.curr_3_value = self.ctrl_curr_3.value()
        self.th_power_supp.curr_3_changed = True
        self.th_power_supp.i_3_refresh = 1
        return

    def ctrl_curr_4_Changed(self):
        self.th_power_supp.curr_4_value = self.ctrl_curr_4.value()
        self.th_power_supp.curr_4_changed = True
        self.th_power_supp.i_4_refresh = 1
        return

    def butt_pow_stop_Changed(self):
        self.th_power_supp.power_is_set_off = True
        self.butt_pow_start.setEnabled(True)
        self.butt_pow_stop.setEnabled(False)
        self.lab_psu_on_off.setText('OFF')
        return

    def butt_pow_pulse_Changed(self):
        self.butt_pow_pulse.setEnabled(False)
        self.pulse_current_bool = True
        self.time_pulse_current = time.clock()
        self.butt_pow_start_Changed()
        return

    def butt_pow_UP_Changed(self):
        self.ctrl_curr_1.setProperty("value", 0.001)
        self.ctrl_curr_2.setProperty("value", self.curr_UP_value)
        self.ctrl_curr_3.setProperty("value", self.curr_UP_value)
        self.ctrl_curr_4.setProperty("value", 0.001)
        self.config_curr = 1
        return

    def ctrl_pow_UP_Changed(self):
        self.curr_UP_value = self.ctrl_pow_UP.value()
        return

    def butt_pow_RL_Changed(self):
        self.ctrl_curr_1.setProperty("value", self.curr_RL_value / 2.0)
        self.ctrl_curr_2.setProperty("value", self.curr_RL_value / 2.0)
        self.ctrl_curr_3.setProperty("value", self.curr_RL_value)
        self.ctrl_curr_4.setProperty("value", self.curr_RL_value)
        self.config_curr = 2
        return

    def ctrl_pow_RL_Changed(self):
        self.curr_RL_value = self.ctrl_pow_RL.value()
        return

    def butt_pow_LR_Changed(self):
        self.ctrl_curr_1.setProperty("value", self.curr_LR_value)
        self.ctrl_curr_2.setProperty("value", self.curr_LR_value)
        self.ctrl_curr_3.setProperty("value", self.curr_LR_value / 2.0)
        self.ctrl_curr_4.setProperty("value", self.curr_LR_value / 2.0)
        self.config_curr = 3
        return

    def ctrl_pow_LR_Changed(self):
        self.curr_LR_value = self.ctrl_pow_LR.value()
        return

    def butt_pow_DOWN_Changed(self):
        self.ctrl_curr_1.setProperty("value", self.curr_DOWN_value)
        self.ctrl_curr_2.setProperty("value", 0.001)
        self.ctrl_curr_3.setProperty("value", 0.001)
        self.ctrl_curr_4.setProperty("value", self.curr_DOWN_value)
        self.config_curr = 4
        return

    def ctrl_pow_DOWN_Changed(self):
        self.curr_DOWN_value = self.ctrl_pow_DOWN.value()
        return

    def butt_pow_zDOWN_Changed(self):
        self.ctrl_curr_1.setProperty("value", -self.curr_zDOWN_value)
        self.ctrl_curr_2.setProperty("value", -self.curr_zDOWN_value)
        self.ctrl_curr_3.setProperty("value", self.curr_zDOWN_value)
        self.ctrl_curr_4.setProperty("value", self.curr_zDOWN_value)
        self.config_curr = 5
        return

    def ctrl_pow_zDOWN_Changed(self):
        self.curr_zDOWN_value = self.ctrl_pow_zDOWN.value()
        return

    def butt_pow_zUP_Changed(self):
        self.ctrl_curr_1.setProperty("value", self.curr_zUP_value)
        self.ctrl_curr_2.setProperty("value", -self.curr_zUP_value)
        self.ctrl_curr_3.setProperty("value", -self.curr_zUP_value)
        self.ctrl_curr_4.setProperty("value", self.curr_zUP_value)
        self.config_curr = 6
        return

    def ctrl_pow_zUP_Changed(self):
        self.curr_zUP_value = self.ctrl_pow_zUP.value()
        return

    def butt_pow_zeroOFF_Changed(self, param):
        if param == False:
            self.ctrl_curr_1.setProperty("value", 0.000)
            self.ctrl_curr_2.setProperty("value", 0.000)
            self.ctrl_curr_3.setProperty("value", -0.000)
            self.ctrl_curr_4.setProperty("value", -0.000)
        return

    def butt_pow_zero_Changed(self):
        self.ctrl_curr_1.setProperty("value", 0.000)
        self.ctrl_curr_2.setProperty("value", 0.000)
        self.ctrl_curr_3.setProperty("value", 0.000)
        self.ctrl_curr_4.setProperty("value", 0.000)
        return

    def butt_pow_config_Changed(self, par1):
        # def butt_pow_config_Changed(self, par1,par2,par3,par4):
        # print 'par1234', par1, par2, par3, par4
        # self.ctrl_curr_1.setProperty("value", float(par1))
        # self.ctrl_curr_2.setProperty("value", float(par2))
        # self.ctrl_curr_3.setProperty("value", float(par3))
        # self.ctrl_curr_4.setProperty("value", float(par4))
        index = int(par1)
        c1 = self.th_exp_dir.configurations[index - 1][0]
        c2 = self.th_exp_dir.configurations[index - 1][1]
        c3 = self.th_exp_dir.configurations[index - 1][2]
        c4 = self.th_exp_dir.configurations[index - 1][3]

        self.ctrl_curr_1.setProperty("value", c1)
        self.ctrl_curr_2.setProperty("value", c2)
        self.ctrl_curr_3.setProperty("value", c3)
        self.ctrl_curr_4.setProperty("value", c4)

        return

    def butt_pow_coil_1_Changed(self):
        self.ctrl_curr_1.setProperty("value", 1.200)
        self.ctrl_curr_2.setProperty("value", 0.000)
        self.ctrl_curr_3.setProperty("value", 0.000)
        self.ctrl_curr_4.setProperty("value", 0.000)
        return

    def butt_pow_coil_2_Changed(self):
        self.ctrl_curr_1.setProperty("value", 0.000)
        self.ctrl_curr_2.setProperty("value", 1.200)
        self.ctrl_curr_3.setProperty("value", 0.000)
        self.ctrl_curr_4.setProperty("value", 0.000)
        return

    def butt_pow_coil_3_Changed(self):
        self.ctrl_curr_1.setProperty("value", 0.000)
        self.ctrl_curr_2.setProperty("value", 0.000)
        self.ctrl_curr_3.setProperty("value", 1.200)
        self.ctrl_curr_4.setProperty("value", 0.000)
        return

    def butt_pow_coil_4_Changed(self):
        self.ctrl_curr_1.setProperty("value", 0.000)
        self.ctrl_curr_2.setProperty("value", 0.000)
        self.ctrl_curr_3.setProperty("value", 0.000)
        self.ctrl_curr_4.setProperty("value", 1.200)
        return

    '''def flag_ps_display(self,parameter):
        self.lab_ard_status.setText(parameter )
        if parameter == 'Error Temp HIGH':
            self.butt_pow_start.setEnabled(True)
            self.butt_pow_stop.setEnabled(False)
            self.lab_psu_on_off.setText('OFF')'''

    def butt_exp_i_dir_start_Changed(self):
        self.butt_exp_i_dir_start.setEnabled(False)
        self.butt_exp_i_dir_stop.setEnabled(True)
        self.th_exp_dir.start_index = self.ctrl_exp_i_index_go.value()
        self.th_exp_dir.z_center_oil = self.z_c_oil
        self.th_exp_dir.start()

        return

    def butt_exp_i_dir_stop_Changed(self):
        self.butt_exp_i_dir_start.setEnabled(True)
        self.butt_exp_i_dir_stop.setEnabled(False)
        self.th_exp_dir.done_i_direction = True

        return

    def ctrl_exp_i_index_go_Changed(self):
        self.exp_val_index_go = self.ctrl_exp_i_index_go.value()
        return

    def update_index_exp_i_dir(self, param_input):
        self.lab_exp_i_now_index.setText(param_input)

    def butt_exp_start_Changed(self):
        self.th_experiments.start()
        self.butt_exp_start.setEnabled(False)
        self.butt_exp_stop.setEnabled(True)
        self.butt_exp_run.setEnabled(True)
        self.butt_exp_save_file.setEnabled(True)
        self.txt_exp_name_file.setPlaceholderText('f1_f2_vs_z__x0000_y000')
        return

    def butt_exp_stop_Changed(self):
        self.butt_exp_start.setEnabled(True)
        self.butt_exp_stop.setEnabled(False)
        self.butt_exp_run.setEnabled(False)
        self.butt_exp_idle.setEnabled(False)
        self.th_experiments.done_exp = True
        self.butt_exp_save_file.setEnabled(False)
        return

    def butt_exp_run_Changed(self):
        self.butt_exp_run.setEnabled(False)
        self.butt_exp_idle.setEnabled(True)
        self.th_experiments.name_folder_stack = self.txt_exp_name_file.text()
        self.th_experiments.exp_run = True
        self.th_experiments.exp_move_initial = True
        self.butt_act_abs.setEnabled(False)
        self.butt_act_rel_neg.setEnabled(False)
        self.butt_act_rel_pos.setEnabled(False)
        self.ctrl_exp_val_max.setEnabled(False)
        self.ctrl_exp_val_min.setEnabled(False)
        self.ctrl_exp_val_step.setEnabled(False)
        self.butt_exp_save_file.setEnabled(False)
        self.th_experiments.val_exper_min = self.ctrl_exp_val_min.value()
        self.th_experiments.val_exper_max = self.ctrl_exp_val_max.value()
        self.th_experiments.val_exper_step = self.ctrl_exp_val_step.value()
        return

    def butt_exp_idle_Changed(self):
        self.butt_exp_run.setEnabled(True)
        self.butt_exp_idle.setEnabled(False)
        self.butt_act_abs.setEnabled(True)
        self.butt_act_rel_neg.setEnabled(True)
        self.butt_act_rel_pos.setEnabled(True)
        self.th_experiments.exp_idle = True
        self.ctrl_exp_val_max.setEnabled(True)
        self.ctrl_exp_val_min.setEnabled(True)
        self.ctrl_exp_val_step.setEnabled(True)
        self.butt_exp_save_file.setEnabled(True)
        self.save_pict_exp = False

        return

    def update_save_pict(self):
        self.save_pict_exp = True

    def log_exp_stack_init(self):
        self.stack_z = [self.th_experiments.val_exper_real_time_z]
        self.stack_f1 = [self.focus]
        self.stack_f2 = [self.focus_2]
        self.stack_x1 = [self.center_x]
        self.stack_x2 = [self.center_x_2]
        self.stack_y1 = [self.center_y]
        self.stack_y2 = [self.center_y_2]
        self.stack_r1 = [self.round_factor]
        self.stack_r2 = [self.round_factor_2]
        self.stack_w1 = [self.width]
        self.stack_w2 = [self.width_2]
        self.stack_h1 = [self.height]
        self.stack_h2 = [self.height_2]

    def log_exp_stack_running(self):
        self.stack_z.append(self.th_experiments.val_exper_real_time_z)
        self.stack_f1.append(self.focus)
        self.stack_f2.append(self.focus_2)
        self.stack_x1.append(self.center_x)
        self.stack_x2.append(self.center_x_2)
        self.stack_y1.append(self.center_y)
        self.stack_y2.append(self.center_y_2)
        self.stack_r1.append(self.round_factor)
        self.stack_r2.append(self.round_factor_2)
        self.stack_w1.append(self.width)
        self.stack_w2.append(self.width_2)
        self.stack_h1.append(self.height)
        self.stack_h2.append(self.height_2)

    #    def butt_exp_save_file_Changed(self):
    #        path_file = os.getcwd()+'\\save\\'
    #        name_save = self.txt_exp_name_file.text()
    #        path_file = path_file + name_save+'.dat'
    #        f_name = open(path_file, 'w')
    #        to_write = 'z,f1,f2,xc1,yc1,w1,h1,r1,xc2,yc2,w2,h2,r2'
    #        f_name.write(to_write+'\n')
    #        for ii in range(len(self.xxx)):
    #            to_write = str(self.xxx[ii])+','+str(self.yyy[ii])+','+str(self.yyy_2[ii])+','
    #            to_write = to_write             +str(self.yyy_x1[ii])+','+str(self.yyy_y1[ii])+','
    #            to_write = to_write             +str(self.yyy_w1[ii])+','+str(self.yyy_h1[ii])+','
    #            to_write = to_write             +str(self.yyy_r1[ii])+','
    #            to_write = to_write             +str(self.yyy_x2[ii])+','+str(self.yyy_y2[ii])+','
    #             to_write = to_write             +str(self.yyy_w2[ii])+','+str(self.yyy_h2[ii])+','
    #            to_write = to_write             +str(self.yyy_r2[ii])
    #            f_name.write(to_write+'\n')
    #        f_name.close()
    #        return

    def butt_exp_save_file_Changed(self):
        path_file = os.getcwd() + '\\save\\'
        name_save = self.txt_exp_name_file.text()
        path_file = path_file + name_save + '.dat'
        f_name = open(path_file, 'w')
        to_write = 'z,f1,f2,xc1,yc1,w1,h1,r1,xc2,yc2,w2,h2,r2'
        f_name.write(to_write + '\n')
        for ii in range(len(self.stack_z)):
            to_write = str(self.stack_z[ii]) + ',' + str(self.stack_f1[ii]) + ',' + str(self.stack_f2[ii]) + ','
            to_write = to_write + str(self.stack_x1[ii]) + ',' + str(self.stack_y1[ii]) + ','
            to_write = to_write + str(self.stack_w1[ii]) + ',' + str(self.stack_h1[ii]) + ','
            to_write = to_write + str(self.stack_r1[ii]) + ','
            to_write = to_write + str(self.stack_x2[ii]) + ',' + str(self.stack_y2[ii]) + ','
            to_write = to_write + str(self.stack_w2[ii]) + ',' + str(self.stack_h2[ii]) + ','
            to_write = to_write + str(self.stack_r2[ii])

            f_name.write(to_write + '\n')

        f_name.close()

        return

    def ctrl_exp_val_min_Changed(self):
        return

    def ctrl_exp_val_max_Changed(self):
        return

    def ctrl_exp_val_step_Changed(self):
        return

    def paintEvent(self, event=None):

        qp = QtGui.QPainter()

        qp.begin(self)
        self.drawFrames(qp)
        qp.end()

        self.update()

    def drawFrames(self, qp):

        small = 16.0
        small_1 = self.zoom_factor
        x_min = 794
        y_min = 470
        x_max = 1794
        y_max = 1470
        x_mid = int((x_min + x_max) / 2.0)
        y_mid = int((y_min + y_max) / 2.0)
        x_rez = 2588
        y_rez = 1940
        slider_val = self.slider_bead_size_value

        x11 = 735;
        x12 = x11 + 134
        y11 = 770;
        y12 = y11 + 300

        x21 = 870;
        x22 = x21 + 140
        y21 = 580;
        y22 = y21 + 690

        x31 = 1080;
        x32 = x31 + 155
        y31 = 606;
        y32 = y31 + 600

        x41 = 1250;
        x42 = x41 + 180
        y41 = 700;
        y42 = y41 + 995

        x51 = 1550;
        x52 = x51 + 195
        y51 = 705;
        y52 = y51 + 600

        frame.queueFrameCapture()
        frame_2.queueFrameCapture()
        frame.waitFrameCapture(1000)

        # tt = datetime.datetime.now()
        # print 't_b ', str(getattr(tt,'second'))+'.'+str(getattr(tt,'microsecond'))

        frame_data = frame.getBufferByteData()

        frame_2.waitFrameCapture(1000)
        frame_data_2 = frame_2.getBufferByteData()

        self.time_calib = time.clock()

        n_frame = np.ndarray(buffer=frame_data, dtype=np.uint8, shape=(frame.height, frame.width))
        n_frame_2 = np.ndarray(buffer=frame_data_2, dtype=np.uint8, shape=(frame_2.height, frame_2.width))
        # print type(n_frame)

        # print "time_1", time.clock()

        # n_frame = camcapture.getImage(5000) #2s timeout # Numpy frame - openCV
        # print "time_2", time.clock()

        # n_frame_2=camcapture_2.getImage(2000)
        # n_frame_2 = self.th_video.n_frame_2_th
        # self.th_video.trigger = False
        # print "time_3", time.clock()
        if (self.index_pct_fps == 0):
            self.time_fps_old = time.clock()

        self.index_pct_fps = self.index_pct_fps + 1

        if (self.index_pct_fps == 20):
            # print 19 / (time.clock()-self.time_fps_old)
            self.measured_fps = 19.0 / (time.clock() - self.time_fps_old)
            self.text_changed_measured_fps()
            self.index_pct_fps = 0

        # print self.index_pct_fps

        n_frame_rect = n_frame.copy()
        # cv2.rectangle(n_frame_rect,(700,500),(1700,1500),(255,127,127),4)
        cv2.rectangle(n_frame_rect, (x_min, y_min), (x_max, y_max), (255, 127, 127), 4)

        cv2.rectangle(n_frame_rect, (x11, y11), (x12, y12), (255, 127, 127), 4)
        cv2.rectangle(n_frame_rect, (x21, y21), (x22, y22), (255, 127, 127), 4)
        cv2.rectangle(n_frame_rect, (x31, y31), (x32, y32), (255, 127, 127), 4)
        cv2.rectangle(n_frame_rect, (x41, y41), (x42, y42), (255, 127, 127), 4)
        cv2.rectangle(n_frame_rect, (x51, y51), (x52, y52), (255, 127, 127), 4)

        if QtGui.QAbstractButton.isChecked(self.checkbox_grid):
            cv2.line(n_frame_rect, (x_mid, 0), (x_mid, self.size_grid), (255, 127, 127), 4)
            cv2.line(n_frame_rect, (x_mid, y_rez), (x_mid, y_rez - self.size_grid), (255, 127, 127), 4)
            cv2.line(n_frame_rect, (0, y_mid), (self.size_grid, y_mid), (255, 127, 127), 4)
            cv2.line(n_frame_rect, (x_rez, y_mid), (x_rez - self.size_grid, y_mid), (255, 127, 127), 4)

        if QtGui.QAbstractButton.isChecked(self.checkbox_spim_box):
            cv2.rectangle(n_frame_rect, (self.spim_x_min, self.spim_y_min),
                          (self.spim_x_max, self.spim_y_max), (255, 127, 127), 5)

        if QtGui.QAbstractButton.isChecked(self.checkbox_ref_bead):
            cv2.line(n_frame_rect, (1495, 940), (1495, 1000), (255, 127, 127), 4)
            cv2.line(n_frame_rect, (1465, 970), (1525, 970), (255, 127, 127), 4)

        q_frame = NumPyQImage(n_frame_rect)  # Qt frame
        q_frame_2 = NumPyQImage(n_frame_2)
        self.n_frame_cam1 = n_frame

        if QtGui.QAbstractButton.isChecked(self.checkbox_m) and (time.clock() - self.time_old_mov) > 2.0:
            self.index_m = self.index_m + 1
            path_file_m = os.getcwd() + '\\movies\\'
            cv2.imwrite(path_file_m + str(self.index_m) + ".jpeg",
                        cv2.resize(n_frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR))
            self.time_old_mov = time.clock()

        if (self.save_pict_exp == True):
            self.index_exp = self.index_exp + 1
            # path_file_exp = os.getcwd()+'\\stack\\'
            cv2.imwrite(self.th_experiments.folder_path_c1 + 'cam1_' + str(self.index_exp) + ".jpeg",
                        cv2.resize(n_frame, None, fx=1.0, fy=1.0, interpolation=cv2.INTER_LINEAR))
            cv2.imwrite(self.th_experiments.folder_path_c2 + 'cam2_' + str(self.index_exp) + ".jpeg",
                        cv2.resize(n_frame_2, None, fx=1.0, fy=1.0, interpolation=cv2.INTER_LINEAR))
            ffocus, xxc, yyc = bead_focus_stack(n_frame)
            # print ffocus, xxc, yyc

            ffile_name = open(self.th_experiments.folder_path_c1[:-6] + '\\focus_stack.dat', 'a')
            ffile_name.write(
                str(self.th_experiments.val_exper_real_time_z) + ',' + str(ffocus) + ',' + str(xxc) + ',' + str(
                    yyc) + '\n')
            ffile_name.close()

            self.save_pict_exp = False

        if (self.seq_time_laps_run == True):
            if ((time.clock() - self.time_seq_tlaps) >= self.period_seq_tlaps):
                if (self.config_curr == 1):
                    self.butt_pow_DOWN_Changed()
                elif (self.config_curr == 4):
                    self.butt_pow_UP_Changed()
                else:
                    print 'no current changed'

                self.seq_tlaps_increment_file_name()
                self.butt_random_time_laps_start_Changed()
                self.time_seq_tlaps = time.clock()

        if (self.time_laps_run_flag == True):

            if (((time.clock() - self.t_init_laps_PS) >= (self.t1_value_laps_PS - 0.5)) and (
                    self.flag_t1_laps_PS == True)):
                self.butt_pow_start_Changed()
                self.flag_t1_laps_PS = False
                self.flag_t2_laps_PS = True

            if (((time.clock() - self.t_init_laps_PS) >= (self.t1_value_laps_PS + self.t2_value_laps_PS - 0.5))
                    and (self.flag_t2_laps_PS == True)):
                self.butt_pow_stop_Changed()
                self.flag_t2_laps_PS = False

            if (self.index_time_laps < self.ctrl_random_timelaps_frame_no.value()):
                if (time.clock() - self.time_old_time_laps > self.ctrl_random_timelaps_frame_time.value()):
                    self.index_time_laps = self.index_time_laps + 1
                    cv2.imwrite(self.folder_path_time_laps_c1 + 'cam1_' + str(self.index_time_laps + 100) + ".tiff",
                                cv2.resize(n_frame, None, fx=1.0, fy=1.0, interpolation=cv2.INTER_LINEAR))
                    cv2.imwrite(self.folder_path_time_laps_c2 + 'cam2_' + str(self.index_time_laps + 100) + ".tiff",
                                cv2.resize(n_frame_2, None, fx=1.0, fy=1.0, interpolation=cv2.INTER_LINEAR))
                    self.lab_random_timelaps_frame_index.setText(str(self.index_time_laps))
                    # print self.index_time_laps
                    self.time_old_time_laps = time.clock()
            else:
                self.butt_random_time_laps_stop_Changed()

        if QtGui.QAbstractButton.isChecked(self.checkbox_p):
            sq_frame = q_frame.scaled(q_frame.width() / small_1,
                                      q_frame.height() / small_1, )  # resize # small Qt frame
            # qp.drawImage(QPoint(20, 20), sq_frame)        # Display the frame
            sq_frame_2 = q_frame_2.scaled(q_frame_2.width() / small_1, q_frame_2.height() / small_1, )
            qp.drawImage(QPoint(20, 410), sq_frame_2)
            qp.drawImage(QPoint(20, 20), sq_frame)
        else:
            sq_frame = q_frame.scaled(q_frame.width() / small, q_frame.height() / small, )  # resize # small Qt frame
            # qp.drawImage(QPoint(20, 20), sq_frame)        # Display the frame
            sq_frame_2 = q_frame_2.scaled(q_frame_2.width() / small, q_frame_2.height() / small, )
            qp.drawImage(QPoint(20, 410), sq_frame_2)
            qp.drawImage(QPoint(20, 20), sq_frame)

        timp = time.time()
        # print time.clock()#-self.time_old
        # print timp ,timp.second #, #timp.microsecond

        if ((self.pulse_current_bool == True) and (time.clock() - self.time_pulse_current > 0.6)):
            self.butt_pow_pulse.setEnabled(True)
            self.pulse_current_bool = False
            self.butt_pow_stop_Changed()

        if QtGui.QAbstractButton.isChecked(self.checkbox_diff):
            n_frame_diff = cv2.absdiff(n_frame, n_frame_2)
            q_frame_diff = NumPyQImage(n_frame_diff)
            sq_frame_diff = q_frame_diff.scaled(q_frame_diff.width() / 7,
                                                q_frame_diff.height() / 7, )  # resize # small Qt frame
            qp.drawImage(QPoint(470, 570), sq_frame_diff)  # Display the frame

        if QtGui.QAbstractButton.isChecked(self.checkbox_XZ_section):
            n_frame_xz = np.zeros((260, 260), np.uint8)
            n_frame_xz[:] = (255)
            cv2.line(n_frame_xz, (130, 126), (130, 134), (0, 0, 0), 1)
            cv2.line(n_frame_xz, (126, 130), (134, 130), (0, 0, 0), 1)
            cv2.rectangle(n_frame_xz, (30, 10), (230, 250), (0, 0, 0), 1)
            cv2.line(n_frame_xz, (170, 99), (170, 103), (0, 0, 0), 1)
            cv2.line(n_frame_xz, (168, 101), (172, 101), (0, 0, 0), 1)

            cv2.line(n_frame_xz, (170 - 61, 101 - 64), (170 - 89, 101 - 44), (0, 0, 0), 1)
            cv2.line(n_frame_xz, (170 - 89, 101 - 44), (170 + 61, 101 + 64), (0, 0, 0), 1)
            cv2.line(n_frame_xz, (170 + 61, 101 + 64), (170 + 89, 101 + 44), (0, 0, 0), 1)
            cv2.line(n_frame_xz, (170 + 89, 101 + 44), (170 - 61, 101 - 64), (0, 0, 0), 1)

            self.scaling_fact = 2.5
            delta_x_pix_cent = (self.origin_x - self.center_x) / self.conv_um_pix
            delta_x_center_xz = int(round(delta_x_pix_cent / self.scaling_fact, 0))

            delta_z_mm_cent = (self.z_c_oil - self.val_coord_z_bead) * 1000
            delta_z_center_xz = int(round(delta_z_mm_cent / self.scaling_fact, 0))

            z_limit_min = 4.080
            z_limit_max = 4.170

            delta_z_mm_lim_min = (self.z_c_oil - z_limit_min) * 1000
            delta_z_center_lim_min_xz = int(round(delta_z_mm_lim_min / self.scaling_fact, 0))

            delta_z_mm_lim_max = (self.z_c_oil - z_limit_max) * 1000
            delta_z_center_lim_max_xz = int(round(delta_z_mm_lim_max / self.scaling_fact, 0))

            cv2.line(n_frame_xz, (1, 130 + delta_z_center_lim_min_xz), (259, 130 + delta_z_center_lim_min_xz),
                     (0, 0, 0), 1)
            cv2.line(n_frame_xz, (1, 130 + delta_z_center_lim_max_xz), (259, 130 + delta_z_center_lim_max_xz),
                     (0, 0, 0), 1)

            if abs(delta_z_center_xz) > 127:
                if delta_z_center_xz > 0:
                    delta_z_center_xz = 127
                else:
                    delta_z_center_xz = -127

            cv2.circle(n_frame_xz, (130 - delta_x_center_xz, 130 + delta_z_center_xz), 2, (0, 0, 0), 2)

            q_frame_xz = NumPyQImage(n_frame_xz)  # convert to QImage
            qp.drawImage(QPoint(470, 630), q_frame_xz)

        if QtGui.QAbstractButton.isChecked(self.checkbox_t):  # Show threshold is selected
            n_frame_thresh = NumThres(n_frame, self.threshMin, self.threshMax)
            q_frame_thresh = NumPyQImage(n_frame_thresh)  # convert to QImage
            sq_frame_thresh = q_frame_thresh.scaled(q_frame_thresh.width() / small,
                                                    q_frame_thresh.height() / small, )  # resize
            qp.drawImage(QPoint(455, 20), sq_frame_thresh)  # Display the frame

            n_frame_thresh_2 = NumThres(n_frame_2, self.threshMin_2, self.threshMax_2)
            q_frame_thresh_2 = NumPyQImage(n_frame_thresh_2)  # convert to QImage
            sq_frame_thresh_2 = q_frame_thresh_2.scaled(q_frame_thresh_2.width() / small,
                                                        q_frame_thresh_2.height() / small, )  # resize
            qp.drawImage(QPoint(455, 410), sq_frame_thresh_2)  # Display the frame

        if QtGui.QAbstractButton.isChecked(self.checkbox_b):  # Detect beads is selected
            n_frame_beads, xr, yr, wr, hr, no_beads, xc, yc, c_factor = beads_detection(n_frame,
                                                                                        self.threshMin, self.threshMax,
                                                                                        self.c_factor_min,
                                                                                        self.c_factor_max,
                                                                                        self.area_factor_min,
                                                                                        self.area_factor_max)
            self.number_beads = no_beads
            self.text_changed_bead()

            n_frame_beads_2, xr_2, yr_2, wr_2, hr_2, no_beads_2, xc_2, yc_2, c_factor_2 = beads_detection(n_frame_2,
                                                                                                          self.threshMin_2,
                                                                                                          self.threshMax_2,
                                                                                                          self.c_factor_min,
                                                                                                          self.c_factor_max,
                                                                                                          self.area_factor_min,
                                                                                                          self.area_factor_max)
            self.number_beads_2 = no_beads_2
            self.text_changed_bead_2()

            if no_beads > 0:  # At least one bead is detected

                q_frame_beads = NumPyQImage(n_frame_beads)  # convert to QImage
                sq_frame_beads = q_frame_beads.scaled(q_frame_beads.width() / small,
                                                      q_frame_beads.height() / small, )  # resize
                qp.drawImage(QPoint(620, 20), sq_frame_beads)  # Display the frame

                # w_r = wr
                # h_r = hr

                cn_frame = crop(n_frame, xr, yr, wr, hr, slider_val)  # croped frame with the bead // croped numpy
                cq_frame = NumPyQImage(cn_frame)  # convert to QImage
                scq_frame = cq_frame.scaled(cq_frame.width() / slider_val, cq_frame.height() / slider_val, )
                qp.drawImage(QPoint(455, 145), scq_frame)  # Display the frame

                # cv2.imwrite(str(timp)+".jpeg",cn_frame)
                # imagefile=QtGui.QImageWriter()
                # imagefile.setFileName(str(timp)+".jpeg")
                # imagefile.setFormat("jpeg")
                # imagefile.write(cq_frame)

                cn_frame_sobel = sobel_edge(cn_frame)
                cq_frame_sobel = NumPyQImage(cn_frame_sobel)  # convert to QImage
                scq_frame_sobel = cq_frame_sobel.scaled(cq_frame_sobel.width() / slider_val,
                                                        cq_frame_sobel.height() / slider_val, )
                qp.drawImage(QPoint(620, 145), scq_frame_sobel)  # Display the frame

                mean, stdev = cv2.meanStdDev(cn_frame_sobel)
                # self.focus = round(stdev[0][0]/mean[0][0],3)

                if (QtGui.QAbstractButton.isChecked(self.checkbox_demag_avg_focus_RT)):
                    self.storage_focus_1_RT[self.index_focus_avg_1_RT] = round(stdev[0][0] / mean[0][0], 3)
                    self.index_focus_avg_1_RT = self.index_focus_avg_1_RT + 1
                    if (self.index_focus_avg_1_RT > (self.avg_focus_no_frames - 1)):
                        self.index_focus_avg_1_RT = 0

                    self.focus = round(np.average(self.storage_focus_1_RT[:self.avg_focus_no_frames]), 3)

                else:
                    self.focus = round(stdev[0][0] / mean[0][0], 3)

                self.text_changed_focus()

                self.storage_focus1[self.index_focus_avg] = self.focus
                self.index_focus_avg = self.index_focus_avg + 1
                if (self.index_focus_avg > (self.size_focus_avg - 1)):
                    self.index_focus_avg = 0

                self.center_x = xc
                self.center_y = yc
                self.text_changed_x_y()

                self.width = wr
                self.height = hr
                self.text_changed_w_h()

                # print type(self.number_beads+0.0)
                self.round_factor = round(c_factor, 2)
                self.text_changed_round()
                # print 'out10'
                if QtGui.QAbstractButton.isEnabled(self.butt_ard_stop):  # PWS can be controlled
                    # print time.clock()-self.time_old_ard
                    if QtGui.QAbstractButton.isChecked(self.checkbox_center) and (
                            time.clock() - self.time_old_ard) > 0.5:
                        if ((xc > x_min and xc < x_max) and (yc > y_min and yc < y_max)):
                            if (xc - x_mid) > 10:
                                self.butt_pow_RL_Changed()
                                # print 'out1'
                            elif (xc - x_mid) < -10:
                                self.butt_pow_LR_Changed()
                                # print 'out2'
                            elif (yc - y_mid) > 4:
                                self.butt_pow_UP_Changed()
                                # print 'out3'
                            elif (yc - y_mid) < -4:
                                self.butt_pow_DOWN_Changed()
                                # print 'out4'
                                # elif (self.val_coord_z_bead-8.55)>0.003:
                                #    self.butt_pow_zDOWN_Changed()
                                # print 'out5'
                            else:
                                self.butt_pow_DOWN_Changed()
                                # print 'out6'
                        else:
                            self.butt_pow_zeroOFF_Changed(False)
                            # print 'out7'
                        self.time_old_ard = time.clock()

                    if QtGui.QAbstractButton.isChecked(self.checkbox_write) and (
                            time.clock() - self.time_old_ard) > 0.5:
                        if ((xc > x_min and xc < x_max) and (yc > y_min and yc < y_max)):
                            if (xc - self.x_target) > 3:
                                self.butt_pow_RL_Changed()
                                # print 'out1'
                            elif (xc - self.x_target) < -3:
                                self.butt_pow_LR_Changed()
                                # print 'out2'
                            elif (yc - self.y_target) > 3:
                                self.butt_pow_UP_Changed()
                                # print 'out3'
                            elif (yc - self.y_target) < -3:
                                self.butt_pow_DOWN_Changed()
                                # print 'out4'
                                # elif (self.val_coord_z_bead-8.55)>0.003:
                                #    self.butt_pow_zDOWN_Changed()
                                # print 'out5'
                            else:
                                self.butt_pow_DOWN_Changed()
                                # print 'out6'
                        else:
                            self.butt_pow_zeroOFF_Changed(False)
                            # print 'out7'
                        self.time_old_ard = time.clock()
                        # print 'out4'

                    if QtGui.QAbstractButton.isChecked(self.checkbox_random_safety):
                        if (not ((xc > x_min and xc < x_max) and (yc > y_min and yc < y_max))):
                            self.butt_random_current_zero_Changed()

            if no_beads_2 > 0:  # At least one bead is detected

                q_frame_beads_2 = NumPyQImage(n_frame_beads_2)  # convert to QImage
                sq_frame_beads_2 = q_frame_beads_2.scaled(q_frame_beads_2.width() / small,
                                                          q_frame_beads_2.height() / small, )  # resize
                qp.drawImage(QPoint(620, 410), sq_frame_beads_2)  # Display the frame

                cn_frame_2 = crop(n_frame_2, xr_2, yr_2, wr_2, hr_2,
                                  slider_val)  # cropped frame with the bead // cropped numpy
                cq_frame_2 = NumPyQImage(cn_frame_2)  # convert to QImage
                scq_frame_2 = cq_frame_2.scaled(cq_frame_2.width() / slider_val, cq_frame_2.height() / slider_val, )
                qp.drawImage(QPoint(455, 535), scq_frame_2)  # Display the frame

                cn_frame_sobel_2 = sobel_edge(cn_frame_2)
                cq_frame_sobel_2 = NumPyQImage(cn_frame_sobel_2)  # convert to QImage
                scq_frame_sobel_2 = cq_frame_sobel_2.scaled(cq_frame_sobel_2.width() / slider_val,
                                                            cq_frame_sobel_2.height() / slider_val, )
                qp.drawImage(QPoint(620, 535), scq_frame_sobel_2)  # Display the frame

                mean_2, stdev_2 = cv2.meanStdDev(cn_frame_sobel_2)
                # self.focus_2 = round(stdev_2[0][0]/mean_2[0][0],3)

                if (QtGui.QAbstractButton.isChecked(self.checkbox_demag_avg_focus_RT)):
                    self.storage_focus_2_RT[self.index_focus_avg_2_RT] = round(stdev_2[0][0] / mean_2[0][0], 3)
                    self.index_focus_avg_2_RT = self.index_focus_avg_2_RT + 1
                    if (self.index_focus_avg_2_RT > (self.avg_focus_no_frames - 1)):
                        self.index_focus_avg_2_RT = 0

                    self.focus_2 = round(np.average(self.storage_focus_2_RT[:self.avg_focus_no_frames]), 3)

                else:
                    self.focus_2 = round(stdev_2[0][0] / mean_2[0][0], 3)

                self.text_changed_focus_2()

                self.center_x_2 = xc_2
                self.center_y_2 = yc_2
                self.text_changed_x_y_2()

                self.width_2 = wr_2
                self.height_2 = hr_2
                self.text_changed_w_h_2()

                # print type(self.number_beads+0.0)
                self.round_factor_2 = round(c_factor_2, 2)
                self.text_changed_round_2()

            if no_beads > 0 and no_beads_2 > 0:
                self.delta_x = self.center_x - self.center_x_2
                self.delta_y = self.center_y - self.center_y_2
                self.text_changed_delta_x_y()
            else:
                self.delta_x = -9999
                self.delta_y = -9999
                self.text_changed_delta_x_y()

            # if QtGui.QAbstractButton.isEnabled(self.butt_act_stop):
            if QtGui.QAbstractButton.isEnabled(self.butt_act_stop):
                # if self.th_actuator.track == True:
                self.th_actuator.focus_act_1 = self.focus
                self.th_actuator.focus_act_2 = self.focus_2
                limits_f_1 = self.focus > 0.95 and self.focus < 1.5
                limits_f_2 = self.focus_2 > 0.84 and self.focus_2 < 1.37

                if self.th_actuator.track == True:
                    # if limits_f_1 and limits_f_2 and self.lab_act_sta.text()=='READY':
                    if self.lab_act_sta.text() == 'READY':
                        # z_avg = bead_z_evaluate(self.focus, self.focus_2)
                        # z_delta_bead = delta_z_bead(z_avg)

                        # self.val_coord_z_bead = round(float(self.lab_act_pos.text())-z_delta_bead,4)
                        self.val_coord_z_bead = round(float(self.lab_act_pos.text()), 4)
                        self.text_changed_z_bead_coord()

            if QtGui.QAbstractButton.isEnabled(self.butt_exp_i_dir_stop):
                self.th_exp_dir.x_bead = xc
                self.th_exp_dir.y_bead = yc
                self.th_exp_dir.z_bead = self.val_coord_z_bead

        if self.do_plot == True:
            self.xxx.append(time.clock() - self.time_old)
            # self.yyy.append(self.focus)
            self.yyy.append(self.val_coord_z_bead)
            # self.yyy_2.append(self.focus_2)
            self.data_plot_changed()
            # self.data_plot_2_changed()

        if self.rec_calib == True:
            # self.calib_fileout_update()
            self.calib_fileout_update_new()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = PySideCam()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    # print "main"
