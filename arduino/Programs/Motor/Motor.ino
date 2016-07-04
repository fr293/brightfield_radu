#define encoderA 22
#define encoderB 23
#define switchA 24
#define switchB 25
#define led 13

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

Adafruit_MotorShield AFMS = Adafruit_MotorShield(); 
Adafruit_DCMotor *motor = AFMS.getMotor(4);


void setup(){
  Serial.begin(115200);
  Serial.println("Initialised1");
	
  AFMS.begin();
  motor->setSpeed(50);
  motor->run(RELEASE);
  for(int i=0;i<500;i++){
    motor->run(FORWARD);
    delay(10);
  }
  Serial.println("Forward Done");
  for(int i=0;i<500;i++){
    motor->run(BACKWARD);
    delay(10);
  }
  motor->run(RELEASE);
  Serial.println("Backward Done");
}

void loop(){
}
