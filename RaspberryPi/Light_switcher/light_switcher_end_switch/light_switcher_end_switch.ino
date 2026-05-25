// Управление ядром по двум концевикам.
// Команда set1: едем к левому концевику, при успехе ответ done.
// Команда set2: едем к правому концевику, при успехе ответ done.
// Если нужный концевик уже нажат, ответ alreadyset.
// Если за заданный таймаут не дошли до концевика, ответ timeout.

#include <Stepper.h>

// ===============================
// НАСТРОЙКИ МОТОРА
// ===============================

// Количество шагов на один полный оборот двигателя
#define STEPS_PER_REV 2038

// Скорость двигателя в оборотах в минуту.
const int MOTOR_SPEED_RPM = 6;

// Номер пина: левый концевик
const int LEFT_SWITCH_PIN = 13;

// Номер пина: правый концевик
const int RIGHT_SWITCH_PIN = 12;

// Пины подключения шагового двигателя к Arduino.
// Порядок такой же, как в твоем рабочем примере.
const int MOTOR_PIN_1 = 2;
const int MOTOR_PIN_2 = 4;
const int MOTOR_PIN_3 = 3;
const int MOTOR_PIN_4 = 5;

// Таймаут движения в миллисекундах
const unsigned long MOVE_TIMEOUT_MS = 15000;

// Направление движения к левому и правому концевику.
// Если мотор едет не туда, просто поменяй знаки местами.
const int LEFT_DIR_STEPS = 1;
const int RIGHT_DIR_STEPS = -1;

// Количество шагов за один цикл проверки концевика.
// 1 = максимально просто и точно, но немного медленнее по логике.
const int STEP_CHUNK = 1;

// ===============================
// ИНИЦИАЛИЗАЦИЯ МОТОРА
// ===============================
Stepper stepper(STEPS_PER_REV, MOTOR_PIN_1, MOTOR_PIN_2, MOTOR_PIN_3, MOTOR_PIN_4);

String cmd = "";

// ===============================
// СЧИТЫВАНИЕ КОНЦЕВИКОВ
// ===============================
bool leftPressed() {
  return digitalRead(LEFT_SWITCH_PIN) == LOW;
}

bool rightPressed() {
  return digitalRead(RIGHT_SWITCH_PIN) == LOW;
}

// ===============================
// ДВИЖЕНИЕ К ЛЕВОМУ КОНЦЕВИКУ
// ===============================
String moveToLeft() {
  if (leftPressed()) return "alreadyset";

  unsigned long startTime = millis();

  while (!leftPressed()) {
    if (millis() - startTime > MOVE_TIMEOUT_MS) return "timeout";
    stepper.step(LEFT_DIR_STEPS * STEP_CHUNK);
  }

  return "done";
}

// ===============================
// ДВИЖЕНИЕ К ПРАВОМУ КОНЦЕВИКУ
// ===============================
String moveToRight() {
  if (rightPressed()) return "alreadyset";

  unsigned long startTime = millis();

  while (!rightPressed()) {
    if (millis() - startTime > MOVE_TIMEOUT_MS) return "timeout";
    stepper.step(RIGHT_DIR_STEPS * STEP_CHUNK);
  }

  return "done";
}

// ===============================
// ОБРАБОТКА КОМАНДЫ
// ===============================
void processCommand(String s) {
  s.trim();
  s.toLowerCase();

  if (s == "set1") {
    Serial.println(moveToLeft());
  } else if (s == "set2") {
    Serial.println(moveToRight());
  } else if (s.length() > 0) {
    Serial.println("unknown");
  }
}

// ===============================
// ЧТЕНИЕ SERIAL ПО СТРОКЕ
// ===============================
void readSerialLine() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      processCommand(cmd);
      cmd = "";
    } else if (c != '\r') {
      cmd += c;
      if (cmd.length() > 40) cmd = "";
    }
  }
}

// ===============================
// SETUP
// ===============================
void setup() {
  Serial.begin(9600);

  pinMode(LEFT_SWITCH_PIN, INPUT_PULLUP);
  pinMode(RIGHT_SWITCH_PIN, INPUT_PULLUP);

  stepper.setSpeed(MOTOR_SPEED_RPM);
}

// ===============================
// LOOP
// ===============================
void loop() {
  readSerialLine();
}