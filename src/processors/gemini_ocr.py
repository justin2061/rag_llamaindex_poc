import os
import base64
from typing import Optional, Dict, Any
import streamlit as st
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    st.warning("Google Generative AI library not installed. OCR功能將無法使用。")

from config.config import GEMINI_API_KEY, ENABLE_OCR

class GeminiOCRProcessor:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.enabled = ENABLE_OCR and GEMINI_AVAILABLE and self.api_key
        
        if self.enabled:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.available = True
            except Exception as e:
                st.error(f"Gemini API 初始化失敗: {str(e)}")
                self.available = False
        else:
            self.available = False
            if not self.api_key:
                st.warning("未設定 GEMINI_API_KEY，OCR功能將無法使用")
    
    def is_available(self) -> bool:
        """檢查OCR服務是否可用"""
        return self.available
    
    def extract_text_from_image(self, image_data: bytes, image_type: str) -> Dict[str, Any]:
        """從圖片提取文字"""
        if not self.is_available():
            return {
                'success': False,
                'error': 'OCR服務不可用',
                'text': ''
            }
        
        try:
            # 準備圖片數據
            if image_type.lower() in ['jpg', 'jpeg']:
                mime_type = 'image/jpeg'
            elif image_type.lower() == 'png':
                mime_type = 'image/png'
            elif image_type.lower() == 'webp':
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'  # 預設為jpeg
            
            # 準備提示詞
            prompt = """
請仔細識別這張圖片中的所有文字內容。要求：

1. **準確性**：確保文字識別的準確性，特別是中文字符
2. **格式保持**：盡可能保持原有的格式和結構
3. **表格處理**：如果是表格，請以Markdown表格格式輸出
4. **列表處理**：如果是列表，請保持列表格式（使用 - 或 1. 2. 等）
5. **標題層次**：識別標題並使用適當的Markdown格式（# ## ###）
6. **特殊符號**：保留重要的特殊符號和標點
7. **多語言**：準確識別中文、英文、數字等混合內容

請直接輸出識別的文字內容，不需要額外說明。
"""
            
            # 調用Gemini API
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": image_data
                }
            ])
            
            if response.text:
                return {
                    'success': True,
                    'error': None,
                    'text': response.text.strip(),
                    'confidence': 'high'  # Gemini不提供confidence分數，設為高
                }
            else:
                return {
                    'success': False,
                    'error': '無法從圖片中提取文字',
                    'text': ''
                }
                
        except Exception as e:
            error_msg = f"OCR處理失敗: {str(e)}"
            st.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'text': ''
            }
    
    def batch_process_images(self, image_data_list: list) -> list:
        """批次處理多張圖片"""
        if not self.is_available():
            return [{
                'success': False,
                'error': 'OCR服務不可用',
                'text': ''
            } for _ in image_data_list]
        
        results = []
        total_images = len(image_data_list)
        
        for i, (image_data, image_type, filename) in enumerate(image_data_list):
            try:
                # 更新進度
                progress = (i + 1) / total_images
                
                # 處理單張圖片
                result = self.extract_text_from_image(image_data, image_type)
                result['filename'] = filename
                result['processed_at'] = i + 1
                result['total'] = total_images
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'success': False,
                    'error': f"處理 {filename} 時發生錯誤: {str(e)}",
                    'text': '',
                    'filename': filename,
                    'processed_at': i + 1,
                    'total': total_images
                })
        
        return results
    
    def get_supported_formats(self) -> list:
        """取得支援的圖片格式"""
        return ['png', 'jpg', 'jpeg', 'webp', 'bmp']
    
    def validate_image_format(self, image_type: str) -> bool:
        """驗證圖片格式是否支援"""
        return image_type.lower() in self.get_supported_formats()
