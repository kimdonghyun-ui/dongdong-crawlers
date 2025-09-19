# crawlers/elevenst.py
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime

async def crawl_elevenst(keyword, include, exclude, min_price, max_price, max_pages=None):
    BASE_URL = "https://search.11st.co.kr/pc/total-search?kwd={keyword}&tabId=TOTAL_SEARCH&sortCd=L&pageNo={page}"

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
                await page.wait_for_selector("li.c-search-list__item", timeout=15000)
            except:
                break

            items = await page.query_selector_all("li.c-search-list__item")
            print(f"상품 개수: {len(items)}")

            for item in items:
                title_tag = await item.query_selector("div.c-card-item__name dd")
                price_tag = await item.query_selector("dd.c-card-item__price .value")
                link_tag = await item.query_selector("a.c-card-item__anchor")

                if not title_tag or not price_tag or not link_tag:
                    continue

                title = (await title_tag.inner_text()).strip()
                price_text = (await price_tag.inner_text()).strip().replace(",", "")
                href_raw = await link_tag.get_attribute("href")
                if not href_raw:
                    continue
                goodscode = href_raw.split("/")[-1].split("?")[0]
                href = f"https://www.11st.co.kr/products/{goodscode}"

                try:
                    price = int(price_text)
                except ValueError:
                    continue

                print(f"   - {title} | {price}원 | {href}")

                # ✅ 필터링
                if include and not any(w.lower() in title.lower() for w in include):
                    continue
                if exclude and any(w in title for w in exclude):
                    continue
                if not (min_price <= price <= max_price):
                    continue

                # ✅ 최저가 비교
                if lowest_price is None or price < lowest_price:
                    lowest_price = price
                    lowest_items = [{
                        "title": title,
                        "price": price,
                        "url": href,
                        "code": goodscode,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "site": "11st",
                    }]
                elif price == lowest_price:
                    lowest_items.append({
                        "title": title,
                        "price": price,
                        "url": href,
                        "code": goodscode,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "site": "11st",
                    })

            if lowest_items:
                break

            if max_pages and page_num >= max_pages:
                break

            next_btn = await page.query_selector("li.last button")
            if not next_btn:
                break
            page_num += 1

            await asyncio.sleep(3)

        await browser.close()
        return lowest_items
