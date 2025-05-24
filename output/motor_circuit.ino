#include "pin_definitions.h"

// Define global variables
int motorSpeed = 0;       // Variable to store the motor speed (0-255)
int potValue = 0;         // Variable to store the potentiometer reading (0-1023)

// Function prototypes
void setMotorSpeed(int speed);
void setMotorDirection(int direction);

// setup() function - runs once at the beginning
void setup() {
  // Initialize serial communication for debugging
  Serial.begin(9600);
  Serial.println("DC Motor Control - Initialization");

  // Set pin modes for motor control pins
  pinMode(MOTOR_IN1_PIN, OUTPUT);
  pinMode(MOTOR_IN2_PIN, OUTPUT);
  pinMode(MOTOR_ENA_PIN, OUTPUT);
  pinMode(MOTOR_ENB_PIN, OUTPUT); // ENB is not used, but set as output to avoid floating pin

  // Initially stop the motor
  setMotorSpeed(0);
  setMotorDirection(0); // or 1, doesn't matter at start
  digitalWrite(MOTOR_ENB_PIN, HIGH); // Enable ENB if not used for other motor

  Serial.println("Motor and Pin Configuration Complete");
}

// loop() function - runs continuously
void loop() {
  // Read the potentiometer value
  potValue = analogRead(POT_PIN);

  // Map the potentiometer value (0-1023) to motor speed (0-255)
  motorSpeed = map(potValue, 0, 1023, 0, 255);

  // Set the motor speed
  setMotorSpeed(motorSpeed);

  // Control motor direction (example: change direction when potentiometer reaches midpoint)
  if (potValue > 512) {
    setMotorDirection(1); //Forward
  }