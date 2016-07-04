#include <Arduino.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"
#include <SPI.h>
#include <Wire.h>
#include <stdlib.h>
#include <avr/dtostrf.h>

//*****************
// CONFIGURATION
//*****************
// Quadrature Decoder IC Pins
const int D0 = A0;
const int D1 = A1;
const int D2 = 2;
const int D3 = 3;
const int D4 = 4;
const int D5 = 5;
const int D6 = 6;
const int D7 = 7;
const int clk = 11;
const int sel1 = 12;
const int sel2 = 13;
const int rst = 8;
const int readEnable = 10;

// Linear Actuator Properties
const String axisName="xAxis";
const int homePin=A2;
const int endPin=A3;
const int motorPort=4;
const float encoderResolution=0.05101E-3;
const int maxSpeed=255;

// Control Properties
const float kP=10;
const float kI=0.2;
const float kD=0;
const int dt=50;
const int pidUpdateFreq=1000/dt;
const int integralThreshold=20;
const float driveScaleFactor=0.1;
const double positionError=0;

//************
// FUNCTIONS
//************
void jog(int motorSpeed);
void move(double movePosition, String moveType, int moveSpeed);
void pid();
void stop();
void reset();
char* deblank(char *str);

String updateStatus();

//*******************
// GLOBAL VARIABLES
//*******************
// Motor and axis
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
Adafruit_DCMotor *motor = AFMS.getMotor(motorPort);
long encoderPos = 0;
long lastEncoderPos = 0;
long moveEncoderPos[3];
double position = 0.0;
int moveStatus = 0;

// PID Control
long error=0;
long lastError=0;
float integral=0.0;
float derivative=0.0;
double drive=0.0;

int homeStatus=0;
int endStatus=0;
int lastMotorSpeed=0;
int lastMotorDirection=0;

int encoderClock=1;
int lastEncoderClock=1;
int encoderBuffer[24];

// Serial Command
bool rxFlag = 0;
bool cmdValidFlag = 0;
bool cmdQueryFlag = 0;
bool cmdNumFlag = 0;
char rx[50];

// Sprintf
char buf[40];
char bufFloat[20];
double lastPrintPos = -1000.0;


//********
// SETUP
//********
void setup() {
	// Serial initialisation
	Serial.begin(115200);
	Serial.println("*********************");
	Serial.println("Arduino UNO Newport 850G Linear Actuator Controller (Demo Version)");
	Serial.println("Developed as part of the OpenLabTools initiative under Dr. Alexandre Kabla");
	Serial.println("Cambridge University Engineering Department 2015");
	Serial.println("*********************");
	Serial.println("Initialise Begin");
	
	// Motor shield initialisation
	AFMS.begin();

	// Pin allocatins for home and end pins
	pinMode(homePin,INPUT);
	digitalWrite(homePin, HIGH); // Pullup resistor
	pinMode(endPin,INPUT);
	digitalWrite(endPin, HIGH);

    // Set Pin 11 PWN freqency to 31kHz
    TCCR2B = TCCR2B & B11111000 | B00000001;    // set timer 2 divisor to     1 for PWM frequency of 31372.55 Hz
    //TCCR1B = TCCR1B & B11111000 | B00000001;    // set timer 1 divisor to     1 for PWM frequency of 31372.55 Hz
    
    // Pin allocations for Quadrature Decoder IC
    pinMode(D0,INPUT);
    pinMode(D1,INPUT);
    pinMode(D2,INPUT);
    pinMode(D3,INPUT);
    pinMode(D4,INPUT);
    pinMode(D5,INPUT);
    pinMode(D6,INPUT);
    pinMode(D7,INPUT);
    pinMode(clk,OUTPUT);
    pinMode(sel1,OUTPUT);
    pinMode(sel2,OUTPUT);
    pinMode(rst,OUTPUT);
	pinMode(readEnable,OUTPUT);
    
    // Use PWM pin to generate clock signal
    analogWrite(clk, 128);
    // Reset off
	digitalWrite(rst, 0);
	delay(100);
    digitalWrite(rst, 1);
	
	cli();//stop interrupts
    // set timer1 interrupt at 1Hz
    TCCR1A = 0;// set entire TCCR1A register to 0
    TCCR1B = 0;// same for TCCR1B
    TCNT1  = 0;//initialize counter value to 0
    // set compare match register for 1hz increments
    OCR1A = 7811;// = (16*10^6) / (1*1024) - 1 (must be <65536)
    // turn on CTC mode
    TCCR1B |= (1 << WGM12);
    // Set CS10 and CS12 bits for 1024 prescaler
    TCCR1B |= (1 << CS12) | (1 << CS10);  
    // enable timer compare interrupt
    TIMSK1 |= (1 << OCIE1A);
    
	Serial.println("Initialise Complete: Serial command mode");
	sei();//allow interrupts
}

