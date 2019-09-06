const double res_ser=9890.0;

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




void setup() {
  analogReadResolution(12);
  Serial.begin(9600);
  
}


void loop() {

  int volt_level;
  double average;
  uint8_t i;
  
  double resist, temper;
  
  for(i=0;i<numsamples;i++){
    samples[i] = analogRead(therm_pin);
    delay(2);
  }
  
  average=0.0;
  
  for(i=0;i<numsamples;i++){
    average = average +(float) samples[i];
  }
  
  average = average / (float) numsamples;
  
  
  //volt_level = analogRead(therm_pin);
  
  //resist = convert_ADC_resist(volt_level);
  resist = convert_ADC_resist(average);

  temper = fit_temp(resist);

 Serial.print("Analog reading ");
 Serial.println(average);  
  
   //Serial.print("Thermistor resistance ");
   //Serial.println(resist);

   Serial.print("Thermistor temperature ");
   Serial.println(round(temper*10.0)/10.0);
  
  delay(3000);
  
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
  
  
  
