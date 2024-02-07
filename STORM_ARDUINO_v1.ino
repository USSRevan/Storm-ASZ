//#### AUTO ORDER PICKER ___ ARDUINO UNO PART

#include <GCodeParser.h>

#include <Servo.h>


#define ___DEBUG___
#ifdef ___DEBUG___
  #define DPRINT(X) Serial.print(X)
  #define DPRINTLN(X) Serial.println(X)
#else  
  #define DPRINT(X)
  #define DPRINTLN(X)
#endif




/*
#define OPTO_PIN A0

#define OPTO_THRESHOLD 10


int opto_background = 0;

int opto_getRaw(){
  return 1023 - analogRead(OPTO_PIN);
}

void opto_init(){
  pinMode(OPTO_PIN, INPUT);
  opto_background = opto_getRaw();
}

bool opto_check(){
  return opto_getRaw() >= 800;
}
*/



#define ENDER_PIN 2

void ender_init(){
  pinMode(ENDER_PIN, INPUT_PULLUP);
}

bool ender_check(){
  return digitalRead(ENDER_PIN);
}






#include <FlexyStepper.h>

//9.7 между зубьями шкива
#define STEPPER_STEP_PIN  4
#define STEPPER_DIR_PIN   5

#define STEPPER_STEPS_PER_MM      6.3

#define STEPPER_SPEED_MM_PER_SEC  300.0
#define STEPPER_ACC_MM_PER_SEC2   300.0

#define STEPPER_HOMING_SPEED_MM_PER_SEC   300.0
#define STEPPER_MAX_HOMING_DISTANCE       2500
#define STEPPER_HOMING_DIRECTION          -1


FlexyStepper stepper;


void stepper_setSpeed_mmPerSec(float speed_mmPerSec){
  stepper.setSpeedInMillimetersPerSecond(speed_mmPerSec);
}

void stepper_setAcc_mmPerSec2(float acc_mmPerSec2){
  stepper.setAccelerationInMillimetersPerSecondPerSecond(acc_mmPerSec2);
}


void stepper_init(){
  stepper.connectToPins(STEPPER_STEP_PIN, STEPPER_DIR_PIN); 
  stepper.setStepsPerMillimeter(STEPPER_STEPS_PER_MM);
  
  stepper_setSpeed_mmPerSec(STEPPER_SPEED_MM_PER_SEC);
  stepper_setAcc_mmPerSec2(STEPPER_ACC_MM_PER_SEC2);
}


bool stepper_home(){
  bool success = stepper.moveToHomeInMillimeters(STEPPER_HOMING_DIRECTION, 
                                                 STEPPER_HOMING_SPEED_MM_PER_SEC, 
                                                 STEPPER_MAX_HOMING_DISTANCE, 
                                                 ENDER_PIN);
  return success;
}


void stepper_stop(){
  stepper.setTargetPositionToStop();
}


void stepper_move_mm(float target_x){
  stepper.moveToPositionInMillimeters(-target_x);
}






#define U_SERVO_PIN 9
#define Y_SERVO_PIN 10

Servo uServo;
Servo vServo;




GCodeParser GCode = GCodeParser();


//grab
#define U_SERVO_CLOSED 0
#define U_SERVO_OPENED 180

//выдвижение
#define Y_SERVO_HOMING_SPEED 20
#define Y_SERVO_CLOSING 0
#define Y_SERVO_STOP    90
#define Y_SERVO_OPENING 130

#define Y_SERVO_TIME_MS_PER_GRAD 4
#define Y_SERVO_BACK_ADDITION_TIME_MS 0

int grab_pos = 0;

void grab_init(){
  uServo.attach(U_SERVO_PIN, 500, 2500);
  vServo.attach(Y_SERVO_PIN, 500, 2500);
}


