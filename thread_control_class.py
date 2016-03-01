import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadControl(QThread):
    def __init__(self,UI):
        super(ThreadControl, self).__init__()
        self.set_position = [0,0,0]
        self.UI = UI

        self.manual_base_current = 0

    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('control thread start')

    def absrel_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('abs')
        else:
            print('rel')

    def start_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('magnet start movement')
        else:
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
        for i in range(len(set_current_list)):
            self.UI.set_current_list[i].spinbox.setValue(set_current_list[i])