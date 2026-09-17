-- Migration 003: balances and gifts (v4.0)
-- Adds: users.star_balance, users.instruction_passed, users.last_instruction_message_id
-- Adds tables: bot_settings, user_balance_transactions, gift_claims, star_topups
-- Idempotent: safe to re-run.

BEGIN;

-- 1. users: new columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS star_balance bigint NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS instruction_passed boolean NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_instruction_message_id integer;

-- 2. bot_settings: global key-value settings
CREATE TABLE IF NOT EXISTS bot_settings (
    key         text PRIMARY KEY,
    value       text NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO bot_settings (key, value)
VALUES ('screenshot_price', '15')
ON CONFLICT (key) DO NOTHING;

-- 3. user_balance_transactions: ledger of internal user balance
CREATE TABLE IF NOT EXISTS user_balance_transactions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         bigint NOT NULL REFERENCES users(id),
    amount          bigint NOT NULL,
    balance_after   bigint NOT NULL,
    reason          text NOT NULL,
    reference_id    uuid,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ubt_user_id ON user_balance_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_ubt_created_at ON user_balance_transactions(created_at);

-- 4. gift_claims: facts of receiving gifts
CREATE TABLE IF NOT EXISTS gift_claims (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 bigint NOT NULL REFERENCES users(id),
    gift_id                 text NOT NULL,
    gift_name               text,
    star_count              integer NOT NULL,
    status                  text NOT NULL DEFAULT 'pending',
    telegram_charge_id      text,
    created_at              timestamptz NOT NULL DEFAULT now(),
    sent_at                 timestamptz
);

CREATE INDEX IF NOT EXISTS idx_gift_claims_user_id ON gift_claims(user_id);
CREATE INDEX IF NOT EXISTS idx_gift_claims_status ON gift_claims(status);

-- 5. star_topups: bot balance top-up requests
CREATE TABLE IF NOT EXISTS star_topups (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id                    bigint NOT NULL REFERENCES users(id),
    amount                      integer NOT NULL,
    status                      text NOT NULL DEFAULT 'pending',
    invoice_payload             text UNIQUE NOT NULL,
    invoice_message_id          integer,
    telegram_payment_charge_id  text,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    paid_at                     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_star_topups_admin_id ON star_topups(admin_id);
CREATE INDEX IF NOT EXISTS idx_star_topups_status ON star_topups(status);

COMMIT;