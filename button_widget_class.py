from PySide.QtGui import *
from PySide.QtCore import *

class PushButtonWidget(QPushButton):
    def __init__(self,text,slot,*args):
        super(PushButtonWidget,self).__init__()
        #create button
        self.setText(text)

        if args:
            self.ref_text = args[0]
            self.ref_flag = True
        else:
            self.ref_flag = False

        self.slot = slot
        self.clicked.connect(self.clicked_slot)

    def clicked_slot(self):
        if self.ref_flag == True:
            self.slot(self.ref_text)
        else:
            self.slot()

class MomentaryButtonWidget(QPushButton):
    #constructor
    def __init__(self,text,slot_list):
        super(MomentaryButtonWidget,self).__init__()
        #create button
        self.button = QPushButton(text)
        self.toggle_flag = False

        #connections
        if slot_list is not list:
            self.slot_on = slot_list
            self.slot_off = slot_list
            self.return_flag = True
        else:
            self.slot_on = slot_list[0]
            self.slot_off = slot_list[1]
            self.return_flag = False
        self.button.pressed.connect(self.toggle)
        self.button.released.connect(self.toggle)

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.button)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)
        
    def toggle(self):
        #turn on
        if self.toggle_flag == False:
            self.toggle_flag = True
            if self.return_flag:
                self.slot_on(self.toggle_flag)
            else:
                self.slot_on()
        #turn off
        else:
            self.toggle_flag = False
            if self.return_flag:
                self.slot_off(self.toggle_flag)
            else:
                self.slot_off()

class DoubleToggleButtonWidget(QWidget):
    #constructor
    def __init__(self,text_list,slot_list,*args):
        super(DoubleToggleButtonWidget,self).__init__()

        if len(text_list) == 2:
            style = 'horizontal'
        elif len(text_list) == 3:
            style = 'vertical'

        if args:
            self.button_style = args[0]
        else:
            self.button_style = 'push' #default

        #create widgets
        if self.button_style == 'push':
            self.button1 = QPushButton(text_list[0])
            self.button2 = QPushButton(text_list[1])
        elif self.button_style == 'radio':
            self.button1 = QRadioButton(text_list[0])
            self.button2 = QRadioButton(text_list[1])

        if style == 'vertical':
            self.label = QLabel(text_list[2])
            self.label.setAlignment(Qt.AlignHCenter)

        #initialise buttons
        if self.button_style == 'push':
            self.button1.setEnabled(True)
            self.button2.setEnabled(False)
        elif self.button_style == 'radio':
            self.button1.setChecked(False)
            self.button2.setChecked(True)
        self.toggle_flag = False

        #connections
        if slot_list is not list:
            self.slot_on = slot_list
            self.slot_off = slot_list
            self.return_flag = True
        else:
            self.slot_on = slot_list[0]
            self.slot_off = slot_list[1]
            self.return_flag = False
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
            self.vbox.setContentsMargins(0,0,0,0)
            self.setLayout(self.vbox)

    def toggle(self):
        #turn on
        if self.toggle_flag == False:
            self.toggle_flag = True
            if self.button_style == 'push':
                self.button1.setEnabled(False)
                self.button2.setEnabled(True)
            if self.button_style == 'radio':
                self.button1.setChecked(True)
                self.button2.setChecked(False)
            if self.return_flag:
                self.slot_on(self.toggle_flag)
            else:
                self.slot_on()
        #turn off
        else:
            self.toggle_flag = False
            if self.button_style == 'push':
                self.button1.setEnabled(True)
                self.button2.setEnabled(False)
            if self.button_style == 'radio':
                self.button1.setChecked(False)
                self.button2.setChecked(True)
            if self.return_flag:
                self.slot_off(self.toggle_flag)
            else:
                self.slot_off()

    def set_toggle(self,set_toggle_flag):
        if set_toggle_flag == True and self.toggle_flag == False:
            self.toggle()
        if set_toggle_flag == False and self.toggle_flag == True:
            self.toggle()