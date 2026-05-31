import asyncio
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
        
        # Updated selectors - Kwork changed their HTML structure
        cards = soup.find_all('div', class_='ProjectCard')
        if not cards:
            cards = soup.find_all('div', class_='wants-card')
        if not cards:
            cards = soup.find_all('a', class_='wants-card__link')
        
        parsed_info = []

        for card in cards:
            # Try multiple selector paths
            link_tag = card.find('a', href=True)
            if not link_tag:
                link_tag = card if card.name == 'a' else None
            
            title = link_tag.get_text(strip=True) if link_tag else "Без названия"
            link = "https://kwork.ru" + link_tag.get('href') if link_tag and link_tag.get('href') else "Нет ссылки"

            # Price extraction
            price_el = card.find('div', class_='wants-card__price') or card.find('span', class_='fs1') or card.find('div', class_='ProjectCard__price')
            raw_price = price_el.get_text(strip=True) if price_el else "Цена не указана"
            price = raw_price.replace("Желаемый бюджет:", "").replace("Бюджет:", "").replace("до", "").replace("Цена", "").replace(":", "").strip()

            # Description extraction
            desc_full = card.find('div', class_='overflow-hidden', style=lambda s: s and 'display: none' in s)
            if not desc_full:
                desc_full = card.find('div', class_='breakwords')
            if not desc_full:
                desc_full = card.find('div', class_='ProjectCard__description')
            
            description = desc_full.get_text(separator=' ', strip=True) if desc_full else "Нет описания"
            description = description.replace("Показать полностью", "").replace("Скрыть", "").strip()

            # Responses extraction
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

