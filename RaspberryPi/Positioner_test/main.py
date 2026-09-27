import serial
import time
import signal
import sys


# ============================================================
# НАСТРОЙКИ
# ============================================================

PORT = "/dev/serial/by-path/platform-xhci-hcd.0-usb-0:1:1.0-port0"
BAUDRATE = 115200

# Скорость поиска концевика, мм/мин
SEARCH_FEED = 2000

# Скорость движения в центр, мм/мин
MOVE_FEED = 3000

# Максимальное расстояние поиска края, мм
SEARCH_DISTANCE = 50000

# Отход от концевика после срабатывания, мм
# (в GRBL-координатах; реальное перемещение
#  уменьшено передаточным числом ~40:1)
BACKOFF = 500

# Маппинг физических осей на GRBL-входы концевиков.
#
# Если концевик физической оси подключен к другому
# входу контроллера, укажите здесь правильный GRBL-лейбл.
#
# Формат: физическая_ось -> GRBL-ось_концевика
# По умолчанию совпадают: X->X, Y->Y, Z->Z
#
# Пример: если физ. ось X использует концевик GRBL-входа Z,
# а физ. ось Z — концевик GRBL-входа X:
#   LIMIT_AXIS_MAP = {"X": "Z", "Y": "Y", "Z": "X"}
LIMIT_AXIS_MAP = {
    "X": "X",
    "Y": "Y",
    "Z": "Z",
}

# Инверсия входов концевиков ($5).
#
# NC-концевики (Normally Closed):
#   в нормальном состоянии цепь замкнута,
#   при нажатии — размыкается.
#   Для GRBL это инвертированная логика -> $5=1.
#
# NO-концевики (Normally Open):
#   $5=0 (по умолчанию).
INVERT_LIMIT_PINS = True

# Таймауты, секунды
SEND_TIMEOUT = 5
IDLE_TIMEOUT = 120
ALARM_TIMEOUT = 840
LIMIT_RELEASE_TIMEOUT = 30
STATUS_TIMEOUT = 0.5

# Интервал между опросами статуса
STATUS_INTERVAL = 0.1


# ============================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================

ser = None


# ============================================================
# ЭКСТРЕННАЯ ОСТАНОВКА
# ============================================================

def emergency_stop():
    """Realtime-команда "!" -- немедленная пауза GRBL."""
    print("Останавливаем движение...")
    try:
        if ser and ser.is_open:
            ser.write(b"!")
            ser.flush()
            time.sleep(0.3)
    except Exception:
        pass


def signal_handler(signum, frame):
    """Обработчик Ctrl+C."""
    print()
    print("Получен Ctrl+C.")
    emergency_stop()
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# ============================================================
# CLEANUP
# ============================================================

def cleanup():
    """Восстанавливаем Hard Limits и закрываем порт."""
    try:
        if ser and ser.is_open:
            ser.write(b"\x18")
            ser.flush()
            time.sleep(0.5)
            ser.reset_input_buffer()
            ser.write(b"$21=1\n")
            ser.flush()
            time.sleep(0.3)
            ser.close()
    except Exception:
        pass
    print("Порт закрыт.")


# ============================================================
# ПОДКЛЮЧЕНИЕ
# ============================================================

def connect():
    global ser

    print(f"Подключение к {PORT}...")

    ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
    time.sleep(2)

    # Soft reset
    ser.write(b"\x18")
    ser.flush()
    time.sleep(1)
    ser.reset_input_buffer()

    # Читаем приветствие
    end = time.time() + 2
    while time.time() < end:
        line = ser.readline().decode(
            errors="replace"
        ).strip()
        if line:
            print(f"    {line}")

    print("Подключено.")

    # Инверсия входов концевиков
    if INVERT_LIMIT_PINS:
        print("Устанавливаем $5=1 (NC-концевики)...")
        ser.write(b"$5=1\n")
        ser.flush()
        time.sleep(0.3)
        while ser.in_waiting:
            line = ser.readline().decode(
                errors="replace"
            ).strip()
            if line:
                print(f"    {line}")


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def drain():
    """Вычитывает всё из serial-буфера."""
    while ser.in_waiting:
        ser.readline()


