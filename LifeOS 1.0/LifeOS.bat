@echo off
echo 正在启动 LifeOS 指挥部...

:: 1. 后台启动 Streamlit 服务
start /min cmd /c "streamlit run app.py"

:: 2. 等待 3 秒，确保服务已经跑起来了
timeout /t 3 >nul

:: 3. 用 Edge 的 APP 模式打开 (注意这里改成了 msedge)
start msedge --app=http://localhost:8501

exit