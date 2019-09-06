/* Magnet Device Control Program Version 1.0.0

(C) Qian Cheng, 2014

 Power Suppy        Coil     Relay Pin Number

Serial 1 CH 1        1             47

Serial 1 CH 2        2             49

Serial 2 CH 1        3             51

Serial 2 CH 2        4             53 


*/

//include the libray 
#include <SerialCommand.h> //SerialCommand Library
#include <cstdlib>
#include <stdlib.h>

// Arduino pin for relay on board 1-4 for coil
#define arduino1 47 
#define arduino2 49 
#define arduino3 51 
#define arduino4 53 

SerialCommand sCmd; // The demo SerialCommand object

boolean bool1, bool2, bool3, bool4; //return the current state of the relay

boolean test; //test the input value

String readString; //feedback reading

char serialvalue1[10], serialvalue2[10];

void setup() {
  
  // Configure the onboard pin for output
  pinMode(arduino1, OUTPUT); 
  pinMode(arduino2, OUTPUT); 
  pinMode(arduino3, OUTPUT); 
  pinMode(arduino4, OUTPUT); 
  
  // default to relay switch off
  digitalWrite(arduino1, LOW); 
  digitalWrite(arduino2, LOW); 
  digitalWrite(arduino3, LOW); 
  digitalWrite(arduino4, LOW); 
  
  //get the current state of the switch
  bool1 = digitalRead(arduino1);
  bool2 = digitalRead(arduino2);
  bool3 = digitalRead(arduino3);
  bool4 = digitalRead(arduino4);
 
  Serial.begin(9600);
  Serial1.begin(9600);
  Serial2.begin(9600);

  // Setup callbacks for SerialCommand commands
  sCmd.addCommand("Read_Coil", Read_Coil); 
  sCmd.addCommand("Set_Current", Set_Current);
  sCmd.addCommand("Power_ON", Power_ON);
  sCmd.addCommand("Power_OFF", Power_OFF);
  
  sCmd.setDefaultHandler(unrecognized); // Handler for command that isn't matched
  
  while (! Serial);
  
  while (! Serial1);
  
  while (! Serial2);
    
 // Serial.println("Enter a command:");
  
 // Serial.println("** Set_Current x y ** Read_Coil x ** (x:Coil ID y:Value)");
  
  
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
  
  Power_OFF();
  
  
  
}


void loop() {
  
  sCmd.readSerial(); // We don't do much, just process serial commands
  
}



void Read_Coil() {
  
  char *arg1;
  int Number1;
  
  Serial.println("\nIn process");
  
  //Get the next argument from the SerialCommand object buffer
   arg1 = sCmd.next();
   
  //Converts a char string to an integer or a number
  Number1 = atoi(arg1);
  
  int i,j = 0;
  
  char arg3[5], arg4[5];
  double num1, num2, resistance;
  
  //switch to each coil
  switch (Number1) {
    
  //Coil 1 Ch 1
    case 1:
    
    Serial1.write("V1?");
    Serial1.write(10);
 
   //wait until the power supply returns a value
    delay (20);
    
    while (Serial1.available()) {
  
    serialvalue1[i] =  Serial1.read();
   
    i++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue1);//voltage
    
    //delay(50);
        
    Serial1.write("I1?");
    Serial1.write(10);
    
    //wait until the power supply returns a value
    delay (20);
    
    while (Serial1.available()) {
  
    serialvalue2[j] =  Serial1.read();
   
    j++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue2);//current
    
    for (int m =0; m<5; m++) {
      
      arg3[m] = serialvalue1[m+3];
      
      arg4[m] = serialvalue2[m+3];
      
    }
    
    num1 = atof(arg3);
    
    num2 = atof(arg4);
    
    resistance = num1 / num2;
    
    Serial.println(num1,3);
    
    Serial.println(num2,3);
    
    Serial.println(resistance,3);
    
    break;
    
  //Coil 2 Ch 2
    case 2:
    
    Serial1.write("V2?");
    Serial1.write(10);
 
   //wait until the power supply returns a value
    delay (20);
    
    while (Serial1.available()) {
  
    serialvalue1[i] =  Serial1.read();
   
    i++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue1);//voltage
    
    //delay(50);
        
    Serial1.write("I2?");
    Serial1.write(10);
    
    //wait until the power supply returns a value
    delay (20);
    
    while (Serial1.available()) {
  
    serialvalue2[j] =  Serial1.read();
   
    j++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue2);//current
    
    for (int m =0; m<5; m++) {
      
      arg3[m] = serialvalue1[m+3];
      
      arg4[m] = serialvalue2[m+3];
      
    }
    
    num1 = atof(arg3);
    
    num2 = atof(arg4);
    
    resistance = num1 / num2;
    
    Serial.println(num1,3);
    
    Serial.println(num2,3);
    
    Serial.println(resistance,3);
    
    break;
    
    //Coil 3 Ch 1
    case 3:
    
    Serial2.write("V1?");
    Serial2.write(10);
 
   //wait until the power supply returns a value
    delay (20);
    
    while (Serial2.available()) {
  
    serialvalue1[i] =  Serial2.read();
   
    i++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue1);//voltage
    
    //delay(50);
        
    Serial2.write("I1?");
    Serial2.write(10);
    
    //wait until the power supply returns a value
    delay (20);
    
    while (Serial2.available()) {
  
    serialvalue2[j] =  Serial2.read();
   
    j++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue2);//current
    
    for (int m =0; m<5; m++) {
      
      arg3[m] = serialvalue1[m+3];
      
      arg4[m] = serialvalue2[m+3];
      
    }
    
    num1 = atof(arg3);
    
    num2 = atof(arg4);
    
    resistance = num1 / num2;
    
    Serial.println(num1,3);
    
    Serial.println(num2,3);
    
    Serial.println(resistance,3);
    
    break;
    
      //Coil 4 Ch 2
    case 4:
    
    Serial2.write("V2?");
    Serial2.write(10);
 
   //wait until the power supply returns a value
    delay (20);
    
    while (Serial2.available()) {
  
    serialvalue1[i] =  Serial2.read();
   
    i++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue1);//voltage
    
    //delay(50);
        
    Serial2.write("I2?");
    Serial2.write(10);
    
    //wait until the power supply returns a value
    delay (20);
    
    while (Serial2.available()) {
  
    serialvalue2[j] =  Serial2.read();
   
    j++;
    
    //delay(10);
    
    } 
    
    Serial.println(serialvalue2);//current
    
    for (int m =0; m<5; m++) {
      
      arg3[m] = serialvalue1[m+3];
      
      arg4[m] = serialvalue2[m+3];
      
    }
    
    num1 = atof(arg3);
    
    num2 = atof(arg4);
    
    resistance = num1 / num2;
    
    Serial.println(num1,3);
    
    Serial.println(num2,3);
    
    Serial.println(resistance,3);
    
    break;
    
    //default condition
    default:
    
    Serial.print("No coils matched.");
   
  }
    
}

