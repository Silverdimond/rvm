#include <Servo.h>

Servo myServo;  // Create a Servo object

void setup() {
  Serial.begin(9600);  // Start serial communication at 9600 baud
  myServo.attach(8);   // Attach the servo to pin D8
  myServo.write(0);    // Move to 0 degrees initially
  pinMode(9, INPUT);
}

void loop() {
  if(digitalRead(9)==HIGH)
  {
     myServo.write(90);    
  }
  else
  {
   myServo.write(0);    
  }
   
}
