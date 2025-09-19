# --- Base 이미지 ---
    FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

    # --- 작업 디렉토리 ---
    WORKDIR /app
    
    # --- requirements 설치 ---
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # --- 앱 코드 복사 ---
    COPY . .
    
    # --- 포트 열기 ---
    EXPOSE 8000
    
    # --- 실행 커맨드 ---
    CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
    