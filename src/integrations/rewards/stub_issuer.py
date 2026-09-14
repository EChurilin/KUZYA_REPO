class StubRewardIssuer:
    """
    Заглушка для работы с балансом и выдачей наград.
    В будущем будет заменена на реальный клиент Telegram Bot API.
    """
    
    async def get_balance(self, reward_type: str) -> int:
        # Возвращаем большое число, чтобы на этапе разработки 
        # не было блокировок из-за нехватки средств
        return 1000000

    async def issue_reward(self, user_id: int, reward_type: str, amount: int) -> str:
        # Возвращаем фейковый ID транзакции
        return f"stub_tx_{user_id}_{amount}"