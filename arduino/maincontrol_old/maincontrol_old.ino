

/* Magnet Device Control Program Version 2.3 - resistance check - remove / errors PSU

(C) Qian Cheng, 2014

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

const double aa0  = -9.155;
const double aa1  = 55.567;
const double aa2  = 46.733;
const double aa3  = 56.823;

const double tt1  = 537.10;
const double tt2  = 2577.64;
const double tt3  = 18627.4;

#define therm_pin  A0
#define numsamples 50

int samples[numsamples];

unsigned long previousMillis = 0;   //will store last time the resistance was recorded
const long interval = 10;            //interval at which to read temperature


SerialCommand sCmd; // The demo SerialCommand object

boolean RelayState[4]; //return the current state of the relay

int coil_no = 0;//a counter to decide which coil to be tested

int errormsg = 0; //a flag to determine whether the power supply is allowed to trun on or not, 1 for True(error)

int psstate = 0;

int index_temp = 0; // counter for temperature readings

void setup() {
uint8_t i;

// Increase the analog IN resolution from 10 to 12 bits 
analogReadResolution(12);
for(i=0;i<numsamples;i++){
  samples[i] = 2048; // init samples to a non zero value -> half of the 2^12
}

// Configure the onboard pin for output
pinMode(RelayPin1, OUTPUT);
pinMode(RelayPin2, OUTPUT);
pinMode(RelayPin3, OUTPUT);
pinMode(RelayPin4, OUTPUT);

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
Serial2.begin(19200);

while (! Serial);
while (! Serial1);
while (! Serial2);

// Setup callbacks for SerialCommand commands
sCmd.addCommand("PSURead",PSURead);
sCmd.addCommand("PSUWrite",PSUWrite);
sCmd.addCommand("Set_Local",Set_Local);
sCmd.addCommand("Power_ON", Power_ON);
sCmd.addCommand("Power_OFF", Power_OFF);
sCmd.addCommand("Set_flag", Set_Flag);
sCmd.addCommand("Read_flag", Read_Flag);
sCmd.setDefaultHandler(unrecognized); // Handler for command that isn't matched
sCmd.addCommand("Input_Current",Input_Current);
sCmd.addCommand("Light_ON",Light_ON);
sCmd.addCommand("Light_OFF",Light_OFF);
sCmd.addCommand("Temperature",Read_Temperature);
sCmd.addCommand("PSU_error",PSU_error);

Power_OFF(); // switch off all power supplies
// useful when resetting Arduino

Serial1.write("I1 0.001");
Serial1.write(10);
delay(20);

Serial1.write("I2 0.001");
Serial1.write(10);
delay(20);

Serial2.write("I1 0.001");
Serial2.write(10);
delay(20);

Serial2.write("I2 0.001");
Serial2.write(10);
delay(20);

//Serial.println("Program Starts");

//Timer1.attachInterrupt(Counter).start(100000);//Timer increment


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
samples[index_temp] = analogRead(therm_pin);
index_temp = index_temp +1;

if (index_temp>numsamples-1){
  index_temp = 0;
}
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

double threshold = 3.45; //The threshold value of the resistance of the coil at high temperature

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

char *channeli_reset [4] = {"I1 0.001\n","I2 0.001\n","I1 0.001\n","I2 0.001\n"};
char *channeli [4] = {"I1 ","I2 ","I1 ","I2 "};
int relaypin[4] = {RelayPin1, RelayPin2, RelayPin3, RelayPin4};

// if (RelayState[Coil-1] == test) True_Write(Coil, channeli[Coil-1], arg);
// else

False_Write(Coil, test, channeli[Coil-1], arg, channeli_reset[Coil-1], 
relaypin[Coil-1]);

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

void False_Write (int Coil, boolean test, char* str1, char* str2, char* 
str3, int pin) {

if (RelayState[Coil-1] == test){

True_Write(Coil, str1, str2);}

else{

if (Coil == 1 || Coil == 2) {

Serial1.write(str3);
delay(100);
RelayState[Coil-1] = !RelayState[Coil-1]; //state change
digitalWrite(pin, RelayState[Coil-1]);
delay(100);
True_Write(Coil, str1, str2);
}

if (Coil == 3 || Coil == 4){

Serial2.write(str3);
delay(100);
RelayState[Coil-1] = !RelayState[Coil-1]; //state change
digitalWrite(pin, RelayState[Coil-1]);
delay(100);
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

Serial1.write("OP1 1");
Serial1.write(10);
delay(20);

Serial1.write("OP2 1");
Serial1.write(10);
delay(20);

Serial2.write("OP1 1");
Serial2.write(10);
delay(20);

Serial2.write("OP2 1");
Serial2.write(10);
delay(20);

} else if (errormsg ==1) {

//Serial.println("\nError.Power Supply is locked");

}

}

void Power_OFF () {

psstate = 0;

Serial1.write("OP1 0");
Serial1.write(10);
delay(20);

Serial1.write("OP2 0");
Serial1.write(10);
delay(20);


Serial2.write("OP1 0");
Serial2.write(10);
delay(20);

Serial2.write("OP2 0");
Serial2.write(10);
delay(20);

}

void Set_Local () {

Serial1.write("LOCAL");
Serial1.write(10);
delay(20);

Serial2.write("LOCAL");
Serial2.write(10);
delay(20);

}

void Light_ON() {
  
Serial2.write("OP3 1");
Serial2.write(10);

}

void Light_OFF() {
  
Serial2.write("OP3 0");
Serial2.write(10);
}

void Read_Temperature(){

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

double convert_ADC_resist(double level_ADC){
  double resis_temp;
  
  resis_temp = (4095.0/ level_ADC)-1.0;
  resis_temp = res_ser/resis_temp;
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

void PSU_error(){
  
  char* ctr;
  char str[25];
  //char* str;
  double volt;
  int index;
  char string[5];
  //String str;
  
  index = 18;
  
  
  ctr = "*IDN?\n";
  Serial2.write(ctr);
  delay(50);
  //Serial.println( Serial2.available());
  
  //while (Serial2.available()){
    index = 3;
    index = Serial2.readBytesUntil(LF,str,25);
  //}
  Serial.print( ctr);
  Serial.println( index);
  
 // for (int n=0;n<5;n++){
  //  string[n] = str[n];
  //}
  
//  Serial.println( atoi(str));
Serial.println( str);

  //Serial.println( atof(string));
  
//  volt = Read_Data(3);
//  Serial.println( volt);
  
  
  
}

  

