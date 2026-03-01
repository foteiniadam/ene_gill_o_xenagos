#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// PWM driver για τον έλεγχο των κινητήρων μέσω I2C
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x47);

// Τιμές PWM για ευθεία κίνηση και στροφή (ρυθμίζονται πειραματικά)
int speed = 1000;
int turnSpeed = 2000;

// Ακίδες αισθητήρων παρακολούθησης γραμμής
#define SensorLeft 6
#define SensorMiddle 7
#define SensorRight 8

// Κατάσταση αισθητήρων γραμμής
unsigned char SL, SM, SR;

// Εντολή κίνησης από Bluetooth
// 'G' = κίνηση / παρακολούθηση γραμμής
// 'S' = άμεση ακινητοποίηση
char command = 'G';

void setup() {
  Serial.begin(9600);

  // Αρχικοποίηση PWM driver
  pwm.begin();
  pwm.setPWMFreq(60);

  // Ορισμός αισθητήρων ως είσοδοι
  pinMode(SensorLeft, INPUT);
  pinMode(SensorMiddle, INPUT);
  pinMode(SensorRight, INPUT);

  // Εκκίνηση με το όχημα ακινητοποιημένο
  stop();
}

void loop() {
  // Έλεγχος για νέα εντολή από Bluetooth
  if (Serial.available()) {
    command = Serial.read();
  }

  // Αν δοθεί εντολή stop, διακόπτεται κάθε κίνηση
  if (command == 'S') {
    stop();
    return;
  }

  // Ανάγνωση αισθητήρων γραμμής
  SL = digitalRead(SensorLeft);
  SM = digitalRead(SensorMiddle);
  SR = digitalRead(SensorRight);

  // Λογική παρακολούθησης γραμμής
  if (SM == HIGH) {
    // Το όχημα βρίσκεται πάνω στη γραμμή
    if (SL == LOW && SR == HIGH) {
      turnR();
    } else if (SR == LOW && SL == HIGH) {
      turnL();
    } else {
      advance();
    }
  } else {
    // Το όχημα έχει χάσει τη γραμμή
    if (SL == LOW && SR == HIGH) {
      turnR();
    } else if (SR == LOW && SL == HIGH) {
      turnL();
    } else {
      stop();
    }
  }
}

// Ευθεία κίνηση: όλοι οι κινητήρες προς τα εμπρός
void advance() {
  pwm.setPWM(0, 0, speed);
  pwm.setPWM(1, 0, 0);
  pwm.setPWM(2, 0, speed);
  pwm.setPWM(3, 0, 0);
  pwm.setPWM(4, 0, speed);
  pwm.setPWM(5, 0, 0);
  pwm.setPWM(6, 0, speed);
  pwm.setPWM(7, 0, 0);
}

// Στροφή δεξιά: ενεργοποίηση αριστερών κινητήρων
void turnR() {
  pwm.setPWM(0, 0, turnSpeed);
  pwm.setPWM(1, 0, 0);
  pwm.setPWM(2, 0, turnSpeed);
  pwm.setPWM(3, 0, 0);
  pwm.setPWM(4, 0, 0);
  pwm.setPWM(5, 0, turnSpeed);
  pwm.setPWM(6, 0, 0);
  pwm.setPWM(7, 0, turnSpeed);
}

// Στροφή αριστερά: ενεργοποίηση δεξιών κινητήρων
void turnL() {
  pwm.setPWM(0, 0, 0);
  pwm.setPWM(1, 0, turnSpeed);
  pwm.setPWM(2, 0, 0);
  pwm.setPWM(3, 0, turnSpeed);
  pwm.setPWM(4, 0, turnSpeed);
  pwm.setPWM(5, 0, 0);
  pwm.setPWM(6, 0, turnSpeed);
  pwm.setPWM(7, 0, 0);
}

// Πλήρης ακινητοποίηση οχήματος
void stop() {
  pwm.setPWM(0, 0, 0);
  pwm.setPWM(1, 0, 0);
  pwm.setPWM(2, 0, 0);
  pwm.setPWM(3, 0, 0);
  pwm.setPWM(4, 0, 0);
  pwm.setPWM(5, 0, 0);
  pwm.setPWM(6, 0, 0);
  pwm.setPWM(7, 0, 0);
}