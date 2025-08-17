#!/usr/bin/env python3
"""
簡化的 Elasticsearch RAG 測試，顯示完整錯誤信息
"""

import sys
import os
sys.path.append('/app')

# Suppress streamlit warnings
os.environ['STREAMLIT_DISABLE_WARNINGS'] = 'true'

from custom_elasticsearch_store import CustomElasticsearchStore
from elasticsearch import Elasticsearch
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import TextNode
from datetime import datetime

def test_simple_indexing():
    """測試簡單的文檔索引"""
    print("🔧 Step 1: Setting up Elasticsearch client...")
    
    try:
        es = Elasticsearch(['http://elasticsearch:9200'], request_timeout=30)
        if not es.ping():
            print("❌ Elasticsearch ping failed")
            return False
        print("✅ Elasticsearch client ready")
    except Exception as e:
        print(f"❌ ES client error: {e}")
        return False
    
    print("🔧 Step 2: Setting up embedding model...")
    
    try:
        embed_model = HuggingFaceEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
        Settings.embed_model = embed_model
        print("✅ Embedding model ready")
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return False
    
    print("🔧 Step 3: Creating custom vector store...")
    
    try:
        vector_store = CustomElasticsearchStore(
            es_client=es,
            index_name='test_simple_es',
            text_field='content',
            vector_field='embedding'
        )
        print("✅ Custom vector store ready")
    except Exception as e:
        print(f"❌ Vector store error: {e}")
        return False
    
    print("🔧 Step 4: Creating storage context...")
    
    try:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print("✅ Storage context ready")
    except Exception as e:
        print(f"❌ Storage context error: {e}")
        return False
    
    print("🔧 Step 5: Creating test documents...")
    
    try:
        documents = [
            Document(
                text="This is a test document about machine learning.",
                metadata={"source": "test1", "timestamp": datetime.now().isoformat()}
            ),
            Document(
                text="This document discusses artificial intelligence and deep learning.",
                metadata={"source": "test2", "timestamp": datetime.now().isoformat()}
            )
        ]
        print(f"✅ Created {len(documents)} test documents")
    except Exception as e:
        print(f"❌ Document creation error: {e}")
        return False
    
    print("🔧 Step 6: Creating VectorStoreIndex...")
    
    try:
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model,
            show_progress=True
        )
        print("✅ VectorStoreIndex created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ VectorStoreIndex creation error: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
        # Try alternative approach
        print("🔧 Trying alternative approach...")
        try:
            # Create empty index first
            index = VectorStoreIndex(
                nodes=[],
                storage_context=storage_context,
                embed_model=embed_model
            )
            
            # Add documents one by one
            for i, doc in enumerate(documents):
                print(f"Adding document {i+1}...")
                index.insert(doc)
                
            print("✅ Alternative approach succeeded!")
            return True
            
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🧪 Starting simplified Elasticsearch RAG test")
    print("=" * 60)
    
    success = test_simple_indexing()
    
    print("=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        
        # Check final document count
        try:
            es = Elasticsearch(['http://elasticsearch:9200'], request_timeout=30)
            count_response = es.count(index='test_simple_es')
            print(f"📊 Final document count: {count_response['count']}")
        except Exception as e:
            print(f"❌ Count check failed: {e}")
    else:
        print("💥 Test failed!")
        
    sys.exit(0 if success else 1)