import time
import numpy as np

from PySide.QtCore import *
from PySide.QtGui import *

from spin_box_widget_class import *
from button_widget_class import *

class Axis_GUI(QObject):
    absrel_trigger = Signal(bool)
    start_trigger = Signal(bool)
    home_trigger = Signal()
    zero_trigger = Signal()
    lock_trigger = Signal(bool)
    set_position_trigger = Signal(float)
    jogp_trigger = Signal(bool)
    jogm_trigger = Signal(bool)
    feed_velocity_trigger = Signal(float)
    feed_trigger = Signal(bool)
    def __init__(self,axis_name,axis_address):
        super(Axis_GUI,self).__init__()

        self.axis_name = axis_name
        self.axis_address = axis_address

        self.value = ValueDisplayWidget(['Position','mm'],[7,4])
        self.velocity_value = ValueDisplayWidget(['Velocity','mm/s'],[7,4])
        self.sbox = SpinBoxWidget(['Set Position','mm'],0,[-25,0.005,25],[7,4],self.set_position_changed,False)
        self.zero_button = PushButtonWidget('Zero',self.zero)
        self.home_button = PushButtonWidget('Home',self.home)
        self.lock_tbutton = DoubleToggleButtonWidget(['Lock','Unlock'],self.lock_toggle)
        self.absrel_tbutton = DoubleToggleButtonWidget(['Absolute','Relative'],self.absrel_toggle,'radio')
        self.start_tbutton = DoubleToggleButtonWidget(['Start','Stop'],self.start_toggle)
        self.jogp_mbutton = MomentaryButtonWidget('Jog +',self.jogp_toggle)
        self.jogm_mbutton = MomentaryButtonWidget('Jog -',self.jogm_toggle)
        self.feed_sbox = SpinBoxWidget(['Feed Velocity','mm/s'],0,[-10,0.001,10],[6,3],self.feed_velocity_changed,False)
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

        self.tab.addTab(self.manual_widget,'Manual')
        self.tab.addTab(self.move_widget,'Move')
        self.tab.addTab(self.functions_widget,'Functions')


        self.rxbar = QLineEdit()
        self.rxbar.setReadOnly(True)
        self.txbar = QLineEdit()
        self.txbar.setReadOnly(True)

        self.vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.value)
        hbox.addStretch(1)
        hbox.addWidget(self.velocity_value)
        self.vbox.addLayout(hbox)
        self.vbox.addWidget(self.tab)

        hbox = QHBoxLayout()
        hbox.addWidget(self.rxbar)
        hbox.addWidget(self.txbar)
        self.vbox.addLayout(hbox)

        self.widget = QWidget()
        self.widget.setLayout(self.vbox)

    def update_handle(self,position,velocity):
        self.value.set_value(position)
        self.velocity_value.set_value(velocity)
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
        self.zero_trigger.emit()

    def home(self):
        self.home_trigger.emit()

    def feed_toggle(self,toggle_flag):
        self.feed_trigger.emit(toggle_flag)

    def feed_velocity_changed(self,feed_velocity):
        self.feed_velocity_trigger.emit(feed_velocity)
