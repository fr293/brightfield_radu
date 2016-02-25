import random
import time

from PySide.QtCore import *
from PySide.QtGui import *

class ThreadPowerSupply(QThread):
    def __init__(self,ser):
        super(ThreadPowerSupply, self).__init__()
        self.serial = ser

    def run(self):  # method which runs the thread
                    # it will be started from main thread
        print('ps thread start')
        # @@@@@@@@@ initialisation parameters @@@@@@@@@@@
        self.done_ps = False   # controls the exit from while loop and
                               # termination of the thread
        self.power_is_set_on = False  # if power is ON, True
        self.power_is_set_off = False

        self.error_1_ps_1_status = False
        self.error_2_ps_1_status = False
        self.error_1_ps_2_status = False
        self.error_2_ps_2_status = False

        self.send_cmd_ps_status = False
        self.send_cmd_ps_index = 1
        self.send_cmd_ps_text = '*IDN?'

        self.current_value = [0.0,0.0,0.0,0.0]

        self.current_changed = [True, True, True, True]

        self.current_refresh = [1,1,1,1]

        time_old_temp = time.clock()
        time_old_update_I = time.clock()
        time_old_psu_1 = time.clock()
        time_old_psu_2 = time.clock()
        d_time = 0.090  # update time for power supply
        channel = 1 # coil

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        while (not self.done_ps): # loop for getting data from actuator
            time.sleep(0.02)
            kk = random.uniform(0,4)  # the sequence of change the current to be random not 1,2,3,4 always
                                      # there are 24 possible permutations; too many; just 4

            #out_flag_ps = self.do_and_reply('Read_flag\r\n') # get status of arduino
            #if out_flag_ps =='0':
            #    out_flag_ps_str = 'Ready Temp OK'
            #elif out_flag_ps =='1':
            #    out_flag_ps_str = 'Error Temp HIGH'
            #else:
            #    out_flag_ps_str ='Error serial link'

            #self.emit(SIGNAL("flag_ps_send(QString)"),out_flag_ps_str) # the threadAct emits a signal with a parameter
                                                                      # to be received by the main thread

            #if self.power_reset:
            #    self.do_and_nowait('Set_flag 0\r\n')
            #    self.power_reset = False
# FIRST VERSION IMPLEMENTATION
            #if (time.clock()-time_old_update_I)>1.0:  # in case current value was not received by PSU
            #    self.current_changed[0] = True
            #    self.current_changed[1] = True
            #    self.current_changed[2] = True
            #    self.current_changed[3] = True
            #    time_old_update_I = time.clock()
