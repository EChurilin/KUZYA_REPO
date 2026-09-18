from aiogram import Router, F
from aiogram.types import PreCheckoutQuery, Message
from src.infrastructure.container import Container

router = Router()


@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Обработка PreCheckoutQuery: подтверждение платежа.
    Для платежей в Telegram Stars (XTR) всегда отвечаем ok=True,
    так как нет внешнего платёжного провайдера для валидации.
    Ответить необходимо в течение 10 секунд, иначе платёж отклоняется.
    """
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, container: Container):
    """
    Обработка SuccessfulPayment: фиксация оплаты и подтверждение админу.
    Сообщение приходит в чат, где был оплачен инвойс (чат админа с клиентским ботом).
    """
    successful_payment = message.successful_payment
    payload = successful_payment.invoice_payload
    telegram_charge_id = successful_payment.telegram_payment_charge_id

    topup = await container.topup_service.process_successful_payment(payload, telegram_charge_id)

    if topup is None:
        # payload не найден — не наш платёж, игнорируем
        return

    await message.answer(f"Баланс пополнен на {topup.amount} звёзд.")