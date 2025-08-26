import os
from datetime import datetime
from typing import List, Dict, Optional
from config.config import CONVERSATION_MEMORY_STEPS, MAX_CONTEXT_LENGTH, ENABLE_CONVERSATION_MEMORY

class ConversationMemory:
    def __init__(self, max_steps: Optional[int] = None):
        self.max_steps = max_steps or CONVERSATION_MEMORY_STEPS
        self.max_context_length = MAX_CONTEXT_LENGTH
        self.enabled = ENABLE_CONVERSATION_MEMORY
        self.memory: List[Dict] = []
        
    def is_enabled(self) -> bool:
        """檢查記憶功能是否啟用"""
        return self.enabled
    
    def add_exchange(self, question: str, answer: str) -> None:
        """添加一輪問答到記憶中"""
        if not self.is_enabled():
            return
        
        exchange = {
            "question": question.strip(),
            "answer": answer.strip(),
            "timestamp": datetime.now().isoformat(),
            "id": len(self.memory) + 1
        }
        
        self.memory.append(exchange)
        
        # 保持記憶步數限制
        if len(self.memory) > self.max_steps:
            self.memory.pop(0)
            # 重新編號
            for i, mem in enumerate(self.memory):
                mem['id'] = i + 1
    
    def get_context_prompt(self) -> str:
        """生成上下文提示"""
        if not self.is_enabled() or not self.memory:
            return ""
        
        context_parts = ["=== 對話歷史 ==="]
        total_length = 0
        
        # 從最近的對話開始，逐步添加直到達到長度限制
        for exchange in reversed(self.memory):
            question_part = f"使用者問題 {exchange['id']}: {exchange['question']}"
            answer_part = f"助理回答 {exchange['id']}: {exchange['answer'][:200]}{'...' if len(exchange['answer']) > 200 else ''}"
            
            exchange_text = f"{question_part}\n{answer_part}\n"
            
            if total_length + len(exchange_text) > self.max_context_length:
                break
            
            context_parts.insert(-1, exchange_text)  # 插入到最後一個元素之前
            total_length += len(exchange_text)
        
        context_parts.append("=== 當前問題 ===")
        
        return "\n".join(context_parts)
    
    def get_memory_for_display(self) -> List[Dict]:
        """取得用於顯示的記憶內容"""
        if not self.is_enabled():
            return []
        
        # 返回記憶的副本，避免外部修改
        return [mem.copy() for mem in self.memory]
    
    def clear_memory(self) -> None:
        """清除所有記憶"""
        self.memory.clear()
    
    def remove_last_exchange(self) -> bool:
        """移除最後一輪對話"""
        if self.memory:
            self.memory.pop()
            # 重新編號
            for i, mem in enumerate(self.memory):
                mem['id'] = i + 1
            return True
        return False
    
    def get_memory_count(self) -> int:
        """取得當前記憶數量"""
        return len(self.memory)
    
    def get_memory_stats(self) -> Dict:
        """取得記憶統計資訊"""
        if not self.is_enabled():
            return {
                'enabled': False,
                'current_count': 0,
                'max_steps': self.max_steps,
                'total_characters': 0,
                'oldest_timestamp': None,
                'newest_timestamp': None
            }
        
        total_chars = sum(len(mem['question']) + len(mem['answer']) for mem in self.memory)
        
        timestamps = [mem['timestamp'] for mem in self.memory]
        oldest = min(timestamps) if timestamps else None
        newest = max(timestamps) if timestamps else None
        
        return {
            'enabled': True,
            'current_count': len(self.memory),
            'max_steps': self.max_steps,
            'total_characters': total_chars,
            'oldest_timestamp': oldest,
            'newest_timestamp': newest
        }
    
    def update_max_steps(self, new_max_steps: int) -> None:
        """更新最大記憶步數"""
        if new_max_steps < 1:
            return
        
        self.max_steps = new_max_steps
        
        # 如果當前記憶超過新的限制，移除最舊的記憶
        while len(self.memory) > self.max_steps:
            self.memory.pop(0)
        
        # 重新編號
        for i, mem in enumerate(self.memory):
            mem['id'] = i + 1
    
    def search_memory(self, keyword: str) -> List[Dict]:
        """在記憶中搜尋關鍵詞"""
        if not self.is_enabled() or not keyword.strip():
            return []
        
        keyword = keyword.lower().strip()
        results = []
        
        for mem in self.memory:
            if (keyword in mem['question'].lower() or 
                keyword in mem['answer'].lower()):
                results.append(mem.copy())
        
        return results
    
    def export_memory(self) -> str:
        """匯出記憶內容為文字格式"""
        if not self.is_enabled() or not self.memory:
            return "無記憶內容可匯出"
        
        export_lines = [
            f"對話記憶匯出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"記憶步數: {len(self.memory)}/{self.max_steps}",
            "=" * 50,
            ""
        ]
        
        for mem in self.memory:
            export_lines.extend([
                f"對話 {mem['id']} - {mem['timestamp']}",
                f"問題: {mem['question']}",
                f"回答: {mem['answer']}",
                "-" * 30,
                ""
            ])
        
        return "\n".join(export_lines)
