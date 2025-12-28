import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm # 引入字体管理
import numpy as np
import sqlite3
import requests
import time
import hashlib
import os
import base64
from datetime import datetime, timedelta

# === 1. 🎄 基础配置 & 纪念日 ===
LAUNCH_DATE = datetime(2025, 12, 25).date()
TODAY = datetime.now().date()
DAYS_RUNNING = (TODAY - LAUNCH_DATE).days + 1

# 隐藏侧边栏
st.set_page_config(
    page_title=f"🎄靖的LifeOS (Day {DAYS_RUNNING})", 
    page_icon="🎁", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

# 🛠️ 字体修复核心逻辑：优先找本地 font.ttf，找不到找系统盘，再不行回退英文
def get_font_prop():
    # 1. 优先检查目录下有没有 font.ttf (用户自己上传的)
    if os.path.exists("font.ttf"):
        return fm.FontProperties(fname="font.ttf")
    
    # 2. 检查常见的系统中文字体路径 (针对 Linux/Windows)
    common_fonts = [
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", # Linux 常见
        "C:\\Windows\\Fonts\\simhei.ttf", # Windows 黑体
        "C:\\Windows\\Fonts\\msyh.ttf",   # Windows 微软雅黑
        "/System/Library/Fonts/PingFang.ttc" # Mac
    ]
    for f in common_fonts:
        if os.path.exists(f):
            return fm.FontProperties(fname=f)
            
    # 3. 实在没有，就返回默认（可能会乱码，但至少不报错）
    return None 

# 获取字体属性对象
font_prop = get_font_prop()

# ❄️ 氛围：下雪
st.snow() 

# ==========================================
# 🎨 样式：零依赖安全版 (纯CSS实现，拒绝网络裂图)
# ==========================================
logo_html = ""
if os.path.exists("logo_day1.png"):
    try:
        with open("logo_day1.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}">'
    except: pass

if not logo_html:
    logo_html = """<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:white; border-radius:50%; font-size:40px;">🎁</div>"""

st.markdown(f"""
    <style>
        #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
        .block-container {{padding-top: 1rem;}}

        /* 🎄 全局红绿边框 */
        .stApp {{
            border: 8px solid transparent;
            border-image: linear-gradient(to bottom right, #d42e2e 0%, #2e8b57 100%);
            border-image-slice: 1;
            margin: 5px;
        }}

        /* 标题样式 */
        .main-title {{
            text-align: center; font-family: 'Arial Black', sans-serif; font-size: 2.5em;
            background: -webkit-linear-gradient(#d63031, #00b894); -webkit-background-clip: text;
            -webkit-text-fill-color: transparent; margin-top: 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}

        /* 右下角固定 Logo */
        .fixed-logo {{
            position: fixed; bottom: 20px; right: 20px; z-index: 9999;
            text-align: center; opacity: 0.9; transition: all 0.3s ease;
        }}
        .fixed-logo:hover {{ transform: scale(1.1); opacity: 1; }}
        .logo-container {{
            width: 80px; height: 80px; 
            border-radius: 50%; 
            border: 3px solid #d63031;
            box-shadow: 0 0 15px rgba(214, 48, 49, 0.5); 
            background: white;
            overflow: hidden; 
        }}
        
        /* 🎁 圣诞版：6大主题卡片 */
        .christmas-card {{
            background: white;
            border: 2px solid #e6e6e6;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 15px;
            transition: transform 0.2s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .christmas-card:hover {{
            transform: translateY(-3px);
            border-color: #2e8b57;
            box-shadow: 0 8px 15px rgba(46, 139, 87, 0.15);
        }}
        .candy-cane-bar {{ width: 100%; height: 10px; background-color: #f1f1f1; border-radius: 5px; overflow: hidden; margin-top: 8px; }}
        .candy-cane-fill {{ height: 100%; background: repeating-linear-gradient(45deg, #d63031, #d63031 10px, #ff7675 10px, #ff7675 20px); border-radius: 5px; }}

        /* 商店卡片 */
        .shop-item {{ background: white; border: 1px solid #eee; border-radius: 12px; padding: 15px; text-align: center; cursor: pointer; transition: 0.2s; }}
        .shop-item:hover {{ border-color: #d63031; box-shadow: 0 0 15px rgba(214, 48, 49, 0.2); }}

        /* CSS Banner 样式 */
        .christmas-banner {{
            background: linear-gradient(135deg, #d42e2e 0%, #2e8b57 100%);
            padding: 30px; border-radius: 20px; text-align: center; color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15); margin-bottom: 20px; border: 2px solid #fab1a0;
        }}
        .christmas-banner h1 {{ font-family: 'Arial Black', sans-serif; font-size: 2.8em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); color: #fff; }}
    </style>
    <div class="fixed-logo">
        <div class="logo-container">{logo_html}</div>
        <div style="font-size:10px; color:#d63031; font-weight:bold; background:white; padding:2px; border-radius:4px; margin-top:5px;">Day {DAYS_RUNNING}</div>
    </div>
""", unsafe_allow_html=True)

# === 2. 常量 & 数据库工具 ===
THEME_CONFIG = {
    "核心能力": {"icon": "🧠", "desc": "专业 / 算法"},
    "创新实践": {"icon": "🎄", "desc": "项目 / 代码"},
    "终身探索": {"icon": "🔭", "desc": "阅读 / 新知"},
    "身心健康": {"icon": "🦌", "desc": "运动 / 睡眠"},
    "社会连接": {"icon": "❄️", "desc": "人脉 / 演讲"},
    "审美修养": {"icon": "🎨", "desc": "艺术 / 设计"}
}
DEFAULT_GOODS = [{"name": "🥤 快乐水", "price": 60, "icon": "🥤"},{"name": "🎮 游戏时光", "price": 120, "icon": "🎮"},{"name": "🎁 圣诞盲盒", "price": 180, "icon": "🎁"},{"name": "🛌 赖床券", "price": 200, "icon": "🛌"},{"name": "🍰 生日蛋糕", "price": 0, "icon": "🎂"},{"name": "✈️ 旅行基金", "price": 5000, "icon": "✈️"}]

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

def init_db():
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS daily_log (date TEXT, emotion REAL, cognition REAL, awareness REAL, motivation REAL, interpersonal REAL, user_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS task_log (id INTEGER PRIMARY KEY AUTOINCREMENT, start_time TEXT, end_time TEXT, theme TEXT, task_name TEXT, duration_min INTEGER, ipo_stage TEXT, snap_emotion REAL, snap_cognition REAL, snap_awareness REAL, snap_motivation REAL, snap_social REAL, user_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS expense_log (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, item_name TEXT, cost INTEGER, user_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS weekly_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, start_date TEXT, end_date TEXT, content TEXT, user_id TEXT)')
    conn.commit(); conn.close()

def add_user(username, password):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    try: c.execute('INSERT INTO users VALUES (?,?)', (username, make_hashes(password))); conn.commit(); return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,)); data = c.fetchall(); conn.close()
    return check_hashes(password, data[0][0]) if data else False

# === 业务逻辑 ===
def save_status(scores, user_id):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("DELETE FROM daily_log WHERE date=? AND user_id=?", (today, user_id))
    c.execute("INSERT INTO daily_log VALUES (?,?,?,?,?,?,?)", (today, *scores, user_id)); conn.commit(); conn.close()
    st.toast("✅ 状态已同步！", icon="🎄")

def save_task(start, theme, task, duration, ipo, scores, user_id):
    conn = sqlite3.connect('life_os.db'); conn.execute("INSERT INTO task_log VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)", (start, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), theme, task, duration, ipo, *scores, user_id)); conn.commit(); conn.close()

def buy_item(name, price, user_id):
    conn = sqlite3.connect('life_os.db'); conn.execute("INSERT INTO expense_log VALUES (NULL,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, price, user_id)); conn.commit(); conn.close()

def get_finance_status(user_id):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    c.execute("SELECT SUM(duration_min) FROM task_log WHERE user_id=?", (user_id,)); inc = c.fetchone()[0] or 0
    c.execute("SELECT SUM(cost) FROM expense_log WHERE user_id=?", (user_id,)); exp = c.fetchone()[0] or 0
    conn.close(); return inc, exp, inc-exp

def get_theme_stats(user_id):
    conn = sqlite3.connect('life_os.db'); df = pd.read_sql_query("SELECT theme, SUM(duration_min) as total FROM task_log WHERE user_id=? GROUP BY theme", conn, params=(user_id,)); conn.close(); stats = {}
    for k in THEME_CONFIG.keys(): row = df[df['theme']==k]; total = row['total'].values[0] if not row.empty else 0; stats[k] = {"lvl": int(total/60), "prog": (total%60)/60*100, "total": total}
    return stats

def get_today_tasks(user_id):
    conn = sqlite3.connect('life_os.db'); 
    try: df = pd.read_sql_query("SELECT * FROM task_log WHERE user_id=? ORDER BY id DESC LIMIT 10", conn, params=(user_id,))
    except: df = pd.DataFrame()
    conn.close(); return df

def save_weekly_report(content, user_id):
    conn = sqlite3.connect('life_os.db'); today = datetime.now().strftime("%Y-%m-%d"); start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    conn.execute("INSERT INTO weekly_reports VALUES (NULL,?,?,?,?,?)", (today, start, today, content, user_id)); conn.commit(); conn.close()
    st.success("✅ 周报已归档！")

def get_past_reports(user_id):
    conn = sqlite3.connect('life_os.db')
    try: df = pd.read_sql_query("SELECT * FROM weekly_reports WHERE user_id=? ORDER BY id DESC", conn, params=(user_id,))
    except: df = pd.DataFrame()
    conn.close(); return df

def get_weekly_data(user_id):
    conn = sqlite3.connect('life_os.db'); end = datetime.now(); start = end - timedelta(days=7)
    t = pd.read_sql_query(f"SELECT * FROM task_log WHERE user_id='{user_id}' AND start_time > '{start}'", conn)
    e = pd.read_sql_query(f"SELECT * FROM expense_log WHERE user_id='{user_id}' AND date > '{start}'", conn)
    conn.close(); return t, e, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def call_deepseek_ai(prompt, key):
    if not key: return "⚠️ 请先在上方【驾驶舱】填入 API Key 🔑"
    try:
        res = requests.post("https://api.deepseek.com/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": "deepseek-chat", "messages": [{"role":"user","content":prompt}], "stream":False})
        return res.json()['choices'][0]['message']['content'] if res.status_code == 200 else f"API报错: {res.text}"
    except Exception as e: return str(e)

# === UI 组件 ===
def render_theme_card_christmas(name, data):
    conf = THEME_CONFIG[name]
    st.markdown(f"""
    <div class="christmas-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; align-items:center;">
                <div style="font-size:1.8rem; margin-right:10px;">{conf['icon']}</div>
                <div>
                    <div style="font-weight:bold; color:#2d3436; font-size:1.1rem;">{name}</div>
                    <div style="font-size:0.8rem; color:#888;">{conf['desc']}</div>
                </div>
            </div>
            <div style="text-align:right;">
                <span style="font-size:1.2rem; font-weight:900; color:#d63031;">Lv.{data['lvl']}</span>
                <div style="font-size:0.7rem; color:#aaa;">{int(data['total'])} min</div>
            </div>
        </div>
        <div class="candy-cane-bar"><div class="candy-cane-fill" style="width:{data['prog']}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)

# 🛠️ 雷达图修复版：支持自定义字体，防止乱码
def plot_radar_v2(scores):
    # 标签：如果没字体，就用英文防乱码
    if font_prop:
        labels = ['情绪', '认知', '觉察', '动机', '人际']
    else:
        labels = ['Emotion', 'Cognition', 'Awareness', 'Motivation', 'Social']

    angles = np.linspace(0, 2*np.pi, 5, endpoint=False).tolist()
    scores_plot = scores + scores[:1]; angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    fig.patch.set_alpha(0); ax.set_facecolor('#f8f9fa'); ax.spines['polar'].set_visible(False)
    
    # 关键修改：应用字体
    if font_prop:
        ax.set_xticklabels(labels, fontsize=10, fontweight='bold', fontproperties=font_prop)
    else:
        ax.set_xticklabels(labels, fontsize=10, fontweight='bold')

    ax.set_yticklabels([]); ax.set_xticks(angles[:-1]); 
    color = '#2e8b57' if sum(scores)/5 >= 6 else '#d63031' 
    ax.fill(angles, scores_plot, color=color, alpha=0.3); ax.plot(angles, scores_plot, color=color, linewidth=2)
    return fig

# 智能Banner (零依赖版)
def render_banner():
    has_image = False
    if os.path.exists("banner.png"):
        try: st.image("banner.png", use_container_width=True); has_image=True
        except: pass
    elif os.path.exists("banner.jpg"):
        try: st.image("banner.jpg", use_container_width=True); has_image=True
        except: pass
    if not has_image:
        st.markdown("""<div class="christmas-banner"><h1>🎄 LifeOS Cloud 🎅</h1><p>Merry Christmas & Happy Birthday!</p></div>""", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>🎄 LifeOS Cloud</h1>", unsafe_allow_html=True)

# === 5. 主程序 ===
def main():
    init_db()
    
    if "user" in st.query_params: 
        st.session_state.logged_in = True
        st.session_state.username = st.query_params["user"]
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'username' not in st.session_state: st.session_state.username = ""
    if 'timer_active' not in st.session_state: st.session_state.timer_active = False
    if 'deepseek_key' not in st.session_state: st.session_state.deepseek_key = ""

    # --- 登录界面 ---
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            render_banner()
            tab_login, tab_reg = st.tabs(["🔑 登录", "📝 注册"])
            with tab_login:
                username = st.text_input("用户名", key="login_user")
                password = st.text_input("密码", type="password", key="login_pass")
                if st.button("🚀 进入系统", use_container_width=True):
                    if login_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.query_params["user"] = username
                        st.rerun()
                    else: st.error("账号或密码错啦")
            with tab_reg:
                new_user = st.text_input("新用户名", key="reg_user")
                new_pass = st.text_input("设置密码", type="password", key="reg_pass")
                if st.button("✨ 创建账号", use_container_width=True):
                    if add_user(new_user, new_pass): st.success("注册成功！请登录")
                    else: st.error("用户名已存在")
        return

    # --- 已登录主界面 ---
    user_id = st.session_state.username
    inc, exp, bal = get_finance_status(user_id)
    today_tasks = get_today_tasks(user_id)
    today_min = today_tasks[today_tasks['end_time'].str.contains(datetime.now().strftime("%Y-%m-%d"))]['duration_min'].sum() if not today_tasks.empty else 0

    render_banner()

    # 🚀 驾驶舱 (含：音乐 + 系统管理 + 心情 + Key)
    with st.expander("🎅 个人驾驶舱 (音乐 / 设置 / 系统管理)", expanded=True):
        c_mood, c_key, c_music, c_sys = st.columns([1, 1, 1.2, 0.8])
        
        with c_mood: 
            mood = st.selectbox("📝 今日心情", ["开心 😄", "平静 😌", "疲惫 😫", "焦虑 😖", "期待 🤩", "过生日! 🎂"], index=5)
            st.caption(f"当前: {mood}")
            
        with c_key: 
            user_key = st.text_input("🔑 DeepSeek Key", type="password", value=st.session_state.deepseek_key)
            if user_key: st.session_state.deepseek_key = user_key
            
        with c_music:
            st.write("🎵 **圣诞八音盒**")
            music_file = "bgm.mp3" if os.path.exists("bgm.mp3") else "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3"
            st.audio(music_file, format="audio/mp3")
            
        with c_sys:
            st.write(f"👤 **{user_id}**")
            st.caption(f"🚀 Run: {DAYS_RUNNING} Days")
            if st.button("🚪 退出登录", type="secondary", use_container_width=True):
                st.session_state.logged_in = False
                st.query_params.clear()
                st.rerun()

    # HUD
    st.markdown(f"""<div style="display: flex; justify-content: space-between; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 15px 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #fff;"><div style="text-align: center; flex: 1;"><div style="font-size:12px; color:#888">WEALTH</div><div style="font-size: 24px; font-weight: 800; color:#d63031">¥ {bal}</div></div><div style="text-align: center; flex: 1;"><div style="font-size:12px; color:#888">FOCUS</div><div style="font-size: 24px; font-weight: 800; color:#2e8b57">{today_min} min</div></div><div style="text-align: center; flex: 1;"><div style="font-size:12px; color:#888">STATUS</div><div style="font-size: 24px; font-weight: 800; color:#e17055">Level Up</div></div></div>""", unsafe_allow_html=True)

    # 🚀 6大标签页
    t1, t2, t3, t4, t5, t6 = st.tabs(["⚔️ 作战中心", "🎁 商店", "📜 日志", "🤖 AI", "📝 周报", "📊 状态调控"])
    
    with t1:
        stats = get_theme_stats(user_id)
        cols = st.columns(3) + st.columns(3)
        for i, k in enumerate(THEME_CONFIG):
            with cols[i]:
                render_theme_card_christmas(k, stats[k])
        
        if not st.session_state.timer_active:
            st.divider()
            c1, c2, c3 = st.columns([2,1,1])
            with c1: task = st.text_input("当前任务")
            with c2: theme = st.selectbox("领域", list(THEME_CONFIG.keys()))
            with c3: ipo = st.selectbox("阶段", ["Input", "Process", "Output"])
            
            if st.button("🔥 开始专注", type="primary", use_container_width=True) and task: 
                st.session_state.timer_active=True
                st.session_state.start_time=datetime.now()
                st.session_state.current_theme=theme
                st.session_state.current_task=task
                st.session_state.current_ipo=ipo
                st.rerun()
        else:
            diff = datetime.now() - st.session_state.start_time
            mins = int(diff.total_seconds()/60)
            secs = int(diff.total_seconds()%60)
            
            # 🟢 倒计时修复：强制显示动态时间
            st.markdown(f"""
            <div style='text-align:center; padding:30px; background:#2d3436; color:white; border-radius:15px; margin-top:20px; border: 2px solid #d63031;'>
                <h2>🎄 专注中: {st.session_state.current_task}</h2>
                <h1 style='font-size:60px; font-family:monospace; color:#55efc4'>{mins:02d}:{secs:02d}</h1>
                <p>💡 请不要刷新页面，倒计时正在运行...</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🏁 完成任务", type="primary", use_container_width=True): 
                default_scores = [5,5,5,5,5]
                save_task(st.session_state.start_time.strftime("%Y-%m-%d %H:%M:%S"), st.session_state.current_theme, st.session_state.current_task, mins, st.session_state.current_ipo, default_scores, user_id)
                st.session_state.timer_active=False
                st.balloons()
                st.rerun()
            
            # 🟢 倒计时修复核心：每1秒强制刷新一次，让时间走起来！
            time.sleep(1)
            st.rerun()

    with t2:
        cols = st.columns(4)
        for i, item in enumerate(DEFAULT_GOODS):
            with cols[i%4]:
                st.markdown(f"<div class='shop-item'><h1>{item['icon']}</h1><b>{item['name']}</b><br><span style='color:#d63031; font-weight:bold;'>¥ {item['price']}</span></div>", unsafe_allow_html=True)
                if st.button("🎁 兑换", key=f"b{i}", use_container_width=True):
                    if bal >= item['price']: 
                        buy_item(item['name'], item['price'], user_id)
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else: st.error("金币不够啦")
    with t3: 
        st.dataframe(get_today_tasks(user_id)[['end_time','theme','task_name','duration_min','ipo_stage']], hide_index=True, use_container_width=True)
    with t4:
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        for msg in st.session_state.chat_history: st.chat_message(msg["role"]).write(msg["content"])
        if prompt := st.chat_input("输入问题..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."): 
                    reply = call_deepseek_ai(prompt, st.session_state.deepseek_key)
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    with t5:
        t, e, d1, d2 = get_weekly_data(user_id)
        st.info(f"📅 统计范围: {d1} 至 {d2}")
        if st.button("⚡ 生成本周周报"):
            if t.empty: st.warning("本周暂无数据")
            else:
                with st.spinner("撰写中..."): 
                    st.session_state.current_report = call_deepseek_ai(f"我是{user_id}。根据本周数据(专注{t['duration_min'].sum()}分钟, 消费{e['cost'].sum()}, 完成{len(t)}任务)，写一份温馨幽默的圣诞生日周报。", st.session_state.deepseek_key)
        if "current_report" in st.session_state:
            st.write(st.session_state.current_report)
            if st.button("💾 归档保存"): 
                save_weekly_report(st.session_state.current_report, user_id)
                del st.session_state.current_report
                st.rerun()
        st.markdown("---")
        st.subheader("🗄️ 往期周报档案")
        reports = get_past_reports(user_id)
        if reports.empty: st.caption("暂无历史存档")
        else:
            for i, row in reports.iterrows(): 
                with st.expander(f"📅 {row['date']} (存档 #{row['id']})"): 
                    st.write(row['content'])
            
    # === 新增：状态调控 Tab ===
    with t6:
        st.subheader("📊 核心状态调控中心")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.write("请为当下的状态打分 (0-10):")
            scores = [st.slider(l,0,10,5, key=f"s_{i}") for i, l in enumerate(["情绪","认知","觉察","动机","人际"])]
            st.write("")
            if st.button("📡 同步状态数据", type="primary", use_container_width=True):
                save_status(scores, user_id)
        with c2:
            st.write("当前五维能力雷达图:")
            # 🛡️ 字体状态检测提示
            if font_prop:
                st.success(f"✅ 已加载字体: {font_prop.get_name()}")
            else:
                st.warning("⚠️ 未检测到中文字体，雷达图将暂时显示英文以防止乱码。请上传 font.ttf 修复。")
            fig = plot_radar_v2(scores)
            st.pyplot(fig, use_container_width=True)

if __name__ == "__main__":
    main()