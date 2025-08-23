# Enhanced RAG API 文檔

## 概述

Enhanced RAG API 提供完整的智能問答和知識庫管理功能，包括：

- **智能問答**：帶前後文對話記憶的 RAG 查詢
- **知識庫管理**：文件上傳、處理、删除
- **對話記錄**：對話歷史管理和統計
- **認證機制**：API 金鑰和 JWT Token 認證
- **系統監控**：健康檢查和狀態監控

## 快速開始

### 1. 啟動 API 服務

```bash
# 安裝依賴
pip install -r api/requirements_api.txt

# 啟動服務
python run_enhanced_api.py
```

API 服務將在 `http://localhost:8000` 啟動

### 2. API 文檔

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 認證

API 支援兩種認證方式：

#### 預設 API 金鑰

| 用戶類型 | API Key | 權限 |
|---------|---------|------|
| demo | `demo-api-key-123` | read, write |
| admin | `admin-api-key-456` | read, write |
| user | `user-api-key-789` | read |

#### JWT Token 認證

```bash
# 獲取 Token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "demo-api-key-123"}'

# 使用 Token
curl -X GET "http://localhost:8000/health" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API 端點

### 基礎端點

#### `GET /` - 根端點
返回 API 基本信息

#### `GET /health` - 健康檢查
返回系統健康狀態

**響應例子：**
```json
{
  "status": "healthy",
  "elasticsearch_connected": true,
  "api_version": "2.0.0",
  "uptime_seconds": 3600,
  "total_documents": 42,
  "total_conversations": 128,
  "timestamp": "2025-08-22T12:00:00"
}
```

### 認證端點

#### `POST /auth/token` - 生成訪問令牌

**請求：**
```json
{
  "api_key": "demo-api-key-123"
}
```

**響應：**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "demo",
  "permissions": ["read", "write"]
}
```

### 智能問答端點

#### `POST /chat` - 智能問答（帶對話記憶）

**請求：**
```json
{
  "question": "什麼是機器學習？",
  "conversation_context": {
    "conversation_id": "uuid-string",
    "messages": [
      {
        "role": "user",
        "content": "你好",
        "timestamp": "2025-08-22T12:00:00"
      },
      {
        "role": "assistant", 
        "content": "你好！有什麼我可以幫助你的嗎？",
        "timestamp": "2025-08-22T12:00:01"
      }
    ],
    "max_history": 10
  },
  "user_id": "user123",
  "session_id": "session456",
  "include_sources": true,
  "max_sources": 3
}
```

**響應：**
```json
{
  "answer": "機器學習是人工智能的一個子領域...",
  "sources": [
    {
      "source": "ml_guide.pdf",
      "file_path": "/docs/ml_guide.pdf",
      "score": 0.95,
      "content": "機器學習的定義...",
      "page": "1",
      "type": "document"
    }
  ],
  "conversation_id": "uuid-string",
  "metadata": {
    "request_id": "req-123",
    "user_id": "user123",
    "contextual_query": true
  },
  "context": {
    "conversation_id": "uuid-string",
    "messages": [...],
    "max_history": 10
  },
  "response_time_ms": 1250,
  "timestamp": "2025-08-22T12:00:00"
}
```

### 知識庫管理端點

#### `POST /upload` - 上傳文件

**請求：**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

**響應：**
```json
{
  "file_id": "uuid-string",
  "filename": "document.pdf",
  "size_bytes": 1024000,
  "status": "processed",
  "chunks_created": 25,
  "processing_time_ms": 3000
}
```

#### `GET /knowledge-base` - 獲取知識庫狀態

**響應：**
```json
{
  "total_files": 5,
  "total_chunks": 150,
  "total_size_mb": 12.5,
  "files": [
    {
      "id": "uuid-string",
      "name": "document.pdf",
      "size_mb": 2.5,
      "type": "pdf",
      "upload_time": "2025-08-22T12:00:00",
      "chunk_count": 30,
      "status": "active"
    }
  ]
}
```

#### `DELETE /knowledge-base/files/{file_id}` - 刪除文件

**響應：**
```json
{
  "message": "File uuid-string deleted successfully"
}
```

### 對話記錄端點

#### `GET /conversations` - 獲取對話記錄

**參數：**
- `page`: 頁數 (默認: 1)
- `page_size`: 每頁大小 (默認: 20)
- `user_id`: 用戶ID (可選)
- `session_id`: 會話ID (可選)

**響應：**
```json
{
  "conversations": [
    {
      "conversation_id": "uuid-string",
      "question": "什麼是AI？",
      "answer": "AI是人工智能...",
      "timestamp": "2025-08-22T12:00:00",
      "user_id": "user123"
    }
  ],
  "total_count": 100,
  "page": 1,
  "page_size": 20
}
```

#### `GET /conversations/stats` - 獲取對話統計

**響應：**
```json
{
  "total_conversations": 500,
  "unique_sessions": 50,
  "average_rating": 4.2,
  "conversations_by_date": [...],
  "popular_tags": [...]
}
```

