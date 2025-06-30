"""
Configuration file for RAG Chatbot
Centralized configuration management
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'data/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
    
    # Vector Store Configuration
    VECTOR_STORE_PATH = os.getenv('VECTOR_STORE_PATH', 'data/vectorstore')
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # LLM Configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    LOCAL_LLM_ENDPOINT = os.getenv('LOCAL_LLM_ENDPOINT', 'http://localhost:1234/v1/chat/completions')
    LOCAL_MODEL_NAME = os.getenv('LOCAL_MODEL_NAME', 'phi-2')
    
    # RAG Configuration
    MAX_RETRIEVAL_DOCS = 3
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000
    
    # UI Configuration
    THEME_DEFAULT = 'light'
    CHAT_HISTORY_LIMIT = 50
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        # Check required directories
        required_dirs = [cls.UPLOAD_FOLDER, cls.VECTOR_STORE_PATH]
        for directory in required_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {directory}: {str(e)}")
        
        # Check API keys (optional but recommended)
        if not cls.GOOGLE_API_KEY:
            print("⚠️  Warning: GOOGLE_API_KEY not set. Gemini functionality will be limited.")
        
        return errors
    
    @classmethod
    def get_llm_config(cls, model_type: str):
        """Get LLM-specific configuration"""
        if model_type == 'gemini':
            return {
                'api_key': cls.GOOGLE_API_KEY,
                'model': 'gemini-pro',
                'temperature': cls.TEMPERATURE,
                'max_tokens': cls.MAX_TOKENS
            }
        elif model_type == 'local':
            return {
                'endpoint': cls.LOCAL_LLM_ENDPOINT,
                'model': cls.LOCAL_MODEL_NAME,
                'temperature': cls.TEMPERATURE,
                'max_tokens': cls.MAX_TOKENS
            }
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    @classmethod
    def get_vector_store_config(cls):
        """Get vector store configuration"""
        return {
            'persist_directory': cls.VECTOR_STORE_PATH,
            'embedding_model': cls.EMBEDDING_MODEL,
            'chunk_size': cls.CHUNK_SIZE,
            'chunk_overlap': cls.CHUNK_OVERLAP
        }
    
    @classmethod
    def get_document_loader_config(cls):
        """Get document loader configuration"""
        return {
            'chunk_size': cls.CHUNK_SIZE,
            'chunk_overlap': cls.CHUNK_OVERLAP,
            'allowed_extensions': cls.ALLOWED_EXTENSIONS
        }

# Development configuration
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

# Production configuration
class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Stricter settings for production
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB
    CHAT_HISTORY_LIMIT = 20

# Testing configuration
class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    VECTOR_STORE_PATH = 'data/test_vectorstore'
    UPLOAD_FOLDER = 'data/test_uploads'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 