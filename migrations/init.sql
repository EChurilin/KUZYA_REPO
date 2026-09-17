-- ============================================
-- Kizya Bot Database Schema
-- PostgreSQL 16+
-- ============================================

-- Таблица пользователей (Telegram user_id как PK)
CREATE TABLE users (
    id BIGINT PRIMARY KEY,  -- Telegram user_id
    username TEXT,
    first_name TEXT,
    language_code TEXT,
    role TEXT NOT NULL DEFAULT 'user',  -- user, moderator, admin
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Справочник игр
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Поблочная инструкция
CREATE TABLE instruction_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "order" INTEGER NOT NULL,
    text TEXT,
    media_type TEXT NOT NULL,  -- text, photo, video
    media_path TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Сессии (центральная сущность)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'active',  -- active, completed, expired, cancelled
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_screenshot_at TIMESTAMPTZ,
    screenshot_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Индекс для быстрого поиска активной сессии пользователя
CREATE INDEX idx_sessions_user_active ON sessions(user_id, status) WHERE status = 'active';

-- Кампании (ЗАГЛУШКА для будущей аналитики)
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Заявки (создаются после закрытия сессии)
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'pending_review',  -- pending_review, approved, rejected, rewarded
    actual_screenshot_count INTEGER NOT NULL DEFAULT 0,
    approved_screenshot_count INTEGER NOT NULL DEFAULT 0,
    moderator_comment TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    rewarded_at TIMESTAMPTZ,
    reviewed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    auto_closed BOOLEAN NOT NULL DEFAULT false
);

-- Индексы для очереди модерации и истории пользователя
CREATE INDEX idx_applications_status_submitted ON applications(status, submitted_at);
CREATE INDEX idx_applications_user_submitted ON applications(user_id, submitted_at DESC);

-- Скриншоты (привязаны к сессии, позже к заявке)
CREATE TABLE application_screenshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    client_file_id TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, approved, rejected
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Индексы для быстрого доступа к скриншотам
CREATE INDEX idx_screenshots_session ON application_screenshots(session_id);
CREATE INDEX idx_screenshots_application ON application_screenshots(application_id);

-- Награды
CREATE TABLE rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    reward_type TEXT NOT NULL,  -- stars, gift
    amount INTEGER NOT NULL,
    transaction_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, issued, failed
    issued_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- Снапшоты баланса (кэш от Telegram API)
CREATE TABLE balance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reward_type TEXT NOT NULL,
    balance BIGINT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Индекс для быстрого получения последнего снапшота
CREATE INDEX idx_balance_snapshots_type_fetched ON balance_snapshots(reward_type, fetched_at DESC);

-- Тикеты поддержки
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'open',  -- open, in_progress, closed
    priority TEXT NOT NULL DEFAULT 'medium',  -- low, medium, high
    assigned_to BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- Сообщения в тикетах
CREATE TABLE support_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender_id BIGINT NOT NULL,
    sender_type TEXT NOT NULL,  -- user, staff
    text TEXT,
    file_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Аудит-лог (для отслеживания изменений)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    actor_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Лимиты (rate limiting)
CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    counter INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- Индексы для производительности
-- ============================================

-- Для CleanupService: поиск протухших сессий
CREATE INDEX idx_sessions_active_last_action ON sessions(status, last_screenshot_at) WHERE status = 'active';

-- Для CleanupService: поиск старых скриншотов
CREATE INDEX idx_screenshots_created_session_status ON application_screenshots(created_at, session_id);

-- ============================================
-- Функции и триггеры (опционально)
-- ============================================

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для tables с updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_instruction_blocks_updated_at BEFORE UPDATE ON instruction_blocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();