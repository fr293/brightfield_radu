import time
import numpy as np
import cv2
#import cv2.cv as cv
import os
import csv
import atexit

from PySide.QtCore import *
from PySide.QtGui import *

try:
    from pymba import *
except ImportError as e:
    print e
    print "Is VimbaC.dll found by the runtime?"
    exit()

class ThreadDetection(QThread):
    bead_update_trigger = Signal(str,float)
    bead_position_update_trigger = Signal(list,list,list,list)
    focus_update_trigger = Signal(float,float)
    display_frame_update_trigger = Signal(int,object,int)
    display_frame_update_trigger_bead = Signal(int,object,object,int,object,object,object)

    def __init__(self,UI):
        super(ThreadDetection, self).__init__()

        #camera parameters
        self.resx = 2588
        self.resy = 1940
        self.resolution = 0.0005 #mm per px
        self.offsetx = self.resx*self.resolution/2
        self.offsety = self.resy*self.resolution/2
        self.offsetz = 0
        self.volume_x = 0.7
        self.volume_y = 0.7
        self.volume_z = 0.6

        self.time_refresh = 0
        self.detect_flag = True
        
        self.area_min = 990
        self.area_max = 7000
        self.circ_min = 0.80
        self.circ_max = 1.23
        self.thresh1_min = 80
        self.thresh1_max = 250
        self.thresh2_min = 80
        self.thresh2_max = 250
        self.bead_size = 41.13



        #video config
        vimba = Vimba()
        vimba.startup()
        system = vimba.getSystem()
        #get camera IDs
        camera_ids = vimba.getCameraIds()
        for cam_id in camera_ids:
            print "Camera found: ", cam_id
        #open and get video
        camcapture = vimba.getCamera(camera_ids[0])
        camcapture.openCamera()

        # # list camera features
        # cameraFeatureNames = camcapture.getFeatureNames()
        # for name in cameraFeatureNames:
        #     print 'Camera feature:', name

        #self.resx = int(camcapture.WidthMax/2)
        #self.resy = camcapture.HeightMax/2
        camcapture.Width = int(self.resx)
        camcapture.Height = int(self.resy)
        print('Camera 1')
        print 'resx:',camcapture.Width
        print 'resy:',camcapture.Height
        print 'max FPS',camcapture.AcquisitionFrameRateLimit
        self.max_fps = camcapture.AcquisitionFrameRateLimit
        self.set_fps = 1.0
        self.fps = 0.0
        self.time_fps = 0
        self.time_fps_l = -10.0
        self.dt_fps = 0.0


        cam1_exp_time_dec = camcapture.readRegister("F0F0081C") # address for shutter
        cam1_exp_time_base_no = int('{0:b}'.format(cam1_exp_time_dec)[20:],2)
        cam1_exp_time_ms = cam1_exp_time_base_no*0.02
        print(cam1_exp_time_ms)

        self.frame = camcapture.getFrame()
        self.frame.announceFrame()
        camcapture.startCapture()
        camcapture.runFeatureCommand("AcquisitionStart")

        #open and get second video
        camcapture2 = vimba.getCamera(camera_ids[1])
        camcapture2.openCamera()

        camcapture2.Width = int(self.resx)
        camcapture2.Height = int(self.resy)
        print('Camera 2')
        print 'resx:',camcapture2.Width
        print 'resy:',camcapture2.Height
        print 'max FPS',camcapture2.AcquisitionFrameRateLimit

        cam2_exp_time_dec = camcapture2.readRegister("F0F0081C") # address for shutter
        cam2_exp_time_base_no = int('{0:b}'.format(cam2_exp_time_dec)[20:],2)
        cam2_exp_time_ms = cam2_exp_time_base_no*0.02
        self.frame2 = camcapture2.getFrame()
        self.frame2.announceFrame()
        camcapture2.startCapture()
        camcapture2.runFeatureCommand("AcquisitionStart")

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

        self.positions = [0,0,0]
        self.camera_positions = [0,0,0]
        self.camera_offsets = [0,0,0]
        self.axis_positions = [0,0,0,0]

        self.tip_positions = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]


    def run(self):  # method which runs the thread
        print('Detection Thread Started')
        self.save_positions('load')
        while True:
            if time.clock() - self.time_fps_l >= 1.0/self.set_fps:
                #Calculate frame rate
                self.time_fps = time.clock()
                self.dt_fps = (self.time_fps - self.time_fps_l)*1000
                self.fps = 1000.0/self.dt_fps
                self.time_fps_l = self.time_fps

                #Get frames
                self.frame.queueFrameCapture()
                self.frame.waitFrameCapture(1000)
                frame_data = self.frame.getBufferByteData()
                self.frame2.queueFrameCapture()
                self.frame2.waitFrameCapture(1000)
                frame_data2 = self.frame2.getBufferByteData()

                #Convert to array
                self.n_frame = np.ndarray(buffer=frame_data, dtype=np.uint8, shape=(self.frame.height,self.frame.width))
                self.n_frame_rect = self.n_frame.copy()
                #cv2.rectangle(self.n_frame_rect,(x_min,y_min),(x_max,y_max),(255,127,127),4)
                self.n_frame2 = np.ndarray(buffer=frame_data2, dtype=np.uint8, shape=(self.frame2.height,self.frame2.width))
                self.n_frame_rect2 = self.n_frame2.copy()
                #cv2.rectangle(self.n_frame_rect2,(x_min,y_min),(x_max,y_max),(255,127,127),4)

                #Detect beads
                if self.detect_flag:
                    #camera 1
                    self.n_frame_beads,xr,yr,self.width1,self.height1,self.nbead1,self.centerx1,self.centery1,self.round1 = self.detect_beads(self.n_frame,
                                                                          self.thresh1_min,self.thresh1_max,
                                                                          self.circ_min,self.circ_max,
                                                                          self.area_min,self.area_max)
                    #if self.nbead1 > 0: # At least one bead is detected
                    self.cn_frame = self.crop(self.n_frame,xr,yr,self.width1,self.height1,2) # cropped frame with the bead // cropped numpy
                    self.cn_frame_sobel = self.sobel_edge(self.cn_frame)

                    mean, stdev = cv2.meanStdDev(self.cn_frame_sobel)
                    self.focus1 = stdev[0][0]/mean[0][0]
                    #camera 2
                    self.n_frame_beads2,xr2,yr2,self.width2,self.height2,self.nbead2,self.centerx2,self.centery2,self.round2 = self.detect_beads(self.n_frame2,
                                                                          self.thresh2_min,self.thresh2_max,
                                                                          self.circ_min,self.circ_max,
                                                                          self.area_min,self.area_max)
                    #if self.nbead2 > 0: # At least one bead is detected
                    self.cn_frame2 = self.crop(self.n_frame2,xr2,yr2,self.width2,self.height2,2) # cropped frame with the bead // cropped numpy
                    self.cn_frame_sobel2 = self.sobel_edge(self.cn_frame2)

                    mean, stdev = cv2.meanStdDev(self.cn_frame_sobel2)
                    self.focus2 = stdev[0][0]/mean[0][0]

                #Update bead positions
                self.calculate_positions()
                self.update_UI()
                self.time_refresh = time.clock()

    def update_UI(self):
        #update UI with values for various parameters
        for key,val in zip(['fps','dt_fps','max_fps'],
                           [self.fps,self.dt_fps,self.max_fps]):
            self.bead_update_trigger.emit(key,val)
        for key,val in zip(['focus1','round1','nbead1','centerx1','centery1','width1','height1'],
                           [self.focus1,self.round1,self.nbead1,self.centerx1,self.centery1,self.width1,self.height1]):
            self.bead_update_trigger.emit(key,val)
        for key,val in zip(['focus2','round2','nbead2','centerx2','centery2','width2','height2'],
                           [self.focus2,self.round2,self.nbead2,self.centerx2,self.centery2,self.width2,self.height2]):
            self.bead_update_trigger.emit(key,val)

        self.bead_position_update_trigger.emit(self.positions,self.camera_positions,self.tip_positions,self.axis_positions)

        self.focus_update_trigger.emit(self.focus1,self.focus2)

        #update UI with images of beads
        #self.display_frame_update_trigger.emit(1,self.n_frame_rect,self.n_frame,self.nbead1)
        #self.display_frame_update_trigger.emit(2,self.n_frame_rect2,self.n_frame2,self.nbead2)
        self.display_frame_update_trigger.emit(1,self.n_frame_rect,self.nbead1)
        self.display_frame_update_trigger.emit(2,self.n_frame_rect2,self.nbead2)
        # if self.nbead1 == 0:
        #     self.display_update_trigger.emit(1,self.n_frame_rect,self.n_frame,self.nbead1)
        # else:
        #     self.display_frame_update_trigger_bead.emit(1,self.n_frame_rect,self.n_frame,self.nbead1,self.n_frame_beads,self.cn_frame,self.cn_frame_sobel)
        #
        # if self.nbead2 == 0:
        #     self.display_update_trigger.emit(2,self.n_frame_rect2,self.n_frame2,self.nbead2)
        # else:
        #     self.display_frame_update_trigger_bead.emit(2,self.n_frame_rect2,self.n_frame2,self.nbead2,self.n_frame_beads2,self.cn_frame2,self.cn_frame_sobel2)




    def value_changed(self,value,ref_text):
        value_str = 'self.'+ref_text
        exec(value_str+' = value')
        print 'value changed',value,ref_text

    def xaxis_changed(self,value):
        self.axis_positions[0] = value

    def yaxis_changed(self,value):
        self.axis_positions[1] = - value

    def zaxis_changed(self,value):
        self.axis_positions[2] = value

    def y2axis_changed(self,value):
        self.axis_positions[3] = value
        
    def calculate_positions(self):
        for i in range(3):
            self.camera_positions[i] = self.axis_positions[i] - self.camera_offsets[i]

        #Average camera bead locations
        centerx = (self.centerx1+self.centerx2)/2
        #flip y axis
        centery = self.resy - (self.centery1+self.centery2)/2

        self.positions[0] = centerx*self.resolution - self.offsetx + self.camera_positions[0]
        self.positions[1] = centery*self.resolution - self.offsety + self.camera_positions[1]
        self.positions[2] = self.camera_positions[2]

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

    def save_img(self,filepath):
        cv2.imwrite(filepath,self.n_frame)
        print 'image saved: ' + filepath
        return

    def zero_cam(self,i):
        self.camera_offsets[i] = self.axis_positions[i]
        self.save_positions()
        print 'zero pos {0}'.format(i)

    def tip_pos(self,i):
        if i < 4:
            for j in range(3):
                self.tip_positions[i][j] = self.camera_positions[j]
                self.tip_positions[4][j] = (self.tip_positions[0][j]+self.tip_positions[1][j]+self.tip_positions[2][j]+self.tip_positions[3][j])/4
        if i == 4:
            for j in range(3):
                self.tip_positions[4][j] = (self.tip_positions[0][j]+self.tip_positions[1][j]+self.tip_positions[2][j]+self.tip_positions[3][j])/4
                self.camera_offsets[j] = self.axis_positions[j] - (self.camera_positions[j] - self.tip_positions[4][j])
            self.calculate_positions()
            for i in range(4):
                for j in range(3):
                    self.tip_positions[i][j] = self.tip_positions[i][j] - self.tip_positions[4][j]
            for j in range(3):
                self.tip_positions[4][j] = 0
        self.save_positions()
        print 'tip pos {0}: x{1} y{2} z{3}'.format(i,self.tip_positions[i][0],self.tip_positions[i][1],self.tip_positions[i][2])

    def save_positions(self, mode = 'save'):
        # file name
        f_path = os.getcwd()+'\\save\\'
        f_name = 'camera_positions'
        f_path = f_path + f_name +'.csv'
        # open file
        with open(f_path,'r+') as f:
            if mode == 'load':
                reader = csv.reader(f)
                read_list = []
                for position in reader.next():
                    read_list.append(position)
                for i in range(3):
                    self.camera_offsets[i] = float(read_list[i])

                for i in range(5):
                    read_list = []
                    for position in reader.next():
                        read_list.append(position)
                    for j in range(3):
                        self.tip_positions[i][j] = float(read_list[j])
            elif mode == 'save':
                writer = csv.writer(f)
                write_list = []
                for offset in self.camera_offsets:
                    write_list.append('{0:7.4f}'.format(offset))
                writer.writerow(write_list)
                for i in range(5):
                    write_list = []
                    for j in range(3):
                        write_list.append('{0:7.4f}'.format(self.tip_positions[i][j]))
                    writer.writerow(write_list)