# webhook_server.py
from aiohttp import web
from database.engine import async_session
from database.models import User
from services.marzban import MarzbanAPI
from datetime import datetime, timedelta
from handlers.payment import TARIFFS

marzban = MarzbanAPI()
bot_instance = None  # Сюда передадим бота при запуске

async def yookassa_handler(request):
    print("🔔 ПРИШЕЛ ВЕБХУК ОТ ЮKASSA!") # Добавь эту строку
    try:
        event = await request.json()
        print(f"Данные события: {event}")


        # ЮKassa присылает 'payment.succeeded' когда деньги получены
        if event.get('event') == 'payment.succeeded':
            payment_info = event['object']
            metadata = payment_info.get('metadata', {})

            user_id = int(metadata.get('user_id'))
            tariff_id = metadata.get('tariff_id')
            msg_to_delete = metadata.get('message_id')

            if user_id and tariff_id:
                added_days = TARIFFS[tariff_id]["days"]

                # --- ВАША ЛОГИКА ВЫДАЧИ ПОДПИСКИ ---
                async with async_session() as session:
                    user = await session.get(User, user_id)
                    if user:
                        now = datetime.now()
                        if user.subscription_end and user.subscription_end > now:
                            new_end = user.subscription_end + timedelta(days=added_days)
                        else:
                            new_end = now + timedelta(days=added_days)

                        expire_timestamp = int(new_end.timestamp())

                        try:
                            marzban_user = await marzban.get_user(user.marzban_username)
                            if marzban_user:
                                await marzban.update_user(user.marzban_username, expire_timestamp)
                            else:
                                await marzban.create_user(user.marzban_username, expire_timestamp, data_limit_gb=150)
                        except Exception as e:
                            print(f"Ошибка Marzban: {e}")

                        user.subscription_end = new_end
                        user.is_active = True
                        user.notified_5d = False
                        user.notified_1d = False
                        user.notified_1h = False
                        await session.commit()

                        # 👇 ВОТ ЭТОТ БЛОК ТЕПЕРЬ ВНУТРИ if user: 👇
                        if bot_instance:

                            if msg_to_delete:
                                try:
                                    await bot_instance.delete_message(chat_id=user_id, message_id=int(msg_to_delete))
                                except Exception as e:
                                    print(f"Не удалось удалить сообщение: {e}")

                            await bot_instance.send_message(
                                chat_id=user_id,
                                text=f"🎉 Спасибо! Оплата прошла успешно.\n"
                                     f"✅ Подписка активирована на <b>{added_days} дней</b> (до {new_end.strftime('%d.%m.%Y')}).",
                                parse_mode="HTML"
                            )
                    else:
                        print(f"❌ Пришла оплата, но юзер {user_id} не найден в БД!")

        return web.Response(text="OK", status=200)
    except Exception as e:
        print(f"Webhook Error: {e}")
        return web.Response(text="Error", status=500)


async def start_webhook_server(bot):
    global bot_instance
    bot_instance = bot  # Сохраняем бота, чтобы отправлять сообщения

    app = web.Application()
    app.router.add_post('/yookassa/webhook', yookassa_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("🚀 Webhook сервер запущен на порте 8080")