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
axis axis1(01,22,24,26,28,30,32,34,36,9,2,3,5,4,14,15,3,encoderResolution);

bool debugMode = 1;

// Serial Command
bool rxFlag = 0;
bool cmdValidFlag = 0;
bool cmdQueryFlag = 0;
bool cmdNumFlag = 0;
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
	
	attachInterrupt(axis1.homePin,axis1HomeHandler,HIGH);
	attachInterrupt(axis1.endPin,axis1EndHandler,HIGH);
	
	Serial.println("Initialised1");
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
            Serial.println(buf);
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
            Serial.println(buf); 
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
                sprintf(buf, "Numeric value:%s\n", bufFloat);
                Serial.print(buf);
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
/* 			if (cmdAddr == 2){
				axis2.jog(motorSpeed);
			}
			if (cmdAddr == 3){
				axis3.jog(motorSpeed);
			}
			if (cmdAddr == 4){
				axis4.jog(motorSpeed);
			} */
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
	
	sprintf(buf, "%02d%+d\n", axis1.axisAddr, axis1.getEncoder());
	Serial.print(buf);
	delay(500);
	if(digitalRead(axis1.homePin)==1){
		sprintf(buf, "%02dhome\n", axis1.axisAddr);
		Serial.print(buf);
	}
	if(digitalRead(axis1.endPin)==1){
		sprintf(buf, "%02dend\n", axis1.axisAddr);
		Serial.print(buf);
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

void axis1HomeHandler(){
	axis1.homeHandler();
}
void axis1EndHandler(){
	axis1.endHandler();
}