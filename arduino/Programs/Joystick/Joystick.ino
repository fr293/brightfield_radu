const int joyXPin=A1;
const int joyYPin=A0;

int joyXZero=512;
int joyYZero=512;
int joyX=joyXZero;
int joyY=joyYZero;


void setup() {
  Serial.begin(115200);
  Serial.println("Initialised");
}

void loop() {
  joyX=joyXZero-analogRead(joyXPin);
  joyY=analogRead(joyYPin)-joyYZero;
  Serial.print("X:");
  Serial.print(joyX,DEC);
  Serial.print("  Y:");
  Serial.println(joyY,DEC);
  delay(100);
}
  
