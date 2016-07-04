#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <../Adafruit_GFX_Library/Adafruit_GFX.h>
#include <../Adafruit_SSD1306/Adafruit_SSD1306.h>
#include <Actuator_GUI.h>

//DEFINE MENUS//

String mainMenuItems[]={"Serial Mode\n","Home Axes\n","Jog Axes\n","Move Absolute\n","Move Relative\n","Reset Position\n","Other Functions\n","Settings\n","\0"};
menu mainMenu("Main Menu",mainMenuItems);

String serialMenuItems[]={" \n"," \n"," \n"," \n"," \n","\0"};
int serialCursorItems[]={-1};
menu serialMenu("Serial Mode",serialMenuItems,serialCursorItems);

String homeMenuItems[]={"x:    --.----\n","y:    --.----\n","z:    --.----\n","Home x","Home y","Home z\n","End x ","End y ","End z ","\0"};
int homeCursorItems[]={3,6,4,7,5,8,-1};
menu homeMenu("Home Axes",homeMenuItems,homeCursorItems);

String jogMenuItems[]={"x:    --.----","Jog x\n","y:    --.----","Jog y\n","z:    --.----","Jog z\n","\0"};
int jogCursorItems[]={1,3,5,-1};
menu jogMenu("Jog Axes",jogMenuItems,jogCursorItems);

String moveAbsMenuItems[]={"x:    --.----","Start\n","move:","--.----","Stop\n","y:    --.----\n","move:","--.----\n","z:    --.----\n","move:","--.----\n","\0"};
int moveAbsCursorItems[]={1,4,3,7,10,-1};
menu moveAbsMenu("Move Absolute",moveAbsMenuItems,moveAbsCursorItems);

String moveRelMenuItems[]={"x:    --.----","Start\n","move:","--.----","Stop\n","y:    --.----\n","move:","--.----\n","z:    --.----\n","move:","--.----\n","\0"};
int moveRelCursorItems[]={1,4,3,7,10,-1};
menu moveRelMenu("Move Relative",moveRelMenuItems,moveRelCursorItems);

String resetMenuItems[]={"x:    --.----","Zero x\n","y:    --.----","Zero y\n","z:    --.----","Zero z\n","\0"};
int resetCursorItems[]={1,3,5,-1};
menu resetMenu("Reset Position",resetMenuItems,resetCursorItems);

String functionsMenuItems[]={"Function 1\n","Function 2\n","Function 3\n","Function 4\n","Function 5\n","\0"};
menu functionsMenu("Other Functions",functionsMenuItems);

String settingsMenuItems[]={"Setting1","value\n","Setting2","value\n","Setting3","value\n","Setting4","value\n","Setting5","value\n","Setting6","value\n","Setting7","value\n","Setting8","value\n","Setting9","value\n","\0"};
int settingsCursorItems[]={1,3,5,7,9,11,13,15,17,-1};
menu settingsMenu("Settings",settingsMenuItems,settingsCursorItems);


	//GUI CLASS//

//GUI CLASS CONSTRUCTOR//
GUI::GUI() : Adafruit_SSD1306(oledResetPin){
	maxTitleCharacters=displayWidth/titleTextWidth;
	maxStandardCharacters=(displayWidth/standardTextWidth)-2;
	maxLines=((displayHeight-titleTextHeight)/standardTextHeight)-1;
}


//INITIALISE DISPLAY//
void GUI::initialise(){
	begin(SSD1306_SWITCHCAPVCC, 0x3D);
	display();
}


