#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Actuator_GUI.h>
#include <Actuator_Axis.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"


Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);


const int xEncoderAPin=22;
const int xEncoderBPin=24;
const int xHomePin=26;
const int xEndPin=28;
const int xMotorPort=1;
const float xEncoderResolution=0.05101E-3;
const int xMaxSpeed=255;

GUI gui(oledResetPin);
axis xAxis(xEncoderAPin,xEncoderBPin,xHomePin,xEndPin,xMotorPort,xEncoderResolution,xMaxSpeed);

extern menu mainMenu;
extern menu jogMenu;
extern menu moveMenu;
extern menu zeroMenu;
extern menu homeMenu;
extern menu settingsMenu;

bool dim=true;

void setup() {

	Serial.begin(115200);
	Serial.println("Initialising");
	
	gui.initialise();
	AFMS.begin();

	attachInterrupt(xEncoderAPin,xEncoderAHandler,CHANGE);
	attachInterrupt(xEncoderBPin,xEncoderBHandler,CHANGE);
	
	
	
	Serial.println("Initialised");
	xAxis.motor->setSpeed(10);

}

void loop() {	
	xAxis.motor->run(BACKWARD);
	delay(500);
	gui.dim(dim);
	delay(500);
	char xBuf[20];
	sprintf(xBuf, "x:  %8.4f\n", xAxis.readPosition());
	jogMenu.menuItems[0]=String(xBuf);
	gui.menuRender(jogMenu);
	
	if(dim==true){
	dim=false;
	}
	else{
	dim=true;
	}
	xAxis.motor->run(RELEASE);
	Serial.print(millis());
	Serial.print(" - ");
	gui.display();	
	Serial.println(millis());
}

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



