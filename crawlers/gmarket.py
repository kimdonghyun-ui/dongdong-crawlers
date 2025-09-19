# crawlers/gmarket.py
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime

async def crawl_gmarket(keyword, include, exclude, min_price, max_price, max_pages=None):
    BASE_URL = "https://www.gmarket.co.kr/n/search?keyword={keyword}&p={page}&s=1"

    lowest_items = []
    lowest_price = None
    page_num = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        page = await browser.new_page()

        await page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        })
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        while True:
            url = BASE_URL.format(keyword=keyword, page=page_num)
            print(f"\n▶ {page_num} 페이지 확인 중: {url}")

            try:
                await page.goto(url, timeout=60000)  # ⬅️ timeout 60초
            except Exception as e:
                print(f"🚨 page.goto 실패: {e}")
                break

            try:
                await page.wait_for_selector("div.box__component", timeout=15000)  # ⬅️ 대기시간 연장
            except:
                break

            items = await page.query_selector_all("div.box__component")
            print(f"상품 개수: {len(items)}")

            # (나머지 로직 동일)
            ...
        
        await browser.close()
        return lowest_items
