from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.filters import CommandStart

from database.engine import async_session
from database.models import User
from keyboards.reply import get_main_menu
from keyboards.inline import get_support_keyboard
from services.marzban import MarzbanAPI


router = Router()
marzban = MarzbanAPI()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            trial_end = datetime.now() + timedelta(days=1)
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                marzban_username=f"tg_{user_id}",
                subscription_end=trial_end,
                is_active=True
            )
            session.add(user)
            await session.commit()

            expire_timestamp = int(trial_end.timestamp())
            try:
                # Создаем юзера в панели при первом старте (лимит 150гб)
                await marzban.create_user(f"tg_{user_id}", expire_timestamp, data_limit_gb=150)
            except Exception as e:
                print(f"Ошибка создания триала в Marzban: {e}")
            # --------------------------

            await message.answer(
                f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
                f"🟢 Добро пожаловать в <b>Green VPN</b> — твой доступ к свободному интернету.\n\n"
                f"🚀 <b>Почему мы?</b>\n"
                f"Мы используем самые быстрые современные протоколы. С нами ты даже не заметишь, что используешь VPN: сайты открываются мгновенно, а видео грузится без задержек.\n\n"
                f"🎁 <b>Твой бонус:</b>\n"
                f"Как новому пользователю, мы дарим тебе <b>1 день</b> премиум-теста. Пользуйся с удовольствием!\n\n"
                f"👇 <i>чтобы использовать подписку, воспользуйся кнопкой-инструкцией:</i>",
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
        else:
            status = "🟢 Активна" if user.is_active else "🔴 Неактивна"
            await message.answer(
                f"👋 <b>С возвращением в Green VPN!</b>\n\n"
                f"Статус вашей подписки: <b>{status}</b>.\n\n"
                f"Если у вас возникли вопросы или нужна помощь — смело пишите в нашу поддержку. "
                f"Мы всегда на связи и оперативно поможем! 🛠️",
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )


@router.message(F.text == "👤 Мой профиль")
async def cmd_profile(message: types.Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            return

        now = datetime.now()
        status = "🟢 Активна" if user.is_active else "🔴 Неактивна"

        if user.subscription_end:
            end_date = user.subscription_end.strftime("%d.%m.%Y")

            if user.subscription_end > now:
                time_left = user.subscription_end - now
                days = time_left.days

                if days > 0:
                    time_left_str = f"{days} дн."
                else:
                    hours = time_left.seconds // 3600
                    time_left_str = f"{hours} ч."
            else:
                time_left_str = "Истекла"
        else:
            end_date = "Нет"
            time_left_str = "—"

        marzban_data = await marzban.get_user(user.marzban_username)
        sub_url = marzban_data.get("subscription_url", "Ошибка получения ссылки")

        if user.is_active:
            text = (
                f"<b>👤 Твой профиль:</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"😉 Имя: {user.username}\n"
                f"🆔 ID: <code>{user.telegram_id}</code>\n"
                f"🏷 Статус: {status}\n"
                f"📅 Подписка до: {end_date} <i>(Осталось: {time_left_str})</i>\n\n"
                f"🔗 <b>Твоя ссылка для приложения (просто кликни по ней):</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"<code>{sub_url}</code>\n"
                f"━━━━━━━━━━━━━━"
            )
        else:
            text = (
                f"<b>👤 Твой профиль:</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"😉 Имя: {user.username}\n"
                f"🆔 ID: <code>{user.telegram_id}</code>\n"
                f"🏷 Статус: {status}\n"
                f"📅 Подписка отсутствует\n"
                f"━━━━━━━━━━━━━━"
            )

        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📖 Инструкции")
async def cmd_help(message: types.Message):
    text = (
        "<b>🤓 Как пользоваться Green VPN:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. зайдите в свой профиль по кнопке ниже. Если вы используете наш VPN впервые, возможно "
        "придется немного подождать создания вашей конфигурации. \n"
        "2. Скачайте приложение <b>V2RayNG</b> (Android) или <b>V2Box</b> (iOS).\n"
        "   <i>Возможно также скачать их аналоги: happ, streisand (доступны на всех ОС)</i>\n"
        "3. В профиле бота скопируйте свою ссылку (конфиг).\n"
        "4. В приложении нажмите «+» или «Import from clipboard» и вставьте ссылку.\n"
        "5. Нажмите кнопку подключения (самолетик) — готово!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🆘 Поддержка")
async def cmd_support(message: types.Message):
    await message.answer(
        "Возникли проблемы? Наш админ поможет тебе во всем разобраться!",
        reply_markup=get_support_keyboard()
    )


@router.message()
async def unknown_command(message: types.Message):
    text = ("Похоже, вы ввели <b>неизвестную мне команду</b> 😔, пожалуйста, воспользуйтесь кнопками ниже,"
            " чтобы воспользоваться нашими услугами.")
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )