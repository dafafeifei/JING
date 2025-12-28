@echo off
echo ==========================================
echo 正在为您配置 LifeOS 运行环境...
echo ==========================================
echo.
echo [1/2] 正在升级 pip 工具...
python -m pip install --upgrade pip
echo.
echo [2/2] 正在安装核心库 (Streamlit, Pandas, Matplotlib)...
python -m pip install streamlit pandas matplotlib requests
echo.
echo ==========================================
echo ✅ 环境配置完成！
echo 请直接双击“启动LifeOS.bat”进入系统。
echo ==========================================
pause