## 對話記憶功能

### 前後文理解

API 自動維護對話上下文，實現真正的多輪對話：

```json
{
  "conversation_context": {
    "conversation_id": "uuid-string",
    "messages": [
      {"role": "user", "content": "什麼是機器學習？"},
      {"role": "assistant", "content": "機器學習是..."},
      {"role": "user", "content": "它有哪些類型？"},
      {"role": "assistant", "content": "機器學習主要有三種類型..."}
    ]
  }
}
```

### 上下文策略

- **自動上下文構建**：自動將歷史對話轉換為查詢上下文
- **消息數量限制**：可配置保留的最大消息數 (默認: 10對)
- **智能截斷**：超出限制時保留最近的對話
- **會話隔離**：不同 conversation_id 的對話完全隔離

## 錯誤處理

### HTTP 狀態碼

- `200`: 成功
- `400`: 請求錯誤 (例如：無效文件格式)
- `401`: 認證失敗
- `403`: 權限不足
- `404`: 資源不存在
- `500`: 服務器內部錯誤
- `503`: 服務不可用

### 錯誤響應格式

```json
{
  "error": "Authentication failed",
  "detail": "Invalid API key or token",
  "timestamp": "2025-08-22T12:00:00",
  "request_id": "req-123"
}
```

## 性能優化

### 響應時間

- 健康檢查: < 50ms
- 簡單對話: < 2000ms
- 帶上下文對話: < 3000ms
- 文件上傳: 取決於文件大小

### 併發處理

- 支援多個並發請求
- 每個請求獨立處理
- 自動負載均衡

### 緩存策略

- 文檔向量緩存
- 對話上下文緩存
- API 響應部分緩存

## 安全考慮

### 認證安全

- JWT Token 24小時過期
- API 金鑰需定期輪換
- 支援權限分級

### 數據安全

- 對話記錄加密存儲
- 用戶數據隔離
- 敏感信息自動過濾

### 生產環境建議

```python
# 環境變量配置
API_SECRET_KEY=your-strong-secret-key-in-production
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# CORS 設置
CORS_ORIGINS=["https://yourdomain.com"]
```

## 測試

運行完整的 API 測試：

```bash
python tests/test_enhanced_api.py
```

測試覆蓋：

- ✅ 健康檢查
- ✅ 認證流程
- ✅ 簡單對話
- ✅ 帶上下文對話
- ✅ 知識庫管理
- ✅ 對話記錄
- ✅ 錯誤處理

## 使用示例

### Python 客戶端

```python
import requests

class RAGAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.session = requests.Session()
        
        # 獲取 Token
        response = self.session.post(f"{base_url}/auth/token", 
                                   json={"api_key": api_key})
        token = response.json()["access_token"]
        
        # 設置認證頭
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    
    def chat(self, question, context=None):
        data = {"question": question}
        if context:
            data["conversation_context"] = context
            
        response = self.session.post(f"{self.base_url}/chat", json=data)
        return response.json()

# 使用例子
client = RAGAPIClient("http://localhost:8000", "demo-api-key-123")

# 第一次對話
result1 = client.chat("什麼是機器學習？")
print(result1["answer"])

# 帶上下文的第二次對話
result2 = client.chat("它有哪些應用？", result1["context"])
print(result2["answer"])
```

### JavaScript 客戶端

```javascript
class RAGAPIClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.token = null;
  }
  
  async authenticate() {
    const response = await fetch(`${this.baseUrl}/auth/token`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({api_key: this.apiKey})
    });
    
    const data = await response.json();
    this.token = data.access_token;
  }
  
  async chat(question, context = null) {
    const data = {question};
    if (context) data.conversation_context = context;
    
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify(data)
    });
    
    return await response.json();
  }
}

// 使用例子
const client = new RAGAPIClient('http://localhost:8000', 'demo-api-key-123');
await client.authenticate();

const result = await client.chat('你好，請介紹一下你的功能');
console.log(result.answer);
```

## 部署指南

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r api/requirements_api.txt
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "run_enhanced_api.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  enhanced-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_SECRET_KEY=your-production-secret
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
```

## 監控和日誌

### 健康檢查端點

定期檢查 `/health` 端點監控服務狀態

### 日誌記錄

- 請求/響應日誌
- 錯誤堆疊追蹤  
- 性能指標記錄

### 指標監控

- 請求數量和響應時間
- 錯誤率統計
- 資源使用情況

## 版本更新

### v2.0.0 (當前版本)

- ✅ 完整對話記憶功能
- ✅ JWT Token 認證
- ✅ 知識庫管理 API
- ✅ 對話記錄管理
- ✅ 完整錯誤處理

### 計劃功能

- [ ] WebSocket 實時對話
- [ ] 文件批量處理
- [ ] 高級搜索過濾
- [ ] 用戶偏好設置
- [ ] API 使用統計

---

如需更多幫助，請參考 API 文檔或提交 Issue。