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
        self.bead_size = self.thread_det.bead_size

        self.camera_resx = self.thread_det.resx
        self.camera_resy = self.thread_det.resy

        self.resx = 300
        self.resy = self.resx*(float(self.camera_resy)/self.camera_resx)
        self.scale = float(self.resx)/self.camera_resx
        self.scale_sm = self.scale
        print(self.scale)

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
            self.nbead1 = self.thread_det.nbead1
            if self.nbead1 > 0:
                self.n_frame_beads = self.thread_det.n_frame_beads
                self.cn_frame = self.thread_det.cn_frame
                self.cn_frame_sobel = self.thread_det.cn_frame_sobel


            self.n_frame_rect2 = self.thread_det.n_frame_rect2
            self.n_frame2 = self.thread_det.n_frame2
            self.nbead2 = self.thread_det.nbead2
            if self.nbead2 > 0:
                self.n_frame_beads2 = self.thread_det.n_frame_beads2
                self.cn_frame2 = self.thread_det.cn_frame2
                self.cn_frame_sobel2 = self.thread_det.cn_frame_sobel2

            self.time_refresh = self.thread_det.time_refresh

    def drawFrames(self, qp):
        #camera 1
        q_frame = NumPyQImage(self.n_frame_rect)#convert to QImage
        sq_frame = q_frame.scaled(q_frame.width()*self.scale,q_frame.height()*self.scale,) #resize
        qp.drawImage(QPoint(20, 20), sq_frame) #display
        if self.nbead1 > 0:
            q_frame_beads = NumPyQImage(self.n_frame_beads)
            sq_frame_beads = q_frame_beads.scaled(q_frame_beads.width()*self.scale_sm,q_frame_beads.height()*self.scale_sm,)
            qp.drawImage(QPoint(20, self.resy+40), sq_frame_beads)

            cq_frame = NumPyQImage(self.cn_frame)
            scq_frame = cq_frame.scaled(cq_frame.width()/2, cq_frame.height()/2,)
            qp.drawImage(QPoint(20, 2*self.resy+60), scq_frame)

            cq_frame_sobel = NumPyQImage(self.cn_frame_sobel)
            scq_frame_sobel = cq_frame_sobel.scaled(cq_frame_sobel.width()/2, cq_frame_sobel.height()/2,)
            qp.drawImage(QPoint(200, 2*self.resy+60), scq_frame_sobel)
        #camera 2
        q_frame2 = NumPyQImage(self.n_frame_rect2)#convert to QImage
        sq_frame2 = q_frame2.scaled(q_frame2.width()*self.scale,q_frame2.height()*self.scale,) #resize
        qp.drawImage(QPoint(self.resx+40, 20), sq_frame2) #display
        if self.nbead2 > 0:
            q_frame_beads2 = NumPyQImage(self.n_frame_beads2)
            sq_frame_beads2 = q_frame_beads2.scaled(q_frame_beads2.width()*self.scale_sm,q_frame_beads2.height()*self.scale_sm,)
            qp.drawImage(QPoint(self.resx+40, self.resy+40), sq_frame_beads2)

            cq_frame2 = NumPyQImage(self.cn_frame2)
            scq_frame2 = cq_frame2.scaled(cq_frame2.width()/2, cq_frame2.height()/2,)
            qp.drawImage(QPoint(self.resx+40, 2*self.resy+60), scq_frame2)

            cq_frame_sobel2 = NumPyQImage(self.cn_frame_sobel2)
            scq_frame_sobel2 = cq_frame_sobel2.scaled(cq_frame_sobel2.width()/2, cq_frame_sobel2.height()/2,)
            qp.drawImage(QPoint(self.resx+220, 2*self.resy+60), scq_frame_sobel2)

#CLASS to convert NumPy to QImage
class NumPyQImage(QImage):
    def __init__(self, numpyImg):
        #print type(numpyImg), len(numpyImg.shape), numpyImg.shape

        #if len(numpyImg.shape) !=2:
        #    raise ValueError("it's not 2D array,  i.e. Mono8")

        # if type(numpyImg) is not None:
        #     numpyImg = np.require(numpyImg,np.uint8,'C') # rearrange to be C style storage
        # else:
        #     numpyImg = np.zeros((100,100),np.uint8)
        #     numpyImg[:] = (255)

        h, w = numpyImg.shape

        result = QImage(numpyImg.data, w,h,QImage.Format_Indexed8)
        result.ndarray = numpyImg
        for i in range(256):
            result.setColor(i,QColor(i,i,i).rgb())
        self._imgData = result
        super(NumPyQImage, self).__init__(self._imgData)
