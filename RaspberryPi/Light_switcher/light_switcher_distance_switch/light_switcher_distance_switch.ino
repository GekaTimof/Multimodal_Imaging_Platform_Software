#include <Stepper.h>
#include <EEPROM.h>

// ============================================
// ОСНОВНЫЕ ПАРАМЕТРЫ ДЛЯ ПОДГОНКИ

// Количество шагов на полный оборот двигателя
#define STEPS_PER_REV 2038

// Скорость шагового двигателя
const int MOTOR_SPEED = 10;

// Максимальное время выполнения любой команды двигателя (мс)
const unsigned long MOTOR_TIMEOUT = 20000;

// Максимальное количество сохраняемых позиций
const int MAX_POSITIONS = 10;

// Минимально допустимое расстояние датчика
const float MIN_DISTANCE_CM = 0.0;

// Максимально допустимое расстояние датчика
const float MAX_DISTANCE_CM = 500.0;

// Таймаут ожидания сигнала от HC-SR04
const unsigned long SENSOR_TIMEOUT_US = 30000;


// ============================================
// НАСТРОЙКИ ШАГОВОГО ДВИГАТЕЛЯ
Stepper stepper(STEPS_PER_REV, 2, 4, 3, 5);


// ============================================
// ПИНЫ HC-SR04
const int TRIG_PIN = 9;
const int ECHO_PIN = 8;


// ============================================
// НАСТРОЙКИ ПАМЯТИ ПОЗИЦИЙ

struct SavedPosition {
  bool isSet;         // Позиция задана или нет
  float distanceCm;   // Расстояние в см
};

SavedPosition positions[MAX_POSITIONS];


// ===============================================
// ПАРАМЕТРЫ АВТОМАТИЧЕСКОГО ПОИСКА ПОЗИЦИИ
const int MOVE_CHUNK_SMALL = 5;       // Маленький шаг
const int MOVE_CHUNK_MEDIUM = 20;     // Средний шаг
const int MOVE_CHUNK_LARGE = 140;      // Большой шаг

const float POSITION_TOLERANCE = 0.05; // Допустимая ошибка в см



// ============================================
// ЧТЕНИЕ РАССТОЯНИЯ
float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, SENSOR_TIMEOUT_US);

  if (duration == 0) {
    return -1;
  }

  float distance = duration * 0.0343 / 2.0;
  return distance;
}


// ============================================
// СОХРАНЕНИЕ ПОЗИЦИЙ В EEPROM
void savePositionsToEEPROM() {
  int addr = 0;

  for (int i = 0; i < MAX_POSITIONS; i++) {
    EEPROM.put(addr, positions[i]);
    addr += sizeof(SavedPosition);
  }

  Serial.println(F("Позиции сохранены в EEPROM"));
}


// ============================================
// ЗАГРУЗКА ПОЗИЦИЙ ИЗ EEPROM
void loadPositionsFromEEPROM() {
  int addr = 0;

  for (int i = 0; i < MAX_POSITIONS; i++) {
    EEPROM.get(addr, positions[i]);

    // Защита от мусорных данных в EEPROM
    if (positions[i].distanceCm < MIN_DISTANCE_CM || positions[i].distanceCm > MAX_DISTANCE_CM) {
      positions[i].isSet = false;
      positions[i].distanceCm = 0;
    }

    addr += sizeof(SavedPosition);
  }

  Serial.println(F("Позиции загружены из EEPROM"));
}


// ============================================
// ОЧИСТКА ВСЕХ ПОЗИЦИЙ
void clearPositions() {
  for (int i = 0; i < MAX_POSITIONS; i++) {
    positions[i].isSet = false;
    positions[i].distanceCm = 0;
  }

  savePositionsToEEPROM();
  Serial.println(F("Все позиции очищены"));
}


// ============================================
// ДВИЖЕНИЕ ШАГОВОГО ДВИГАТЕЛЯ С ТАЙМАУТОМ
void moveStepperWithTimeout(long steps) {
  unsigned long startTime = millis();

  int direction = (steps > 0) ? 1 : -1;
  long remainingSteps = abs(steps);

  while (remainingSteps > 0) {
    // Проверка таймаута
    if (millis() - startTime > MOTOR_TIMEOUT) {
      Serial.println(F("Ошибка: движение прервано по таймауту (8 секунд)"));
      return;
    }

    // Двигаем по 1 шагу для возможности проверки времени
    stepper.step(direction);
    remainingSteps--;
  }

  Serial.println(F("Движение завершено"));
}