//RENDER AND DISPLAY ACTIVE MENU//
void GUI::menuDisplay(menu& _menu){
	bool scroll=false;		//character scroll flag
	bool titleScroll=false;	//title character scroll flag
	bool flash=true;		//flash flag
	String titleBuffer;		//buffer to store scrolling title text
	
	//Update Internal Counters
	if(navigate==true){								//if active menu has changed
		cursorPosition=_menu.menuCursorPosition;	//update current cursor position to previous cursor position stored in menu class
		menuSize=_menu.menuSize;					//update menu size
		menuCursorSize=_menu.menuCursorSize;		//update number of cursor items in menu
		
		scrollbarShift=0;							//reset shifter for menu scrolling
		_menu.titleScrollIndex=0;					//reset shifter for title character scrolling
		scrollTimer=millis();						//reset character scroll timer
		titleScrollTimer=millis();					//reset title scroll timer
		flashTimer=millis();						//reset flash timer
		navigate=false;
	}
	else{											//if active menu has not changed
		_menu.menuCursorPosition=cursorPosition;	//update cursor position stored in menu class to current cursor position
	}
	
	//Scroll Initialise
	if(_menu.scrollInit==false&&_menu.titleLength>maxTitleCharacters){		//if title text is too long to fit on screen
		_menu.menuTitle+=" // ";											//add a divider at the end of the title for scrolling
		_menu.titleLength=_menu.menuTitle.length();							//update number of characters in title
		_menu.scrollInit=true;												//set scroll initialise flag
	}
	
	//Character Scroll Timer
	if(millis()-scrollTimer>=scrollSpeed){		//character scroll timer
		scroll=true;							//set character scroll flag
		titleScroll=true;						//set title scroll flag
		scrollTimer=millis();					//reset timer
	}
	else{
		scroll=false;							//reset character scroll flag
		titleScroll=false;						//reset title scroll flag
	}
	
	//Title Scroll Timer - increases title scroll time if title text is at left justified (ie. home) position
	if(_menu.titleScrollIndex==0){
		if(millis()-titleScrollTimer>=scrollSpeed*7){	//title scroll timer - slower than character scroll timer
			titleScrollTimer=millis();					//reset title timer
			titleScroll=true;							//set title scroll flag
		}
		else{
			titleScroll=false;							//reset title scroll flag
		}
	}
	
	//Flash Timer
	if(millis()-flashTimer>=flashSpeed){		//flash timer
		flash=!flash;							//toggle flash
		flashTimer=millis();					//reset timer
	}
	
	//Title Scroll Shift
	if(titleScroll==true){
		if(_menu.titleScrollIndex<_menu.titleLength){
			_menu.titleScrollIndex++;					//shift title text along by one character
		}
		else{
			_menu.titleScrollIndex=0;					//shift back to zero if at end of title text
			titleScrollTimer=millis();
		}
	}
	
	//Title Scroll Buffer
	if(_menu.scrollInit){
		if((_menu.titleScrollIndex+maxTitleCharacters)<_menu.titleLength){				//display continuous title text
			titleBuffer=_menu.menuTitle.substring(_menu.titleScrollIndex,_menu.titleScrollIndex+maxTitleCharacters);
		}
		else if((_menu.titleScrollIndex+maxTitleCharacters)>=_menu.titleLength){		//display loops round to start of title text
			titleBuffer=_menu.menuTitle.substring(_menu.titleScrollIndex)+_menu.menuTitle.substring(0,maxTitleCharacters-(_menu.titleLength-_menu.titleScrollIndex));
		}
	}
	else{
		titleBuffer=_menu.menuTitle;
	}
	
	//Menu Scroll Shift
	if(_menu.menuSize>maxLines){
		int i=0;
		int j=0;
		if(_menu.cursorItems[_menu.menuCursorPosition]>maxLines-1){
			while(i<maxLines&&j<_menu.cursorItems[_menu.menuCursorPosition]+1){
				if(_menu.menuItems[_menu.cursorItems[_menu.menuCursorPosition]-j-1].endsWith("\n")==true){
					i++;
				}
				j++;
			}
		}
		if(j<maxLines){
			j=maxLines;
		}
		while(_menu.cursorItems[_menu.menuCursorPosition]-(j-1)>scrollbarShift){
			scrollbarShift++;
		}
		while(_menu.cursorItems[_menu.menuCursorPosition]<scrollbarShift){
			scrollbarShift--;
			while(scrollbarShift>0&&_menu.menuItems[scrollbarShift-1].endsWith("\n")==false){
			scrollbarShift--;
			}
		}
	}
	else{
		scrollbarShift=0;
	}
	
	//Clear Display and Print Title
	clearDisplay();				//clear previous contents of display buffer
	setTextWrap(false);			//do not allow text to automatically wrap into next line
	setCursor(0,0);				//set position of cursor
	setTextSize(2);				//set text size to title text
	setTextColor(WHITE);		//set text colour to white
	print(titleBuffer);			//print title text to display buffer
	drawFastHLine(0,titleTextHeight-2,displayWidth,WHITE);	//draw title text dividor
	
	//Menu Text Print
	setCursor(0,titleTextHeight);	
	setTextSize(1);
	for(int i=0;i<menuSize;i++){
		if((i+scrollbarShift)==_menu.cursorItems[_menu.menuCursorPosition]){
			if(flash==false&&menuActive!=-1){
				setTextColor(WHITE);
			}
			else{
				setTextColor(BLACK,WHITE);
			}
			print(_menu.menuItems[(i+scrollbarShift)]);
		}
		else{
			setTextColor(WHITE);
			print(_menu.menuItems[(i+scrollbarShift)]);
		}
		setTextColor(WHITE);
		if(_menu.menuItems[(i+scrollbarShift)].endsWith("\n")!=true){
			print(" ");
		}
	}
	
	//Scroll Indicator Triangles
	//Upper Triangle
	if(scrollbarShift!=0){
		fillTriangle(
			displayWidth-standardTextWidth-1,titleTextHeight+standardTextHeight,
			displayWidth-1,titleTextHeight+standardTextHeight,
			displayWidth-standardTextWidth/2-1,titleTextHeight+standardTextHeight/2,WHITE
		);
	}
	//Lower Triangle
	if(_menu.cursorLines[_menu.menuCursorSize-1]-(maxLines-1)>scrollbarShift){
		fillTriangle(
			displayWidth-standardTextWidth-1,displayHeight-standardTextHeight*2,
			displayWidth-1,displayHeight-standardTextHeight*2,
			displayWidth-standardTextWidth/2-1,displayHeight-standardTextHeight*2+standardTextHeight/2,WHITE
		);
	}
	
	//Status Information
	fillRect(0,displayHeight-standardTextHeight,displayWidth,standardTextHeight,BLACK);
	drawFastHLine(0,displayHeight-standardTextHeight,displayWidth,WHITE);
	setCursor(0,displayHeight-standardTextHeight+1);
	setTextColor(WHITE);
	print(status);
	setCursor(displayWidth-standardTextWidth*9,displayHeight-standardTextHeight+1);
	print("|");
	print(axisStatus[0]);
	print("|");
	print(axisStatus[1]);
	print("|");
	print(axisStatus[2]);
	
	display();
}


