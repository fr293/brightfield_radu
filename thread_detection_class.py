import time
import numpy as np
import cv2
import cv2.cv as cv

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadDetection(QThread):
    def __init__(self):
        super(ThreadDetection, self).__init__()

    def run(self):  # method which runs the thread
        print('Detection Thread Started')