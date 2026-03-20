#include <SPI.h>
#include <RF24.h>

RF24 radio(9, 8);  // CE=D9, CSN=D8
const byte address[6] = "00001";

void setup() {
  Serial.begin(9600);
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_HIGH);
  radio.stopListening();  // TX mode
  Serial.println("TX Ready");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();  // Read single char, not String

    if (cmd == 'F' || cmd == 'B' || cmd == 'L' || cmd == 'R' || cmd == 'S') {
      char payload[2];
      payload[0] = cmd;
      payload[1] = '\0';
      radio.write(&payload, sizeof(payload));
      Serial.print("Sent: ");
      Serial.println(cmd);
    }
    // Any other character (like \n) is simply ignored
  }
}