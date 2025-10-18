/*
ESP8266 Potentiometer Server V1
Maria Katherine 18 OCT 2025
Supports multiple commands over a single TCP connection
Max steps: 0-99. do not go above 99
99: 10K
10: 1k 
1: 100
0: 40 ohms
connect to COM port, type in commands "pot <0-99>"
code is cleaner, serial and wifi merged to one function
*/

#include <ESP8266WiFi.h>

// const char* ssid = "MyCafe2.4";
// const char* password = "passwordapa";

const char* ssid = "TP-Link_8FE0";
const char* password = "TimmysDisciples";

WiFiServer server(1234);

int steps_0 = 0;
bool potWasOff = false;

// GPIO pins
const int CS  = 15;  // D8
const int INC = 13;  // D7
const int UD  = 12;  // D6
const int PWR = 14;  // D5

const int incDelay = 1;
const int csDelay = 1;

void setup() {
  Serial.begin(115200);

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();

  // GPIO setup
  pinMode(CS, OUTPUT); 
  pinMode(INC, OUTPUT);
  pinMode(UD, OUTPUT);
  pinMode(PWR, OUTPUT);

  digitalWrite(PWR, LOW);
  digitalWrite(INC, HIGH);
  digitalWrite(CS, HIGH);
  delay(csDelay);

  Serial.println("Ready for commands");
}

void incResistance(int steps) {
  digitalWrite(UD, HIGH);
  digitalWrite(CS, LOW);
  for (int i = 0; i < steps; i++) {
    digitalWrite(INC, HIGH);
    delay(incDelay);
    digitalWrite(INC, LOW);
    delay(incDelay);
  }
  digitalWrite(INC, HIGH);
  digitalWrite(CS, HIGH);
}

void decResistance(int steps) {
  digitalWrite(UD, LOW);
  digitalWrite(CS, LOW);
  for (int i = 0; i < steps; i++) {
    digitalWrite(INC, HIGH);
    delay(incDelay);
    digitalWrite(INC, LOW);
    delay(incDelay);
  }
  digitalWrite(INC, HIGH);
  digitalWrite(CS, HIGH);
}

void processCommand(String command) {
  command.trim();

  if (command == "pot off") {
    Serial.println("Open circuit");
    digitalWrite(PWR, LOW);
    steps_0 = 0;
    potWasOff = true;
    return;
  }

  if (command == "pot 0") {
    Serial.println("Reset to 0 steps");
    digitalWrite(PWR, HIGH);
    decResistance(100);
    steps_0 = 0;
    potWasOff = false;
    return;
  }

  if (command.startsWith("pot ")) {
    int steps = command.substring(4).toInt();
    int delta = steps - steps_0;

    if (potWasOff) {
      Serial.println("Recovering from OFF");
      digitalWrite(PWR, HIGH);
      decResistance(100);
      potWasOff = false;
    }

    if (delta > 0) {
      incResistance(delta);
    } else if (delta < 0) {
      decResistance(-delta);
    }

    steps_0 = steps;
    Serial.printf("Now at step: %d\n", steps_0);
  } else {
    Serial.println("Invalid command");
  }
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    Serial.println("Client connected");

    while (client.connected()) {
      if (client.available()) {
        String command = client.readStringUntil('\n');
        if (command.length() > 0) {
          Serial.print("Received command: ");
          Serial.println(command);
          processCommand(command);
          client.println("OK"); // reply after each command
        }
      }
      delay(1); // small delay to avoid blocking
    }

    client.stop();
    Serial.println("Client disconnected");
  }
}
