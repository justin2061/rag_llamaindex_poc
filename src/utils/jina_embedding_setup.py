"""
Jina Embedding 設置工具
確保在RAG系統初始化時正確配置Jina embeddings
"""

import logging
import os
from typing import Optional
from llama_index.core import Settings

# 配置logging
logger = logging.getLogger(__name__)

def setup_jina_embedding(api_key: Optional[str] = None, model: str = "jina-embeddings-v3") -> bool:
    """
    設置Jina embedding模型作為全局默認模型
    
    Args:
        api_key: Jina API密鑰，如果None則從環境變數獲取
        model: 模型名稱，默認為jina-embeddings-v3
    
    Returns:
        bool: 設置是否成功
    """
    try:
        # 導入Jina embedding
        from llama_index.embeddings.jinaai import JinaEmbedding
        
        # 獲取API密鑰
        if api_key is None:
            from config.config import JINA_API_KEY
            api_key = JINA_API_KEY
        
        if not api_key or not api_key.strip():
            logger.error("❌ Jina API密鑰未提供")
            return False
        
        logger.info(f"🔧 設置Jina embedding模型: {model}")
        
        # 創建Jina embedding模型
        jina_embed = JinaEmbedding(
            api_key=api_key,
            model=model
        )
        
        # 測試embedding以確保模型工作正常
        test_text = "Test embedding functionality"
        test_embedding = jina_embed.get_text_embedding(test_text)
        
        # 設置為全局模型
        Settings.embed_model = jina_embed
        
        logger.info(f"✅ Jina embedding設置成功")
        logger.info(f"   - 模型: {model}")
        logger.info(f"   - 維度: {len(test_embedding)}")
        logger.info(f"   - API密鑰前綴: {api_key[:20]}...")
        
        return True
        
    except ImportError:
        logger.error("❌ llama-index-embeddings-jinaai 模組未安裝")
        logger.info("   請運行: pip install llama-index-embeddings-jinaai")
        return False
        
    except Exception as e:
        logger.error(f"❌ Jina embedding設置失敗: {e}")
        return False

def setup_fallback_embedding() -> bool:
    """
    設置後備embedding模型（本地模型）
    
    Returns:
        bool: 設置是否成功
    """
    try:
        # 優先嘗試本地 Sentence Transformers Jina 模型
        from src.utils.sentence_transformer_embedding import setup_sentence_transformer_jina
        
        logger.info("🔄 嘗試使用本地 Sentence Transformers Jina 模型...")
        if setup_sentence_transformer_jina("jinaai/jina-embeddings-v3"):
            logger.info("✅ 本地 Jina 模型設置成功")
            return True
        
        # 如果失敗，回退到簡單模型
        logger.warning("⚠️ 本地 Jina 模型不可用，使用簡單後備模型")
        from src.utils.immediate_fix import setup_immediate_fix
        setup_immediate_fix()
        return True
        
    except Exception as e:
        logger.error(f"❌ 後備embedding設置失敗: {e}")
        return False

def ensure_embedding_initialized() -> bool:
    """
    確保embedding模型已初始化，優先使用Jina，失敗則使用後備方案
    
    Returns:
        bool: 是否成功初始化任何embedding模型
    """
    # 首先嘗試設置Jina embedding
    if setup_jina_embedding():
        return True
    
    # 如果失敗，使用後備方案
    logger.warning("⚠️ Jina embedding設置失敗，使用後備方案")
    return setup_fallback_embedding()

if __name__ == "__main__":
    # 測試
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 測試Jina embedding設置...")
    
    if ensure_embedding_initialized():
        print("✅ Embedding初始化成功")
        
        # 測試embedding功能
        from llama_index.core import Settings
        test_text = "這是一個測試文本"
        embedding = Settings.embed_model.get_text_embedding(test_text)
        print(f"   - 測試文本: {test_text}")
        print(f"   - Embedding維度: {len(embedding)}")
        print(f"   - 前5個值: {embedding[:5]}")
        
    else:
        print("❌ Embedding初始化失敗")