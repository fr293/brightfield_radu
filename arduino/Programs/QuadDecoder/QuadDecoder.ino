#include <SPI.h>
#include <Wire.h>

/*
// Arduino Due
const int pin0=39;
const int pin1=41;
const int pin2=43;
const int pin3=45;
const int pin4=47;
const int pin5=49;
const int pin6=51;
const int pin7=53;
*/

// Arduino Uno
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
const int reset = 8;
const int readEnable = 10;

const int homePin=A2;
const int endPin=A3;
bool homeFlag = 0;
bool endFlag = 0;

void setup() {
    // Set Pin 11 PWN freqency to 31kHz
    TCCR2B = TCCR2B & B11111000 | B00000001;    // set timer 2 divisor to     1 for PWM frequency of 31372.55 Hz
    //TCCR1B = TCCR1B & B11111000 | B00000001;    // set timer 1 divisor to     1 for PWM frequency of 31372.55 Hz
	
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
    pinMode(reset,OUTPUT);
	
	pinMode(homePin,INPUT);
    pinMode(endPin,INPUT);
    
    // Use PWM pin to generate clock signal
    analogWrite(clk, 128);
    // Reset off
    digitalWrite(reset, 0);
    delay(100);
    digitalWrite(reset, 1);

}

void loop() {	
    getEncoder();
    //readSingle();
	/*
	homeFlag = (bool)digitalRead(homePin);
	endFlag = (bool)digitalRead(endPin);
	
	if (homeFlag == 1){
		Serial.println("home");
	}
	else{
		Serial.println("not home");
	}
	
	if (endFlag == 1){
		Serial.println("end");
	}
	else{
		Serial.println("not end");
	}
	*/
	
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



