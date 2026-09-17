#!/bin/sh
set -e

# Определяем тип бота из переменной окружения
BOT_TYPE="${BOT_TYPE:-client}"

echo "Запуск бота типа: $BOT_TYPE"

# В зависимости от типа запускаем соответствующий модуль
case "$BOT_TYPE" in
    client)
        echo "Запуск client_bot..."
        exec python -m src.bots.client_bot.main
        ;;
    staff)
        echo "Запуск staff_bot..."
        exec python -m src.bots.staff_bot.main
        ;;
    *)
        echo "Неизвестный тип бота: $BOT_TYPE"
        echo "Допустимые значения: client, staff"
        exit 1
        ;;
esac