//READ JOYSTICK VALUE//
int GUI::joyRead(char axis){
	joyX=joyXZero-analogRead(joyXPin);
	joyY=analogRead(joyYPin)-joyYZero;
	switch(axis){
		case 'x': return joyX;
		case 'y': return joyY;
		default: return 0;
	}
}


//READ JOYSTICK FOR CURSOR MOVEMENT//
void GUI::cursorMove(){
	if(menuActive!=-1){		//disable cursor movement when menu is active 
		return;
	}
	if((millis()-lastJoyTime)>joyDelay){
		if(joyRead('y')<-(512-joyThreshold)){
			lastJoyTime=millis();
			if(cursorPosition==menuCursorSize-1){
				cursorPosition=0;
			}
			else{
				cursorPosition++;
			}
		}
		else if(joyRead('y')>512-joyThreshold){
			lastJoyTime=millis();
			if(cursorPosition==0){
				cursorPosition=menuCursorSize-1;
			}
			else{
				cursorPosition--;
			}
		}
	}
}


//NAVIGATION LOGIC FOR "SELECT" BUTTON//
void GUI::select(){
	switch(menuSelect[0]){
		case 0:		//MAIN MENUS
			navigate=true;
			switch(menuSelect[1]){
				case 0:		//Start Screen
					menuSelect[0]=0;	//go to Main Menu: [0][1]
					menuSelect[1]=1;
					break;
				case 1:		//Main Menu
					menuSelect[0]=1;	//go to Sub Menus: [1][x]
					menuSelect[1]=cursorPosition;
				break;
			}
			break;
		case 1:		//SUB MENUS
			switch(menuSelect[1]){
				case 0: 	//Serial Mode
					break;
				case 1: 	//Home Axes
					menuActive=cursorPosition;	//activates Homing
					break;
				case 2:		//Jog Axes
					menuActive=cursorPosition;	//activates Jog
					break;
				case 3:		//Move Absolute
					menuActive=cursorPosition;	//activates Move Absolute
					break;
				case 4:		//Move Relative
					break;
				case 5:		//Reset Position
					menuActive=cursorPosition;	//activates Reset
					break;
				case 6:		//Other Functions
					break;
				case 7:		//Settings
					break;
			}
			break;
	}
}


