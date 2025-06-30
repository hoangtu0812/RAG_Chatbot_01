"""
Test script for RAG Chatbot
Tests various components and functionality
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.document_loader import DocumentLoader
from backend.vector_store import VectorStore
from backend.llm_provider import LLMProvider

def test_document_loader():
    """Test document loading functionality"""
    print("Testing Document Loader...")
    
    loader = DocumentLoader()
    
    # Test with sample text file
    sample_file = "data/sample/sample_document.txt"
    if os.path.exists(sample_file):
        documents = loader.load_document(sample_file)
        if documents:
            print(f"✅ Successfully loaded {len(documents)} chunks from {sample_file}")
            print(f"   First chunk preview: {documents[0].page_content[:100]}...")
        else:
            print(f"❌ Failed to load {sample_file}")
    else:
        print(f"⚠️  Sample file not found: {sample_file}")
    
    print()

def test_vector_store():
    """Test vector store functionality"""
    print("Testing Vector Store...")
    
    try:
        vector_store = VectorStore()
        
        # Test if vector store is working
        stats = vector_store.get_stats()
        print(f"✅ Vector store initialized successfully")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Unique sources: {stats.get('unique_sources', 0)}")
        
        # Test search functionality
        test_query = "What is RAG?"
        results = vector_store.search(test_query, k=2)
        print(f"✅ Search test completed, found {len(results)} results")
        
    except Exception as e:
        print(f"❌ Vector store test failed: {str(e)}")
    
    print()

def test_llm_provider():
    """Test LLM provider functionality"""
    print("Testing LLM Provider...")
    
    try:
        llm_provider = LLMProvider()
        
        # Test Gemini connection
        gemini_test = llm_provider.test_connection('gemini')
        if gemini_test['success']:
            print("✅ Gemini connection successful")
        else:
            print(f"⚠️  Gemini connection failed: {gemini_test.get('error', 'Unknown error')}")
        
        # Test Local LLM connection
        local_test = llm_provider.test_connection('local')
        if local_test['success']:
            print("✅ Local LLM connection successful")
        else:
            print(f"⚠️  Local LLM connection failed: {local_test.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ LLM provider test failed: {str(e)}")
    
    print()

def test_flask_app():
    """Test Flask application endpoints"""
    print("Testing Flask Application...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Test if server is running
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running")
        else:
            print(f"⚠️  Flask app returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask app is not running. Start it with: python main.py")
    except Exception as e:
        print(f"❌ Flask app test failed: {str(e)}")
    
    print()

def test_sample_data_upload():
    """Test uploading sample data"""
    print("Testing Sample Data Upload...")
    
    base_url = "http://localhost:5000"
    sample_files = [
        "data/sample/sample_document.txt",
        "data/sample/ai_technologies.txt"
    ]
    
    for file_path in sample_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(f"{base_url}/upload", files=files, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            print(f"✅ Successfully uploaded {file_path}")
                        else:
                            print(f"❌ Upload failed for {file_path}: {data.get('error')}")
                    else:
                        print(f"❌ Upload failed for {file_path}: HTTP {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Error uploading {file_path}: {str(e)}")
        else:
            print(f"⚠️  Sample file not found: {file_path}")
    
    print()

def test_chat_functionality():
    """Test chat functionality"""
    print("Testing Chat Functionality...")
    
    base_url = "http://localhost:5000"
    
    test_messages = [
        "What is RAG?",
        "How does machine learning work?",
        "What are the benefits of using RAG?"
    ]
    
    for message in test_messages:
        try:
            payload = {
                'message': message,
                'model_type': 'gemini'  # Test with Gemini first
            }
            
            response = requests.post(
                f"{base_url}/chat",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    print(f"✅ Chat test successful for: '{message[:30]}...'")
                    print(f"   Response preview: {data['response'][:100]}...")
                else:
                    print(f"❌ Chat test failed for: '{message[:30]}...' - No response")
            else:
                print(f"❌ Chat test failed for: '{message[:30]}...' - HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Chat test error for '{message[:30]}...': {str(e)}")
    
    print()

def main():
    """Run all tests"""
    print("🧪 RAG Chatbot Test Suite")
    print("=" * 50)
    
    # Test individual components
    test_document_loader()
    test_vector_store()
    test_llm_provider()
    
    # Test Flask application
    test_flask_app()
    
    # Test with sample data (only if Flask app is running)
    try:
        response = requests.get("http://localhost:5000/", timeout=2)
        if response.status_code == 200:
            test_sample_data_upload()
            test_chat_functionality()
    except:
        print("⚠️  Skipping Flask-dependent tests (app not running)")
    
    print("🏁 Test suite completed!")
    print("\nTo start the application:")
    print("1. Set up your .env file with API keys")
    print("2. Run: python main.py")
    print("3. Open: http://localhost:5000")

if __name__ == "__main__":
    main() 