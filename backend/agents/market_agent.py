"""
Market Intelligence Agent - RAG-Powered
Provides pharmaceutical market data and analysis using RAG
"""
import os
import logging
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from config.llm.llm_config import generate_llm_response

# Check if RAG dependencies are available
try:
    from vector_store.rag_engine import RAGEngine
    from vector_store.document_ingestion import DocumentIngestion, create_sample_market_corpus
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  RAG not available. Market Agent will use fallback mode.")

logger = logging.getLogger(__name__)

class MarketAgent:
    """
    Market Intelligence Agent - RAG-Powered
    Retrieves and analyzes pharmaceutical market data using semantic search
    """

    def __init__(self, use_rag: bool = True, initialize_corpus: bool = True):
        """
        Initialize Market Intelligence Agent

        Args:
            use_rag: Whether to use RAG (True) or fallback to mock data (False)
            initialize_corpus: Whether to initialize sample corpus on first run
        """
        self.name = "Market Intelligence Agent"
        self.agent_id = "market"
        self.use_rag = use_rag and RAG_AVAILABLE

        if self.use_rag:
            try:
                self.data_source = "RAG-Powered Market Intelligence"
                self.rag_engine = RAGEngine(
                    collection_name="market_intelligence",
                    persist_directory="./vector_store/chroma_db"
                )

                # Initialize corpus if empty and requested
                stats = self.rag_engine.get_collection_stats()
                if stats["total_documents"] == 0 and initialize_corpus:
                    logger.info("Initializing market intelligence corpus...")
                    self._initialize_corpus()

                logger.info(f"✅ Market Agent initialized with RAG ({stats['total_documents']} documents)")

            except Exception as e:
                logger.error(f"Failed to initialize RAG: {e}")
                logger.info("Falling back to mock data mode")
                self.use_rag = False
                self.data_source = "Mock Market Data (RAG unavailable)"
        else:
            self.data_source = "Mock Market Data"
            logger.info("Market Agent initialized in mock data mode")

    def _initialize_corpus(self):
        """Initialize the RAG corpus with sample market documents"""
        try:
            # Create sample corpus
            corpus_path = create_sample_market_corpus(
                output_path="./vector_store/documents/market_corpus.json"
            )

            # Ingest into RAG
            ingestion = DocumentIngestion(self.rag_engine)
            count = ingestion.ingest_json_documents(
                corpus_path,
                chunk_size=1000,
                overlap=200
            )

            logger.info(f"✅ Initialized corpus with {count} document chunks")

        except Exception as e:
            logger.error(f"Failed to initialize corpus: {e}")
            raise

    def get_system_prompt(self) -> str:
        """System prompt for market intelligence analysis"""
        return """You are a pharmaceutical market intelligence specialist with expertise in:
        - Market size analysis and forecasting
        - Competitive landscape assessment
        - Therapy area trends and dynamics
        - Key player analysis and market share
        - Pricing and reimbursement strategies
        - Pipeline and emerging opportunities
        - Regional market dynamics

        Provide comprehensive, data-driven insights based on the retrieved documents.
        Always cite specific numbers, percentages, and trends from the source material.
        Structure your analysis clearly with key findings highlighted.
        Be professional, concise, and actionable."""

    def process(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Process market intelligence query using RAG

        Args:
            query: User query about pharmaceutical markets
            top_k: Number of relevant documents to retrieve

        Returns:
            Dict with findings, confidence, and references
        """
        logger.info(f"📊 Market Agent processing query: {query[:100]}...")

        if self.use_rag:
            return self._process_with_rag(query, top_k)
        else:
            return self._process_with_mock_data(query)

    def _process_with_rag(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Process query using RAG retrieval and LLM synthesis"""
        try:
            # Retrieve relevant documents
            logger.info(f"🔍 Searching RAG for relevant market intelligence...")
            retrieved_docs = self.rag_engine.search(query, top_k=top_k)

            if not retrieved_docs:
                logger.warning("No relevant documents found in RAG")
                return self._create_no_data_response(query)

            logger.info(f"Found {len(retrieved_docs)} relevant documents")

            # Generate comprehensive analysis using LLM
            analysis = self._generate_rag_analysis(query, retrieved_docs)

            # Extract references from retrieved docs
            references = self._create_references_from_docs(retrieved_docs)

            # Calculate confidence based on relevance scores
            avg_relevance = sum(doc["relevance_score"] for doc in retrieved_docs) / len(retrieved_docs)
            confidence = int(avg_relevance * 100)

            result = {
                "agent": self.name,
                "agent_id": self.agent_id,
                "finding": analysis,
                "confidence": confidence,
                "data_source": "RAG-Powered Market Intelligence",
                "documents_retrieved": len(retrieved_docs),
                "references": references
            }

            logger.info(f"✅ Market Agent completed analysis (confidence: {confidence}%)")
            return result

        except Exception as e:
            logger.error(f"Error in RAG processing: {e}")
            return self._create_error_response(query, str(e))

    def _generate_rag_analysis(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Generate comprehensive market analysis from retrieved documents

        Args:
            query: User query
            retrieved_docs: List of retrieved document chunks

        Returns:
            Comprehensive market analysis
        """
        # Compile context from retrieved documents
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            title = doc["metadata"].get("title", "Untitled")
            date = doc["metadata"].get("date", "N/A")
            content = doc["content"]

            context_parts.append(
                f"Document {i} - {title} ({date}):\n{content}\n"
            )

        context = "\n---\n".join(context_parts)

        # Create analysis prompt
        prompt = f"""Based on the following market intelligence documents, provide a comprehensive analysis for this query:

Query: {query}

Retrieved Market Intelligence:
{context}

Provide a detailed market intelligence analysis that:
1. **Market Overview**: Current market size, growth rates (CAGR), and forecasts
2. **Key Players**: Leading companies and their market positions
3. **Product Landscape**: Major products, sales figures, and market share
4. **Market Dynamics**: Trends, drivers, and challenges
5. **Regional Insights**: Geographic distribution if relevant
6. **Future Outlook**: Pipeline developments and market opportunities

Be specific with numbers, cite years and sources, and structure the response clearly.
If data is missing for any aspect, acknowledge it clearly.
Aim for 3-4 paragraphs covering the most relevant aspects."""

        try:
            # Generate analysis using LLM
            logger.info("Generating market analysis with LLM...")
            analysis = generate_llm_response(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=0.3,  # Lower temperature for factual analysis
                max_tokens=1000
            )

            return analysis

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback: return summarized document excerpts
            return self._create_fallback_analysis(query, retrieved_docs)

    def _create_fallback_analysis(self, query: str, docs: List[Dict[str, Any]]) -> str:
        """Create a basic analysis when LLM fails"""
        summaries = []
        for doc in docs[:3]:  # Top 3 documents
            title = doc["metadata"].get("title", "Market Report")
            content_preview = doc["content"][:300] + "..."
            summaries.append(f"**{title}**\n{content_preview}")

        return "\n\n".join(summaries)

    def _create_references_from_docs(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create reference list from retrieved documents"""
        references = []

        for doc in docs:
            metadata = doc["metadata"]
            ref = {
                "type": "market-intelligence",
                "title": metadata.get("title", "Market Intelligence Document"),
                "source": metadata.get("source", "Internal Knowledge Base"),
                "date": metadata.get("date", "2024"),
                "therapy_area": metadata.get("therapy_area", "N/A"),
                "relevance": int(doc["relevance_score"] * 100),
                "agentId": self.agent_id,
                "document_id": doc["id"]
            }
            references.append(ref)

        return references

    def _create_no_data_response(self, query: str) -> Dict[str, Any]:
        """Response when no relevant data is found"""
        return {
            "agent": self.name,
            "agent_id": self.agent_id,
            "finding": f"No specific market intelligence data found for query: '{query}'. The knowledge base may need to be updated with relevant market reports.",
            "confidence": 40,
            "data_source": self.data_source,
            "documents_retrieved": 0,
            "references": []
        }

    def _create_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Response when an error occurs"""
        return {
            "agent": self.name,
            "agent_id": self.agent_id,
            "finding": f"Error processing market intelligence query: {error}",
            "confidence": 0,
            "data_source": self.data_source,
            "error": error,
            "references": []
        }

    def _process_with_mock_data(self, query: str) -> Dict[str, Any]:
        """Fallback: process with mock data when RAG is unavailable"""
        logger.info("Using mock data fallback")

        # Simple keyword-based mock data
        query_lower = query.lower()

        mock_responses = {
            "glp-1": "GLP-1 market: $23.5B (2024), 18.2% CAGR. Leaders: Novo Nordisk (Ozempic $14.2B), Eli Lilly (Mounjaro $5.1B). Forecast: $45.8B by 2030.",
            "diabetes": "Diabetes market: $68.5B (2024), 9.3% CAGR. Key segments: Insulin ($32.1B), GLP-1 ($23.5B), SGLT2i ($8.9B). Forecast: $112.4B by 2030.",
            "oncology": "Oncology market: $185.3B (2024), 11.7% CAGR. Immunotherapy leads at $78.2B. Key players: Roche, BMS, Merck. Forecast: $356.2B by 2030.",
            "alzheimer": "Alzheimer's market: $4.8B (2024), 35.2% CAGR. Leqembi and Donanemab driving growth. Forecast: $28.5B by 2030.",
        }

        finding = next(
            (response for keyword, response in mock_responses.items() if keyword in query_lower),
            "Global pharmaceutical market: $1.48T with 6.8% CAGR."
        )

        return {
            "agent": self.name,
            "agent_id": self.agent_id,
            "finding": finding,
            "confidence": 75,
            "data_source": "Mock Data (RAG unavailable)",
            "references": [
                {
                    "type": "market-report",
                    "title": "Global Pharmaceutical Market Report 2024",
                    "source": "IQVIA Institute",
                    "date": "2024",
                    "relevance": 80,
                    "agentId": self.agent_id
                }
            ]
        }

    def add_market_document(
        self,
        content: str,
        title: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a new market intelligence document to RAG

        Args:
            content: Document content
            title: Document title
            metadata: Document metadata (date, source, therapy_area, etc.)

        Returns:
            Success boolean
        """
        if not self.use_rag:
            logger.warning("Cannot add document: RAG not available")
            return False

        try:
            doc = {
                "id": metadata.get("id", f"doc_{hash(title)}"),
                "content": content,
                "title": title,
                **metadata
            }

            self.rag_engine.add_documents([doc])
            logger.info(f"✅ Added document: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize agent
    agent = MarketAgent(use_rag=True, initialize_corpus=True)

    # Test queries
    test_queries = [
        "What is the GLP-1 market size and forecast?",
        "Tell me about the oncology immunotherapy market",
        "What are the key players in Alzheimer's disease treatment?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        result = agent.process(query)

        print(f"\nFinding:\n{result['finding']}")
        print(f"\nConfidence: {result['confidence']}%")
        print(f"Documents Retrieved: {result.get('documents_retrieved', 'N/A')}")
        print(f"\nReferences: {len(result['references'])} sources")
