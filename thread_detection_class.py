import time
import numpy as np
import cv2
import cv2.cv as cv

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadDetection(QThread):
    def __init__(self,gui_):
        super(ThreadDetection, self).__init__()

        self.gui = gui_

    def run(self):  # method which runs the thread
        print('Detection Thread Started')

    def value_changed(self,value,ref_text):
        print('bead value changed: '+ref_text)

    #returns picture after thresholding
    def threshold_frame(frame,thresh_min,thresh_max):
        res, ret_frame = cv2.threshold(frame,thresh_min,thresh_max,cv2.THRESH_BINARY)
        return ret_frame

    #detects and filter beads
    def detect_beads(n_frame,thresh_min,thresh_max,circ_min,circ_max,area_min,area_max):

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
    def crop_stack(n_frame,xc,yc):

        y1 = yc-46
        y2 = yc+46

        x1 = xc-46
        x2 = xc+46

        ret_frame = np.copy(n_frame[y1:y2,x1:x2])

        return ret_frame

    #detects and filter beads for stack
    def detect_beads_stack(n_frame):

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
    def crop(n_frame,xr,yr,wr,hr,bead_slider):

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
    def sobel_edge(n_frame):
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
    def bead_focus_stack(n_frame):

        s_in_frame, xc,yc  = beads_detection_stack(n_frame)
        s_out_frame = sobel_edge(s_in_frame)

        avg, sigma = cv2.meanStdDev(s_out_frame)

        focus_param = round(sigma[0][0]/avg[0][0],3)

        return focus_param, xc, yc


    #return theoretical focus param s
    def f1_analytic(x):
        a = -502568.69217
        b = 206443.52808
        c = -28265.96318
        d = 1289.98324
        return a + b*x + c*x*x + d*x*x*x

    def f2_analytic( x):
        a = 491477.6662
        b = -201782.91117
        c = 27613.70843
        d = -1259.57454
        return a + b*x + c*x*x + d*x*x*x

    #get z offset of the bead
    def bead_z_evaluate(f1, f2):
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
    def follow_bead(x_av):
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

    def follow_bead_new(f_1_over_f_2):
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

    def delta_z_bead(x_av):
        x_1 = 7.25995
        return x_av-x_1

