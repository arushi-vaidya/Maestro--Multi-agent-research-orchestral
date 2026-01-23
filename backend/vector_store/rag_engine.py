"""
RAG Engine for Market Intelligence
Handles document embedding, storage, and retrieval using ChromaDB
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️  RAG dependencies not installed. Install with: pip install -r requirements_rag.txt")

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval-Augmented Generation Engine

    Uses ChromaDB for vector storage and sentence-transformers for embeddings.
    Provides semantic search over market intelligence documents.
    """

    def __init__(
        self,
        collection_name: str = "market_intelligence",
        persist_directory: str = "./vector_store/chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG Engine

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist vector database
            embedding_model: Sentence transformer model name
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "RAG dependencies not installed. "
                "Install with: pip install -r requirements_rag.txt"
            )

        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at: {persist_directory}")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Market intelligence documents"}
            )
            logger.info(f"Created new collection: {collection_name}")

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Add documents to vector store

        Args:
            documents: List of document dicts with 'id', 'content', and metadata
            batch_size: Number of documents to process at once

        Returns:
            Number of documents added

        Expected document format:
        {
            "id": "unique_doc_id",
            "content": "Document text content",
            "title": "Document title",
            "date": "2024-01-01",
            "source": "Source name",
            "therapy_area": "Oncology",
            ... other metadata
        }
        """
        logger.info(f"Adding {len(documents)} documents to vector store...")

        added_count = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Extract components
            ids = [doc["id"] for doc in batch]
            contents = [doc["content"] for doc in batch]
            metadatas = []

            for doc in batch:
                # Extract metadata (exclude id and content)
                metadata = {
                    k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in doc.items()
                    if k not in ["id", "content"]
                }
                metadatas.append(metadata)

            # Generate embeddings
            embeddings = self.embedding_model.encode(
                contents,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )

            added_count += len(batch)
            logger.info(f"Added batch {i//batch_size + 1}: {added_count}/{len(documents)} documents")

        logger.info(f"✅ Successfully added {added_count} documents")
        return added_count

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant documents

        Args:
            query: Search query text
            top_k: Number of top results to return
            filter_metadata: Optional metadata filters (e.g., {"therapy_area": "Oncology"})

        Returns:
            List of document dictionaries with content, metadata, and relevance scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()

        # Search ChromaDB
        search_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }

        if filter_metadata:
            search_kwargs["where"] = filter_metadata

        results = self.collection.query(**search_kwargs)

        # Format results
        documents = []
        for i in range(len(results["ids"][0])):
            doc = {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "relevance_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                "distance": results["distances"][0][i]
            }
            documents.append(doc)

        logger.info(f"Found {len(documents)} relevant documents for query: {query[:50]}...")
        return documents

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None

    def delete_documents(self, doc_ids: List[str]) -> int:
        """
        Delete documents by IDs

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            Number of documents deleted
        """
        try:
            self.collection.delete(ids=doc_ids)
            logger.info(f"Deleted {len(doc_ids)} documents")
            return len(doc_ids)
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_documents": count,
            "embedding_model": self.embedding_model_name,
            "persist_directory": self.persist_directory
        }

    def reset_collection(self):
        """
        Delete all documents and reset the collection
        WARNING: This cannot be undone!
        """
        logger.warning(f"Resetting collection: {self.collection_name}")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Market intelligence documents"}
        )
        logger.info("Collection reset complete")


class DocumentProcessor:
    """
    Processes various document formats for RAG ingestion
    """

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Input text
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # Only break if > 50% through
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    @staticmethod
    def create_document_from_text(
        text: str,
        doc_id: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Create document chunks with metadata

        Args:
            text: Document text
            doc_id: Base document ID
            metadata: Document metadata
            chunk_size: Size of chunks
            overlap: Overlap between chunks

        Returns:
            List of document dictionaries ready for RAG ingestion
        """
        chunks = DocumentProcessor.chunk_text(text, chunk_size, overlap)
        documents = []

        for i, chunk in enumerate(chunks):
            doc = {
                "id": f"{doc_id}_chunk_{i}",
                "content": chunk,
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            documents.append(doc)

        return documents


# Example usage
if __name__ == "__main__":
    # Test the RAG engine
    logging.basicConfig(level=logging.INFO)

    # Initialize RAG engine
    rag = RAGEngine()

    # Sample documents
    sample_docs = [
        {
            "id": "market_glp1_2024",
            "content": """GLP-1 agonist market reached $23.5B in 2024 with 18.2% CAGR.
            Novo Nordisk leads with Ozempic ($14.2B) and Wegovy ($4.5B).
            Eli Lilly's Mounjaro gained significant market share since 2022 launch.""",
            "title": "GLP-1 Market Analysis 2024",
            "date": "2024-01-15",
            "therapy_area": "Diabetes",
            "source": "Market Intelligence Report"
        },
        {
            "id": "oncology_market_2024",
            "content": """Oncology therapeutics market size: $185.3B with 11.7% CAGR.
            Immunotherapy dominates at $78.2B, followed by targeted therapy at $62.1B.
            Key players: Roche, Bristol Myers Squibb, Merck.""",
            "title": "Oncology Market Overview",
            "date": "2024-02-01",
            "therapy_area": "Oncology",
            "source": "IQVIA Report"
        }
    ]

    # Add documents
    rag.add_documents(sample_docs)

    # Search
    results = rag.search("diabetes GLP-1 market", top_k=2)

    print("\n🔍 Search Results:")
    for doc in results:
        print(f"\nTitle: {doc['metadata'].get('title')}")
        print(f"Relevance: {doc['relevance_score']:.3f}")
        print(f"Content: {doc['content'][:200]}...")

    # Stats
    stats = rag.get_collection_stats()
    print(f"\n📊 Collection Stats: {stats}")
