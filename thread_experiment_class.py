import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadExperiment(QThread):
    def __init__(self,UI):
        super(ThreadExperiment, self).__init__()

        self.set_positions = [0,0,0] #value set in UI

        self.UI = UI

        self.positions = [0,0,0]
        self.camera_positions = [0,0,0]
        self.positions_l = [0,0,0]

        self.update_flag = False


    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('experiment thread start')
        while True:
            print 'something'
            time.sleep(1)

    def exp_toggle(self,toggle_flag):
        # if toggle_flag == True:
        # f_path = os.getcwd()+'\\exp\\'
        # f_name = 'camera_positions'
        # f_path = f_path + f_name +'.csv'
        # # open file
        # with open(f_path,'r+') as f:
        #     if mode == 'load':
        #         reader = csv.reader(f)
        #         read_list = []
        #         for position in reader.next():
        #             read_list.append(position)
        #         for i in range(3):
        #             self.camera_offsets[i] = float(read_list[i])
        #
        #         for i in range(5):
        #             read_list = []
        #             for position in reader.next():
        #                 read_list.append(position)
        #             for j in range(3):
        #                 self.tip_positions[i][j] = float(read_list[j])
        #     elif mode == 'save':
        #         writer = csv.writer(f)
        #         write_list = []
        #         for offset in self.camera_offsets:
        #             write_list.append('{0:7.4f}'.format(offset))
        #         writer.writerow(write_list)
        #         for i in range(5):
        #             write_list = []
        #             for j in range(3):
        #                 write_list.append('{0:7.4f}'.format(self.tip_positions[i][j]))
        #             writer.writerow(write_list)
        #     print('exp start')
        # elif toggle_flag == False:
        #     print('exp stop')

    def bead_changed(self,positions,camera_positions):
        self.update_flag = True
        for i in range(3):
            self.positions_l[i] = self.positions[i]
            self.positions[i] = positions[i]
            self.camera_positions[i] = camera_positions[i]