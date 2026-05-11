#!/bin/bash

# Скрипт установки и управления Light Switcher сервисом

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="light-switcher"
SERVICE_FILE="$SCRIPT_DIR/light-switcher.service"
SYSTEMD_SERVICE="/etc/systemd/system/$SERVICE_NAME.service"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
}

# Установка зависимостей
install_dependencies() {
    print_info "Установка зависимостей..."
    
    # Обновление пакетов
    apt update
    
    # Установка Python и pyserial если нужно
    apt install -y python3 python3-pip python3-serial
    
    # Установка pyserial через pip
    pip3 install pyserial
    
    print_info "Зависимости установлены"
}

# Создание директории для логов
create_log_dir() {
    LOG_DIR="$SCRIPT_DIR/logs"
    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR"
        chown pi:pi "$LOG_DIR"
        print_info "Создана директория для логов: $LOG_DIR"
    fi
}

# Установка systemd сервиса
install_service() {
    print_info "Установка systemd сервиса..."
    
    # Копирование файла сервиса
    cp "$SERVICE_FILE" "$SYSTEMD_SERVICE"
    
    # Перезагрузка systemd
    systemctl daemon-reload
    
    # Включение сервиса
    systemctl enable "$SERVICE_NAME.service"
    
    print_info "Сервис $SERVICE_NAME установлен и включен для автозапуска"
}

# Управление сервисом
manage_service() {
    local action=$1
    
    case $action in
        start)
            print_info "Запуск сервиса $SERVICE_NAME..."
            systemctl start "$SERVICE_NAME.service"
            systemctl status "$SERVICE_NAME.service" --no-pager
            ;;
        stop)
            print_info "Остановка сервиса $SERVICE_NAME..."
            systemctl stop "$SERVICE_NAME.service"
            ;;
        restart)
            print_info "Перезапуск сервиса $SERVICE_NAME..."
            systemctl restart "$SERVICE_NAME.service"
            systemctl status "$SERVICE_NAME.service" --no-pager
            ;;
        status)
            systemctl status "$SERVICE_NAME.service" --no-pager
            ;;
        enable)
            systemctl enable "$SERVICE_NAME.service"
            print_info "Сервис $SERVICE_NAME включен для автозапуска"
            ;;
        disable)
            systemctl disable "$SERVICE_NAME.service"
            print_info "Сервис $SERVICE_NAME отключен из автозапуска"
            ;;
        logs)
            journalctl -u "$SERVICE_NAME.service" -f
            ;;
        *)
            print_error "Неизвестное действие: $action"
            echo "Доступные действия: start, stop, restart, status, enable, disable, logs"
            exit 1
            ;;
    esac
}

# Удаление сервиса
remove_service() {
    print_warning "Удаление сервиса $SERVICE_NAME..."
    
    # Остановка и отключение сервиса
    systemctl stop "$SERVICE_NAME.service" 2>/dev/null
    systemctl disable "$SERVICE_NAME.service" 2>/dev/null
    
    # Удаление файла сервиса
    rm -f "$SYSTEMD_SERVICE"
    
    # Перезагрузка systemd
    systemctl daemon-reload
    
    print_info "Сервис $SERVICE_NAME удален"
}

# Проверка подключения Arduino
test_connection() {
    print_info "Проверка подключения Arduino..."
    
    # Поиск возможных Serial портов
    echo "Возможные Serial порты:"
    ls -la /dev/tty* | grep -E "USB|ACM|AMA"
    
    # Запуск теста сервиса
    cd "$SCRIPT_DIR"
    python3 services/light_switcher_service.py
}

# Показ справки
show_help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  install     - Полная установка сервиса и зависимостей"
    echo "  setup       - Только настройка systemd сервиса"
    echo "  start       - Запуск сервиса"
    echo "  stop        - Остановка сервиса"
    echo "  restart     - Перезапуск сервиса"
    echo "  status      - Проверка статуса сервиса"
    echo "  enable      - Включение автозапуска"
    echo "  disable     - Отключение автозапуска"
    echo "  logs        - Просмотр логов сервиса"
    echo "  remove      - Удаление сервиса"
    echo "  test        - Тест подключения к Arduino"
    echo "  help        - Показ этой справки"
    echo ""
    echo "Примеры:"
    echo "  sudo $0 install    # Полная установка"
    echo "  sudo $0 start      # Запуск сервиса"
    echo "  $0 test            # Тест подключения"
}

# Основная логика
case "${1:-help}" in
    install)
        check_root
        install_dependencies
        create_log_dir
        install_service
        print_info "Установка завершена. Запустите сервис командой: sudo $0 start"
        ;;
    setup)
        check_root
        create_log_dir
        install_service
        print_info "Настройка завершена. Запустите сервис командой: sudo $0 start"
        ;;
    start|stop|restart|status|enable|disable|logs)
        check_root
        manage_service "$1"
        ;;
    remove)
        check_root
        remove_service
        ;;
    test)
        test_connection
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac
