const int xAxis = A0;
const int yAxis = A1;

const int buttonPin = 2;

int delayBetween = 20; // 20 is default

int checkTreshold = 75;

int outputTreshold = 110;

int baseXValue;
int baseYValue;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(500000);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
  baseXValue = analogRead(A0);
  baseYValue = analogRead(A1);
}

void loop() {
  // put your main code here, to run repeatedly:

  byte data = 0;

  int x = analogRead(A0) - baseXValue;
  int y = analogRead(A1) - baseYValue;

  int buttonState = digitalRead(buttonPin);

  // BINARY HELL
  // 0-1 биты для x
  // 2-3 биты для y
  // 4 бит для buttonState
  
  if (abs(y) > checkTreshold || abs(x) > checkTreshold) {
    
    if (x > outputTreshold) { 
      data |= (1 << 0); // Бит 0
    } else if (x < -outputTreshold) {
      data |= (1 << 1); // Бит 1
    }
    
    if (y > outputTreshold) { 
      data |= (1 << 2); // Бит 2
    } else if (y < -outputTreshold) {
      data |= (1 << 3); // Бит 3  
    }; 
  }
  
  if (buttonState == LOW) data |= (1 << 4);  // Бит 4

  Serial.write(data);

  delay(delayBetween);
}
