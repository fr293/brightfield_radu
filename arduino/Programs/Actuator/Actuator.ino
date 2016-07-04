#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Actuator_GUI.h>

const int resetPin=0;
Adafruit_SSD1306 display(resetPin);
GUI gui;

String mainMenuItems[]={"Jog Axes","Move to Location","Reset Zero","Home Axes","Settings","\0"};
menu mainMenu("Main Menu",mainMenuItems);

String jogMenuItems[]={"Item1","Item2","Item3","Item4","Item5","\0"};
menu jogMenu("Jog Axes",jogMenuItems);

String moveMenuItems[]={"Item1","Item2","Item3","Item4","Item5","\0"};
menu moveMenu("Move to Location",moveMenuItems);

String settingsMenuItems[]={"Item1","Item2","Item3","Item4","Item5","\0"};
menu settingsMenu("Settings",settingsMenuItems);


const int buttonAPin=2;
const int buttonBPin=3;
const int debounceDelayA=200;
const int debounceDelayB=200;
int lastDebounceTimeA=0;
int lastDebounceTimeB=0;

const int joyXPin=A1;
const int joyYPin=A0;
const int joyThreshold=20;
int joyXZero=512;
int joyYZero=512;
int joyX=joyXZero;
int joyY=joyYZero;

String menuItems[]={"Main Menu","Jog Axes","Move to Location","Reset Zero","Home Axes","","Exit"};
const int menuSize=6;
int menuSelect=1;
const int navigateDelay=200;

void setup() {
	Serial.begin(115200);
	Serial.println("Initialising");
	
	attachInterrupt(buttonAPin,buttonA,RISING);
	attachInterrupt(buttonBPin,buttonB,RISING);
	
	//gui.initialise();
	
	displayInit();
	displayMenu();
	Serial.println("Initialised");
}

void loop() {
  cursorMove();
  displayMenu();
  delay(navigateDelay);
}

void displayInit(){
  display.begin(SSD1306_SWITCHCAPVCC, 0x3D);
  display.display();
  delay(1000);
}

void displayMenu(){  
  display.clearDisplay();
  display.setCursor(0,0);
  
  display.setTextSize(2);
  display.setTextColor(WHITE,BLACK);
  display.println(menuItems[0]);
  
  display.setTextSize(1);
  for(int i=1;i<=menuSize;i++){
    if(i==menuSelect){
      display.setTextColor(BLACK,WHITE);
    }
    display.println(menuItems[i]);
    display.setTextColor(WHITE,BLACK);
  }
  
  display.display();
}

void joyRead(){
  joyX=joyXZero-analogRead(joyXPin);
  joyY=analogRead(joyYPin)-joyYZero;
}

void cursorMove(){
	while(1){
		joyRead();
		if(joyY<-(512-joyThreshold)){      
			do{
				if(menuSelect==menuSize){
					menuSelect=1;
				}
				else{
					menuSelect++;
				}
			} while(menuItems[menuSelect]=="");
			break;
		}
		else if(joyY>512-joyThreshold){
			do{
				if(menuSelect==1){
					menuSelect=menuSize;
				}
				else{
					menuSelect--;
				}
			} while(menuItems[menuSelect]=="");
			break;
		}
	}
}

void buttonA(){
	if((millis()-lastDebounceTimeA)>debounceDelayA){
		Serial.println("Button A");
		lastDebounceTimeA=millis();
	}
}

void buttonB(){
	if((millis()-lastDebounceTimeB)>debounceDelayB){
		Serial.println("Button B");
		lastDebounceTimeB=millis();
	}
}
	
