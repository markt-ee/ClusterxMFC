

#include <WiFi.h>
const char* ssid = "TP-Link_8FE0";
const char* password = "TimmysDisciples";
WiFiServer server(1234);


int steps_delta = 0;
int steps_0 = 0;


const int CS = 5; //const int is a read only variable
const int INC = 18;
const int UD = 22;
const int PWR = 17;
// Time Delay
const int incDelay = 100;
const int csDelay = 100;
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
  pinMode(CS, OUTPUT);
  pinMode(INC, OUTPUT);
  pinMode(UD, OUTPUT); //direction for inc or dec
  pinMode(PWR,OUTPUT);
  // They are Active Low
  // Idle state
  digitalWrite(PWR, HIGH); // Open circuit (MOSFET off)
  digitalWrite(INC, HIGH);
  delay(incDelay);
  digitalWrite(CS, HIGH); // chip deselected
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
 // Serial.print("Incremented ");
 // Serial.print(steps);
 // Serial.println(" steps.");
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
  // Serial.print("Decremented ");
  // Serial.print(steps);
  // Serial.println(" steps.");
  
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

          if (command == "pot off"){
          Serial.println("enabling open circuit");
          digitalWrite(PWR, LOW);
          }

          if (steps_delta < 0) {
          digitalWrite(PWR, HIGH);
          decResistance(abs(steps_delta));
          }

          if (steps_delta > 0) {
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
        Serial.println("enabling open circuit");
        digitalWrite(PWR, LOW);
      }

      if (steps_delta < 0) {
        digitalWrite(PWR, HIGH);
        decResistance(abs(steps_delta));
      }

      if (steps_delta > 0) {
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


