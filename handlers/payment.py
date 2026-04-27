# handlers/payment.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
import uuid
from yookassa import Configuration, Payment

router = Router()

TARIFFS = {
    "sub_1": {"label": "1 месяц", "price": 11900, "days": 30},
    "sub_3": {"label": "3 месяца", "price": 33500, "days": 90},
    "sub_6": {"label": "6 месяцев", "price": 63900, "days": 180},
    "sub_12": {"label": "12 месяцев", "price": 117500, "days": 365},
}

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

@router.message(F.text == "💎 Купить подписку")
async def show_tariffs(message: Message):
    builder = InlineKeyboardBuilder()

    for key, data in TARIFFS.items():
        price_rub = data['price'] // 100
        if key == "sub_1":
            text = f"😁 {data['label']} — {price_rub}₽"
        elif key == "sub_3":
            text = f"😎 {data['label']} — {price_rub}₽ (скидка ~6%)"
        elif key == "sub_6":
            text = f"🔥 {data['label']} — {price_rub}₽ (скидка ~11%)"
        else:
            text = f"🥵 {data['label']} — {price_rub}₽ (скидка ~18%)"

        builder.button(text=text, callback_data=f"select_{key}")

    builder.adjust(1)
    await message.answer(
        "<b>Выберите подходящий тариф👇:</b>\n\n"
        "🚀 Все тарифы включают трафик (150 гб / месяц) и максимально возможную скорость.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("select_"))
async def send_payment_link(callback: CallbackQuery):
    tariff_id = callback.data.replace("select_", "")
    data = TARIFFS[tariff_id]
    amount_rub = data['price'] // 100
    user_id = callback.from_user.id
    current_message_id = callback.message.message_id

    # Создаем платеж в ЮKassa
    payment = Payment.create({
        "amount": {
            "value": f"{amount_rub}.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/green_vpn_robot"
        },
        "capture": True,
        "description": f"Подписка Green VPN: {data['label']}",
        "metadata": {
            "user_id": str(user_id), # Сохраняем ID юзера
            "tariff_id": tariff_id,
            "message_id": str(current_message_id)
        }
    }, str(uuid.uuid4())) # Важно: uuid нужно обернуть в str()

    payment_url = payment.confirmation.confirmation_url


    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить (СБП, Карты)", url=payment_url)
    builder.button(text="вернуться назад", callback_data='back')
    builder.adjust(1)

    await callback.message.edit_text(
        f"💳 <b>Оплата тарифа: {data['label']}</b>\n\n"
        f"Стоимость: <b>{amount_rub}₽</b>\n\n"
        f"<i>После оплаты подписка выдастся автоматически в течение минуты.</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "back")
async def start_callback(query: CallbackQuery):
    builder = InlineKeyboardBuilder()

    for key, data in TARIFFS.items():
        price_rub = data['price'] // 100
        if key == "sub_1":
            text = f"😁 {data['label']} — {price_rub}₽"
        elif key == "sub_3":
            text = f"😎 {data['label']} — {price_rub}₽ (скидка ~6%)"
        elif key == "sub_6":
            text = f"🔥 {data['label']} — {price_rub}₽ (скидка ~11%)"
        else:
            text = f"🥵 {data['label']} — {price_rub}₽ (скидка ~18%)"

        builder.button(text=text, callback_data=f"select_{key}")

    builder.adjust(1)
    start_text = "<b>Если вы решили выбрать другой тариф, то они все тут😏:</b>\n\n"

    await query.message.edit_text(text=start_text, reply_markup=builder.as_markup(),
        parse_mode="HTML")