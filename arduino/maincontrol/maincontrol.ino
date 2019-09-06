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
#include <Wire.h>
#include <Adafruit_ADS1015.h>

Adafruit_ADS1115 ads(0x48);  // board voltage 3.3, gaine_ONE, 1 bit = 0.125mV


//Arduino pin for relay regarding to coil 1-4
#define RelayPin1 47
#define RelayPin2 49
#define RelayPin3 51
#define RelayPin4 53

//Arduino LED for temperature control warning
#define ArduinoLED 13

//Define two terminating characters CR and LF
#define CR 13
#define LF 10

//Define resistance - temperature conversion parameters - fit fct calibration
// temp = f(R) -> y=y0 +a1*exp(-x/t1) +a2*exp(-x/t2) +a3*exp(-x/t3)
const double res_ser = 9890.0;
const double res_ser2 = 9930.0;
const double res_ser3 = 9870.0;
const double res_ser4 = 9890.0;


const double aa0  = -9.155;
const double aa1  = 55.567;
const double aa2  = 46.733;
const double aa3  = 56.823;

const double tt1  = 537.10;
const double tt2  = 2577.64;
const double tt3  = 18627.4;

//#define therm_pin  A0
#define therm_pin2  A7
//#define therm_pin  0
//#define therm_pin_2  1

//#define numsamples 20
//#define numsamples2 20

//int samples[numsamples];
//int samples2[numsamples2];
//int t_tmp;
int t_read_step = 3;

int16_t adc0_level;
int16_t adc1_level;
int16_t adc2_level;
int16_t adc_dump_level;
int16_t adc7_level_arduino;

unsigned long previousMillis = 0;   //will store last time the resistance was recorded
//const long interval = 3;            //interval at which to read temperature
//const long interval = 20;            //interval at which to read temperature
//onst long interval = 500;            //interval at which to read temperature 2 x5 = 1000 ms
const long interval = 300;            //interval at which to read temperature - 3 sensors x3 = 900 ms
//const long interval = 250;            //interval at which to read temperature - 2.5 sensors x4 = 1000 ms

//const long interval = 10250;            //testing power suply - don't need temperature




SerialCommand sCmd; // The demo SerialCommand object

boolean RelayState[4]; //return the current state of the relay

int coil_no = 0;//a counter to decide which coil to be tested

int errormsg = 0; //a flag to determine whether the power supply is allowed to trun on or not, 1 for True(error)

int psstate = 0;

//int index_temp = 0; // counter for temperature readings
//int index_temp2 = 0; // counter for temperature readings

String id_ps; // the # of power supply

int no_ps = 0;

