from PySide.QtGui import *


class SpinBoxWidget(QWidget):
    #constructor
    def __init__(self,text,initial_value,value_range,float_digits,slot):
        super(SpinBoxWidget,self).__init__()

        digits = float_digits[0]
        decimals = float_digits[1]

        #create widgets
        self.label = QLabel(text)
        self.spinbox = QDoubleSpinBox()

        #spin box settings
        minVal = value_range[0]
        step = value_range[1]
        maxVal = value_range[2]
        self.spinbox.setMinimum(minVal)
        self.spinbox.setSingleStep(step)
        self.spinbox.setMaximum(maxVal)
        self.spinbox.setDecimals(decimals)

        #connections
        self.spinbox.valueChanged.connect(self.set_value_changed)
        self.spinbox.valueChanged.connect(slot)

        self.spinbox.setValue(initial_value)
        self.set_value = initial_value


        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.spinbox)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

    def set_value_changed(self):
        self.set_value = self.spinbox.value()

class DoubleSpinBoxWidget(QWidget):
    #constructor
    def __init__(self,text,initial_value,value_range,float_digits,slot,*args):
        super(DoubleSpinBoxWidget,self).__init__()

        digits = float_digits[0]
        decimals = float_digits[1]

        #create widgets
        self.label = QLabel(text)
        self.spinbox = QDoubleSpinBox()
        self.format_string = str('{0:'+'{0}.{1}f'.format(digits,decimals)+'}')
        if args:
            self.format_string = self.format_string + ' ' + args[0]
        self.value_label = QLabel(self.format_string.format(initial_value))
        
        #double spin box settings
        minVal = value_range[0]
        step = value_range[1]
        maxVal = value_range[2]
        self.spinbox.setMinimum(minVal)
        self.spinbox.setSingleStep(step)
        self.spinbox.setMaximum(maxVal)
        self.spinbox.setDecimals(decimals)
        self.spinbox.setValue(initial_value)

        #connections
        self.spinbox.valueChanged.connect(self.set_value_changed)
        self.spinbox.valueChanged.connect(slot)

        self.spinbox.setValue(initial_value)
        self.set_value = initial_value
        
        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.spinbox)
        self.layout.addStretch(1)
        self.layout.addWidget(self.value_label)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.setLayout(self.layout)
        
    def set_value_changed(self):
        self.set_value = self.spinbox.value()
        self.value_label.setText(self.format_string.format(self.set_value))

    def value_changed(self,newVal):
        self.value_label.setText(str(newVal))
