"""
LLM Provider Module
Handles different LLM providers including Google Gemini and Local models via LM Studio
"""

import os
import requests
import google.generativeai as genai
from typing import List, Dict, Any
from langchain.schema import Document
from dotenv import load_dotenv
import re

load_dotenv()

class LLMProvider:
    """Manages different LLM providers for the RAG chatbot"""
    
    def __init__(self):
        """Initialize LLM providers"""
        # Google Gemini configuration
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Local LLM configuration (LM Studio)
        self.local_endpoint = os.getenv('LOCAL_LLM_ENDPOINT', 'http://localhost:1234/v1/chat/completions')
        self.local_model = os.getenv('LOCAL_MODEL_NAME', 'phi-2')
    
    def _format_html(self, text: str) -> str:
        """Format markdown-like text to HTML for chatbot output"""
        # Đổi **Tiêu đề:** thành <b>Tiêu đề:</b>
        text = re.sub(r'\*\*(.+?):\*\*', r'<b>\1:</b>', text)
        # Đổi các dòng bắt đầu bằng - hoặc * thành <ul><li>...</li></ul>
        lines = text.split('\n')
        in_list = False
        html_lines = []
        for line in lines:
            if re.match(r'^\s*[-\*]\s+', line):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append('<li>' + re.sub(r'^\s*[-\*]\s+', '', line) + '</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Đổi số thứ tự 1. 2. ... thành <ol>
                m = re.match(r'^\s*\d+\.\s+', line)
                if m:
                    if not html_lines or not html_lines[-1].endswith('<ol>'):
                        html_lines.append('<ol>')
                    html_lines.append('<li>' + re.sub(r'^\s*\d+\.\s+', '', line) + '</li>')
                else:
                    if html_lines and html_lines[-1] == '<ol>':
                        html_lines.append('</ol>')
                    html_lines.append(line)
        if in_list:
            html_lines.append('</ul>')
        if html_lines and html_lines[-1] == '<ol>':
            html_lines.append('</ol>')
        # Đổi \n thành <br> cho các đoạn còn lại
        html = '\n'.join(html_lines)
        html = html.replace('\n', '<br>')
        return html

    def generate_gemini_response(self, user_message: str, relevant_docs: List[Document], model_name: str = 'gemini-pro', chat_history=None) -> str:
        """Generate response using Google Gemini, with selectable model_name, default to Vietnamese"""
        try:
            if not self.gemini_api_key:
                return "Error: Google API key not configured"
            genai.configure(api_key=self.gemini_api_key)
            gemini_model = genai.GenerativeModel(model_name)
            context = self._prepare_context(relevant_docs)
            # Format history: chỉ truyền câu hỏi của user
            history_str = ""
            if chat_history:
                for turn in chat_history:
                    history_str += f"Người dùng: {turn['user']}\n---\n"
            prompt = f"""Bạn là một trợ lý AI hữu ích, trả lời bằng tiếng Việt.\n\nDưới đây là lịch sử hội thoại gần nhất giữa bạn và người dùng (nếu có), tiếp theo là ngữ cảnh tài liệu.\n\nLưu ý: KHÔNG lặp lại nội dung trả lời trước, chỉ trả lời cho câu hỏi hiện tại. Nếu thông tin nằm rải rác ở nhiều đoạn, hãy tổng hợp lại. Nếu có thể, hãy trình bày dạng danh sách rõ ràng, dễ đọc.\n\nLịch sử hội thoại (chỉ dùng để tham khảo, KHÔNG lặp lại nội dung trả lời trước):\n{history_str}\n==============================\nNgữ cảnh tài liệu:\n{context}\n==============================\nCâu hỏi của người dùng: {user_message}\n\nTrả lời:"""
            print("\n===== PROMPT GỬI ĐẾN GEMINI =====\n" + prompt + "\n===============================\n")
            response = gemini_model.generate_content(prompt)
            return self._format_html(response.text)
        except Exception as e:
            return f"Error generating Gemini response: {str(e)}"
    
    def generate_local_response(self, user_message: str, relevant_docs: List[Document], chat_history=None) -> str:
        """Generate response using local LLM via LM Studio, default to Vietnamese"""
        try:
            context = self._prepare_context(relevant_docs)
            # Format history: chỉ truyền câu hỏi của user
            history_str = ""
            if chat_history:
                for turn in chat_history:
                    history_str += f"Người dùng: {turn['user']}\n---\n"
            prompt = f"""Bạn là một trợ lý AI hữu ích, trả lời bằng tiếng Việt.\n\nDưới đây là lịch sử hội thoại gần nhất giữa bạn và người dùng (nếu có), tiếp theo là ngữ cảnh tài liệu.\n\nLưu ý: KHÔNG lặp lại nội dung trả lời trước, chỉ trả lời cho câu hỏi hiện tại. Nếu thông tin nằm rải rác ở nhiều đoạn, hãy tổng hợp lại. Nếu có thể, hãy trình bày dạng danh sách rõ ràng, dễ đọc.\n\nLịch sử hội thoại (chỉ dùng để tham khảo, KHÔNG lặp lại nội dung trả lời trước):\n{history_str}\n==============================\nNgữ cảnh tài liệu:\n{context}\n==============================\nCâu hỏi của người dùng: {user_message}\n\nTrả lời:"""
            print("\n===== PROMPT GỬI ĐẾN LOCAL LLM =====\n" + prompt + "\n===============================\n")
            payload = {
                "model": self.local_model,
                "messages": [
                    {"role": "system", "content": "Bạn là một trợ lý AI hữu ích, trả lời bằng tiếng Việt."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            response = requests.post(
                self.local_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                return self._format_html(result['choices'][0]['message']['content'])
            else:
                return f"Error: Local LLM server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to local LLM server. Please ensure LM Studio is running."
        except Exception as e:
            return f"Error generating local response: {str(e)}"
    
    def _prepare_context(self, relevant_docs: List[Document]) -> str:
        """Prepare context string from relevant documents"""
        if not relevant_docs:
            return "No relevant documents found."
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content
            if len(content) > 2000:
                content = content[:2000] + "..."
            context_parts.append(f"Document {i} (Source: {source}):\n{content}\n")
        return "\n".join(context_parts)
    
    def test_connection(self, model_type: str = 'gemini') -> Dict[str, Any]:
        """Test connection to LLM providers"""
        try:
            if model_type == 'gemini':
                if not self.gemini_api_key:
                    return {'success': False, 'error': 'Google API key not configured'}
                
                response = self.gemini_model.generate_content("Hello, this is a test.")
                return {'success': True, 'response': response.text}
            
            elif model_type == 'local':
                payload = {
                    "model": self.local_model,
                    "messages": [
                        {"role": "user", "content": "Hello, this is a test."}
                    ],
                    "max_tokens": 50
                }
                
                response = requests.post(
                    self.local_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {'success': True, 'response': result['choices'][0]['message']['content']}
                else:
                    return {'success': False, 'error': f'Server returned status {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)} 