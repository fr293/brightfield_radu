#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Actuator_GUI.h>
#include <Actuator_Axis.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);
GUI gui;

const String xAxisName="xAxis";
const int xEncoderAPin=23;
const int xEncoderBPin=25;
const int xHomePin=27;
const int xEndPin=29;
const int xMotorPort=4;
const float xEncoderResolution=0.05101E-3;
const int xMaxSpeed=255;
axis xAxis(xAxisName,xEncoderAPin,xEncoderBPin,xHomePin,xEndPin,xMotorPort,xEncoderResolution,xMaxSpeed);


//SETUP SEQUENCE//

void setup() {
	Serial.begin(115200);
	Serial.println("Initialising");
	
	gui.initialise();
	AFMS.begin();
	startTimer(TC1,0,TC3_IRQn,gui.cursorUpdateFreq);
	startTimer(TC1,1,TC4_IRQn,pidUpdateFreq);

	attachInterrupt(gui.buttonAPin,buttonAHandler,RISING);
	attachInterrupt(gui.buttonBPin,buttonBHandler,RISING);
	
	attachInterrupt(xEncoderAPin,xEncoderAHandler,CHANGE);
	attachInterrupt(xEncoderBPin,xEncoderBHandler,CHANGE);
	
	/*
	pinMode(xHomePin,INPUT);
	attachInterrupt(xHomePin,xHomeHandler,FALLING);
	pinMode(xEndPin,INPUT);
	attachInterrupt(xEndPin,xEndHandler,FALLING);
	*/
	
	gui.status="Ready";
	Serial.println("Initialised");
}


//MAIN PROGRAM LOOP//

void loop() {	
	if(digitalRead(xHomePin)==0||xAxis.homeStatus==1){
		xAxis.stop();
	}
	
	
	switch(gui.menuSelect[0]){
		case 0:		//MAIN MENUS
		
			switch(gui.menuSelect[1]){
				case 0:		//Start Menu
					break;
				case 1:		//Main Menu
					gui.menuDisplay(mainMenu);
					break;
			}
			break;
			
		case 1:		//SUB MENUS
		
			switch(gui.menuSelect[1]){
				case 0: 	//Serial Mode
					serialMode();
					break;
				case 1: 	//Home Axes
					homeAxes();
					break;
				case 2:		//Jog Axes
					jogAxes();
					break;
				case 3:		//Move Absolute
					moveAbs();
					break;
				case 4:		//Move Relative
					gui.menuDisplay(moveRelMenu);
					break;
				case 5:		//Reset Position
					resetPosition();
					break;
				case 6:		//Other Functions
					gui.menuDisplay(functionsMenu);
					break;
				case 7:		//Settings
					gui.menuDisplay(settingsMenu);
					
					break;
			}
			break;
		
		default: 
			break;
	}
	
	
}

String printPosition(int axisNumber, bool newLine){
	double position[3];
	char buffer[20];
	String stringBuffer;
	switch(axisNumber){
		case 0:
			position[0]=xAxis.readPosition();
			if(position[0]>=0){
				position[0]=float(floor(position[0]*10000+0.5))/10000;
			}
			else{
				position[0]=float(ceil(position[0]*10000-0.5))/10000;
			}
			sprintf(buffer, "x:   %8.4f",position[0]);
			break;
		case 1:
			//sprintf(buffer, "y:   %8.4f", yAxis.readPosition());
			break;
		case 2:
			//sprintf(buffer, "z:   %8.4f", zAxis.readPosition());
			break;
	}
	stringBuffer=String(buffer);
	if(newLine==true){
		stringBuffer+="\n";
	}
	return stringBuffer;
}
	

//SERIAL MODE//
void serialMode(){
	gui.menuDisplay(serialMenu);
	if (Serial.available() > 0) {
                // read the incoming byte:
                char incomingByte = (char) Serial.read();

                // say what you got:
                Serial.print("I received: ");
                Serial.println(incomingByte);
	}	
}


//HOME AXES//
void homeAxes(){
	char buffer[20];
	sprintf(buffer, "x:   %8.4f\n", xAxis.readPosition());
	homeMenu.menuItems[0]=String(buffer);
	/*
	sprintf(buffer, "y:   %8.4f\n", yAxis.readPosition());
	homeMenu.menuItems[1]=String(buffer);
	sprintf(buffer, "z:   %8.4f\n", zAxis.readPosition());
	homeMenu.menuItems[2]=String(buffer);
	*/
	
	gui.menuDisplay(homeMenu);
	
	switch(gui.menuActive){
		case -1:
			xAxis.stop();
			break;
		case 0:
			if(xAxis.homeStatus==2){
				xAxis.stop();
				xAxis.reset();
				xAxis.homeStatus=0;
				gui.status="Home x Done";
				gui.menuActive=-1;
			}
			else{
				xAxis.jog(-1000);
				gui.status="Home x";
			}
			break;
		case 1:
			gui.status="Home y";
			break;
		case 2:
			gui.status="Home z";
			break;
		case 3:
			if(xAxis.endStatus==2){
				xAxis.endStatus=0;
				gui.status="End x Done";
				xAxis.reset();
				gui.menuActive=-1;
			}
			else{
				xAxis.jog(1000);
				gui.status="End x";
			}
			break;
		case 4:
			gui.status="End y";
			break;
		case 5:
			gui.status="End z";
			break;
	}
}


