from groq import AsyncGroq
import json
from settings import config



client = AsyncGroq(api_key=config.API_KEY)

SYSTEM_PROMPT = """
Ты — узкопрофильный технический эксперт. Ты фильтруешь заказы для Python-разработчика. Твоя единственная цель: отделить программирование от ручного труда и дизайна.

СТЕК: Python, aiogram, FastAPI, Playwright, Парсинг, Интеграция ИИ (LLM).

БИНАРНЫЙ ФИЛЬТР (Оценка 0 сразу):
- Если работа подразумевает: "написать текст", "реферат", "статья", "сценарий", "перевод", "рерайт".
- Если работа подразумевает: "дизайн", "карточка товара", "логотип", "обработка фото", "удаление фона".
- Если работа подразумевает: "набор текста", "перепечатать с фото", "заполнить Excel вручную".
ЭТО НЕ ПРОГРАММИРОВАНИЕ. СТАВЬ 0.

ШКАЛА ОЦЕНКИ (0-100):
- 0: Любой гуманитарный или ручной труд (тексты, дизайн, переводы).
- 20-40: Другие языки (PHP, C++, JS-фронтенд) или общие задачи (тестирование, верстка).
- 60-80: Стандартные задачи: ТГ-боты, простые парсеры сайтов, работа с БД.
- 81-100: ИДЕАЛЬНО: Сложный парсинг (Playwright), асинхронность, интеграция ИИ (Llama/OpenAI), работа с API (CRM, МойСклад, Маркетплейсы через API).

ПРАВИЛО REASON:
Пиши коротко, в чем заключается ТЕХНИЧЕСКАЯ суть. Если это мусор — пиши "Это ручной труд/тексты".

ФОРМАТ ВЫВОДА: JSON {"score": число, "reason": "строка"}
"""

async def analyze_order(order):
    text = f"""
    Заголовок: {order['title']}
    Цена: {order['price']}
    Описание: {order['description']}
    """
    
    try:
        completion = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system",
                "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            response_format={"type": "json_object"},
            timeout=30.0
        )
        return completion.choices[0].message.content
    
    except Exception as e:
        print("Ошибка в файле ai_filter")
        return json.dumps({"score": 0, "reason": "ошибка апи"})