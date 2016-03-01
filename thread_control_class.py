import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadControl(QThread):
    def __init__(self,UI):
        super(ThreadControl, self).__init__()
        self.set_position = [0,0,0]
        self.UI = UI

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
        i = dict[ref_text]
        print('manual direction' + str(i))

    def hold_toggle(self,toggle_flag):
        if toggle_flag == True:
            print('bead hold')
        elif toggle_flag == False:
            print('bead release')