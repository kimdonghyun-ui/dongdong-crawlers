import asyncio
from playwright.async_api import async_playwright

async def crawl_elevenst(keyword: str, include: str = "", exclude: str = "", min_price: int = 0, max_price: int = 999999999):
    results = []
    url = f"https://search.11st.co.kr/Search.tmall?kwd={keyword}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--single-process",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )
        page = await context.new_page()

        print(f"▶ 11번가 크롤링 시작: {url}")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")

        items = await page.query_selector_all("div.c_card")

        print(f"상품 개수: {len(items)}")
        for item in items:
            try:
                title = await item.query_selector_eval("a.c_card_subject", "el => el.textContent") if await item.query_selector("a.c_card_subject") else ""
                link = await item.query_selector_eval("a.c_card_subject", "el => el.href") if await item.query_selector("a.c_card_subject") else ""
                price = await item.query_selector_eval("span.value", "el => el.textContent") if await item.query_selector("span.value") else "0"

                if not title or not price:
                    continue

                price = int(price.replace(",", "").replace("원", "").strip())

                if include and include not in title:
                    continue
                if exclude and exclude in title:
                    continue
                if price < min_price or price > max_price:
                    continue

                results.append({"title": title.strip(), "price": price, "link": link.strip()})
                print(f"   - {title.strip()} | {price}원 | {link.strip()}")

            except Exception as e:
                print(f"❌ 상품 파싱 실패: {e}")

        await browser.close()

    return results
