import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="etnet YouTube Dashboard", layout="wide")
st.title("📺 etnet YouTube Analytics Dashboard")
st.caption("數據來源：YouTube Analytics API｜每日自動更新")

# ── Load data ─────────────────────────────────────────────
@st.cache_data
def load_data():
    overview = pd.read_csv("data/channel_overview.csv")
    monthly  = pd.read_csv("data/monthly_analytics.csv")
    yearly   = pd.read_csv("data/yearly_analytics.csv")
    top      = pd.read_csv("data/top_videos_this_month.csv")
    daily    = pd.read_csv("data/daily_analytics.csv")
    return overview, monthly, yearly, top, daily

try:
    overview, monthly, yearly, top, daily = load_data()
except Exception as e:
    st.error(f"讀取數據失敗：{e}")
    st.stop()

# Debug：顯示欄位名（確認CSV正確）
with st.expander("🔍 Debug：欄位確認"):
    st.write("monthly 欄位：", monthly.columns.tolist())
    st.write("monthly 前5行：", monthly.head())
    st.write("yearly 欄位：", yearly.columns.tolist())
    st.write("yearly 前5行：", yearly.head())

# ── Channel Overview ──────────────────────────────────────
st.header("📊 頻道概覽")
cols = st.columns(len(overview))
for i, row in overview.iterrows():
    with cols[i]:
        channel_label = str(row.get("channel_name", row.get("channel_label", f"Channel {i+1}")))
        st.metric(channel_label, f"{int(row['subscribers']):,}", "訂閱數")
        st.metric("總觀看次數", f"{int(row['total_views']):,}")
        st.metric("影片數量", f"{int(row['video_count']):,}")

# ── Daily Views Trend ─────────────────────────────────────
st.header("📈 每日觀看趨勢")
if not daily.empty and "date" in daily.columns and "views" in daily.columns:
    daily["date"] = pd.to_datetime(daily["date"])
    fig_daily = px.line(daily, x="date", y="views", color="channel",
                        markers=True, title="Daily Views by Channel")
    st.plotly_chart(fig_daily, use_container_width=True)
else:
    st.warning("每日數據暫時未有")

# ── Monthly Views ─────────────────────────────────────────
st.header("📈 每月觀看趨勢")
if not monthly.empty and "month" in monthly.columns and "views" in monthly.columns:
    fig = px.line(monthly, x="month", y="views", color="channel",
                  markers=True, title="Monthly Views by Channel")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("月份數據暫時未有")

# ── Monthly Engagement Rate ───────────────────────────────
st.header("💡 每月 Engagement Rate")
if not monthly.empty and "engagement_rate" in monthly.columns:
    # 轉換為百分比顯示
    monthly_display = monthly.copy()
    monthly_display["engagement_rate_pct"] = monthly_display["engagement_rate"] * 100
    fig2 = px.bar(monthly_display, x="month", y="engagement_rate_pct", color="channel",
                  barmode="group", title="Engagement Rate (%) by Month",
                  labels={"engagement_rate_pct": "Engagement Rate (%)"})
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Engagement Rate 數據暫時未有")

# ── Yearly Summary ────────────────────────────────────────
st.header("📅 年度匯總")
if not yearly.empty and "year" in yearly.columns:
    yearly["year"] = yearly["year"].astype(str)
    fig3 = px.bar(yearly, x="year", y="views", color="channel",
                  barmode="group", title="Yearly Views by Channel")
    st.plotly_chart(fig3, use_container_width=True)

    # 年度訂閱者增長
    if "subscribers" in yearly.columns:
        fig4 = px.bar(yearly, x="year", y="subscribers", color="channel",
                      barmode="group", title="Yearly Subscribers by Channel")
        st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("年度數據暫時未有")

# ── Top Videos This Month ─────────────────────────────────
st.header("🏆 本月最受歡迎影片 Top 10")
if not top.empty:
    channel_filter = st.selectbox("選擇頻道", top["channel"].unique())
    top_filtered = top[top["channel"] == channel_filter].reset_index(drop=True)
    top_filtered.index += 1

    # 顯示影片標題（如果有）
    display_cols = [c for c in ["video_id","views","likes","comments","engagement_rate","video_url"] if c in top_filtered.columns]
    st.dataframe(top_filtered[display_cols])

    # 如果有 video_url，顯示為可點擊連結
    if "video_url" in top_filtered.columns:
        st.markdown("### 🔗 影片連結")
        for idx, row in top_filtered.iterrows():
            st.markdown(f"**{idx}.** [{row.get('video_id', 'Video')}]({row['video_url']})")
else:
    st.warning("本月影片數據暫時未有")

# ── Footer ────────────────────────────────────────────────
st.markdown("---")
st.caption("最後更新時間：2026-03 | 數據由 YouTube Analytics API 提供")
