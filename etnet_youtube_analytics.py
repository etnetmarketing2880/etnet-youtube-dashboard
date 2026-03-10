#!/usr/bin/env python3
"""
ETNet YouTube Analytics Data Fetcher
從 YouTube Analytics API 獲取頻道數據並生成 CSV 文件
"""

import os
import sys
import pickle
import traceback
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

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtube.readonly"]


def get_credentials(token_file: str) -> Credentials:
    """從 pickle 文件載入 credentials"""
    creds = None

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

    return creds


def main():
    print("=" * 60)
    print("ETNet YouTube Analytics Data Fetcher")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 計算日期範圍
    today = datetime.now()
    start_date_daily = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date_daily = today.strftime("%Y-%m-%d")
    start_date_monthly = (today - relativedelta(months=15)).replace(day=1).strftime("%Y-%m-%d")
    end_date_monthly = today.strftime("%Y-%m-%d")
    start_date_yearly = "2025-01-01"
    end_date_yearly = today.strftime("%Y-%m-%d")
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

        if not os.path.exists(token_file):
            print(f"  ⚠️ Token 文件不存在: {token_file}，跳過此頻道")
            continue

        try:
            # 載入 credentials
            creds = get_credentials(token_file)
            if not creds:
                print(f"  ❌ 無法載入 credentials")
                continue

            # 建立 API 服務
            analytics = build("youtubeAnalytics", "v2", credentials=creds)
            youtube = build("youtube", "v3", credentials=creds)

            # 獲取頻道 ID
            response = youtube.channels().list(part="id,snippet,statistics", mine=True).execute()
            if not response.get("items"):
                print(f"  ❌ 無法獲取頻道信息")
                continue

            channel_id = response["items"][0]["id"]
            channel_name = config["channel_name"]
            stats = response["items"][0].get("statistics", {})
            print(f"  頻道 ID: {channel_id}")

            # 1. 頻道概覽
            all_channel_overview.append({
                "channel_id": channel_id,
                "channel_name": channel_name,
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "channel_label": channel_name,
            })
            print("  ✅ 頻道概覽")

            # 2. 每日數據
            try:
                daily_resp = analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost",
                    dimensions="day",
                    startDate=start_date_daily,
                    endDate=end_date_daily,
                ).execute()
                if daily_resp.get("rows"):
                    for row in daily_resp["rows"]:
                        all_daily_data.append({
                            "date": row[0],
                            "channel": channel_name,
                            "views": int(row[1]),
                            "watch_minutes": int(row[2]),
                            "subscribers_gained": int(row[3]),
                            "subscribers_lost": int(row[4]),
                        })
                    print(f"  ✅ 每日數據 ({len(daily_resp['rows'])} 天)")
            except Exception as e:
                print(f"  ⚠️ 每日數據錯誤: {e}")

            # 3. 每月數據
            try:
                monthly_resp = analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    metrics="views,estimatedMinutesWatched,likes,comments,subscribersGained",
                    dimensions="month",
                    startDate=start_date_monthly,
                    endDate=end_date_monthly,
                ).execute()
                if monthly_resp.get("rows"):
                    for row in monthly_resp["rows"]:
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
                            "subscribers_gained": int(row[5]),
                            "engagement_rate": round(engagement_rate, 4),
                        })
                    print(f"  ✅ 每月數據 ({len(monthly_resp['rows'])} 月)")
            except Exception as e:
                print(f"  ⚠️ 每月數據錯誤: {e}")

            # 4. 年度數據
            try:
                yearly_resp = analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    metrics="views,estimatedMinutesWatched,subscribersGained",
                    dimensions="year",
                    startDate=start_date_yearly,
                    endDate=end_date_yearly,
                ).execute()
                if yearly_resp.get("rows"):
                    for row in yearly_resp["rows"]:
                        all_yearly_data.append({
                            "year": int(row[0]),
                            "channel": channel_name,
                            "views": int(row[1]),
                            "watch_minutes": int(row[2]),
                            "subscribers": int(row[3]),
                        })
                    print(f"  ✅ 年度數據 ({len(yearly_resp['rows'])} 年)")
            except Exception as e:
                print(f"  ⚠️ 年度數據錯誤: {e}")

            # 5. 熱門影片
            try:
                top_resp = analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    metrics="views,estimatedMinutesWatched,likes,comments",
                    dimensions="video",
                    startDate=month_start,
                    endDate=end_date_daily,
                    maxResults=10,
                    sort="-views",
                ).execute()
                if top_resp.get("rows"):
                    for row in top_resp["rows"]:
                        video_id = row[0]
                        views = int(row[1])
                        likes = int(row[3])
                        comments = int(row[4])
                        engagement_rate = (likes + comments) / views if views > 0 else 0
                        all_top_videos.append({
                            "video_id": video_id,
                            "views": views,
                            "watch_minutes": int(row[2]),
                            "likes": likes,
                            "comments": comments,
                            "engagement_rate": round(engagement_rate, 4),
                            "video_url": f"https://youtube.com/watch?v={video_id}",
                            "channel": channel_name,
                        })
                    print(f"  ✅ 熱門影片 ({len(top_resp['rows'])} 部)")
            except Exception as e:
                print(f"  ⚠️ 熱門影片錯誤: {e}")

        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            traceback.print_exc()
            continue

    # ── 生成 CSV 文件 ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("生成 CSV 文件...")
    print("=" * 60)

    # 確保至少有基本 CSV 檔案
    if all_channel_overview:
        pd.DataFrame(all_channel_overview).to_csv("channel_overview.csv", index=False)
        print(f"  ✅ channel_overview.csv")
    else:
        # 保留舊檔案或創建空的
        print("  ⚠️ 沒有頻道概覽數據，保留現有檔案")

    if all_daily_data:
        pd.DataFrame(all_daily_data).to_csv("daily_analytics.csv", index=False)
        print(f"  ✅ daily_analytics.csv")
    else:
        print("  ⚠️ 沒有每日數據，保留現有檔案")

    if all_monthly_data:
        pd.DataFrame(all_monthly_data).to_csv("monthly_analytics.csv", index=False)
        print(f"  ✅ monthly_analytics.csv")
    else:
        print("  ⚠️ 沒有每月數據，保留現有檔案")

    if all_yearly_data:
        pd.DataFrame(all_yearly_data).to_csv("yearly_analytics.csv", index=False)
        print(f"  ✅ yearly_analytics.csv")
    else:
        print("  ⚠️ 沒有年度數據，保留現有檔案")

    if all_top_videos:
        pd.DataFrame(all_top_videos).sort_values(["channel", "views"], ascending=[True, False]).to_csv("top_videos_this_month.csv", index=False)
        print(f"  ✅ top_videos_this_month.csv")
    else:
        print("  ⚠️ 沒有熱門影片數據，保留現有檔案")

    print("\n" + "=" * 60)
    print("✅ 數據更新完成！")
    print("=" * 60)

    # 返回成功與否
    return len(all_channel_overview) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
