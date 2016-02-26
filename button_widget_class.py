from PySide.QtGui import *
from PySide.QtCore import *

class MomentaryButtonWidget(QWidget):
    #constructor
    def __init__(self,text,*args):
        super(MomentaryButtonWidget,self).__init__()
        #create button
        self.button = QPushButton(text)
        self.toggleFlag = False

        #connections
        self.nargs = len(args)
        if self.nargs == 1:
            self.slot_toggle = args[0]
        elif len(args) == 2:
            self.slot_on = args[0]
            self.slot_off = args[1]
        self.button.pressed.connect(self.toggle)
        self.button.released.connect(self.toggle)

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.button)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

    def toggle(self):
        #turn on
        if self.toggleFlag == False:
            self.toggleFlag = True
            if self.nargs == 2:
                self.slot_on
        #turn off
        else:
            self.toggleFlag = False
            if self.nargs == 2:
                self.slot_off
        if self.nargs == 1:
            self.slot_toggle(self.toggleFlag)

class DoubleToggleButtonWidget(QWidget):
    #constructor
    def __init__(self,text_list,slot_list):
        super(DoubleToggleButtonWidget,self).__init__()

        if len(text_list) == 2:
            style = 'horizontal'
        elif len(text_list) == 3:
            style = 'vertical'

        #create widgets
        self.button1 = QPushButton(text_list[0])
        self.button2 = QPushButton(text_list[1])
        if style == 'vertical':
            self.label = QLabel(text_list[2])
            self.label.setAlignment(Qt.AlignHCenter)

        #initialise buttons
        self.button1.setEnabled(True)
        self.button2.setEnabled(False)
        self.toggleFlag = False

        #connections
        if slot_list is not list:
            self.slot_on = slot_list
            self.slot_off = slot_list
            self.returnFlag = True
        else:
            self.slot_on = slot_list[0]
            self.slot_off = slot_list[1]
            self.returnFlag = False
        self.button1.clicked.connect(self.toggle)
        self.button2.clicked.connect(self.toggle)

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.button1)
        self.layout.addWidget(self.button2)
        self.layout.setContentsMargins(0,0,0,0)

        if style == 'horizontal':
            self.setLayout(self.layout)
        elif style == 'vertical':
            self.vbox = QVBoxLayout()
            self.vbox.addWidget(self.label)
            self.vbox.addLayout(self.layout)
            self.setLayout(self.vbox)

    def toggle(self):
        #turn on
        if self.toggleFlag == False:
            self.toggleFlag = True
            self.button1.setEnabled(False)
            self.button2.setEnabled(True)
            if self.returnFlag:
                self.slot_on(self.toggleFlag)
            else:
                self.slot_on()
        #turn off
        else:
            self.toggleFlag = False
            self.button1.setEnabled(True)
            self.button2.setEnabled(False)
            if self.returnFlag:
                self.slot_off(self.toggleFlag)
            else:
                self.slot_off()

class ValueDisplayWidget(QWidget):
    #constructor
    def __init__(self,text,float_digits,*args):
        super(ValueDisplayWidget,self).__init__()

        digits = float_digits[0]
        decimals = float_digits[1]

        self.label = QLabel(text)
        self.value_label = QLabel()

        self.format_string = str('{0:'+'{0}.{1}f'.format(digits,decimals)+'}')
        self.value_label.setText(self.format_string.format(0))
        if args:
            self.value_label.setText(self.format_string.format(args[0]))

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.value_label)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)