// ===============================================
// ПЕРЕМЕЩЕНИЕ К СОХРАНЁННОЙ ПОЗИЦИИ
void moveToPosition(int posIndex) {
  if (posIndex < 1 || posIndex > MAX_POSITIONS) {
    Serial.println(F("Ошибка: неверный номер позиции"));
    return;
  }

  int index = posIndex - 1;

  if (!positions[index].isSet) {
    Serial.println(F("Предупреждение: позиция не задана"));
    return;
  }

  float targetDistance = positions[index].distanceCm;

  Serial.print(F("Целевое расстояние: "));
  Serial.print(targetDistance);
  Serial.println(F(" см"));

  unsigned long startTime = millis();

  while (true) {
    if (millis() - startTime > MOTOR_TIMEOUT) {
      Serial.println(F("Ошибка: движение прервано по таймауту"));
      return;
    }

    float currentDistance = readDistance();

    if (currentDistance < 0) {
      Serial.println(F("Ошибка: не удалось прочитать расстояние"));
      return;
    }

    float diff = targetDistance - currentDistance;
    float absDiff = abs(diff);

    Serial.print("Текущее расстояние: ");
    Serial.print(currentDistance);
    Serial.print(" см | Разница: ");
    Serial.println(diff);

    if (absDiff <= POSITION_TOLERANCE) {
      Serial.println(F("Позиция достигнута"));
      return;
    }

    int moveChunk = MOVE_CHUNK_SMALL;

    if (absDiff > 1.0) {
      moveChunk = MOVE_CHUNK_LARGE;
    }
    else if (absDiff > 0.3) {
      moveChunk = MOVE_CHUNK_MEDIUM;
    }
    

    if (diff > 0) {
      stepper.step(-moveChunk);
    }
    else {
      stepper.step(moveChunk);
    }
  }
}


// ===============================================
// ОБРАБОТКА КОМАНД SERIAL
void processCommand(String cmd) {
  cmd.trim();

  // ============================================
  // Перемещение влево
  if (cmd.startsWith("mvl(")) {
    int startIdx = cmd.indexOf('(') + 1;
    int endIdx = cmd.indexOf(')');

    long steps = cmd.substring(startIdx, endIdx).toInt();

    Serial.print(F("Движение влево на "));
    Serial.print(steps);
    Serial.println(F(" шагов"));

    moveStepperWithTimeout(-steps);
  }


  // ============================================
  // Перемещение вправо
  else if (cmd.startsWith("mvr(")) {
    int startIdx = cmd.indexOf('(') + 1;
    int endIdx = cmd.indexOf(')');

    long steps = cmd.substring(startIdx, endIdx).toInt();

    Serial.print(F("Движение вправо на "));
    Serial.print(steps);
    Serial.println(F(" шагов"));

    moveStepperWithTimeout(steps);
  }


  // ============================================
  // Сохранить текущую дистанцию как позицию X
  else if (cmd.startsWith("set(")) {
    int startIdx = cmd.indexOf('(') + 1;
    int endIdx = cmd.indexOf(')');

    int posNumber = cmd.substring(startIdx, endIdx).toInt();

    if (posNumber < 1 || posNumber > MAX_POSITIONS) {
      Serial.println(F("Ошибка: номер позиции вне диапазона"));
      return;
    }

    float distance = readDistance();

    if (distance < 0) {
      Serial.println(F("Ошибка: не удалось измерить расстояние"));
      return;
    }

    positions[posNumber - 1].isSet = true;
    positions[posNumber - 1].distanceCm = distance;

    savePositionsToEEPROM();

    Serial.print(F("Позиция "));
    Serial.print(posNumber);
    Serial.print(F(" сохранена. Расстояние: "));
    Serial.print(distance);
    Serial.println(F(" см"));
  }


  // ============================================
  // Переместиться к позиции X
  else if (cmd.startsWith("pos(")) {
    int startIdx = cmd.indexOf('(') + 1;
    int endIdx = cmd.indexOf(')');

    int posNumber = cmd.substring(startIdx, endIdx).toInt();

    Serial.print(F("Переход к позиции "));
    Serial.println(posNumber);

    moveToPosition(posNumber);
  }


  // ============================================
  // Очистка памяти
  else if (cmd.equalsIgnoreCase("clear")) {
    clearPositions();
  }


  // ============================================
  // Проверка текущего расстояния
  else if (cmd.equalsIgnoreCase("dist")) {
    float distance = readDistance();

    if (distance < 0) {
      Serial.println(F("Ошибка чтения расстояния"));
    } else {
      Serial.print(F("Текущее расстояние: "));
      Serial.print(distance);
      Serial.println(F(" см"));
    }
  }

  else {
    Serial.println(F("Неизвестная команда"));
  }
}


// ============================================
// SETUP
void setup() {
  Serial.begin(9600);
  Serial.println(F("Старт системы"));

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  stepper.setSpeed(MOTOR_SPEED);

  loadPositionsFromEEPROM();

  Serial.println(F("Система готова"));
  Serial.println(F("Доступные команды:"));
  Serial.println(F("mvl(X) - перемещение в лево на X"));
  Serial.println(F("mvr(X) - перемещение в право на X"));
  Serial.println(F("set(X) - установка текущего положения как позицию X"));
  Serial.println(F("pos(X) - перемещение к положению позиции X"));
  Serial.println(F("clear - отчистка списка позиций"));
  Serial.println(F("dist - текущая дистанция"));
}


// ============================================
// LOOP
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    processCommand(cmd);
  }
}
