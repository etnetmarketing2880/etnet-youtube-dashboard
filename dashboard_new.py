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

# 自定義CSS樣式
st.markdown("""
<style>
    :root {
        --primary-color: #FF0000;
        --secondary-color: #282D33;
        --accent-color: #E60000;
    }
    
    .main {
        background-color: #f5f5f5;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    h1, h2, h3 {
        color: #282D33;
    }
</style>
""", unsafe_allow_html=True)

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
                    st.success("登入成功！")
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
        
        st.divider()
        
        if st.button("📤 登出", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.success("已登出")
            st.rerun()
        
        # 頁腳
        st.markdown("---")
        st.caption(f"登入時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ═══════════════════════════════════════════════════════════
# 登入頁面
# ═══════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align: center; padding: 50px 20px;'>
        <h1 style='font-size: 3em; margin-bottom: 10px; color: #FF0000;'>📺 etnet YouTube</h1>
        <h2 style='color: #282D33; font-size: 2em;'>Analytics Dashboard</h2>
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
    
    # 加載數據
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
    
    # 主標題
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #FF0000; margin-bottom: 5px;'>📺 YouTube Analytics Dashboard</h1>
        <p style='color: #666;'>數據來源：YouTube Analytics API｜每日自動更新</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 標籤頁設計
    tab1, tab2, tab3, tab4 = st.tabs(["📊 概覽", "📈 趨勢分析", "📅 年度匯總", "🏆 Top 影片"])
    
    # ─────────────────────────────────────────────────────────
    # TAB 1: 頻道概覽
    # ─────────────────────────────────────────────────────────
    with tab1:
        st.header("頻道概覽")
        st.markdown("實時頻道統計數據")
        
        cols = st.columns(len(overview))
        for i, row in overview.iterrows():
            name = row.get("channel_name") or row.get("channel_label","")
            with cols[i]:
                st.markdown(f"""
                <div style='background: white; padding: 20px; border-radius: 10px; 
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h3 style='color: #FF0000;'>{name}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("訂閱數", f"{int(row['subscribers']):,}", 
                             delta=None, delta_color="off")
                with col2:
                    st.metric("影片數量", f"{int(row['video_count']):,}",
                             delta=None, delta_color="off")
                
                st.metric("總觀看次數", f"{int(row['total_views']):,}",
                         delta=None, delta_color="off")
    
    # ─────────────────────────────────────────────────────────
    # TAB 2: 月度趨勢
    # ─────────────────────────────────────────────────────────
    with tab2:
        st.header("月度趨勢分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("每月觀看次數")
            monthly["month"] = monthly["month"].astype(str)
            fig = px.line(
                monthly, 
                x="month", 
                y="views", 
                color="channel",
                markers=True, 
                title="Monthly Views by Channel",
                line_shape="spline"
            )
            fig.update_layout(
                template="plotly_white",
                hovermode="x unified",
                height=400
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        
        with col2:
            st.subheader("每月Engagement Rate")
            fig2 = px.bar(
                monthly, 
                x="month", 
                y="engagement_rate", 
                color="channel",
                barmode="group", 
                title="Engagement Rate (%) by Month"
            )
            fig2.update_layout(
                template="plotly_white",
                hovermode="x unified",
                height=400
            )
            fig2.update_xaxes(tickangle=45)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    
    # ─────────────────────────────────────────────────────────
    # TAB 3: 年度匯總
    # ─────────────────────────────────────────────────────────
    with tab3:
        st.header("年度統計匯總")
        yearly["year"] = yearly["year"].astype(str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("年度觀看次數")
            fig3 = px.bar(
                yearly, 
                x="year", 
                y="views", 
                color="channel",
                barmode="group", 
                title="Yearly Views"
            )
            fig3.update_layout(
                template="plotly_white",
                hovermode="x unified",
                height=400
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        
        with col2:
            st.subheader("年度Engagement Rate")
            fig4 = px.bar(
                yearly, 
                x="year", 
                y="engagement_rate", 
                color="channel",
                barmode="group", 
                title="Yearly Engagement Rate (%)"
            )
            fig4.update_layout(
                template="plotly_white",
                hovermode="x unified",
                height=400
            )
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    
    # ─────────────────────────────────────────────────────────
    # TAB 4: Top 影片
    # ─────────────────────────────────────────────────────────
    with tab4:
        st.header("本月最受歡迎影片 Top 10")
        
        channels = top["channel"].unique().tolist()
        selected = st.selectbox("選擇頻道", channels, key="channel_select")
        
        df_top = top[top["channel"] == selected].copy().reset_index(drop=True)
        df_top.index += 1
        
        # 創建更好看的表格
        display_df = pd.DataFrame({
            "排名": range(1, len(df_top) + 1),
            "影片ID": df_top["video_id"],
            "觀看次數": df_top["views"].apply(lambda x: f"{int(x):,}"),
            "讚數": df_top["likes"].apply(lambda x: f"{int(x):,}"),
            "評論": df_top["comments"].apply(lambda x: f"{int(x):,}"),
            "Engagement Rate": df_top["engagement_rate"].apply(lambda x: f"{x:.2f}%")
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "排名": st.column_config.NumberColumn(width=50),
            }
        )
        
        # 影片連結
        st.markdown("**觀看影片：**")
        cols = st.columns(5)
        for idx, (i, row) in enumerate(df_top.head(10).iterrows()):
            with cols[idx % 5]:
                st.markdown(
                    f"[影片 {i+1}]({row['video_url']})",
                    unsafe_allow_html=True
                )
