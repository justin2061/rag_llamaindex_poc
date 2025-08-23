#!/usr/bin/env python3
"""
Enhanced RAG API 測試腳本
"""

import requests
import json
import time
import os
from typing import Dict, Any

# API 配置
API_BASE_URL = "http://localhost:8000"
API_KEYS = {
    "demo": "demo-api-key-123",
    "admin": "admin-api-key-456", 
    "user": "user-api-key-789"
}

class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def test_health_check(self):
        """測試健康檢查端點"""
        print("🔍 測試健康檢查...")
        
        response = self.session.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康檢查通過")
            print(f"   狀態: {data['status']}")
            print(f"   Elasticsearch: {'✅' if data['elasticsearch_connected'] else '❌'}")
            print(f"   文檔數: {data['total_documents']}")
            return True
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            return False
    
    def test_authentication(self, api_key: str):
        """測試認證功能"""
        print(f"🔐 測試認證...")
        
        # 測試生成 Token
        auth_data = {"api_key": api_key}
        response = self.session.post(f"{self.base_url}/auth/token", json=auth_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            print(f"✅ Token 生成成功")
            print(f"   用戶: {data['user_id']}")
            print(f"   權限: {data['permissions']}")
            
            # 設置認證頭
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
            return True
        else:
            print(f"❌ 認證失敗: {response.status_code}")
            return False
    
    def test_simple_chat(self):
        """測試簡單對話"""
        print("💬 測試簡單對話...")
        
        chat_data = {
            "question": "你好，請問你能做什麼？",
            "user_id": "test_user",
            "include_sources": True
        }
        
        response = self.session.post(f"{self.base_url}/chat", json=chat_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 對話成功")
            print(f"   回答: {data['answer'][:100]}...")
            print(f"   來源數: {len(data['sources'])}")
            print(f"   對話ID: {data['conversation_id']}")
            print(f"   響應時間: {data['response_time_ms']}ms")
            return data
        else:
            print(f"❌ 對話失敗: {response.status_code}")
            if response.text:
                print(f"   錯誤: {response.text}")
            return None
    
    def test_contextual_chat(self, conversation_context: Dict[str, Any] = None):
        """測試帶上下文的對話"""
        print("🧠 測試帶上下文對話...")
        
        chat_data = {
            "question": "剛才我們聊什麼了？",
            "user_id": "test_user",
            "include_sources": True
        }
        
        if conversation_context:
            chat_data["conversation_context"] = conversation_context
        
        response = self.session.post(f"{self.base_url}/chat", json=chat_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 上下文對話成功")
            print(f"   回答: {data['answer'][:100]}...")
            print(f"   上下文消息數: {len(data['context']['messages'])}")
            return data
        else:
            print(f"❌ 上下文對話失敗: {response.status_code}")
            return None
    
    def test_knowledge_base_status(self):
        """測試知識庫狀態"""
        print("📚 測試知識庫狀態...")
        
        response = self.session.get(f"{self.base_url}/knowledge-base")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 知識庫狀態獲取成功")
            print(f"   文件數: {data['total_files']}")
            print(f"   文本塊數: {data['total_chunks']}")
            print(f"   總大小: {data['total_size_mb']:.2f} MB")
            return True
        else:
            print(f"❌ 知識庫狀態獲取失敗: {response.status_code}")
            return False
    
    def test_conversation_history(self):
        """測試對話記錄"""
        print("📝 測試對話記錄...")
        
        response = self.session.get(f"{self.base_url}/conversations?page=1&page_size=5")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 對話記錄獲取成功")
            print(f"   總數: {data['total_count']}")
            print(f"   當前頁: {data['page']}")
            print(f"   頁面大小: {data['page_size']}")
            return True
        else:
            print(f"❌ 對話記錄獲取失敗: {response.status_code}")
            return False
    
    def test_conversation_stats(self):
        """測試對話統計"""
        print("📊 測試對話統計...")
        
        response = self.session.get(f"{self.base_url}/conversations/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 對話統計獲取成功")
            print(f"   統計項目: {len(data)}")
            return True
        else:
            print(f"❌ 對話統計獲取失敗: {response.status_code}")
            return False
    
    def run_full_test(self):
        """運行完整測試套件"""
        print("🧪 開始 Enhanced RAG API 完整測試")
        print("=" * 50)
        
        # 測試健康檢查
        if not self.test_health_check():
            print("❌ 健康檢查失敗，停止測試")
            return False
        print()
        
        # 測試認證
        if not self.test_authentication(API_KEYS["demo"]):
            print("❌ 認證失敗，停止測試")
            return False
        print()
        
        # 測試知識庫狀態
        self.test_knowledge_base_status()
        print()
        
        # 測試簡單對話
        chat_result = self.test_simple_chat()
        print()
        
        # 測試帶上下文對話
        if chat_result:
            context = chat_result.get('context')
            self.test_contextual_chat(context)
        print()
        
        # 測試對話記錄
        self.test_conversation_history()
        print()
        
        # 測試對話統計
        self.test_conversation_stats()
        print()
        
        print("✅ 所有測試完成!")
        return True

def main():
    """主函數"""
    # 檢查 API 是否運行
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ API 服務未運行 (狀態碼: {response.status_code})")
            print(f"請先運行: python run_enhanced_api.py")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ 無法連接到 API 服務: {e}")
        print(f"請確保 API 服務正在運行: python run_enhanced_api.py")
        return
    
    # 運行測試
    tester = APITester()
    tester.run_full_test()

if __name__ == "__main__":
    main()