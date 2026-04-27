from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy import select
from database.engine import async_session
from database.models import User


async def check_subscriptions(bot: Bot):
    async with async_session() as session:
        now = datetime.now()

        result = await session.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()

        for user in users:
            if not user.subscription_end:
                continue

            time_left = user.subscription_end - now

            if timedelta(days=4, hours=23) < time_left <= timedelta(days=5) and not user.notified_5d:
                try:
                    await bot.send_message(user.telegram_id,
                                           "⏳ Твоя подписка истекает через 5 дней! Не забудь продлить.")
                    user.notified_5d = True
                except:
                    pass

            elif timedelta(hours=23) < time_left <= timedelta(days=1) and not user.notified_1d:
                try:
                    await bot.send_message(user.telegram_id,
                                           "⚠️ Подписка закончится завтра! Продли сейчас, чтобы не потерять доступ.")
                    user.notified_1d = True
                except:
                    pass

            elif timedelta(minutes=59) < time_left <= timedelta(hours=1) and not user.notified_1h:
                try:
                    await bot.send_message(user.telegram_id, "‼️ Внимание! До отключения VPN остался всего 1 час.")
                    user.notified_1h = True
                except:
                    pass

            elif time_left <= timedelta(0):
                try:
                    await bot.send_message(user.telegram_id, "🔴 Твоя подписка истекла. Доступ к VPN ограничен.")
                    user.is_active = False
                except:
                    pass

        await session.commit()