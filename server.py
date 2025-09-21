# server.py
from fastapi import FastAPI, Request, BackgroundTasks
from crawlers.gmarket import crawl_gmarket
from crawlers.elevenst import crawl_elevenst
import uvicorn
import os
import httpx
from datetime import datetime

# ✅ 로컬 환경에서만 .env 로드
if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

STRAPI_API_URL = os.getenv("STRAPI_API_URL")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Python FastAPI 서버 정상 동작 중"}


# ✅ 오늘 날짜 기준으로 Strapi 데이터 정리 + 저장
async def save_to_strapi(results):
    if not results or not STRAPI_API_URL:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    site = results[0].get("site")

    async with httpx.AsyncClient() as client:
        try:
            # 1. 오늘 날짜 + 사이트 기준으로 기존 데이터 조회
            query = f"filters[date][$eq]={today}&filters[site][$eq]={site}"
            check_res = await client.get(
                f"{STRAPI_API_URL}/crawls?{query}",
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )
            check_data = check_res.json().get("data", [])

            # 2. 기존 데이터 있으면 전부 삭제
            if check_data:
                print("🗑 오늘 기존 데이터 삭제")
                for item in check_data:
                    item_id = item.get("id")
                    if item_id:
                        await client.delete(
                            f"{STRAPI_API_URL}/crawls/{item_id}",
                            headers={"Content-Type": "application/json"},
                            timeout=30.0,
                        )

            # 3. 새 데이터 전부 저장
            for result in results:
                await client.post(
                    f"{STRAPI_API_URL}/crawls",
                    headers={"Content-Type": "application/json"},
                    json={"data": result},
                    timeout=30.0,
                )

            print(f"✅ Strapi 저장 완료: {len(results)} 개")

        except Exception as e:
            print("❌ Strapi 저장 오류:", e)


@app.post("/crawl")
async def crawl(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    site = body.get("site", "gmarket")
    keyword = body.get("keyword")
    include = body.get("include", [])
    exclude = body.get("exclude", [])
    min_price = int(body.get("minPrice") or body.get("min_price") or 0)
    max_price = int(body.get("maxPrice") or body.get("max_price") or 999999999)

    async def crawl_and_save():
        result = []
        if site == "gmarket":
            result = await crawl_gmarket(keyword, include, exclude, min_price, max_price)
        elif site == "11st":
            result = await crawl_elevenst(keyword, include, exclude, min_price, max_price)
        else:
            print("❌ 지원하지 않는 사이트:", site)
            return
        await save_to_strapi(result)

    # ✅ 백그라운드 작업으로 실행
    background_tasks.add_task(crawl_and_save)

    return {"success": True, "message": "크롤링 작업이 시작되었습니다."}


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