# SECOND VERSION IMPLEMENTATION
            if ((time.clock()-time_old_update_I)>1.0):
                if  ((self.current_refresh[0]==2) and (time.clock()-time_old_psu_1)>d_time ):  # in case current value was not received by PSU
                    curr_1_str = str(self.current_value[0])
                    self.do_and_nowait('PW 1 '+curr_1_str+'\r\n')
                    self.current_refresh[0] = self.current_refresh[0] +1
                    time_old_psu_1 = time.clock()

                if  ((self.current_refresh[1]==2) and (time.clock()-time_old_psu_1)>d_time ):  # in case current value was not received by PSU
                    curr_2_str = str(self.current_value[1])
                    self.do_and_nowait('PW 2 '+curr_2_str+'\r\n')
                    self.current_refresh[1] = self.current_refresh[1] +1
                    time_old_psu_1 = time.clock()

                if ((self.current_refresh[2]==2) and (time.clock()-time_old_psu_2)>d_time ):  # in case current value was not received by PSU
                    curr_3_str = str(self.current_value[2])
                    self.do_and_nowait('PW 3 '+curr_3_str+'\r\n')
                    self.current_refresh[2] = self.current_refresh[2] +1
                    time_old_psu_2 = time.clock()

                if ((self.current_refresh[3]==2)  and (time.clock()-time_old_psu_2)>d_time ):  # in case current value was not received by PSU
                    curr_4_str = str(self.current_value[3])
                    self.do_and_nowait('PW 4 '+curr_4_str+'\r\n')
                    self.current_refresh[3] = self.current_refresh[3] +1
                    time_old_psu_2 = time.clock()



            if (self.power_is_set_on and ((time.clock()-time_old_psu_1)>d_time) and \
                    ((time.clock()-time_old_psu_2)>d_time)): # and out_flag_ps =='0':
                self.do_and_nowait('P_ON\r\n')
                self.power_is_set_on = False
                time_old_psu_1 = time.clock()
                time_old_psu_2 = time.clock()


            if (self.power_is_set_off and ((time.clock()-time_old_psu_1)>d_time) and \
                    ((time.clock()-time_old_psu_2)>d_time)): # and out_flag_ps =='0':
                self.do_and_nowait('P_OFF\r\n')
                self.power_is_set_off = False
                time_old_psu_1 = time.clock()
                time_old_psu_2 = time.clock()

            if (self.error_1_ps_1_status and ((time.clock()-time_old_psu_1)>d_time) ):
                self.do_and_reply_ps_error('CMD1 EER?\r\n')
                self.error_1_ps_1_status = False
                time_old_psu_1 = time.clock()

            if (self.error_2_ps_1_status and ((time.clock()-time_old_psu_1)>d_time) ):
                self.do_and_reply_ps_error('CMD1 *ESR?\r\n')
                self.error_2_ps_1_status = False
                time_old_psu_1 = time.clock()

            if (self.error_1_ps_2_status and ((time.clock()-time_old_psu_2)>d_time) ):
                self.do_and_reply_ps_error('CMD2 EER?\r\n')
                self.error_1_ps_2_status = False
                time_old_psu_2 = time.clock()

            if (self.error_2_ps_2_status and ((time.clock()-time_old_psu_2)>d_time) ):
                self.do_and_reply_ps_error('CMD2 *ESR?\r\n')
                self.error_2_ps_2_status = False
                time_old_psu_2 = time.clock()

            if (self.send_cmd_ps_status):
                if ((self.send_cmd_ps_index == 1) and ((time.clock()-time_old_psu_1)>d_time)):
                    self.do_and_reply_ps_error('CMD1 '+ str(self.send_cmd_ps_text) + '\r\n')
                    self.send_cmd_ps_status = False
                    time_old_psu_1 = time.clock()

                if ((self.send_cmd_ps_index == 2) and ((time.clock()-time_old_psu_2)>d_time)):
                    temporal = 'CMD2 '+ str(self.send_cmd_ps_text) + '\r\n'
                    #print temporal
                    self.do_and_reply_ps_error(temporal)
                    self.send_cmd_ps_status = False
                    time_old_psu_2 = time.clock()




            if (kk <1.0):
                if (self.current_changed[0] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.current_value[0])
                    self.do_and_nowait('PW 1 '+curr_1_str+'\r\n')
                    self.current_changed[0] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[0] = self.current_refresh[0] +1
                    time_old_psu_1 = time.clock()
                if (self.current_changed[2] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.current_value[2])
                    self.do_and_nowait('PW 3 '+curr_3_str+'\r\n')
                    self.current_changed[2] = False
                    self.current_refresh[2] = self.current_refresh[2] +1
                    time_old_update_I = time.clock()
                    time_old_psu_2 = time.clock()
                if (self.current_changed[1] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.current_value[1])
                    self.do_and_nowait('PW 2 '+curr_2_str+'\r\n')
                    self.current_changed[1] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[1] = self.current_refresh[1] +1
                    time_old_psu_1 = time.clock()
                if (self.current_changed[3] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.current_value[3])
                    self.do_and_nowait('PW 4 '+curr_4_str+'\r\n')
                    self.current_changed[3] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[3] = self.current_refresh[3] +1
                    time_old_psu_2 = time.clock()

            elif ((kk <2.0) and (kk >= 1.0)):
                if (self.current_changed[0] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.current_value[0])
                    self.do_and_nowait('PW 1 '+curr_1_str+'\r\n')
                    self.current_changed[0] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[0] = self.current_refresh[0] +1
                    time_old_psu_1 = time.clock()
                if (self.current_changed[2] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.current_value[2])
                    self.do_and_nowait('PW 3 '+curr_3_str+'\r\n')
                    self.current_changed[2] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[2] = self.current_refresh[2] +1
                    time_old_psu_2 = time.clock()
                if (self.current_changed[3] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.current_value[3])
                    self.do_and_nowait('PW 4 '+curr_4_str+'\r\n')
                    self.current_changed[3] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[3] = self.current_refresh[3] +1
                    time_old_psu_2 = time.clock()
                if (self.current_changed[1] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.current_value[1])
                    self.do_and_nowait('PW 2 '+curr_2_str+'\r\n')
                    self.current_changed[1] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[1] = self.current_refresh[1] +1
                    time_old_psu_1 = time.clock()

            elif ((kk <3.0) and (kk >= 2.0)):
                if (self.current_changed[2] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.current_value[2])
                    self.do_and_nowait('PW 3 '+curr_3_str+'\r\n')
                    self.current_changed[2] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[2] = self.current_refresh[2] +1
                    time_old_psu_2 = time.clock()
                if (self.current_changed[0] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.current_value[0])
                    self.do_and_nowait('PW 1 '+curr_1_str+'\r\n')
                    self.current_changed[0] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[0] = self.current_refresh[0] +1
                    time_old_psu_1 = time.clock()
                if (self.current_changed[1] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.current_value[1])
                    self.do_and_nowait('PW 2 '+curr_2_str+'\r\n')
                    self.current_changed[1] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[1] = self.current_refresh[1] +1
                    time_old_psu_1 = time.clock()
                if (self.current_changed[3] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.current_value[3])
                    self.do_and_nowait('PW 4 '+curr_4_str+'\r\n')
                    self.current_changed[3] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[3] = self.current_refresh[3] +1
                    time_old_psu_2 = time.clock()

            else:
                if (self.current_changed[2] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_3_str = str(self.current_value[2])
                    self.do_and_nowait('PW 3 '+curr_3_str+'\r\n')
                    self.current_changed[2] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[2] = self.current_refresh[2] +1
                    time_old_psu_2 = time.clock()
                if (self.current_changed[0] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_1_str = str(self.current_value[0])
                    self.do_and_nowait('PW 1 '+curr_1_str+'\r\n')
                    self.current_changed[0] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[0] = self.current_refresh[0] +1
                    time_old_psu_1 = time.clock()
                if (self.current_changed[3] and (time.clock() - time_old_psu_2) > d_time):  # True
                    curr_4_str = str(self.current_value[3])
                    self.do_and_nowait('PW 4 '+curr_4_str+'\r\n')
                    self.current_changed[3] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[3] = self.current_refresh[3] +1
                    time_old_psu_2 = time.clock()
                if (self.current_changed[1] and (time.clock() - time_old_psu_1) > d_time):  # True
                    curr_2_str = str(self.current_value[1])
                    self.do_and_nowait('PW 2 '+curr_2_str+'\r\n')
                    self.current_changed[1] = False
                    time_old_update_I = time.clock()
                    self.current_refresh[1] = self.current_refresh[1] +1
                    time_old_psu_1 = time.clock()


            if (time.clock()-time_old_temp)>1.0: # 2 sensors was 2.0
                if channel == 1:
                    temp_thermistor = self.do_and_reply_ps('T1\r\n')
                    self.emit(SIGNAL("temp_C_send(QString)"),temp_thermistor)
                    time_old_temp = time.clock()
                    channel = 2
                elif channel == 2:
                    temp_thermistor2 = self.do_and_reply_ps('T2\r\n')
                    self.emit(SIGNAL("temp_C_send2(QString)"),temp_thermistor2)
                    time_old_temp = time.clock()
                    channel = 3
                elif channel == 3:
                    temp_thermistor3 = self.do_and_reply_ps('T3\r\n')
                    self.emit(SIGNAL("temp_C_send3(QString)"),temp_thermistor3)
                    time_old_temp = time.clock()
                    channel = 1
                #elif channel == 4:
                #    temp_thermistor4 = self.do_and_reply_ps('T4\r\n')
                #    self.emit(SIGNAL("temp_C_send4(QString)"),temp_thermistor4)
                #    time_old_temp = time.clock()
                #    channel = 1
                else:
                    print 'error channel'
                #print channel


        self.do_and_nowait('P_OFF\r\n')
        #self.emit(SIGNAL("flag_ps_send(QString)"),' ')
        self.do_and_nowait('Set_Local\r\n')
        print "Done with Power Supply thread"      # to be converted into a comment

    def do_and_reply_ps(self, to_do):  # method - to get answer from controller
        self.serial.write(to_do)            # write to serial a command
        time.sleep(0.02)
        reply_1 = self.serial.readline()    # read from serial the answer
        reply_2 = reply_1[:4]     # remove \r\n from the answer 20.5

        no_ch_buffer = self.serial.inWaiting()
        #print 'ch_ps ', no_ch_buffer

        if (no_ch_buffer != 0):
            reply_1 = self.serial.readline()    # read from serial the answer
            reply_2 = reply_1[:4]     # remove \r\n from the answer 20.5
            if (self.serial.inWaiting() != 0):
                reply_1 = self.serial.readline()    # read from serial the answer
                reply_2 = reply_1[:4]     # remove \r\n from the answer 20.5
                index_serial = 0
                while (self.serial.inWaiting() != 0) and (index_serial<5):
                    reply_1 = self.serial.readline()    # read from serial the answer
                    reply_2 = reply_1[:4]     # remove \r\n from the answer 20.5
                    index_serial = index_serial + index_serial



        return reply_2

    def do_and_nowait(self,to_do):  # method - no answer expected from actuator
        self.serial.write(to_do)
        return

    def do_and_reply_ps_error(self, to_do):  # method - to get answer from controller
        #print to_do
        self.serial.write(to_do)            # write to serial a command
        time.sleep(0.1)
        reply_1 = self.serial.readline()    # read from serial the answer
        print to_do[:-2] + ' ' + reply_1[:-1]

        no_ch_buffer = self.serial.inWaiting()
        #print 'ch_ps ', no_ch_buffer

        if (no_ch_buffer != 0):
            reply_1 = self.serial.readline()    # read from serial the answer
            print to_do[:-2] +' ' + reply_1[:-1]
            if (self.serial.inWaiting() != 0):
                reply_1 = self.serial.readline()    # read from serial the answer
                print to_do[:-2] +' ' + reply_1[:-1]
                index_serial = 0
                while (self.serial.inWaiting() != 0) and (index_serial<5):
                    reply_1 = self.serial.readline()    # read from serial the answer
                    print to_do[:-2] + ' ' + reply_1[:-1]
                    index_serial = index_serial + index_serial
        return