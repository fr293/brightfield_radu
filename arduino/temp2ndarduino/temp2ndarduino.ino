/* Magnet Device Control Program Version 2.5 - resistance check - removed, add temperature reading +2nd temp

Dual Power Supply Mode

(C) Qian Cheng, 2015

Power Suppy Coil Relay Pin Number

Serial 1 CH 1 1 47

Serial 1 CH 2 2 49

Serial 2 CH 1 3 51

Serial 2 CH 2 4 53


*/

//include the libray
#include <SerialCommand.h> //SerialCommand Library
#include <cstdlib>
#include <stdlib.h>
#include <DueTimer.h>

//Define two terminating characters CR and LF
#define CR 13
#define LF 10

//Define resistance - temperature conversion parameters - fit fct calibration
// temp = f(R) -> y=y0 +a1*exp(-x/t1) +a2*exp(-x/t2) +a3*exp(-x/t3)

const double res_ser = 9890.0;
const double res_ser2 = 9930.0;

const double aa0  = -9.155;
const double aa1  = 55.567;
const double aa2  = 46.733;
const double aa3  = 56.823;

const double tt1  = 537.10;
const double tt2  = 2577.64;
const double tt3  = 18627.4;

#define therm_pin  A0
//#define therm_pin2  A7

#define numsamples 20
#define numsamples2 20

int samples[numsamples];
int samples2[numsamples2];
int t_tmp;
int t_read_step = 1;

unsigned long previousMillis = 0;   //will store last time the resistance was recorded
//const long interval = 3;            //interval at which to read temperature
const long interval = 20;            //interval at which to read temperature


SerialCommand sCmd; // The demo SerialCommand object

int index_temp = 0; // counter for temperature readings
int index_temp2 = 0; // counter for temperature readings


void setup() {
uint8_t i;

// Increase the analog IN resolution from 10 to 12 bits 
analogReadResolution(12);
for(i=0;i<numsamples;i++){
  samples[i] = 2048;
}

for(i=0;i<numsamples2;i++){
  samples2[i] = 2048;
}


//initialise serial communication
Serial.begin(19200);

while (! Serial);


// Setup callbacks for SerialCommand commands
sCmd.setDefaultHandler(unrecognized); // Handler for command that isn't matched
sCmd.addCommand("Temp_1",Read_Temp_1);
sCmd.addCommand("Temp_2",Read_Temp_2);


}


void loop() {

unsigned long currentMillis = millis(); 

sCmd.readSerial(); // We don't do much, just process serial commands


if (currentMillis-previousMillis >= interval){
previousMillis = currentMillis;
switch (t_read_step){
  case 1:
    t_tmp = analogRead(therm_pin); // multiplex ADC switch
    t_read_step = 2;
    break;
  case 2:
    samples[index_temp] = analogRead(therm_pin);
    t_read_step = 1;
    index_temp = index_temp +1;
    break;
  //case 3:
  //  t_tmp = analogRead(therm_pin2);
  //  t_read_step = 4;
  //  break;
  //case 4:
  //  samples2[index_temp2] = analogRead(therm_pin2);
  //  t_read_step = 3;
  //  index_temp2 = index_temp2 +1;
   // break;
}
  
//t_tmp = analogRead(therm_pin); // multiplex ADC switch
//delay(10);
//samples[index_temp] = analogRead(therm_pin);
//delay(10);
//t_tmp = analogRead(therm_pin2);
//delay(10);
//samples2[index_temp] = analogRead(therm_pin2);
//delay(10);
//Serial.print("Analog reading 2  ");
//Serial.println(analogRead(therm_pin_2));  
 
//index_temp = index_temp +1;

if (index_temp>(numsamples-1)){
  index_temp = 0;
}

//if (index_temp2>(numsamples2-1)){
//  index_temp2 = 0;
//}

}


}





// This gets set as the default handler, and gets called when no other command matches.
void unrecognized(const char *command) {
Serial.println("Not a Valid Command");
}

double convert_ADC_resist(double level_ADC){
  double resis_temp;
  
  resis_temp = (4095.0/ level_ADC)-1.0;
  resis_temp = res_ser/resis_temp;
  return resis_temp;
}

  
double convert_ADC_resist2(double level_ADC){
  double resis_temp;
  
  resis_temp = (4095.0/ level_ADC)-1.0;
  resis_temp = res_ser2/resis_temp;
  return resis_temp;
}
  

double fit_temp(double res){
  
  double fit1,fit2,fit3;
  double temp_out;
  
  fit1 = aa1*exp(-res/tt1);
  fit2 = aa2*exp(-res/tt2);
  fit3 = aa3*exp(-res/tt3);
  
  temp_out = aa0 + fit1+fit2+fit3;
  return temp_out;
}

void Read_Temp_1(){

  double average;
  uint8_t i;
  double resist, temper;

  average=0.0;
  
  for(i=0;i<numsamples;i++){
    average = average +(float) samples[i];
  }
  
  average = average / (float) numsamples;
  resist = convert_ADC_resist(average);
  temper = fit_temp(resist);

//Serial.print("Analog reading ");
//Serial.println(average);  
 
//Serial.print("Thermistor resistance ");
//Serial.println(resist);

//Serial.print("Thermistor temperature ");
Serial.println(round(temper*10.0)/10.0);

}

void Read_Temp_2(){

  double average;
  uint8_t i;
  double resist, temper;

  average=0.0;
  
  for(i=0;i<numsamples2;i++){
    average = average +(float) samples2[i];
  }
  
  average = average / (float) numsamples2;
  resist = convert_ADC_resist2(average);
  temper = fit_temp(resist);

//Serial.print("Analog reading ");
//Serial.println(average);  
 
//Serial.print("Thermistor resistance ");
//Serial.println(resist);

//Serial.print("Thermistor temperature ");
Serial.println(round(temper*10.0)/10.0);

}


