@echo off
echo 🚀 Docker 快速構建腳本 (Windows)
echo ========================

REM 檢查 Docker 狀態
echo 📋 檢查 Docker 狀態...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安裝或未啟動
    pause
    exit /b 1
)

REM 顯示目錄大小
echo 📊 分析目錄大小...
echo 當前目錄內容：
dir /s *.py 2>nul | find "File(s)"
echo.
echo data 目錄內容：
if exist data\ (
    dir data\ /s 2>nul | find "File(s)"
) else (
    echo data 目錄不存在
)

REM 清理選項
echo.
set /p cleanup="🧹 是否要清理 Docker 緩存？(y/N): "
if /i "%cleanup%"=="y" (
    echo 清理 Docker 緩存...
    docker system prune -f
    docker image prune -f
)

REM 檢查 .dockerignore
echo.
echo 📋 檢查 .dockerignore 設定...
if not exist .dockerignore (
    echo ❌ 找不到 .dockerignore 文件
    pause
    exit /b 1
)

echo ✅ .dockerignore 存在

REM 選擇構建模式
echo.
echo 🔧 選擇構建模式...
echo 1) 開發模式 (代碼 volume 掛載，快速)
echo 2) 生產模式 (代碼複製到容器)
set /p mode="請選擇模式 (1/2，默認 1): "

if "%mode%"=="2" (
    echo.
    echo 🚀 開始生產模式構建...
    echo 使用命令：docker-compose -f docker-compose.prod.yml build --no-cache
    
    set start_time=%time%
    docker-compose -f docker-compose.prod.yml build --no-cache
    set compose_file=docker-compose.prod.yml
) else (
    echo.
    echo 🚀 開始開發模式構建...
    echo 使用命令：docker-compose build --no-cache
    echo 注意：代碼將通過 volume 掛載，構建會更快
    
    set start_time=%time%
    docker-compose build --no-cache
    set compose_file=docker-compose.yml
)

if errorlevel 1 (
    echo ❌ 構建失敗
    pause
    exit /b 1
)

set end_time=%time%
echo ✅ 構建成功！

echo.
echo 🚀 啟動服務...
docker-compose -f %compose_file% up -d

if errorlevel 1 (
    echo ❌ 啟動失敗
    pause
    exit /b 1
)

echo ✅ 服務已啟動！
echo 訪問地址：http://localhost:8501
echo 查看日誌：docker-compose logs -f

echo.
echo 🎉 完成！
pause