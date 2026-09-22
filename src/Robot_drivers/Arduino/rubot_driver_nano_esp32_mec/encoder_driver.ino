/* *************************************************************
   Encoder definitions
   
   Add an "#ifdef" block to this file to include support for
   a particular encoder board or library. Then add the appropriate
   #define near the top of the main ROSArduinoBridge.ino file.
   
   ************************************************************ */
/* Functions and type-defs for PID control.

   Taken mostly from Mike Ferguson's ArbotiX code which lives at:
   
   http://vanadium-ros-pkg.googlecode.com/svn/trunk/arbotix/
*/
#define FRONT_LEFT  0
#define FRONT_RIGHT 1
#define BACK_LEFT   2
#define BACK_RIGHT  3


#ifdef USE_BASE

#ifdef ROBOGAIA
  /* The Robogaia Mega Encoder shield */
  #include "MegaEncoderCounter.h"

  /* Create the encoder shield object */
  MegaEncoderCounter encoders = MegaEncoderCounter(4); // Initializes the Mega Encoder Counter in the 4X Count mode
  
  /* Wrap the encoder reading function */
  long readEncoder(int i) {
    if (i == LEFT) return encoders.YAxisGetCount();
    else return encoders.XAxisGetCount();
  }

  /* Wrap the encoder reset function */
  void resetEncoder(int i) {
    if (i == LEFT) return encoders.YAxisReset();
    else return encoders.XAxisReset();
  }
#elif defined(ARDUINO_ENC_COUNTER)
  volatile long left_enc_pos = 0L;
  volatile long right_enc_pos = 0L;
  static const int8_t ENC_STATES [] = {0,1,-1,0,-1,0,0,1,1,0,0,-1,0,-1,1,0};  //encoder lookup table
    
  /* Interrupt routine for LEFT encoder, taking care of actual counting */
  ISR (PCINT2_vect){
  	static uint8_t enc_last=0;
        
	enc_last <<=2; //shift previous state two places
	enc_last |= (PIND & (3 << 2)) >> 2; //read the current state into lowest 2 bits
  
  	left_enc_pos += ENC_STATES[(enc_last & 0x0f)];
  }
  
  /* Interrupt routine for RIGHT encoder, taking care of actual counting */
  ISR (PCINT1_vect){
        static uint8_t enc_last=0;
          	
	enc_last <<=2; //shift previous state two places
	enc_last |= (PINC & (3 << 4)) >> 4; //read the current state into lowest 2 bits
  
  	right_enc_pos += ENC_STATES[(enc_last & 0x0f)];
  }
  
  /* Wrap the encoder reading function */
  long readEncoder(int i) {
    if (i == LEFT) return left_enc_pos;
    else return right_enc_pos;
  }

  /* Wrap the encoder reset function */
  void resetEncoder(int i) {
    if (i == LEFT){
      left_enc_pos=0L;
      return;
    } else { 
      right_enc_pos=0L;
      return;
    }
  }

#elif defined(ESP32_ENC_COUNTER)
  volatile long front_left_enc_pos = 0L;
  volatile long front_right_enc_pos = 0L;
  volatile long back_left_enc_pos = 0L;
  volatile long back_right_enc_pos = 0L;

  const int frontleftPinA = 1;//2
  const int frontleftPinB = 48;//3

  const int frontrightPinA = 2;
  const int frontrightPinB = 3;

  const int backleftPinA = 38;
  const int backleftPinB = 47;
  const int backrightPinA = 21;//21
  const int backrightPinB = 18;//18

  volatile uint8_t backleftState = 0;
  volatile uint8_t backrightState = 0;
  volatile uint8_t frontleftState = 0;
  volatile uint8_t frontrightState = 0;

  // Tabla de transición (como en el Nano)
  const int8_t ENC_STATES[] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};

  void IRAM_ATTR handleBackLeft() {
    backleftState <<= 2;
    backleftState |= (digitalRead(backleftPinA) << 1) | digitalRead(backleftPinB);
    back_left_enc_pos += ENC_STATES[backleftState & 0x0F];
  }

  void IRAM_ATTR handleBackRight() {
    backrightState <<= 2;
    backrightState |= (digitalRead(backrightPinA) << 1) | digitalRead(backrightPinB);
    back_right_enc_pos += ENC_STATES[backrightState & 0x0F];
  }

  void IRAM_ATTR handleFrontLeft() {
    frontleftState <<= 2;
    frontleftState |= (digitalRead(frontleftPinA) << 1) | digitalRead(frontleftPinB);
    front_left_enc_pos += ENC_STATES[frontleftState & 0x0F];
  }

  void IRAM_ATTR handleFrontRight() {
    frontrightState <<= 2;
    frontrightState |= (digitalRead(frontrightPinA) << 1) | digitalRead(frontrightPinB);
    front_right_enc_pos += ENC_STATES[frontrightState & 0x0F];
  }
  void setupEncoders() {
    pinMode(backleftPinA, INPUT_PULLUP);
    pinMode(backleftPinB, INPUT_PULLUP);
    pinMode(backrightPinA, INPUT_PULLUP);
    pinMode(backrightPinB, INPUT_PULLUP);

    pinMode(frontleftPinA, INPUT_PULLUP);
    pinMode(frontleftPinB, INPUT_PULLUP);
    pinMode(frontrightPinA, INPUT_PULLUP);
    pinMode(frontrightPinB, INPUT_PULLUP);

    attachInterrupt(backleftPinA, handleBackLeft, CHANGE);
    attachInterrupt(backleftPinB, handleBackLeft, CHANGE);
    attachInterrupt(backrightPinA, handleBackRight, CHANGE);
    attachInterrupt(backrightPinB, handleBackRight, CHANGE);

    attachInterrupt(frontleftPinA, handleFrontLeft, CHANGE);
    attachInterrupt(frontleftPinB, handleFrontLeft, CHANGE);
    attachInterrupt(frontrightPinA, handleFrontRight, CHANGE);
    attachInterrupt(frontrightPinB, handleFrontRight, CHANGE);

  }

  /* Wrap the encoder reading function */
  long readEncoder(int i) {
    if (i == FRONT_LEFT) {
    return front_left_enc_pos;
    }
    if (i == FRONT_RIGHT) {
      return front_right_enc_pos;
    }
    if (i == BACK_LEFT) {
      return back_left_enc_pos;
    }
    else {
      return back_right_enc_pos;
    }
  }

  /* Wrap the encoder reset function */
  void resetEncoder(int i) {
    if (i == FRONT_LEFT){
      front_left_enc_pos=0L;
      return;
    }
    if (i == FRONT_RIGHT){
      front_right_enc_pos=0L;
      return;
    }
    if (i == BACK_LEFT){
      back_left_enc_pos=0L;
      return;
    }
    else {
      back_right_enc_pos=0L;
      return;
    }
  }


#else
  #error A encoder driver must be selected!
#endif

/* Wrap the encoder reset function */
void resetEncoders() {
  resetEncoder(FRONT_LEFT);
  resetEncoder(FRONT_RIGHT);
  resetEncoder(BACK_LEFT);
  resetEncoder(BACK_RIGHT);
}

#endif



