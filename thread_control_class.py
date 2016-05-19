import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadControl(QThread):
    current_update_trigger = Signal(list)
    def __init__(self,UI):
        super(ThreadControl, self).__init__()

        self.set_positions = [0,0,0] #value set in UI

        self.UI = UI

        self.manual_base_current = 0

        #0 ready
        #1 action start
        #2 action in progress
        #3 action stop
        self.move_status = 0
        self.pos_type = 'rel'
        self.move_type = 'jog'
        self.feed_vel = 0

        self.positions = [0,0,0]
        self.camera_positions = [0,0,0]
        self.positions_l = [0,0,0] #last position
        self.move_positions = [0,0,0] #target position

        self.update_flag = False


    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('control thread start')
        while True:
            #start movement
            if self.move_status == 1:
                #calculate target move position
                for i in range(3):
                    if self.pos_type == 'abs':
                        self.move_positions[i] = self.set_positions[i]
                    elif self.pos_type == 'rel':
                        self.move_positions[i] = self.set_positions[i] + self.positions[i]
                    #disable position and current settings
                    self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(True)
                for i in range(4):
                    self.UI.set_current_sbox[i].spinbox.setReadOnly(True)
                self.integral = [0,0,0,0]
                self.UI.ps_cont_tbutton.set_toggle(True)
                self.move_status = 2
                print 'start'

            if self.move_status == 2:
                #if time.clock() - time_l > 0.1:
                #time_l = time.clock()
                if self.update_flag:
                    dpos = [a - b for a,b in zip(self.move_positions,self.positions)]
                    #print dpos
                    self.change_currents(self.calculate_currents(dpos))
                    self.update_flag = False
                    print 'continue'
                #if all(i <= 0.002 for i in dpos):
                    #self.integral = [0,0,0,0]
                    #self.move_status = 3
                    #print 'target reached'

            if self.move_status == 3:
                #enable positions and current settings
                for i in range(3):
                    self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(False)
                for i in range(4):
                    self.UI.set_current_sbox[i].spinbox.setReadOnly(False)
                self.UI.ps_cont_tbutton.set_toggle(False)
                self.move_status = 0
                print 'stopped'



    def absrel_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.pos_type = 'abs'
            print('abs')
        else:
            self.pos_type = 'rel'
            print('rel')

    def start_toggle(self,toggle_flag):
        if toggle_flag == True:
            self.move_status = 1
            print('magnet start movement')
        else:
            self.move_status = 3
            print('magnet stop movement')

    def magnet_set_changed(self,value,ref_text):
        dict = {'x':0,'y':1,'z':2}
        i = dict[ref_text]
        self.set_positions[i] = value
        print('control set position '+ ref_text +' changed: '+str(value))

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
        if toggle_flag == True:
            print('bead hold')
        elif toggle_flag == False:
            print('bead release')

    def exp_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('exp start')
        elif toggle_flag == False:
            print('exp stop')

    def manual_base_current_changed(self,value):
        self.manual_base_current = value

    def change_currents(self,set_current_list):
        print set_current_list
        self.current_update_trigger.emit(set_current_list)

    def calculate_currents(self,dpositions):
        max_current = 1
        kP = 30
        kI = 0

        set_current_list = [0,0,0,0]
        scaling = [1,1,0.5]
        drive = [0,0,0]
        error = [0,0,0]
        for i in range(3):
            error[i] = dpositions[i]
            #self.integral[i] = self.integral[i] + error[i]
            drive[i] = error[i]*kP# + self.integral[i]*kI
            if abs(drive[i]) > max_current:
                drive[i] = max_current*drive[i]/abs(drive[i])

        if abs(dpositions[2]) > 0.01:
            drive[0] = 0
            drive[1] = 0
        elif abs(dpositions[0]/dpositions[1]) > 1.2:
            drive[1] = 0
            drive[2] = 0
        else:
            #(dpositions[1]/dpositions[0]) > 1.2 and dpositions[1] > 0.1:
            drive[0] = 0
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
                    current[j] = current_mapping[2*i][j]*drive[i]*scaling[i]
                else:
                    current[j] = current_mapping[2*i+1][j]*drive[i]*scaling[i]
                set_current_list[j] = set_current_list[j] + current[j]

        return set_current_list

    def bead_changed(self,positions,camera_positions):
        self.update_flag = True
        for i in range(3):
            self.positions_l[i] = self.positions[i]
            self.positions[i] = positions[i]
            self.camera_positions[i] = camera_positions[i]