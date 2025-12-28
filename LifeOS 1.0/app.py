import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import requests
import time
from datetime import datetime, timedelta

# === 1. 全局配置 & 终极 CSS 美化 ===
st.set_page_config(page_title="LifeOS Command", page_icon="🦁", layout="wide", initial_sidebar_state="expanded")
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 注入 CSS：这是让应用变美的魔法
st.markdown("""
    <style>
        /* 1. 全局去噪 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        
        /* 2. 顶部 HUD 仪表盘样式 */
        .hud-container {
            display: flex; justify-content: space-between; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 15px 25px; border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 25px; border: 1px solid #ffffff;
        }
        .hud-item { text-align: center; flex: 1; }
        .hud-label { font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; }
        .hud-value { font-size: 24px; font-weight: 800; color: #2d3436; margin-top: 5px; }
        .hud-icon { font-size: 20px; margin-right: 5px; }

        /* 3. 领域卡片 (战力) */
        .theme-card {
            background-color: white; border-radius: 12px; padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03); border: 1px solid #f1f3f5;
            transition: all 0.2s ease; margin-bottom: 15px;
        }
        .theme-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
        .theme-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .theme-icon { font-size: 1.5rem; background: #f8f9fa; padding: 8px; border-radius: 8px; }
        .theme-name { font-weight: bold; font-size: 1rem; color: #343a40; margin-left: 10px; }
        .theme-lvl { font-size: 0.8rem; font-weight: bold; color: #adb5bd; background: #f1f3f5; padding: 2px 8px; border-radius: 10px; }

        /* 4. 商店卡片 */
        .shop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; }
        .shop-item {
            background: white; border: 1px solid #eee; border-radius: 12px; padding: 15px;
            text-align: center; cursor: pointer; transition: 0.2s; position: relative; overflow: hidden;
        }
        .shop-item:hover { border-color: #ffd700; box-shadow: 0 0 10px rgba(255, 215, 0, 0.2); }
        .shop-price { 
            background: #fff9db; color: #f59f00; font-weight: bold; 
            padding: 2px 8px; border-radius: 4px; font-size: 0.9em; margin-top: 8px; display: inline-block;
        }

        /* 5. 侧边栏优化 */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
        
        /* 6. 进度条美化 */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        }
    </style>
""", unsafe_allow_html=True)

# === 2. 常量配置 ===
THEME_CONFIG = {
    "核心能力": {"icon": "🧠", "color": "#FF6B6B", "desc": "算法 / 逻辑 / 专业课"},
    "创新实践": {"icon": "⚡", "color": "#FFD93D", "desc": "代码 / 项目 / 创业"},
    "终身探索": {"icon": "🔭", "color": "#4D96FF", "desc": "阅读 / 纪录片 / 新知"},
    "身心健康": {"icon": "🧘", "color": "#6BCB77", "desc": "冥想 / 运动 / 睡眠"},
    "社会连接": {"icon": "🤝", "color": "#A020F0", "desc": "人脉 / 约会 / 演讲"},
    "审美修养": {"icon": "🎨", "color": "#FF69B4", "desc": "设计 / 音乐 / 艺术"}
}

DEFAULT_GOODS = [
    {"name": "🥤 快乐水/奶茶", "price": 60, "icon": "🥤"},
    {"name": "🎮 游戏一局", "price": 40, "icon": "🎮"},
    {"name": "🍿 追番/电影", "price": 120, "icon": "🎬"},
    {"name": "🛌 赖床券", "price": 180, "icon": "🛌"},
    {"name": "⌨️ 极客外设", "price": 1000, "icon": "⌨️"},
    {"name": "✈️ 说走就走", "price": 5000, "icon": "✈️"}
]

