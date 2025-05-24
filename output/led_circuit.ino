void setup() {\n  pinMode(LED_PIN, OUTPUT);\n}",
          "explanation": "This function runs once at the beginning of the program. It configures the LED pin as an output."
        },
        {
          "section": "loop() Function",
          "code": "void loop() {\n  digitalWrite(LED_PIN, HIGH); // Turn the LED on.\n  delay(1000);                 // Wait for 1 second.\n  digitalWrite(LED_PIN, LOW);  // Turn the LED off.\n  delay(1000);                 // Wait for 1 second.\n}