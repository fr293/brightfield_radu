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

class ThreadDetection(QThread):
    def __init__(self):
        super(ThreadDetection, self).__init__()
        self.time_refresh = 0
        self.detect_flag = True
        
        self.area_min = 990
        self.area_max = 7000
        self.circ_min = 0.80
        self.circ_max = 1.23
        self.thresh1_min = 80
        self.thresh1_max = 250
        self.bead_size = 41.13
        
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

        self.frame = camcapture.getFrame()
        self.frame.announceFrame()
        camcapture.startCapture()
        camcapture.runFeatureCommand("AcquisitionStart")

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

    def run(self):  # method which runs the thread
        print('Detection Thread Started')
        while True:

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

            self.n_frame = np.ndarray(buffer=frame_data, dtype=np.uint8, shape=(self.frame.height,self.frame.width))
            self.n_frame_rect = self.n_frame.copy()
            cv2.rectangle(self.n_frame_rect,(x_min,y_min),(x_max,y_max),(255,127,127),4)

            #cv2.rectangle(n_frame_rect,(x11,y11),(x12,y12),(255,127,127),4)
            #cv2.rectangle(n_frame_rect,(x21,y21),(x22,y22),(255,127,127),4)
            #cv2.rectangle(n_frame_rect,(x31,y31),(x32,y32),(255,127,127),4)
            #cv2.rectangle(n_frame_rect,(x41,y41),(x42,y42),(255,127,127),4)
            #cv2.rectangle(n_frame_rect,(x51,y51),(x52,y52),(255,127,127),4)




            if self.detect_flag:
                self.n_frame_beads,xr,yr,wr,hr,self.no_beads,xc,yc,c_factor = self.detect_beads(self.n_frame,
                                                                      self.thresh1_min,self.thresh1_max,
                                                                      self.circ_min,self.circ_max,
                                                                      self.area_min,self.area_max)
                if self.no_beads > 0: # At least one bead is detected
                    self.cn_frame = self.crop(self.n_frame,xr,yr,wr,hr,2) # croped frame with the bead // croped numpy

                    self.cn_frame_sobel = self.sobel_edge(self.cn_frame)

                    self.center_x = xc
                    self.center_y = yc
                    print('xc: ' + str(xc) + '; yc: ' +str(yc))
                    #self.text_changed_x_y()

                    self.width = wr
                    self.height = hr
                    print('wr: ' + str(wr) + '; hr: ' +str(hr))
                    #self.text_changed_w_h()

                    #print type(self.no_beads+0.0)
                    self.round_factor = round(c_factor,2)
                    #self.text_changed_round()

            self.time_refresh = time.clock()

    def value_changed(self,value,ref_text):
        print('bead value changed: '+ref_text)


    #returns picture after thresholding
    def threshold_frame(self,frame,thresh_min,thresh_max):
        res, ret_frame = cv2.threshold(frame,thresh_min,thresh_max,cv2.THRESH_BINARY)
        return ret_frame

    #detects and filter beads
    def detect_beads(self,n_frame,thresh_min,thresh_max,circ_min,circ_max,area_min,area_max):

        #gray = cv2.cvtColor(n_frame,cv2.COLOR_BGR2GRAY) # might not be necessary
        gray = n_frame.copy()
        gray_contours = gray.copy()

        thresh = self.threshold_frame(gray,thresh_min,thresh_max)
        thresh_initial = thresh.copy() # a copy just in case, as it's changed by findContours

        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

        no_detected = 0
        xr,yr,wr,hr,cx,cy = 0,0,0,0,0,0
        ccirc = 0.5
        for cont in contours:
            area = cv2.contourArea(cont)
            if area >0.1: # circ requires area != 0
                length = cv2.arcLength(cont,closed=True)
                circ = (length*length)/(4.0*np.pi*area) # circularity factor
                #area_min, area_max = 100, 1500 # to be transmited as parameters - FUTURE
                #circ_min, circ_max = 0.8, 1.3 # to be transmited as parameters - FUTURE
                if area > area_min and area <area_max:
                    if circ > circ_min and circ <circ_max:
                        xr,yr,wr,hr = cv2.boundingRect(cont)
                        xc = xr + int(wr/2.0)
                        yc = yr + int(hr/2.0)
                        #print circ
                        cv2.rectangle(gray,(xc-wr,yc-hr),(xc+wr,yc+hr),(255,0,0),2)
                        M = cv2.moments(cont) # finding centroids of cont
                        cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
                        no_detected = no_detected + 1
                        ccirc = circ
                        #print cx,cy, xc,yc

        #print no_detected, wr,hr,xc,yc
        cv2.drawContours(gray_contours, contours,-1,(0,255,0)) # all contours detected '-1' //
        return gray,xr,yr,wr,hr,no_detected,cx,cy,ccirc #, gray_contours, thresh, thresh_initial

    #crop picture with bead
    def crop_stack(self,n_frame,xc,yc):

        y1 = yc-46
        y2 = yc+46

        x1 = xc-46
        x2 = xc+46

        ret_frame = np.copy(n_frame[y1:y2,x1:x2])

        return ret_frame

    #detects and filter beads for stack
    def detect_beads_stack(self,n_frame):

        th_min = 80
        th_max = 255
        circ_min = 0.8
        circ_max = 1.3
        area_min = 600
        area_max = 1500

        xc_bead_i = 1495
        yc_bead_i = 970

        xc_bead_f = xc_bead_i
        yc_bead_f = yc_bead_i

        n_frame_crop = crop_stack(n_frame,xc_bead_i,yc_bead_i)

        gray = n_frame_crop.copy()
        thresh = NumThres(gray,th_min,th_max)

        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) >0:  # only one bead is detected
            for cont in contours:
                area = cv2.contourArea(cont)
                if area >100: # circ requires area != 0
                    length = cv2.arcLength(cont,closed=True)
                    circ = (length*length)/(4.0*np.pi*area) # circularity factor
                    if area > area_min and area <area_max:
                        if circ > circ_min and circ <circ_max:
                            M = cv2.moments(cont) # finding centroids of cont
                            xxc,yyc = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
                            xc_bead_f = xc_bead_i -46 + xxc
                            yc_bead_f = yc_bead_i -46 + yyc

        n2_frame_crop = crop_stack(n_frame,xc_bead_f,yc_bead_f)

        return n2_frame_crop, xc_bead_f,yc_bead_f #, gray_contours, thresh, thresh_initial


    #crop picture with bead
    def crop(self,n_frame,xr,yr,wr,hr,bead_slider):

        if wr % 2 != 0:  # it seems that wr and hr must be an even number to prevent distorsion of the picture
            wr = wr + 1
        if hr % 2 != 0:
            hr = hr + 1

        xc = xr + int(wr/2.0)
        yc = yr + int(hr/2.0)

        #y1 = yc-int(1.0*hr)
        #y2 = yc+int(1.0*hr)

        #x1 = xc-int(1.0*wr)
        #x2 = xc+int(1.0*wr)

        y1 = yc-int(bead_slider*46)
        y2 = yc+int(bead_slider*46)

        x1 = xc-int(bead_slider*46)
        x2 = xc+int(bead_slider*46)

        size_crop = (wr,hr,1)

        ret_frame = np.copy(n_frame[y1:y2,x1:x2])

        return ret_frame

    #return modified image by SOBEL filter
    def sobel_edge(self,n_frame):
        kernel = 3
        ddepth = cv2.CV_16S

        img_sobel_x = cv2.Sobel(n_frame, ddepth,1,0,ksize=kernel,borderType=cv2.BORDER_DEFAULT) # x derivative
        img_sobel_y = cv2.Sobel(n_frame, ddepth,0,1,ksize=kernel,borderType=cv2.BORDER_DEFAULT) # y derivative

        #img_sobel_x = cv2.Scharr(n_frame, ddepth,1,0)
        #img_sobel_y = cv2.Scharr(n_frame, ddepth,0,1)

        img_sobel_x_abs=cv2.convertScaleAbs(img_sobel_x) # converting all to positive // to uint8
        img_sobel_y_abs=cv2.convertScaleAbs(img_sobel_y) # converting all to positive // to uint8

        img_sobel_n = cv2.addWeighted(img_sobel_x_abs,0.5, img_sobel_y_abs, 0.5,0) # norm = abs(x) + abs(y)
        # it provides similar results like norm = sqrt(x*x+y*y)
        return img_sobel_n

    #return focus parameter bead reference stack
    def bead_focus_stack(self,n_frame):

        s_in_frame, xc,yc  = detect_beads_stack(n_frame)
        s_out_frame = sobel_edge(s_in_frame)

        avg, sigma = cv2.meanStdDev(s_out_frame)

        focus_param = round(sigma[0][0]/avg[0][0],3)

        return focus_param, xc, yc


    #return theoretical focus param s
    def f1_analytic(self,x):
        a = -502568.69217
        b = 206443.52808
        c = -28265.96318
        d = 1289.98324
        return a + b*x + c*x*x + d*x*x*x

    def f2_analytic(self,x):
        a = 491477.6662
        b = -201782.91117
        c = 27613.70843
        d = -1259.57454
        return a + b*x + c*x*x + d*x*x*x

    #get z offset of the bead
    def bead_z_evaluate(self,f1, f2):
        tol = 0.001
        x_min = 7.27
        x_max = 7.35
        c =  (x_min+x_max)/2

        while abs(f1_analytic(c)-f1) > tol or (x_max - x_min)/2 > tol:
            if (f1_analytic(c)-f1>0 and f1_analytic(x_min)-f1>0) or (f1_analytic(c)-f1<0 and f1_analytic(x_min)-f1<0):
                x_min = c
            else:
                x_max = c
            c =  (x_min+x_max)/2
        x1 = c

        x_min = 7.27
        x_max = 7.35
        c =  (x_min+x_max)/2

        while abs(f2_analytic(c)-f2) > tol or (x_max - x_min)/2 > tol:
            if (f2_analytic(c)-f2>0 and f2_analytic(x_min)-f2>0) or (f2_analytic(c)-f2<0 and f2_analytic(x_min)-f2<0):
                x_min = c
            else:
                x_max = c
            c =  (x_min+x_max)/2
        x2 = c

        x_avg = (x1+x2)/2
        return x_avg

    #move or not the actuator
    def follow_bead(self,x_av):
        x_1 = 7.25995
        x_2 = 7.35794

        x_half = (x_1+x_2)/2

        if abs(x_av-x_half)>0.015:
            go_act = True
            rel_z_go = -(x_av - x_half)
        else:
            go_act = False
            rel_z_go =0.0

        return go_act, rel_z_go

    def follow_bead_new(self,f_1_over_f_2):
        #f_11 = 1.15    # intial - default
        #f_22 = 1.05    # intial - default

        f_11 = 1.15
        f_22 = 1.05

        x11 = 7.60268
        x22 = 7.64864
        y11 = 1.38048
        y22 = 0.71469

        slope = (y11-y22)/(x11-x22)
        inters = y11 - slope*x11

        z_actual = (f_1_over_f_2-inters)/slope
        z_desired = (1.1-inters)/slope

        #x_half = (x_1+x_2)/2

        if f_1_over_f_2>f_11 or f_1_over_f_2<f_22:
            go_act = True
            delta_z_for_limit = z_actual - z_desired
            logic_test = delta_z_for_limit >0
            if abs(delta_z_for_limit)>0.005:
                if logic_test:
                    rel_z_go = -0.005
                else:
                    rel_z_go = 0.005
            else:
                rel_z_go = -(z_actual - z_desired)
        else:
            go_act = False
            rel_z_go =0.0

        return go_act, rel_z_go

    def delta_z_bead(self,x_av):
        x_1 = 7.25995
        return x_av-x_1

