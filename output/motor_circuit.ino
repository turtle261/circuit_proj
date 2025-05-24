// --- Motor Control Project Code ---

// --- 1. Pin Definitions ---
#define MOTOR_IN1 2       // L298N Input 1
#define MOTOR_IN2 3       // L298N Input 2
#define MOTOR_ENA 9       // L298N Enable A (PWM for speed)
#define POT_PIN A0        // Potentiometer Analog Input
#define LED_PIN 13        // LED Indicator

// --- 2. Global Variables ---
int motorSpeed = 0;       // Motor speed (0-255)
int potValue = 0;         // Potentiometer reading (0-1023)

// --- 3. Setup Function ---
void setup() {
  // Initialize serial communication for debugging
  Serial.begin(9600);

  // Set pin modes
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  Serial.println("Motor control started");
}

// --- 4. Loop Function ---
void loop() {
  // Read potentiometer value
  potValue = analogRead(POT_PIN);

  // Map potentiometer value to motor speed (0-255)
  motorSpeed = map(potValue, 0, 1023, 0, 255);

  // Control motor direction and speed
  controlMotor(motorSpeed);

  // Optional: Print motor speed to serial monitor for debugging
  Serial.print("Potentiometer Value: ");
  Serial.print(potValue);
  Serial.print(", Motor Speed: ");
  Serial.println(motorSpeed);

  // Add a small delay
  delay(10);
}

// --- 5. Motor Control Function ---
void controlMotor(int speed) {
  // --- Direction Control ---
  // Rotate forward if speed > 0
  if (speed > 0) {
    digitalWrite(MOTOR_IN1, HIGH);
    digitalWrite(MOTOR_IN2, LOW);
    digitalWrite(LED_PIN, HIGH); // LED ON when motor is moving forward
  }
  // Stop if speed is 0
  else {
    digitalWrite(MOTOR_IN1, LOW);
    digitalWrite(MOTOR_IN2, LOW);
    digitalWrite(LED_PIN, LOW); // LED OFF when motor is stopped
  }

  // --- Speed Control ---
  analogWrite(MOTOR_ENA, speed);  // PWM control of motor speed
}

/*
   --- USAGE INSTRUCTIONS ---

   1.  Connect the circuit according to the schematic.  Double-check all wiring,
       especially the power connections to the L298N and the motor.

   2.  Upload this code to your Arduino Uno.

   3.  Power the Arduino and the motor driver with the appropriate power supplies
       (5V for Arduino, 12V for the motor driver).  Ensure the motor power supply
       can provide sufficient current (at least the motor's stall current).

   4.  Rotate the potentiometer to adjust the motor speed. The motor should rotate
       in one direction, and its speed should vary with the potentiometer's position.

   5.  The LED on pin 13 will illuminate when the motor is running and turn off
       when the motor is stopped.

   --- TROUBLESHOOTING ---

   *   If the motor doesn't turn, check the power connections to the motor driver
       and the motor itself.  Also, verify that the Arduino is properly powered.

   *   If the motor runs at full speed regardless of the potentiometer position,
       ensure that the potentiometer is wired correctly and that the analog input
       pin (A0) is correctly defined in the code.

   *   If the motor rotates in the wrong direction, swap the MOTOR_IN1 and
       MOTOR_IN2 pins in the code or physically swap the motor wires.

   *   If the L298N gets too hot, reduce the motor voltage or use a heat sink.

   --- NOTES ---

   *   This code provides basic motor control. You can extend it to include
       features like direction control using additional digital input pins.

   *   The PWM frequency on pin 9 is approximately 490 Hz by default.  This
       frequency is suitable for most DC motors.  If you experience unusual motor
       behavior (e.g., excessive noise), you can try changing the PWM frequency.
       However, this requires more advanced Arduino programming techniques.

   *   Be careful when working with motor drivers and external power supplies.
       Always disconnect the power before making any wiring changes.
*/