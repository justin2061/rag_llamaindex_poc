"""
Enhanced RAG System V2.0
整合所有Phase 1-3優化的增強RAG系統
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import traceback
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.postprocessor import SimilarityPostprocessor
from elasticsearch import Elasticsearch

# 導入新的優化組件
from src.processors.enhanced_document_processor import EnhancedDocumentProcessor
from src.indexers.hierarchical_indexer import HierarchicalIndexer
from src.retrievers.hybrid_retriever import HybridRetriever, HybridSearchConfig
from src.embeddings.multi_embedding_manager import MultiEmbeddingManager
from src.rerankers.contextual_reranker import ContextualReranker, RerankingContext
from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRAGSystemV2(ElasticsearchRAGSystem):
    """
    增強RAG系統V2.0
    整合Phase 1-3的所有優化功能
    """
    
    def __init__(self, elasticsearch_config: Optional[Dict] = None):
        """初始化增強RAG系統V2.0"""
        
        logger.info("🚀 初始化 Enhanced RAG System V2.0")
        
        # 首先設置正確的embedding模型
        from src.utils.jina_embedding_setup import ensure_embedding_initialized
        if not ensure_embedding_initialized():
            logger.error("❌ Embedding模型初始化失敗")
            raise RuntimeError("Embedding模型初始化失敗")
        
        # 然後初始化基礎系統
        super().__init__(elasticsearch_config)
        
        # 初始化索引屬性
        self.vector_store_index = None
        
        # 載入優化配置
        from config.config import (
            ENABLE_HIERARCHICAL_CHUNKING,
            ENABLE_HYBRID_SEARCH,
            ENABLE_MULTI_EMBEDDING,
            ENABLE_CONTEXTUAL_RERANKING,
            HYBRID_SEARCH_WEIGHTS
        )
        
        # 初始化優化組件
        self.enable_hierarchical_chunking = ENABLE_HIERARCHICAL_CHUNKING
        self.enable_hybrid_search = ENABLE_HYBRID_SEARCH
        self.enable_multi_embedding = ENABLE_MULTI_EMBEDDING
        self.enable_contextual_reranking = ENABLE_CONTEXTUAL_RERANKING
        
        # 初始化新組件
        self._initialize_v2_components()
        
        # 確保有基本的索引設置
        try:
            # 嘗試從父類獲取已初始化的索引
            if hasattr(self, 'index') and self.index:
                self.vector_store_index = self.index
                logger.info("✅ 使用父類已初始化的索引")
            elif hasattr(self, 'vector_store') and self.vector_store and not self.vector_store_index:
                from llama_index.core import VectorStoreIndex
                self.vector_store_index = VectorStoreIndex.from_vector_store(self.vector_store)
                logger.info("✅ Vector store index 從 vector_store 初始化完成")
            elif hasattr(self, 'elasticsearch_store') and self.elasticsearch_store and not self.vector_store_index:
                # 使用 elasticsearch_store 來初始化索引
                from llama_index.core import VectorStoreIndex
                self.vector_store_index = VectorStoreIndex.from_vector_store(self.elasticsearch_store)
                logger.info("✅ Vector store index 從 elasticsearch_store 初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ Vector store index 初始化失敗: {e}")
        
        logger.info("✅ Enhanced RAG System V2.0 初始化完成")
        self._log_optimization_status()
    
    def _initialize_v2_components(self):
        """初始化V2.0新組件 - 簡化版本，只保留必要組件"""
        
        try:
            logger.info("🔧 使用簡化模式初始化 - 只保留 Jina embedding")
            
            # 只有在啟用功能時才初始化對應組件
            if self.enable_hierarchical_chunking:
                # 1. 增強文檔處理器
                self.enhanced_processor = EnhancedDocumentProcessor()
                logger.info("📄 Enhanced Document Processor 已載入")
                
                # 3. 階層式索引器
                if self.elasticsearch_client:
                    self.hierarchical_indexer = HierarchicalIndexer(
                        elasticsearch_client=self.elasticsearch_client,
                        index_name=self.index_name,
                        processor=self.enhanced_processor
                    )
                    logger.info("🏗️ Hierarchical Indexer 已載入")
            else:
                logger.info("⏭️ 跳過階層切割組件")
            
            if self.enable_multi_embedding:
                # 2. 多Embedding管理器
                self.multi_embedding_manager = MultiEmbeddingManager(
                    enable_multi_embedding=self.enable_multi_embedding
                )
                logger.info("🎯 Multi-Embedding Manager 已載入")
            else:
                logger.info("⏭️ 跳過多Embedding管理器")
            
            # 4. 混合檢索器
            if self.enable_hybrid_search and self.elasticsearch_client:
                from config.config import HYBRID_SEARCH_WEIGHTS
                hybrid_config = HybridSearchConfig(
                    vector_weight=HYBRID_SEARCH_WEIGHTS.get("vector", 0.6),
                    keyword_weight=HYBRID_SEARCH_WEIGHTS.get("keyword", 0.3),
                    semantic_weight=HYBRID_SEARCH_WEIGHTS.get("semantic", 0.1)
                )
                
                # 使用基本的embedding模型而不是多embedding管理器
                embedding_model = getattr(self, 'multi_embedding_manager', None)
                if embedding_model:
                    embedding_model = embedding_model.models.get("general")
                
                self.hybrid_retriever = HybridRetriever(
                    elasticsearch_client=self.elasticsearch_client,
                    index_name=self.index_name,
                    config=hybrid_config,
                    embedding_model=embedding_model
                )
                logger.info("🔍 Hybrid Retriever 已載入")
            else:
                logger.info("⏭️ 跳過混合檢索器")
            
            # 5. 上下文重排序器
            if self.enable_contextual_reranking:
                self.contextual_reranker = ContextualReranker(
                    enable_contextual_reranking=self.enable_contextual_reranking
                )
                logger.info("🎯 Contextual Reranker 已載入")
            else:
                logger.info("⏭️ 跳過上下文重排序器")
            
            logger.info("✅ 簡化模式初始化完成")
            
        except Exception as e:
            logger.error(f"❌ V2.0組件初始化失敗: {e}")
            logger.info("🔄 嘗試fallback到基礎模式")
            # 不拋出異常，允許系統以基礎模式運行
    
    def _log_optimization_status(self):
        """記錄優化狀態"""
        logger.info("📊 優化功能狀態:")
        logger.info(f"   - 階層切割: {'✅' if self.enable_hierarchical_chunking else '❌'}")
        logger.info(f"   - 混合檢索: {'✅' if self.enable_hybrid_search else '❌'}")
        logger.info(f"   - 多Embedding: {'✅' if self.enable_multi_embedding else '❌'}")
        logger.info(f"   - 上下文重排序: {'✅' if self.enable_contextual_reranking else '❌'}")
    
    def process_uploaded_file_v2(self, uploaded_file, file_manager) -> Dict[str, Any]:
        """
        V2.0文件處理流程
        使用增強的文檔處理和階層索引
        """
        
        # 獲取文件名和大小（兼容FastAPI和Streamlit）
        filename = getattr(uploaded_file, 'filename', getattr(uploaded_file, 'name', 'unknown'))
        file_size = getattr(uploaded_file, 'size', 0)
        
        logger.info(f"🔄 V2.0文件處理開始: {filename}")
        
        processing_stats = {
            "filename": filename,
            "file_size": file_size,
            "start_time": datetime.now(),
            "chunks_created": 0,
            "optimization_used": [],
            "processing_stages": {}
        }
        
        try:
            # Stage 1: 基礎文件處理
            stage_start = datetime.now()
            file_path = file_manager.save_uploaded_file(uploaded_file)
            if not file_path:
                raise ValueError("文件保存失敗")
            
            processing_stats["processing_stages"]["file_save"] = {
                "duration": (datetime.now() - stage_start).total_seconds(),
                "status": "success"
            }
            
            # Stage 2: 文檔載入和預處理
            stage_start = datetime.now()
            documents = self._load_documents_from_file(file_path)
            
            processing_stats["processing_stages"]["document_load"] = {
                "duration": (datetime.now() - stage_start).total_seconds(),
                "documents_loaded": len(documents),
                "status": "success"
            }
            
            # Stage 3: 增強文檔處理
            if self.enable_hierarchical_chunking:
                stage_start = datetime.now()
                enhanced_documents = []
                
                for doc in documents:
                    processed_docs = self.enhanced_processor.process_document(doc)
                    enhanced_documents.extend(processed_docs)
                
                documents = enhanced_documents
                processing_stats["optimization_used"].append("hierarchical_chunking")
                processing_stats["processing_stages"]["enhanced_processing"] = {
                    "duration": (datetime.now() - stage_start).total_seconds(),
                    "chunks_created": len(documents),
                    "status": "success"
                }
                logger.info(f"📄 階層處理完成，產生 {len(documents)} 個chunks")
            
            # Stage 4: 階層式索引
            if hasattr(self, 'hierarchical_indexer'):
                stage_start = datetime.now()
                indexing_stats = self.hierarchical_indexer.create_hierarchical_index(documents)
                
                processing_stats["optimization_used"].append("hierarchical_indexing")
                processing_stats["processing_stages"]["hierarchical_indexing"] = {
                    "duration": (datetime.now() - stage_start).total_seconds(),
                    "indexed_chunks": indexing_stats["indexed_chunks"],
                    "indexing_strategies": indexing_stats["indexing_strategies"],
                    "status": "success"
                }
                processing_stats["chunks_created"] = indexing_stats["indexed_chunks"]
                logger.info(f"🏗️ 階層索引完成，索引 {indexing_stats['indexed_chunks']} 個chunks")
            else:
                # 備用：傳統索引方式
                stage_start = datetime.now()
                index = self.create_index(documents)
                if index:
                    self.vector_store_index = index
                
                processing_stats["processing_stages"]["traditional_indexing"] = {
                    "duration": (datetime.now() - stage_start).total_seconds(),
                    "status": "success"
                }
                processing_stats["chunks_created"] = len(documents)
            
            # 更新系統狀態
            processing_stats["end_time"] = datetime.now()
            processing_stats["total_duration"] = (
                processing_stats["end_time"] - processing_stats["start_time"]
            ).total_seconds()
            processing_stats["status"] = "success"
            
            # 記錄處理統計
            self._store_processing_stats(processing_stats)
            
            logger.info(f"✅ V2.0文件處理完成: {filename}")
            logger.info(f"   - 總耗時: {processing_stats['total_duration']:.2f}秒")
            logger.info(f"   - 產生chunks: {processing_stats['chunks_created']}")
            logger.info(f"   - 使用優化: {', '.join(processing_stats['optimization_used'])}")
            
            return processing_stats
            
        except Exception as e:
            logger.error(f"❌ V2.0文件處理失敗: {e}")
            processing_stats["status"] = "error"
            processing_stats["error"] = str(e)
            processing_stats["end_time"] = datetime.now()
            return processing_stats
    
    def query_with_sources_v2(
        self,
        question: str,
        conversation_history: List[Dict[str, str]] = None,
        user_preferences: Dict[str, Any] = None,
        max_sources: int = 3
    ) -> Dict[str, Any]:
        """
        V2.0智能查詢，整合所有優化功能
        """
        
        logger.info(f"🔍 V2.0智能查詢開始: {question}")
        
        query_stats = {
            "question": question,
            "start_time": datetime.now(),
            "optimization_used": [],
            "query_stages": {},
            "sources_found": 0
        }
        
        try:
            # Stage 1: 查詢預處理和意圖分析
            stage_start = datetime.now()
            
            # 分析搜索意圖
            from src.rerankers.contextual_reranker import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            search_intent = analyzer.analyze_search_intent(question)
            
            query_stats["query_stages"]["preprocessing"] = {
                "duration": (datetime.now() - stage_start).total_seconds(),
                "search_intent": search_intent,
                "status": "success"
            }
            
            # Stage 2: 智能檢索
            stage_start = datetime.now()
            
            if self.enable_hybrid_search and hasattr(self, 'hybrid_retriever'):
                # 使用混合檢索
                from llama_index.core.schema import QueryBundle
                query_bundle = QueryBundle(query_str=question)
                retrieved_nodes = self.hybrid_retriever.retrieve(query_bundle)
                query_stats["optimization_used"].append("hybrid_search")
                logger.info(f"🔍 混合檢索找到 {len(retrieved_nodes)} 個結果")
            else:
                # 備用：傳統檢索
                if self.vector_store_index:
                    retriever = self.vector_store_index.as_retriever(similarity_top_k=max_sources*2)
                    retrieved_nodes = retriever.retrieve(question)
                else:
                    raise ValueError("沒有可用的檢索器")
            
            query_stats["query_stages"]["retrieval"] = {
                "duration": (datetime.now() - stage_start).total_seconds(),
                "nodes_retrieved": len(retrieved_nodes),
                "status": "success"
            }
            
            # Stage 3: 上下文重排序
            stage_start = datetime.now()
            
            if self.enable_contextual_reranking and retrieved_nodes:
                # 構建重排序上下文
                reranking_context = RerankingContext(
                    query=question,
                    conversation_history=conversation_history or [],
                    user_preferences=user_preferences or {},
                    domain_context="general",
                    search_intent=search_intent
                )
                
                # 執行重排序
                reranked_nodes = self.contextual_reranker.rerank_results(
                    retrieved_nodes, reranking_context
                )
                retrieved_nodes = reranked_nodes
                query_stats["optimization_used"].append("contextual_reranking")
                logger.info(f"🎯 重排序完成，最終 {len(retrieved_nodes)} 個結果")
            
            query_stats["query_stages"]["reranking"] = {
                "duration": (datetime.now() - stage_start).total_seconds(),
                "final_nodes": len(retrieved_nodes),
                "status": "success"
            }
            
            # Stage 4: 答案生成
            stage_start = datetime.now()
            
            # 限制最終結果數量
            final_nodes = retrieved_nodes[:max_sources]
            
            # 使用LLM生成答案
            context_str = self._build_context_from_nodes(final_nodes)
            answer = self._generate_answer_with_context(question, context_str, conversation_history)
            
            # 構建來源信息
            sources = []
            for i, node in enumerate(final_nodes):
                source_info = {
                    "source": node.node.metadata.get("source", f"文檔_{i+1}"),
                    "file_path": node.node.metadata.get("file_path", ""),
                    "score": float(node.score),
                    "content": node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text,
                    "page": node.node.metadata.get("page", ""),
                    "type": "enhanced_document"
                }
                sources.append(source_info)
            
            query_stats["query_stages"]["answer_generation"] = {
                "duration": (datetime.now() - stage_start).total_seconds(),
                "answer_length": len(answer),
                "sources_used": len(sources),
                "status": "success"
            }
            
            # 完成統計
            query_stats["end_time"] = datetime.now()
            query_stats["total_duration"] = (
                query_stats["end_time"] - query_stats["start_time"]
            ).total_seconds()
            query_stats["sources_found"] = len(sources)
            query_stats["status"] = "success"
            
            # 構建響應
            response = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "query": question,
                    "total_sources": len(sources),
                    "response_time_ms": int(query_stats["total_duration"] * 1000),
                    "model": "Enhanced RAG V2.0",
                    "backend": "Elasticsearch + Multi-Optimization",
                    "optimization_used": query_stats["optimization_used"],
                    "performance": {
                        "total_stages": len(query_stats["query_stages"]),
                        "total_time": query_stats["total_duration"],
                        "stages": [
                            {
                                "stage": stage_name,
                                "duration": stage_data["duration"],
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            }
                            for stage_name, stage_data in query_stats["query_stages"].items()
                        ]
                    }
                }
            }
            
            logger.info(f"✅ V2.0智能查詢完成")
            logger.info(f"   - 總耗時: {query_stats['total_duration']:.3f}秒")
            logger.info(f"   - 來源數量: {len(sources)}")
            logger.info(f"   - 使用優化: {', '.join(query_stats['optimization_used'])}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ V2.0智能查詢失敗: {e}")
            traceback.print_exc()
            
            # 返回錯誤響應
            return {
                "answer": "抱歉，查詢處理過程中發生錯誤。請稍後再試。",
                "sources": [],
                "metadata": {
                    "error": str(e),
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _build_context_from_nodes(self, nodes) -> str:
        """從節點構建上下文"""
        context_parts = []
        for i, node in enumerate(nodes, 1):
            source = node.node.metadata.get("source", f"文檔{i}")
            content = node.node.text
            context_parts.append(f"[來源 {i}: {source}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer_with_context(
        self, 
        question: str, 
        context: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """基於上下文生成答案"""
        
        # 構建對話歷史
        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # 最近3輪對話
            history_parts = []
            for msg in recent_history:
                role = "用戶" if msg.get("role") == "user" else "助理"
                content = msg.get("content", "")
                history_parts.append(f"{role}: {content}")
            
            if history_parts:
                history_context = "對話歷史:\n" + "\n".join(history_parts) + "\n\n"
        
        # 構建完整提示
        prompt = f"""{history_context}請基於以下提供的資料回答問題，如果資料中沒有相關信息，請明確說明。

