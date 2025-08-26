"""
Multi-Embedding Manager
多Embedding模型管理器，支援不同場景的最佳embedding選擇
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingModelConfig:
    """Embedding模型配置"""
    model_name: str
    model_type: str  # general, domain, sentence, keyword
    dimension: int
    strengths: List[str]  # 優勢場景
    use_cases: List[str]  # 適用情況
    weight: float = 1.0

class BaseEmbeddingModel(ABC):
    """抽象Embedding模型基類"""
    
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self.model = None
    
    @abstractmethod
    def load_model(self):
        """載入模型"""
        pass
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """文本embedding"""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量embedding"""
        pass

class JinaEmbeddingModel(BaseEmbeddingModel):
    """Jina Embedding模型"""
    
    def load_model(self):
        try:
            from llama_index.core import Settings
            self.model = Settings.embed_model
            logger.info(f"✅ 載入Jina模型: {self.config.model_name}")
        except Exception as e:
            logger.error(f"❌ Jina模型載入失敗: {e}")
    
    def embed_text(self, text: str) -> List[float]:
        if not self.model:
            self.load_model()
        return self.model.get_text_embedding(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            self.load_model()
        return [self.embed_text(text) for text in texts]

class HuggingFaceEmbeddingModel(BaseEmbeddingModel):
    """HuggingFace Embedding模型"""
    
    def load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.config.model_name)
            logger.info(f"✅ 載入HuggingFace模型: {self.config.model_name}")
        except ImportError:
            logger.warning("⚠️ sentence-transformers 未安裝，使用備用方案")
            self.load_model = self._load_backup_model
        except Exception as e:
            logger.error(f"❌ HuggingFace模型載入失敗: {e}")
    
    def _load_backup_model(self):
        """備用方案：使用Jina模型"""
        from llama_index.core import Settings
        self.model = Settings.embed_model
        logger.info("🔄 使用Jina模型作為備用")
    
    def embed_text(self, text: str) -> List[float]:
        if not self.model:
            self.load_model()
        
        try:
            if hasattr(self.model, 'encode'):
                # SentenceTransformer模型
                embedding = self.model.encode([text])[0]
                return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            else:
                # 備用Jina模型
                return self.model.get_text_embedding(text)
        except Exception as e:
            logger.error(f"❌ embedding生成失敗: {e}")
            return [0.0] * self.config.dimension
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            self.load_model()
        
        try:
            if hasattr(self.model, 'encode'):
                embeddings = self.model.encode(texts)
                return [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
            else:
                return [self.embed_text(text) for text in texts]
        except Exception as e:
            logger.error(f"❌ 批量embedding生成失敗: {e}")
            return [[0.0] * self.config.dimension for _ in texts]

class MultiEmbeddingManager:
    """多Embedding模型管理器"""
    
    def __init__(self, enable_multi_embedding: bool = True):
        self.enable_multi_embedding = enable_multi_embedding
        self.models: Dict[str, BaseEmbeddingModel] = {}
        self.model_configs = self._get_default_configs()
        
        # 初始化模型
        self._initialize_models()
        
        logger.info(f"🎯 MultiEmbeddingManager 初始化完成")
        logger.info(f"   - 啟用多模型: {enable_multi_embedding}")
        logger.info(f"   - 可用模型: {list(self.models.keys())}")
    
    def _get_default_configs(self) -> Dict[str, EmbeddingModelConfig]:
        """獲取預設模型配置"""
        return {
            "general": EmbeddingModelConfig(
                model_name="jina-embeddings-v3",
                model_type="general",
                dimension=1024,
                strengths=["通用文本", "多語言", "平衡性能"],
                use_cases=["日常查詢", "通用檢索", "基礎相似度"],
                weight=1.0
            ),
            "domain": EmbeddingModelConfig(
                model_name="BAAI/bge-base-zh-v1.5",
                model_type="domain",
                dimension=768,
                strengths=["中文優化", "領域特定", "語義理解"],
                use_cases=["專業文檔", "技術內容", "中文查詢"],
                weight=0.8
            ),
            "sentence": EmbeddingModelConfig(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_type="sentence",
                dimension=384,
                strengths=["句子級相似度", "語義匹配", "快速推理"],
                use_cases=["句子比對", "問答匹配", "快速檢索"],
                weight=0.7
            ),
            "keyword": EmbeddingModelConfig(
                model_name="keyword-embedding-custom",
                model_type="keyword",
                dimension=256,
                strengths=["關鍵詞抽取", "主題識別", "稀疏表示"],
                use_cases=["關鍵詞搜索", "主題分析", "標籤匹配"],
                weight=0.5
            )
        }
    
    def _initialize_models(self):
        """初始化所有模型"""
        for model_name, config in self.model_configs.items():
            try:
                if model_name == "general":
                    # 使用Jina作為通用模型
                    model = JinaEmbeddingModel(config)
                elif model_name in ["domain", "sentence"]:
                    # 使用HuggingFace模型
                    model = HuggingFaceEmbeddingModel(config)
                else:
                    # 關鍵詞模型使用簡化版實現
                    model = self._create_keyword_model(config)
                
                model.load_model()
                self.models[model_name] = model
                
            except Exception as e:
                logger.warning(f"⚠️ 模型 {model_name} 初始化失敗: {e}")
                # 使用通用模型作為備用
                if model_name != "general":
                    self.models[model_name] = self.models.get("general")
    
    def _create_keyword_model(self, config: EmbeddingModelConfig) -> BaseEmbeddingModel:
        """創建關鍵詞模型（簡化版實現）"""
        class KeywordEmbeddingModel(BaseEmbeddingModel):
            def load_model(self):
                # 關鍵詞模型不需要載入，直接標記為已載入
                self.model = "keyword_model_placeholder"
            
            def embed_text(self, text: str) -> List[float]:
                # 簡化版關鍵詞embedding：基於TF-IDF的向量表示
                return self._simple_keyword_embedding(text)
            
            def embed_batch(self, texts: List[str]) -> List[List[float]]:
                return [self.embed_text(text) for text in texts]
            
            def _simple_keyword_embedding(self, text: str) -> List[float]:
                """簡化版關鍵詞embedding"""
                # 這裡實現一個基礎的TF-IDF風格的向量
                words = text.lower().split()
                
                # 預定義的關鍵詞詞典（實際應用中應該更大更完整）
                keyword_dict = {
                    "機器學習": 1, "深度學習": 2, "人工智能": 3, "演算法": 4,
                    "模型": 5, "訓練": 6, "預測": 7, "數據": 8, "特徵": 9, "分類": 10
                }
                
                # 創建固定維度的向量
                vector = [0.0] * self.config.dimension
                
                for word in words:
                    if word in keyword_dict:
                        idx = keyword_dict[word] % self.config.dimension
                        vector[idx] += 1.0
                
                # 正規化
                norm = sum(x*x for x in vector) ** 0.5
                if norm > 0:
                    vector = [x/norm for x in vector]
                
                return vector
        
        return KeywordEmbeddingModel(config)
    
    def get_best_model_for_content(self, content: str, content_type: str = "paragraph") -> str:
        """根據內容選擇最佳模型"""
        
        if not self.enable_multi_embedding:
            return "general"
        
        # 根據內容類型選擇模型
        if content_type == "title":
            return "sentence"  # 標題使用句子模型
        elif content_type == "keyword" or len(content.split()) < 5:
            return "keyword"   # 短文本使用關鍵詞模型
        elif self._is_technical_content(content):
            return "domain"    # 技術內容使用領域模型
        else:
            return "general"   # 預設使用通用模型
    
    def _is_technical_content(self, content: str) -> bool:
        """判斷是否為技術內容"""
        tech_keywords = [
            "算法", "模型", "訓練", "預測", "機器學習", "深度學習", 
            "人工智能", "數據", "特徵", "分類", "回歸", "神經網路"
        ]
        
        content_lower = content.lower()
        tech_count = sum(1 for keyword in tech_keywords if keyword in content_lower)
        
        # 如果包含2個以上技術關鍵詞，認為是技術內容
        return tech_count >= 2
    
    def embed_with_multiple_models(
        self, 
        text: str, 
        model_names: List[str] = None
    ) -> Dict[str, List[float]]:
        """使用多個模型生成embedding"""
        
        if not self.enable_multi_embedding:
            # 只使用通用模型
            general_embedding = self.models["general"].embed_text(text)
            return {"general": general_embedding}
        
        if model_names is None:
            model_names = list(self.models.keys())
        
        embeddings = {}
        
        for model_name in model_names:
            if model_name in self.models:
                try:
                    embedding = self.models[model_name].embed_text(text)
                    embeddings[model_name] = embedding
                except Exception as e:
                    logger.warning(f"⚠️ 模型 {model_name} embedding失敗: {e}")
                    # 使用通用模型作為備用
                    if "general" in self.models and model_name != "general":
                        embeddings[model_name] = self.models["general"].embed_text(text)
        
        return embeddings
    
    def get_adaptive_embedding(self, text: str, query_context: Dict[str, Any] = None) -> List[float]:
        """自適應embedding：根據上下文選擇最佳策略"""
        
        # 分析查詢上下文
        content_type = "paragraph"
        if query_context:
            content_type = query_context.get("content_type", "paragraph")
            search_intent = query_context.get("search_intent", "general")
        
        # 選擇最佳模型
        best_model = self.get_best_model_for_content(text, content_type)
        
        # 生成embedding
        if best_model in self.models:
            return self.models[best_model].embed_text(text)
        else:
            # 備用方案
            return self.models["general"].embed_text(text)
    
    def compute_ensemble_embedding(
        self, 
        text: str, 
        model_weights: Dict[str, float] = None
    ) -> List[float]:
        """計算集成embedding"""
        
        if not self.enable_multi_embedding:
            return self.models["general"].embed_text(text)
        
        # 使用預設權重
        if model_weights is None:
            model_weights = {name: config.weight for name, config in self.model_configs.items()}
        
        # 獲取所有模型的embedding
        all_embeddings = self.embed_with_multiple_models(text)
        
        if not all_embeddings:
            logger.warning("⚠️ 所有模型embedding失敗，使用零向量")
            return [0.0] * 512
        
        # 計算加權平均
        ensemble_embedding = None
        total_weight = 0.0
        
        for model_name, embedding in all_embeddings.items():
            weight = model_weights.get(model_name, 0.0)
            if weight > 0:
                embedding_array = np.array(embedding)
                
                if ensemble_embedding is None:
                    ensemble_embedding = weight * embedding_array
                else:
                    # 處理不同維度的embedding
                    if len(embedding_array) != len(ensemble_embedding):
                        # 調整到相同維度（取較小者）
                        min_dim = min(len(embedding_array), len(ensemble_embedding))
                        embedding_array = embedding_array[:min_dim]
                        ensemble_embedding = ensemble_embedding[:min_dim]
                    
                    ensemble_embedding += weight * embedding_array
                
                total_weight += weight
        
        # 正規化
        if total_weight > 0 and ensemble_embedding is not None:
            ensemble_embedding = ensemble_embedding / total_weight
            return ensemble_embedding.tolist()
        else:
            # 備用方案：返回通用模型的embedding
            return self.models["general"].embed_text(text)
    
    def get_model_info(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有模型信息"""
        model_info = {}
        
        for name, config in self.model_configs.items():
            model_info[name] = {
                "model_name": config.model_name,
                "model_type": config.model_type,
                "dimension": config.dimension,
                "strengths": config.strengths,
                "use_cases": config.use_cases,
                "weight": config.weight,
                "loaded": name in self.models and self.models[name].model is not None
            }
        
        return model_info
    
    def benchmark_models(self, test_texts: List[str]) -> Dict[str, Dict[str, float]]:
        """基準測試所有模型"""
        import time
        
        results = {}
        
        for model_name, model in self.models.items():
            if model.model is None:
                continue
            
            start_time = time.time()
            
            try:
                # 測試單個文本embedding
                single_time_start = time.time()
                model.embed_text(test_texts[0])
                single_time = time.time() - single_time_start
                
                # 測試批量embedding
                batch_time_start = time.time()
                model.embed_batch(test_texts[:5])  # 測試5個文本
                batch_time = (time.time() - batch_time_start) / 5
                
                total_time = time.time() - start_time
                
                results[model_name] = {
                    "single_embedding_time": single_time,
                    "batch_embedding_time": batch_time,
                    "total_time": total_time,
                    "dimension": self.model_configs[model_name].dimension
                }
                
            except Exception as e:
                logger.error(f"❌ 模型 {model_name} 基準測試失敗: {e}")
                results[model_name] = {
                    "error": str(e)
                }
        
        return results