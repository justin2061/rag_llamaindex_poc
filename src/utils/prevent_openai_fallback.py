#!/usr/bin/env python3
"""
防止 LlamaIndex 回退到 OpenAI（統一行為）
"""

import os

def prevent_openai_fallback():
    """防止 LlamaIndex 回退到 OpenAI"""
    # 設置假的 OpenAI API key，避免 LlamaIndex 進行驗證但不會真正使用
    os.environ['OPENAI_API_KEY'] = 'sk-fake-key-to-avoid-llamaindex-validation-error'
    # 清理其他可能的 OpenAI 配置，避免誤用
    for k in ['OPENAI_API_BASE', 'OPENAI_ORGANIZATION']:
        if k in os.environ:
            del os.environ[k]
    print("🛡️ 已防止 OpenAI 預設回退")

if __name__ == "__main__":
    prevent_openai_fallback()