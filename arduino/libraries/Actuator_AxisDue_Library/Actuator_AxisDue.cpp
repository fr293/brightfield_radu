#include <Arduino.h>
#include <../Adafruit_Motor_Shield_V2_Library/Adafruit_MotorShield.h>
#include "../Adafruit_Motor_Shield_V2_Library/utility/Adafruit_PWMServoDriver.h"
#include <SPI.h>
#include <Wire.h>
#include <Actuator_AxisDue.h>

//AXIS CLASS CONSTRUCTOR//
axis::axis(int _axisAddr,
			int _D0,
			int _D1,
			int _D2,
			int _D3,
			int _D4,
			int _D5,
			int _D6,
			int _D7,
			int _clk,
			int _sel1,
			int _sel2,
			int _rst,
			int _readEnable,
			int _homePin,
			int _endPin,
			int _motorPort,
			float _encoderResolution){
				
	// Arduino DUE
	D0 = _D0;
	D1 = _D1;
	D2 = _D2;
	D3 = _D3;
	D4 = _D4;
	D5 = _D5;
	D6 = _D6;
	D7 = _D7;
	clk = _clk;
	sel1 = _sel1;
	sel2 = _sel2;
	rst = _rst;
	readEnable = _readEnable;
	
	homePin = _homePin;
	endPin = _endPin;
	motorPort = _motorPort;
	encoderResolution = _encoderResolution;
	axisAddr = _axisAddr;
	
	motor = AFMS.getMotor(motorPort);
}

void axis::initialise(){
	//Serial.println("Initialising Axis");  
    pinMode(D0,INPUT);
    pinMode(D1,INPUT);
    pinMode(D2,INPUT);
    pinMode(D3,INPUT);
    pinMode(D4,INPUT);
    pinMode(D5,INPUT);
    pinMode(D6,INPUT);
    pinMode(D7,INPUT);
    
    pinMode(sel1,OUTPUT);
    pinMode(sel2,OUTPUT);
    pinMode(rst,OUTPUT);
    pinMode(readEnable,OUTPUT);
    
    // Use PWM pin to generate clock signal
	//analogWrite(clk, 128);
	//PWMC_ConfigureClocks(42000000 , 0, VARIANT_MCK);
    // rst off
    digitalWrite(rst, 0);
    delay(100);
    digitalWrite(rst, 1);
	
	pinMode(homePin,INPUT);
	digitalWrite(homePin, HIGH); 
    //Serial.println("Initialised Axis");   
	sprintf(buf,"Axis initialised: %02d",axisAddr);
	Serial.println(buf);	
}

void axis::homeHandler(){
	if (homeFlag == 0){
		homeFlag = 1;
	}
}

void axis::endHandler(){
	if (endFlag == 0){
		endFlag = 1;
	}
}

//JOG AXIS//
//Use for all move and stop functions
void axis::jog(int motorSpeed){
	if(motorSpeed>=256){
		motorSpeed=255;
	}
	else if(motorSpeed<=-256){
		motorSpeed=-255;
	}
	if(lastMotorSpeed!=motorSpeed){
	motor->setSpeed(abs(motorSpeed));
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
	else if(motorSpeed==0&&lastMotorDirection!=0){
			motor->run(RELEASE);
			lastMotorDirection=0;
	}
}


long axis::getEncoder(){
    // Read 32-bit counter
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
        delay(10);
        
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
	*/
	//Reverse count dir
    count = -count;
    // Print encoder count
    //Serial.println(count);

	return checkEncoder(count);
}



long axis::getEncoderF(){ //fast version
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
	*/
	//Reverse count dir
    count = -count;
    // Print encoder count
    //Serial.println(count);

	return checkEncoder(count);
}


long axis::checkEncoder(long count){
	//Check for artefacts - checks that new encoder value is less than 1000 counts away from average of last 10 encoder values
	long countL = 0;
	int sum,size;
	size = sizeof(encoderCountL)/sizeof(encoderCountL[0]);
	sum = 0;
	if (encoderCountIndex < size){
		encoderCountL[encoderCountIndex] = count;
		encoderCountIndex += 1;
		encoderCountIndex++;
	}
	else{
		for(int i = 0; i < size; i++){
			sum += encoderCountL[i];
		}
		countL = sum/size;
		if (abs(count - countL) > 4000){
			count = encoderCountL[size-1];
			//Serial.print('y');
		}
		else{
			for(int i = 0; i < size-1; i++){
				encoderCountL[i] = encoderCountL[i+1];
			}
			encoderCountL[size-1] = count;
			//Serial.print('n');
		}
	}
	/*
	Serial.print(count);
	Serial.print(':');
	Serial.println(countL);
	*/
	return count;
}