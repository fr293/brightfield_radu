import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadDisplay(QThread):
    def __init__(self,gui_):
        super(ThreadDisplay, self).__init__()
        self.gui = gui_
        self.bead_zoom = 1

    def run(self):  # method which runs the thread
        print('Display Thread Started')
        #while(True):

        self.paintEvent()

    def paintEvent(self):
        self.qp = QPainter()

        self.qp.begin(self.gui)
        self.drawFrames(self.qp)
        self.qp.end()

        self.gui.update()

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


        frame.queueFrameCapture()
        frame_2.queueFrameCapture()
        frame.waitFrameCapture(1000)


        #tt = datetime.datetime.now()
        #print 't_b ', str(getattr(tt,'second'))+'.'+str(getattr(tt,'microsecond'))

        frame_data = frame.getBufferByteData()

        frame_2.waitFrameCapture(1000)
        frame_data_2 = frame_2.getBufferByteData()

        self.time_calib = time.clock()

        n_frame = np.ndarray(buffer=frame_data, dtype=np.uint8, shape=(frame.height,frame.width))
        n_frame_2 = np.ndarray(buffer=frame_data_2, dtype=np.uint8, shape=(frame_2.height,frame_2.width))
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

        if (self.index_pct_fps == 20):
            #print 19 / (time.clock()-self.time_fps_old)
            self.measured_fps = 19.0 / (time.clock()-self.time_fps_old)
            self.text_changed_measured_fps()
            self.index_pct_fps = 0

        #print self.index_pct_fps

        n_frame_rect = n_frame.copy()
        #cv2.rectangle(n_frame_rect,(700,500),(1700,1500),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x_min,y_min),(x_max,y_max),(255,127,127),4)

        cv2.rectangle(n_frame_rect,(x11,y11),(x12,y12),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x21,y21),(x22,y22),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x31,y31),(x32,y32),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x41,y41),(x42,y42),(255,127,127),4)
        cv2.rectangle(n_frame_rect,(x51,y51),(x52,y52),(255,127,127),4)

        if QAbstractButton.isChecked(self.checkbox_grid):
            cv2.line(n_frame_rect,(x_mid,0),(x_mid,self.size_grid),(255,127,127),4)
            cv2.line(n_frame_rect,(x_mid,y_rez),(x_mid,y_rez-self.size_grid),(255,127,127),4)
            cv2.line(n_frame_rect,(0,y_mid),(self.size_grid,y_mid),(255,127,127),4)
            cv2.line(n_frame_rect,(x_rez,y_mid),(x_rez-self.size_grid,y_mid),(255,127,127),4)

        if QAbstractButton.isChecked(self.checkbox_spim_box):
            cv2.rectangle(n_frame_rect,(self.spim_x_min,self.spim_y_min),
                                       (self.spim_x_max,self.spim_y_max),(255,127,127),5)

        if QAbstractButton.isChecked(self.checkbox_ref_bead):
            cv2.line(n_frame_rect,(1495,940),(1495,1000),(255,127,127),4)
            cv2.line(n_frame_rect,(1465,970),(1525,970),(255,127,127),4)


        q_frame = NumPyQImage(n_frame_rect)                 # Qt frame
        q_frame_2=NumPyQImage(n_frame_2)
        self.n_frame_cam1 = n_frame

        if QAbstractButton.isChecked(self.checkbox_m) and (time.clock()-self.time_old_mov)>2.0:
            self.index_m = self.index_m +1
            path_file_m = os.getcwd()+'\\movies\\'
            cv2.imwrite(path_file_m+str(self.index_m)+".jpeg",cv2.resize(n_frame,None,fx=0.5, fy=0.5,interpolation = cv2.INTER_LINEAR))
            self.time_old_mov = time.clock()

        if (self.save_pict_exp==True):
            self.index_exp = self.index_exp +1
            #path_file_exp = os.getcwd()+'\\stack\\'
            cv2.imwrite(self.th_experiments.folder_path_c1+'cam1_'+str(self.index_exp)+".jpeg",
                        cv2.resize(n_frame,None,fx=1.0, fy=1.0,interpolation = cv2.INTER_LINEAR))
            cv2.imwrite(self.th_experiments.folder_path_c2+'cam2_'+str(self.index_exp)+".jpeg",
                        cv2.resize(n_frame_2,None,fx=1.0, fy=1.0,interpolation = cv2.INTER_LINEAR))
            ffocus, xxc, yyc = bead_focus_stack(n_frame)
            #print ffocus, xxc, yyc

            ffile_name = open(self.th_experiments.folder_path_c1[:-6]+'\\focus_stack.dat', 'a')
            ffile_name.write(str(self.th_experiments.val_exper_real_time_z)+','+str(ffocus)+','+str(xxc)+','+str(yyc)+'\n')
            ffile_name.close()


            self.save_pict_exp=False

        if (self.seq_time_laps_run == True):
            if ((time.clock() - self.time_seq_tlaps) >= self.period_seq_tlaps):
                if (self.config_curr == 1):
                    self.butt_pow_DOWN_Changed()
                elif (self.config_curr == 4):
                    self.butt_pow_UP_Changed()
                else:
                    print 'no current changed'

                self.seq_tlaps_increment_file_name()
                self.butt_random_time_laps_start_Changed()
                self.time_seq_tlaps = time.clock()


        if (self.time_laps_run_flag == True):

            if (((time.clock()-self.t_init_laps_PS)>=(self.t1_value_laps_PS-0.5)) and (self.flag_t1_laps_PS ==True)):
                self.butt_pow_start_Changed()
                self.flag_t1_laps_PS = False
                self.flag_t2_laps_PS = True

            if (((time.clock()-self.t_init_laps_PS)>=(self.t1_value_laps_PS+self.t2_value_laps_PS-0.5))
                and (self.flag_t2_laps_PS ==True)):
                self.butt_pow_stop_Changed()
                self.flag_t2_laps_PS = False


            if (self.index_time_laps < self.ctrl_random_timelaps_frame_no.value()):
                if (time.clock() - self.time_old_time_laps > self.ctrl_random_timelaps_frame_time.value()):
                    self.index_time_laps = self.index_time_laps + 1
                    cv2.imwrite(self.folder_path_time_laps_c1+'cam1_'+str(self.index_time_laps+100)+".tiff",
                        cv2.resize(n_frame,None,fx=1.0, fy=1.0,interpolation = cv2.INTER_LINEAR))
                    cv2.imwrite(self.folder_path_time_laps_c2+'cam2_'+str(self.index_time_laps+100)+".tiff",
                        cv2.resize(n_frame_2,None,fx=1.0, fy=1.0,interpolation = cv2.INTER_LINEAR))
                    self.lab_random_timelaps_frame_index.setText(str(self.index_time_laps))
                    #print self.index_time_laps
                    self.time_old_time_laps = time.clock()
            else:
                self.butt_random_time_laps_stop_Changed()





        if QAbstractButton.isChecked(self.checkbox_p):
            sq_frame = q_frame.scaled(q_frame.width()/small_1,q_frame.height()/small_1,) # resize # small Qt frame
            #qp.drawImage(QPoint(20, 20), sq_frame)        # Display the frame
            sq_frame_2 = q_frame_2.scaled(q_frame_2.width()/small_1,q_frame_2.height()/small_1,)
            qp.drawImage(QPoint(20, 410), sq_frame_2)
            qp.drawImage(QPoint(20, 20), sq_frame)
        else:
            sq_frame = q_frame.scaled(q_frame.width()/small,q_frame.height()/small,) # resize # small Qt frame
            #qp.drawImage(QPoint(20, 20), sq_frame)        # Display the frame
            sq_frame_2 = q_frame_2.scaled(q_frame_2.width()/small,q_frame_2.height()/small,)
            qp.drawImage(QPoint(20, 410), sq_frame_2)
            qp.drawImage(QPoint(20, 20), sq_frame)


        timp = time.time()
        #print time.clock()#-self.time_old
        #print timp ,timp.second #, #timp.microsecond

        if ((self.pulse_current_bool ==True) and (time.clock()-self.time_pulse_current >0.6)):
            self.butt_pow_pulse.setEnabled(True)
            self.pulse_current_bool = False
            self.butt_pow_stop_Changed()


        if QAbstractButton.isChecked(self.checkbox_diff):
            n_frame_diff = cv2.absdiff(n_frame, n_frame_2)
            q_frame_diff = NumPyQImage(n_frame_diff)
            sq_frame_diff = q_frame_diff.scaled(q_frame_diff.width()/7,q_frame_diff.height()/7,) # resize # small Qt frame
            qp.drawImage(QPoint(470, 570), sq_frame_diff)        # Display the frame




        if QAbstractButton.isChecked(self.checkbox_XZ_section):
            n_frame_xz = np.zeros((260,260),np.uint8)
            n_frame_xz[:] = (255)
            cv2.line(n_frame_xz,(130,126),(130,134),(0,0,0),1)
            cv2.line(n_frame_xz,(126,130),(134,130),(0,0,0),1)
            cv2.rectangle(n_frame_xz,(30,10),(230,250),(0,0,0),1)
            cv2.line(n_frame_xz,(170,99),(170,103),(0,0,0),1)
            cv2.line(n_frame_xz,(168,101),(172,101),(0,0,0),1)

            cv2.line(n_frame_xz,(170-61,101-64),(170-89,101-44),(0,0,0),1)
            cv2.line(n_frame_xz,(170-89,101-44),(170+61,101+64),(0,0,0),1)
            cv2.line(n_frame_xz,(170+61,101+64),(170+89,101+44),(0,0,0),1)
            cv2.line(n_frame_xz,(170+89,101+44),(170-61,101-64),(0,0,0),1)




            self.scaling_fact = 2.5
            delta_x_pix_cent = (self.origin_x - self.center_x)/self.conv_um_pix
            delta_x_center_xz = int(round(delta_x_pix_cent/self.scaling_fact,0))

            delta_z_mm_cent = (self.z_c_oil - self.val_coord_z_bead) *1000
            delta_z_center_xz = int(round(delta_z_mm_cent/self.scaling_fact,0))

            z_limit_min = 4.080
            z_limit_max = 4.170

            delta_z_mm_lim_min = (self.z_c_oil - z_limit_min) *1000
            delta_z_center_lim_min_xz = int(round(delta_z_mm_lim_min/self.scaling_fact,0))

            delta_z_mm_lim_max = (self.z_c_oil - z_limit_max) *1000
            delta_z_center_lim_max_xz = int(round(delta_z_mm_lim_max/self.scaling_fact,0))

            cv2.line(n_frame_xz,(1,130+delta_z_center_lim_min_xz),(259,130+delta_z_center_lim_min_xz),(0,0,0),1)
            cv2.line(n_frame_xz,(1,130+delta_z_center_lim_max_xz),(259,130+delta_z_center_lim_max_xz),(0,0,0),1)


            if abs(delta_z_center_xz)> 127:
                if delta_z_center_xz> 0:
                    delta_z_center_xz = 127
                else:
                    delta_z_center_xz = -127





            cv2.circle(n_frame_xz,(130-delta_x_center_xz,130+delta_z_center_xz),2,(0,0,0),2)

            q_frame_xz = NumPyQImage(n_frame_xz) # convert to QImage
            qp.drawImage(QPoint(470, 630), q_frame_xz)





        if QAbstractButton.isChecked(self.checkbox_t): # Show threshold is selected
            n_frame_thresh = NumThres(n_frame,self.threshMin,self.threshMax)
            q_frame_thresh = NumPyQImage(n_frame_thresh) # convert to QImage
            sq_frame_thresh = q_frame_thresh.scaled(q_frame_thresh.width()/small,q_frame_thresh.height()/small,) # resize
            qp.drawImage(QPoint(455, 20), sq_frame_thresh) # Display the frame

            n_frame_thresh_2 = NumThres(n_frame_2,self.threshMin_2,self.threshMax_2)
            q_frame_thresh_2 = NumPyQImage(n_frame_thresh_2) # convert to QImage
            sq_frame_thresh_2 = q_frame_thresh_2.scaled(q_frame_thresh_2.width()/small,q_frame_thresh_2.height()/small,) # resize
            qp.drawImage(QPoint(455, 410), sq_frame_thresh_2) # Display the frame


        if QAbstractButton.isChecked(self.checkbox_b): # Detect beads is selected
            n_frame_beads,xr,yr,wr,hr, no_beads, xc,yc, c_factor = beads_detection(n_frame,
                                                                  self.threshMin,self.threshMax,
                                                                  self.c_factor_min,self.c_factor_max,
                                                                  self.area_factor_min,self.area_factor_max)
            self.number_beads = no_beads
            self.text_changed_bead()

            n_frame_beads_2,xr_2,yr_2,wr_2,hr_2, no_beads_2, xc_2,yc_2, c_factor_2 = beads_detection(n_frame_2,
                                                                  self.threshMin_2,self.threshMax_2,
                                                                  self.c_factor_min,self.c_factor_max,
                                                                  self.area_factor_min,self.area_factor_max)
            self.number_beads_2 = no_beads_2
            self.text_changed_bead_2()

            if no_beads > 0: # At least one bead is detected

                q_frame_beads = NumPyQImage(n_frame_beads)   # convert to QImage
                sq_frame_beads = q_frame_beads.scaled(q_frame_beads.width()/small,q_frame_beads.height()/small,) # resize
                qp.drawImage(QPoint(620, 20), sq_frame_beads)  # Display the frame

                #w_r = wr
                #h_r = hr

                cn_frame = crop(n_frame,xr,yr,wr,hr,slider_val) # croped frame with the bead // croped numpy
                cq_frame = NumPyQImage(cn_frame) # convert to QImage
                scq_frame = cq_frame.scaled(cq_frame.width()/slider_val, cq_frame.height()/slider_val,)
                qp.drawImage(QPoint(455, 145), scq_frame)  # Display the frame

                #cv2.imwrite(str(timp)+".jpeg",cn_frame)
                #imagefile=QImageWriter()
                #imagefile.setFileName(str(timp)+".jpeg")
                #imagefile.setFormat("jpeg")
                #imagefile.write(cq_frame)

                cn_frame_sobel = sobel_edge(cn_frame)
                cq_frame_sobel = NumPyQImage(cn_frame_sobel) # convert to QImage
                scq_frame_sobel = cq_frame_sobel.scaled(cq_frame_sobel.width()/slider_val, cq_frame_sobel.height()/slider_val,)
                qp.drawImage(QPoint(620, 145), scq_frame_sobel)  # Display the frame


                mean, stdev = cv2.meanStdDev(cn_frame_sobel)
                #self.focus = round(stdev[0][0]/mean[0][0],3)

                if (QAbstractButton.isChecked(self.checkbox_demag_avg_focus_RT)):
                    self.storage_focus_1_RT[self.index_focus_avg_1_RT] = round(stdev[0][0]/mean[0][0],3)
                    self.index_focus_avg_1_RT = self.index_focus_avg_1_RT + 1
                    if (self.index_focus_avg_1_RT > (self.avg_focus_no_frames-1)):
                        self.index_focus_avg_1_RT = 0

                    self.focus = round(np.average(self.storage_focus_1_RT[:self.avg_focus_no_frames]),3)

                else:
                    self.focus = round(stdev[0][0]/mean[0][0],3)

                self.text_changed_focus()


                self.storage_focus1[self.index_focus_avg] = self.focus
                self.index_focus_avg = self.index_focus_avg +1
                if (self.index_focus_avg > (self.size_focus_avg-1)):
                    self.index_focus_avg = 0

                self.center_x = xc
                self.center_y = yc
                self.text_changed_x_y()

                self.width = wr
                self.height = hr
                self.text_changed_w_h()

                #print type(self.number_beads+0.0)
                self.round_factor = round(c_factor,2)
                self.text_changed_round()
                #print 'out10'
                if QAbstractButton.isEnabled(self.butt_ard_stop): # PWS can be controlled
                    #print time.clock()-self.time_old_ard
                    if QAbstractButton.isChecked(self.checkbox_center) and (time.clock()-self.time_old_ard)>0.5:
                        if ((xc >x_min and xc<x_max) and (yc >y_min and yc<y_max)):
                            if (xc - x_mid) >  10:
                                self.butt_pow_RL_Changed()
                                #print 'out1'
                            elif (xc - x_mid) < -10:
                                self.butt_pow_LR_Changed()
                                #print 'out2'
                            elif (yc-y_mid)> 4:
                                self.butt_pow_UP_Changed()
                                #print 'out3'
                            elif (yc-y_mid) < -4:
                                self.butt_pow_DOWN_Changed()
                                #print 'out4'
                            #elif (self.val_coord_z_bead-8.55)>0.003:
                            #    self.butt_pow_zDOWN_Changed()
                                #print 'out5'
                            else:
                                self.butt_pow_DOWN_Changed()
                                #print 'out6'
                        else:
                            self.butt_pow_zeroOFF_Changed(False)
                            #print 'out7'
                        self.time_old_ard = time.clock()

                    if QAbstractButton.isChecked(self.checkbox_write) and (time.clock()-self.time_old_ard)>0.5:
                        if ((xc >x_min and xc<x_max) and (yc >y_min and yc<y_max)):
                            if (xc - self.x_target) >  3:
                                self.butt_pow_RL_Changed()
                                #print 'out1'
                            elif (xc - self.x_target) < -3:
                                self.butt_pow_LR_Changed()
                                #print 'out2'
                            elif (yc-self.y_target)> 3:
                                self.butt_pow_UP_Changed()
                                #print 'out3'
                            elif (yc-self.y_target) < -3:
                                self.butt_pow_DOWN_Changed()
                                #print 'out4'
                            #elif (self.val_coord_z_bead-8.55)>0.003:
                            #    self.butt_pow_zDOWN_Changed()
                                #print 'out5'
                            else:
                                self.butt_pow_DOWN_Changed()
                                #print 'out6'
                        else:
                            self.butt_pow_zeroOFF_Changed(False)
                            #print 'out7'
                        self.time_old_ard = time.clock()
                        #print 'out4'

                    if QAbstractButton.isChecked(self.checkbox_random_safety):
                        if (not ((xc >x_min and xc<x_max) and (yc >y_min and yc<y_max))):
                            self.butt_random_current_zero_Changed()



            if no_beads_2 > 0: # At least one bead is detected

                q_frame_beads_2 = NumPyQImage(n_frame_beads_2)   # convert to QImage
                sq_frame_beads_2 = q_frame_beads_2.scaled(q_frame_beads_2.width()/small,q_frame_beads_2.height()/small,) # resize
                qp.drawImage(QPoint(620, 410), sq_frame_beads_2)  # Display the frame

                cn_frame_2 = crop(n_frame_2,xr_2,yr_2,wr_2,hr_2,slider_val) # cropped frame with the bead // cropped numpy
                cq_frame_2 = NumPyQImage(cn_frame_2) # convert to QImage
                scq_frame_2 = cq_frame_2.scaled(cq_frame_2.width()/slider_val, cq_frame_2.height()/slider_val,)
                qp.drawImage(QPoint(455, 535), scq_frame_2)  # Display the frame

                cn_frame_sobel_2 = sobel_edge(cn_frame_2)
                cq_frame_sobel_2 = NumPyQImage(cn_frame_sobel_2) # convert to QImage
                scq_frame_sobel_2 = cq_frame_sobel_2.scaled(cq_frame_sobel_2.width()/slider_val,
                                                            cq_frame_sobel_2.height()/slider_val,)
                qp.drawImage(QPoint(620, 535), scq_frame_sobel_2)  # Display the frame


                mean_2, stdev_2 = cv2.meanStdDev(cn_frame_sobel_2)
                #self.focus_2 = round(stdev_2[0][0]/mean_2[0][0],3)

                if (QAbstractButton.isChecked(self.checkbox_demag_avg_focus_RT)):
                    self.storage_focus_2_RT[self.index_focus_avg_2_RT] = round(stdev_2[0][0]/mean_2[0][0],3)
                    self.index_focus_avg_2_RT = self.index_focus_avg_2_RT + 1
                    if (self.index_focus_avg_2_RT > (self.avg_focus_no_frames-1)):
                        self.index_focus_avg_2_RT = 0

                    self.focus_2 = round(np.average(self.storage_focus_2_RT[:self.avg_focus_no_frames]),3)

                else:
                    self.focus_2 = round(stdev_2[0][0]/mean_2[0][0],3)

                self.text_changed_focus_2()

                self.center_x_2 = xc_2
                self.center_y_2 = yc_2
                self.text_changed_x_y_2()

                self.width_2 = wr_2
                self.height_2 = hr_2
                self.text_changed_w_h_2()

                #print type(self.number_beads+0.0)
                self.round_factor_2 = round(c_factor_2,2)
                self.text_changed_round_2()

            if no_beads >0 and no_beads_2 >0:
                self.delta_x = self.center_x-self.center_x_2
                self.delta_y = self.center_y-self.center_y_2
                self.text_changed_delta_x_y()
            else:
                self.delta_x = -9999
                self.delta_y = -9999
                self.text_changed_delta_x_y()

            #if QAbstractButton.isEnabled(self.butt_act_stop):
            if QAbstractButton.isEnabled(self.butt_act_stop):
                #if self.th_actuator.track == True:
                self.th_actuator.focus_act_1 = self.focus
                self.th_actuator.focus_act_2 = self.focus_2
                limits_f_1 = self.focus > 0.95  and self.focus < 1.5
                limits_f_2 = self.focus_2 > 0.84  and self.focus_2 < 1.37

                if self.th_actuator.track==True:
                    #if limits_f_1 and limits_f_2 and self.lab_act_sta.text()=='READY':
                    if self.lab_act_sta.text()=='READY':
                        #z_avg = bead_z_evaluate(self.focus, self.focus_2)
                        #z_delta_bead = delta_z_bead(z_avg)

                        #self.val_coord_z_bead = round(float(self.lab_act_pos.text())-z_delta_bead,4)
                        self.val_coord_z_bead =round(float(self.lab_act_pos.text()),4)
                        self.text_changed_z_bead_coord()

            if QAbstractButton.isEnabled(self.butt_exp_i_dir_stop):
                self.th_exp_dir.x_bead = xc
                self.th_exp_dir.y_bead = yc
                self.th_exp_dir.z_bead = self.val_coord_z_bead




        if self.do_plot == True:
            self.xxx.append(time.clock()-self.time_old)
            #self.yyy.append(self.focus)
            self.yyy.append(self.val_coord_z_bead)
            #self.yyy_2.append(self.focus_2)
            self.data_plot_changed()
            #self.data_plot_2_changed()

        if self.rec_calib == True:
            #self.calib_fileout_update()
            self.calib_fileout_update_new()
