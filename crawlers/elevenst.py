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
                await page.goto(url, timeout=60000)
            except Exception as e:
                print(f"🚨 page.goto 실패: {e}")
                break

            try:
                await page.wait_for_selector("div.c_card", timeout=20000)
            except:
                print("🚨 상품 리스트 로딩 실패, 다음 페이지 없음")
                break

            items = await page.query_selector_all("div.c_card")
            print(f"상품 개수: {len(items)}")

            for item in items:
                title_tag = await item.query_selector("div.c_prd_name > a")
                price_tag = await item.query_selector("span.value")
                link_tag = await item.query_selector("div.c_prd_name > a")

                if not title_tag or not price_tag or not link_tag:
                    continue

                title = (await title_tag.inner_text()).strip()
                price_text = (await price_tag.inner_text()).strip().replace(",", "")
                href = await link_tag.get_attribute("href")
                if not href:
                    continue
                href = "https://www.11st.co.kr" + href

                try:
                    price = int(price_text)
                except ValueError:
                    continue

                print(f"   - {title} | {price}원 | {href}")

                if include and not any(w.lower() in title.lower() for w in include):
                    continue
                if exclude and any(w in title for w in exclude):
                    continue

                if price < min_price or price > max_price:
                    print(f"   🚫 가격 범위 제외: {price}")
                    continue

                if lowest_price is None or price < lowest_price:
                    lowest_price = price
                    lowest_items = [{
                        "title": title,
                        "price": price,
                        "url": href,
                        "code": href.split("/")[-1],
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "site": "11st",
                    }]
                elif price == lowest_price:
                    lowest_items.append({
                        "title": title,
                        "price": price,
                        "url": href,
                        "code": href.split("/")[-1],
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "site": "11st",
                    })

            if max_pages and page_num >= max_pages:
                break

            next_btn = await page.query_selector("a.btn_next")
            if not next_btn:
                break
            page_num += 1

            await asyncio.sleep(2)

        await browser.close()
        return lowest_items
