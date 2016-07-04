#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <Actuator_AxisDue.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"
#include <stdlib.h>
#include <avr/dtostrf.h>

Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);

//axis(String _axisAddr,int _D0,int _D1,int _D2,int _D3,int _D4,int _D5,int _D6,int _D7,int _D8,int _clk,int _sel1,int _sel2,int _rst,int _readEnable,int _homePin,int _endPin,int _motorPort,float _encoderResolution);
const float encoderResolution = 0.05101E-3;
const int clk = 9;
axis axis1(01,38,40,42,44,46,48,50,52,clk,2,3,6,4,16,17,1,encoderResolution);
axis axis2(02,22,24,26,28,30,32,34,36,clk,2,3,5,4,14,15,2,encoderResolution);
axis axis3(03,23,25,27,29,31,33,35,37,clk,2,3,7,4,18,19,3,encoderResolution);


int nAxis = 3;

	
bool debugMode = 0;

// Serial Command
bool rxFlag = 0;
bool cmdValidFlag = 0;
bool cmdQueryFlag = 0;
bool cmdNumFlag = 0;
bool cmdOverrideFlag = 0;
char rx[50];

// Sprintf
char buf[40];
char bufFloat[20];

//SETUP SEQUENCE//
void setup() {
	Serial.begin(115200);
	Serial.println("Initialising");
	
	AFMS.begin();
	axis1.initialise();
	axis2.initialise();
	axis3.initialise();

    pinMode(clk,OUTPUT);
	// Use PWM pin to generate clock signal
	analogWrite(clk, 128);
	PWMC_ConfigureClocks(42000000 , 0, VARIANT_MCK);
    // rst off
	
	attachInterrupt(digitalPinToInterrupt(axis1.homePin),axis1HomeHandler,RISING);
	attachInterrupt(digitalPinToInterrupt(axis2.homePin),axis2HomeHandler,RISING);
	attachInterrupt(digitalPinToInterrupt(axis3.homePin),axis3HomeHandler,RISING);
	//attachInterrupt(axis1.endPin,axis1EndHandler,HIGH);
	
	Serial.println("Initialised");
}

