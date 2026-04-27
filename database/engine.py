from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models import Base, User
from config import DB_URL
from datetime import datetime

async def get_user_subscription(session, tg_id: int):
    # Теперь select будет работать
    result = await session.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalar_one_or_none()

    if not user or not user.subscription_end:
        return None

    now = datetime.utcnow()
    if user.subscription_end > now:
        remaining = user.subscription_end - now
        return {
            "is_active": True,
            "days_left": remaining.days,
            "end_date": user.subscription_end
        }
    else:
        return {"is_active": False, "days_left": 0}

# Создаем движок подключения
engine = create_async_engine(DB_URL, echo=True)

# Создаем фабрику сессий для работы с БД
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Функция для создания таблиц при запуске (потом лучше использовать Alembic)
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)