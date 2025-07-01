"""
RAG Chatbot Main Application
A Flask-based web application for RAG (Retrieval-Augmented Generation) chatbot
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import shutil
import re
import requests

from backend.llm_provider import LLMProvider
from backend.document_loader import DocumentLoader
from backend.vector_store import VectorStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
vector_store = VectorStore()
document_loader = DocumentLoader()
llm_provider = LLMProvider()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test upload page"""
    return render_template('test_upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process for RAG"""
    try:
        logger.info("Upload request received")
        
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        logger.info(f"File received: {file.filename}")
        
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Nếu file trùng tên, xóa chunk cũ trong vector store trước khi thêm mới
        vector_store.delete_document(filename)

        file.save(filepath)
        logger.info(f"File saved to: {filepath}")
        
        # Process document and add to vector store
        logger.info("Processing document...")
        documents = document_loader.load_document(filepath)
        logger.info(f"Document loader returned: {len(documents) if documents else 0} documents")
        
        if documents:
            logger.info(f"Loaded {len(documents)} document chunks")
            logger.info("Adding documents to vector store...")
            success = vector_store.add_documents(documents)
            logger.info(f"Add documents result: {success}")
            
            if success:
                logger.info("Documents added to vector store successfully")
                return jsonify({
                    'success': True,
                    'message': f'File {filename} uploaded and processed successfully ({len(documents)} chunks)',
                    'filename': filename
                })
            else:
                logger.error("Failed to add documents to vector store")
                return jsonify({'error': 'Failed to add documents to vector store'}), 500
        else:
            logger.error("No documents loaded from file")
            return jsonify({'error': 'Failed to process document - no content extracted'}), 500
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with RAG"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        model_type = data.get('model_type', 'gemini')  # 'gemini' or 'local'
        model_name = data.get('model_name', 'gemini-pro')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Retrieve relevant documents (embedding search)
        relevant_docs = vector_store.search(user_message, k=10)
        
        # Tìm thêm các chunk chứa từ khóa đặc biệt trong câu hỏi
        keywords = re.findall(r'\b\w{3,}\b', user_message)
        keywords += ['208HV', 'NMLD']  # Thêm các từ khóa cố định nếu muốn
        keywords = list(set([k.lower() for k in keywords]))
        all_docs = vector_store.get_document_list()
        extra_docs = []
        for doc in all_docs:
            content = doc.get('content_preview', '').lower()
            if any(kw in content for kw in keywords):
                extra_docs.append(doc)
        # Chuyển extra_docs sang dạng Document nếu cần
        # Loại bỏ trùng lặp theo id
        doc_ids = set(d.metadata.get('id') for d in relevant_docs)
        for d in extra_docs:
            if d['id'] not in doc_ids:
                from langchain.schema import Document
                relevant_docs.append(Document(page_content=d['content_preview'], metadata=d['metadata']))
        # Lấy 10 lượt hội thoại gần nhất
        chat_history = session.get('chat_history', [])[-10:]
        # Generate response using selected LLM, truyền history
        if model_type == 'local':
            response = llm_provider.generate_local_response(user_message, relevant_docs, chat_history=chat_history, model_name=data.get('model_name'))
        else:
            response = llm_provider.generate_gemini_response(user_message, relevant_docs, model_name=model_name, chat_history=chat_history)
        # Store chat history in session
        if 'chat_history' not in session:
            session['chat_history'] = []
        session['chat_history'].append({
            'user': user_message,
            'assistant': response,
            'timestamp': datetime.now().isoformat()
        })
        return jsonify({
            'response': response,
            'sources': sorted(list({doc.metadata.get('source', 'Unknown') for doc in relevant_docs}))
        })
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/documents', methods=['GET'])
def get_documents():
    """Get list of unique uploaded documents"""
    try:
        documents = vector_store.get_document_list()
        # Lấy danh sách tên file duy nhất
        unique_sources = list({doc['source'] for doc in documents})
        return jsonify({'documents': [{'source': s} for s in unique_sources]})
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/vector-debug', methods=['GET'])
def vector_debug():
    """Trả về toàn bộ dữ liệu vector store để debug (chỉ dùng cho phát triển)"""
    try:
        documents = vector_store.get_document_list()
        return jsonify({'documents': documents})
    except Exception as e:
        logger.error(f"Vector debug error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    try:
        history = session.get('chat_history', [])
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Get history error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear chat history"""
    try:
        session.pop('chat_history', None)
        return jsonify({'success': True, 'message': 'Chat history cleared'})
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/gemini-models', methods=['GET'])
def gemini_models():
    """Get available Gemini models from Google API"""
    try:
        import google.generativeai as genai
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google API key not configured'}), 400
        genai.configure(api_key=api_key)
        models = genai.list_models()
        # Lọc các model text (không phải vision)
        model_list = [m.name for m in models if 'vision' not in m.name]
        return jsonify({'models': model_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-vectorstore', methods=['POST'])
def clear_vectorstore():
    """Clear all documents from vector store"""
    try:
        logger.info("Starting vectorstore clear process...")
        # Sử dụng method clear_all() thay vì xóa thư mục trực tiếp
        success = vector_store.clear_all()
        logger.info(f"Clear all result: {success}")
        
        # Khởi tạo lại ChromaDB sau khi clear
        logger.info("Reinitializing vectorstore...")
        vector_store.reinitialize()
        logger.info("Vectorstore reinitialized successfully")
        
        if success:
            return jsonify({'success': True, 'message': 'Vectorstore cleared!'})
        else:
            return jsonify({'error': 'Failed to clear vectorstore'}), 500
    except Exception as e:
        logger.error(f"Clear vectorstore error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for managing vectorstore and documents"""
    return render_template('admin.html')

@app.route('/delete-document', methods=['POST'])
def delete_document():
    """Delete all chunks of a document by source filename"""
    try:
        data = request.get_json()
        source = data.get('source')
        if not source:
            return jsonify({'error': 'No source provided'}), 400
        success = vector_store.delete_document(source)
        if success:
            return jsonify({'success': True, 'message': f'Deleted all chunks for {source}'})
        else:
            return jsonify({'error': f'No chunks found for {source}'}), 404
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

@app.route('/api-list')
def api_list():
    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        methods = list(rule.methods - {'HEAD', 'OPTIONS'})
        doc = app.view_functions[rule.endpoint].__doc__
        for m in methods:
            endpoints.append({
                'method': m,
                'path': str(rule),
                'doc': doc.strip() if doc else ''
            })
    endpoints = sorted(endpoints, key=lambda x: (x['path'], x['method']))
    return jsonify({'endpoints': endpoints})

@app.route('/local-models', methods=['GET'])
def local_models():
    """Get available local LLM models from LM Studio API"""
    try:
        lmstudio_url = os.getenv('LOCAL_LLM_ENDPOINT', 'http://127.0.0.1:1234/v1/chat/completions')
        # Lấy host từ endpoint
        if '/v1/chat/completions' in lmstudio_url:
            base_url = lmstudio_url.split('/v1/chat/completions')[0]
        else:
            base_url = 'http://127.0.0.1:1234'
        models_url = base_url + '/v1/models'
        resp = requests.get(models_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # LM Studio trả về {'data': [ {id: model_name, ...}, ... ]}
            model_list = [m['id'] for m in data.get('data', [])]
            return jsonify({'models': model_list})
        else:
            return jsonify({'error': f'LM Studio returned status {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vectorstore-status', methods=['GET'])
def vectorstore_status():
    """Get vectorstore and model status for UI"""
    try:
        # DB status
        stats = vector_store.get_stats()
        db_connected = not vector_store.is_empty() or stats.get('total_documents', 0) >= 0
        # Model status
        gemini_ok = llm_provider.gemini_api_key is not None
        # Test local LLM connection (optional, fast check)
        local_ok = False
        try:
            import requests
            lmstudio_url = os.getenv('LOCAL_LLM_ENDPOINT', 'http://127.0.0.1:1234/v1/chat/completions')
            resp = requests.get(lmstudio_url.replace('/v1/chat/completions','/v1/models'), timeout=2)
            local_ok = resp.status_code == 200
        except Exception:
            local_ok = False
        return jsonify({
            'db_connected': db_connected,
            'total_documents': stats.get('unique_sources', 0),
            'total_chunks': stats.get('total_documents', 0),
            'unique_sources': stats.get('unique_sources', 0),
            'model_status': {
                'gemini': gemini_ok,
                'local': local_ok
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logoBSR.png')
def serve_logo():
    return send_from_directory('.', 'logoBSR.png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 