void setup() {
//uint8_t i;

// Increase the analog IN resolution from 10 to 12 bits 
analogReadResolution(12);
//for(i=0;i<numsamples;i++){
//  samples[i] = 2048; // init samples to a non zero value -> half of the 2^12
//  samples2[i] = 2048;
//}

ads.setGain(GAIN_ONE);
ads.begin();


// Configure the onboard pin for output
pinMode(RelayPin1, OUTPUT);
pinMode(RelayPin2, OUTPUT);
pinMode(RelayPin3, OUTPUT);
pinMode(RelayPin4, OUTPUT);

//pinMode(therm_pin, INPUT);
//pinMode(therm_pin_2, INPUT);

// initialize the digital pin for LED as an output.
pinMode(ArduinoLED, OUTPUT);

// default to relay switch off
digitalWrite(RelayPin1, LOW);
digitalWrite(RelayPin2, LOW);
digitalWrite(RelayPin3, LOW);
digitalWrite(RelayPin4, LOW);

//initially set the LED is low...low represents a normal condition
digitalWrite(ArduinoLED, LOW);

//get the current state of the switch
RelayState[0] = digitalRead(RelayPin1);
RelayState[1] = digitalRead(RelayPin2);
RelayState[2] = digitalRead(RelayPin3);
RelayState[3] = digitalRead(RelayPin4);

//initialise serial communication
Serial.begin(19200);
Serial1.begin(19200);
//Serial2.begin(9600);

while (! Serial);
while (! Serial1);
//while (! Serial2);

Serial1.flush();

char inChar, temp;

Serial1.write("*IDN?\n");

delay(85); //ask the identification of the power supply and wait until it responds

if(Serial1.available() > 0){ //read the string and save in id_ps
  
  inChar = Serial1.read(); //id_ps = Serial1.readStringUntil('\n');
  
}
while (Serial1.available()){
temp = Serial1.read();
}
// Clear the send buffer of the PSU. It can store only 63 characters.

// erase any error stored on PSU
Serial1.write("EER?");
Serial1.write(10);

delay(100);
while (Serial1.available()){
temp = Serial1.read();
}

delay(85);

Serial1.write("*ESR?");
Serial1.write(10);

delay(100);
while (Serial1.available()){
temp = Serial1.read();
}

// end erase any error



//Serial.print(inChar);

if(inChar == 'H' ) {  //The first letter for the new power supply is 'H'
  
  no_ps = 2;  //the new power supply
  
} else if(inChar == 'T' ){ //The first letter for the new power supply is 'T'
  
  no_ps = 1;  // the old power supply
  Serial2.begin(19200);
  while (! Serial2);
  
while (Serial2.available()){ // clear buffer
temp = Serial2.read();
}  

// erase any error stored on PSU
Serial2.write("EER?");
Serial2.write(10);

delay(100);
while (Serial2.available()){
temp = Serial2.read();
}

delay(85);

Serial2.write("*ESR?");
Serial2.write(10);

delay(100);
while (Serial2.available()){
temp = Serial2.read();
}

// end erase any error
  
}  else {
  
  no_ps = 0;  // no power supply detected
}

//Serial.print(no_ps); // should we comment?

// Setup callbacks for SerialCommand commands
sCmd.addCommand("PR",PSURead);
sCmd.addCommand("PW",PSUWrite);
sCmd.addCommand("Set_Local",Set_Local);
sCmd.addCommand("P_ON", Power_ON);
sCmd.addCommand("P_OFF", Power_OFF);
sCmd.addCommand("Set_flag", Set_Flag);
sCmd.addCommand("Read_flag", Read_Flag);
sCmd.setDefaultHandler(unrecognized); // Handler for command that isn't matched
sCmd.addCommand("IN_C",Input_Current);
sCmd.addCommand("Light_ON",Light_ON);
sCmd.addCommand("Light_OFF",Light_OFF);
sCmd.addCommand("T1",Read_Temp_1);
sCmd.addCommand("T2",Read_Temp_2);
sCmd.addCommand("T3",Read_Temp_3);
//sCmd.addCommand("T4",Read_Temp_4);
sCmd.addCommand("CMD1",General_Command1);
sCmd.addCommand("CMD2",General_Command2);

if (no_ps == 1) {
delay(85);  
Power_OFF(); // switch off all power supplies
//useful when resetting Arduino  
delay(85);


Serial1.write("I1 0.001");
Serial1.write(10);
//delay(20);

Serial2.write("I1 0.001");
Serial2.write(10);
delay(85);


Serial1.write("I2 0.001");
Serial1.write(10);
//delay(20);

Serial2.write("I2 0.001");
Serial2.write(10);
delay(85);

} 

if (no_ps == 2) {
  
Serial1.write("INST OUT1\n");
Serial1.write("CURR 0.002\n");

Serial1.write("INST OUT2\n");
Serial1.write("CURR 0.001\n");

Serial1.write("INST OUT3\n");
Serial1.write("CURR 0.001\n");

Serial1.write("INST OUT4\n");
Serial1.write("CURR 0.001\n");

}

}


