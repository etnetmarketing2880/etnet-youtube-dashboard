# ETNet YouTube Dashboard

此專案用於自動更新 YouTube 頻道數據。

## 數據來源

數據由 GitHub Actions 每日自動從 YouTube Analytics API 獲取。

## 查看數據

數據存放在 `data/` 資料夾內：
- `channel_overview.csv` - 頻道概覽
- `daily_analytics.csv` - 每日數據
- `monthly_analytics.csv` - 每月數據
- `yearly_analytics.csv` - 年度數據
- `top_videos_this_month.csv` - 本月熱門影片
