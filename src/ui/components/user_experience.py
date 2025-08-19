import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import json
import os

class UserExperience:
    """用戶體驗管理器 - 處理個人化設定和使用狀態"""
    
    def __init__(self):
        self.user_data_file = "data/user_preferences.json"
        self.ensure_user_data()
    
    def ensure_user_data(self):
        """確保用戶數據目錄存在"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.user_data_file):
            self.save_user_data({
                "is_first_visit": True,
                "preferred_mode": "personal",  # personal or demo
                "completed_onboarding": False,
                "upload_history": [],
                "chat_preferences": {
                    "theme": "light",
                    "language": "zh-TW",
                    "show_sources": True,
                    "enable_memory": True
                },
                "last_visit": None,
                "feature_discovery": {
                    "drag_drop": False,
                    "batch_upload": False,
                    "chat_memory": False,
                    "file_management": False
                }
            })
    
    def load_user_data(self) -> Dict:
        """載入用戶數據"""
        try:
            with open(self.user_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_user_data(self, data: Dict):
        """保存用戶數據"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"保存用戶數據失敗: {str(e)}")
    
    def is_first_visit(self) -> bool:
        """檢查是否為首次訪問"""
        data = self.load_user_data()
        return data.get("is_first_visit", True)
    
    def mark_visited(self):
        """標記已訪問"""
        data = self.load_user_data()
        data["is_first_visit"] = False
        data["last_visit"] = datetime.now().isoformat()
        self.save_user_data(data)
    
    def is_onboarding_completed(self) -> bool:
        """檢查是否完成引導"""
        data = self.load_user_data()
        return data.get("completed_onboarding", False)
    
    def complete_onboarding(self):
        """完成引導流程"""
        data = self.load_user_data()
        data["completed_onboarding"] = True
        self.save_user_data(data)
    
    def get_preferred_mode(self) -> str:
        """獲取偏好模式"""
        data = self.load_user_data()
        return data.get("preferred_mode", "personal")
    
    def set_preferred_mode(self, mode: str):
        """設定偏好模式"""
        data = self.load_user_data()
        data["preferred_mode"] = mode
        self.save_user_data(data)
    
    def get_chat_preferences(self) -> Dict:
        """獲取聊天偏好"""
        data = self.load_user_data()
        return data.get("chat_preferences", {
            "theme": "light",
            "language": "zh-TW",
            "show_sources": True,
            "enable_memory": True
        })
    
    def update_chat_preferences(self, preferences: Dict):
        """更新聊天偏好"""
        data = self.load_user_data()
        data["chat_preferences"].update(preferences)
        self.save_user_data(data)
    
    def add_upload_record(self, filename: str, file_type: str, size: int):
        """添加上傳記錄"""
        data = self.load_user_data()
        upload_record = {
            "filename": filename,
            "type": file_type,
            "size": size,
            "timestamp": datetime.now().isoformat()
        }
        data["upload_history"].append(upload_record)
        
        # 只保留最近 50 條記錄
        if len(data["upload_history"]) > 50:
            data["upload_history"] = data["upload_history"][-50:]
        
        self.save_user_data(data)
    
    def get_upload_history(self) -> List[Dict]:
        """獲取上傳歷史"""
        data = self.load_user_data()
        return data.get("upload_history", [])
    
    def mark_feature_discovered(self, feature: str):
        """標記功能已發現"""
        data = self.load_user_data()
        if "feature_discovery" not in data:
            data["feature_discovery"] = {}
        data["feature_discovery"][feature] = True
        self.save_user_data(data)
    
    def is_feature_discovered(self, feature: str) -> bool:
        """檢查功能是否已發現"""
        data = self.load_user_data()
        return data.get("feature_discovery", {}).get(feature, False)
    
    def get_usage_stats(self) -> Dict:
        """獲取使用統計"""
        data = self.load_user_data()
        upload_history = data.get("upload_history", [])
        
        total_uploads = len(upload_history)
        total_size = sum(record.get("size", 0) for record in upload_history)
        
        # 按類型統計
        type_stats = {}
        for record in upload_history:
            file_type = record.get("type", "unknown")
            type_stats[file_type] = type_stats.get(file_type, 0) + 1
        
        return {
            "total_uploads": total_uploads,
            "total_size": total_size,
            "type_stats": type_stats,
            "last_visit": data.get("last_visit"),
            "days_since_first_visit": self._days_since_first_visit(data)
        }
    
    def _days_since_first_visit(self, data: Dict) -> int:
        """計算首次訪問至今的天數"""
        last_visit = data.get("last_visit")
        if not last_visit:
            return 0
        
        try:
            last_date = datetime.fromisoformat(last_visit)
            return (datetime.now() - last_date).days
        except:
            return 0
    
    def reset_user_data(self):
        """重置用戶數據（用於測試）"""
        if os.path.exists(self.user_data_file):
            os.remove(self.user_data_file)
        self.ensure_user_data()
