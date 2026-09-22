/* Functions and type-defs for PID control.

   Taken mostly from Mike Ferguson's ArbotiX code which lives at:
   
   http://vanadium-ros-pkg.googlecode.com/svn/trunk/arbotix/
*/
#define FL_MOTOR 0 // Motor Front Dret
#define FR_MOTOR 1 // Motor Front Esquerre
#define BL_MOTOR 2 // Motor Darrere Dret
#define BR_MOTOR 3 // Motor Darrere Esquerre

#define N_MOTORS 4 // Nombre total de motors

#define FRONT_LEFT  0
#define FRONT_RIGHT 1
#define BACK_LEFT   2
#define BACK_RIGHT  3



/* PID setpoint info For a Motor */
typedef struct {
  double TargetTicksPerFrame;    // target speed in ticks per frame
  long Encoder;                  // encoder count
  long PrevEnc;                  // last encoder count

  /*
  * Using previous input (PrevInput) instead of PrevError to avoid derivative kick,
  * see http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-derivative-kick/
  */
  int PrevInput;                // last input
  //int PrevErr;                   // last error

  /*
  * Using integrated term (ITerm) instead of integrated error (Ierror),
  * to allow tuning changes,
  * see http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-tuning-changes/
  */
  //int Ierror;
  int ITerm;                    //integrated term

  long output;                    // last motor setting
}
PID_Controller;

PID_Controller motorPID[N_MOTORS];

/* PID Parameters */
int Kp = 20;
int Kd = 12;
int Ki = 0;
int Ko = 50;

unsigned char moving = 0; // is the base in motion?

/*
* Initialize PID variables to zero to prevent startup spikes
* when turning PID on to start moving
* In particular, assign both Encoder and PrevEnc the current encoder value
* See http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-initialization/
* Note that the assumption here is that PID is only turned on
* when going from stop to moving, that's why we can init everything on zero.
*/
void resetPID(){
  motorPID[FL_MOTOR].TargetTicksPerFrame = 0.0;
  motorPID[FL_MOTOR].Encoder = readEncoder(FL_MOTOR);
  motorPID[FL_MOTOR].PrevEnc = motorPID[FL_MOTOR].Encoder;
  motorPID[FL_MOTOR].output = 0;
  motorPID[FL_MOTOR].PrevInput = 0;
  motorPID[FL_MOTOR].ITerm = 0;

  motorPID[FR_MOTOR].TargetTicksPerFrame = 0.0;
  motorPID[FR_MOTOR].Encoder = readEncoder(FR_MOTOR);
  motorPID[FR_MOTOR].PrevEnc = motorPID[FR_MOTOR].Encoder;
  motorPID[FR_MOTOR].output = 0;
  motorPID[FR_MOTOR].PrevInput = 0;
  motorPID[FR_MOTOR].ITerm = 0;

  motorPID[BL_MOTOR].TargetTicksPerFrame = 0.0;
  motorPID[BL_MOTOR].Encoder = readEncoder(BL_MOTOR);
  motorPID[BL_MOTOR].PrevEnc = motorPID[BL_MOTOR].Encoder;
  motorPID[BL_MOTOR].output = 0;
  motorPID[BL_MOTOR].PrevInput = 0;
  motorPID[BL_MOTOR].ITerm = 0;
  
  motorPID[BR_MOTOR].TargetTicksPerFrame = 0.0;
  motorPID[BR_MOTOR].Encoder = readEncoder(BR_MOTOR);
  motorPID[BR_MOTOR].PrevEnc = motorPID[BR_MOTOR].Encoder;
  motorPID[BR_MOTOR].output = 0;
  motorPID[BR_MOTOR].PrevInput = 0;
  motorPID[BR_MOTOR].ITerm = 0;  

}

/* PID routine to compute the next motor commands */
void doPID(PID_Controller * p) {
  long Perror;
  long output;
  int input;

  //Perror = p->TargetTicksPerFrame - (p->Encoder - p->PrevEnc);
  input = p->Encoder - p->PrevEnc;

  //Modificar
  Perror = p->TargetTicksPerFrame - input;


  /*
  * Avoid derivative kick and allow tuning changes,
  * see http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-derivative-kick/
  * see http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-tuning-changes/
  */
  //output = (Kp * Perror + Kd * (Perror - p->PrevErr) + Ki * p->Ierror) / Ko;
  // p->PrevErr = Perror;
  output = (Kp * Perror - Kd * (input - p->PrevInput) + p->ITerm) / Ko;
  p->PrevEnc = p->Encoder;

  output += p->output;
  // Accumulate Integral error *or* Limit output.
  // Stop accumulating when output saturates
  if (output >= MAX_PWM)
    output = MAX_PWM;
  else if (output <= -MAX_PWM)
    output = -MAX_PWM;
  else
  /*
  * allow turning changes, see http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-tuning-changes/
  */
    p->ITerm += Ki * Perror;

  p->output = output;
  p->PrevInput = input;
}

void updatePID() {
  // Leer los encoders
  motorPID[FL_MOTOR].Encoder = readEncoder(FRONT_LEFT);
  motorPID[FR_MOTOR].Encoder = readEncoder(FRONT_RIGHT);
  motorPID[BL_MOTOR].Encoder = readEncoder(BACK_LEFT);
  motorPID[BR_MOTOR].Encoder = readEncoder(BACK_RIGHT);

  // Si no estamos en movimiento, resetear PID si no está limpio
  if (!moving) {
    if (motorPID[FL_MOTOR].PrevInput != 0 || motorPID[FR_MOTOR].PrevInput != 0 ||
        motorPID[BL_MOTOR].PrevInput != 0 || motorPID[BR_MOTOR].PrevInput != 0) {
      Serial.println("-> resetPID()");
      resetPID();
    }
    return;
  }

  // Aplicar PID a cada motor
  doPID(&motorPID[FL_MOTOR]);
  doPID(&motorPID[FR_MOTOR]);
  doPID(&motorPID[BL_MOTOR]);
  doPID(&motorPID[BR_MOTOR]);

  // Aplicar velocidades
  setMotorSpeeds(
    motorPID[FL_MOTOR].output,  // Front right
    motorPID[FR_MOTOR].output,  // Front left
    motorPID[BL_MOTOR].output,  // Back right
    motorPID[BR_MOTOR].output   // Back left
  );
}


