-- Миграция 006: добавление поля closed_at для реализации кулдауна на старт новой сессии
-- Версия: 4.2
-- Назначение: 
--   1. Хранить время закрытия сессии для расчёта кулдауна (10 минут)
--   2. Унифицировать обработку пустых и непустых автозакрытых сессий

-- Колонка для времени закрытия сессии (любым способом: ручным, автозакрытием)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

-- Индекс для быстрой проверки кулдауна: ищем последнюю completed-сессию пользователя
CREATE INDEX IF NOT EXISTS idx_sessions_user_completed 
    ON sessions(user_id, closed_at DESC) 
    WHERE status = 'completed';

-- Обновляем closed_at для уже завершённых сессий (приравниваем к created_at как fallback)
UPDATE sessions 
SET closed_at = created_at 
WHERE closed_at IS NULL 
  AND status IN ('completed', 'expired', 'cancelled');
