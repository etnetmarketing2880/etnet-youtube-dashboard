#!/usr/bin/env python3
"""
YouTube OAuth Token Generator
用於產生 YouTube Analytics API 所需的 OAuth token
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


def generate_token(client_secret_file: str, token_output_file: str, channel_name: str):
    """
    產生 OAuth token

    Args:
        client_secret_file: Google Cloud OAuth 憑證 JSON 檔案路徑
        token_output_file: 輸出的 token 檔案路徑
        channel_name: 頻道名稱（用於顯示）
    """
    print(f"\n{'='*60}")
    print(f"認證頻道: {channel_name}")
    print(f"{'='*60}")

    creds = None

    # 檢查是否已有舊 token
    if os.path.exists(token_output_file):
        with open(token_output_file, "rb") as token:
            creds = pickle.load(token)
        print("發現現有 token，檢查是否有效...")

    # 如果冇有效憑證，進行認證
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token 已過期，正在刷新...")
            creds.refresh(Request())
        else:
            print(f"請在瀏覽器中登入並授權 {channel_name} 頻道...")
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 儲存 token
        with open(token_output_file, "wb") as token:
            pickle.dump(creds, token)
        print(f"✅ Token 已儲存至: {token_output_file}")

    else:
        print("✅ Token 仍然有效")

    # 輸出 base64 編碼（用於 GitHub Secrets）
    with open(token_output_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print(f"\n📋 Base64 編碼（複製以下內容到 GitHub Secret）:")
    print("-" * 60)
    print(encoded)
    print("-" * 60)

    return encoded


def main():
    print("=" * 60)
    print("YouTube OAuth Token Generator")
    print("=" * 60)
    print("""
這個工具會幫你產生 YouTube Analytics API 所需的 OAuth token。

前置準備：
1. 在 Google Cloud Console 創建 OAuth 2.0 憑證
2. 下載 client_secret.json 檔案
3. 確保 YouTube Analytics API 已啟用

詳細步驟請參考：https://github.com/etnetmarketing2880/etnet-youtube-dashboard#setup
""")

    channels = [
        {
            "name": "etnet",
            "secret_file": "client_secret_etnet.json",
            "token_file": "token_etnet.pickle",
        },
        {
            "name": "25度生活",
            "secret_file": "client_secret_25degrees.json",
            "token_file": "token_25度生活.pickle",
        },
        {
            "name": "健康好人生",
            "secret_file": "client_secret_health.json",
            "token_file": "token_健康好人生.pickle",
        },
    ]

    results = {}

    for channel in channels:
        secret_file = channel["secret_file"]

        if not os.path.exists(secret_file):
            print(f"\n⚠️ 未找到 {secret_file}")
            print(f"   請將 {channel['name']} 的 OAuth 憑證檔案放在當前目錄")
            continue

        try:
            encoded = generate_token(
                secret_file,
                channel["token_file"],
                channel["name"]
            )
            results[channel["name"]] = encoded
        except Exception as e:
            print(f"❌ 認證 {channel['name']} 時出錯: {e}")

    # 總結
    print("\n" + "=" * 60)
    print("📊 認證結果總結")
    print("=" * 60)

    for name, encoded in results.items():
        print(f"\n✅ {name}")
        print(f"   Token 檔案已儲存")
        print(f"   GitHub Secret: TOKEN_{name.upper().replace('度', 'DEG').replace('好人生', 'HEALTH')}")

    if not results:
        print("\n❌ 沒有成功認證任何頻道")
        print("\n請確保：")
        print("1. 已下載 client_secret_*.json 檔案")
        print("2. YouTube Analytics API 已啟用")
        print("3. OAuth 同意畫面已設定")


if __name__ == "__main__":
    main()
