#!/usr/bin/env python3
"""
ETNet YouTube Analytics Data Fetcher
從 YouTube Analytics API 獲取頻道數據並生成 CSV 文件
"""

import os
import pickle
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# ── 配置 ─────────────────────────────────────────────────────
CHANNELS = {
    "etnet": {
        "token_file": "token_etnet.pickle",
        "secret_file": "client_secret_etnet.json",
        "channel_name": "etnet",
    },
    "25度生活": {
        "token_file": "token_25度生活.pickle",
        "secret_file": "client_secret_25degrees.json",
        "channel_name": "25度生活",
    },
    "健康好人生": {
        "token_file": "token_健康好人生.pickle",
        "secret_file": "client_secret_health.json",
        "channel_name": "健康好人生",
    },
}

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]
API_SERVICE_NAME = "youtubeAnalytics"
API_VERSION = "v2"


def get_credentials(token_file: str) -> Credentials:
    """從 pickle 文件載入 credentials"""
    creds = None

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # 保存更新後的 credentials
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

    return creds


def get_youtube_analytics_service(credentials: Credentials):
    """建立 YouTube Analytics API 服務"""
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def get_channel_id(service, credentials: Credentials) -> str:
    """獲取頻道 ID"""
    # 使用 YouTube Data API 獲取 channel ID
    youtube = build("youtube", "v3", credentials=credentials)
    response = youtube.channels().list(part="id,snippet", mine=True).execute()

    if response.get("items"):
        item = response["items"][0]
        return item["id"], item["snippet"]["title"]
    return None, None


def fetch_basic_metrics(service, channel_id: str, start_date: str, end_date: str) -> dict:
    """獲取基本指標（觀看次數、訂閱者等）"""
    response = service.reports().query(
        ids=f"channel=={channel_id}",
        metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost",
        dimensions="day",
        startDate=start_date,
        endDate=end_date,
    ).execute()

    return response


def fetch_monthly_metrics(service, channel_id: str, start_date: str, end_date: str) -> dict:
    """獲取每月指標"""
    response = service.reports().query(
        ids=f"channel=={channel_id}",
        metrics="views,estimatedMinutesWatched,likes,comments,shares,subscribersGained,subscribersLost",
        dimensions="month",
        startDate=start_date,
        endDate=end_date,
    ).execute()

    return response


def fetch_top_videos(service, channel_id: str, start_date: str, end_date: str, max_results: int = 10) -> dict:
    """獲取熱門影片"""
    response = service.reports().query(
        ids=f"channel=={channel_id}",
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
        dimensions="video",
        startDate=start_date,
        endDate=end_date,
        maxResults=max_results,
        sort="-views",
    ).execute()

    return response


def get_video_url(youtube, video_id: str) -> str:
    """獲取影片 URL 和標題"""
    try:
        response = youtube.videos().list(part="snippet", id=video_id).execute()
        if response.get("items"):
            title = response["items"][0]["snippet"]["title"]
            return f"https://youtube.com/watch?v={video_id}", title
    except:
        pass
    return f"https://youtube.com/watch?v={video_id}", video_id


