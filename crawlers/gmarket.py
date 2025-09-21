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
            headless=False,  # 서버 배포 시 headless=True 권장
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        page = await browser.new_page()

        # UA 고정
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
                await page.goto(url, timeout=30000)
            except Exception as e:
                print(f"⚠️ 페이지 로딩 실패: {e}")
                break

            try:
                await page.wait_for_selector("div.box__component, div.box__component-item", timeout=20000)
            except:
                print("⚠️ 상품 리스트 로딩 실패")
                break

            items = await page.query_selector_all("div.box__component, div.box__component-item")
            print(f"상품 개수: {len(items)}")

            for item in items:
                title_tag = await item.query_selector("span.text__item")
                price_tag = await item.query_selector("strong.text__value")
                link_tag = await item.query_selector("a.link__item")

                if not title_tag or not price_tag or not link_tag:
                    continue

                title = (await title_tag.inner_text()).strip()
                price_text = (await price_tag.inner_text()).strip().replace(",", "")
                goodscode = await link_tag.get_attribute("data-montelena-goodscode")
                href = f"https://item.gmarket.co.kr/Item?goodscode={goodscode}"

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

                # ✅ 가격 범위 필터
                if price < min_price or price > max_price:
                    print(f"   🚫 가격 범위 제외: {price}")
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
                        "site": "gmarket",
                    }]
                elif price == lowest_price:
                    lowest_items.append({
                        "title": title,
                        "price": price,
                        "url": href,
                        "code": goodscode,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "site": "gmarket",
                    })

            # 🔥 페이지 제한
            if max_pages and page_num >= max_pages:
                break

            # ✅ 다음 페이지 버튼
            next_btn = await page.query_selector("a.link__page-next")
            if not next_btn:
                print("⚠️ 다음 페이지 버튼 없음. 종료")
                break

            try:
                await next_btn.click()
                await page.wait_for_selector("div.box__component, div.box__component-item", timeout=20000)
                print(f"➡️ 다음 페이지 이동 성공: {page_num+1} 페이지")
            except Exception as e:
                print(f"⚠️ 페이지 이동 실패: {e}")
                break

            page_num += 1
            await asyncio.sleep(2)  # 서버 부담 줄이기

        await browser.close()
        return lowest_items