# === 3. 数据库与后端逻辑 (保持 V10.0 核心不变) ===
def init_db():
    conn = sqlite3.connect('life_os.db')
    c = conn.cursor()
    tables = [
        "CREATE TABLE IF NOT EXISTS daily_log (date TEXT, emotion REAL, cognition REAL, awareness REAL, motivation REAL, interpersonal REAL)",
        "CREATE TABLE IF NOT EXISTS task_log (id INTEGER PRIMARY KEY AUTOINCREMENT, start_time TEXT, end_time TEXT, theme TEXT, task_name TEXT, duration_min INTEGER, ipo_stage TEXT, snap_emotion REAL, snap_cognition REAL, snap_awareness REAL, snap_motivation REAL, snap_social REAL)",
        "CREATE TABLE IF NOT EXISTS expense_log (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, item_name TEXT, cost INTEGER)",
        "CREATE TABLE IF NOT EXISTS weekly_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, start_date TEXT, end_date TEXT, content TEXT)"
    ]
    for t in tables: c.execute(t)
    conn.commit(); conn.close()

# ... (保留原有的 save_status, save_task, buy_item, get_finance_status 等所有逻辑函数，此处省略重复代码以节省篇幅，实际运行时请确保包含 V10.0 的所有函数) ...
# 为了代码完整性，这里我把必须的函数简写放上：

def save_status(scores):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("DELETE FROM daily_log WHERE date=?", (today,))
    c.execute("INSERT INTO daily_log VALUES (?,?,?,?,?,?)", (today, *scores))
    conn.commit(); conn.close()
    st.toast("✅ 状态已校准", icon="📡")

def save_task(start, theme, task, duration, ipo, scores):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO task_log VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)", (start, end, theme, task, duration, ipo, *scores))
    conn.commit(); conn.close()

def buy_item(name, price):
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    c.execute("INSERT INTO expense_log VALUES (NULL,?,?,?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, price))
    conn.commit(); conn.close()

def get_finance_status():
    conn = sqlite3.connect('life_os.db'); c = conn.cursor()
    c.execute("SELECT SUM(duration_min) FROM task_log"); inc = c.fetchone()[0] or 0
    c.execute("SELECT SUM(cost) FROM expense_log"); exp = c.fetchone()[0] or 0
    conn.close(); return inc, exp, inc-exp

def get_theme_stats():
    conn = sqlite3.connect('life_os.db'); df = pd.read_sql_query("SELECT theme, SUM(duration_min) as total FROM task_log GROUP BY theme", conn); conn.close()
    stats = {}
    for k in THEME_CONFIG.keys():
        row = df[df['theme']==k]; total = row['total'].values[0] if not row.empty else 0
        stats[k] = {"lvl": int(total/60), "prog": (total%60)/60*100, "total": total}
    return stats

def get_today_tasks():
    conn = sqlite3.connect('life_os.db'); df = pd.read_sql_query("SELECT * FROM task_log ORDER BY id DESC LIMIT 10", conn); conn.close(); return df

def get_weekly_data():
    conn = sqlite3.connect('life_os.db')
    end = datetime.now(); start = end - timedelta(days=7)
    t = pd.read_sql_query(f"SELECT * FROM task_log WHERE start_time > '{start}'", conn)
    e = pd.read_sql_query(f"SELECT * FROM expense_log WHERE date > '{start}'", conn)
    s = pd.read_sql_query(f"SELECT * FROM daily_log WHERE date > '{start.strftime('%Y-%m-%d')}'", conn)
    conn.close(); return t, e, s, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def get_achievements(inc):
    badges = []
    if inc >= 60: badges.append("🥉 新手")
    if inc >= 500: badges.append("🥈 熟练")
    if inc >= 2000: badges.append("🥇 专家")
    return badges

def call_deepseek_ai(prompt, key):
    if not key: return "⚠️ 请在侧边栏填入 API Key"
    try:
        res = requests.post("https://api.deepseek.com/chat/completions", 
                            headers={"Authorization": f"Bearer {key}"}, 
                            json={"model": "deepseek-chat", "messages": [{"role":"user","content":prompt}], "stream":False})
        return res.json()['choices'][0]['message']['content'] if res.status_code==200 else res.text
    except Exception as e: return str(e)

# === 4. UI 组件渲染函数 ===

def render_hud(balance, today_min, avg_score):
    """渲染顶部的抬头显示器"""
    st.markdown(f"""
    <div class="hud-container">
        <div class="hud-item">
            <div class="hud-label">💎 财富储备</div>
            <div class="hud-value" style="color:#d63031">{balance} <span style="font-size:14px">G</span></div>
        </div>
        <div class="hud-item" style="border-left: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0;">
            <div class="hud-label">⚡ 今日专注</div>
            <div class="hud-value" style="color:#0984e3">{today_min} <span style="font-size:14px">min</span></div>
        </div>
        <div class="hud-item">
            <div class="hud-label">🧬 机体状态</div>
            <div class="hud-value" style="color:#00b894">{avg_score:.1f} <span style="font-size:14px">/10</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_theme_card_v2(name, data):
    """渲染更漂亮的卡片"""
    conf = THEME_CONFIG[name]
    st.markdown(f"""
    <div class="theme-card">
        <div class="theme-header">
            <div style="display:flex; align-items:center">
                <div class="theme-icon">{conf['icon']}</div>
                <div>
                    <div class="theme-name">{name}</div>
                    <div style="font-size:10px; color:#999; margin-left:10px">{conf['desc']}</div>
                </div>
            </div>
            <div class="theme-lvl">Lv.{data['lvl']}</div>
        </div>
        <div style="background:#f1f3f5; height:6px; border-radius:3px; overflow:hidden;">
            <div style="width:{data['prog']}%; height:100%; background:linear-gradient(90deg, {conf['color']}, #8e44ad); border-radius:3px;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:10px; color:#adb5bd;">
            <span>{int(data['prog'])}% to Next Lv</span>
            <span>Total: {data['total']}m</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def plot_radar_v2(scores):
    labels = ['情绪', '认知', '觉察', '动机', '人际']
    angles = np.linspace(0, 2*np.pi, 5, endpoint=False).tolist()
    scores += scores[:1]; angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(polar=True))
    fig.patch.set_alpha(0); ax.set_facecolor('#f8f9fa')
    
    # 移除多余的边框和刻度
    ax.spines['polar'].set_visible(False)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9, color="#636e72")
    
    color = '#6c5ce7' if sum(scores[:-1])/5 >= 6 else '#ff7675'
    ax.fill(angles, scores, color=color, alpha=0.2)
    ax.plot(angles, scores, color=color, linewidth=2)
    return fig

