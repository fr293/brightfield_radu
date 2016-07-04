#ifndef ACTUATOR_GUI_h
#define ACTUATOR_GUI_h

#include <Arduino.h>

const int oledResetPin=0;

class menu{
	public:
		menu(String _menuTitle, String _menuItems[]);
		menu(String _menuTitle, String _menuItems[], int _cursorItems[]);
		String menuTitle;
		int titleLength;		//number of characters in title
		String menuItems[20];
		int itemsLength[20];	//number of characters in each menu item
		int cursorItems[20];	//which menu item each cursor item corresponds to
		int cursorLines[20];	//which line each cursor item is on
		int menuSize;
		int menuCursorSize;
		int menuCursorPosition=0;
		bool scrollInit=0;
		int titleScrollIndex=0;
	private:
};

extern menu mainMenu;
extern menu serialMenu;
extern menu homeMenu;
extern menu jogMenu;
extern menu moveAbsMenu;
extern menu moveRelMenu;
extern menu resetMenu;
extern menu functionsMenu;
extern menu settingsMenu;

class GUI : public Adafruit_SSD1306{
	public:
		const int displayHeight=64;
		const int displayWidth=128;
		const int titleTextHeight=16;
		const int titleTextWidth=12;
		const int standardTextHeight=8;
		const int standardTextWidth=6;
		
		const int cursorUpdateFreq=25;
		const int joyXPin=A1;
		const int joyYPin=A0;
		const int joyThreshold=20;
		const int joyXZero=512;
		const int joyYZero=512;
		const int joyDelay=200;

		const int buttonAPin=3;
		const int buttonBPin=2;
		const int debounceDelayA=200;
		const int debounceDelayB=200;
		
		const int scrollSpeed=400; //number of milliseconds between character shifts when scrolling
		const int flashSpeed=400; //number of milliseconds between cursor flashing
		
		GUI();
		void initialise();
		void menuDisplay(menu& _menu);		
		int joyRead(char axis);
		void cursorMove();
		void select();
		void back();
		void buttonA();
		void buttonB();

		int menuSelect[2]={0,0};
		int menuActive=-1;
		int cursorPosition;
		bool navigate=true;
		
		int menuSize;
		int menuCursorSize;
		
		int joyX;
		int joyY;
		long lastJoyTime=0;
		
		String status;
		String axisStatus[3];
	
	private:
		long lastDebounceTimeA;
		long lastDebounceTimeB;
		
		int maxTitleCharacters;
		int maxStandardCharacters;
		int maxLines;
		long scrollTimer;
		long titleScrollTimer;
		long flashTimer;
		int scrollbarShift=0;
		
		
};

#endif