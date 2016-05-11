import time
import numpy as np

from PySide.QtCore import *
from PySide.QtGui import *

from spin_box_widget_class import *
from button_widget_class import *

class Axis_GUI(QObject):
    absrel_trigger = Signal(bool)
    start_trigger = Signal(bool)
    home_trigger = Signal(bool)
    lock_trigger = Signal(bool)
    set_position_trigger = Signal(float)
    jogp_trigger = Signal(bool)
    jogm_trigger = Signal(bool)
    feed_vel_trigger = Signal(float)
    feed_trigger = Signal(bool)
    def __init__(self,axis_name,axis_address):
        super(Axis_GUI,self).__init__()

        self.axis_name = axis_name
        self.axis_address = axis_address

        self.value = ValueDisplayWidget(['Position','mm'],[7,4])
        self.abs_value = ValueDisplayWidget(['Abs','mm'],[7,4])
        self.sbox = SpinBoxWidget(['Set Position','mm'],0,[0,0.005,50],[7,4],self.set_position_changed,False)
        self.zero_button = PushButtonWidget('Zero',self.zero)
        self.home_button = PushButtonWidget('Home',self.home)
        self.lock_tbutton = DoubleToggleButtonWidget(['Lock','Unlock'],self.lock_toggle)
        self.absrel_tbutton = DoubleToggleButtonWidget(['Absolute','Relative'],self.absrel_toggle,'radio')
        self.start_tbutton = DoubleToggleButtonWidget(['Start','Stop'],self.start_toggle)
        self.jogp_mbutton = MomentaryButtonWidget('Jog +',self.jogp_toggle)
        self.jogm_mbutton = MomentaryButtonWidget('Jog -',self.jogm_toggle)
        self.feed_sbox = SpinBoxWidget(['Feed Velocity','mm/s'],0,[-10,0.5,10],[4,1],self.feed_vel_changed,False)
        self.feed_tbutton = DoubleToggleButtonWidget(['Start','Stop','Feed Axis'],self.feed_toggle)

        #tabs
        self.tab = QTabWidget()

        self.functions_widget = QWidget()
        vbox_ = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.home_button)
        hbox.addWidget(self.zero_button)
        vbox_.addLayout(hbox)
        vbox_.addWidget(self.lock_tbutton)
        vbox_.addStretch(1)
        self.functions_widget.setLayout(vbox_)

        self.move_widget = QWidget()
        vbox_ = QVBoxLayout()
        vbox_.addWidget(self.sbox)
        vbox_.addWidget(self.absrel_tbutton)
        vbox_.addWidget(self.start_tbutton)
        vbox_.addStretch(1)
        self.move_widget.setLayout(vbox_)

        self.manual_widget = QWidget()
        vbox_ = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.jogm_mbutton)
        hbox.addWidget(self.jogp_mbutton)
        vbox_.addLayout(hbox)
        vbox_.addWidget(self.feed_tbutton)
        vbox_.addWidget(self.feed_sbox)
        self.manual_widget.setLayout(vbox_)

        self.tab.addTab(self.functions_widget,'Functions')
        self.tab.addTab(self.move_widget,'Move')
        self.tab.addTab(self.manual_widget,'Manual')

        self.rxbar = QLineEdit()
        self.rxbar.setReadOnly(True)
        self.txbar = QLineEdit()
        self.txbar.setReadOnly(True)

        self.vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.value)
        hbox.addStretch(1)
        hbox.addWidget(self.abs_value)
        self.vbox.addLayout(hbox)
        self.vbox.addWidget(self.tab)
        self.vbox.addWidget(self.rxbar)
        self.vbox.addWidget(self.txbar)
        self.widget = QWidget()
        self.widget.setLayout(self.vbox)

    def update_handle(self,position):
        self.value.set_value(position)
        #print('position updated:{0}'.format(position))

    def rx_handle(self,rx):
        self.rxbar.setText('rx:'+rx)

    def tx_handle(self,tx):
        self.txbar.setText('tx:'+tx)

    def set_position_changed(self,value):
        self.set_position_trigger.emit(value)

    def absrel_toggle(self,toggle_flag):
        self.absrel_trigger.emit(toggle_flag)

    def start_toggle(self,toggle_flag):
        self.start_trigger.emit(toggle_flag)

    def lock_toggle(self,toggle_flag):
        self.lock_trigger.emit(toggle_flag)

    def jogp_toggle(self,toggle_flag):
        self.jogp_trigger.emit(toggle_flag)

    def jogm_toggle(self,toggle_flag):
        self.jogm_trigger.emit(toggle_flag)

    def zero(self):
        print(self.axis_name + ': zero')

    def home(self):
        print(self.axis_name + ': home')

    def feed_toggle(self,toggle_flag):
        print(self.axis_name + ': feed')

    def feed_vel_changed(self,feed_vel):
        self.feed_vel_trigger.emit(feed_vel)
