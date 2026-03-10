import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from auth_manager import AuthManager
from datetime import datetime

st.set_page_config(
    page_title="etnet YouTube Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'Get help': None, 'Report a bug': None, 'About': None}
)

# 初始化認證管理器
auth_manager = AuthManager()

# 初始化session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# ═══════════════════════════════════════════════════════════
# 側邊欄設計
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 用戶登入")
    
    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["登入", "註冊"])
        
        with tab1:
            st.subheader("登入帳戶")
            username = st.text_input("用戶名", key="login_user")
            password = st.text_input("密碼", type="password", key="login_pass")
            
            if st.button("🔓 登入", use_container_width=True, type="primary"):
                if auth_manager.authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = auth_manager.get_user_role(username)
                    st.rerun()
                else:
                    st.error("用戶名或密碼錯誤")
        
        with tab2:
            st.subheader("創建新帳戶")
            new_user = st.text_input("新用戶名", key="reg_user")
            new_pass = st.text_input("密碼（最少6位）", type="password", key="reg_pass")
            confirm_pass = st.text_input("確認密碼", type="password", key="reg_confirm")
            
            if st.button("✅ 註冊", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("密碼不相符")
                else:
                    success, msg = auth_manager.register(new_user, new_pass)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
    
    else:
        # 已登入狀態
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**身份：** {st.session_state.user_role}")
        
        if st.button("📤 登出", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()
        
        # 頁腳
        st.markdown("---")
        st.caption(f"上次登入：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ═══════════════════════════════════════════════════════════
# 登入頁面
# ═══════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align: center; padding: 50px 20px;'>
        <h1 style='font-size: 3em; margin-bottom: 10px;'>📺 etnet YouTube</h1>
        <h2 style='color: #FF0000; font-size: 2em;'>Analytics Dashboard</h2>
        <p style='font-size: 1.2em; color: #666;'>實時YouTube頻道數據分析平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👈 請在左側邊欄登入或註冊新帳戶", icon="ℹ️")
    
    st.markdown("---")
    
    # 功能介紹
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        #### 📊 實時數據
        - 頻道概覽統計
        - 訂閱數增長趨勢
        - 觀看次數分析
        """)
    with col2:
        st.markdown("""
        #### 💡 智能分析
        - 月度趨勢對比
        - 年度匯總統計
        - Engagement Rate追蹤
        """)
    with col3:
        st.markdown("""
        #### 🏆 內容分析
        - Top 影片排行
        - 互動率排名
        - 內容表現評估
        """)

else:
    # ═══════════════════════════════════════════════════════════
    # 主要Dashboard內容
    # ═══════════════════════════════════════════════════════════
    @st.cache_data
    def load_data():
        overview = pd.read_csv("data/channel_overview.csv")
        monthly  = pd.read_csv("data/monthly_analytics.csv")
        yearly   = pd.read_csv("data/yearly_analytics.csv")
        top      = pd.read_csv("data/top_videos_this_month.csv")
        # 確保數字欄位係數字
        for col in ["views","likes","comments","watch_minutes"]:
            for df in [monthly, yearly, top]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        return overview, monthly, yearly, top
    
    overview, monthly, yearly, top = load_data()

    # ── Channel Overview ──────────────────────────────────────
    st.header("📊 頻道概覽")
    cols = st.columns(len(overview))
    for i, row in overview.iterrows():
        name = row.get("channel_name") or row.get("channel_label","")
        with cols[i]:
            st.subheader(str(name))
            st.metric("訂閱數",    f"{int(row['subscribers']):,}")
            st.metric("總觀看次數", f"{int(row['total_views']):,}")
            st.metric("影片數量",   f"{int(row['video_count']):,}")

    # ── Monthly Views ─────────────────────────────────────────
    st.header("📈 每月觀看趨勢")
    monthly["month"] = monthly["month"].astype(str)
    fig = px.line(monthly, x="month", y="views", color="channel",
                  markers=True, title="Monthly Views by Channel")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    # ── Monthly Engagement Rate ───────────────────────────────
    st.header("💡 每月 Engagement Rate (%)")
    fig2 = px.bar(monthly, x="month", y="engagement_rate", color="channel",
                  barmode="group", title="Engagement Rate (%) by Month")
    fig2.update_xaxes(tickangle=45)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Yearly Summary ────────────────────────────────────────
    st.header("📅 年度匯總")
    yearly["year"] = yearly["year"].astype(str)
    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.bar(yearly, x="year", y="views", color="channel",
                      barmode="group", title="Yearly Views")
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        fig4 = px.bar(yearly, x="year", y="engagement_rate", color="channel",
                      barmode="group", title="Yearly Engagement Rate (%)")
        st.plotly_chart(fig4, use_container_width=True)

    # ── Top Videos This Month ─────────────────────────────────
    st.header("🏆 本月最受歡迎影片 Top 10")
    channels = top["channel"].unique().tolist()
    selected = st.selectbox("選擇頻道", channels)
    df_top = top[top["channel"] == selected].copy().reset_index(drop=True)
    df_top.index += 1
    df_top["video_url"] = df_top["video_url"].apply(
        lambda x: f'<a href="{x}" target="_blank">▶ 睇片</a>')
    st.write(
        df_top[["video_id","views","likes","comments","engagement_rate","video_url"]]
        .to_html(escape=False, index=True),
        unsafe_allow_html=True
    )
