import uuid
from datetime import datetime, timezone
from typing import Optional

from src.core.entities import StarTopup
from src.core.exceptions import TopupNotFoundError
from src.core.interfaces import TopupRepository
from src.integrations.payments.invoice_sender import InvoiceSender
from src.services.balance_service import BalanceService


class TopupService:
    """Сервис для управления пополнением реального баланса звёзд бота."""

    def __init__(
        self,
        topup_repo: TopupRepository,
        invoice_sender: InvoiceSender,
        balance_service: BalanceService,
    ):
        self._topup_repo = topup_repo
        self._invoice_sender = invoice_sender
        self._balance_service = balance_service

    async def create_topup_request(self, admin_id: int, amount: int) -> StarTopup:
        """Создаёт запись о пополнении и генерирует уникальный invoice_payload."""
        now = datetime.now(timezone.utc)
        payload = f"topup_{uuid.uuid4().hex[:32]}"
        topup = StarTopup(
            id=uuid.uuid4(),
            admin_id=admin_id,
            amount=amount,
            status="pending",
            invoice_payload=payload,
            invoice_message_id=None,
            telegram_payment_charge_id=None,
            created_at=now,
            paid_at=None,
        )
        await self._topup_repo.create(topup)
        return topup

    async def send_invoice(self, topup: StarTopup) -> int:
        """Отправляет инвойс админу и сохраняет message_id. Возвращает message_id."""
        message_id = await self._invoice_sender.send_invoice(
            chat_id=topup.admin_id,
            title="Пополнение баланса бота",
            description=f"Пополнение баланса бота на {topup.amount} звёзд",
            payload=topup.invoice_payload,
            amount=topup.amount,
        )
        await self._topup_repo.set_invoice_message_id(topup.id, message_id)
        return message_id

    async def cancel_topup(self, topup_id: uuid.UUID) -> None:
        """Отменяет пополнение: удаляет сообщение инвойса и помечает запись как cancelled."""
        topup = await self._topup_repo.get_by_id(topup_id)
        if topup is None:
            raise TopupNotFoundError(f"Пополнение {topup_id} не найдено.")
        if topup.status != "pending":
            return  # Уже оплачено или отменено — ничего не делаем

        # Удаляем сообщение инвойса, если оно было отправлено
        if topup.invoice_message_id is not None:
            await self._invoice_sender.delete_message(
                chat_id=topup.admin_id,
                message_id=topup.invoice_message_id,
            )

        await self._topup_repo.update_status(topup_id, "cancelled", None)

    async def process_successful_payment(
        self, payload: str, telegram_charge_id: str
    ) -> Optional[StarTopup]:
        """Обрабатывает успешную оплату: находит запись по payload и помечает как paid."""
        topup = await self._topup_repo.get_by_payload(payload)
        if topup is None:
            return None
        if topup.status == "paid":
            return topup  # Идемпотентность: уже обработано

        await self._topup_repo.update_status(topup.id, "paid", telegram_charge_id)
        topup.status = "paid"
        topup.telegram_payment_charge_id = telegram_charge_id
        return topup

    async def get_bot_balance(self) -> int:
        """Возвращает реальный баланс звёзд бота."""
        return await self._balance_service.get_current_balance()