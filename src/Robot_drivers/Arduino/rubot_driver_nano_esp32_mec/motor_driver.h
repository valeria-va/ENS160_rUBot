/***************************************************************
   Motor driver function definitions - by James Nugen
   *************************************************************/


#ifdef TB6612FNG
  #define BACK_RIGHT_MOTOR_BACKWARD  8
  #define BACK_RIGHT_MOTOR_FORWARD   9
  #define BACK_RIGHT_MOTOR_ENABLE    10

  #define BACK_LEFT_MOTOR_BACKWARD   6//8
  #define BACK_LEFT_MOTOR_FORWARD    7//9
  #define BACK_LEFT_MOTOR_ENABLE     5//10

  #define FRONT_RIGHT_MOTOR_BACKWARD 11
  #define FRONT_RIGHT_MOTOR_FORWARD  12
  #define FRONT_RIGHT_MOTOR_ENABLE   14


  #define FRONT_LEFT_MOTOR_BACKWARD  17//11
  #define FRONT_LEFT_MOTOR_FORWARD   13//12
  #define FRONT_LEFT_MOTOR_ENABLE    4//14

#endif

void initMotorController();
void setMotorSpeed(int i, int spd);
void setMotorSpeeds(int frontleftSpeed, int frontrightSpeed,int backleftSpeed,int backrightSpeed);
