import asyncio
from aiogram import Bot, Dispatcher
from settings import config
from aiogram.types import BotCommand
from settings import config
from database import engine, Base, is_new
from handlers import router
from parser import parse_kwork

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def check(bot):
    while True:
        print("🔎 Проверяю новые данные...")
        results = await parse_kwork()

        count = 0
        for item in results:
            if await is_new(item['link']):
                count += 1
                text = f"🔥 Новый заказ: {item['title']}\n💰 Цена: {item['price']}\n👥 {item['responses']}🔗 {item['link']}"
                await bot.send_message(config.MY_CHAT_ID, text)
            else:
                continue
        print(f"🔎 Новых заказов - {count}")

        await asyncio.sleep(300)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы")


async def main():   
    dp.include_router(router) 
    asyncio.create_task(check(bot))
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        print("✅ Бот запущен")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🚫 Бот остановлен")
