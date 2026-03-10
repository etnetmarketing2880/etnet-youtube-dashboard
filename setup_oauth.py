#!/usr/bin/env python3
"""
YouTube OAuth Setup - 簡化版
只需運行一次，產生 refresh_token 供 GitHub Actions 使用
"""

import os
import pickle
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# YouTube Analytics API 所需的權限
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def setup_channel(channel_name: str, client_secret_file: str):
    """為單一頻道設置 OAuth"""

    print(f"\n{'='*60}")
    print(f"設置頻道: {channel_name}")
    print(f"{'='*60}")

    if not os.path.exists(client_secret_file):
        print(f"❌ 找不到 {client_secret_file}")
        print(f"   請先下載 Google OAuth 憑證檔案")
        return None

    print(f"\n步驟：")
    print(f"1. 瀏覽器會自動開啟")
    print(f"2. 登入擁有「{channel_name}」頻道的 Google 帳號")
    print(f"3. 授權應用程式存取 YouTube Analytics")

    try:
        # 執行 OAuth 流程
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_file, SCOPES
        )
        creds = flow.run_local_server(port=0)

        # 儲存完整 token（本地備份）
        token_file = f"token_{channel_name}.pickle"
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
        print(f"\n✅ Token 已儲存至: {token_file}")

        # 輸出 base64 編碼的完整 token
        with open(token_file, "rb") as f:
            token_base64 = base64.b64encode(f.read()).decode("utf-8")

        return token_base64

    except Exception as e:
        print(f"❌ 認證失敗: {e}")
        return None


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║       YouTube Analytics OAuth Token 產生器                 ║
║                                                            ║
║  這個工具會幫你產生 GitHub Actions 所需的 OAuth tokens     ║
╚════════════════════════════════════════════════════════════╝

📌 前置準備：
   你需要為每個 YouTube 頻道創建 Google OAuth 憑證

   步驟：
   1. 去 Google Cloud Console: https://console.cloud.google.com
   2. 創建新專案或選擇現有專案
   3. 啟用 YouTube Analytics API
   4. 設定 OAuth 同意畫面
   5. 建立 OAuth 2.0 用戶端 ID（類型：網頁應用程式）
   6. 下載 JSON 憑證檔案
""")

    # 定義頻道配置
    channels = []

    print("\n請選擇要設置的頻道（可多選）：")
    print("  1. etnet")
    print("  2. 25度生活")
    print("  3. 健康好人生")
    print("  4. 全部")

    choice = input("\n輸入選項 (1/2/3/4): ").strip()

    if choice == "4":
        channels = [
            ("etnet", "client_secret_etnet.json"),
            ("25度生活", "client_secret_25degrees.json"),
            ("健康好人生", "client_secret_health.json"),
        ]
    elif choice == "1":
        channels = [("etnet", "client_secret_etnet.json")]
    elif choice == "2":
        channels = [("25度生活", "client_secret_25degrees.json")]
    elif choice == "3":
        channels = [("健康好人生", "client_secret_health.json")]
    else:
        print("無效選項")
        return

    results = {}

    for channel_name, secret_file in channels:
        token_base64 = setup_channel(channel_name, secret_file)
        if token_base64:
            results[channel_name] = token_base64

    # 輸出結果
    print("\n" + "=" * 60)
    print("📋 GitHub Secrets 設定指南")
    print("=" * 60)

    secret_mapping = {
        "etnet": "TOKEN_ETNET",
        "25度生活": "TOKEN_25DEG",
        "健康好人生": "TOKEN_HEALTH",
    }

    for channel_name, token_base64 in results.items():
        secret_name = secret_mapping.get(channel_name, channel_name.upper())
        print(f"\n🔐 {channel_name}")
        print(f"   GitHub Secret 名稱: {secret_name}")
        print(f"   內容（複製以下整段文字）：")
        print("-" * 40)
        print(token_base64)
        print("-" * 40)

    print("\n✅ 完成！請將以上內容複製到 GitHub Repository Secrets")
    print("   Settings → Secrets and variables → Actions → New repository secret")


if __name__ == "__main__":
    main()
