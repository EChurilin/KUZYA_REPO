-- 002_staff_features.sql
-- Миграция для функционала staff_bot (игры, инструкция, отчеты)

-- 1. Расширение таблицы games
ALTER TABLE games ADD COLUMN IF NOT EXISTS link text;
ALTER TABLE games ADD COLUMN IF NOT EXISTS photo_path text;
ALTER TABLE games ADD COLUMN IF NOT EXISTS deactivated_at timestamp;

-- 2. Расширение таблицы instruction_blocks
ALTER TABLE instruction_blocks ADD COLUMN IF NOT EXISTS version int NOT NULL DEFAULT 1;
ALTER TABLE instruction_blocks ADD COLUMN IF NOT EXISTS is_published boolean NOT NULL DEFAULT false;

-- 3. Помечаем существующие блоки инструкции как опубликованные
UPDATE instruction_blocks SET is_published = true WHERE is_published = false;

-- 4. Индексы
CREATE INDEX IF NOT EXISTS idx_games_deactivated_at ON games(deactivated_at) WHERE deactivated_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_instruction_blocks_version ON instruction_blocks(version);
CREATE INDEX IF NOT EXISTS idx_instruction_blocks_published ON instruction_blocks(is_published);