void Set_Current() {
  
  char *arg1, *arg2, buffer[10], *arg3;
  int Number1;
  double Number2, Number3;
  
 //   Serial.println("\nIn process");
  
   //Get the next argument from the SerialCommand object buffer
   arg1 = sCmd.next();
   arg2 = sCmd.next();
   
   //Converts a char string to an integer or a number
   Number1 = atoi(arg1);
   Number2 = atof(arg2);
   Number3 = sqrt(Number2*Number2); //take the abs value of the input value
   
   //convert the number back to char string
   dtostrf(Number3, 10, 3, buffer);
   arg3= buffer;
   
   //define the boolean of the value
   if (Number2 >= 0) {
     
     test = false;
     
   } else{
     
     test = true;
     
   }
  
   //switch to each coil
    switch (Number1) {
    
    //Coil 1 Ch 1
    case 1:
    
    if (bool1 == test) {
      
    Serial1.write("I1 ");
    Serial1.write(buffer);
    Serial1.write(10);
  //  Serial.print(buffer);//(Number3);
    
    } else {
      
    Serial1.write("I1 0.001");  
    Serial1.write(10);  
   
    delay(100);
    
    bool1 =  !bool1; //state change
    digitalWrite(arduino1, bool1); // change the state of the relay
    
    delay(100);

    Serial1.write("I1 ");
    Serial1.write(buffer);
    Serial1.write(10);
  //  Serial.print(buffer);//(Number3);
  
    }  
    break;  
    
    //Coil 2 Ch 2
    case 2:
    
    if (bool2 == test) {
      
    Serial1.write("I2 ");
    Serial1.write(buffer);
    Serial1.write(10);
  //  Serial.print(buffer);//(Number3);
    
    } else {
      
    Serial1.write("I2 0.001");  
    Serial1.write(10);  
   
    delay(100);
    
    bool2 =  !bool2; //state change
    digitalWrite(arduino2, bool2); // change the state of the relay
    
    delay(100);

    Serial1.write("I2 ");
    Serial1.write(buffer);
    Serial1.write(10);
 //   Serial.print(buffer);//(Number3);
  
    }  
    break;  
 
    //Coil 3 Ch 1
    case 3:
    
    if (bool3 == test) {
      
    Serial2.write("I1 ");
    Serial2.write(buffer);
    Serial2.write(10);
 //   Serial.print(buffer);//(Number3);
    
    } else {
      
    Serial2.write("I1 0.001");  
    Serial2.write(10);  
   
    delay(100);
    
    bool3 =  !bool3; //state change
    digitalWrite(arduino3, bool3); // change the state of the relay
    
    delay(100);

    Serial2.write("I1 ");
    Serial2.write(buffer);
    Serial2.write(10);
 //   Serial.print(buffer);//(Number3);
  
    }  
    break;  
 
    //Coil 4 Ch 1
    case 4:
    
    if (bool4 == test) {
      
    Serial2.write("I2 ");
    Serial2.write(buffer);
    Serial2.write(10);
 //   Serial.print(buffer);//(Number3);
    
    } else {
      
    Serial2.write("I2 0.001");  
    Serial2.write(10);  
   
    delay(100);
    
    bool4 =  !bool4; //state change
    digitalWrite(arduino4, bool4); // change the state of the relay
    
    delay(100);

    Serial2.write("I2 ");
    Serial2.write(buffer);
    Serial2.write(10);
 //   Serial.print(buffer);//(Number3);
  
    }  
    break;  
  
    //default condition
    default:
    
    Serial.print("No coils matched.");
    
    }
    
}

// This gets set as the default handler, and gets called when no other command matches.
void unrecognized(const char *command) {
  Serial.println("Not a Valid Command");
}

//define a function to convert the number into a char array
char *dtostrf (double val, signed char width, unsigned char prec, char *sout) {
  char fmt[20];
  sprintf(fmt, "%%%d.%df", width, prec);
  sprintf(sout, fmt, val);
  return sout;
}

void Power_ON () {
 
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
}

void Power_OFF () {
 
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