void grab_move(int angle){
  //vServo.write(angle);
  int dif = (angle - grab_pos);
  
  //DPRINTLN("Speed = " + String(speed));
  int timeout = abs(dif) * Y_SERVO_TIME_MS_PER_GRAD;
    
  int speed = Y_SERVO_STOP;
  if (dif > 0){
    speed = Y_SERVO_CLOSING;
  }
  else if (dif < 0){
    speed = Y_SERVO_OPENING;
    timeout += Y_SERVO_BACK_ADDITION_TIME_MS;
  }
  
  vServo.write(speed);
  delay(timeout);
  vServo.write(Y_SERVO_STOP);
  DPRINTLN("Start pos = " + String(grab_pos));
  grab_pos = angle;
  DPRINTLN("Current pos = " + String(grab_pos));
  vServo.write(Y_SERVO_STOP);
}


void grab_move_home(){
  int speed = Y_SERVO_STOP;
  if (grab_pos > 0){
    speed += Y_SERVO_HOMING_SPEED;
  }
  else{
    speed -= Y_SERVO_HOMING_SPEED;
  }
  //if (!opto_check()){
    vServo.write(speed);
    //while (!opto_check());
    delay(200);
    vServo.write(Y_SERVO_STOP);
    grab_pos = 0;
}


void grab_u(int u){
  u = constrain(u, U_SERVO_CLOSED, U_SERVO_OPENED);
  uServo.write(u);
}


void grab_v(int v){
  v = constrain(v, Y_SERVO_CLOSING, Y_SERVO_OPENING);
  vServo.write(v);
}


void grab(int v, int u){
  v = constrain(v, Y_SERVO_CLOSING, Y_SERVO_OPENING); 
  u = constrain(u, U_SERVO_CLOSED, U_SERVO_OPENED);
  grab_u(u);
  grab_move(v);
}


void grab_home(){
  grab_move_home();
  //grab_move(0);
  grab_u(180);
  //grab(Y_SERVO_STOP, U_SERVO_OPENED);
}






void g1(float x, int y, int u, int f, int a){
  if (u != -1){
    grab_u(u);
  }
  if (y != -1){
    grab_move(y);
  }
  if (f != -1){
    stepper_setSpeed_mmPerSec(f);
  }
  if (a != -1){
    stepper_setAcc_mmPerSec2(a);
  }
  if (x != -1){
    stepper_move_mm(x);
  }
  
  Serial.println(">>REACHED");
}


void g28(bool is_x, bool is_y){
  if (is_y){
    grab_home();
    delay(1000);
  }
  else if (is_x){
    stepper_home();  
  }
  else{
    grab_home();
    delay(1000);
    stepper_home();
  }
  Serial.println(">>HOME");
}


void(* resetFunc) (void) = 0;//declare reset function at address 0




void setup() 
{
  Serial.begin(115200);
  ender_init();
  DPRINTLN("Ender was inited!");
  grab_init();
  DPRINTLN("Grab was inited!");
  stepper_init();
  DPRINTLN("Stepper was inited!");  
  delay(100);
  DPRINTLN("Going home..");
  g28(0,1);
  g28(1,0);
}

void loop() 
{ 
  if (Serial.available() > 0)
  {
    if (GCode.AddCharToLine(Serial.read()))
    {
      GCode.ParseLine();
      GCode.RemoveCommentSeparators();
      if (GCode.HasWord('G'))
      {
        int code = (int)GCode.GetWordValue('G'); 
        if (code == 1){
          int x = (GCode.HasWord('X')) ? (int)GCode.GetWordValue('X') : -1;
          int y = (GCode.HasWord('Y')) ? (int)GCode.GetWordValue('Y') : -1;
          int u = (GCode.HasWord('U')) ? (int)GCode.GetWordValue('U') : -1;
      int f = (GCode.HasWord('F')) ? (int)GCode.GetWordValue('F') : -1;
          int a = (GCode.HasWord('A')) ? (int)GCode.GetWordValue('A') : -1;
          g1(x,y,u,f,a);
        }
        if (code == 4){
          int s = (GCode.HasWord('S')) ? (int)GCode.GetWordValue('S') : 1;
          delay(s*1000);
          Serial.println(">>WAKEUP");
        }
        else if (code == 28){
          bool is_x = (GCode.HasWord('X')) ? 1 : 0;
          bool is_y = (GCode.HasWord('Y')) ? 1 : 0;
          g28(is_x, is_y);
        }
        else if (code == 69){
          Serial.println(">>RESET");
          resetFunc();
        }
      }
    }
  }
}
