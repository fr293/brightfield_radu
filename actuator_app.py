# -*- coding: utf-8 -*-
sandbox = False

import sys
from math import *
import time
import atexit
import serial

# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *
# from PySide import QtGui, QtCore

from spin_box_widget_class import *
from thread_power_supply_class import *
from button_widget_class import *

if sandbox == False:
    from display_widget_class import *
from thread_detection_class import *
from axis_class import *
from thread_control_class import *
from thread_actuator_class import *

import pyqtgraph as pg

mutex = QMutex()


# ****************************************************
# ******* CLASS - THREAD FOR GUI (main thread) *******
class GUIWindow(QMainWindow):
    # constructor
    def __init__(self):
        super(GUIWindow, self).__init__()
        self.init_flag = False

        self.mutex = QMutex()
        self.initUI()
        self.thread_act = ThreadActuator(self, self.axis_GUI_list)
        self.thread_act.start()

        self.init_flag = True

    def __del__(self):
        print 'Exiting'
        self.thread_act.exit()
        self.thread_act.wait()
        print "Exit"

    # Initialisation of GUI interface
    def initUI(self):
        # window characteristics
        dimx = 300
        dimy = 800
        self.setGeometry(200, 50, dimx, dimy)  # Coordinates of the window on the screen, dimension of window
        self.setWindowTitle('Actuator Control')
        self.setWindowIcon(QIcon('icon.png'))

        self.create_act_group()

        # create layouts
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.act_group)

        # create widgets/dock widgets from group boxes
        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        # set widgets to main window
        self.setCentralWidget(main_widget)

    def create_act_group(self):
        vbox = QVBoxLayout()
        self.act_estop_button = PushButtonWidget('Emergency Stop', self.act_estop)
        vbox.addWidget(self.act_estop_button)
        self.axis_GUI_list = []
        for axis_label, axis_address in zip(['x-axis', 'y-axis', 'y2-axis'], [1, 2, 3]):
            # create axis object
            axis = Axis_GUI(axis_label, axis_address)
            self.axis_GUI_list.append(axis)
            # group box
            gbox = QGroupBox(axis_label)
            gbox.setLayout(axis.vbox)
            vbox.addWidget(gbox)
        vbox.addStretch(1)
        self.act_textbar = QLineEdit()
        self.act_textbar.setReadOnly(True)
        vbox.addWidget(self.act_textbar)
        # add everything to group box
        self.act_group = QGroupBox('ACTUATOR CONTROL PANEL')
        self.act_group.setLayout(vbox)
        self.act_group.setFixedWidth(300)

    def act_estop(self):
        self.thread_act.estop()
        print('EMERGENCY STOP')


# ******** MAIN
def main():
    app = QApplication.instance()  # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QApplication(sys.argv)

    GUIObject = GUIWindow()
    GUIObject.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
