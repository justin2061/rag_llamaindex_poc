@echo off
setlocal enabledelayedexpansion

REM Graph RAG 智能文檔問答系統 Docker 部署腳本 (Windows)

echo 🚀 Graph RAG 智能文檔問答系統 Docker 部署
echo ================================================

REM 檢查 Docker 和 Docker Compose
:check_docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安裝，請先安裝 Docker Desktop
    echo    下載地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Docker Compose 未安裝，請確保 Docker Desktop 包含 Compose
        pause
        exit /b 1
    )
    set "DOCKER_COMPOSE=docker compose"
) else (
    set "DOCKER_COMPOSE=docker-compose"
)

echo ✅ Docker 環境檢查通過

REM 檢查 .env 檔案
:check_env
if not exist ".env" (
    echo ⚠️ .env 檔案不存在，正在創建範本...
    (
        echo # API 設定
        echo GROQ_API_KEY=your_groq_api_key_here
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo.
        echo # Graph RAG 設定
        echo ENABLE_GRAPH_RAG=true
        echo MAX_TRIPLETS_PER_CHUNK=10
        echo GRAPH_COMMUNITY_SIZE=5
        echo.
        echo # 檔案上傳設定
        echo MAX_FILE_SIZE_MB=10
        echo MAX_IMAGE_SIZE_MB=5
        echo.
        echo # 系統設定
        echo CONVERSATION_MEMORY_STEPS=5
        echo MAX_CONTEXT_LENGTH=4000
        echo ENABLE_CONVERSATION_MEMORY=true
        echo ENABLE_OCR=true
    ) > .env
    
    echo 📝 請編輯 .env 檔案並設定您的 API 金鑰
    echo    - GROQ_API_KEY: 必需，用於 LLM
    echo    - GEMINI_API_KEY: 可選，用於 OCR 功能
    echo.
    set /p edit_env="是否現在編輯 .env 檔案？(y/N): "
    if /i "!edit_env!"=="y" (
        notepad .env
    )
) else (
    echo ✅ .env 檔案存在
)

REM 檢查 API 金鑰
:check_api_keys
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if "%%a"=="GROQ_API_KEY" set "GROQ_API_KEY=%%b"
)

if "!GROQ_API_KEY!"=="your_groq_api_key_here" (
    echo ⚠️ 請在 .env 檔案中設定有效的 GROQ_API_KEY
    echo    取得金鑰: https://console.groq.com/keys
    pause
    exit /b 1
)

if "!GROQ_API_KEY!"=="" (
    echo ⚠️ 請在 .env 檔案中設定有效的 GROQ_API_KEY
    echo    取得金鑰: https://console.groq.com/keys
    pause
    exit /b 1
)

echo ✅ API 金鑰檢查通過

REM 創建必要目錄
:create_directories
echo 📁 創建必要目錄...
if not exist "data" mkdir data
if not exist "data\pdfs" mkdir data\pdfs
if not exist "data\index" mkdir data\index
if not exist "data\user_uploads" mkdir data\user_uploads
if not exist "data\chroma_db" mkdir data\chroma_db
echo ✅ 目錄創建完成

REM 構建並啟動服務
:deploy_services
echo 🔨 構建 Docker 映像...

REM 構建映像
%DOCKER_COMPOSE% build --no-cache
if %errorlevel% neq 0 (
    echo ❌ Docker 映像構建失敗
    pause
    exit /b 1
)

echo 🚀 啟動服務...
%DOCKER_COMPOSE% up -d
if %errorlevel% neq 0 (
    echo ❌ 服務啟動失敗
    pause
    exit /b 1
)

echo 📊 檢查服務狀態...
timeout /t 10 /nobreak >nul
%DOCKER_COMPOSE% ps

REM 顯示部署資訊
:show_deployment_info
echo.
echo 🎉 部署完成！
echo ================================================
echo 🌐 主應用程式: http://localhost:8501
echo 🗄️ ChromaDB 管理: http://localhost:8000
echo.
echo 📋 常用命令:
echo    查看日誌: %DOCKER_COMPOSE% logs -f
echo    停止服務: %DOCKER_COMPOSE% down
echo    重啟服務: %DOCKER_COMPOSE% restart
echo    查看狀態: %DOCKER_COMPOSE% ps
echo.
echo 🔧 如需重新部署:
echo    %DOCKER_COMPOSE% down ^&^& %DOCKER_COMPOSE% up -d --build
echo.

echo ✅ Graph RAG 系統部署完成！
echo.
echo 按任意鍵開啟瀏覽器...
pause >nul
start http://localhost:8501

endlocal