//MAIN PROGRAM LOOP//
void loop() {
    // Read Serial Command String
    if(Serial.available() > 0){
        // Read in string
        String rxstr = Serial.readStringUntil('\r\n');
        // Convert string to char array
        rxstr.toCharArray(rx,50);
        // Remove spaces
        deblank(rx);
        
		if (debugMode){
			Serial.println(rx);
		}
		rxFlag = 1;
        // Check rx is not too long or short
        if (strlen(rx)>22){
            rxFlag = 0;
			Serial.println("Error: Command string too long");
        }
		else if (strlen(rx)<4){
            rxFlag = 0;
			Serial.println("Error: Command string too short");
        }      
    }
	
    // Interpret Command String
    int cmdAddr;
    char cmdName[3];
    double cmdNum;
    if (rxFlag == 1){
        cmdValidFlag = 1;
        
        // Get axis address
        char rxAddr[3];
        strncpy(rxAddr,rx,2);
        rxAddr[2] = '\0';
        // Check axis address is a number
        if(isdigit(rxAddr[0])&&isdigit(rxAddr[1])){
            // Convert to int
            cmdAddr = atoi(rxAddr);
            sprintf(buf,"Axis address: %02d",cmdAddr);
			if (debugMode){
            Serial.println(buf);
			}
        }
        else{
            Serial.println("Error: Axis address invalid");
            cmdValidFlag = 0;
        }
        
        // Get command name
        strncpy(cmdName,rx+2,2);
        cmdName[2] = '\0';
        // Check command name is uppercase char
        if(isupper(cmdName[0])&&isupper(cmdName[1])){
            sprintf(buf,"Command name: %s",cmdName);
			if (debugMode){
            Serial.println(buf); 
			}
        }
        else{
            Serial.println("Error: Command name invalid");
            cmdValidFlag = 0;
        }
        
        
        
        // Check if command has numeric value
        if (strlen(rx) == 4){
            cmdNumFlag = 0;
            //Serial.println("No numeric value");
        }
        // Check if command is query
        else if (rx[4] == '?'){
            if(rx[5] == '\0'){
                Serial.println("Command is query");
                cmdNumFlag = 0;
                cmdQueryFlag = 1;
            }
            else{
                Serial.println("Error: Command syntax incorrect");
                cmdValidFlag = 0;
            }
        }
        else{
            cmdNumFlag = 1;
            // Get numeric value
            char _cmdNum[18];
            strncpy(_cmdNum,rx+4,strlen(rx)-4);
            _cmdNum[strlen(rx)-4] = '\0';
            // Check if cmdNum is a valid number
			if(isdigit(_cmdNum[strlen(_cmdNum)-1])){
                cmdNum = atof(_cmdNum);
                dtostrf(cmdNum, 13, 4, bufFloat);
				if (debugMode){
					sprintf(buf, "Numeric value:%s\n", bufFloat);
					Serial.print(buf);
				}
            }
            else{
                Serial.println("Error: Numeric value invalid");
                cmdValidFlag = 0;
            }
        }
        
        rxFlag = 0;
        if(cmdValidFlag == 1){
            //Serial.println("Serial command valid");
        }
    }
    
	if (cmdAddr == 1 && axis1.cmdOverrideFlag == 1){
		cmdValidFlag = 0;
	}
	if (cmdAddr == 2 && axis2.cmdOverrideFlag == 1){
		cmdValidFlag = 0;
	}
	if (cmdAddr == 3 && axis3.cmdOverrideFlag == 1){
		cmdValidFlag = 0;
	}
	
    // Execute Command
    if (cmdValidFlag == 1){
        // Stop Motion
        if (!strcmp(cmdName,"ST")){
            Serial.println("ST: Stop motion");
        }
        // Get Current Position
        if (!strcmp(cmdName,"TP")){
            Serial.println("TP: Get current position");
			//sprintf(buf, "Axis position: %s mm; Encoder count: %ld\n", bufFloat,encoderPos);
            //sprintf(buf, "Position:%s\n", bufFloat);
            Serial.print(buf);
        }
        // Jog
        if (!strcmp(cmdName,"JG")){
            int motorSpeed = 100;
            if(cmdNumFlag == 1){
                motorSpeed = (int)cmdNum;
            }
            else{
                Serial.println("No motor speed specified: default value");
            }
			if (debugMode){
				sprintf(buf, "JG: Jog; Motor speed: %4d\n", motorSpeed);
				Serial.print(buf);
			}
			if (cmdAddr == 1){
				axis1.jog(motorSpeed);
			}
 			if (cmdAddr == 2){
				axis2.jog(motorSpeed);
			}
			if (cmdAddr == 3){
				axis3.jog(motorSpeed);
			}
        }
        // Reset
        if (!strcmp(cmdName,"RS")){
            Serial.println("RS: Reset position");
        }
        // Move Absolute
        if (!strcmp(cmdName,"PA")){
            dtostrf(cmdNum, 8, 4, bufFloat);
            sprintf(buf, "PA: Move Abslute; Position:%s\n", bufFloat);
            Serial.print(buf);
        }
        // Move Relative
        if (!strcmp(cmdName,"PR")){
            dtostrf(cmdNum, 8, 4, bufFloat);
            sprintf(buf, "PR: Move Relative; Position:%s\n", bufFloat);
            Serial.print(buf);
        }
		
        // Home
        if (!strcmp(cmdName,"HM")){
            Serial.println("HM: Home Axis");
        }
		
		// End
        if (!strcmp(cmdName,"ED")){
            Serial.println("ED: End Axis");
        }
		
		cmdValidFlag = 0;
    }
	
	readBytes();
	
	tx(axis1);
	if(nAxis>1){
		tx(axis2);
		if(nAxis>2){
			tx(axis3);
		}
	}
}


// Removes blank characters from char array
char* deblank(char *str)
{
  char *out = str, *put = str;

  for(; *str != '\0'; ++str)
  {
    if(*str != ' ')
      *put++ = *str;
  }
  *put = '\0';

  return out;
}