//timer1 interrupt 1Hz
ISR(TIMER1_COMPA_vect){
	if(lastPrintPos!=position){
		dtostrf(position, 8, 4, bufFloat);
		sprintf(buf, "Axis position: %s mm\n", bufFloat);
		//(buf, "Axis position:   %s count: %ld\n", bufFloat,encoderPos);
		Serial.print(buf);
		lastPrintPos = position;
	}
}

void loop() {	
    // Read Serial Command String
    if(Serial.available() > 0){
        // Read in string
        String rxstr = Serial.readStringUntil('\r\n');
        // Convert string to char array
        rxstr.toCharArray(rx,50);
        // Remove spaces
        deblank(rx);
        
		Serial.println(rx);
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
            stop();
        }
        // Get Current Position
        if (!strcmp(cmdName,"TP")){
            Serial.println("TP: Get current position");
            
            getPosition();
            dtostrf(position, 8, 4, bufFloat);
			sprintf(buf, "Axis position: %s mm; Encoder count: %ld\n", bufFloat,encoderPos);
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
            sprintf(buf, "JG: Jog; Motor speed: %4d\n", motorSpeed);
            Serial.print(buf);
            jog(motorSpeed);
        }
        // Reset
        if (!strcmp(cmdName,"RS")){
            Serial.println("RS: Reset position");
            reset();
        }
        // Move Absolute
        if (!strcmp(cmdName,"PA")){
            dtostrf(cmdNum, 8, 4, bufFloat);
            sprintf(buf, "PA: Move Abslute; Position:%s\n", bufFloat);
            Serial.print(buf);
            move(cmdNum,"abs",1);
        }
        // Move Relative
        if (!strcmp(cmdName,"PR")){
            dtostrf(cmdNum, 8, 4, bufFloat);
            sprintf(buf, "PR: Move Relative; Position:%s\n", bufFloat);
            Serial.print(buf);
            move(cmdNum,"rel",1);
        }
		
        // Home
        if (!strcmp(cmdName,"HM")){
            Serial.println("HM: Home Axis");
            homeStatus=1;
			stop();
        }
		
		// End
        if (!strcmp(cmdName,"ED")){
            Serial.println("ED: End Axis");
            endStatus=1;
        }
		
		cmdValidFlag = 0;
    }
    
    // PID Loop
    getPosition();
	if(homeStatus == 1 || endStatus == 1 || digitalRead(homePin) == 1 || digitalRead(endPin) == 1){
		stop();
	}
    if(moveStatus == 1){
        move(0.0,"abs",1);
    }
    pid();
    delay(50);    
}


//ROUND DOUBLE TO LONG//
long longRound(double f){
	long returnLong;
	if(f>=0.0){
		returnLong=floor(f+0.5);
	}
	else{
		returnLong=ceil(f-0.5);
	}
	return returnLong;
}

