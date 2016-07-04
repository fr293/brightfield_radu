#include <SPI.h>
#include <Wire.h>
#include <ctype.h>

int incomingByte = 0;   // for incoming serial data

bool rxFlag = 0;
bool cmdValid = 0;
bool cmdQuery = 0;
char rx[50];
char buf[50];
char bufFloat[20];

void setup() {
	Serial.begin(115200);
	Serial.println("Initialising");
}

void loop() {	
    if(Serial.available() > 0){
        // Read in string
        String rxstr = Serial.readStringUntil('\r\n');
        // Convert string to char array
        rxstr.toCharArray(rx,50);
        // Remove spaces
        deblank(rx);
        
        // Check rx is not too long
        Serial.println(strlen(rx));
        if (strlen(rx)<=22){
            Serial.println(rx);
            rxFlag = 1;
        }
        else{
            Serial.println("Error command string too long");
        }                
    }
    
    if (rxFlag == 1){
        cmdValid = 1;
        
        // Get axis address
        char rxAddr[3];
        strncpy(rxAddr,rx,2);
        rxAddr[2] = '\0';
        // Check axis address is a number
        if(isdigit(rxAddr[0])&&isdigit(rxAddr[1])){
            // Convert to int
            int addr = atoi(rxAddr);
            sprintf(buf,"Axis address: %02d",addr);
            Serial.println(buf);
        }
        else{
            Serial.println("Error: Axis address invalid");
            cmdValid = 0;
        }
        
        // Get command name
        char cmdName[3];
        strncpy(cmdName,rx+2,2);
        cmdName[3] = '\0';
        // Check command name is uppercase char
        if(isupper(cmdName[0])&&isupper(cmdName[1])){
            sprintf(buf,"Command name: %s",cmdName);
            Serial.println(buf); 
        }
        else{
            Serial.println("Error: Command name invalid");
            cmdValid = 0;
        }
        
        // Check if command is query
        if (rx[4] == '?'){
            if(rx[5] == '\0'){
                Serial.println("Command is query");
                cmdQuery = 1;
            }
            else{
                Serial.println("Error: Command syntax incorrect");
                cmdValid = 0;
            }
        }
        
        // Get numeric value
        char _cmdNum[18];
        strncpy(_cmdNum,rx+4,strlen(rx)-4);
        _cmdNum[strlen(rx)-4] = '\0';
        // Check if cmdNum is a valid number
        if(isdigit(_cmdNum[0])&&isdigit(_cmdNum[strlen(_cmdNum)-1])){
            double cmdNum = atof(_cmdNum);
            dtostrf(cmdNum, 13, 4, bufFloat);
            sprintf(buf, "Numeric value:%s\n", bufFloat);
            Serial.print(buf);
        }
        else{
            Serial.println("Error: Numeric value invalid");
        }
        
        rxFlag = 0;
    }

    /*
    String str;
    if(Serial.available() > 0)
    {
        str = Serial.readStringUntil('\n');
        Serial.println(str);
    }
    */

    /*
    char buf[20];
    char _buf[20];
    dtostrf(position, 8, 4, _buf);
	sprintf(buf, "x:   %s\n", _buf);
    Serial.println(buf);
    delay(1000);
    */
}

char* deblank(char *str)
{
  char *out = str, *put = str;

  for(; *str != '\0'; ++str)
  {
    if(*str != ' ')
      *put++ = *str;
  }
  *put = '\0';

  return out;
}
