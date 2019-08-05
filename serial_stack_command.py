import serial
import time

ser = serial.Serial('COM3', 9600, timeout=1)
time.sleep(5)

for i in range(1,101):
    ser.write('FRM\r\n')
    time.sleep(2)
    ser.write('DAC ' +str(int(2900-(i*10)))+'\r\n')
    time.sleep(0.1)
    ser.write('STR ' +str(1)+ '\r\n')
    time.sleep(2)

ser.close()