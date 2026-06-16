from sqlalchemy import select, delete, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from datetime import datetime, timedelta, timezone
from settings import config


engine = create_async_engine(
    url=config.DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))



async def is_new(link):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(Order).where(Order.link == link))
            order = result.scalar_one_or_none()
            if order:
                return False
            
            new_order = Order(link=link)
            session.add(new_order)
            return True
        

async def del_old(AsyncSessionLocal):
    async with AsyncSessionLocal() as session:
        time = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = delete(Order).where(Order.created_at < time)
        await session.execute(stmt)
        await session.commit()



