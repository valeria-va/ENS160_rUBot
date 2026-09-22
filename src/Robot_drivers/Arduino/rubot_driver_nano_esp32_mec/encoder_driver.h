/* *************************************************************
   Encoder driver function definitions - by James Nugen
   ************************************************************ */
   
   
#ifdef ARDUINO_ENC_COUNTER

  //Motor M4
  #define BACK_LEFT_ENC_PIN_A 47  
  #define BACK_LEFT_ENC_PIN_B 38  
  
  //Motor M3
  #define BACK_RIGHT_ENC_PIN_A 21  
  #define BACK_RIGHT_ENC_PIN_B 18   

  //Motor M2
  #define FRONT_RIGHT_ENC_PIN_A 13 //48
  #define FRONT_RIGHT_ENC_PIN_B 14 //1

  //Motor M1
  #define FRONT_LEFT_ENC_PIN_A 48
  #define FRONT_LEFT_ENC_PIN_B 1

#endif
   
long readEncoder(int i);
void resetEncoder(int i);
void resetEncoders();

