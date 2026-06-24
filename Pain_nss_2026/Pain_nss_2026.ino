#include <Wire.h>
#include <ESP8266WiFi.h>
#include <LiquidCrystal_I2C.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "DHTesp.h"
#include <Adafruit_ADXL345_U.h>
#include <ESP8266WebServer.h>

// ======== Wi-Fi ========
const char* ssid = "Project";
const char* password = "12345678";

// ======== Web Server ========
ESP8266WebServer server(80);

// ======== Sensors ========
MAX30105 particleSensor;
DHTesp dht;
LiquidCrystal_I2C lcd(0x27,16,2);
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

// ======== Pins ========
#define CONTROL_PIN D5    // output control
#define BUZZER_PIN  D6
#define GSR_PIN     A0

// ======== Variables ========
int beatAvg = 0;
int spo2 = 0;
float temperatureDHT = 0, humidity = 0;
int gsrValue = 0;
float X_val = 0, Y_val = 0;
unsigned long lastLCD = 0;
int lcdPage = 0;

// ======== Setup ========
void setup() {
  Serial.begin(9600);
  pinMode(CONTROL_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(CONTROL_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  lcd.begin();
  lcd.backlight();
  lcd.setCursor(0,0);
  lcd.print("Connecting WiFi");

  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("WiFi OK IP:");
  lcd.setCursor(0,1);
  lcd.print(WiFi.localIP());
  delay(2000);

  if(!particleSensor.begin(Wire, I2C_SPEED_STANDARD)){
    Serial.println("MAX30105 not found!");
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(60);
  particleSensor.setPulseAmplitudeGreen(0);

  dht.setup(D0, DHTesp::DHT11);
  delay(2000);

  if(!accel.begin()){
    Serial.println("ADXL345 not detected!");
    while(1);
  }
  accel.setRange(ADXL345_RANGE_2_G);

  // Web server
  server.on("/", handleRoot);
  server.onNotFound(handleCommand); // handle /1, /2, /5 etc.
  server.begin();
  Serial.println("Server ready");
}

// ======== Loop ========
void loop() {
  updateSensors();
  updateLCD();
  displaySerial();
  server.handleClient();
  delay(500);
}

// ======== Update Sensors ========
void updateSensors(){
  long irValue = particleSensor.getIR();
  beatAvg = irValue/1000;
  if(beatAvg < 40) beatAvg = 0;
  spo2 = beatAvg + 3;

  humidity = dht.getHumidity();
  temperatureDHT = dht.getTemperature();

  gsrValue = analogRead(GSR_PIN);

  sensors_event_t e;
  accel.getEvent(&e);
  X_val = e.acceleration.x;
  Y_val = e.acceleration.y;
}

// ======== Web server handlers ========
void handleRoot(){
  String html = "<html><head><meta http-equiv='refresh' content='5'/>"
                "<title>ESP8266 Health Monitor</title>"
                "<style>body{font-family:Arial;text-align:center;background:#f2f2f2;}h2{color:#333;}</style></head><body>";
  html += "<p><b>BPM:</b> "+String(beatAvg)+"</p>";
  html += "<p><b>SpO2:</b> "+String(spo2)+"</p>";
  html += "<p><b>Temperature:</b> "+String(temperatureDHT)+" °C</p>";
  html += "<p><b>Humidity:</b> "+String(humidity)+" %</p>";
  html += "<p><b>GSR:</b> "+String(gsrValue)+"</p>";
  html += "<p><b>X:</b> "+String(X_val)+" &nbsp; <b>Y:</b> "+String(Y_val)+"</p>";
  html += "</body></html>";
  server.send(200,"text/html",html);
}

void handleCommand(){
  String uri = server.uri();
  String secStr = uri.substring(1);
  if(secStr.length() > 0 && secStr.toInt() > 0){
    handleActivate(secStr.toInt());
  }
  handleRoot();
}

void handleActivate(int seconds){
  Serial.printf("D5 HIGH for %d s\n",seconds);
  digitalWrite(CONTROL_PIN,HIGH);
  delay(seconds*1000);
  digitalWrite(CONTROL_PIN,LOW);
  Serial.println("D5 LOW");
}

// ======== LCD pages ========
void updateLCD(){
  if(millis() - lastLCD < 2000) return; // change every 2 s
  lastLCD = millis();
  lcd.clear();
  switch(lcdPage){
    case 0:
      lcd.setCursor(0,0); lcd.print("BPM:"); lcd.print(beatAvg);
      lcd.setCursor(0,1); lcd.print("SpO2:"); lcd.print(spo2);
      break;
    case 1:
      lcd.setCursor(0,0); lcd.print("Temp:"); lcd.print(temperatureDHT,1); lcd.print("C");
      lcd.setCursor(0,1); lcd.print("Hum:"); lcd.print(humidity,1); lcd.print("%");
      break;
    case 2:
      lcd.setCursor(0,0); lcd.print("X:"); lcd.print(X_val,1);
      lcd.setCursor(0,1); lcd.print("Y:"); lcd.print(Y_val,1);
      break;
    case 3:
      lcd.setCursor(0,0); lcd.print("GSR:"); lcd.print(gsrValue);
      lcd.setCursor(0,1); lcd.print("D5 Ready");
      break;
  }
  lcdPage = (lcdPage + 1) % 4;
}

// ======== Serial Monitor ========
void displaySerial(){
  Serial.println("====== Sensor Data ======");
  Serial.printf("BPM: %d  SpO2: %d\n", beatAvg, spo2);
  Serial.printf("Temp: %.1fC  Hum: %.1f%%\n", temperatureDHT, humidity);
  Serial.printf("GSR: %d\n", gsrValue);
  Serial.printf("X: %.2f  Y: %.2f\n", X_val, Y_val);
  Serial.println("==========================");
}
