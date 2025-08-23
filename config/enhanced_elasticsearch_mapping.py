"""
Enhanced Elasticsearch Mapping Configuration
優化的Elasticsearch索引映射配置，支援多階段RAG優化
"""

def get_enhanced_mapping(vector_dimension=512):
    """
    獲取增強的Elasticsearch映射配置
    
    Args:
        vector_dimension: 向量維度，預設512
    
    Returns:
        dict: Elasticsearch mapping配置
    """
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "enhanced_chinese_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "cjk_width",
                            "cjk_bigram",
                            "synonym_filter"
                        ]
                    },
                    "ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "ngram_filter"
                        ]
                    },
                    "keyword_analyzer": {
                        "type": "custom",
                        "tokenizer": "keyword",
                        "filter": ["lowercase"]
                    }
                },
                "filter": {
                    "ngram_filter": {
                        "type": "ngram",
                        "min_gram": 2,
                        "max_gram": 4
                    },
                    "synonym_filter": {
                        "type": "synonym",
                        "synonyms": [
                            "機器學習,ML,machine learning",
                            "人工智能,AI,artificial intelligence",
                            "深度學習,DL,deep learning"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                # 主要內容字段 - 支援多種分析方式
                "content": {
                    "type": "text",
                    "analyzer": "enhanced_chinese_analyzer",
                    "search_analyzer": "enhanced_chinese_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 1024
                        },
                        "ngram": {
                            "type": "text",
                            "analyzer": "ngram_analyzer"
                        }
                    }
                },
                
                # 標題字段
                "title": {
                    "type": "text",
                    "analyzer": "enhanced_chinese_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                
                # 摘要字段
                "summary": {
                    "type": "text",
                    "analyzer": "enhanced_chinese_analyzer"
                },
                
                # 512維向量字段
                "embedding": {
                    "type": "dense_vector",
                    "dims": vector_dimension,
                    "index": True,
                    "similarity": "cosine",
                    "index_options": {
                        "type": "hnsw",
                        "m": 32,
                        "ef_construction": 200
                    }
                },
                
                # 多種embedding支援
                "embeddings": {
                    "properties": {
                        "general": {
                            "type": "dense_vector",
                            "dims": vector_dimension,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "domain": {
                            "type": "dense_vector", 
                            "dims": vector_dimension,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "sentence": {
                            "type": "dense_vector",
                            "dims": vector_dimension,
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                },
                
                # 結構化元數據
                "metadata": {
                    "properties": {
                        # 基本文件信息
                        "source": {"type": "keyword"},
                        "file_path": {"type": "keyword"},
                        "file_type": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "page": {"type": "integer"},
                        "total_pages": {"type": "long"},
                        "chunk_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        
                        # 文檔結構信息
                        "document_structure": {
                            "properties": {
                                "chapter": {"type": "keyword"},
                                "section": {"type": "keyword"},
                                "subsection": {"type": "keyword"},
                                "paragraph_index": {"type": "integer"},
                                "content_type": {"type": "keyword"},  # title, content, summary, list, table
                                "semantic_level": {"type": "integer"},  # 1=標題, 2=段落, 3=句子
                                "hierarchy_path": {"type": "keyword"}  # 如: "章節1/子章節1/段落1"
                            }
                        },
                        
                        # 切割策略信息
                        "chunking_strategy": {
                            "properties": {
                                "strategy_type": {"type": "keyword"},  # short, medium, long
                                "chunk_size": {"type": "integer"},
                                "chunk_overlap": {"type": "integer"},
                                "chunk_index": {"type": "integer"},
                                "total_chunks": {"type": "integer"},
                                "parent_chunk_id": {"type": "keyword"}
                            }
                        },
                        
                        # 語義信息
                        "semantic_info": {
                            "properties": {
                                "keywords": {"type": "keyword"},
                                "entities": {"type": "keyword"},
                                "topics": {"type": "keyword"},
                                "sentiment": {"type": "keyword"},
                                "language": {"type": "keyword"},
                                "confidence_score": {"type": "float"}
                            }
                        },
                        
                        # 處理信息
                        "processing_info": {
                            "properties": {
                                "processed_at": {"type": "date"},
                                "processor_version": {"type": "keyword"},
                                "ocr_confidence": {"type": "float"},
                                "extraction_method": {"type": "keyword"}
                            }
                        }
                    }
                },
                
                # BM25評分支援
                "bm25_content": {
                    "type": "text",
                    "analyzer": "standard",
                    "similarity": "BM25"
                }
            }
        }
    }

def get_hybrid_search_mapping(vector_dimension=512):
    """
    獲取支援混合搜索的映射配置
    """
    base_mapping = get_enhanced_mapping(vector_dimension)
    
    # 添加混合搜索特定字段
    base_mapping["mappings"]["properties"].update({
        "search_vectors": {
            "properties": {
                "query_vector": {
                    "type": "dense_vector",
                    "dims": vector_dimension,
                    "similarity": "cosine"
                },
                "context_vector": {
                    "type": "dense_vector", 
                    "dims": vector_dimension,
                    "similarity": "cosine"
                }
            }
        },
        
        "search_metadata": {
            "properties": {
                "relevance_score": {"type": "float"},
                "keyword_match_score": {"type": "float"},
                "semantic_match_score": {"type": "float"},
                "structural_match_score": {"type": "float"},
                "combined_score": {"type": "float"}
            }
        }
    })
    
    return base_mapping

def create_index_template(index_name="rag_intelligent_assistant", vector_dimension=512):
    """
    創建索引模板
    """
    return {
        "index_patterns": [f"{index_name}*"],
        "template": get_enhanced_mapping(vector_dimension),
        "priority": 500,
        "version": 2,
        "_meta": {
            "description": "Enhanced RAG system index template with Phase 1-3 optimizations",
            "created_by": "RAG_optimization_system",
            "version": "2.0.0"
        }
    }