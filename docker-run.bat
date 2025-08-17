@echo off
REM Docker 運行腳本 - 台灣茶葉知識RAG系統 (Windows版本)

echo 🚀 啟動台灣茶葉知識RAG系統 Docker 容器...

REM 檢查 .env 檔案是否存在
if not exist ".env" (
    echo ⚠️  警告: .env 檔案不存在
    echo 請創建 .env 檔案並設定 GROQ_API_KEY
    echo 範例內容:
    echo GROQ_API_KEY=your_groq_api_key_here
    pause
    exit /b 1
)

REM 創建必要的目錄
if not exist "data\pdfs" mkdir data\pdfs
if not exist "data\index" mkdir data\index

REM 建立 Docker 映像
echo 📦 建立 Docker 映像...
docker build -t taiwan-tea-rag .

REM 停止現有容器
echo 🛑 停止現有容器...
docker stop taiwan-tea-rag 2>nul
docker rm taiwan-tea-rag 2>nul

REM 啟動新容器
echo 🐳 啟動新容器...
docker run -d ^
  --name taiwan-tea-rag ^
  -p 8620:8501 ^
  -v "%cd%\data:/app/data" ^
  -v "%cd%\.env:/app/.env" ^
  --restart unless-stopped ^
  taiwan-tea-rag

REM 等待容器啟動
timeout /t 5 /nobreak >nul

REM 檢查容器狀態
docker ps | findstr taiwan-tea-rag >nul
if %errorlevel%==0 (
    echo ✅ 容器成功啟動!
    echo 🌐 應用程式網址: http://localhost:8620
    echo 📊 查看容器日誌: docker logs -f taiwan-tea-rag
    echo 🛑 停止容器: docker stop taiwan-tea-rag
) else (
    echo ❌ 容器啟動失敗，查看日誌:
    docker logs taiwan-tea-rag
)

pause 