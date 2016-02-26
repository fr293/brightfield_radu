import time
import numpy as np
import cv2
import cv2.cv as cv

from PySide.QtCore import *
from PySide.QtGui import *


try:
    from pymba import *
except ImportError as e:
    print e
    print "Is VimbaC.dll found by the runtime?"
    exit()

class DisplayWidget(QWidget):
    def __init__(self):
        super(DisplayWidget, self).__init__()

        self.bead_zoom = 2

        # ************************************
        # *********** VIDEO config ***********
        vimba=Vimba()
        vimba.startup()
        system = vimba.getSystem()

        camera_ids = vimba.getCameraIds()
        for cam_id in camera_ids:
            print "Camera found: ", cam_id

        # ******* OPEN AND GET VIDEO *********
        camcapture = vimba.getCamera(camera_ids[0])      #connect first camera by 'id'
        camcapture.openCamera()
        cam1_exp_time_dec = camcapture.readRegister("F0F0081C") # address for Shuter
        cam1_exp_time_base_no = int('{0:b}'.format(cam1_exp_time_dec)[20:],2)
        cam1_exp_time_ms = cam1_exp_time_base_no*0.02
        #print 'exp ', cam1_exp_time_base_no, cam1_exp_time_ms
        #static_write_register = "10000010000000000000"
        #cam1_exp_time_base_no_new = 203
        #cam1_exp_time_base_no_new_bin = '{0:012b}'.format(cam1_exp_time_base_no_new)
        #write_register = hex(int(static_write_register + cam1_exp_time_base_no_new_bin,2))[2:-1]
        #print write_register
        #time.sleep(0.5)
        #camcapture.writeRegister("F0F0081C",write_register)

        self.frame = camcapture.getFrame()
        self.frame.announceFrame()
        camcapture.startCapture()
        camcapture.runFeatureCommand("AcquisitionStart")
        # +++++++++++++++++++++++++++++++++++++++

        # ***************************************
        # ******* OPEN AND GET 2nd VIDEO *********
        camcapture_2 = vimba.getCamera(camera_ids[1])      #connect first camera by 'id'
        camcapture_2.openCamera()
        cam2_exp_time_dec = camcapture_2.readRegister("F0F0081C") # address for Shuter
        cam2_exp_time_base_no = int('{0:b}'.format(cam2_exp_time_dec)[20:],2)
        cam2_exp_time_ms = cam2_exp_time_base_no*0.02

        self.frame_2 = camcapture_2.getFrame()
        self.frame_2.announceFrame()
        camcapture_2.startCapture()
        camcapture_2.runFeatureCommand("AcquisitionStart")
        # +++++++++++++++++++++++++++++++++++++++

        self.time_old_ard = time.clock()
        self.index_m =1000
        self.index_exp=1000
        self.time_old_mov = time.clock()
        self.index_letter = 0
        self.index_pct_fps = 0
        self.config_curr = 7
        self.size_focus_avg = 30
        self.max_focus_1_2_avg = 50
        self.storage_focus1 = np.zeros(shape=(self.size_focus_avg))
        self.storage_focus_1_RT = np.zeros(shape=(self.max_focus_1_2_avg))
        self.storage_focus_2_RT = np.zeros(shape=(self.max_focus_1_2_avg))
        self.index_focus_avg = 0
        self.index_focus_avg_1_RT = 0
        self.index_focus_avg_2_RT = 0

    def paintEvent(self, *args, **kwargs):
        qp = QPainter()
        qp.begin(self)
        self.drawFrames(qp)
        qp.end()
        self.update()

    def drawFrames(self, qp):

        small = 16.0
        small_1 = self.bead_zoom
        x_min = 794
        y_min = 470
        x_max = 1794
        y_max = 1470
        x_mid = int((x_min+x_max)/2.0)
        y_mid = int((y_min+y_max)/2.0)
        x_rez = 2588
        y_rez = 1940
        #slider_val = self.slider_bead_size_value

        x11 = 735; x12 = x11 + 134
        y11 = 770; y12 = y11 + 300

        x21 = 870; x22 = x21 + 140
        y21 = 580; y22 = y21 + 690

        x31 = 1080; x32 = x31 + 155
        y31 = 606;  y32 = y31 + 600

        x41 = 1250; x42 = x41 + 180
        y41 = 700;  y42 = y41 + 995

        x51 = 1550; x52 = x51 + 195
        y51 = 705;  y52 = y51 + 600


        self.frame.queueFrameCapture()
        self.frame.waitFrameCapture(1000)
        frame_data = self.frame.getBufferByteData()

        self.time_calib = time.clock()

        n_frame = np.ndarray(buffer=frame_data, dtype=np.uint8, shape=(self.frame.height,self.frame.width))
        print('loaded')
        #print type(n_frame)

        #print "time_1", time.clock()

        #n_frame = camcapture.getImage(5000) #2s timeout # Numpy frame - openCV
        #print "time_2", time.clock()

        #n_frame_2=camcapture_2.getImage(2000)
        #n_frame_2 = self.th_video.n_frame_2_th
        #self.th_video.trigger = False
        #print "time_3", time.clock()
        if (self.index_pct_fps == 0):
            self.time_fps_old = time.clock()

        self.index_pct_fps = self.index_pct_fps + 1

        #print self.index_pct_fps

        n_frame_rect = n_frame.copy()
        #cv2.rectangle(n_frame_rect,(700,500),(1700,1500),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x_min,y_min),(x_max,y_max),(255,127,127),4)

        cv2.rectangle(n_frame_rect,(x11,y11),(x12,y12),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x21,y21),(x22,y22),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x31,y31),(x32,y32),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x41,y41),(x42,y42),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x51,y51),(x52,y52),(255,127,127),4)

        q_frame = NumPyQImage(n_frame_rect)                 # Qt frame
        self.n_frame_cam1 = n_frame

        #if QAbstractButton.isChecked(self.checkbox_p):
        sq_frame = q_frame.scaled(q_frame.width()/small_1,q_frame.height()/small_1,) # resize # small Qt frame
        #qp.drawImage(QPoint(20, 20), sq_frame)        # Display the frame
        qp.drawImage(QPoint(20, 20), sq_frame)



        timp = time.time()
        #print time.clock()#-self.time_old
        #print timp ,timp.second #, #timp.microsecond


#CLASS to convert NumPy to QImageO
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



        h, w =numpyImg.shape

        result = QImage(numpyImg.data, w,h,QImage.Format_Indexed8)
        result.ndarray = numpyImg
        for i in range(256):
            result.setColor(i,QColor(i,i,i).rgb())
        self._imgData = result
        super(NumPyQImage, self).__init__(self._imgData)
