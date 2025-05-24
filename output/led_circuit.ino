// Author: Bard
// Date: October 26, 2023


// 1. Pin Definitions

#define LED_PIN 13  // Define the digital pin connected to the LED (can be changed)


// 2. Global Constants

const int BLINK_INTERVAL = 1000; // Define the blink interval in milliseconds (1000ms = 1 second)


// 3. Function Prototypes (None needed for this simple example)



// 4. Setup Function

void setup() {
  // Configure the LED pin as an output
  pinMode(LED_PIN, OUTPUT);
}


// 5. Loop Function

void loop() {
  // Turn the LED on
  digitalWrite(LED_PIN, HIGH); // Set the LED pin to HIGH (5V) to turn the LED on
  delay(BLINK_INTERVAL);      // Wait for the specified blink interval (1 second)

  // Turn the LED off
  digitalWrite(LED_PIN, LOW);  // Set the LED pin to LOW (0V) to turn the LED off
  delay(BLINK_INTERVAL);      // Wait for the specified blink interval (1 second)
}


// 6. Additional Functions (None needed for this simple example)


/*
 * Usage Instructions:
 * 1.  Connect the LED to the Arduino board:
 *     - Connect the positive (anode) leg of the LED to the digital pin defined by LED_PIN (default: pin 13) through a 220 Ohm resistor.
 *     - Connect the negative (cathode) leg of the LED to the Arduino's GND (ground) pin.
 *
 * 2.  Upload the code to the Arduino board:
 *     - Open the Arduino IDE.
 *     - Copy and paste this code into the Arduino IDE.
 *     - Select the correct board and port from the "Tools" menu.
 *     - Click the "Upload" button to upload the code to the Arduino board.
 *
 * 3.  The LED should now blink with a 1-second interval (1 second ON, 1 second OFF).
 *
 * Code Comments:
 * - The code defines the LED pin using a #define statement for easy modification.
 * - The setup() function configures the LED pin as an output.
 * - The loop() function repeatedly turns the LED on and off with a 1-second delay in between.
 * - The delay() function pauses the program execution for the specified time in milliseconds.
 *
 * Circuit Information:
 * - Arduino Uno (or equivalent)
 * - LED (Standard 5mm Red LED)
 * - Resistor (220 Ohm, 1/4W)
 * - Jumper wires
 * - Breadboard (optional)
 *
 * Schematic:
 *  [Arduino Digital Pin 13] -- [220 Ohm Resistor] -- [LED Anode (+)]
 *  [LED Cathode (-)] -- [Arduino GND]
 *
 * Resistor Calculation:
 * - The 220 Ohm resistor limits the LED current to approximately 13.6mA, calculated as follows:
 *   (5V - 2V) / 220 Ohms = 0.0136A = 13.6mA.  This is within the safe operating range for a standard 5mm LED.
 *   (Assuming a forward voltage of 2V for the LED)
 *
 *  Pin Definitions:
 *  - LED_PIN: Digital pin connected to the LED.  Default is pin 13.
 *
 *  Alternative Implementations:
 *  - Use millis() for non-blocking delays if other tasks need to be performed concurrently.
 *  - Use PWM to control the LED brightness.
 */