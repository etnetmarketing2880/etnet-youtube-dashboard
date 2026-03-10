# Streamlit Cloud 入口文件
# 此文件會導入並運行 dashboard.py

import sys
import os

# 確保 data 目錄存在
os.makedirs("data", exist_ok=True)

# 導入並運行主 dashboard
from dashboard import *
