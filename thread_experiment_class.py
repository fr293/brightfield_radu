import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

import numpy as np
import cv2
import cv2.cv as cv
import os
import csv
import atexit

class ThreadExperiment(QThread):
    current_update_trigger = Signal(list)
    z_track_trigger = Signal(bool)
    y2_feed_trigger = Signal(float)
    bead_move_cmd_trigger = Signal(str,str,list,list)
    ps_toggle_trigger = Signal(bool)
    def __init__(self,UI):
        super(ThreadExperiment, self).__init__()

        self.move_status = 0
        self.set_positions = [0,0,0]
        self.set_position_errors = [0.01,0.01,0.01]
        self.set_currents = [0,0,0,0]
        self.boundaries = [0,0,0,0]

        self.UI = UI

        self.positions = [0,0,0]
        self.camera_positions = [0,0,0]
        self.axis_positions = [0,0,0,0]
        self.positions_l = [0,0,0]
        self.bead_dict = {}
        for i in [1,2]:
            for key in ['focus','round','nbead','centerx','centery','width','height']:
                widget_str = key+str(i)
                self.bead_dict[widget_str] = 0
        self.currents = [0,0,0,0]
        self.ps_power = False

        self.update_flag = False
        self.save_flag = False
        self.exp_flag = False

        self.cmd_status = 0
        self.cmd_i = 0
        self.stop_time = 0

        self.exp_save_fname = 'savefile'
        self.exp_fname = 'loadfile'
        self.exp_cmds = []
        self.exp_save_mode = 'default'


    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('experiment thread start')
        while True:
            if self.save_flag:
                if self.update_flag:
                    self.exp_save(self.exp_save_mode)
                    self.update_flag = False

            if self.exp_flag:
                cmd = self.exp_cmds[self.cmd_i][0]
                status = self.cmd_status
                if status == 0:
                    print time.strftime("%H:%M:%S ") + 'experiment cmd #{0} of {1}:'.format(self.cmd_i,len(self.exp_cmds)) + cmd

                if len(self.exp_cmds[self.cmd_i]) > 1:
                    try:
                        float(self.exp_cmds[self.cmd_i][1])
                        num = []
                        for number in self.exp_cmds[self.cmd_i][1:]:
                            num.append(float(number))
                    except ValueError:
                        str = []
                        for string in self.exp_cmds[self.cmd_i][1:]:
                            str.append(string)


                if cmd == 'save file name':
                    self.exp_save_fname = str[0]
                    status = 4
                elif cmd == 'save mode':
                    self.exp_save_mode = str[0]
                    status = 4
                elif cmd == 'start logging':
                    self.exp_save_toggle(True)
                    status = 4
                elif cmd == 'stop logging':
                    self.exp_save_toggle(False)
                    status = 4
                elif cmd == 'wait':
                    if status == 0:
                        self.stop_time = time.clock() + num[0]
                        status = 1
                    elif status == 1:
                        if time.clock() >= self.stop_time:
                            status = 4
                elif cmd == 'move abs':
                    if status == 0:
                        self.timeout = 10
                        self.stop_time = self.timeout + time.clock()
                        for i in range(3):
                            self.set_positions[i] = num[i]
                            self.set_position_errors[i] = num[i+3]
                        self.bead_move_cmd_trigger.emit('pos','abs',self.set_positions,self.set_position_errors)
                        status = 1
                    if status == 1:
                        if self.move_status == 2:
                            print time.strftime("%H:%M:%S ") + 'moving to location'
                            status = 2
                        if time.clock() >= self.stop_time:
                            print time.strftime("%H:%M:%S ") + 'timeout trying move again'
                            status = 0
                    if status == 2:
                        if self.move_status == 0:
                            status = 4
                            print time.strftime("%H:%M:%S ") + 'arrived at location'
                elif cmd == 'move current':
                    for i in range(4):
                        self.set_currents[i] = num[i]
                    for i in range(3):
                        self.boundaries[i] = num[i+4]
                    self.timeout = num[7]
                    if status == 0:
                        self.stop_time = self.timeout + time.clock()
                        self.change_currents(self.set_currents)
                        self.ps_toggle_trigger.emit(True)
                        print time.strftime("%H:%M:%S ") + 'current on {0},{1},{2},{3}'.format(self.set_currents[0],self.set_currents[1],self.set_currents[2],self.set_currents[3])
                        status = 1
                    elif status == 1:
                        if time.clock() >= self.stop_time:
                            self.ps_toggle_trigger.emit(False)
                            print time.strftime("%H:%M:%S ") + 'timeout current off'
                            status = 4
                        if not all(abs(pos) <= bound for pos,bound in zip(self.positions,self.boundaries)):
                            self.ps_toggle_trigger.emit(False)
                            print time.strftime("%H:%M:%S ") + 'boundary current off'
                            status = 4
                elif cmd == 'move hold start':
                    if status == 0:
                        self.timeout = 10
                        self.stop_time = self.timeout + time.clock()
                        self.bead_move_cmd_trigger.emit('hold','start',[0,0,0],[0,0,0])
                        status = 1
                    if status == 1:
                        if self.move_status == 2:
                            print time.strftime("%H:%M:%S ") + 'hold started'
                            status = 4
                        if time.clock() >= self.stop_time:
                            print time.strftime("%H:%M:%S ") + 'timeout trying hold again'
                            status = 0
                elif cmd == 'move hold stop':
                    if status == 0:
                        self.timeout = 10
                        self.stop_time = self.timeout + time.clock()
                        if self.move_status == 2:
                            self.bead_move_cmd_trigger.emit('hold','stop',[0,0,0],[0,0,0])
                        status = 1
                    if status == 1:
                        if self.move_status == 0:
                            print time.strftime("%H:%M:%S ") + 'hold stopped'
                            status = 4
                        if time.clock() >= self.stop_time:
                            print time.strftime("%H:%M:%S ") + 'timeout trying hold again'
                            status = 0
                elif cmd == 'feed y2 axis':
                    for i in range(3):
                        self.boundaries[i] = num[i+1]
                    self.timeout = num[4]
                    if status == 0:
                        self.stop_time = self.timeout + time.clock()
                        self.y2_feed_trigger.emit(num[0])
                        print time.strftime("%H:%M:%S ") + 'feed y2 axis {0}'.format(num[0])
                        status = 1
                    elif status == 1:
                        if time.clock() >= self.stop_time:
                            self.y2_feed_trigger.emit(0)
                            print time.strftime("%H:%M:%S ") + 'timeout feed y2 off'
                            status = 4
                        if not all(abs(pos) <= bound for pos,bound in zip(self.positions,self.boundaries)):
                            self.y2_feed_trigger.emit(0)
                            print time.strftime("%H:%M:%S ") + 'boundary feed y2 off'
                            status = 4

                elif cmd == 'start z tracking':
                    self.z_track_trigger.emit(True)
                    status = 4

                self.cmd_status = status

                if self.cmd_status == 4:
                    self.cmd_i += 1
                    if self.cmd_i == len(self.exp_cmds):
                        self.exp_toggle(False)
                    self.cmd_status = 0

    def exp_toggle(self,toggle_flag):
        if toggle_flag == True:
            f_path = os.getcwd()+'\\exp\\'
            f_name = self.exp_fname
            f_path = f_path + f_name +'.csv'
            if not os.path.exists(f_path):
                print 'file does not exist'
            # open file
            with open(f_path,'rb') as f:
                reader = csv.reader(f)
                self.exp_cmds = []
                for row in reader:
                    self.exp_cmds.append(row)
                    print row
            print len(self.exp_cmds)
            self.cmd_status = 0
            self.cmd_i = 0
            self.exp_flag = True
            print time.strftime("%H:%M:%S ") + 'exp start'
        elif toggle_flag == False:
            self.exp_flag = False
            if self.save_flag:
                self.exp_save_toggle(False)
            print time.strftime("%H:%M:%S ") + 'exp stop'

    def exp_save_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.save_flag = True
            print 'start data logging'
        elif toggle_flag == False:
            self.save_flag = False
            print('stop data logging')

    def exp_save(self,mode = 'default'):
        f_path = os.getcwd()+'\\exp\\'
        f_name = self.exp_save_fname
        f_path = f_path + f_name +'.csv'
        if not os.path.exists(f_path):
            heading_flag = True
            f = file(f_path, 'w')
            f.close()
            print 'file created:' + f_path
        else:
            heading_flag = False
        if mode == 'default':
            with open(f_path,'a') as f:
                writer = csv.writer(f)
                if heading_flag:
                    write_list = ['t','bead x','bead y','bead z','cam x','cam y','cam z','act x','act y1','act z','act y2','curr 1','curr 2','curr 3','curr 4','ps power','focus1','focus2']
                    writer.writerow(write_list)
                write_list = []
                write_list.append('{0:9.4f}'.format(time.clock()))
                for i in range(3):
                    write_list.append('{0:7.4f}'.format(self.positions[i]))
                for i in range(3):
                    write_list.append('{0:7.4f}'.format(self.camera_positions[i]))
                for i in range(4):
                    write_list.append('{0:7.4f}'.format(self.axis_positions[i]))
                for i in range(4):
                    write_list.append('{0:7.4f}'.format(self.currents[i]))
                if self.ps_power:
                    write_list.append('1')
                else:
                    write_list.append('0')
                write_list.append('{0}'.format(self.bead_dict['focus1']))
                write_list.append('{0}'.format(self.bead_dict['focus2']))
                writer.writerow(write_list)
        if mode == 'simple':
            with open(f_path,'a') as f:
                writer = csv.writer(f)
                if heading_flag:
                    write_list = ['t','bead x','bead y','bead z','focus1','focus2']
                    writer.writerow(write_list)
                write_list = []
                write_list.append('{0:9.4f}'.format(time.clock()))
                for i in range(3):
                    write_list.append('{0:7.4f}'.format(self.positions[i]))
                write_list.append('{0}'.format(self.bead_dict['focus1']))
                write_list.append('{0}'.format(self.bead_dict['focus2']))
                writer.writerow(write_list)

    def bead_position_changed(self,positions,camera_positions,tip_positions,axis_positions):
        self.update_flag = True
        for i in range(3):
            self.positions_l[i] = self.positions[i]
            self.positions[i] = positions[i]
            self.camera_positions[i] = camera_positions[i]
        for i in range(4):
            self.axis_positions[i] = axis_positions[i]

    def bead_changed(self,key,val):
        self.bead_dict[key] = val

    def current_changed(self,set_current_list):
        for i in range(len(set_current_list)):
            self.currents[i] = set_current_list[i]

    def ps_power_changed(self,toggle_flag):
        self.ps_power = toggle_flag

    def exp_fname_changed(self,fname):
        self.exp_fname = fname

    def exp_save_fname_changed(self,fname):
        self.exp_save_fname = fname

    def move_status_changed(self,move_status):
        self.move_status = move_status

    def change_currents(self,set_current_list):
        #print set_current_list
        self.current_update_trigger.emit(set_current_list)
        self.current_changed(set_current_list)