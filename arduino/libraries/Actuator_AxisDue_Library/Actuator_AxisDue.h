#ifndef ACTUATOR_AXISDUE_h
#define ACTUATOR_AXISDUE_h

#include <Arduino.h>
#include <../Adafruit_Motor_Shield_V2_Library/Adafruit_MotorShield.h>
#include "../Adafruit_Motor_Shield_V2_Library/utility/Adafruit_PWMServoDriver.h"

extern Adafruit_MotorShield AFMS;

class axis{
	public:
		axis(int _axisAddr,
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
			float _encoderResolution);
			
		void initialise();
		void jog(int motorSpeed);
		long getEncoder();
		long getEncoderF();
		long checkEncoder(long count);
		void homeHandler();
		void endHandler();
		
		
		Adafruit_DCMotor *motor;
		long encoderCount = 0;
		long encoderCountL[10];
		int encoderCountIndex;

		


		int axisAddr;
		int D0;
		int D1;
		int D2;
		int D3;
		int D4;
		int D5;
		int D6;
		int D7;
		int sel1;
		int sel2;
		int clk;
		int rst;
		int readEnable;
		int homePin;
		int endPin;
		int motorPort;
		float encoderResolution;
		int lastMotorSpeed = 0;
		int lastMotorDirection = 0;
		int homeSpeed = 50;
		int homeFlag = 0;
		int endFlag = 0;
		int cmdOverrideFlag = 0;
		int byte[4][8];
		
		private:
		char buf[40];
};

#endif