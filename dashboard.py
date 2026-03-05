import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="etnet YouTube Dashboard", layout="wide")
st.title("📺 etnet YouTube Analytics Dashboard")
st.caption("數據來源：YouTube Analytics API｜每日自動更新")

# Load data
overview = pd.read_csv("data/channel_overview.csv")
monthly  = pd.read_csv("data/monthly_analytics.csv")
yearly   = pd.read_csv("data/yearly_analytics.csv")
top      = pd.read_csv("data/top_videos_this_month.csv")

# ── Channel Overview ──────────────────────────────────────
st.header("📊 頻道概覽")
cols = st.columns(3)
for i, row in overview.iterrows():
    with cols[i]:
        st.metric(row["channel_name"], f"{int(row['subscribers']):,}", "訂閱數")
        st.metric("總觀看次數", f"{int(row['total_views']):,}")
        st.metric("影片數量",   f"{int(row['video_count']):,}")

# ── Monthly Views ─────────────────────────────────────────
st.header("📈 每月觀看趨勢")
fig = px.line(monthly, x="month", y="views", color="channel",
              markers=True, title="Monthly Views by Channel")
st.plotly_chart(fig, use_container_width=True)

# ── Monthly Engagement Rate ───────────────────────────────
st.header("💡 每月 Engagement Rate")
fig2 = px.bar(monthly, x="month", y="engagement_rate", color="channel",
              barmode="group", title="Engagement Rate (%) by Month")
st.plotly_chart(fig2, use_container_width=True)

# ── Yearly Summary ────────────────────────────────────────
st.header("📅 年度匯總")
fig3 = px.bar(yearly, x="year", y="views", color="channel",
              barmode="group", title="Yearly Views")
st.plotly_chart(fig3, use_container_width=True)

# ── Top Videos This Month ─────────────────────────────────
st.header("🏆 本月最受歡迎影片 Top 10")
channel_filter = st.selectbox("選擇頻道", top["channel"].unique())
top_filtered = top[top["channel"] == channel_filter].reset_index(drop=True)
top_filtered.index += 1
top_filtered["video_url"] = top_filtered["video_url"].apply(
    lambda x: f'<a href="{x}" target="_blank">🔗 連結</a>')
st.write(top_filtered[["video_id","views","likes","comments","engagement_rate","video_url"]].to_html(escape=False), unsafe_allow_html=True)
