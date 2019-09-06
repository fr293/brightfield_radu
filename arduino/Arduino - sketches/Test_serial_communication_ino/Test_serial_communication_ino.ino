void setup() {
  // put your setup code here, to run once:
Serial1.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(1000);
  Serial1.write("I1 0.22");
  Serial1.write(10);
  delay(1000);
  Serial1.write("V1 1.45");
  Serial1.write(10);
  delay(1000);
  Serial1.write("I2 0.234");
  Serial1.write(10);
  delay(1000);
  Serial1.write("V2 1.432");
  Serial1.write(10);

  delay(1000);

}
