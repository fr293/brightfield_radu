const double res_ser=9890.0;
const double res_ser2=9930.0;

const double aa0  = -9.155;
const double aa1  = 55.567;
const double aa2  = 46.733;
const double aa3  = 56.823;

const double tt1  = 537.10;
const double tt2  = 2577.64;
const double tt3  = 18627.4;


#define therm_pin  A0
#define therm_pin2  A7
#define numsamples 50

int samples[numsamples];
int samples2[numsamples];




void setup() {
  analogReadResolution(12);
  Serial.begin(19200);
  
}


void loop() {

  int volt_level;
  int volt_level2;
  double average;
  double average2;
  uint8_t i;
  
  double resist, temper;
  double resist2, temper2;
  
  for(i=0;i<numsamples;i++){
    samples[i] = analogRead(therm_pin);
    samples2[i] = analogRead(therm_pin2);
    delay(2);
  }
  
  average=0.0;
  average2=0.0;
  
  for(i=0;i<numsamples;i++){
    average = average +(float) samples[i];
    average2 = average2 +(float) samples2[i];
  }
  
  average = average / (float) numsamples;
  average2 = average2 / (float) numsamples;
  
  
  //volt_level = analogRead(therm_pin);
  
  //resist = convert_ADC_resist(volt_level);
  resist = convert_ADC_resist(average);
  resist2 = convert_ADC_resist2(average2);

  temper = fit_temp(resist);
  temper2 = fit_temp(resist2);

 Serial.print("Analog reading ");
 Serial.println(average);  
 
 Serial.print("Analog reading 2 ");
 Serial.println(average2);  
 
   //Serial.print("Thermistor resistance ");
   //Serial.println(resist);

   Serial.print("Thermistor temperature ");
   Serial.println(round(temper*10.0)/10.0);

   Serial.print("Thermistor temperature 2 ");
   Serial.println(round(temper2*10.0)/10.0);
  
  delay(3000);
  
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
  
  
