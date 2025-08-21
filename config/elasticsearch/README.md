# Elasticsearch Mapping 配置文件

此目錄包含 Elasticsearch 索引映射的配置文件，支持模板化和變數替換。

## 文件說明

### 1. `index_mapping.json`
**默認的文檔索引映射配置**
- 支持中文和多語言分析器
- 包含完整的 metadata 字段定義
- 支持變數替換：`${SHARDS}`, `${REPLICAS}`, `${DIMENSION}`, `${SIMILARITY}`

### 2. `conversation_mapping.json`
**對話記錄索引映射配置**
- 專門為對話記錄設計
- 包含 nested 類型的 sources 字段
- 支持評分和反饋功能

### 3. `high_performance_mapping.json`
**高性能索引映射配置**
- 優化的索引設置（刷新間隔、結果窗口等）
- 嚴格的動態映射控制
- 優化的向量索引選項（int8_hnsw）
- 選擇性字段索引以提高性能

## 變數替換

支持以下變數：
- `${SHARDS}`: 分片數量
- `${REPLICAS}`: 副本數量  
- `${DIMENSION}`: 向量維度
- `${SIMILARITY}`: 向量相似度算法

## 使用方法

### Python 代碼中使用

```python
from config.elasticsearch.mapping_loader import ElasticsearchMappingLoader

# 創建加載器
loader = ElasticsearchMappingLoader()

# 使用默認配置
mapping = loader.load_mapping()

# 使用自定義變數
mapping = loader.load_mapping(
    DIMENSION=384,
    SIMILARITY="cosine",
    SHARDS=2,
    REPLICAS=1
)

# 使用 RAG 系統配置
config = {
    'shards': 1,
    'replicas': 0,
    'dimension': 384,
    'similarity': 'cosine'
}
mapping = loader.create_mapping_with_config(config)
```

### 直接使用便捷函數

```python
from config.elasticsearch.mapping_loader import get_elasticsearch_mapping

# 使用默認配置
mapping = get_elasticsearch_mapping()

# 使用自定義配置
config = {'dimension': 384, 'similarity': 'cosine'}
mapping = get_elasticsearch_mapping(config)
```

## 自定義配置

### 創建新的 mapping 文件

1. 複製現有的 `.json` 文件
2. 修改配置參數
3. 使用變數替換支持動態配置

### 配置驗證

```python
loader = ElasticsearchMappingLoader()
mapping = loader.load_mapping()

if loader.validate_mapping(mapping):
    print("✅ 配置有效")
else:
    print("❌ 配置無效")
```

## 最佳實踐

### 1. 生產環境配置
```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s"
  }
}
```

### 2. 開發環境配置
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "1s"
  }
}
```

### 3. 向量配置優化
```json
{
  "embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine",
    "index_options": {
      "type": "int8_hnsw",
      "m": 16,
      "ef_construction": 100
    }
  }
}
```

## 故障排除

### 常見問題

1. **變數未替換**
   - 確認變數格式：`${VARIABLE_NAME}`
   - 檢查傳入的變數字典

2. **JSON 格式錯誤**
   - 使用 JSON 驗證工具檢查語法
   - 注意逗號和引號

3. **映射衝突**
   - 刪除舊索引或使用新索引名
   - 檢查字段類型一致性

4. **維度不匹配**
   - 確認 `${DIMENSION}` 值與嵌入模型一致
   - 檢查 `.env` 文件中的配置

### 調試命令

```bash
# 檢查索引映射
curl -X GET "localhost:9200/your_index/_mapping?pretty"

# 檢查索引設置
curl -X GET "localhost:9200/your_index/_settings?pretty"

# 刪除索引（謹慎操作！）
curl -X DELETE "localhost:9200/your_index"
```

## 更新歷史

- v1.0: 初始版本，基本映射配置
- v1.1: 添加高性能配置和對話記錄映射
- v1.2: 支持變數替換和模板化配置