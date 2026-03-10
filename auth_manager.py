import streamlit as st
import json
import os
from datetime import datetime
import hashlib

class AuthManager:
    def __init__(self, users_file="data/users.json"):
        self.users_file = users_file
        self.load_users()
    
    def load_users(self):
        """從文件加載用戶數據"""
        if os.path.exists(self.users_file):
            with open(self.users_file, "r", encoding="utf-8") as f:
                self.users = json.load(f)
        else:
            # 預設管理員帳戶
            self.users = {
                "admin": {
                    "password": self._hash_password("admin123"),
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            }
            self.save_users()
    
    def save_users(self):
        """保存用戶數據到文件"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password):
        """Hash密碼"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """驗證用戶"""
        if username in self.users:
            if self.users[username]["password"] == self._hash_password(password):
                return True
        return False
    
    def register(self, username, password, role="viewer"):
        """註冊新用戶"""
        if username in self.users:
            return False, "用戶已存在"
        
        if len(password) < 6:
            return False, "密碼長度至少需要6個字符"
        
        self.users[username] = {
            "password": self._hash_password(password),
            "role": role,
            "created_at": datetime.now().isoformat()
        }
        self.save_users()
        return True, "註冊成功"
    
    def get_user_role(self, username):
        """獲取用戶角色"""
        if username in self.users:
            return self.users[username]["role"]
        return None