問題: {question}

參考資料:
{context}

請提供準確、詳細的答案:"""
        
        try:
            # 使用LLM生成答案
            llm = Settings.llm
            response = llm.complete(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"❌ 答案生成失敗: {e}")
            return "抱歉，無法基於提供的資料生成答案。請嘗試重新表達您的問題。"
    
    def _store_processing_stats(self, stats: Dict[str, Any]):
        """儲存處理統計"""
        try:
            # 將統計信息儲存到系統狀態中
            if not hasattr(self, 'processing_history'):
                self.processing_history = []
            
            self.processing_history.append(stats)
            
            # 只保留最近20次處理記錄
            if len(self.processing_history) > 20:
                self.processing_history = self.processing_history[-20:]
                
        except Exception as e:
            logger.warning(f"⚠️ 統計儲存失敗: {e}")
    
    def get_system_performance_stats(self) -> Dict[str, Any]:
        """獲取系統性能統計"""
        
        stats = {
            "system_version": "Enhanced RAG System V2.0",
            "optimization_status": {
                "hierarchical_chunking": self.enable_hierarchical_chunking,
                "hybrid_search": self.enable_hybrid_search,
                "multi_embedding": self.enable_multi_embedding,
                "contextual_reranking": self.enable_contextual_reranking
            },
            "processing_history": getattr(self, 'processing_history', []),
            "component_status": {}
        }
        
        # 檢查各組件狀態
        if hasattr(self, 'multi_embedding_manager'):
            stats["component_status"]["multi_embedding_manager"] = {
                "available_models": list(self.multi_embedding_manager.models.keys()),
                "model_info": self.multi_embedding_manager.get_model_info()
            }
        
        if hasattr(self, 'hierarchical_indexer'):
            stats["component_status"]["hierarchical_indexer"] = {
                "index_statistics": self.hierarchical_indexer.get_index_statistics()
            }
        
        return stats
    
    def optimize_system_performance(self):
        """優化系統性能"""
        logger.info("🔧 開始系統性能優化")
        
        try:
            # 優化Elasticsearch索引
            if hasattr(self, 'hierarchical_indexer'):
                self.hierarchical_indexer.optimize_index()
            
            # 清理處理歷史（保留有用統計）
            if hasattr(self, 'processing_history') and len(self.processing_history) > 50:
                self.processing_history = self.processing_history[-20:]
            
            logger.info("✅ 系統性能優化完成")
            
        except Exception as e:
            logger.error(f"❌ 系統性能優化失敗: {e}")
    
    def benchmark_v2_system(self, test_queries: List[str]) -> Dict[str, Any]:
        """V2.0系統基準測試"""
        
        logger.info(f"🧪 開始V2.0系統基準測試，查詢數量: {len(test_queries)}")
        
        benchmark_results = {
            "test_start_time": datetime.now(),
            "total_queries": len(test_queries),
            "query_results": [],
            "performance_summary": {}
        }
        
        for i, query in enumerate(test_queries):
            logger.info(f"測試查詢 {i+1}/{len(test_queries)}: {query}")
            
            query_start = datetime.now()
            result = self.query_with_sources_v2(query)
            query_duration = (datetime.now() - query_start).total_seconds()
            
            query_result = {
                "query_index": i,
                "query": query,
                "duration": query_duration,
                "sources_found": len(result.get("sources", [])),
                "optimization_used": result.get("metadata", {}).get("optimization_used", []),
                "success": result.get("metadata", {}).get("status") != "error"
            }
            
            benchmark_results["query_results"].append(query_result)
        
        # 計算性能摘要
        successful_queries = [r for r in benchmark_results["query_results"] if r["success"]]
        
        if successful_queries:
            durations = [r["duration"] for r in successful_queries]
            sources_counts = [r["sources_found"] for r in successful_queries]
            
            benchmark_results["performance_summary"] = {
                "success_rate": len(successful_queries) / len(test_queries),
                "average_query_time": sum(durations) / len(durations),
                "min_query_time": min(durations),
                "max_query_time": max(durations),
                "average_sources_found": sum(sources_counts) / len(sources_counts),
                "optimization_usage": {}
            }
            
            # 統計優化功能使用情況
            all_optimizations = []
            for result in successful_queries:
                all_optimizations.extend(result["optimization_used"])
            
            from collections import Counter
            opt_counter = Counter(all_optimizations)
            total_uses = sum(opt_counter.values())
            
            if total_uses > 0:
                benchmark_results["performance_summary"]["optimization_usage"] = {
                    opt: count/total_uses for opt, count in opt_counter.items()
                }
        
        benchmark_results["test_end_time"] = datetime.now()
        benchmark_results["total_test_duration"] = (
            benchmark_results["test_end_time"] - benchmark_results["test_start_time"]
        ).total_seconds()
        
        logger.info("✅ V2.0系統基準測試完成")
        logger.info(f"   - 成功率: {benchmark_results['performance_summary'].get('success_rate', 0)*100:.1f}%")
        logger.info(f"   - 平均查詢時間: {benchmark_results['performance_summary'].get('average_query_time', 0):.3f}秒")
        
        return benchmark_results
    
    def _load_documents_from_file(self, file_path: str) -> List:
        """
        從文件載入文檔
        支援多種文件格式：PDF、TXT、DOCX、MD等
        """
        from llama_index.core import Document, SimpleDirectoryReader
        import os
        
        logger.info(f"📁 載入文檔: {file_path}")
        
        try:
            # 檢查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 獲取文件擴展名
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.txt':
                # 處理純文本文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                document = Document(
                    text=content,
                    metadata={
                        "file_path": file_path,
                        "file_name": os.path.basename(file_path),
                        "file_type": "text",
                        "source": file_path
                    }
                )
                documents = [document]
                
            elif file_ext == '.md':
                # 處理Markdown文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                document = Document(
                    text=content,
                    metadata={
                        "file_path": file_path,
                        "file_name": os.path.basename(file_path),
                        "file_type": "markdown",
                        "source": file_path
                    }
                )
                documents = [document]
                
            else:
                # 使用SimpleDirectoryReader處理其他格式
                reader = SimpleDirectoryReader(
                    input_files=[file_path],
                    required_exts=[file_ext]
                )
                raw_documents = reader.load_data()
                
                # 對於PDF等多頁面文檔，合併頁面內容
                if file_ext == '.pdf' and len(raw_documents) > 1:
                    logger.info(f"📄 PDF包含 {len(raw_documents)} 頁，進行頁面合併...")
                    
                    # 合併所有頁面的文本
                    combined_text = ""
                    page_contents = []
                    
                    for i, doc in enumerate(raw_documents):
                        page_num = i + 1
                        page_text = doc.text.strip()
                        
                        # 跳過空頁面
                        if not page_text:
                            continue
                            
                        # 添加頁面分隔符
                        page_contents.append(f"\n--- 第{page_num}頁 ---\n{page_text}")
                    
                    combined_text = "\n".join(page_contents)
                    
                    # 創建合併後的文檔
                    combined_doc = Document(
                        text=combined_text,
                        metadata={
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path),
                            "file_type": "pdf",
                            "source": file_path,
                            "total_pages": len(raw_documents),
                            "content_length": len(combined_text),
                            "processing_method": "page_merged"
                        }
                    )
                    
                    documents = [combined_doc]
                    logger.info(f"✅ PDF頁面合併完成，總文本長度: {len(combined_text)} 字符")
                    
                else:
                    # 對於單頁文檔或非PDF，保持原樣
                    documents = raw_documents
                    
                    # 更新元數據
                    for doc in documents:
                        if hasattr(doc, 'metadata'):
                            doc.metadata.update({
                                "file_path": file_path,
                                "file_name": os.path.basename(file_path),
                                "source": file_path
                            })
            
            logger.info(f"✅ 成功載入文檔: {len(documents)} 個文檔")
            return documents
            
        except Exception as e:
            logger.error(f"❌ 文檔載入失敗: {e}")
            # 創建一個錯誤文檔
            error_doc = Document(
                text=f"文檔載入失敗: {str(e)}",
                metadata={
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "file_type": "error",
                    "error": str(e),
                    "source": file_path
                }
            )
            return [error_doc]
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """
        獲取已索引文件的列表和狀態信息
        Returns:
            List[Dict]: 包含文件信息的字典列表
        """
        try:
            if not self.vector_store_index:
                logger.warning("⚠️ 向量存儲未初始化")
                return []
            
            # 嘗試從 Elasticsearch 獲取文件信息
            vector_store = getattr(self.vector_store_index, 'vector_store', None)
            if vector_store and hasattr(vector_store, '_client') and hasattr(vector_store, '_index_name'):
                try:
                    # 使用聚合查詢獲取唯一文件信息
                    query = {
                        "size": 0,
                        "aggs": {
                            "unique_files": {
                                "terms": {
                                    "field": "metadata.file_name",
                                    "size": 1000
                                },
                                "aggs": {
                                    "file_info": {
                                        "top_hits": {
                                            "size": 1,
                                            "_source": ["metadata"],
                                            "sort": [{"_timestamp": {"order": "desc"}}]
                                        }
                                    },
                                    "chunk_count": {
                                        "value_count": {
                                            "field": "_id"
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    response = vector_store._client.search(
                        index=vector_store._index_name,
                        body=query
                    )
                    
                    files = []
                    for bucket in response['aggregations']['unique_files']['buckets']:
                        file_name = bucket['key']
                        chunk_count = bucket['chunk_count']['value']
                        
                        # 獲取文件元數據
                        hits = bucket['file_info']['hits']['hits']
                        if hits:
                            metadata = hits[0]['_source']['metadata']
                            
                            # 計算文件大小（估算）
                            file_size_mb = metadata.get('content_length', 0) / (1024 * 1024) if metadata.get('content_length') else 0.0
                            
                            files.append({
                                'id': metadata.get('file_path', file_name),
                                'name': file_name,
                                'size_mb': round(file_size_mb, 2),
                                'type': metadata.get('file_type', 'unknown'),
                                'upload_time': metadata.get('upload_time', ''),
                                'node_count': chunk_count,
                                'status': 'active',
                                'source': metadata.get('source', ''),
                                'processing_method': metadata.get('processing_method', 'standard')
                            })
                    
                    logger.info(f"📂 獲取到 {len(files)} 個已索引文件")
                    return files
                    
                except Exception as es_error:
                    logger.warning(f"⚠️ Elasticsearch查詢失敗: {es_error}")
                    # 降級到基本實現
                    pass
            
            # 基本實現：嘗試從索引中獲取基本信息
            try:
                # 使用VectorStoreIndex的查詢功能
                if self.vector_store_index:
                    # 通過查詢獲取文檔
                    retriever = self.vector_store_index.as_retriever(similarity_top_k=100)
                    docs = retriever.retrieve("test query for listing files")
                    
                    # 按文件名分組
                    files_dict = {}
                    for doc in docs:
                        if hasattr(doc, 'metadata'):
                            metadata = doc.metadata
                            file_name = metadata.get('file_name', 'unknown')
                            if file_name not in files_dict:
                                files_dict[file_name] = {
                                    'id': metadata.get('file_path', file_name),
                                    'name': file_name,
                                    'size_mb': 0.0,
                                    'type': metadata.get('file_type', 'unknown'),
                                    'upload_time': metadata.get('upload_time', ''),
                                    'node_count': 0,
                                    'status': 'active'
                                }
                            
                            # 累計統計
                            files_dict[file_name]['node_count'] += 1
                            # 嘗試從文本長度估算大小
                            if hasattr(doc, 'text'):
                                text_size_mb = len(doc.text.encode('utf-8')) / (1024 * 1024)
                                files_dict[file_name]['size_mb'] += text_size_mb
                    
                    # 轉換為列表
                    files = list(files_dict.values())
                    for file_info in files:
                        file_info['size_mb'] = round(file_info['size_mb'], 2)
                    
                    return files
            
            except Exception as fallback_error:
                logger.warning(f"⚠️ 基本查詢也失敗: {fallback_error}")
            
            return []
            
        except Exception as e:
            logger.error(f"❌ 獲取已索引文件列表失敗: {e}")
            return []
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """
        獲取文檔統計信息
        Returns:
            Dict: 包含統計信息的字典
        """
        try:
            files = self.get_indexed_files()
            total_files = len(files)
            total_chunks = sum(file_info.get('node_count', 0) for file_info in files)
            total_size_mb = sum(file_info.get('size_mb', 0.0) for file_info in files)
            
            return {
                'total_files': total_files,
                'total_documents': total_chunks,
                'total_size_mb': round(total_size_mb, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取文檔統計信息失敗: {e}")
            return {
                'total_files': 0,
                'total_documents': 0,
                'total_size_mb': 0.0
            }