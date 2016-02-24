from PySide.QtGui import *

class MomentaryButtonWidget(QWidget):
    #constructor
    def __init__(self,text,slot_on,slot_off):
        super(MomentaryButtonWidget,self).__init__()
        #create button
        self.button = QPushButton(text)
        self.toggleFlag = False

        #connections
        self.button.pressed.connect(self.toggle)
        self.button.pressed.connect(slot_on)
        self.button.released.connect(self.toggle)
        self.button.released.connect(slot_off)

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.button)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

    def toggle(self):
        if self.toggleFlag == False:
            self.toggleFlag = True
        else:
            self.toggleFlag = False

class DoubleToggleButtonWidget(QWidget):
    #constructor
    def __init__(self,text1,text2,slot1,slot2):
        super(DoubleToggleButtonWidget,self).__init__()

        self.slot1 = slot1
        self.slot2 = slot2

        #create widgets
        self.button1 = QPushButton(text1)
        self.button2 = QPushButton(text2)

        #initialise buttons
        self.button1.setEnabled(True)
        self.button2.setEnabled(False)
        self.toggleFlag = False

        #connections
        self.button1.clicked.connect(self.toggle)
        self.button2.clicked.connect(self.toggle)

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.button1)
        self.layout.addWidget(self.button2)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

    def toggle(self):
        #turn on
        if self.toggleFlag == False:
            self.toggleFlag = True
            self.button1.setEnabled(False)
            self.button2.setEnabled(True)
            self.slot1()
        #turn off
        else:
            self.toggleFlag = False
            self.button1.setEnabled(True)
            self.button2.setEnabled(False)
            self.slot2()

