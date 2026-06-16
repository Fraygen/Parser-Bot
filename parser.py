import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def parse_kwork():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        page.set_default_timeout(60000)
        await page.goto("https://kwork.ru/projects", wait_until="domcontentloaded")

        await asyncio.sleep(3)

        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        cards = soup.find_all('div', class_='want-card')

        print(f"[DEBUG] Найдено карточек: {len(cards)}")
        if cards:
            print(f"[DEBUG] Первая карточка (первые 500 символов):\n{str(cards[0])[:500]}")
        else:
            print("[DEBUG] Карточки не найдены. Проверьте HTML страницы.")

        parsed_info = []

        for card in cards:
            try:
                # Title
                title_tag = card.select_one('h1.wants-card__header-title > a')
                if not title_tag:
                    title_tag = card.find('a', href=True)
                title = title_tag.get_text(strip=True) if title_tag else "Без названия"
                link = "https://kwork.ru" + title_tag.get('href') if title_tag and title_tag.get('href') else "Нет ссылки"

                # Price — extract digits only, strip ₽ and surrounding text
                price_el = card.select_one('div.wants-card__price > div.d-inline')
                if not price_el:
                    price_el = card.find('div', class_='wants-card__price')
                raw_price = price_el.get_text(strip=True) if price_el else ""
                price_match = re.search(r'[\d\s]+', raw_price)
                price = price_match.group(0).replace(" ", "").strip() if price_match else raw_price.strip() or "Цена не указана"

                # Description — visible block only (not display:none)
                desc_el = card.select_one(
                    'div.wants-card__description-text > div.overflow-hidden:not([style*="display: none"]) > div.d-inline'
                )
                if not desc_el:
                    desc_el = card.find('div', class_='overflow-hidden',
                                        style=lambda s: not (s and 'display: none' in s))
                if not desc_el:
                    desc_el = card.find('div', class_='breakwords')
                description = desc_el.get_text(separator=' ', strip=True) if desc_el else "Нет описания"
                description = description.replace("Показать полностью", "").replace("Скрыть", "").strip()

                # Responses — span.mr8 containing "Предложений"
                responses = "0"
                for span in card.find_all('span', class_='mr8'):
                    txt = span.get_text(strip=True)
                    if "Предложений" in txt or "предложен" in txt.lower() or "отклик" in txt.lower():
                        num_match = re.search(r'\d+', txt)
                        responses = num_match.group(0) if num_match else txt
                        break

                parsed_info.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "price": price,
                    "responses": responses
                })

            except Exception as e:
                print(f"[DEBUG] Ошибка при парсинге карточки: {e}")
                continue

        await browser.close()
        return parsed_info


if __name__ == "__main__":
    results = asyncio.run(parse_kwork())
    
    print(f"✅ Найдено заказов: {len(results)}\n")    
    for item in results:
        print(f"📌 {item['title']}")
        print(f"💰 Бюджет: {item['price']} | 👥 {item['responses']}")
        print(f"📝 Описание: {item['description']}")
        print(f"🔗 Ссылка: {item['link']}")
        print("-" * 50)