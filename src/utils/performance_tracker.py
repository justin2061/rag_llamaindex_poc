#!/usr/bin/env python3
"""
RAG系統性能追蹤工具
記錄各個階段的執行時間和性能指標
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager
# 條件性導入 streamlit，API環境下使用 mock 實現
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    # Mock streamlit 接口以支持 API 環境
    class MockStreamlit:
        @staticmethod
        def info(message): pass
        @staticmethod  
        def markdown(message): pass
        @staticmethod
        def columns(count): return [MockColumn()] * count
        @staticmethod
        def metric(label, value): pass
        @staticmethod
        def text(message): pass
        @staticmethod
        def caption(message): pass
    
    class MockColumn:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def metric(self, label, value): pass
        def text(self, message): pass
    
    st = MockStreamlit()


@dataclass
class TimeMetric:
    """時間指標數據類"""
    stage_name: str
    start_time: float
    end_time: float
    duration: float
    timestamp: str
    additional_info: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)


class PerformanceTracker:
    """RAG性能追蹤器"""
    
    def __init__(self):
        self.metrics: List[TimeMetric] = []
        self.current_session_metrics: List[TimeMetric] = []
        self.stage_stack: List[Dict[str, Any]] = []
        
    @contextmanager
    def track_stage(self, stage_name: str, **kwargs):
        """上下文管理器：追蹤特定階段的執行時間
        
        Args:
            stage_name: 階段名稱
            **kwargs: 額外的追蹤信息
        """
        start_time = time.time()
        start_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 將階段推入堆疊
        stage_info = {
            'stage_name': stage_name,
            'start_time': start_time,
            'start_timestamp': start_timestamp,
            'additional_info': kwargs
        }
        self.stage_stack.append(stage_info)
        
        try:
            yield self
        finally:
            # 彈出階段並記錄結束時間
            if self.stage_stack:
                stage_info = self.stage_stack.pop()
                end_time = time.time()
                duration = end_time - stage_info['start_time']
                
                metric = TimeMetric(
                    stage_name=stage_info['stage_name'],
                    start_time=stage_info['start_time'],
                    end_time=end_time,
                    duration=duration,
                    timestamp=stage_info['start_timestamp'],
                    additional_info=stage_info['additional_info']
                )
                
                self.metrics.append(metric)
                self.current_session_metrics.append(metric)
    
    def record_manual_timing(self, stage_name: str, duration: float, **kwargs):
        """手動記錄時間指標
        
        Args:
            stage_name: 階段名稱
            duration: 持續時間（秒）
            **kwargs: 額外信息
        """
        current_time = time.time()
        metric = TimeMetric(
            stage_name=stage_name,
            start_time=current_time - duration,
            end_time=current_time,
            duration=duration,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            additional_info=kwargs
        )
        
        self.metrics.append(metric)
        self.current_session_metrics.append(metric)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """獲取當前會話的性能摘要"""
        if not self.current_session_metrics:
            return {"total_stages": 0, "total_time": 0, "stages": []}
        
        total_time = sum(metric.duration for metric in self.current_session_metrics)
        
        stages_summary = []
        for metric in self.current_session_metrics:
            stages_summary.append({
                "stage": metric.stage_name,
                "duration": round(metric.duration, 3),
                "percentage": round((metric.duration / total_time) * 100, 1) if total_time > 0 else 0,
                "timestamp": metric.timestamp,
                "info": metric.additional_info or {}
            })
        
        return {
            "total_stages": len(self.current_session_metrics),
            "total_time": round(total_time, 3),
            "average_stage_time": round(total_time / len(self.current_session_metrics), 3),
            "stages": stages_summary
        }
    
    def get_stage_statistics(self, stage_name: str) -> Dict[str, Any]:
        """獲取特定階段的統計信息"""
        stage_metrics = [m for m in self.metrics if m.stage_name == stage_name]
        
        if not stage_metrics:
            return {"count": 0, "total_time": 0, "average_time": 0, "min_time": 0, "max_time": 0}
        
        durations = [m.duration for m in stage_metrics]
        
        return {
            "count": len(stage_metrics),
            "total_time": round(sum(durations), 3),
            "average_time": round(sum(durations) / len(durations), 3),
            "min_time": round(min(durations), 3),
            "max_time": round(max(durations), 3),
            "latest_execution": stage_metrics[-1].timestamp
        }
    
    def clear_session_metrics(self):
        """清空當前會話指標"""
        self.current_session_metrics = []
    
    def export_metrics(self, format: str = 'json') -> str:
        """導出指標數據
        
        Args:
            format: 導出格式 ('json' 或 'csv')
        """
        if format == 'json':
            return json.dumps([metric.to_dict() for metric in self.metrics], indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if self.metrics:
                fieldnames = ['stage_name', 'duration', 'timestamp', 'start_time', 'end_time']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for metric in self.metrics:
                    row = {
                        'stage_name': metric.stage_name,
                        'duration': metric.duration,
                        'timestamp': metric.timestamp,
                        'start_time': metric.start_time,
                        'end_time': metric.end_time
                    }
                    writer.writerow(row)
            
            return output.getvalue()
    
    def format_duration(self, duration: float) -> str:
        """格式化持續時間顯示"""
        if duration < 1:
            return f"{duration*1000:.0f}ms"
        elif duration < 60:
            return f"{duration:.2f}s"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            return f"{minutes}m {seconds:.1f}s"
    
    def display_performance_summary(self):
        """在Streamlit中顯示性能摘要"""
        # 在非streamlit環境下跳過UI顯示
        if not HAS_STREAMLIT:
            return
            
        summary = self.get_session_summary()
        
        if summary["total_stages"] == 0:
            st.info("📊 暫無性能數據")
            return
        
        st.markdown("### ⏱️ 性能追蹤摘要")
        
        # 總體指標
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總執行時間", self.format_duration(summary["total_time"]))
        with col2:
            st.metric("執行階段數", summary["total_stages"])
        with col3:
            st.metric("平均階段時間", self.format_duration(summary["average_stage_time"]))
        
        # 階段詳情
        if summary["stages"]:
            st.markdown("#### 📋 各階段耗時詳情")
            
            for stage in summary["stages"]:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"🔧 {stage['stage']}")
                with col2:
                    st.text(f"{self.format_duration(stage['duration'])}")
                with col3:
                    st.text(f"{stage['percentage']}%")
                
                # 顯示額外信息
                if stage['info']:
                    info_text = ", ".join([f"{k}: {v}" for k, v in stage['info'].items()])
                    st.caption(f"   ℹ️ {info_text}")


# 全局追蹤器實例
_global_tracker = None

def get_performance_tracker() -> PerformanceTracker:
    """獲取全局性能追蹤器實例"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PerformanceTracker()
    return _global_tracker

