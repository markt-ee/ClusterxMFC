/*
This code controls 4 potentiometers with 1 esp32
pot0 to pot3 
*/

#include <WiFi.h>
//const char* ssid = "TP-Link_8FE0";
//const char* password = "TimmysDisciples";

const char* ssid = "MyCafe2.4";
const char* password = "passwordapa";
WiFiServer server(1234);


int steps_delta = 0;
int steps_0 = 0;


//GPIO PINS
//POT0, POT3
//pot 1const int is a read only variable
const int CS = 5; const int CS1 = 36; const int CS2 = 32; const int CS3 = 14;
const int INC = 18; const int INC1 = 39; const int INC2 = 33; const int INC3 = 12;
const int UD = 22; const int UD1 = 34;const int UD2 = 25; const int UD3 = 13;
const int PWR = 19; const int PWR1 = 32; const int PWR2 = 26; const int PWR3 = 27;


// Time Delay // Do we need this delay? 
const int incDelay = 5;
const int csDelay = 5;
const int currentStep = 0;
// Initialize the potentiometer

void setup() {
  // baud rate
  Serial.begin(115200);

  // set up wifi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
  



  // Sets control pins as outputs
  pinMode(CS, OUTPUT);   pinMode(CS1, OUTPUT);   pinMode(CS2, OUTPUT);   pinMode(CS3, OUTPUT);
  pinMode(INC, OUTPUT);   pinMode(INC1, OUTPUT);   pinMode(INC2, OUTPUT);   pinMode(INC3, OUTPUT); //direction for inc or dec
  pinMode(UD, OUTPUT);   pinMode(UD1, OUTPUT);   pinMode(UD2, OUTPUT);   pinMode(UD3, OUTPUT); //direction for inc or dec
  pinMode(PWR,OUTPUT);  pinMode(PWR1,OUTPUT);   pinMode(PWR2,OUTPUT);  pinMode(PWR3,OUTPUT);//use GPIO for PWR 3.3 to enable open ckt 



  // They are Active Low??
  // Idle state
  digitalWrite(PWR, LOW);  digitalWrite(PWR1, LOW);  digitalWrite(PWR2, LOW);  digitalWrite(PWR3, LOW);// PWR LOW for open ckt
  digitalWrite(INC, HIGH);  digitalWrite(INC1, HIGH); digitalWrite(INC2, HIGH); digitalWrite(INC3, HIGH); //INC activelow?
  delay(incDelay);
  digitalWrite(CS, HIGH); digitalWrite(CS1, HIGH);digitalWrite(CS2, HIGH);digitalWrite(CS3, HIGH);// CS Active low chip deselected
  delay(csDelay);
  Serial.println("Enter number of steps to increment:");
}


void incResistance(int steps){ // 100 steps
  digitalWrite(UD, HIGH); // sets direction to inc
  digitalWrite(CS, LOW); // enable chip

  for (int i=0; i < steps; i++ ){

    // trigger falling edge to enable increment
    digitalWrite(INC, HIGH); // Toggle INC pin
    delay(incDelay);
    digitalWrite(INC, LOW); // at falling edge, inc happens
    delay(incDelay);
  }

  digitalWrite(INC, HIGH);
  delay(incDelay);
  digitalWrite(CS, HIGH);  //CS High both Inc and Dec
  delay(csDelay);
}


void decResistance(int steps){ // 100 steps
  digitalWrite(UD, LOW); // sets direction to dec
  digitalWrite(CS, LOW); // enable chip DECREASE LOW
  for (int i=0; i < steps; i++ ){

    //trigger falling edge to enable icrement
    digitalWrite(INC, HIGH); // Toggle INC pin
    delay(incDelay);
    digitalWrite(INC, LOW); // at falling edge, inc happens
    delay(incDelay);
  }
  
  digitalWrite(INC, HIGH);
  delay(incDelay);
  digitalWrite(CS, HIGH);  //CS HIGH both Inc and Dec
  delay(csDelay);
  
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client connected");
    while (client.connected()) {
      if (client.available()) {

        String command = client.readStringUntil('\n');
        client.println("Command received: " + command);
        Serial.print("Received command: ");
        Serial.println(command);
        command.trim();

        if (command.startsWith("pot ")) {
          int steps = command.substring(4).toInt();
          steps_delta = steps - steps_0;

          if (command == "pot off"){ //steps = 0
            Serial.println("enabling open circuit");
            Serial.println(steps);
            digitalWrite(PWR, LOW);
            Serial.println("enabling open circuit");
            steps_0 = 0;  // Reset to avoid confusion
            return;
          }

          else if (command == "pot 0"){
            //steps = 0 
            digitalWrite(PWR, HIGH);
            Serial.println("set to 40 ohms from open ckt");
            decResistance(100);
            steps_0 = 0;
          }

          else if (steps_delta < 0) {
          digitalWrite(PWR, HIGH);
          decResistance(abs(steps_delta));
          }

          else if (steps_delta > 0) {
          digitalWrite(PWR, HIGH);
          incResistance(steps_delta);
          }

        steps_0 = steps;
        Serial.print("steps= ");
        Serial.println(steps);
        client.println("Ready for command");
        }
        else {
        Serial.println("Invalid command. Use format: pot <steps>");
        client.println("Ready for command");
        }
      }


      }
    }
    client.stop();

  
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    Serial.println("command received, please wait");
    input.trim();

    if (input.startsWith("pot ")) {
      int steps = input.substring(4).toInt();
      steps_delta = steps - steps_0;

      if (input == "pot off"){
        //this autosets steps = 0
        Serial.println("enabling open circuit");
        Serial.println(steps);
        digitalWrite(PWR, LOW);
        delay(1);
        steps_0 = 0;
        return;
        // Reset to avoid confusion
      }

      else if (input == "pot 0"){
        //steps = 0 
        digitalWrite(PWR, HIGH);
        Serial.println("set to 40 ohms from open ckt");
        decResistance(100);
        steps_0 = 0;
      }

      else if (steps_delta < 0) {
        digitalWrite(PWR, HIGH);
        decResistance(abs(steps_delta));
      }

      else if (steps_delta > 0) {
        digitalWrite(PWR, HIGH);
        incResistance(steps_delta);
      }
      steps_0 = steps;
      Serial.print("steps= ");
      Serial.println(steps);
      Serial.println("Ready for command");

    } else {
      Serial.println("Invalid command. Use format: pot <steps>");
      Serial.println("Ready for command");
    }
  }
  }