def send(command, timeout=None):
    """Отправляет команду, ждёт ok/error/ALARM."""
    if timeout is None:
        timeout = SEND_TIMEOUT

    drain()
    print(f">>> {command}")

    ser.write((command + "\n").encode())
    ser.flush()

    end = time.time() + timeout
    while time.time() < end:
        line = ser.readline().decode(
            errors="replace"
        ).strip()
        if not line:
            continue
        if line.startswith("<"):
            continue
        print(f"    {line}")
        if line == "ok":
            return True
        if line.startswith("error"):
            return False
        if line.startswith("ALARM"):
            return False

    print(f"!!! Тайм-аут: {command}")
    return False


def unlock():
    """Снимает ALARM ($X)."""
    print("$X (unlock)...")
    drain()
    ser.write(b"$X\n")
    ser.flush()
    end = time.time() + 2
    while time.time() < end:
        line = ser.readline().decode(
            errors="replace"
        ).strip()
        if line and not line.startswith("<"):
            print(f"    {line}")
            if line == "ok":
                return True
    return False


def get_status():
    """Отправляет ? и возвращает строку статуса."""
    drain()
    ser.write(b"?")
    ser.flush()
    end = time.time() + STATUS_TIMEOUT
    while time.time() < end:
        line = ser.readline().decode(
            errors="replace"
        ).strip()
        if line.startswith("<"):
            return line
    return None


def limit_axis(axis):
    """
    Возвращает GRBL-лейбл концевика
    для данной физической оси.
    """
    return LIMIT_AXIS_MAP.get(axis, axis)


def get_active_limits():
    """Возвращает set активных ФИЗИЧЕСКИХ осей из Pn."""
    status = get_status()
    if status is None:
        return set()
    if "|Pn:" not in status:
        return set()

    pn = status.split("|Pn:", 1)[1]
    if "|" in pn:
        pn = pn.split("|", 1)[0]

    # Обратный маппинг: GRBL-лейбл -> физическая ось
    grbl_to_axis = {v: k for k, v in LIMIT_AXIS_MAP.items()}

    active = set()
    for grbl_label in ("X", "Y", "Z"):
        if grbl_label in pn:
            active.add(grbl_to_axis.get(grbl_label, grbl_label))
    return active


def get_position(axis):
    """Возвращает MPos координату физической оси."""
    status = get_status()
    if status is None:
        return None
    try:
        mpos = status.split("MPos:", 1)[1]
        mpos = mpos.split("|", 1)[0]
        values = mpos.split(",")
        # MPos в порядке GRBL: X,Y,Z.
        # Для физической оси берём соответствующий
        # GRBL-индекс движения (по умолчанию совпадает).
        index = {"X": 0, "Y": 1, "Z": 2}[axis]
        return float(values[index])
    except Exception:
        return None


def wait_motion_complete(timeout=None):
    """
    Ждёт завершения движения:
    1. Пауза 0.5 сек — даём GRBL начать движение.
    2. Опрашиваем статус, пока не станет Idle.
    """
    if timeout is None:
        timeout = IDLE_TIMEOUT

    # Даём GRBL время начать движение
    time.sleep(0.5)

    end = time.time() + timeout

    while time.time() < end:
        status = get_status()
        if status is None:
            time.sleep(STATUS_INTERVAL)
            continue

        print(f"    {status}")

        if "<Idle" in status:
            return True

        if "<Alarm" in status:
            return False

        time.sleep(STATUS_INTERVAL)

    print("!!! Тайм-аут ожидания Idle.")
    return False


