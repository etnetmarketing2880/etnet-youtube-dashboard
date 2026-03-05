# ============================================================
# etnet YouTube Analytics Dashboard v3
# 改用 day dimension，自己 group by month/year（最穩陣）
# pip install google-auth google-auth-oauthlib google-api-python-client pandas python-dateutil
# ============================================================

import os
import pickle
import pandas as pd
from datetime import date, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ============================================================
# 設定
# ============================================================

CHANNELS = {
    "etnet":      {"secret": "client_secret_etnet.json",     "handle": "@etnethk"},
    "25度生活":   {"secret": "client_secret_25degrees.json", "handle": "@25degreeslifestyle"},
    "健康好人生": {"secret": "client_secret_health.json",    "handle": "@goodhealthylife-yeah"},
}

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

START_DATE  = "2025-01-01"
TODAY       = date.today()
YESTERDAY   = (TODAY - timedelta(days=1)).strftime("%Y-%m-%d")  # Analytics 用昨日
TODAY_STR   = TODAY.strftime("%Y-%m-%d")
MONTH_START = TODAY.replace(day=1).strftime("%Y-%m-%d")


# ============================================================
# OAuth
# ============================================================

def get_credentials(channel_name, secret_file):
    token_file = f"token_{channel_name}.pickle"
    creds = None
    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
    return creds


# ============================================================
# Channel 基本數據
# ============================================================

def get_channel_info(youtube, handle):
    resp = youtube.channels().list(
        part="id,snippet,statistics",
        forHandle=handle.lstrip("@")
    ).execute()
    item = resp["items"][0]
    return {
        "channel_id":   item["id"],
        "channel_name": item["snippet"]["title"],
        "subscribers":  int(item["statistics"].get("subscriberCount", 0)),
        "total_views":  int(item["statistics"].get("viewCount", 0)),
        "video_count":  int(item["statistics"].get("videoCount", 0)),
    }


# ============================================================
# 用 day dimension 抓數據，再自己 group
# ============================================================

def get_daily_analytics(yt_analytics, channel_id, start, end):
    all_rows = []
    # API 每次最多返回 1000 rows，用 startIndex 翻頁
    start_index = 1
    while True:
        resp = yt_analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start,
            endDate=end,
            metrics="views,likes,comments,estimatedMinutesWatched",
            dimensions="day",
            sort="day",
            maxResults=1000,
            startIndex=start_index
        ).execute()
        rows = resp.get("rows", [])
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < 1000:
            break
        start_index += 1000

    df = pd.DataFrame(all_rows, columns=["date","views","likes","comments","watch_minutes"])
    return df


def group_by_month(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["month"] = df["date"].str[:7]
    monthly = df.groupby("month").agg(
        views=("views","sum"),
        likes=("likes","sum"),
        comments=("comments","sum"),
        watch_minutes=("watch_minutes","sum"),
    ).reset_index()
    monthly["engagement_rate"] = ((monthly["likes"] + monthly["comments"]) / monthly["views"] * 100).round(2)
    return monthly


def group_by_year(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["year"] = df["date"].str[:4]
    yearly = df.groupby("year").agg(
        views=("views","sum"),
        likes=("likes","sum"),
        comments=("comments","sum"),
        watch_minutes=("watch_minutes","sum"),
    ).reset_index()
    yearly["engagement_rate"] = ((yearly["likes"] + yearly["comments"]) / yearly["views"] * 100).round(2)
    return yearly


# ============================================================
# 本月 Top 10 影片
# ============================================================

def get_top_videos_this_month(yt_analytics, channel_id):
    resp = yt_analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=MONTH_START,
        endDate=YESTERDAY,
        metrics="views,likes,comments,estimatedMinutesWatched",
        dimensions="video",
        sort="-views",
        maxResults=10
    ).execute()
    rows = resp.get("rows", [])
    df = pd.DataFrame(rows, columns=["video_id","views","likes","comments","watch_minutes"])
    if not df.empty:
        df["engagement_rate"] = ((df["likes"] + df["comments"]) / df["views"] * 100).round(2)
        df["video_url"] = "https://youtu.be/" + df["video_id"]
    return df


# ============================================================
# 主程式
# ============================================================

all_daily   = []
all_monthly = []
all_yearly  = []
all_top     = []
channel_info = []

print(f"數據範圍：{START_DATE} 至 {YESTERDAY}")
print(f"本月數據：{MONTH_START} 至 {YESTERDAY}\n")

for name, cfg in CHANNELS.items():
    print(f">>> 處理中：{name}")
    creds        = get_credentials(name, cfg["secret"])
    youtube      = build("youtube",          "v3", credentials=creds)
    yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)

    info = get_channel_info(youtube, cfg["handle"])
    info["channel_label"] = name
    channel_info.append(info)
    print(f"    {info['channel_name']} | 訂閱: {info['subscribers']:,}")

    daily = get_daily_analytics(yt_analytics, info["channel_id"], START_DATE, YESTERDAY)
    daily["channel"] = name
    all_daily.append(daily)

    monthly = group_by_month(daily)
    monthly["channel"] = name
    all_monthly.append(monthly)

    yearly = group_by_year(daily)
    yearly["channel"] = name
    all_yearly.append(yearly)

    top = get_top_videos_this_month(yt_analytics, info["channel_id"])
    top["channel"] = name
    all_top.append(top)
    print(f"    ✅ 完成")

pd.DataFrame(channel_info).to_csv("channel_overview.csv",     index=False, encoding="utf-8-sig")
pd.concat(all_daily).to_csv(      "daily_analytics.csv",       index=False, encoding="utf-8-sig")
pd.concat(all_monthly).to_csv(    "monthly_analytics.csv",     index=False, encoding="utf-8-sig")
pd.concat(all_yearly).to_csv(     "yearly_analytics.csv",      index=False, encoding="utf-8-sig")
pd.concat(all_top).to_csv(        "top_videos_this_month.csv", index=False, encoding="utf-8-sig")

print("\n✅ 全部完成！輸出檔案：")
print("  - channel_overview.csv")
print("  - daily_analytics.csv")
print("  - monthly_analytics.csv")
print("  - yearly_analytics.csv")
print("  - top_videos_this_month.csv")
