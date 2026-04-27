from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="💎 Купить подписку")
    builder.button(text="👤 Мой профиль")
    builder.button(text="📖 Инструкции")
    builder.button(text="🆘 Поддержка")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)