//GET ENCODER VALUE
long getEncoder(){
    // Read 32-bit counter
    int byte[4][8];
    for (int i=0; i<4; i++){
        for (int j=7; j>=0; j--){
            byte[i][j]=0;
        }
    }
    // Read Enable
    digitalWrite(readEnable, 0);
    for (int i=0; i<4; i++){
        // Byte select
        switch (i) {
            case 0: //MSB
                digitalWrite(sel1, 0);
                digitalWrite(sel2, 1);
                break;
            case 1: //2ND
                digitalWrite(sel1, 1);
                digitalWrite(sel2, 1);
                break;
            case 2: //3RD
                digitalWrite(sel1, 0);
                digitalWrite(sel2, 0);
                break;
            case 3: //LSB
                digitalWrite(sel1, 1);
                digitalWrite(sel2, 0);
                break;
        }
        //delay(10);
       
        // Read in bits
        byte[i][0]=(boolean)digitalRead(D0);
        byte[i][1]=(boolean)digitalRead(D1);
        byte[i][2]=(boolean)digitalRead(D2);
        byte[i][3]=(boolean)digitalRead(D3);
        byte[i][4]=(boolean)digitalRead(D4);
        byte[i][5]=(boolean)digitalRead(D5);
        byte[i][6]=(boolean)digitalRead(D6);
        byte[i][7]=(boolean)digitalRead(D7);
    }
    // Read Disable
     digitalWrite(readEnable, 1);
    
	// Calculate encoder counts
    // Use least significant three bytes only, MSB used only to determine negative values
    long count = 0;
    // Base values for each byte
    long base[3] = {65536,256,1};
    long power[8] = {1,2,4,8,16,32,64,128};
    // Calculates decimal value of least significant three bytes
    for (int i=1; i<4; i++){
        for (int j=0; j<8; j++){
            count = count + base[i-1]*power[j]*byte[i][j];
        }
		//Serial.println(count);
    }
    // Test MSB to see if in negative range
    if (byte[0][7] == 1){   // MSB
        count = -(16777216 - count);
    }
    
    /*
    // Print all four bytes
    for (int i=0; i<4; i++){
        for (int j=7; j>=0; j--){
            Serial.print(byte[i][j]);
        }
        Serial.print(' ');
    }
    
    // Print encoder count
    Serial.println(count);
	*/
    
    // Update encoder position
    count = -count; // Counter is reversed
    lastEncoderPos = encoderPos;
    encoderPos = count;
    
    return count;
}

//GET AXIS POSITION//
double getPosition(){
    getEncoder();
	position=encoderPos*encoderResolution;
	return position;
}

//JOG AXIS//
//Use for all move and stop functions
void jog(int motorSpeed){
	//Serial.print("Jog: ");
	//Serial.println(motorSpeed);
	
    // Limit  motor speed
	if(motorSpeed>=1000){
		motorSpeed=1000;
	}
	else if(motorSpeed<=-1000){
		motorSpeed=-1000;
	}
	if(lastMotorSpeed!=motorSpeed){
	motor->setSpeed(abs((float)motorSpeed*(float)maxSpeed/1000));
	lastMotorSpeed=motorSpeed;
	}
	if(motorSpeed>0&&lastMotorDirection!=1){
			motor->run(FORWARD);
			lastMotorDirection=1;
	}
	else if(motorSpeed<0&&lastMotorDirection!=-1){
			motor->run(BACKWARD);
			lastMotorDirection=-1;
	}
	else if(motorSpeed=0&&lastMotorDirection!=0){
			motor->run(RELEASE);
			lastMotorDirection=0;
	}
}

//STOP//
//Stop and homing functions
void stop(){
	jog(0);
	if(homeStatus==1){
		int homeCheckFlag = 0;
		while(homeCheckFlag == 0){
			while(digitalRead(homePin)==0){
				jog(-500);
			}
			jog(0);
			delay(100);
			if(digitalRead(homePin)==1){
				homeCheckFlag = 1;
			}
		}
		jog(0);
		while(digitalRead(homePin)==1){
			jog(100);
		}
		jog(0);
		homeStatus=0;
		Serial.println("Home Axis Complete");
	}
	else if(endStatus==1){
		int endCheckFlag = 0;
		while(endCheckFlag == 0){
			while(digitalRead(endPin)==0){
				jog(500);
			}
			jog(0);
			delay(100);
			if(digitalRead(endPin)==1){
				endCheckFlag = 1;
			}
		}
		jog(0);
		while(digitalRead(endPin)==1){
			jog(-100);
		}
		jog(0);
		endStatus=0;
        Serial.println("End Axis Complete");
	}
	else if(digitalRead(homePin)==1){
		Serial.println("Home Stop Detected");
		while(digitalRead(homePin)==1){
			jog(100);
		}
		jog(0);
	}
	else if(digitalRead(endPin)==1){
		Serial.println("End Stop Detected");
		while(digitalRead(endPin)==1){
			jog(-100);
		}
		jog(0);
	}
	else if(moveStatus==1){
		moveStatus = 0;
		Serial.println("Move Aborted");
	}
}

