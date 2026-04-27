# handlers/admin.py
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMINS
from database.engine import async_session
from database.models import User
from sqlalchemy import select
from datetime import datetime
from services.marzban import MarzbanAPI

router = Router()
marzban = MarzbanAPI()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


def is_admin(message: Message):
    return message.from_user.id in ADMINS


# --- Рассылка ---
@router.message(Command("admin"), is_admin)
async def admin_menu(message: Message):
    await message.answer("Команды админа:\n/broadcast — запустить рассылку\n/give_forever ID — выдать вечную подписку")


@router.message(Command("broadcast"), is_admin)
async def start_broadcast(message: Message, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer("Введите текст сообщения для рассылки всем пользователям:")


@router.message(BroadcastState.waiting_for_message, is_admin)
async def do_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        users = result.scalars().all()

    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, message.text)
            count += 1
        except:
            continue

    await message.answer(f"✅ Рассылка завершена! Получили: {count} чел.")


# --- Вечная подписка ---
@router.message(Command("give_forever"), is_admin)
async def give_forever(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Пример: /give_forever 12345678")

    try:
        target_id = int(args[1])
    except ValueError:
        return await message.answer("ID должен быть числом.")

    forever_date = datetime(2099, 1, 1)
    expire_timestamp = int(forever_date.timestamp())

    async with async_session() as session:
        user = await session.get(User, target_id)
        if not user:
            return await message.answer("Пользователь не найден в базе бота.")


        marzban_user = await marzban.get_user(user.marzban_username)

        if not marzban_user:
            result = await marzban.create_user(
                username=user.marzban_username,
                expire_timestamp=expire_timestamp,
                data_limit_gb=0
            )
            status_text = "создан и активирован"
        else:
            result = await marzban.update_user(user.marzban_username, expire_timestamp)
            status_text = "обновлен"

        if result:
            user.subscription_end = forever_date
            user.is_active = True
            await session.commit()
            await message.answer(f"👑 Пользователь {target_id} {status_text} в Marzban с вечной подпиской!")
        else:
            await message.answer("❌ Ошибка при взаимодействии с API Marzban.")