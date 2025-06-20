@echo off
chcp 65001 >nul
echo 学生拍照系统 - 电脑客户端
echo ============================
echo.
echo 正在启动程序...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show PyQt5 >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

REM 启动程序
echo 启动程序...
python run.py

if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查错误信息
    pause
)
