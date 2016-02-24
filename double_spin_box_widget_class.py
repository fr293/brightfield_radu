from PySide.QtGui import *

class DoubleSpinBoxWidget(QWidget):
    #constructor
    def __init__(self,text,initVal,rangeVal,slot):
        super(DoubleSpinBoxWidget,self).__init__()
        
        #create widgets
        self.label = QLabel(text)
        self.spinbox = QDoubleSpinBox()
        
        #double spin box settings
        minVal = rangeVal[0]
        step = rangeVal[1]
        maxVal = rangeVal[2]
        self.spinbox.setMinimum(minVal)
        self.spinbox.setSingleStep(step)
        self.spinbox.setMaximum(maxVal)
        decimals = 3
        self.spinbox.setDecimals(decimals)
        
        self.spinbox.setValue(initVal)
        self.value = initVal
        
        #connections
        self.spinbox.valueChanged.connect(self.value_changed)
        self.spinbox.valueChanged.connect(slot)        
        
        #add widgets to layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinbox)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.setLayout(self.layout)
        
    def value_changed(self):
        self.value = self.spinbox.value()
