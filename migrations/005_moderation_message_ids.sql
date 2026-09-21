-- Миграция 005: добавление message_id для модерации заявок
-- Версия: 4.1
-- Назначение: хранение message_id сообщений скриншотов и итогового сообщения
--             в чате стафф-бота для их удаления при финализации заявки.

-- Колонка для хранения message_id сообщения скриншота в чате стафф-бота
ALTER TABLE application_screenshots ADD COLUMN staff_message_id INTEGER;

-- Колонка для хранения message_id итогового сообщения в чате стафф-бота
ALTER TABLE applications ADD COLUMN summary_message_id INTEGER;
