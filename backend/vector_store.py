"""
Vector Store Module
Manages document embeddings and similarity search using Chroma
"""

import os
import chromadb
from typing import List, Dict, Any
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

class VectorStore:
    """Manages document embeddings and similarity search"""
    
    def __init__(self, persist_directory: str = "data/vectorstore"):
        """Initialize vector store with Chroma"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name="rag_documents"
        )
        
        # Keep track of added documents
        self.document_sources = set()
        self._load_existing_sources()
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the vector store"""
        try:
            if not documents:
                return False
            
            # Add documents to vector store
            self.vectorstore.add_documents(documents)
            
            # Update document sources tracking
            for doc in documents:
                source = doc.metadata.get('source', 'Unknown')
                self.document_sources.add(source)
            
            # Persist changes
            self.vectorstore.persist()
            
            print(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            print(f"Error adding documents to vector store: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 3) -> List[Document]:
        """Search for similar documents"""
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []
    
    def search_with_scores(self, query: str, k: int = 3) -> List[tuple]:
        """Search for similar documents with similarity scores"""
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"Error searching vector store with scores: {str(e)}")
            return []
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get list of all documents in the vector store"""
        try:
            # Get all documents from the collection
            collection = self.vectorstore._collection
            results = collection.get()
            documents = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    documents.append({
                        'id': results['ids'][i],
                        'content': doc,
                        'content_preview': doc[:200] + "..." if len(doc) > 200 else doc,
                        'metadata': metadata,
                        'source': metadata.get('source', 'Unknown')
                    })
            return documents
        except Exception as e:
            print(f"Error getting document list: {str(e)}")
            return []
    
    def delete_document(self, source: str) -> bool:
        """Delete documents by source filename"""
        try:
            # Get documents with matching source
            collection = self.vectorstore._collection
            results = collection.get()
            
            if not results['documents']:
                return False
            
            # Find documents to delete
            ids_to_delete = []
            for i, metadata in enumerate(results['metadatas']):
                if metadata and metadata.get('source') == source:
                    ids_to_delete.append(results['ids'][i])
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                self.document_sources.discard(source)
                self.vectorstore.persist()
                print(f"Deleted {len(ids_to_delete)} documents with source: {source}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all documents from vector store"""
        try:
            self.vectorstore._client.delete_collection("rag_documents")
            self.document_sources.clear()
            print("Cleared all documents from vector store")
            return True
        except Exception as e:
            print(f"Error clearing vector store: {str(e)}")
            return False
    
    def reinitialize(self):
        """Reinitialize vector store after clearing"""
        try:
            # Reinitialize Chroma vector store
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="rag_documents"
            )
            self.document_sources.clear()
            print("Vector store reinitialized")
        except Exception as e:
            print(f"Error reinitializing vector store: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            collection = self.vectorstore._collection
            results = collection.get()
            
            total_documents = len(results['documents']) if results['documents'] else 0
            
            # Count documents by source
            source_counts = {}
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata:
                        source = metadata.get('source', 'Unknown')
                        source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                'total_documents': total_documents,
                'unique_sources': len(self.document_sources),
                'source_counts': source_counts,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            print(f"Error getting vector store stats: {str(e)}")
            return {}
    
    def _load_existing_sources(self):
        """Load existing document sources from vector store"""
        try:
            collection = self.vectorstore._collection
            results = collection.get()
            
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata:
                        source = metadata.get('source', 'Unknown')
                        self.document_sources.add(source)
            
            print(f"Loaded {len(self.document_sources)} existing document sources")
            
        except Exception as e:
            print(f"Error loading existing sources: {str(e)}")
    
    def is_empty(self) -> bool:
        """Check if vector store is empty"""
        try:
            collection = self.vectorstore._collection
            results = collection.get()
            return len(results['documents']) == 0 if results['documents'] else True
        except Exception as e:
            print(f"Error checking if vector store is empty: {str(e)}")
            return True 