def wait_alarm(timeout=None):
    """
    Ждёт ALARM от концевика.
    Возвращает True -- ALARM, False -- таймаут.

    Периодически запрашивает ? чтобы видеть
    состояние в логе и не пропустить данные.
    """
    if timeout is None:
        timeout = ALARM_TIMEOUT

    end = time.time() + timeout
    next_query = time.time() + 0.5

    while time.time() < end:
        # Периодически запрашиваем статус
        now = time.time()
        if now >= next_query:
            try:
                ser.write(b"?")
                ser.flush()
            except Exception:
                pass
            next_query = now + 0.5

        line = ser.readline().decode(
            errors="replace"
        ).strip()

        if not line:
            continue

        if line.startswith("<"):
            print(f"    {line}")
            continue

        print(f"    {line}")

        if line.startswith("ALARM"):
            return True
        if line == "ok":
            continue

    print("!!! Тайм-аут ожидания ALARM.")
    return False


def wait_limit_release(axis, timeout=None):
    """Ждёт, пока ось исчезнет из Pn."""
    if timeout is None:
        timeout = LIMIT_RELEASE_TIMEOUT

    print(f"Ждём освобождения {axis}...")
    end = time.time() + timeout
    while time.time() < end:
        active = get_active_limits()
        if axis not in active:
            print(f"Концевик {axis} свободен.")
            return True
        time.sleep(STATUS_INTERVAL)

    print(f"!!! {axis} не освободился за {timeout} сек.")
    return False


# ============================================================
# ОТХОД ОТ КОНЦЕВИКА
# ============================================================

# Общая дистанция отхода (GRBL-координаты), мм
# Включает зону концевика + запас
RELEASE_DISTANCE = 1000

# Скорость отхода
RELEASE_FEED = 3000

# Максимум попыток отхода (unlock + G1)
RELEASE_MAX_RETRIES = 10


def release_from_limit(axis, direction, distance=None):
    """
    Отводит ось от концевика одним плавным движением.

    Алгоритм:
    1. $X (unlock) -> G91 -> G1 длинное движение
    2. Если ALARM снова (концевик ещё зажат) —
       повторяем unlock + G1
    3. Когда движение пошло без ALARM —
       ждём завершения (Idle)
    """
    if distance is None:
        distance = RELEASE_DISTANCE

    print()
    print(f"--- Отвод {axis} от концевика ---")

    move = distance * direction

    for attempt in range(RELEASE_MAX_RETRIES):

        unlock()
        time.sleep(0.2)
        send("G91")

        cmd = f"G1 {axis}{move} F{RELEASE_FEED}"

        if attempt == 0:
            print(f">>> {cmd}")
        else:
            print(
                f"Попытка {attempt + 1}: "
                f">>> {cmd}"
            )

        drain()
        ser.write((cmd + "\n").encode())
        ser.flush()

        # Читаем ответы, ждём ok + движение
        # Если получим ALARM — повторяем
        got_alarm = False
        end = time.time() + IDLE_TIMEOUT

        while time.time() < end:
            line = ser.readline().decode(
                errors="replace"
            ).strip()

            if not line:
                # Запрашиваем статус
                ser.write(b"?")
                ser.flush()
                continue

            if line.startswith("<"):
                print(f"    {line}")
                if "<Idle" in line:
                    # Движение завершено
                    print(f"--- {axis}: отход OK ---")
                    return True
                if "<Alarm" in line:
                    got_alarm = True
                    break
                continue

            print(f"    {line}")

            if line.startswith("ALARM"):
                got_alarm = True
                break

            if line == "ok":
                continue

        if got_alarm:
            print(
                f"ALARM при отходе, "
                f"повторяем..."
            )
            continue

        # Таймаут
        print("!!! Тайм-аут при отходе.")
        return False

    print(f"!!! {axis}: не удалось отойти от концевика.")
    return False


# ============================================================
# ПОИСК ОДНОГО КРАЯ
# ============================================================