// Move to position
void move(double movePosition, String moveType, int moveSpeed){
	if(moveStatus==0){
		double  _positionError;
		if(positionError<=encoderResolution){
			_positionError=encoderResolution;
		}
		else{
			_positionError=positionError;
		}
		if(moveType=="abs"){
			moveEncoderPos[0]=longRound(movePosition/encoderResolution);
			moveEncoderPos[1]=longRound((movePosition-_positionError)/encoderResolution);
			moveEncoderPos[2]=longRound((movePosition+_positionError)/encoderResolution);
			Serial.println("Move Absolute Begin");
			moveStatus=1;
		}
		else if(moveType=="rel"){
			moveEncoderPos[0]=longRound((position+movePosition)/encoderResolution);
			moveEncoderPos[1]=longRound((position+movePosition-_positionError)/encoderResolution);
			moveEncoderPos[2]=longRound((position+movePosition+_positionError)/encoderResolution);
			Serial.println("Move Relative Begin");
			moveStatus=1;
		}
		else{
			Serial.println("Error: Move Command Invalid");
			return;
		}
		/*
		Serial.println(moveEncoderPos[0]);
		Serial.println(moveEncoderPos[1]);
		Serial.println(moveEncoderPos[2]);
		*/
	}
	else if(moveStatus==1){
		if(encoderPos>moveEncoderPos[1]&&encoderPos<moveEncoderPos[2]){
			jog(0);
			delay(100);
			if(encoderPos>moveEncoderPos[1]&&encoderPos<moveEncoderPos[2]){
				error=0;
				lastError=0;
				integral=0;
				derivative=0;
				//moveStatus=2;
				moveStatus = 0;
				Serial.println("Move Complete");
				/*
				Serial.println(encoderPos);
				Serial.println(moveEncoderPos[0]);
				Serial.println(moveEncoderPos[1]);
				Serial.println(moveEncoderPos[2]);
				*/
			}
			return;
			
		}
		else{
			return;
		}
	}
	else{
		return;
	}
}

// PID movement
void pid(){
	if(moveStatus==1){
		// Calculate position error
		error=moveEncoderPos[0]-encoderPos;
		// PID Control
		if(abs(error)<integralThreshold){
			integral=integral+(float)error*(float)dt;
		}
		derivative=(float)(error-lastError)/(float)dt;
        drive = error*kP+integral*kI;
		//drive=error*kP+integral*kI+derivative*kD;
		lastError=error;
		
		// Jog motor - limit motorSpeed
		int motorSpeed;
		if(drive*driveScaleFactor>1000){
			motorSpeed=1000;
		}
		else if(drive*driveScaleFactor<-1000){
			motorSpeed=-1000;
		}
		else{
			motorSpeed = (int)(drive*driveScaleFactor);
		}
		jog(motorSpeed);
		
        /*
        Serial.print(moveEncoderPos[0]);
        Serial.print(" ; ");
		Serial.print(moveEncoderPos[1]);
        Serial.print(" ; ");
		Serial.print(moveEncoderPos[2]);
        Serial.print(" ; ");
        Serial.print(encoderPos);
        Serial.print(" ; ");
		Serial.print(error);
		Serial.print(" ; ");
		Serial.println(drive);
		*/
		
        
		/*
		Serial.print(error);
		Serial.print(" ; ");
		
		Serial.print(error*kP);
		Serial.print(" , ");
		Serial.print(integral*kI);
		Serial.print(" , ");
		Serial.println(derivative*kD);
		*/
	}
	else{
		return;
	}
}

// Reset encoder count
void reset(){
	stop();
	delay(10);
    
    // Reset on
    digitalWrite(rst, 0);
    delay(10);
    digitalWrite(rst,1);
    
    // Update encoder and position
    getEncoder();
    getPosition();	
}

// Gets status string
String updateStatus(){
	String buffer;
	if(encoderPos>lastEncoderPos){
		buffer=axisName.substring(0,1)+"+";
	}
	else if(encoderPos<lastEncoderPos){
		buffer=axisName.substring(0,1)+"-";
	}
	else if(encoderPos==lastEncoderPos){
		buffer=axisName.substring(0,1)+"$";
	}
	return buffer;
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