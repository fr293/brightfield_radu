import time
import numpy as np
import cv2
#import cv2.cv as cv

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
        self.resolution = self.thread_det.resolution
        self.volume_x = self.thread_det.volume_x
        self.volume_y = self.thread_det.volume_y
        self.volume_z = self.thread_det.volume_z

        self.positions = [0,0,0]
        self.camera_positions = [0,0,0]

        self.display_resx = 400
        self.display_resy = int(self.display_resx*(float(self.camera_resy)/self.camera_resx))
        self.scale = float(self.display_resx)/self.camera_resx

        self.save_img_flag = False
        self.save_video_flag = False
        self.n_video = 0

    def paintEvent(self, *args, **kwargs):
        if self.draw_flag:
            qp = QPainter()
            qp.begin(self)
            self.drawFrames(qp)
            qp.end()
        self.update()
        
    def getFrames(self,n,n_frame_rect,nbead,*args):
        self.draw_flag = True
        if n == 1:
            self.n_frame_rect = n_frame_rect
            #self.n_frame = n_frame
            self.nbead1 = 0#nbead
            # if self.nbead1 > 0:
            #     self.n_frame_beads = args[0]
            #     self.cn_frame = args[1]
            #     self.cn_frame_sobel = args[2]

        if n == 2:
            self.n_frame_rect2 = n_frame_rect
            #self.n_frame2 = n_frame
            self.nbead2 = 0#nbead
            # if self.nbead2 > 0:
            #     self.n_frame_beads2 = args[0]
            #     self.cn_frame2 = args[1]
            #     self.cn_frame_sobel2 = args[2]

        self.time_refresh = time.clock()

    def drawFrames(self, qp):
        resx = self.camera_resx
        resy = self.camera_resy
        resolution = self.resolution
        x_mid = resx/2
        y_mid = resy/2


        #draw crosshair on camera 1
        crosshair = 100
        cv2.line(self.n_frame_rect,(0,y_mid),(x_mid-crosshair,y_mid),(255,127,127),8)
        cv2.line(self.n_frame_rect,(x_mid,0),(x_mid,y_mid - crosshair),(255,127,127),8)
        cv2.line(self.n_frame_rect,(resx,y_mid),(x_mid+crosshair,y_mid),(255,127,127),8)
        cv2.line(self.n_frame_rect,(x_mid,resy),(x_mid,y_mid + crosshair),(255,127,127),8)

        #draw crosshair on zero
        ch1 = 50
        ch2 = 200
        x_zero = int(x_mid - self.camera_positions[0]/resolution)
        y_zero = int(y_mid + self.camera_positions[1]/resolution)
        cv2.line(self.n_frame_rect,(x_zero+ch1,y_zero),(x_zero+ch2,y_zero),(127,127,255),8)
        cv2.line(self.n_frame_rect,(x_zero-ch1,y_zero),(x_zero-ch2,y_zero),(127,127,255),8)
        cv2.line(self.n_frame_rect,(x_zero,y_zero+ch1),(x_zero,y_zero+ch2),(127,127,255),8)
        cv2.line(self.n_frame_rect,(x_zero,y_zero-ch1),(x_zero,y_zero-ch2),(127,127,255),8)

        #draw volume
        w1 = int((self.volume_x/2)/resolution)
        h1 = int((self.volume_y/2)/resolution)
        cv2.line(self.n_frame_rect,(x_zero+w1,y_zero-h1),(x_zero+w1,y_zero+h1),(127,127,255),8)
        cv2.line(self.n_frame_rect,(x_zero-w1,y_zero-h1),(x_zero-w1,y_zero+h1),(127,127,255),8)
        cv2.line(self.n_frame_rect,(x_zero-w1,y_zero+h1),(x_zero+w1,y_zero+h1),(127,127,255),8)
        cv2.line(self.n_frame_rect,(x_zero-w1,y_zero-h1),(x_zero+w1,y_zero-h1),(127,127,255),8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(self.n_frame_rect,'200um', (resx - 375,resy-150), font, 3,(255,255,255),10)
        cv2.line(self.n_frame_rect,(resx-450,resy - 75),(resx-50,resy-75),(255,255,255),20)


        #camera 1
        q_frame = NumPyQImage(self.n_frame_rect)#convert to QImage
        sq_frame = q_frame.scaled(q_frame.width()*self.scale,q_frame.height()*self.scale,) #resize
        qp.drawImage(QPoint(20, 20), sq_frame) #display
        if self.nbead1 > 0:
            q_frame_beads = NumPyQImage(self.n_frame_beads)
            sq_frame_beads = q_frame_beads.scaled(q_frame_beads.width()*self.scale_sm,q_frame_beads.height()*self.scale_sm,)
            qp.drawImage(QPoint(20, self.display_resy+40), sq_frame_beads)

            cq_frame = NumPyQImage(self.cn_frame)
            scq_frame = cq_frame.scaled(cq_frame.width()/2, cq_frame.height()/2,)
            qp.drawImage(QPoint(20, 2*self.display_resy+60), scq_frame)

            cq_frame_sobel = NumPyQImage(self.cn_frame_sobel)
            scq_frame_sobel = cq_frame_sobel.scaled(cq_frame_sobel.width()/2, cq_frame_sobel.height()/2,)
            qp.drawImage(QPoint(200, 2*self.display_resy+60), scq_frame_sobel)

        #camera 2
        q_frame2 = NumPyQImage(self.n_frame_rect2)#convert to QImage
        sq_frame2 = q_frame2.scaled(q_frame2.width()*self.scale,q_frame2.height()*self.scale,) #resize
        qp.drawImage(QPoint(self.display_resx+40, 20), sq_frame2) #display
        if self.nbead2 > 0:
            q_frame_beads2 = NumPyQImage(self.n_frame_beads2)
            sq_frame_beads2 = q_frame_beads2.scaled(q_frame_beads2.width()*self.scale_sm,q_frame_beads2.height()*self.scale_sm,)
            qp.drawImage(QPoint(self.display_resx+40, self.display_resy+40), sq_frame_beads2)

            cq_frame2 = NumPyQImage(self.cn_frame2)
            scq_frame2 = cq_frame2.scaled(cq_frame2.width()/2, cq_frame2.height()/2,)
            qp.drawImage(QPoint(self.display_resx+40, 2*self.display_resy+60), scq_frame2)

            cq_frame_sobel2 = NumPyQImage(self.cn_frame_sobel2)
            scq_frame_sobel2 = cq_frame_sobel2.scaled(cq_frame_sobel2.width()/2, cq_frame_sobel2.height()/2,)
            qp.drawImage(QPoint(self.display_resx+220, 2*self.display_resy+60), scq_frame_sobel2)

        if self.save_img_flag:
            cv2.imwrite(self.filepath,self.n_frame_rect)
            self.save_img_flag = False
            print 'image saved: ' + self.filepath

        if self.save_video_flag:
            filepath = self.filepath + '_{0}'.format(self.n_video) +'.jpeg'
            cv2.imwrite(filepath,cv2.resize(self.n_frame_rect,None,fx=0.5, fy=0.5,interpolation = cv2.INTER_LINEAR))
            self.n_video = self.n_video + 1
            print 'image saved: ' + filepath

    def bead_position_changed(self,positions,camera_positions,tip_positions,axis_positions):
        for i in range(3):
            self.positions[i] = positions[i]
            self.camera_positions[i] = camera_positions[i]

    def save_img(self,filepath):
        self.filepath = filepath + '.jpeg'
        self.save_img_flag = True
        return

    def save_video(self,filepath,toggle_flag):
        if toggle_flag:
            self.filepath = filepath
            self.save_video_flag = True
            self.n_video = 0
        else:
            self.save_video_flag = False
            self.n_video = 0
        return

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

        result = QImage(numpyImg.data, w, h, QImage.Format_Indexed8)
        result.ndarray = numpyImg
        for i in range(256):
            result.setColor(i,QColor(i,i,i).rgb())
        self._imgData = result
        super(NumPyQImage, self).__init__(self._imgData)
