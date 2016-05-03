import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadActuator(QThread,axis_list):
    def __init__(self):
        super(ThreadActuator, self).__init__()

        self.axis_list = axis_list

    def run(self):
        print('thread act done')