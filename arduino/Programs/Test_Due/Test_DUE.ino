#include <SPI.h>
#include <Wire.h>

#include <Actuator_AxisDue.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

// Arduino DUE
const int D0 = 22;
const int D1 = 24;
const int D2 = 26;
const int D3 = 28;
const int D4 = 30;
const int D5 = 32;
const int D6 = 34;
const int D7 = 36;
const int clk = 9;
const int sel1 = 2;
const int sel2 = 3;
const int rst = 5;
const int readEnable = 4;

void setup() {
    Serial.begin(115200);
    Serial.println("Initialising");
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
	PWMC_ConfigureClocks(42000000 , 0, VARIANT_MCK);
    // rst off
    digitalWrite(rst, 0);
    delay(100);
    digitalWrite(rst, 1);
    Serial.println("Initialised");    

}

void loop() {	
    getEncoder();
    delay(100);
}


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
    
    // Print all four bytes
    for (int i=0; i<4; i++){
        for (int j=7; j>=0; j--){
            Serial.print(byte[i][j]);
        }
        Serial.print(' ');
    }
    
    // Print encoder count
    Serial.println(count);
}

long readSingle(){
    // Read 32-bit counter
    int byte[8];
    for (int j=7; j>=0; j--){
            byte[j]=0;
    }
    digitalWrite(readEnable, 0);
    
    // Read in bits
    byte[0]=(boolean)digitalRead(D0);
    byte[1]=(boolean)digitalRead(D1);
    byte[2]=(boolean)digitalRead(D2);
    byte[3]=(boolean)digitalRead(D3);
    byte[4]=(boolean)digitalRead(D4);
    byte[5]=(boolean)digitalRead(D5);
    byte[6]=(boolean)digitalRead(D6);
    byte[7]=(boolean)digitalRead(D7);
    
    digitalWrite(readEnable, 1);
    // Calculate encoder counts
    // Use least significant three bytes only, MSB used only to determine negative values
    long count = 0;
    // Base values for each byte
    long base[3] = {65536,256,1};
    long power[8] = {1,2,4,8,16,32,64,128};
    // Calculates decimal value of least significant three bytes
    for (int j=0; j<8; j++){
        count = count + base[2]*power[j]*byte[j];
    }
    // Print all four bytes
    for (int j=7; j>=0; j--){
        Serial.print(byte[j]);
    }
    Serial.print(' ');

    // Print encoder count
    Serial.println(count);
}


