/***************************************************************
   Motor driver definitions
   
   Add a "#elif defined" block to this file to include support
   for a particular motor driver.  Then add the appropriate
   #define near the top of the main ROSArduinoBridge.ino file.
   
   *************************************************************/

#ifdef USE_BASE
   
#ifdef TB6612FNG
  void initMotorController() {
  // Back Left and Right Motors Pin Config
  pinMode(BACK_LEFT_MOTOR_FORWARD, OUTPUT);
  pinMode(BACK_LEFT_MOTOR_BACKWARD, OUTPUT);
  pinMode(BACK_RIGHT_MOTOR_FORWARD, OUTPUT);
  pinMode(BACK_RIGHT_MOTOR_BACKWARD, OUTPUT);
  // Front Left and Right Motors Pin Config
  pinMode(FRONT_LEFT_MOTOR_FORWARD, OUTPUT);
  pinMode(FRONT_LEFT_MOTOR_BACKWARD, OUTPUT);
  pinMode(FRONT_RIGHT_MOTOR_FORWARD, OUTPUT);
  pinMode(FRONT_RIGHT_MOTOR_BACKWARD, OUTPUT);

  // Back Left and Right Motors Set on Low
  digitalWrite(BACK_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(BACK_LEFT_MOTOR_BACKWARD, LOW);
  digitalWrite(BACK_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(BACK_RIGHT_MOTOR_BACKWARD, LOW);

  // Front Left and Right Motors Set on Low
  digitalWrite(FRONT_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(FRONT_LEFT_MOTOR_BACKWARD, LOW);
  digitalWrite(FRONT_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(FRONT_RIGHT_MOTOR_BACKWARD, LOW);

  // Channel 0 Back Left
  ledcSetup(0, 5000, 8); // canal 0, 1kHz, 8 bits
  ledcAttachPin(BACK_LEFT_MOTOR_ENABLE, 0);
  ledcWrite(0, 0); 
  // Channel 1 Back Right
  ledcSetup(1, 5000, 8); 
  ledcAttachPin(BACK_RIGHT_MOTOR_ENABLE, 1);
  ledcWrite(1, 0);
  // Channel 3 for Front Left  
  ledcSetup(3, 5000, 8); 
  ledcAttachPin(FRONT_LEFT_MOTOR_ENABLE, 3);
  ledcWrite(3, 0);  
  // Channel 3 Front Right 
  ledcSetup(6, 5000, 8); 
  ledcAttachPin(FRONT_RIGHT_MOTOR_ENABLE, 6);
  ledcWrite(6, 0);    

  }
  
  void setMotorSpeed(int i, int spd) {
    unsigned char reverse = 0;
  
    if (spd < 0)
    {
      spd = -spd;
      reverse = 1;
    }
    if (spd > 150){
      spd = 150;
    }

    if (i == BACK_LEFT) { 
      if (reverse == 0) { 
        ledcWrite(0, spd); 
        digitalWrite(BACK_LEFT_MOTOR_FORWARD, HIGH); 
        digitalWrite(BACK_LEFT_MOTOR_BACKWARD, LOW); 
      } else { 
        ledcWrite(0, spd); 
        digitalWrite(BACK_LEFT_MOTOR_FORWARD, LOW); 
        digitalWrite(BACK_LEFT_MOTOR_BACKWARD, HIGH); 
      }
    }

    if (i == BACK_RIGHT) {
      if (reverse == 0) { 
        ledcWrite(1, spd); 
        digitalWrite(BACK_RIGHT_MOTOR_FORWARD, HIGH); 
        digitalWrite(BACK_RIGHT_MOTOR_BACKWARD, LOW); 
      } else { 
        ledcWrite(1, spd); 
        digitalWrite(BACK_RIGHT_MOTOR_FORWARD, LOW); 
        digitalWrite(BACK_RIGHT_MOTOR_BACKWARD, HIGH); 
      }
    }

    if (i == FRONT_LEFT) {
      if      (reverse == 0) {
        ledcWrite(3, spd);
        digitalWrite(FRONT_LEFT_MOTOR_FORWARD, HIGH); 
        digitalWrite(FRONT_LEFT_MOTOR_BACKWARD, LOW);         
      }
      else if (reverse == 1) { 
        ledcWrite(3, spd);
        digitalWrite(FRONT_LEFT_MOTOR_FORWARD, LOW); 
        digitalWrite(FRONT_LEFT_MOTOR_BACKWARD, HIGH);       
      }
    }
    if (i == FRONT_RIGHT) {
      if      (reverse == 0) { 
        ledcWrite(6, spd); 
        digitalWrite(FRONT_RIGHT_MOTOR_FORWARD, HIGH); 
        digitalWrite(FRONT_RIGHT_MOTOR_BACKWARD, LOW); 
      }
      else if (reverse == 1) { 
        ledcWrite(6, spd); 
        digitalWrite(FRONT_RIGHT_MOTOR_FORWARD, LOW); 
        digitalWrite(FRONT_RIGHT_MOTOR_BACKWARD, HIGH); 
      }
    }
  }
  
  void setMotorSpeeds(int frontleftSpeed, int frontrightSpeed,int backleftSpeed,int backrightSpeed) {
    setMotorSpeed(FRONT_LEFT, frontleftSpeed);
    setMotorSpeed(FRONT_RIGHT, frontrightSpeed);
    setMotorSpeed(BACK_LEFT, backleftSpeed);
    setMotorSpeed(BACK_RIGHT, backrightSpeed);

  }
#else
  #error A motor driver must be selected!
#endif

#endif