void loop() {

unsigned long currentMillis = millis(); 

sCmd.readSerial(); // We don't do much, just process serial commands

//The section below is the interrupt and timer.

//Timer1.start();

//if (psstate == 1){

//test(coil_no+1);

//}

//Timer1.stop();

if (currentMillis-previousMillis >= interval){
previousMillis = currentMillis;
switch (t_read_step){
  //case 1:
  //  t_tmp = analogRead(therm_pin); // multiplex ADC switch
  //  t_read_step = 2;
  //  break;
  //case 2:
  //  samples[index_temp] = analogRead(therm_pin);
  //  t_read_step = 1;
  //  index_temp = index_temp +1;
  //  break;
  case 3:
    adc_dump_level = ads.readADC_SingleEnded(0);
    delay(15);
    adc0_level = ads.readADC_SingleEnded(0);
    t_read_step = 4;
    break;
  case 4:
    //adc_dump_level = ads.readADC_SingleEnded(1);
    //delay(15);
    //adc1_level = ads.readADC_SingleEnded(1);
    adc_dump_level = analogRead(therm_pin2);
    delay(15);
    adc7_level_arduino = analogRead(therm_pin2);
    t_read_step = 5;    
    break;
  case 5:
    adc_dump_level = ads.readADC_SingleEnded(1);
    delay(15);
    adc1_level = ads.readADC_SingleEnded(1);
    t_read_step = 3;
    break;
//  case 6:
//    adc_dump_level = ads.readADC_SingleEnded(2);
//    delay(15);
//    adc2_level = ads.readADC_SingleEnded(2);
//    t_read_step = 3;
//    break;
    
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

//if (index_temp>(numsamples-1)){
//  index_temp = 0;
//}
//if (index_temp2>(numsamples2-1)){
//  index_temp2 = 0;
//}

}


}

//An timer interruption handler to count which coil now should be tested, from
void Counter() {

if (coil_no>=0 && coil_no <3) {

coil_no++;

} else if (coil_no >=3) {

coil_no = 0;}

return;

}

//The function test() is just to set a counter and to determine which coil will be checked in this clock cycle
void test(int coil) {

double resistance = Read_Data(coil);

double threshold = 3.25; //The threshold value of the resistance of the coil at high temperature

if (resistance > threshold) {

digitalWrite(ArduinoLED, HIGH);

errormsg = 1;

Power_OFF();

} else {

}

return;

}

//When temperature is too high, the power supply is turned off and locked. Unless the flag is changed to 1, the power supply remains locked.
void Set_Flag() {

char *arg1;

//Get the next argument from the SerialCommand object buffer
arg1 = sCmd.next();

//Converts a char string to an integer or a number
errormsg = atoi(arg1);


if (errormsg==0) {

digitalWrite(ArduinoLED, LOW);
}
//Serial.println("\nFlag has been changed");

}

//The function below is to read the flag
void Read_Flag() {

Serial.print("Flag=");
Serial.print(errormsg);

}


void PSURead() {

char *arg1;
int Coil;
double Result;

//Get the next argument from the SerialCommand object buffer
arg1 = sCmd.next();

//Converts a char string to an integer or a number
Coil = atoi(arg1);

Result=Read_Data(Coil);

}

double Read_Data(int Coil){

int i,j = 0;
double voltage, current, resistance;
char voltage_str[5], current_str[6];
char voltage_read[4], current_read[5]; 

char *channelv [4] = {"V1O?\n","V2O?\n","V1O?\n","V2O?\n"};
char *channeli [4] = {"I1O?\n","I2O?\n","I1O?\n","I2O?\n"};

Coil_Write(Coil, channelv[Coil-1]);
//wait until the power supply returns a value
Coil_Read(Coil, voltage_str);

Coil_Write(Coil, channeli[Coil-1]);
//wait until the power supply returns a value
Coil_Read(Coil, current_str);

for(int m=0; m<4; m++){
  
  voltage_read[m]=voltage_str[m];
  
}

for(int n=0; n<5; n++){
  
  current_read[n]=current_str[n];
  
}

voltage = atof(voltage_read);
current = atof(current_read);

if (current >= 0.04){
  
  resistance = voltage / current;
  
}else {
  
  resistance = 3.0;}
  
return resistance;

}

void Coil_Write(int Coil, char* str) {

if (Coil == 1 || Coil == 2) Serial1.write(str);
if (Coil == 3 || Coil == 4) Serial2.write(str);

}

void Coil_Read(int Coil, char* str) {

int i = 0;

if (Coil == 1 || Coil == 2){
  
while (Serial1.available()){
  
Serial1.readBytesUntil(LF,str, 25);

}
}

if (Coil == 3 || Coil == 4){
  
while (Serial2.available()){

Serial2.readBytesUntil(LF,str, 25);

}
}

}

void PSUWrite(){

char *arg1, *arg2, *arg3, current_buffer[10];
int Coil;
double Current_value, Abs_value;
boolean Status; //test the input value

//Serial.println("\nIn process");

//Get the next argument from the SerialCommand object buffer
arg1 = sCmd.next();
arg2 = sCmd.next();

//Converts a char string to an integer or a number
Coil = atoi(arg1);
Current_value = atof(arg2);
Abs_value = sqrt(Current_value*Current_value); //take the abs value of the input value

//convert the number back to char string
dtostrf(Abs_value, 10, 3, current_buffer);
arg3= current_buffer;

//define the boolean of the value
if (Current_value >= 0) Status = false;

else Status = true;

Write_Data(Coil, Status, arg3);

}

void Write_Data (int Coil, boolean test, char *arg) {
  
//Serial.print(no_ps);

if (no_ps == 2) {
  
char *channeli_reset [4] = {"INST OUT1\n","INST OUT2\n","INST OUT3\n","INST OUT4\n"};
char *channeli [4] = {"INST OUT1\n","INST OUT2\n","INST OUT3\n","INST OUT4\n"};
char *currenti_reset = {"CURR 0.001\n"};
char *currenti = {"CURR "};
int relaypin[4] = {RelayPin1, RelayPin2, RelayPin3, RelayPin4};

False_Write_n (Coil, test, channeli[Coil-1], arg, channeli_reset[Coil-1], relaypin[Coil-1], currenti_reset, currenti);

} 

if (no_ps == 1) {
 
char *channeli_reset [4] = {"I1 0.001\n","I2 0.001\n","I1 0.001\n","I2 0.001\n"};
char *channeli [4] = {"I1 ","I2 ","I1 ","I2 "};

int relaypin[4] = {RelayPin1, RelayPin2, RelayPin3, RelayPin4};

// if (RelayState[Coil-1] == test) True_Write(Coil, channeli[Coil-1], arg);
// else

False_Write(Coil, test, channeli[Coil-1], arg, channeli_reset[Coil-1], relaypin[Coil-1]);

}



}

//Function False_Write_n and True_Write_n deals with the new power supply. We only use Serial1 to communicate.
void False_Write_n (int Coil, boolean test, char* str1, char* str2, char* str3, int pin, char* str4, char* str5) {

if (RelayState[Coil-1] == test){

True_Write_n(Coil, str1, str2, str5);}

else{

Serial1.write(str3);
Serial1.write(str4);
delay(100);
RelayState[Coil-1] = !RelayState[Coil-1]; //state change
digitalWrite(pin, RelayState[Coil-1]);
delay(100);
True_Write_n(Coil, str1, str2, str5);

}
}

void True_Write_n(int Coil, char* str1, char* str2, char* str5) {

Serial1.write(str1);
Serial1.write(str5);
Serial1.write(str2);
Serial1.write(10);

}

void True_Write(int Coil, char* str1, char* str2) {

if (Coil == 1 || Coil == 2) {

Serial1.write(str1);
Serial1.write(str2);
Serial1.write(10);

}

if (Coil == 3 || Coil == 4){

Serial2.write(str1);
Serial2.write(str2);
Serial2.write(10);

}

}

void False_Write (int Coil, boolean test, char* str1, char* str2, char* str3, int pin) {

if (RelayState[Coil-1] == test){

True_Write(Coil, str1, str2);}

else{

if (Coil == 1 || Coil == 2) {

//Serial1.write(str3);
//delay(100);
RelayState[Coil-1] = !RelayState[Coil-1]; //state change
digitalWrite(pin, RelayState[Coil-1]);
//delay(100);
delay(10);
True_Write(Coil, str1, str2);
}

if (Coil == 3 || Coil == 4){

//Serial2.write(str3);
//delay(100);
RelayState[Coil-1] = !RelayState[Coil-1]; //state change
digitalWrite(pin, RelayState[Coil-1]);
//delay(100);
delay(10);
True_Write(Coil, str1, str2);

}
}
}

//input four current for each coil
void Input_Current(){

char *arg[4], *arg3[4], current_buffer[10];

boolean Status[4]; //test the input value

//Serial.println("\nIn process");

double Current_Value[4], Abs_Value[4];

for (int n = 0; n<4; n++) {
  
   Current_Value[n] = atof(sCmd.next());
   
   Abs_Value[n] = sqrt(Current_Value[n]*Current_Value[n]); //take the abs value of the input value
   
   //convert the number back to char string
  dtostrf(Abs_Value[n], 10, 3, current_buffer);
  
  arg3[n]= current_buffer;

  //define the boolean of the value
  if (Current_Value[n] >= 0) Status[n] = false;

  else Status[n] = true;

  Write_Data(n+1, Status[n], arg3[n]);
  
  //Serial.println("\nIn process");
   
}

}


// This gets set as the default handler, and gets called when no other command matches.
void unrecognized(const char *command) {
Serial.println("Not a Valid Command");
}

//define a function to convert the number into a char array
char *dtostrf (double val, signed char width, unsigned char prec, char 
*sout) {
char fmt[20];
sprintf(fmt, "%%%d.%df", width, prec);
sprintf(sout, fmt, val);
return sout;
}

void Power_ON () {

if (errormsg == 0) {
  
  psstate = 1;
  
    if (no_ps == 1) {

Serial1.write("OP1 1");
Serial1.write(10);
//delay(20);

Serial2.write("OP1 1");
Serial2.write(10);
delay(85);

Serial1.write("OP2 1");
Serial1.write(10);
//delay(20);


Serial2.write("OP2 1");
Serial2.write(10);
//delay(20);
}

  if (no_ps == 2) {
    
    Serial1.write("OUTP:GEN ON\n");
//    Serial1.write("OUTP ON\n");
//    delay(50);
//
//    Serial1.write("INST OUT2\n");
//    Serial1.write("OUTP ON\n");
//    delay(50);
//
//    Serial1.write("INST OUT3\n");
//    Serial1.write("OUTP ON\n");
//    delay(50);
//
//    Serial1.write("INST OUT4\n");
//    Serial1.write("OUTP ON\n");
//    delay(50);
  }

} else if (errormsg ==1) {

//Serial.println("\nError.Power Supply is locked");

}

}

void Power_OFF () {

psstate = 0;

if (no_ps == 1) {

Serial1.write("OP1 0");
Serial1.write(10);
//delay(20);

Serial2.write("OP1 0");
Serial2.write(10);
delay(85);


Serial1.write("OP2 0");
Serial1.write(10);
//delay(20);

Serial2.write("OP2 0");
Serial2.write(10);
//delay(20);
}

if (no_ps == 2) {
  
    Serial1.write("OUTP:GEN OFF\n");
//    Serial1.write("OUTP OFF\n");
//    delay(50);
//    
//    Serial1.write("INST OUT2\n");
//    Serial1.write("OUTP OFF\n");
//    delay(50);
//    
//    Serial1.write("INST OUT3\n");
//    Serial1.write("OUTP OFF\n");
//    delay(50);
//    
//    Serial1.write("INST OUT4\n");
//    Serial1.write("OUTP OFF\n");
    //delay(50);
  }

}

void Set_Local () {
  
  if (no_ps == 1) {

delay(85); // be sure that no previous command is executed
Serial1.write("LOCAL");
Serial1.write(10);
//delay(20);

Serial2.write("LOCAL");
Serial2.write(10);
//delay(20);
}

if (no_ps == 2) {
  
  Serial1.write("SYSTem:LOCal");
  Serial1.write(10);
  delay(50);}


}

void Light_ON () {

Serial2.write("OP3 1");
Serial2.write(10);

}
void Light_OFF () {

Serial2.write("OP3 0");
Serial2.write(10);

}

//void Read_Temp_1(){
//  double average;
//  uint8_t i;
//  double resist, temper;
//  average=0.0; 
//  for(i=0;i<numsamples;i++){
//    average = average +(float) samples[i];
//  }  
//  average = average / (float) numsamples;
//  resist = convert_ADC_resist(average);
//  temper = fit_temp(resist);
//Serial.print("Analog reading ");
//Serial.println(average);  
//Serial.print("Thermistor resistance ");
//Serial.println(resist);
//Serial.print("Thermistor temperature ");
//Serial.println(round(temper*10.0)/10.0);
//}


void Read_Temp_1(){

  double adc_V;
  double resist, temper;
  adc_V = (float)adc0_level *0.125/1000.0;  
  resist = convert_ADC_resist(adc_V);
  temper = fit_temp(resist);

Serial.println(round(temper*10.0)/10.0);
}

double convert_ADC_resist(double level_ADC_V){
  double resis_temp;
  
  resis_temp = (3.3/ level_ADC_V)-1.0;
  resis_temp = res_ser/resis_temp;
  return resis_temp;
}
  
double convert_ADC_resist2(double level_ADC_Ard){
  double resis_temp;
  
  resis_temp = (4095.0/ level_ADC_Ard)-1.0;
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

void Read_Temp_2(){

  double adc_Ard;
  double resist, temper;
  adc_Ard = (float)adc7_level_arduino;  
  resist = convert_ADC_resist2(adc_Ard);
  temper = fit_temp(resist);


  Serial.println(round(temper*10.0)/10.0);

}



void Read_Temp_3(){

  double adc_V;
  double resist, temper;
  adc_V = (float)adc1_level *0.125/1000.0;  
  resist = convert_ADC_resist3(adc_V);
  temper = fit_temp(resist);

Serial.println(round(temper*10.0)/10.0);
}

double convert_ADC_resist3(double level_ADC_V){
  double resis_temp;
  
  resis_temp = (3.3/ level_ADC_V)-1.0;
  resis_temp = res_ser3/resis_temp;
  return resis_temp;
}

void Read_Temp_4(){

  double adc_V;
  double resist, temper;
  adc_V = (float)adc2_level *0.125/1000.0;  
  resist = convert_ADC_resist4(adc_V);
  temper = fit_temp(resist);

Serial.println(round(temper*10.0)/10.0);
}

double convert_ADC_resist4(double level_ADC_V){
  double resis_temp;
  
  resis_temp = (3.3/ level_ADC_V)-1.0;
  resis_temp = res_ser4/resis_temp;
  return resis_temp;
}



void General_Command2(){

char *arg1;
int j, k;

//Get the next argument from the SerialCommand object buffer
arg1 = sCmd.next();

Serial2.write(arg1);
Serial2.write(10);

delay(100);
j = Serial2.available();
//Serial.println(j);

while (Serial2.available()){

k = Serial2.read();
Serial.write(k);

}

}

void General_Command1(){

char *arg1;
int j, k;
//Serial.write("/n In progress");

//Get the next argument from the SerialCommand object buffer
arg1 = sCmd.next();

//Serial.println(arg1);

Serial1.write(arg1);
Serial1.write(10);

delay(100);
j = Serial1.available();
//Serial.println(j);

while (Serial1.available()){
k = Serial1.read();
Serial.write(k);
//Serial.println(k);


}

}