void tx(axis &_axis){
	sprintf(buf, "%02d%+d\n", _axis.axisAddr, _axis.getEncoderF());
	Serial.print(buf);
	if(_axis.homeFlag == 1){
		if(digitalRead(_axis.homePin)){
			sprintf(buf, "%02dHO\n", _axis.axisAddr);
			Serial.print(buf);
			_axis.jog(_axis.homeSpeed);
			_axis.homeFlag = 2;
			Serial.print('made it to homeflag2');
		}
		else{
			_axis.homeFlag = 0;
			_axis.cmdOverrideFlag = 0;
		}
	}
	else if(_axis.homeFlag == 2){
		if(digitalRead(_axis.homePin)){
			sprintf(buf, "%02dHO\n", _axis.axisAddr);
			Serial.print(buf);
			if(_axis.lastMotorSpeed!=_axis.homeSpeed||_axis.lastMotorDirection!=1){
				_axis.jog(_axis.homeSpeed);
			}
			Serial.print('waslsaldas');
		}
		else{
			_axis.jog(0);
			sprintf(buf, "%02dHD\n", _axis.axisAddr);
			Serial.print(buf);
			_axis.homeFlag = 0;
			_axis.cmdOverrideFlag = 0;
		}
	}
}

void axis1HomeHandler(){
	axis1.homeHandler();
	axis1.cmdOverrideFlag = 1;
}
void axis2HomeHandler(){
	axis2.homeHandler();
	axis2.cmdOverrideFlag = 1;
}
void axis3HomeHandler(){
	axis3.homeHandler();
	axis3.cmdOverrideFlag = 1;
}
void axis1EndHandler(){
	axis1.endHandler();
}

void readBytes(){
	int byte1[4][8];
	int byte2[4][8];
	int byte3[4][8];
	
	// Read 32-bit counter
    for (int i=0; i<4; i++){
        for (int j=7; j>=0; j--){
            byte1[i][j]=0;
			byte2[i][j]=0;
			byte3[i][j]=0;
        }
    }
    // Read Enable
    digitalWrite(axis1.readEnable, 0);
    for (int i=0; i<4; i++){
        // Byte select
        switch (i) {
            case 0: //MSB
                digitalWrite(axis1.sel1, 0);
                digitalWrite(axis1.sel2, 1);
                break;
            case 1: //2ND
                digitalWrite(axis1.sel1, 1);
                digitalWrite(axis1.sel2, 1);
                break;
            case 2: //3RD
                digitalWrite(axis1.sel1, 0);
                digitalWrite(axis1.sel2, 0);
                break;
            case 3: //LSB
                digitalWrite(axis1.sel1, 1);
                digitalWrite(axis1.sel2, 0);
                break;
        }
        delay(10);
        
        // Read in bits
        byte1[i][0]=(boolean)digitalRead(axis1.D0);
        byte1[i][1]=(boolean)digitalRead(axis1.D1);
        byte1[i][2]=(boolean)digitalRead(axis1.D2);
        byte1[i][3]=(boolean)digitalRead(axis1.D3);
        byte1[i][4]=(boolean)digitalRead(axis1.D4);
        byte1[i][5]=(boolean)digitalRead(axis1.D5);
        byte1[i][6]=(boolean)digitalRead(axis1.D6);
        byte1[i][7]=(boolean)digitalRead(axis1.D7);
		
		byte2[i][0]=(boolean)digitalRead(axis2.D0);
        byte2[i][1]=(boolean)digitalRead(axis2.D1);
        byte2[i][2]=(boolean)digitalRead(axis2.D2);
        byte2[i][3]=(boolean)digitalRead(axis2.D3);
        byte2[i][4]=(boolean)digitalRead(axis2.D4);
        byte2[i][5]=(boolean)digitalRead(axis2.D5);
        byte2[i][6]=(boolean)digitalRead(axis2.D6);
        byte2[i][7]=(boolean)digitalRead(axis2.D7);
		
		byte3[i][0]=(boolean)digitalRead(axis3.D0);
        byte3[i][1]=(boolean)digitalRead(axis3.D1);
        byte3[i][2]=(boolean)digitalRead(axis3.D2);
        byte3[i][3]=(boolean)digitalRead(axis3.D3);
        byte3[i][4]=(boolean)digitalRead(axis3.D4);
        byte3[i][5]=(boolean)digitalRead(axis3.D5);
        byte3[i][6]=(boolean)digitalRead(axis3.D6);
        byte3[i][7]=(boolean)digitalRead(axis3.D7);

    }
    
    digitalWrite(axis1.readEnable, 1);
	
	for (int i=0; i<4; i++){
        for (int j=7; j>=0; j--){
            axis1.byte[i][j] = byte1[i][j];
            axis2.byte[i][j] = byte2[i][j];
            axis3.byte[i][j] = byte3[i][j];
        }
    }
}