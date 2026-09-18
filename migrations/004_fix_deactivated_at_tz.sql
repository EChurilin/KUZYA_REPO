-- Миграция 004: приведение games.deactivated_at к TIMESTAMPTZ
-- Причина: колонка была создана как TIMESTAMP (without time zone),
-- что вызывает ошибку при передаче timezone-aware дат из кода.

ALTER TABLE games
    ALTER COLUMN deactivated_at TYPE timestamptz
    USING deactivated_at AT TIME ZONE 'UTC';