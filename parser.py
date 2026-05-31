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
        
        # Correct selector: div with class "want-card want-card--list want-card--hover"
        cards = soup.find_all('div', class_='want-card')
        
        parsed_info = []

        for card in cards:
            # Title: h1.wants-card__header-title > a
            title_tag = card.find('h1', class_='wants-card__header-title')
            link_tag = title_tag.find('a', href=True) if title_tag else None
            title = link_tag.get_text(strip=True) if link_tag else "Без названия"
            link = "https://kwork.ru" + link_tag.get('href') if link_tag and link_tag.get('href') else "Нет ссылки"

            # Price: div.wants-card__price
            price_el = card.find('div', class_='wants-card__price')
            raw_price = price_el.get_text(strip=True) if price_el else "Цена не указана"
            # Clean up price: remove "Цена до:" and extra whitespace
            price = raw_price.replace("Цена до:", "").replace("₽", "").strip()

            # Description: div.wants-card__description-text > div.overflow-hidden > div.d-inline
            desc_container = card.find('div', class_='wants-card__description-text')
            description = "Нет описания"
            if desc_container:
                # Get the visible description (not hidden)
                overflow_div = desc_container.find('div', class_='overflow-hidden')
                if overflow_div:
                    desc_text = overflow_div.find('div', class_='d-inline')
                    if desc_text:
                        description = desc_text.get_text(strip=True)

            # Responses: span with "Предложений:" text
            responses = "0"
            informers_row = card.find('div', class_='want-card__informers-row')
            if informers_row:
                spans = informers_row.find_all('span', class_='mr8')
                for span in spans:
                    txt = span.get_text(strip=True)
                    if "Предложений" in txt:
                        # Extract number from "Предложений: 0"
                        responses = txt.split(":")[-1].strip()
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

