import time
import numpy as np
import cv2
import cv2.cv as cv

from PySide.QtCore import *
from PySide.QtGui import *

class DisplayWidget(QWidget):
    def __init__(self,thread):
        super(DisplayWidget, self).__init__()
        self.thread_det = thread
        self.draw_flag = False
        self.time_refresh = 0
        self.scale = 0.1
        self.bead_size = 41.13

    def paintEvent(self, *args, **kwargs):
        self.getFrames()
        if self.draw_flag:
            qp = QPainter()
            qp.begin(self)
            self.drawFrames(qp)
            qp.end()
        self.update()
        
    def getFrames(self):
        if self.thread_det.time_refresh > self.time_refresh:
            self.draw_flag = True
            self.n_frame_rect = self.thread_det.n_frame_rect
            self.n_frame = self.thread_det.n_frame
            self.time_refresh = self.thread_det.time_refresh
            self.n_frame_beads = self.thread_det.n_frame_beads
            self.cn_frame = self.thread_det.cn_frame
            self.cn_frame_sobel = self.thread_det.cn_frame_sobel
            self.bead_size = self.thread_det.bead_size
            self.no_beads = self.thread_det.no_beads

    def drawFrames(self, qp):
        #Qt frame
        q_frame = NumPyQImage(self.n_frame_rect)                 # Qt frame
        self.n_frame_cam1 = self.n_frame
        #scaled Qt frame
        sq_frame = q_frame.scaled(q_frame.width()*self.scale,q_frame.height()*self.scale,) # resize # small Qt frame
        qp.drawImage(QPoint(20, 20), sq_frame)
        if self.no_beads > 0:
            q_frame_beads = NumPyQImage(self.n_frame_beads)   # convert to QImage
            sq_frame_beads = q_frame_beads.scaled(q_frame_beads.width()*self.scale,q_frame_beads.height()*self.scale,) # resize
            qp.drawImage(QPoint(20, 250), sq_frame_beads)  # Display the frame

            cq_frame = NumPyQImage(self.cn_frame) # convert to QImage
            scq_frame = cq_frame.scaled(cq_frame.width()/2, cq_frame.height()/2,)
            qp.drawImage(QPoint(20, 500), scq_frame)  # Display the frame

            cq_frame_sobel = NumPyQImage(self.cn_frame_sobel) # convert to QImage
            scq_frame_sobel = cq_frame_sobel.scaled(cq_frame_sobel.width()/2, cq_frame_sobel.height()/2,)
            qp.drawImage(QPoint(200, 500), scq_frame_sobel)  # Display the frame
        
#CLASS to convert NumPy to QImage
class NumPyQImage(QImage):
    def __init__(self, numpyImg):
        #print type(numpyImg), len(numpyImg.shape), numpyImg.shape

        #if len(numpyImg.shape) !=2:
        #    raise ValueError("it's not 2D array, i.e. Mono8")

        if type(numpyImg) is not None:
            numpyImg = np.require(numpyImg,np.uint8,'C') # rearrange to be C style storage
        else:
            numpyImg = np.zeros((100,100),np.uint8)
            numpyImg[:] = (255)

        h, w = numpyImg.shape

        result = QImage(numpyImg.data, w,h,QImage.Format_Indexed8)
        result.ndarray = numpyImg
        for i in range(256):
            result.setColor(i,QColor(i,i,i).rgb())
        self._imgData = result
        super(NumPyQImage, self).__init__(self._imgData)
