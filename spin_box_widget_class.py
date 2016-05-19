from PySide.QtGui import *
from PySide.QtCore import *

class SpinBoxWidget(QWidget):
    #constructor
    def __init__(self,text_list,initial_value,value_range,float_digits,slot,value_disp_flag):
        super(SpinBoxWidget,self).__init__()

        digits = float_digits[0]
        decimals = float_digits[1]
        self.slot = slot
        self.ref_flag = False
        if type(text_list) is not list:
            label_text = text_list
            units_text = ''
        else:
            label_text = text_list[0]
            units_text = text_list[1]
            if len(text_list) == 3:
                self.ref_text = text_list[2]
                self.ref_flag = True


        #create widgets
        self.label = QLabel(label_text)
        self.spinbox = QDoubleSpinBox()
        self.format_string = str('{0:'+'{0}.{1}f'.format(digits,decimals)+'}')
        self.units_label = QLabel(units_text)
        self.format_string = self.format_string
        self.value_label = QLabel(self.format_string.format(initial_value))
        
        #double spin box settings
        minVal = value_range[0]
        step = value_range[1]
        maxVal = value_range[2]
        self.spinbox.setMinimum(minVal)
        self.spinbox.setSingleStep(step)
        self.spinbox.setMaximum(maxVal)
        self.spinbox.setDecimals(decimals)

        #connections
        self.spinbox.valueChanged.connect(self.change_set_value)
        self.spinbox.setValue(initial_value)
        
        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.spinbox)
        if value_disp_flag == True:
            self.layout.addStretch(1)
            self.layout.addWidget(self.value_label)
        if units_text != '':
            self.layout.addWidget(self.units_label)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.setLayout(self.layout)
        
    def change_set_value(self):
        #self.value_label.setText(self.format_string.format(self.set_value))
        if self.ref_flag:
            self.slot(self.spinbox.value(),self.ref_text)
        else:
            self.slot(self.spinbox.value())

    def change_value(self,newVal):
        str = self.format_string.format(newVal)
        self.value_label.setText(str)

class ValueDisplayWidget(QWidget):
    trigger = Signal(float)
    #constructor
    def __init__(self,text_list,float_digits,*args):
        super(ValueDisplayWidget,self).__init__()

        digits = float_digits[0]
        decimals = float_digits[1]
        if type(text_list) is not list:
            label_text = text_list
            units_text = ''
        elif len(text_list) == 2:
            label_text = text_list[0]
            units_text = text_list[1]

        self.label = QLabel(label_text)
        self.value_label = QLabel()
        self.units_label = QLabel(units_text)
        self.format_string = str('{0:'+'{0}.{1}f'.format(digits,decimals)+'}')
        self.value_label.setText(self.format_string.format(0))
        if args:
            self.value_label.setText(self.format_string.format(args[0]))

        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.value_label)
        if len(text_list) == 2:
            self.layout.addWidget(self.units_label)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

    def set_value(self,value):
        self.value_label.setText(self.format_string.format(value))
        self.trigger.emit(value)

    def get_value(self):
        return float(self.value_label.text())