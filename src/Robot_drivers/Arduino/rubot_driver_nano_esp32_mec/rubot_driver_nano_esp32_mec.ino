bool commandReady = false;
/* Functions and type-defs for PID control.

   Taken mostly from Mike Ferguson's ArbotiX code which lives at:
   
   http://vanadium-ros-pkg.googlecode.com/svn/trunk/arbotix/
*/

#define FL_MOTOR 0 // Motor Front Esquerre
#define FR_MOTOR 1 // Motor Front Dret
#define BL_MOTOR 2 // Motor Darrere Esquerre
#define BR_MOTOR 3 // Motor Darrere Dret


#define N_MOTORS 4 // Nombre total de motors

#define USE_BASE      // Enable the base controller code
//#undef USE_BASE     // Disable the base controller code

/* Define the motor controller and encoder library you are using */
#ifdef USE_BASE
   /* The Pololu VNH5019 dual motor driver shield */
   //#define POLOLU_VNH5019

   /* Encoders directly attached to Arduino Nano ESP32 */
   #define ESP32_ENC_COUNTER
   /* L298 Motor driver*/
   #define TB6612FNG
#endif

//#define USE_SERVOS  // Enable use of PWM servos as defined in servos.h
#undef USE_SERVOS     // Disable use of PWM servos

/* Serial port baud rate */
#define BAUDRATE     57600

/* Maximum PWM signal */
#define MAX_PWM        255

#if defined(ARDUINO) && ARDUINO >= 100
#include "Arduino.h"
#else
#include "WProgram.h"
#endif

/* Include definition of serial commands */
#include "commands.h"

/* Sensor functions */
#include "sensors.h"

/* Include servo support if required */
#ifdef USE_SERVOS
   #include <Servo.h>
   #include "servos.h"
#endif

#ifdef USE_BASE
  /* Motor driver function definitions */
  #include "motor_driver.h"

  /* Encoder driver function definitions */
  #include "encoder_driver.h"

  /* PID parameters and functions */
  #include "diff_controller.h"

  /* Run the PID loop at 30 times per second */
  #define PID_RATE           30     // Hz

  /* Convert the rate into an interval */
  const int PID_INTERVAL = 1000 / PID_RATE;
  
  /* Track the next time we make a PID calculation */
  unsigned long nextPID = PID_INTERVAL;

  /* Stop the robot if it hasn't received a movement command
   in this number of milliseconds */
  #define AUTO_STOP_INTERVAL 4000
  long lastMotorCommand = AUTO_STOP_INTERVAL;
#endif

/* Variable initialization */

// A pair of varibles to help parse serial commands (thanks Fergs)
int arg = 0;
int argIndex = 0;

bool initialized = false;
// Variable to hold an input character
char chr;

// Variable to hold the current single-character command
char cmd;

// Character arrays to hold the first and second arguments
char argv1[16];
char argv2[16];
char argv3[16];
char argv4[16];

// The arguments converted to integers
long arg1;
long arg2;
long arg3;
long arg4;

/* Clear the current command parameters */
void resetCommand() {
  cmd = '\0';  
  memset(argv1, 0, sizeof(argv1));
  memset(argv2, 0, sizeof(argv2));
  memset(argv3, 0, sizeof(argv3));
  memset(argv4, 0, sizeof(argv4));
  arg1 = 0;
  arg2 = 0;
  arg3 = 0;
  arg4 = 0;
  arg = 0;
  argIndex = 0;
}

/* Run a command.  Commands are defined in commands.h */
int runCommand() {

  int i = 0;
  char *p = argv1;
  char *str;
  int pid_args[4];
  arg1 = atoi(argv1);
  arg2 = atoi(argv2);
  arg3 = atoi(argv3);
  arg4 = atoi(argv4);

  if (!(cmd >= 'a' && cmd <= 'z')) {
    Serial.println("Invalid command");
    return 0;
  }

  switch(cmd) {
  case GET_BAUDRATE:
    Serial.println(BAUDRATE);
    break;
  case ANALOG_READ:
    if (arg1 < 0 || arg1 >= 40) {
      Serial.println("Not on the desired range.Cancelling.");
      break;
    }
    Serial.println(analogRead(arg1));
    break;
  case DIGITAL_READ:
    Serial.println(digitalRead(arg1));
    break;
  case ANALOG_WRITE:
    analogWrite(arg1, arg2);
    Serial.println("OK"); 
    break;
  case DIGITAL_WRITE:
    if (arg2 == 0) digitalWrite(arg1, LOW);
    else if (arg2 == 1) digitalWrite(arg1, HIGH);
    Serial.println("OK"); 
    break;
  case PIN_MODE:
    if (arg2 == 0) pinMode(arg1, INPUT);
    else if (arg2 == 1) pinMode(arg1, OUTPUT);
    Serial.println("OK");
    break;
  case PING:
    Serial.println(Ping(arg1));
    break;
#ifdef USE_SERVOS
  case SERVO_WRITE:
    servos[arg1].setTargetPosition(arg2);
    Serial.println("OK");
    break;
  case SERVO_READ:
    Serial.println(servos[arg1].getServo().read());
    break;
  
#endif
    
#ifdef USE_BASE
  case READ_ENCODERS:
    Serial.print(readEncoder(FRONT_LEFT));
    Serial.print(" ");
    Serial.print(readEncoder(FRONT_RIGHT));
    Serial.print(" ");
    Serial.print(readEncoder(BACK_LEFT));
    Serial.print(" ");
    Serial.println(readEncoder(BACK_RIGHT));
    break;
   case RESET_ENCODERS:
    resetEncoders();
    resetPID();
    Serial.println("OK");
    break;
  case MOTOR_SPEEDS:
    /* Reset the auto stop timer */
    lastMotorCommand = millis();
    if (arg1 == 0 && arg2 == 0 && arg3 == 0 && arg4 == 0) {
      setMotorSpeeds(0, 0, 0, 0);
      resetPID();
      moving = 0;
    }
    else moving = 1;
    motorPID[FL_MOTOR].TargetTicksPerFrame = arg1;
    motorPID[FR_MOTOR].TargetTicksPerFrame = arg2;
    motorPID[BL_MOTOR].TargetTicksPerFrame = arg3;
    motorPID[BR_MOTOR].TargetTicksPerFrame = arg4;
    Serial.println("OK"); 
    break;
  case MOTOR_RAW_PWM:
    /* Reset the auto stop timer */
    lastMotorCommand = millis();
    resetPID();
    moving = 0; // Sneaky way to temporarily disable the PID
    setMotorSpeeds(arg1, arg2, arg3, arg4);
    Serial.println("OK"); 

    break;
  case UPDATE_PID:
    while ((str = strtok_r(p, ":", &p)) != nullptr) {
       pid_args[i] = atoi(str);
       i++;
    }
    Kp = pid_args[0];
    Kd = pid_args[1];
    Ki = pid_args[2];
    Ko = pid_args[3];
    Serial.println("OK");
    break;
#endif
  default:
    Serial.println("Invalid Command");
    break;
  }
  cmd = '\0';  // Reset del comando ejecutado
  return 1;
}

