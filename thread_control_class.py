import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadControl(QThread):
    current_update_trigger = Signal(list)
    ps_toggle_trigger = Signal(bool)
    move_toggle_trigger = Signal(bool)
    hold_toggle_trigger = Signal(bool)
    move_update_trigger = Signal(float)
    def __init__(self,UI):
        super(ThreadControl, self).__init__()



        self.UI = UI

        self.manual_base_current = 0

        #0 ready
        #1 action start
        #2 action in progress
        #3 action stop
        self.move_status = 0
        self.move_status_tx = -1
        self.pos_type = 'rel'
        self.move_type = 'pos'
        self.set_positions = [0,0,0] #value set in UI
        self.set_position_errors = [0.003,0.003,0.005]

        self.positions = [0,0,0]
        self.camera_positions = [0,0,0]
        self.positions_l = [0,0,0] #last position
        self.move_positions = [0,0,0] #target position

        self.demag_flag = False
        self.demag_sweep = 1.0
        self.demag_step = 0.05
        self.demag_wait = 1
        self.demag_time = 0
        self.demag_currents = [self.demag_sweep,self.demag_sweep,self.demag_sweep,self.demag_sweep]

        self.update_flag = False
        self.update_time = 0
        self.update_time_l = 0
        self.dt = 0.0

        self.z_flag = False
        self.integral = [0,0,0]


    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('control thread start')
        while True:
            if self.update_flag:
                if self.move_status != self.move_status_tx:
                    self.move_update_trigger.emit(self.move_status)
                    self.move_status_tx = self.move_status
                if self.move_type == 'pos':
                    #start movement
                    if self.move_status == 1:
                        #calculate target move position
                        for i in range(3):
                            if self.pos_type == 'abs':
                                self.move_positions[i] = self.set_positions[i]
                            elif self.pos_type == 'rel':
                                self.move_positions[i] = self.set_positions[i] + self.positions[i]
                        self.move_toggle_trigger.emit(True)
                        # #disable position and current settings
                        #     self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(True)
                        # for i in range(4):
                        #     self.UI.set_current_sbox[i].spinbox.setReadOnly(True)
                        # self.integral = [0,0,0,0]
                        self.ps_toggle_trigger.emit(True)
                        self.move_status = 2
                        print 'start'

                    if self.move_status == 2:
                        #if time.clock() - time_l > 0.1:
                        #time_l = time.clock()

                            dpos = [a - b for a,b in zip(self.move_positions,self.positions)]
                            #print dpos
                            self.change_currents(self.calculate_currents(dpos))
                            #self.change_currents(self.calculate_currents_new(dpos))

                            #print 'continue'
                            if all(abs(error) <= max_error for error,max_error in zip(dpos,self.set_position_errors)):
                                self.integral = [0,0,0,0]
                                self.ps_toggle_trigger.emit(False)
                                self.move_status = 3
                                print 'target reached'

                    if self.move_status == 3:
                        if all(abs(error) <= max_error for error,max_error in zip(dpos,self.set_position_errors)):
                            self.move_toggle_trigger.emit(False)
                            self.move_status = 4
                            print 'target definitely reached'
                        else:
                            self.ps_toggle_trigger.emit(True)
                            self.move_status = 2

                    if self.move_status == 4:
                        # #enable positions and current settings
                        # for i in range(3):
                        #     self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(False)
                        # for i in range(4):
                        #     self.UI.set_current_sbox[i].spinbox.setReadOnly(False)
                        self.ps_toggle_trigger.emit(False)
                        self.move_status = 0
                        print 'stopped'

                    self.update_flag = False

                elif self.move_type == 'hold':
                    #start movement
                    if self.move_status == 1:
                        #calculate target move position
                        for i in range(3):
                                self.move_positions[i] = self.positions[i]
                        self.hold_toggle_trigger.emit(True)
                        self.ps_toggle_trigger.emit(True)
                        self.move_status = 2
                        print 'start'

                    if self.move_status == 2:
                        #if time.clock() - time_l > 0.1:
                        #time_l = time.clock()

                            dpos = [a - b for a,b in zip(self.move_positions,self.positions)]
                            #print dpos
                            self.change_currents(self.calculate_currents_hold(dpos))
                            #self.change_currents(self.calculate_currents_new(dpos))

                    if self.move_status == 4:
                        # #enable positions and current settings
                        # for i in range(3):
                        #     self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(False)
                        # for i in range(4):
                        #     self.UI.set_current_sbox[i].spinbox.setReadOnly(False)
                        self.ps_toggle_trigger.emit(False)
                        self.move_status = 0
                        print 'hold stopped'

                    self.update_flag = False



            if self.demag_flag:
                if time.clock() - self.demag_time >= self.demag_wait:
                    if self.demag_currents[0] == self.demag_sweep:
                        print 'start sweep'
                        self.change_currents(self.demag_currents)
                        self.ps_toggle_trigger.emit(True)
                        for i in range(4):
                            self.demag_currents[i] -= self.demag_step
                        self.demag_time = time.clock()

                    elif self.demag_currents[0] <= 0:
                        self.change_currents([0,0,0,0])
                        self.ps_toggle_trigger.emit(False)
                        print 'sweep done'
                        self.demag_currents = [self.demag_sweep,self.demag_sweep,self.demag_sweep,self.demag_sweep]
                        self.demag_flag = False
                        self.demag_time = 0
                    else:
                        self.change_currents(self.demag_currents)
                        for i in range(4):
                            self.demag_currents[i] -= self.demag_step
                        self.demag_time = time.clock()


    def absrel_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.pos_type = 'abs'
            print('abs')
        else:
            self.pos_type = 'rel'
            print('rel')

    def start_toggle(self,toggle_flag):
        self.move_type = 'pos'
        if toggle_flag == True:
            self.move_status = 1
            #print('magnet start movement')
        else:
            self.move_status = 4
            #print('magnet stop movement')

    def magnet_set_changed(self,value,ref_text):
        dict = {'x':0,'y':1,'z':2}
        i = dict[ref_text]
        self.set_positions[i] = value
        print('control set position '+ ref_text +' changed: '+str(value))

    def magnet_set_error_changed(self,value,ref_text):
        dict = {'x':0,'y':1,'z':2}
        i = dict[ref_text]
        self.set_position_errors[i] = value
        print('control set position error '+ ref_text +' changed: '+str(value))

    def manual_direction(self,ref_text):
        dict = {'x+':0,'x-':1,'y+':2,'y-':3,'z+':4,'z-':5}
        current_mapping = [[1,1,0.5,0.5],#x+
                           [0.5,0.5,1,1],#x-
                           [0,1,1,0],#y+
                           [1,0,0,1],#y-
                           [1,-1,-1,1],#z+
                           [-1,-1,1,1]]#z-
        set_current_list = []
        for i in range(4):
            current =  current_mapping[dict[ref_text]][i]*self.manual_base_current
            set_current_list.append(current)
        self.change_currents(set_current_list)
        print('manual direction: ' + ref_text)

    def hold_toggle(self,toggle_flag):
        self.move_type = 'hold'
        if toggle_flag == True:
            self.move_status = 1
            print('magnet start hold')
        else:
            self.move_status = 4
            print('magnet stop hold')

    def exp_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('exp start')
        elif toggle_flag == False:
            print('exp stop')

    def manual_base_current_changed(self,value):
        self.manual_base_current = value

    def change_currents(self,set_current_list):
        #print set_current_list
        self.current_update_trigger.emit(set_current_list)

    def calculate_currents(self,dpositions):
        max_current = 1
        kP = 40
        kI = 0

        set_current_list = [0,0,0,0]
        scaling = [1,2,0.5]
        drive = [0,0,0]
        error = [0,0,0]
        for i in range(3):
            error[i] = dpositions[i]
            #self.integral[i] = self.integral[i] + error[i]
            drive[i] = error[i]*kP# + self.integral[i]*kI
            if abs(drive[i]) > max_current:
                drive[i] = max_current*drive[i]/abs(drive[i])


        if abs(dpositions[2]) > 0.02:
            drive[0] = 0
            drive[1] = 0
        elif abs(dpositions[2]) > self.set_position_errors[2] and abs(dpositions[1]) + abs(dpositions[0]) < 0.02:
            drive[0] = 0
            drive[1] = 0
        else:
            #(dpositions[1]/dpositions[0]) > 1.2 and dpositions[1] > 0.1:
            drive[2] = 0
        #print drive
        dict = {'x+':0,'x-':1,'y+':2,'y-':3,'z+':4,'z-':5}
        current_mapping = [[1,1,0.5,0.5],#x+
                           [0.5,0.5,1,1],#x-
                           [0,1,1,0],#y+
                           [1,0,0,1],#y-
                           [1,-1,-1,1],#z+
                           [-1,-1,1,1]]#z-
        # current_mapping = [[1,1,0,0],#x+
        #                    [0,0,1,1],#x-
        #                    [0,1,1,0],#y+
        #                    [1,0,0,1],#y-
        #                    [1,-1,-1,1],#z+
        #                    [-1,-1,1,1]]#z-
        for i in range(3):
            current = [0,0,0,0]
            for j in range(4):
                if drive[i] >= 0:
                    current[j] = current_mapping[2*i][j]*abs(drive[i])*scaling[i]
                else:
                    current[j] = current_mapping[2*i+1][j]*abs(drive[i])*scaling[i]
                set_current_list[j] = set_current_list[j] + current[j]

        return set_current_list

    def calculate_currents_new(self,dpositions):
        max_current = 1
        kP = 10

    def calculate_currents_hold(self,dpositions):
        max_current = 2
        kP = 40
        kI = 5

        set_current_list = [0,0,0,0]
        integral_threshold = [0.2,0.2,0]
        scaling = [1,1,0.5]
        drive = [0,0,0]
        error = [0,0,0]
        for i in range(3):
            error[i] = dpositions[i]
            if abs(error[i]) < integral_threshold[i]:
                self.integral[i] = self.integral[i] + error[i]*self.dt
            if abs(error[i]) > 0.02 and self.integral[i]/(error[i]+0.0001) < 0:
                self.integral[i] = 0

            drive[i] = error[i]*kP + self.integral[i]*kI

            if abs(drive[i]) > max_current:
                drive[i] = max_current*drive[i]/abs(drive[i])

        #print self.integral
        #print drive
        #print 'continue'

        z_tol = 0.25
        #print self.z_flag
        if self.z_flag:
            if abs(dpositions[2]) < 0.01:
                self.z_flag = False
            else:
                drive[0] = 0
                drive[1] = 0
        else:
            if abs(dpositions[2]) > z_tol:
                self.z_flag = True
            else:
                #(dpositions[1]/dpositions[0])  1.2 and dpositions[1] > 0.1:
                drive[2] = 0
        #print drive
        dict = {'x+':0,'x-':1,'y+':2,'y-':3,'z+':4,'z-':5}
        current_mapping = [[1,1,0,0],#x+
                           [0,0,1,1],#x-
                           [0,1,1,0],#y+
                           [1,0,0,1],#y-
                           [1,-1,-1,1],#z+
                           [-1,-1,1,1]]#z-
        # current_mapping = [[1,1,0,0],#x+
        #                    [0,0,1,1],#x-
        #                    [0,1,1,0],#y+
        #                    [1,0,0,1],#y-
        #                    [1,-1,-1,1],#z+
        #                    [-1,-1,1,1]]#z-
        for i in range(3):
            current = [0,0,0,0]
            for j in range(4):
                if drive[i] >= 0:
                    current[j] = current_mapping[2*i][j]*abs(drive[i])*scaling[i]
                else:
                    current[j] = current_mapping[2*i+1][j]*abs(drive[i])*scaling[i]
                set_current_list[j] = set_current_list[j] + current[j]

        return set_current_list


    def bead_position_changed(self,positions,camera_positions,tip_positions,axis_positions):
        self.update_flag = True
        self.update_time_l = self.update_time
        self.update_time = time.clock()
        self.dt = self.update_time - self.update_time_l
        for i in range(3):
            self.positions_l[i] = self.positions[i]
            self.positions[i] = positions[i]
            self.camera_positions[i] = camera_positions[i]

    def demag_poles(self):
        self.demag_flag = True
        self.demag_time = time.clock()