def main():
    print("=" * 60)
    print("ETNet YouTube Analytics Data Fetcher")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 計算日期範圍
    today = datetime.now()
    start_date_daily = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date_daily = today.strftime("%Y-%m-%d")

    # 月度數據：過去 15 個月
    start_date_monthly = (today - relativedelta(months=15)).replace(day=1).strftime("%Y-%m-%d")
    end_date_monthly = today.strftime("%Y-%m-%d")

    # 年度數據
    start_date_yearly = "2025-01-01"
    end_date_yearly = today.strftime("%Y-%m-%d")

    # 本月開始日期
    month_start = today.replace(day=1).strftime("%Y-%m-%d")

    # 收集所有頻道數據
    all_channel_overview = []
    all_daily_data = []
    all_monthly_data = []
    all_yearly_data = []
    all_top_videos = []

    for key, config in CHANNELS.items():
        print(f"\n處理頻道: {config['channel_name']}")

        token_file = config["token_file"]
        secret_file = config["secret_file"]

        # 檢查文件是否存在
        if not os.path.exists(token_file):
            print(f"  ⚠️ Token 文件不存在: {token_file}，跳過此頻道")
            continue

        try:
            # 載入 credentials
            creds = get_credentials(token_file)

            # 建立 API 服務
            analytics_service = get_youtube_analytics_service(creds)
            youtube_service = build("youtube", "v3", credentials=creds)

            # 獲取頻道 ID
            channel_id, channel_name = get_channel_id(analytics_service, creds)
            if not channel_id:
                print(f"  ❌ 無法獲取頻道 ID")
                continue

            channel_name = config["channel_name"]
            print(f"  頻道 ID: {channel_id}")

            # 1. 獲取頻道概覽
            print("  獲取頻道概覽...")
            channel_info = youtube_service.channels().list(
                part="statistics,snippet",
                id=channel_id
            ).execute()

            if channel_info.get("items"):
                stats = channel_info["items"][0]["statistics"]
                all_channel_overview.append({
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "subscribers": int(stats.get("subscriberCount", 0)),
                    "total_views": int(stats.get("viewCount", 0)),
                    "video_count": int(stats.get("videoCount", 0)),
                    "channel_label": channel_name,
                })

            # 2. 獲取每日數據
            print("  獲取每日數據...")
            daily_response = fetch_basic_metrics(analytics_service, channel_id, start_date_daily, end_date_daily)

            if daily_response.get("rows"):
                for row in daily_response["rows"]:
                    all_daily_data.append({
                        "date": row[0],
                        "channel": channel_name,
                        "views": int(row[1]),
                        "watch_minutes": int(row[2]),
                        "avg_view_duration": int(row[3]),
                        "subscribers_gained": int(row[4]),
                        "subscribers_lost": int(row[5]),
                    })

            # 3. 獲取每月數據
            print("  獲取每月數據...")
            monthly_response = fetch_monthly_metrics(analytics_service, channel_id, start_date_monthly, end_date_monthly)

            if monthly_response.get("rows"):
                for row in monthly_response["rows"]:
                    views = int(row[1])
                    likes = int(row[3])
                    comments = int(row[4])
                    engagement_rate = (likes + comments) / views if views > 0 else 0

                    all_monthly_data.append({
                        "month": row[0],
                        "channel": channel_name,
                        "views": views,
                        "watch_minutes": int(row[2]),
                        "likes": likes,
                        "comments": comments,
                        "shares": int(row[5]),
                        "subscribers_gained": int(row[6]),
                        "subscribers_lost": int(row[7]),
                        "engagement_rate": round(engagement_rate, 4),
                    })

            # 4. 獲取年度數據（通過匯總月度數據）
            print("  獲取年度數據...")
            yearly_response = analytics_service.reports().query(
                ids=f"channel=={channel_id}",
                metrics="views,estimatedMinutesWatched,subscribersGained",
                dimensions="year",
                startDate=start_date_yearly,
                endDate=end_date_yearly,
            ).execute()

            if yearly_response.get("rows"):
                for row in yearly_response["rows"]:
                    all_yearly_data.append({
                        "year": int(row[0]),
                        "channel": channel_name,
                        "views": int(row[1]),
                        "watch_minutes": int(row[2]),
                        "subscribers": int(row[3]),
                    })

            # 5. 獲取本月熱門影片
            print("  獲取本月熱門影片...")
            top_videos_response = fetch_top_videos(analytics_service, channel_id, month_start, end_date_daily, max_results=10)

            if top_videos_response.get("rows"):
                for row in top_videos_response["rows"]:
                    video_id = row[0]
                    views = int(row[1])
                    likes = int(row[3])
                    comments = int(row[4])

                    engagement_rate = (likes + comments) / views if views > 0 else 0

                    video_url, video_title = get_video_url(youtube_service, video_id)

                    all_top_videos.append({
                        "video_id": video_id,
                        "video_title": video_title,
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "watch_minutes": int(row[2]),
                        "engagement_rate": round(engagement_rate, 4),
                        "video_url": video_url,
                        "channel": channel_name,
                    })

            print(f"  ✅ {channel_name} 數據獲取完成")

        except Exception as e:
            print(f"  ❌ 錯誤: {str(e)}")
            continue

    # ── 生成 CSV 文件 ────────────────────────────────────────
    print("\n生成 CSV 文件...")

    # 1. channel_overview.csv
    if all_channel_overview:
        df_overview = pd.DataFrame(all_channel_overview)
        df_overview.to_csv("channel_overview.csv", index=False)
        print(f"  ✅ channel_overview.csv ({len(df_overview)} 頻道)")
    else:
        print("  ⚠️ 沒有頻道概覽數據")

    # 2. daily_analytics.csv
    if all_daily_data:
        df_daily = pd.DataFrame(all_daily_data)
        df_daily.to_csv("daily_analytics.csv", index=False)
        print(f"  ✅ daily_analytics.csv ({len(df_daily)} 行)")
    else:
        print("  ⚠️ 沒有每日數據")

    # 3. monthly_analytics.csv
    if all_monthly_data:
        df_monthly = pd.DataFrame(all_monthly_data)
        df_monthly.to_csv("monthly_analytics.csv", index=False)
        print(f"  ✅ monthly_analytics.csv ({len(df_monthly)} 行)")
    else:
        print("  ⚠️ 沒有每月數據")

    # 4. yearly_analytics.csv
    if all_yearly_data:
        df_yearly = pd.DataFrame(all_yearly_data)
        df_yearly.to_csv("yearly_analytics.csv", index=False)
        print(f"  ✅ yearly_analytics.csv ({len(df_yearly)} 行)")
    else:
        print("  ⚠️ 沒有年度數據")

    # 5. top_videos_this_month.csv
    if all_top_videos:
        df_top = pd.DataFrame(all_top_videos)
        df_top = df_top.sort_values(["channel", "views"], ascending=[True, False])
        df_top.to_csv("top_videos_this_month.csv", index=False)
        print(f"  ✅ top_videos_this_month.csv ({len(df_top)} 行)")
    else:
        print("  ⚠️ 沒有熱門影片數據")

    print("\n" + "=" * 60)
    print("✅ 數據更新完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