/* Setup function--runs once at startup. */
void setup() {
  initMotorController();
  setupEncoders();
  resetEncoders();
  resetPID(); 
  Serial.begin(BAUDRATE);
  /*
  while (!Serial); // espera a que el puerto esté listo
  Serial.flush();  // <- limpia buffer de salida
  while (Serial.available()) Serial.read();  // <- limpia entrada
  */
  cmd = '\0';
  }


/* Enter the main loop.  Read and parse input from the serial port
   and run any valid commands. Run a PID calculation at the target
   interval and check for auto-stop conditions.
*/
void loop() {
  
  while (Serial.available() > 0) {

    
    // Read the next character
    chr = Serial.read();

    // Evita procesar comandos si es un salto de línea suelto
    if (chr == '\n' || chr == 0x0A) {
      continue;
    }


    // Terminate a command with a CR
    if (chr == 13) {
      if (arg == 1) argv1[argIndex] = 0;
      else if (arg == 2) argv2[argIndex] = 0;
      else if (arg == 3) argv3[argIndex] = 0;
      else if (arg == 4) argv4[argIndex] = 0;
      if (cmd >= 'a' && cmd <= 'z') {
        commandReady = true;
      }
      while (Serial.available()) Serial.read();  // Limpia completamente el buffer
      continue;
    }
     
    // Use spaces to delimit parts of the command
    else if (chr == ' ') {
      // Step through the arguments
      if (arg == 0) arg = 1;
      else if (arg == 1)  {
        argv1[argIndex] = 0;
        arg = 2;
        argIndex = 0;
      }
      else if (arg == 2)  {
        argv2[argIndex] = 0;
        arg = 3;
        argIndex = 0;
      }
      else if (arg == 3)  {
        argv3[argIndex] = 0;
        arg = 4;
        argIndex = 0;
      }
      continue;
    }
    else {
      if (arg == 0) {
        // The first arg is the single-letter command
        cmd = chr;
      }
      else if (arg == 1) {
        // Subsequent arguments can be more than one character
        argv1[argIndex] = chr;
        argIndex++;
      }
      else if (arg == 2) {
        argv2[argIndex] = chr;
        argIndex++;
      }
      else if (arg == 3) {
        argv3[argIndex] = chr;
        argIndex++;
      }
      else if (arg == 4) {
        argv4[argIndex] = chr;
        argIndex++;
      }
    }

    //Init para que los motores no arranquen solos hasta que no llega la primera command
    if (!initialized) {
    // Estado de espera antes de la primera orden
    setMotorSpeeds(0, 0, 0, 0);
    resetEncoders();
    resetPID();
    moving = 0;
    return;  // No hacer nada más hasta que llegue un comando válido
    }
  }

if (commandReady) {
  char cmdBackup = cmd;

  if (cmd < 'a' || cmd > 'z') {
    Serial.println("Comando corrupto o inválido. Ignorando.");
    resetCommand();
    commandReady = false;
    return;
  }
  if (!initialized) {
    // Justo antes de ejecutar el primer comando, hacemos el reset
    resetEncoders();
    resetPID();
    setMotorSpeeds(0, 0, 0, 0);
    moving = 0;
    initialized = true;
  }

  runCommand();  // It's only executed when cmd is valid
  commandReady = false;
  resetCommand();

  cmd = cmdBackup;  // In case it was altered unexpectedly
  commandReady = false;
}

// If we are using base control, run a PID calculation at the appropriate intervals
#ifdef USE_BASE
  if (millis() > nextPID) {
    if (moving) {
      //Serial.print("moviendo");
      updatePID();
    }
    nextPID += PID_INTERVAL;
  }
  // Check to see if we have exceeded the auto-stop interval
  if ((millis() - lastMotorCommand) > AUTO_STOP_INTERVAL) {;
    setMotorSpeeds(0, 0, 0, 0);
    moving = 0;
  }
#endif

// Sweep servos
#ifdef USE_SERVOS
  int i;
  for (i = 0; i < N_SERVOS; i++) {
    servos[i].doSweep();
  }
#endif
}

