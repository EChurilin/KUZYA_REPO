# Используем официальный образ Python 3.12 (совместим с нашим кодом)
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости (нужны для некоторых Python-пакетов)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей сначала (для кэширования слоёв Docker)
COPY pyproject.toml ./

# Устанавливаем Python-зависимости
# Используем --no-cache-dir для уменьшения размера образа
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Копируем исходный код приложения
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY migrations/ ./migrations/

# Создаём директорию для хранения скриншотов
RUN mkdir -p /app/storage/screenshots && \
    chmod -R 755 /app/storage

# Копируем entrypoint скрипт и делаем его исполняемым
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Устанавливаем entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]