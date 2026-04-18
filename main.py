import asyncio
from aiogram import Bot, Dispatcher
from settings import config
from aiogram.types import BotCommand
from settings import config
from database import engine, Base, is_new
from handlers import router
from parser import parse_kwork
from ai_filter import analyze_order
import json


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
                print("🤖 Анализирую заказ")

                response = await analyze_order(item)
                try:
                    res = json.loads(response)
                    score = res.get("score", 0)
                    reason = res.get("reason", "Без пояснения")

                    if score >= 60:
                        text = (
                            f"🔥 Оценка: {score}/100\n"
                            f"📝 {item['title']}\n"
                            f"💰 Цена: {item['price']}\n"
                            f"🧐 Почему: {reason}\n"
                            f"🔗 {item['link']}"
                        )
                        await bot.send_message(config.MY_CHAT_ID, text, parse_mode="Markdown")
                    else:
                        print(f"⏩ Пропускаю (балл {score}): {item['title']}")

                except Exception as e:
                    print(f"❌ Ошибка ИИ: {e}")
            
            else:
                continue

        print(f"🔎 Новых заказов - {count}")
        await asyncio.sleep(600)


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
