# server.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from crawlers.gmarket import crawl_gmarket
from crawlers.elevenst import crawl_elevenst
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Python FastAPI 서버 정상 동작 중"}

@app.post("/crawl")
async def crawl(request: Request):
    try:
        body = await request.json()

        site = body.get("site", "gmarket")
        keyword = body.get("keyword")
        include = body.get("include", [])
        exclude = body.get("exclude", [])
        min_price = int(body.get("minPrice") or body.get("min_price") or 0)
        max_price = int(body.get("maxPrice") or body.get("max_price") or 999999999)

        if site == "gmarket":
            result = await crawl_gmarket(keyword, include, exclude, min_price, max_price)
        elif site == "11st":
            result = await crawl_elevenst(keyword, include, exclude, min_price, max_price)
        else:
            return JSONResponse(
                content={"success": False, "error": f"지원하지 않는 사이트: {site}"},
                status_code=400
            )

        return JSONResponse(content={"success": True, "result": result})

    except Exception as e:
        # 🚨 예외 발생 시 무조건 JSON 반환 (HTML 방지)
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