def find_edge(axis, direction):
    """
    Двигает ось до ALARM.
    Возвращает MPos или None.
    """
    label = "+" if direction > 0 else "-"
    print()
    print(f"=== Поиск края {axis}{label} ===")

    unlock()
    time.sleep(0.1)
    send("G91")

    distance = SEARCH_DISTANCE * direction
    cmd = f"G1 {axis}{distance} F{SEARCH_FEED}"

    print(f">>> {cmd}")
    drain()
    ser.write((cmd + "\n").encode())
    ser.flush()

    if not wait_alarm():
        print(f"!!! Край {axis}{label} не найден.")
        return None

    time.sleep(0.1)
    pos = get_position(axis)

    if pos is None:
        print("!!! Не удалось получить позицию.")
        return None

    print(f"Край {axis}{label}: {pos:.3f} мм")
    return pos


# ============================================================
# КАЛИБРОВКА ОДНОЙ ОСИ
# ============================================================

def calibrate_axis(axis):
    print()
    print("#" * 60)
    print(f"  КАЛИБРОВКА ОСИ {axis}")
    print("#" * 60)

    # --- Первый край (+) ---

    edge1 = find_edge(axis, +1)
    if edge1 is None:
        return None

    if not release_from_limit(axis, -1, BACKOFF):
        return None

    # --- Второй край (-) ---

    edge2 = find_edge(axis, -1)
    if edge2 is None:
        return None

    # --- Расчёт ---

    travel = abs(edge1 - edge2)
    center_pos = (edge1 + edge2) / 2.0

    print()
    print(f"  {axis}: край+ = {edge1:.3f}")
    print(f"  {axis}: край- = {edge2:.3f}")
    print(f"  {axis}: ход   = {travel:.3f}")
    print(f"  {axis}: центр = {center_pos:.3f}")

    # --- Отход от второго края ---

    if not release_from_limit(axis, +1, BACKOFF):
        return None

    # --- Перемещение в центр ---

    print()
    print(f"Перемещаем {axis} в центр...")

    current = get_position(axis)
    if current is None:
        return None

    delta = center_pos - current
    send("G91")
    cmd = f"G1 {axis}{delta:.3f} F{MOVE_FEED}"

    if not send(cmd):
        return None

    if not wait_motion_complete():
        return None

    final = get_position(axis)
    print(f"  {axis}: факт = {final:.3f}")
    print(f"  {axis}: OK")

    return {
        "axis": axis,
        "edge_plus": edge1,
        "edge_minus": edge2,
        "travel": travel,
        "center": center_pos,
        "final": final,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 60)
    print("  АВТОМАТИЧЕСКАЯ КАЛИБРОВКА X / Y / Z")
    print("=" * 60)

    connect()

    # Hard Limits ON
    send("$21=1")

    # G91
    if not send("G91"):
        raise RuntimeError("Не удалось установить G91.")

    # Калибровка
    results = {}

    for axis in ("X", "Y", "Z"):
        result = calibrate_axis(axis)
        if result is None:
            raise RuntimeError(
                f"Ошибка калибровки {axis}."
            )
        results[axis] = result

    # Итог
    print()
    print("=" * 60)
    print("  КАЛИБРОВКА ЗАВЕРШЕНА")
    print("=" * 60)

    for axis in ("X", "Y", "Z"):
        r = results[axis]
        print(
            f"  {axis}: ход={r['travel']:.1f}, "
            f"центр={r['center']:.3f}, "
            f"факт={r['final']:.3f}"
        )

    print()
    print("Все оси в центре.")


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Ctrl+C.")
    except Exception as error:
        print()
        print(f"ОШИБКА: {error}")
    finally:
        emergency_stop()
        try:
            if ser and ser.is_open:
                ser.write(b"$21=1\n")
                ser.flush()
                time.sleep(0.3)
        except Exception:
            pass
        cleanup()
