#!/usr/bin/env python3
"""
維度配置驗證工具
檢查當前維度配置是否正確
"""

import os
import sys
import requests
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_env_file():
    """檢查 .env 文件配置"""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ 未找到 .env 文件")
        return None
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for line in content.split('\n'):
        if line.strip().startswith('ELASTICSEARCH_VECTOR_DIMENSION='):
            dimension = int(line.split('=')[1].strip())
            print(f"✅ .env 文件配置: {dimension} 維度")
            return dimension
    
    print("❌ .env 文件中未找到 ELASTICSEARCH_VECTOR_DIMENSION")
    return None

def check_config_py():
    """檢查 config.py 配置"""
    try:
        from config.config import ELASTICSEARCH_VECTOR_DIMENSION
        print(f"✅ config.py 配置: {ELASTICSEARCH_VECTOR_DIMENSION} 維度")
        return ELASTICSEARCH_VECTOR_DIMENSION
    except ImportError:
        print("❌ 無法導入 config.py")
        return None

def check_elasticsearch_connection():
    """檢查 Elasticsearch 連接"""
    try:
        response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            status = health.get('status', 'unknown')
            print(f"✅ Elasticsearch 連接正常 (狀態: {status})")
            return True
        else:
            print(f"❌ Elasticsearch 響應異常: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Elasticsearch 連接失敗: {e}")
        return False

def test_embedding_generation(expected_dimension):
    """測試嵌入生成"""
    try:
        from src.utils.embedding_fix import SafeJinaEmbedding
        
        api_key = os.getenv("JINA_API_KEY")
        if not api_key:
            print("❌ 未設置 JINA_API_KEY")
            return False
        
        embedding_model = SafeJinaEmbedding(
            api_key=api_key,
            model="jina-embeddings-v3",
            dimensions=expected_dimension
        )
        
        if not embedding_model.use_api:
            print("❌ Jina API 不可用")
            return False
        
        test_text = "測試嵌入生成"
        embedding = embedding_model.get_text_embedding(test_text)
        actual_dimension = len(embedding)
        
        if actual_dimension == expected_dimension:
            print(f"✅ 嵌入生成測試成功: {actual_dimension} 維度")
            return True
        else:
            print(f"❌ 嵌入維度不符: 預期 {expected_dimension}, 實際 {actual_dimension}")
            return False
            
    except Exception as e:
        print(f"❌ 嵌入生成測試失敗: {e}")
        return False

def check_elasticsearch_index():
    """檢查 Elasticsearch 索引狀態"""
    try:
        response = requests.get("http://localhost:9200/_cat/indices?v", timeout=5)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            rag_indices = [line for line in lines if 'rag_intelligent_assistant' in line]
            
            if rag_indices:
                print("✅ 找到 RAG 索引:")
                for line in rag_indices:
                    print(f"   {line}")
                return True
            else:
                print("⚠️ 未找到 RAG 索引，可能需要重新索引數據")
                return False
        else:
            print(f"❌ 無法獲取索引信息: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ 檢查索引失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔍 維度配置驗證工具")
    print("=" * 30)
    
    # 檢查配置文件
    env_dimension = check_env_file()
    config_dimension = check_config_py()
    
    # 檢查配置一致性
    if env_dimension and config_dimension:
        if env_dimension == config_dimension:
            print(f"✅ 配置一致性檢查通過: {env_dimension} 維度")
            target_dimension = env_dimension
        else:
            print(f"⚠️ 配置不一致: .env({env_dimension}) vs config.py({config_dimension})")
            target_dimension = env_dimension  # 優先使用 .env 配置
    elif env_dimension:
        target_dimension = env_dimension
    elif config_dimension:
        target_dimension = config_dimension
    else:
        print("❌ 無法獲取維度配置")
        return 1
    
    print(f"\n🎯 目標維度: {target_dimension}")
    print("-" * 30)
    
    # 檢查服務狀態
    es_connected = check_elasticsearch_connection()
    
    # 測試嵌入生成
    if target_dimension:
        embedding_ok = test_embedding_generation(target_dimension)
    else:
        embedding_ok = False
    
    # 檢查索引狀態
    if es_connected:
        index_ok = check_elasticsearch_index()
    else:
        index_ok = False
    
    # 總結
    print(f"\n📋 驗證結果總結:")
    print("-" * 20)
    print(f"配置文件: {'✅ 正常' if target_dimension else '❌ 異常'}")
    print(f"ES 連接:  {'✅ 正常' if es_connected else '❌ 異常'}")
    print(f"嵌入生成: {'✅ 正常' if embedding_ok else '❌ 異常'}")
    print(f"索引狀態: {'✅ 正常' if index_ok else '⚠️ 需要重建'}")
    
    if target_dimension and es_connected and embedding_ok:
        print(f"\n🎉 維度配置驗證成功！當前維度: {target_dimension}")
        
        if not index_ok:
            print(f"\n💡 建議:")
            print(f"   - 重新上傳文檔以創建新的索引")
            print(f"   - 或運行數據重新索引程序")
        
        return 0
    else:
        print(f"\n❌ 維度配置存在問題，請檢查:")
        if not target_dimension:
            print(f"   - 檢查 .env 和 config.py 文件")
        if not es_connected:
            print(f"   - 檢查 Elasticsearch 服務狀態")
        if not embedding_ok:
            print(f"   - 檢查 Jina API 連接和配置")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())