def track_rag_stage(stage_name: str, **kwargs):
    """追蹤RAG階段的裝飾器/上下文管理器"""
    return get_performance_tracker().track_stage(stage_name, **kwargs)

def clear_performance_metrics():
    """清空性能指標"""
    tracker = get_performance_tracker()
    tracker.clear_session_metrics()

def get_rag_performance_summary() -> Dict[str, Any]:
    """獲取RAG性能摘要"""
    return get_performance_tracker().get_session_summary()


# 預定義的RAG階段常量
class RAGStages:
    """RAG處理階段常量"""
    FILE_UPLOAD = "文件上傳"
    DOCUMENT_PARSING = "文檔解析"
    TEXT_CHUNKING = "文本分塊"
    EMBEDDING_GENERATION = "嵌入向量生成"
    INDEX_CREATION = "索引創建"
    QUERY_PROCESSING = "查詢處理"
    SIMILARITY_SEARCH = "相似性搜索"
    CONTEXT_RETRIEVAL = "上下文檢索"
    LLM_INFERENCE = "LLM推理"
    RESPONSE_GENERATION = "回答生成"
    TOTAL_QUERY_TIME = "總查詢時間"
    TOTAL_INDEXING_TIME = "總索引時間"


if __name__ == "__main__":
    # 測試代碼
    tracker = PerformanceTracker()
    
    # 模擬一些階段
    with tracker.track_stage(RAGStages.DOCUMENT_PARSING, file_count=3):
        time.sleep(0.1)
    
    with tracker.track_stage(RAGStages.EMBEDDING_GENERATION, vector_count=100):
        time.sleep(0.2)
    
    with tracker.track_stage(RAGStages.INDEX_CREATION):
        time.sleep(0.05)
    
    # 輸出摘要
    summary = tracker.get_session_summary()
    print("性能摘要:", json.dumps(summary, indent=2, ensure_ascii=False))