//NAVIGATION LOGIC FOR "BACK" BUTTON//
void GUI::back(){
	navigate=true;
	if(menuActive!=-1){
		menuActive=-1;
	}
	else{
		menuSelect[0]=0;	//go to Main Menu: [0][1]
		menuSelect[1]=1;
	}
}


//BUTTON A INTERRUPT HANDLER
void GUI::buttonA(){
	if((millis()-lastDebounceTimeA)>debounceDelayA){
		Serial.println("Button A");
		lastDebounceTimeA=millis();
		select();
	}
}


//BUTTON B INTERRUPT HANDLER
void GUI::buttonB(){
	if((millis()-lastDebounceTimeB)>debounceDelayB){
		Serial.println("Button B");
		lastDebounceTimeB=millis();
		back();
	}
}


	//MENU CLASS//

//MENU CLASS CONSTRUCTOR//
//Without specification of which items to highlight with cursor
menu::menu(String _menuTitle, String _menuItems[]){
	int _cursorLines[20];
	
	menuTitle=_menuTitle;
	titleLength=menuTitle.length();
	
	int i=0;
	while(_menuItems[i]!="\0"){
		menuItems[i]=_menuItems[i];
		itemsLength[i]=menuItems[i].length();
		i++;
	}
	menuSize=i;
	
	for(int j=0;j<menuSize;j++){
		cursorItems[j]=j;
	}
	
	menuCursorSize=menuSize;
	
	int j=0;
	for(int k=0;k<menuSize;k++){
		_cursorLines[k]=j;
		if(menuItems[k].endsWith("\n")){
			j++;
		}
	}
	
	for(int k=0;k<menuCursorSize;k++){
		cursorLines[k]=_cursorLines[cursorItems[k]];
	}
}


//MENU CLASS CONSTRUCTOR//
//With specification of which items to highlight with cursor
menu::menu(String _menuTitle, String _menuItems[],int _cursorItems[]){
	int _cursorLines[20];
	
	menuTitle=_menuTitle;
	titleLength=menuTitle.length();
	
	int i=0;
	while(_menuItems[i]!="\0"){
		menuItems[i]=_menuItems[i];
		itemsLength[i]=menuItems[i].length();
		i++;
	}
	menuSize=i;
	
	int j=0;
	while(_cursorItems[j]!=-1){
		cursorItems[j]=_cursorItems[j];
		j++;
	}
	
	if(_cursorItems[0]==-1){
		cursorItems[0]=-1;
		j=1;
	}
	
	menuCursorSize=j;
	
	int l=0;
	for(int k=0;k<menuSize;k++){
		_cursorLines[k]=l;
		if(menuItems[k].endsWith("\n")){
			l++;
		}
	}
	
	for(int k=0;k<menuCursorSize;k++){
		cursorLines[k]=_cursorLines[cursorItems[k]];
	}
}