//JOG AXES//
void jogAxes(){
	char buffer[20];
	sprintf(buffer, "x:   %8.4f", xAxis.readPosition());
	jogMenu.menuItems[0]=String(buffer);
	/*
	sprintf(buffer, "y:   %8.4f", yAxis.readPosition());
	jogMenu.menuItems[2]=String(buffer);
	sprintf(buffer, "z:   %8.4f", zAxis.readPosition());
	jogMenu.menuItems[4]=String(buffer);
	*/
	
	gui.menuDisplay(jogMenu);
	
	int motorSpeed;
	int joyValue=gui.joyRead('x');
	if(joyValue>gui.joyThreshold){
		motorSpeed=1000*(joyValue-gui.joyThreshold)/(gui.joyXZero-gui.joyThreshold);
	}
	else if(joyValue<-gui.joyThreshold){
		motorSpeed=1000*(joyValue+gui.joyThreshold)/(gui.joyXZero-gui.joyThreshold);
	}
	else{
		motorSpeed=0;
	}
	switch(gui.menuActive){
		case -1:
			gui.status="Ready";
			break;
		case 0:	
			xAxis.jog(motorSpeed);
			gui.status="Jog x";
			break;
		case 1:
			gui.status="Jog y";
			break;
		case 2:
			gui.status="Jog z";
			break;
	}
}

//MOVE ABSOLUTE//
void moveAbs(){
	char buffer[20];
	sprintf(buffer, "x:   %8.4f\n", xAxis.readPosition());
	moveAbsMenu.menuItems[0]=printPosition(0,0);
	
	/*
    moveAbsMenu.menuItems[2]=String(buffer);
	sprintf(buffer, "y:   %8.4f\n", yAxis.readPosition());
	
	sprintf(buffer, "z:   %8.4f\n", zAxis.readPosition());
	moveAbsMenu.menuItems[7]=String(buffer);
	*/
	gui.menuDisplay(moveAbsMenu);
	
	char floatBuf[3][7];
	float movePosition[3];
	moveAbsMenu.menuItems[3].substring(0,7).toCharArray(floatBuf[0],7);
	movePosition[0]=atof(floatBuf[0]);
	switch(gui.menuActive){
		case -1:
			xAxis.stop();
			xAxis.moveStatus=0;
			break;
		case 0:	
			gui.status="Move";
			xAxis.move(movePosition[0],"abs",1);
			if(xAxis.moveStatus==2){
				xAxis.moveStatus=0;
				gui.status="Move Done";
				gui.menuActive=-1;
			}
			break;
		case 3:
			break;
		default:
			break;
	}
	
}

//RESET POSITION//
void resetPosition(){
	char buffer[20];
	sprintf(buffer, "y:   %8.4f", xAxis.readPosition());
	resetMenu.menuItems[0]=printPosition(0,0);
	resetMenu.menuItems[2]=String(buffer);
	/*
	sprintf(buffer, "z:   %8.4f", zAxis.readPosition());
	resetMenu.menuItems[4]=String(buffer);
	*/
	gui.menuDisplay(resetMenu);
	switch(gui.menuActive){
		case -1:
			gui.status="Ready";
			break;
		case 0:	
			gui.status="Reset x";
			xAxis.reset();
			gui.menuActive=-1;
			break;
		case 1:
			gui.status="Reset y";
			gui.menuActive=-1;
			break;
		case 2:
			gui.status="Reset x";
			gui.menuActive=-1;
			break;
	}
}
	

//UPDATE MOTOR STATUS//
void updateStatus(){
	gui.axisStatus[0]=xAxis.updateStatus();
	gui.axisStatus[1]="--";
	gui.axisStatus[2]="--";
}


//INTERRUPTS AND INTERRUPT HANDLERS//

void startTimer(Tc *tc, uint32_t channel, IRQn_Type irq, uint32_t frequency) {
        pmc_set_writeprotect(false);
        pmc_enable_periph_clk((uint32_t)irq);
        TC_Configure(tc, channel, TC_CMR_WAVE | TC_CMR_WAVSEL_UP_RC | TC_CMR_TCCLKS_TIMER_CLOCK4);
        uint32_t rc = VARIANT_MCK/128/frequency; //128 because we selected TIMER_CLOCK4 above
        TC_SetRA(tc, channel, rc/2); //50% high, 50% low
        TC_SetRC(tc, channel, rc);
        TC_Start(tc, channel);
        tc->TC_CHANNEL[channel].TC_IER=TC_IER_CPCS;
        tc->TC_CHANNEL[channel].TC_IDR=~TC_IER_CPCS;
        NVIC_EnableIRQ(irq);
}

void TC3_Handler(){
    TC_GetStatus(TC1, 0);
	gui.cursorMove();
}

void TC4_Handler(){
	TC_GetStatus(TC1, 1);
	updateStatus();
	xAxis.pid();
}
void buttonAHandler(){
	gui.buttonA();
}

void buttonBHandler(){
	gui.buttonB();
}

void xEncoderAHandler(){
	xAxis.encoderA();
}

void xEncoderBHandler(){
	xAxis.encoderB();
}

void xHomeHandler(){
	if(digitalRead(xHomePin)==1||xAxis.homeStatus==1){
		return;
	}
	xAxis.stop();
	xAxis.homeStatus=1;
}

void xEndHandler(){
	if(digitalRead(xEndPin)==1||xAxis.endStatus==1){
		return;
	}
	Serial.println("xEnd");
	xAxis.stop();
	xAxis.endStatus=1;
}
