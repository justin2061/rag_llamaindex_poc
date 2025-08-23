"""
Hierarchical Indexer System
階層式索引系統，支援多粒度文檔索引
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from elasticsearch import Elasticsearch
from llama_index.core import Document
from src.processors.enhanced_document_processor import EnhancedDocumentProcessor

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IndexingStrategy:
    """索引策略配置"""
    strategy_name: str
    chunk_size: int
    chunk_overlap: int
    embedding_models: List[str]
    enable_bm25: bool = True
    enable_structural_indexing: bool = True

class HierarchicalIndexer:
    """階層式索引器"""
    
    def __init__(
        self,
        elasticsearch_client: Elasticsearch,
        index_name: str,
        embedding_models: Dict[str, Any] = None,
        processor: EnhancedDocumentProcessor = None
    ):
        self.es_client = elasticsearch_client
        self.index_name = index_name
        self.embedding_models = embedding_models or {}
        self.processor = processor or EnhancedDocumentProcessor()
        
        # 預設索引策略
        self.indexing_strategies = [
            IndexingStrategy(
                strategy_name="precise",
                chunk_size=512,
                chunk_overlap=100,
                embedding_models=["general", "sentence"],
                enable_bm25=True,
                enable_structural_indexing=True
            ),
            IndexingStrategy(
                strategy_name="contextual",
                chunk_size=1024,
                chunk_overlap=200,
                embedding_models=["general", "domain"],
                enable_bm25=True,
                enable_structural_indexing=True
            ),
            IndexingStrategy(
                strategy_name="comprehensive",
                chunk_size=2048,
                chunk_overlap=400,
                embedding_models=["general"],
                enable_bm25=True,
                enable_structural_indexing=False  # 長文本不需要結構索引
            )
        ]
        
        logger.info(f"🏗️ HierarchicalIndexer 初始化完成")
        logger.info(f"   - 索引名稱: {index_name}")
        logger.info(f"   - 索引策略: {len(self.indexing_strategies)} 種")
    
    def create_hierarchical_index(self, documents: List[Document]) -> Dict[str, Any]:
        """
        創建階層式索引
        """
        logger.info(f"🚀 開始創建階層式索引，文檔數量: {len(documents)}")
        
        indexing_stats = {
            "total_documents": len(documents),
            "indexed_chunks": 0,
            "indexing_strategies": {},
            "start_time": datetime.now()
        }
        
        for document in documents:
            doc_stats = self._index_single_document(document)
            indexing_stats["indexed_chunks"] += doc_stats["chunks_created"]
            
            # 更新策略統計
            for strategy, count in doc_stats["strategy_stats"].items():
                if strategy not in indexing_stats["indexing_strategies"]:
                    indexing_stats["indexing_strategies"][strategy] = 0
                indexing_stats["indexing_strategies"][strategy] += count
        
        indexing_stats["end_time"] = datetime.now()
        indexing_stats["duration"] = (indexing_stats["end_time"] - indexing_stats["start_time"]).total_seconds()
        
        logger.info(f"✅ 階層式索引創建完成")
        logger.info(f"   - 總文檔數: {indexing_stats['total_documents']}")
        logger.info(f"   - 總chunks數: {indexing_stats['indexed_chunks']}")
        logger.info(f"   - 耗時: {indexing_stats['duration']:.2f}秒")
        
        return indexing_stats
    
    def _index_single_document(self, document: Document) -> Dict[str, Any]:
        """索引單個文檔"""
        doc_source = document.metadata.get('source', 'unknown')
        logger.info(f"📄 開始索引文檔: {doc_source}")
        
        doc_stats = {
            "chunks_created": 0,
            "strategy_stats": {}
        }
        
        try:
            # 1. 使用增強處理器處理文檔
            processed_documents = self.processor.process_document(document)
            
            # 2. 按不同策略創建索引
            for strategy in self.indexing_strategies:
                strategy_chunks = self._filter_chunks_by_strategy(processed_documents, strategy)
                
                for chunk_doc in strategy_chunks:
                    # 生成多種embeddings
                    embeddings = self._generate_multiple_embeddings(chunk_doc.text, strategy)
                    
                    # 創建索引文檔
                    index_doc = self._create_index_document(chunk_doc, embeddings, strategy)
                    
                    # 索引到Elasticsearch
                    self._index_to_elasticsearch(index_doc)
                    
                    doc_stats["chunks_created"] += 1
                
                strategy_name = strategy.strategy_name
                doc_stats["strategy_stats"][strategy_name] = len(strategy_chunks)
                logger.info(f"   - {strategy_name} 策略: {len(strategy_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"❌ 文檔索引失敗 {doc_source}: {e}")
        
        return doc_stats
    
    def _filter_chunks_by_strategy(self, documents: List[Document], strategy: IndexingStrategy) -> List[Document]:
        """根據策略過濾chunks"""
        filtered = []
        
        for doc in documents:
            chunking_info = doc.metadata.get('chunking_strategy', {})
            chunk_size = chunking_info.get('chunk_size', 0)
            
            # 根據策略的chunk_size範圍過濾
            size_range = self._get_size_range_for_strategy(strategy)
            if size_range[0] <= chunk_size <= size_range[1]:
                filtered.append(doc)
        
        return filtered
    
    def _get_size_range_for_strategy(self, strategy: IndexingStrategy) -> tuple:
        """獲取策略的大小範圍"""
        base_size = strategy.chunk_size
        return (base_size - 100, base_size + 100)  # 允許±100的範圍
    
    def _generate_multiple_embeddings(self, text: str, strategy: IndexingStrategy) -> Dict[str, List[float]]:
        """生成多種embedding"""
        embeddings = {}
        
        try:
            from llama_index.core import Settings
            
            # 使用預設embedding模型
            if "general" in strategy.embedding_models:
                general_embedding = Settings.embed_model.get_text_embedding(text)
                embeddings["general"] = general_embedding
            
            # 如果配置了其他embedding模型，這裡可以調用
            # 為了簡化，暫時都使用同一個模型
            for model_name in strategy.embedding_models:
                if model_name != "general" and model_name not in embeddings:
                    # 這裡可以根據model_name調用不同的embedding模型
                    embeddings[model_name] = Settings.embed_model.get_text_embedding(text)
            
        except Exception as e:
            logger.warning(f"⚠️ 生成embedding失敗: {e}")
            # 提供後備方案
            embeddings["general"] = [0.0] * 512  # 零向量作為後備
        
        return embeddings
    
    def _create_index_document(self, chunk_doc: Document, embeddings: Dict[str, List[float]], strategy: IndexingStrategy) -> Dict[str, Any]:
        """創建索引文檔"""
        
        # 基本內容
        index_doc = {
            "content": chunk_doc.text,
            "metadata": chunk_doc.metadata,
        }
        
        # 添加主要embedding（用於向量搜索）
        if "general" in embeddings:
            index_doc["embedding"] = embeddings["general"]
        
        # 添加多種embeddings（用於多模型搜索）
        if len(embeddings) > 1:
            index_doc["embeddings"] = embeddings
        
        # 添加BM25內容（如果啟用）
        if strategy.enable_bm25:
            index_doc["bm25_content"] = chunk_doc.text
        
        # 添加標題和摘要（如果可以提取）
        title, summary = self._extract_title_and_summary(chunk_doc)
        if title:
            index_doc["title"] = title
        if summary:
            index_doc["summary"] = summary
        
        # 添加策略信息
        index_doc["indexing_strategy"] = {
            "strategy_name": strategy.strategy_name,
            "chunk_size": strategy.chunk_size,
            "chunk_overlap": strategy.chunk_overlap,
            "embedding_models": strategy.embedding_models,
            "indexed_at": datetime.now().isoformat()
        }
        
        # 添加搜索元數據
        index_doc["search_metadata"] = {
            "content_length": len(chunk_doc.text),
            "word_count": len(chunk_doc.text.split()),
            "has_title": bool(title),
            "has_summary": bool(summary),
            "structure_type": chunk_doc.metadata.get('document_structure', {}).get('content_type', 'unknown')
        }
        
        return index_doc
    
    def _extract_title_and_summary(self, chunk_doc: Document) -> tuple:
        """提取標題和摘要"""
        text = chunk_doc.text
        title = None
        summary = None
        
        # 檢查是否為標題類型
        structure = chunk_doc.metadata.get('document_structure', {})
        if structure.get('content_type') == 'title':
            title = text[:100]  # 標題限制100字符
        
        # 如果文本較長，生成摘要（簡化版）
        if len(text) > 300:
            sentences = text.split('。')
            if len(sentences) > 2:
                summary = '。'.join(sentences[:2]) + '。'  # 取前兩句作為摘要
        
        return title, summary
    
    def _index_to_elasticsearch(self, index_doc: Dict[str, Any]):
        """索引到Elasticsearch"""
        try:
            # 生成文檔ID
            import hashlib
            content_hash = hashlib.md5(index_doc["content"].encode()).hexdigest()
            doc_id = f"{content_hash}_{index_doc['indexing_strategy']['strategy_name']}"
            
            # 索引文檔
            response = self.es_client.index(
                index=self.index_name,
                id=doc_id,
                body=index_doc
            )
            
            if response.get('result') in ['created', 'updated']:
                logger.debug(f"✅ 文檔已索引: {doc_id}")
            else:
                logger.warning(f"⚠️ 文檔索引異常: {response}")
                
        except Exception as e:
            logger.error(f"❌ Elasticsearch索引失敗: {e}")
    
    def update_index_mapping(self):
        """更新索引映射"""
        try:
            from config.enhanced_elasticsearch_mapping import get_hybrid_search_mapping
            
            # 檢查索引是否存在
            if not self.es_client.indices.exists(index=self.index_name):
                logger.info(f"📋 創建新索引: {self.index_name}")
                mapping = get_hybrid_search_mapping()
                self.es_client.indices.create(index=self.index_name, body=mapping)
            else:
                logger.info(f"📋 索引已存在: {self.index_name}")
                # 可以在這裡添加映射更新邏輯
            
        except Exception as e:
            logger.error(f"❌ 更新索引映射失敗: {e}")
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """獲取索引統計信息"""
        try:
            # 獲取基本統計
            stats = self.es_client.indices.stats(index=self.index_name)
            
            # 獲取策略分布統計
            strategy_agg = {
                "aggs": {
                    "strategy_distribution": {
                        "terms": {
                            "field": "indexing_strategy.strategy_name.keyword",
                            "size": 10
                        }
                    },
                    "content_type_distribution": {
                        "terms": {
                            "field": "metadata.document_structure.content_type.keyword",
                            "size": 10
                        }
                    }
                },
                "size": 0
            }
            
            agg_result = self.es_client.search(index=self.index_name, body=strategy_agg)
            
            return {
                "total_documents": stats['indices'][self.index_name]['total']['docs']['count'],
                "index_size": stats['indices'][self.index_name]['total']['store']['size_in_bytes'],
                "strategy_distribution": agg_result['aggregations']['strategy_distribution']['buckets'],
                "content_type_distribution": agg_result['aggregations']['content_type_distribution']['buckets']
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取索引統計失敗: {e}")
            return {}
    
    def optimize_index(self):
        """優化索引"""
        try:
            logger.info(f"🔧 開始優化索引: {self.index_name}")
            
            # 強制合併段
            self.es_client.indices.forcemerge(
                index=self.index_name,
                max_num_segments=1
            )
            
            # 刷新索引
            self.es_client.indices.refresh(index=self.index_name)
            
            logger.info(f"✅ 索引優化完成: {self.index_name}")
            
        except Exception as e:
            logger.error(f"❌ 索引優化失敗: {e}")