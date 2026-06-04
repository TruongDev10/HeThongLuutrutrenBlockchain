#include <Servo.h>

Servo myservo1; // xoay de
Servo myservo2; // tay trai
Servo myservo3; // tay phai
Servo myservo4; // kep

const int servo1Pin = 3;
const int servo2Pin = 5;
const int servo3Pin = 6;
const int servo4Pin = 9;

int pos1 = 90;
int pos2 = 45;
int pos3 = 70;
int pos4 = 180;

const int BASE_MIN = 55;
const int BASE_MAX = 135;

const int ARM2_UP = 45;
const int ARM3_UP = 70;

const int ARM2_NEAR = 70;
const int ARM2_FAR = 55;
const int ARM3_NEAR = 95;
const int ARM3_FAR = 82;

// Chinh theo goc test thuc te cua kep.
const int CLAW_OPEN = 180;
const int CLAW_CLOSE = 60;

const int DROP_RED = 120;
const int DROP_GREEN = 140;
const int DROP_YELLOW = 160;
const int DROP_WRONG = 35;

String inputLine = "";

void handleCommand(String line);
void moveServoSmooth(Servo &servo, int &currentPos, int targetPos, int speedDelay);
void homePosition();
void openClaw();
void closeClaw();
void pickAndPlaceByCamera(float x, float y, String color, String status);
int dropAngleFor(String color, String status);

void setup() {
  myservo1.attach(servo1Pin);
  myservo2.attach(servo2Pin);
  myservo3.attach(servo3Pin);
  myservo4.attach(servo4Pin);

  Serial.begin(9600);

  homePosition();
  delay(1000);

  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      handleCommand(inputLine);
      inputLine = "";
    } else if (c != '\r') {
      inputLine += c;
    }
  }
}

void handleCommand(String line) {
  line.trim();

  if (line.length() == 0) return;

  if (line == "HOME" || line == "home") {
    homePosition();
    Serial.println("OK HOME");
    return;
  }

  // Lenh test nhanh.
  if (line == "OPEN" || line == "open") {
    openClaw();
    Serial.println("OK OPEN");
    return;
  }

  if (line == "CLOSE" || line == "close") {
    closeClaw();
    Serial.println("OK CLOSE");
    return;
  }

  if (line == "red" || line == "RED") {
    pickAndPlaceByCamera(150, 120, "red", "valid");
    Serial.println("OK PICK_DONE");
    return;
  }

  if (line == "green" || line == "GREEN") {
    pickAndPlaceByCamera(150, 120, "green", "valid");
    Serial.println("OK PICK_DONE");
    return;
  }

  if (line == "yellow" || line == "YELLOW") {
    pickAndPlaceByCamera(150, 120, "yellow", "valid");
    Serial.println("OK PICK_DONE");
    return;
  }

  if (!line.startsWith("PICK ")) {
    Serial.println("ERR UNKNOWN_COMMAND");
    return;
  }

  int p1 = line.indexOf(' ');
  int p2 = line.indexOf(' ', p1 + 1);
  int p3 = line.indexOf(' ', p2 + 1);
  int p4 = line.indexOf(' ', p3 + 1);

  if (p1 < 0 || p2 < 0 || p3 < 0 || p4 < 0) {
    Serial.println("ERR BAD_FORMAT");
    return;
  }

  float x = line.substring(p1 + 1, p2).toFloat();
  float y = line.substring(p2 + 1, p3).toFloat();
  String color = line.substring(p3 + 1, p4);
  String status = line.substring(p4 + 1);

  pickAndPlaceByCamera(x, y, color, status);

  Serial.println("OK PICK_DONE");
}

void moveServoSmooth(Servo &servo, int &currentPos, int targetPos, int speedDelay) {
  targetPos = constrain(targetPos, 0, 180);

  if (currentPos < targetPos) {
    for (int i = currentPos; i <= targetPos; i++) {
      servo.write(i);
      delay(speedDelay);
    }
  } else {
    for (int i = currentPos; i >= targetPos; i--) {
      servo.write(i);
      delay(speedDelay);
    }
  }

  currentPos = targetPos;
}

void homePosition() {
  moveServoSmooth(myservo1, pos1, 90, 20);
  moveServoSmooth(myservo2, pos2, ARM2_UP, 20);
  moveServoSmooth(myservo3, pos3, ARM3_UP, 20);
  moveServoSmooth(myservo4, pos4, CLAW_OPEN, 20);
}

void openClaw() {
  moveServoSmooth(myservo4, pos4, CLAW_OPEN, 20);
}

void closeClaw() {
  moveServoSmooth(myservo4, pos4, CLAW_CLOSE, 20);
}

void pickAndPlaceByCamera(float x, float y, String color, String status) {
  int baseAngle = map(constrain((int)x, 0, 300), 0, 300, BASE_MIN, BASE_MAX);
  int arm2Down = map(constrain((int)y, 0, 220), 0, 220, ARM2_FAR, ARM2_NEAR);
  int arm3Down = map(constrain((int)y, 0, 220), 0, 220, ARM3_FAR, ARM3_NEAR);
  int dropAngle = dropAngleFor(color, status);

  homePosition();
  delay(300);

  moveServoSmooth(myservo1, pos1, baseAngle, 20);
  delay(300);

  openClaw();
  delay(500);

  moveServoSmooth(myservo2, pos2, arm2Down, 20);
  moveServoSmooth(myservo3, pos3, arm3Down, 20);
  delay(500);

  closeClaw();
  delay(700);

  moveServoSmooth(myservo2, pos2, ARM2_UP, 20);
  moveServoSmooth(myservo3, pos3, ARM3_UP, 20);
  delay(500);

  moveServoSmooth(myservo1, pos1, dropAngle, 20);
  delay(500);

  moveServoSmooth(myservo2, pos2, 60, 20);
  moveServoSmooth(myservo3, pos3, 85, 20);
  delay(500);

  openClaw();
  delay(700);

  homePosition();
}

int dropAngleFor(String color, String status) {
  color.toLowerCase();
  status.toLowerCase();

  if (status == "wrong_color") return DROP_WRONG;

  if (color == "red") return DROP_RED;
  if (color == "green") return DROP_GREEN;
  if (color == "yellow") return DROP_YELLOW;

  return 90;
}
