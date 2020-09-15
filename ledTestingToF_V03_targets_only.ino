
/* 
 p.wagner@bhvi.org - led presentation for testing eye-tracking device with ToF camera 
 led numbering from top left to right to bottom for testing led, 12 control target led
 in screen:     1      2      3       relating distances[cm]: 100   150      70
                    4 12   5                                   70 >400    30      
                       6    13                                         50   300
                    7       8                                   150     50
                9     10      11                             50     30      100   
*/

int ledtesting[] = {13, 1, 11, 8, 12, 4, 1, 9, 3, 4, 7, 3, 6, 2, 4, 10, 6, 8, 2, 13, 5, 2, 11,
9, 10, 11, 5, 8, 13, 3, 8, 7, 13, 9, 8, 1, 7, 12, 3, 11, 12, 1, 10, 8, 4, 6, 5, 10, 2, 9, 12, 
10, 7, 9, 6, 7, 11, 13, 4, 5, 1, 2, 7, 5, 9, 4, 11, 6, 1, 3, 5, 12, 13, 10, 3, 2, 12, 6, 13}; // set order of led illumination 

//int ledtesting[] = {13, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13};

const size_t n = sizeof(ledtesting) / sizeof(ledtesting[0]);
int ButtonInPin = 0;                                      // start button pin  
int ledtime= 4000;            // + 1200 blinking,  set presention time for target led 
int ButtonVal =0;                                         // button start value 

//String subjectIDfn = "ZB7P8W.csv"; // participant ID filename 
//String starttime, endtime, RecordData;            // variables to save px data onto SD card 

void setup() {  // put your setup code here, to run once:
  Serial.begin(9600);
  for(int i=2; i<=14; i++){
    pinMode(i, OUTPUT);
  }

  pinMode(ButtonInPin, INPUT); 
  
  Serial.println("Press button to start the test sequence"); 
}

void loop() {
  // start at a push of a buttom 
  ButtonVal = digitalRead(ButtonInPin);         // read input value
  if (ButtonVal == HIGH) {                // check if the input is HIGH (button released)
    digitalWrite(14, HIGH);       // turn control LED on 
  } else {                                // testing sequence
  
      Serial.println("Test start time.");
                                        
      for (int i=0; i<sizeof ledtesting/sizeof ledtesting[0]; i++) {// iterating through "ledtesting" and switching led on/off
        Serial.print("LED number:");
        Serial.println(ledtesting[i]);                
        LedBlinking(ledtesting[i], ledtime);
      }
      Serial.println("Test end time.");
      delay(2000);
      Serial.println("Press button to start the test sequence"); 
  }
}
 
void LedBlinking(int LedID, int delaytime) 
{
  LedID = LedID +1;  
  for(int i=0; i<=5; i++){         // blink testing LED     
  digitalWrite(LedID, HIGH);  
  delay(100);           
  digitalWrite(LedID, LOW);  
  delay(100);
  }
  digitalWrite(LedID, HIGH); 
  delay(delaytime);
  digitalWrite(LedID, LOW);
}

  
