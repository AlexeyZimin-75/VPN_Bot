import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.engine import create_db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.scheduler import check_subscriptions
from webhook_server import start_webhook_server

from handlers import user, payment, admin
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    await create_db()

    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_subscriptions, "interval", minutes=1, args=(bot,))
    scheduler.start()
    asyncio.create_task(start_webhook_server(bot))
    print("🤖 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())