# === 5. 主程序 ===
def main():
    init_db()
    if 'timer_active' not in st.session_state: st.session_state.timer_active = False

    # 计算核心数据
    income, expense, balance = get_finance_status()
    today_tasks = get_today_tasks()
    today_min = today_tasks[today_tasks['end_time'].str.contains(datetime.now().strftime("%Y-%m-%d"))]['duration_min'].sum()
    
    # --- 侧边栏 (控制台) ---
    with st.sidebar:
        st.header("🎛️ 控制台")
        st.caption("调整你的机体参数")
        
        emotion = st.slider("情绪", 0, 10, 5)
        cognition = st.slider("认知", 0, 10, 5)
        awareness = st.slider("觉察", 0, 10, 5)
        motivation = st.slider("动机", 0, 10, 5)
        social = st.slider("人际", 0, 10, 5)
        scores = [emotion, cognition, awareness, motivation, social]
        
        if st.button("📡 同步状态", use_container_width=True): save_status(scores)
        
        st.markdown("---")
        st.pyplot(plot_radar_v2(list(scores)))
        
        st.markdown("---")
        api_key = st.text_input("🔑 DeepSeek API", type="password")

    # --- 主界面 ---
    
    # 1. 顶部 HUD
    render_hud(balance, today_min, sum(scores)/5)

    # 2. 标签页导航
    tab1, tab2, tab3, tab4 = st.tabs(["⚔️ 专注作战", "🏪 补给商店", "📜 战地日志", "🧠 战略中枢"])

    # === Tab 1: 作战 (Dashboard) ===
    with tab1:
        # 六维战力卡片
        theme_stats = get_theme_stats()
        cols = st.columns(3) + st.columns(3)
        for i, key in enumerate(THEME_CONFIG.keys()):
            with cols[i]: render_theme_card_v2(key, theme_stats[key])
        
        st.divider()
        
        # 专注引擎
        if not st.session_state.timer_active:
            st.markdown("#### 🚀 启动任务")
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: task = st.text_input("任务目标", placeholder="例如：完成 Python 大作业...")
            with c2: theme = st.selectbox("关联领域", list(THEME_CONFIG.keys()))
            with c3: ipo = st.selectbox("流程", ["Input (摄入)", "Process (内化)", "Output (产出)"])
            
            if st.button("🔥 立即执行", type="primary", use_container_width=True):
                if task:
                    st.session_state.timer_active = True
                    st.session_state.start_time = datetime.now()
                    st.session_state.current_theme = theme
                    st.session_state.current_task = task
                    st.session_state.current_ipo = ipo.split()[0] # 只取英文
                    st.rerun()
        else:
            # 沉浸式计时器
            diff = datetime.now() - st.session_state.start_time
            mins = int(diff.total_seconds()/60); secs = int(diff.total_seconds()%60)
            
            st.markdown(f"""
            <div style="text-align:center; padding: 40px; background:#2d3436; border-radius:20px; color:white; margin-bottom:20px">
                <div style="font-size:20px; opacity:0.8">正在执行: {st.session_state.current_theme}</div>
                <div style="font-size:40px; font-weight:bold; margin:10px 0">{st.session_state.current_task}</div>
                <div style="font-size:80px; font-family:monospace; color:#00cec9">{mins:02d}:{secs:02d}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🏁 任务完成 (结算奖励)", type="primary", use_container_width=True):
                save_task(st.session_state.start_time.strftime("%Y-%m-%d %H:%M:%S"), 
                          st.session_state.current_theme, st.session_state.current_task, 
                          mins, st.session_state.current_ipo, scores)
                st.session_state.timer_active = False; st.balloons(); st.rerun()
            
            time.sleep(1); st.rerun()

    # === Tab 2: 商店 ===
    with tab2:
        st.info(f"💳 当前余额: {balance} G —— 保持渴望，保持愚蠢。")
        cols = st.columns(4)
        for i, item in enumerate(DEFAULT_GOODS):
            with cols[i%4]:
                st.markdown(f"""
                <div class="shop-item">
                    <div style="font-size:2.5em; margin-bottom:10px">{item['icon']}</div>
                    <div style="font-weight:bold; font-size:1.1em">{item['name']}</div>
                    <div class="shop-price">{item['price']} G</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"兑换", key=f"btn_{i}", use_container_width=True):
                    if balance >= item['price']:
                        buy_item(item['name'], item['price'])
                        st.balloons(); st.toast(f"🎉 兑换成功: {item['name']}")
                        time.sleep(1); st.rerun()
                    else: st.error("余额不足")

    # === Tab 3: 日志 ===
    with tab3:
        st.markdown("#### 📜 近期行动流")
        df = get_today_tasks()
        st.dataframe(df[['end_time', 'theme', 'task_name', 'duration_min', 'ipo_stage']], use_container_width=True, hide_index=True)

    # === Tab 4: 战略中枢 ===
    with tab4:
        st.markdown("#### 🧠 AI 首席幕僚")
        st.caption("基于 DeepSeek V3 模型，为你提供周报复盘与战略指导。")
        if st.button("🤖 生成本周深度复盘", type="primary"):
            t, e, s, d1, d2 = get_weekly_data()
            if t.empty: st.warning("数据不足，无法分析。")
            else:
                prompt = f"分析这周数据：总专注{t['duration_min'].sum()}分钟，主要在{t['theme'].mode()[0]}领域。消费{e['cost'].sum()}G。状态均值{s['motivation'].mean()}。请给出毒舌但有用的建议。"
                with st.spinner("正在连接神经网络..."):
                    res = call_deepseek_ai(prompt, api_key)
                    st.markdown(res)

if __name__ == "__main__":
    main()