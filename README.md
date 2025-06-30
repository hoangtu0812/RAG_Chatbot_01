# RAG Chatbot

A modern web-based chatbot using Retrieval-Augmented Generation (RAG) architecture with support for multiple LLM providers.

## Features

- 🤖 **RAG Architecture**: Retrieval-Augmented Generation for context-aware responses
- 📄 **Multi-format Support**: Upload and process PDF, DOCX, and TXT files
- 🧠 **Multiple LLM Providers**: 
  - Google Gemini (Cloud)
  - Local models via LM Studio (phi-2, Gemma, etc.)
- 🎨 **Modern UI**: Clean, responsive interface with dark mode support
- 📊 **Vector Storage**: Chroma vector store for efficient document retrieval
- 🔍 **Document Management**: Upload, view, and manage your knowledge base

## Architecture

```
RAG_ChatBot_01/
├── main.py                 # Flask application entry point
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── backend/
│   ├── __init__.py
│   ├── llm_provider.py    # LLM provider management
│   ├── document_loader.py # Document processing
│   └── vector_store.py    # Vector store operations
├── templates/
│   └── index.html         # Web interface
└── data/
    ├── uploads/           # Uploaded files
    └── vectorstore/       # Chroma vector store
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RAG_ChatBot_01
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Google Gemini API (Optional)
GOOGLE_API_KEY=your-google-api-key-here

# Local LLM Configuration (Optional)
LOCAL_LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
LOCAL_MODEL_NAME=phi-2

# Vector Store Configuration
VECTOR_STORE_PATH=data/vectorstore

# Upload Configuration
MAX_FILE_SIZE=16777216
UPLOAD_FOLDER=data/uploads
```

### LLM Setup

#### Google Gemini
1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file

#### Local LLM (LM Studio)
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load a model (e.g., phi-2, Gemma-2b)
3. Start the local server (usually runs on `http://localhost:1234`)
4. Configure the endpoint in your `.env` file

## Usage

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **Upload documents**
   - Click the upload area in the sidebar
   - Select PDF, DOCX, or TXT files
   - Documents will be processed and added to the vector store

4. **Start chatting**
   - Choose your preferred LLM (Gemini or Local)
   - Ask questions about your uploaded documents
   - The chatbot will retrieve relevant context and generate responses

## API Endpoints

- `GET /` - Main application page
- `POST /upload` - Upload and process documents
- `POST /chat` - Send chat messages
- `GET /documents` - Get list of uploaded documents
- `GET /history` - Get chat history
- `POST /clear-history` - Clear chat history

## Features in Detail

### Document Processing
- **PDF**: Uses PyMuPDF for text extraction
- **DOCX**: Uses python-docx for document parsing
- **TXT**: Direct text file processing
- **Chunking**: Documents are split into manageable chunks for better retrieval

### Vector Store
- **Chroma**: Local vector database for document embeddings
- **Embeddings**: Uses sentence-transformers for text embeddings
- **Persistence**: Vector store is saved locally and persists between sessions

### LLM Integration
- **Gemini**: Cloud-based model with high performance
- **Local**: Self-hosted models for privacy and offline use
- **Context Injection**: Relevant document chunks are included in prompts

### User Interface
- **Responsive Design**: Works on desktop and mobile
- **Dark Mode**: Toggle between light and dark themes
- **Real-time Chat**: Instant message exchange
- **File Management**: Visual document upload and management

## Development

### Project Structure
- `main.py`: Flask application with routes
- `backend/llm_provider.py`: LLM provider abstraction
- `backend/document_loader.py`: Document processing utilities
- `backend/vector_store.py`: Vector store operations
- `templates/index.html`: Frontend interface

### Adding New Features
1. **New LLM Provider**: Extend `LLMProvider` class
2. **New Document Type**: Add parser to `DocumentLoader`
3. **New Vector Store**: Implement vector store interface
4. **UI Enhancements**: Modify `templates/index.html`

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Chroma Connection Issues**
   - Ensure write permissions to `data/vectorstore/`
   - Delete the directory to reset the vector store

3. **Local LLM Not Responding**
   - Check if LM Studio is running
   - Verify the endpoint URL in `.env`
   - Ensure the model is loaded in LM Studio

4. **Gemini API Errors**
   - Verify your API key is correct
   - Check API quota and billing status

### Logs
The application logs errors and operations to the console. Check the terminal output for debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LangChain](https://langchain.com/) for the RAG framework
- [Chroma](https://www.trychroma.com/) for vector storage
- [LM Studio](https://lmstudio.ai/) for local LLM hosting
- [Google Gemini](https://ai.google.dev/) for cloud LLM access 