/*
 * Project: LED Blinking Circuit
 * Description: This code controls an LED connected to an Arduino digital pin,
 *              making it blink on and off at a regular interval (1 second).
 */

// pin_definitions.h (Included in main_code.ino)
// Define the pin to which the LED is connected
const int ledPin = 13;  // Digital pin 13

// setup() function
void setup() {
  // Configure the LED pin as an output
  pinMode(ledPin, OUTPUT);
}

// loop() function
void loop() {
  // Turn the LED on (HIGH is the voltage level)
  digitalWrite(ledPin, HIGH);
  // Wait for 1000 milliseconds (1 second)
  delay(1000);
  // Turn the LED off (LOW is the voltage level)
  digitalWrite(ledPin, LOW);
  // Wait for 1000 milliseconds (1 second)
  delay(1000);
}