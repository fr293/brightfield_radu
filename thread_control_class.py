import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadControl(QThread):
    def __init__(self,UI):
        super(ThreadControl, self).__init__()
        self.set_position = [0,0,0] #value set in UI
        self.UI = UI

        self.manual_base_current = 0

        #0 ready
        #1 action start
        #2 action in progress
        #3 action stop
        self.move_status = 0
        self.pos_type = 'abs'
        self.move_type = 'jog'
        self.feed_vel = 0

        self.position = [0,0,0] #current position
        self.position_l = [0,0,0] #last position
        self.move_position = [0,0,0] #target position

    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('control thread start')
        time_l = -1
        while True:
            #update positions
            if self.UI.init_flag:
                for i in range(3):
                     self.position[i] = self.UI.bead_dict['position'][i].get_value()

            #start movement
            if self.move_status == 1:
                #calculate target move position
                for i in range(3):
                    if self.pos_type == 'abs':
                        self.move_position[i] = self.set_position[i]
                    elif self.pos_type == 'rel':
                        self.move_position[i] = self.set_position[i] + self.position[i]
                    #disable position and current settings
                    self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(True)
                for i in range(4):
                    self.UI.set_current_sbox[i].spinbox.setReadOnly(True)
                dpos = [a - b for a,b in zip(self.move_position,self.position)]
                self.change_currents(self.calculate_currents(dpos))
                self.UI.ps_cont_tbutton.set_toggle(True)
                self.move_status = 2
                print 'start'

            if self.move_status == 2:
                if time.clock() - time_l > 0.1:
                    time_l = time.clock()
                    dpos = [a - b for a,b in zip(self.move_position,self.position)]
                    print dpos
                    self.change_currents(self.calculate_currents(dpos))
                    print 'continue'

            if self.move_status == 3:
                #enable position and current settings
                for i in range(3):
                    self.UI.magnet_set_pos_sbox[i].spinbox.setReadOnly(False)
                for i in range(4):
                    self.UI.set_current_sbox[i].spinbox.setReadOnly(False)
                self.UI.ps_cont_tbutton.set_toggle(False)
                self.move_status = 0


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
        self.set_position[i] = value
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

    def manual_base_current_changed(self,value):
        self.manual_base_current = value

    def change_currents(self,set_current_list):
        print set_current_list
        for i in range(len(set_current_list)):
            self.UI.set_current_sbox[i].spinbox.setValue(set_current_list[i])

    def calculate_currents(self,dposition):
        max_current = 2.5
        current_factor = 10

        set_current_list = [0,0,0,0]
        dpos = [0,0,0,0]
        for i in range(3):
            dpos[i] = dposition[i]*current_factor
            if abs(dpos[i]) > max_current:
                dpos[i] = max_current*dpos[i]/abs(dpos[i])

        dict = {'x+':0,'x-':1,'y+':2,'y-':3,'z+':4,'z-':5}
        current_mapping = [[1,1,0.5,0.5],#x+
                           [0.5,0.5,1,1],#x-
                           [0,1,1,0],#y+
                           [1,0,0,1],#y-
                           [1,-1,-1,1],#z+
                           [-1,-1,1,1]]#z-
        for i in range(4):
            for j in range(3):
                if dpos[j] > 0:
                    current =  current_mapping[2*j][i]*dpos[j]
                else:
                    current =  current_mapping[2*j+1][i]*dpos[j]
                set_current_list[i] += current

        return set_current_list