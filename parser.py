import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def _parse_kwork_inner():
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
        print("[DEBUG] Открываю страницу...")
        await page.goto("https://kwork.ru/projects", wait_until="domcontentloaded")
        print("[DEBUG] Страница загружена, жду 5 сек...")
        
        await asyncio.sleep(3)

        print("[DEBUG] Получаю HTML...")
        content = await page.content()
        print("[DEBUG] Парсю карточки...")
        soup = BeautifulSoup(content, 'html.parser')
        cards = soup.find_all('div', class_='want-card')
        
        parsed_info = []

        for card in cards:
            link_tag = card.find('a', href=True)
            title = link_tag.get_text(strip=True) if link_tag else "Без названия"
            link = "https://kwork.ru" + link_tag.get('href') if link_tag else "Нет ссылки"

            price_el = card.find('div', class_='wants-card__price') or card.find('span', class_='fs1')
            raw_price = price_el.get_text(strip=True) if price_el else "Цена не указана"
            price = raw_price.replace("Желаемый бюджет:", "").replace("Бюджет:", "").replace("до", "").replace("Цена", "").replace(":", "").strip()


            desc_full = card.find('div', class_='overflow-hidden', style=lambda s: s and 'display: none' in s)
            if not desc_full:
                desc_full = card.find('div', class_='breakwords')
            
            description = desc_full.get_text(separator=' ', strip=True) if desc_full else "Нет описания"
            description = description.replace("Показать полностью", "").replace("Скрыть", "").strip()


            responses = "0"
            mr8 = card.find_all('span', class_='mr8')
            for span in mr8:
                txt = span.get_text(strip=True).lower()
                if "предложен" in txt or "отклик" in txt:
                    responses = span.get_text(strip=True)
                    break

            parsed_info.append({
                "title": title,
                "link": link,
                "description": description,
                "price": price,
                "responses": responses
            })

        print(f"[DEBUG] Готово, найдено {len(parsed_info)} карточек")
        await browser.close()
        return parsed_info


async def parse_kwork():
    try:
        return await asyncio.wait_for(_parse_kwork_inner(), timeout=120)
    except asyncio.TimeoutError:
        print("[ERROR] parse_kwork() завис и был прерван по таймауту")
        return []
    except Exception as e:
        print(f"[ERROR] parse_kwork() завершился с ошибкой: {e}")
        return []


if __name__ == "__main__":
    results = asyncio.run(parse_kwork())
    
    print(f"✅ Найдено заказов: {len(results)}\n")    
    for item in results:
        print(f"📌 {item['title']}")
        print(f"💰 Бюджет: {item['price']} | 👥 {item['responses']}")
        print(f"📝 Описание: {item['description']}")
        print(f"🔗 Ссылка: {item['link']}")
        print("-" * 50)