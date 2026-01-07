"""
Market Intelligence Agent - Hybrid Web Search + RAG
Combines fresh web data with deep internal RAG knowledge
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config.llm.llm_config_sync import generate_llm_response

# Import RAG components (existing)
try:
    from vector_store.rag_engine import RAGEngine
    from vector_store.document_ingestion import DocumentIngestion, create_sample_market_corpus
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  RAG not available. Market Agent will use web search only.")

# Import Web Search component (new)
try:
    from utils.web_search import WebSearchEngine
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print("⚠️  Web search not available. Market Agent will use RAG only.")

# Import Confidence Scoring (new)
try:
    from utils.confidence_scoring import ConfidenceScorer
    CONFIDENCE_SCORING_AVAILABLE = True
except ImportError:
    CONFIDENCE_SCORING_AVAILABLE = False
    print("⚠️  Confidence scoring not available. Using simple fallback.")

# Import Keyword Extraction (new)
try:
    from utils.keyword_extraction import KeywordExtractor
    KEYWORD_EXTRACTION_AVAILABLE = True
except ImportError:
    KEYWORD_EXTRACTION_AVAILABLE = False
    print("⚠️  Keyword extraction not available. Using simple fallback.")

# Import Section Synthesis (new)
try:
    from utils.section_synthesis import SectionSynthesizer
    SECTION_SYNTHESIS_AVAILABLE = True
except ImportError:
    SECTION_SYNTHESIS_AVAILABLE = False
    print("⚠️  Section synthesis not available. Using legacy JSON synthesis.")

# Import Forecast Reconciliation (new)
try:
    from utils.forecast_reconciliation import ForecastReconciler
    FORECAST_RECONCILIATION_AVAILABLE = True
except ImportError:
    FORECAST_RECONCILIATION_AVAILABLE = False
    print("⚠️  Forecast reconciliation not available. Using without reconciliation.")

logger = logging.getLogger(__name__)


class MarketAgentHybrid:
    """
    Hybrid Market Intelligence Agent

    Retrieval Strategy:
    1. Query Analysis: Determine if query needs fresh data, historical context, or both
    2. Web Search Layer: Fetch fresh market intelligence from the web
    3. RAG Layer: Retrieve deep context from internal knowledge base
    4. Context Fusion: Combine and deduplicate both sources
    5. LLM Synthesis: Generate comprehensive response from fused context
    6. Structured Output: Return JSON contract for orchestrator
    """

    def __init__(
        self,
        use_rag: bool = True,
        use_web_search: bool = True,
        initialize_corpus: bool = True,
        search_provider: str = "serpapi"
    ):
        """
        Initialize Hybrid Market Agent

        Args:
            use_rag: Enable RAG retrieval
            use_web_search: Enable web search
            initialize_corpus: Initialize sample corpus on first run
            search_provider: Web search provider ('serpapi', 'bing', 'duckduckgo')
        """
        self.name = "Market Intelligence Agent (Hybrid)"
        self.agent_id = "market"

        # Initialize RAG engine (existing logic)
        self.use_rag = use_rag and RAG_AVAILABLE
        if self.use_rag:
            try:
                self.rag_engine = RAGEngine(
                    collection_name="market_intelligence",
                    persist_directory="./vector_store/chroma_db"
                )

                stats = self.rag_engine.get_collection_stats()
                if stats["total_documents"] == 0 and initialize_corpus:
                    logger.info("Initializing market intelligence corpus...")
                    self._initialize_corpus()

                logger.info(f"✅ RAG initialized ({stats['total_documents']} documents)")

            except Exception as e:
                logger.error(f"RAG initialization failed: {e}")
                self.use_rag = False

        # Initialize web search engine (new)
        self.use_web_search = use_web_search and WEB_SEARCH_AVAILABLE
        if self.use_web_search:
            try:
                self.web_search = WebSearchEngine(
                    search_provider=search_provider
                )
                logger.info(f"✅ Web search initialized (provider: {search_provider})")
            except Exception as e:
                logger.error(f"Web search initialization failed: {e}")
                self.use_web_search = False

        # Initialize confidence scorer (new)
        if CONFIDENCE_SCORING_AVAILABLE:
            self.confidence_scorer = ConfidenceScorer()
            logger.info("✅ Confidence scoring initialized")
        else:
            self.confidence_scorer = None

        # Initialize keyword extractor (new)
        if KEYWORD_EXTRACTION_AVAILABLE:
            self.keyword_extractor = KeywordExtractor()
            logger.info("✅ Keyword extraction initialized")
        else:
            self.keyword_extractor = None

        # Initialize section synthesizer (new)
        if SECTION_SYNTHESIS_AVAILABLE:
            self.section_synthesizer = SectionSynthesizer()
            logger.info("✅ Section synthesis initialized")
        else:
            self.section_synthesizer = None

        # Initialize forecast reconciler (new)
        if FORECAST_RECONCILIATION_AVAILABLE:
            self.forecast_reconciler = ForecastReconciler()
            logger.info("✅ Forecast reconciliation initialized")
        else:
            self.forecast_reconciler = None

        # Log final configuration
        retrieval_methods = []
        if self.use_rag:
            retrieval_methods.append("RAG")
        if self.use_web_search:
            retrieval_methods.append("Web Search")
        if not retrieval_methods:
            retrieval_methods.append("Fallback/Mock")

        logger.info(f"🎯 Market Agent ready: {' + '.join(retrieval_methods)}")

    def _initialize_corpus(self):
        """Initialize RAG corpus with sample documents"""
        try:
            corpus_path = create_sample_market_corpus(
                output_path="./vector_store/documents/market_corpus.json"
            )
            ingestion = DocumentIngestion(self.rag_engine)
            count = ingestion.ingest_json_documents(corpus_path, chunk_size=1000, overlap=200)
            logger.info(f"✅ Corpus initialized with {count} chunks")
        except Exception as e:
            logger.error(f"Corpus initialization failed: {e}")
            raise

    def process(self, query: str, top_k_rag: int = 5, top_k_web: int = 10) -> Dict[str, Any]:
        """
        Process market intelligence query using hybrid retrieval

        Args:
            query: User query
            top_k_rag: Number of RAG documents to retrieve
            top_k_web: Number of web results to retrieve

        Returns:
            Structured JSON output following the contract
        """
        logger.info(f"📊 Processing query: {query[:100]}...")

        # Step 1: Query Analysis - determine retrieval strategy
        needs_fresh, needs_historical = self._analyze_query(query)

        logger.info(f"   📋 Query analysis: fresh={needs_fresh}, historical={needs_historical}")

        # Step 2 & 3: Parallel retrieval (web search + RAG)
        web_results = []
        rag_results = []
        search_keywords = []

        # Web Search Layer (FIRST)
        if self.use_web_search and needs_fresh:
            search_keywords = self._extract_search_keywords(query)
            web_results = self._retrieve_from_web(search_keywords, top_k_web)
            logger.info(f"   🌐 Web search: {len(web_results)} results")

        # RAG Layer (SECOND)
        if self.use_rag and needs_historical:
            rag_results = self._retrieve_from_rag(query, top_k_rag)
            logger.info(f"   📚 RAG retrieval: {len(rag_results)} documents")

        # Step 4: Context Fusion
        fused_context = self._fuse_contexts(web_results, rag_results)

        # Step 5: LLM Synthesis
        sections = self._synthesize_intelligence(query, fused_context, web_results, rag_results)

        # Step 5.5: Forecast Reconciliation (NEW)
        coherence_boost = 0.0
        if self.forecast_reconciler:
            sections, coherence_boost = self.forecast_reconciler.reconcile_forecasts(
                sections, web_results, rag_results
            )
            logger.info(f"   🔄 Forecast reconciliation applied (coherence boost: +{coherence_boost:.2f})")

        # Step 6: Calculate Comprehensive Confidence
        if self.confidence_scorer:
            confidence_analysis = self.confidence_scorer.calculate_confidence(
                query=query,
                web_results=web_results,
                rag_results=rag_results,
                sections=sections,
                coherence_boost=coherence_boost  # Pass reconciliation boost
            )
        else:
            # Fallback to simple confidence
            simple_confidence = self._calculate_confidence_fallback(web_results, rag_results)
            confidence_analysis = {
                "score": simple_confidence,
                "breakdown": {},
                "explanation": "Using simple confidence calculation",
                "level": "medium" if simple_confidence > 0.5 else "low"
            }

        # Step 7: Structured JSON Output
        output = {
            "agentId": self.agent_id,
            "query": query,
            "retrieval_used": {
                "web_search": len(web_results) > 0,
                "rag": len(rag_results) > 0
            },
            "search_keywords": search_keywords,
            "web_results": [self._format_web_result(r) for r in web_results],
            "rag_results": [self._format_rag_result(r) for r in rag_results],
            "sections": sections,
            "confidence": confidence_analysis,  # New: Full confidence object
            "confidence_score": confidence_analysis["score"],  # Legacy: For backward compat
            "sources": {
                "web": [r["url"] for r in web_results if "url" in r],
                "internal": [r.get("id", "") for r in rag_results]
            }
        }

        logger.info(f"✅ Query processed (confidence: {confidence_analysis['score']:.2%} - {confidence_analysis['level']})")
        return output

    def _analyze_query(self, query: str) -> Tuple[bool, bool]:
        """
        Analyze query to determine retrieval strategy

        Returns:
            (needs_fresh_data, needs_historical_context)
        """
        query_lower = query.lower()

        # Keywords indicating need for fresh data
        fresh_indicators = [
            "latest", "recent", "current", "2024", "2025", "2026",
            "q1", "q2", "q3", "q4", "today", "now", "update"
        ]

        # Keywords indicating need for historical context
        historical_indicators = [
            "history", "trend", "evolution", "background", "overview",
            "mechanism", "structure", "pipeline", "landscape"
        ]

        needs_fresh = any(indicator in query_lower for indicator in fresh_indicators)
        needs_historical = any(indicator in query_lower for indicator in historical_indicators)

        # Default: use both if unclear
        if not needs_fresh and not needs_historical:
            needs_fresh = True
            needs_historical = True

        return needs_fresh, needs_historical

    def _extract_search_keywords(self, query: str) -> List[str]:
        """
        Extract concise search keywords from query using LLM + deterministic fallback

        New approach:
        1. Try LLM extraction
        2. Validate keywords (reject >8 words, question words)
        3. Fall back to deterministic entity-based extraction
        """
        if not self.keyword_extractor:
            # Legacy fallback if new module unavailable
            return self._extract_search_keywords_legacy(query)

        # Try LLM extraction first
        llm_keywords = None
        try:
            prompt = f"""Extract 2-4 concise search keywords for a web search about this market intelligence query:

Query: {query}

Return ONLY the keywords as a comma-separated list, nothing else.
Focus on: therapy areas, drug names, companies, market terms.

Example output: GLP-1 market size, Novo Nordisk revenue, diabetes drugs 2024"""

            response = generate_llm_response(
                prompt=prompt,
                system_prompt="You are a search keyword extractor. Return only keywords, no explanations.",
                temperature=0.2,
                max_tokens=100
            )

            # Parse keywords
            llm_keywords = [k.strip() for k in response.split(",") if k.strip()]

        except Exception as e:
            logger.warning(f"LLM keyword extraction failed: {e}")

        # Use robust extractor with validation + fallback
        keywords = self.keyword_extractor.extract_keywords_robust(query, llm_keywords)

        logger.info(f"   🔑 Final keywords: {keywords}")
        return keywords

    def _extract_search_keywords_legacy(self, query: str) -> List[str]:
        """
        Legacy keyword extraction (kept for backward compatibility)
        Used when KeywordExtractor module is unavailable
        """
        prompt = f"""Extract 2-4 concise search keywords for a web search about this market intelligence query:

Query: {query}

Return ONLY the keywords as a comma-separated list, nothing else.
Focus on: therapy areas, drug names, companies, market terms.

Example output: GLP-1 market size, Novo Nordisk revenue, diabetes drugs 2024"""

        try:
            response = generate_llm_response(
                prompt=prompt,
                system_prompt="You are a search keyword extractor. Return only keywords, no explanations.",
                temperature=0.2,
                max_tokens=100
            )

            # Parse keywords
            keywords = [k.strip() for k in response.split(",") if k.strip()]

            # hard fallback if LLM output is empty / junk
            if not keywords:
                keywords = [query]

            logger.info(f"   🔑 Extracted keywords (legacy): {keywords}")
            return keywords

        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            # Fallback: use original query
            return [query]

    def _retrieve_from_web(self, keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
        """
        Retrieve fresh market data from web search using multi-query approach

        New approach (vs legacy):
        - Uses 3-5 keyword queries per request (was 1-2)
        - Applies domain filtering and weighting
        - Prioritizes Tier 1 pharma intelligence sources
        - Better deduplication and ranking
        """
        if not keywords:
            return []

        # Use the new multi-query search method
        try:
            results = self.web_search.search_multi_query(
                queries=keywords[:5],  # Use up to 5 keywords (was 2)
                num_results_per_query=max(3, top_k // len(keywords[:5])),
                time_filter="year"  # Prefer recent results
            )

            # Results are already deduplicated and weighted by search_multi_query
            logger.info(f"Web search retrieved {len(results)} results from {len(keywords[:5])} queries")
            return results[:top_k]

        except Exception as e:
            logger.error(f"Multi-query web search failed: {e}")
            return []

    def _retrieve_from_rag(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve historical context from internal RAG"""
        try:
            return self.rag_engine.search(query, top_k=top_k)
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []

    def _fuse_contexts(
        self,
        web_results: List[Dict[str, Any]],
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """
        Fuse web and RAG contexts into single context string
        Clearly labels sources as web or internal
        """
        context_parts = []

        # Add web search results
        if web_results:
            context_parts.append("=== WEB SEARCH RESULTS (Fresh Market Data) ===\n")
            for i, result in enumerate(web_results, 1):
                title = result.get("title", "Untitled")
                snippet = result.get("snippet", "")
                url = result.get("url", "")
                date = result.get("date", "")

                context_parts.append(
                    f"[WEB-{i}] {title} ({date})\n"
                    f"URL: {url}\n"
                    f"{snippet}\n"
                )

        # Add RAG results
        if rag_results:
            context_parts.append("\n=== INTERNAL KNOWLEDGE BASE (Deep Context) ===\n")
            for i, result in enumerate(rag_results, 1):
                title = result["metadata"].get("title", "Internal Document")
                date = result["metadata"].get("date", "")
                content = result["content"]

                context_parts.append(
                    f"[RAG-{i}] {title} ({date})\n"
                    f"{content}\n"
                )

        return "\n---\n".join(context_parts)

    def _synthesize_intelligence(
        self,
        query: str,
        fused_context: str,
        web_results: List[Dict],
        rag_results: List[Dict]
    ) -> Dict[str, str]:
        """
        Synthesize comprehensive market intelligence from fused sources

        New approach:
        - Generate each section independently (7 LLM calls)
        - Plain text only (no JSON parsing)
        - Guaranteed 100% section population

        Returns structured sections following the output contract
        """
        if not self.section_synthesizer:
            # Legacy fallback if new module unavailable
            return self._synthesize_intelligence_legacy(query, fused_context, web_results, rag_results)

        try:
            # Use bulletproof section-wise synthesis
            sections = self.section_synthesizer.synthesize_all_sections(
                query=query,
                fused_context=fused_context,
                web_results=web_results,
                rag_results=rag_results
            )

            # Validate all 7 sections exist (should always be true)
            required_sections = [
                'summary', 'market_overview', 'key_metrics',
                'drivers_and_trends', 'competitive_landscape',
                'risks_and_opportunities', 'future_outlook'
            ]

            for section in required_sections:
                if section not in sections:
                    logger.error(f"Missing section: {section}")
                    sections[section] = f"Insufficient data in retrieved sources for {section.replace('_', ' ')}."

            logger.info(f"✅ Section synthesis complete: {len(sections)} sections")
            return sections

        except Exception as e:
            logger.error(f"Section synthesis failed: {e}")
            return self._create_fallback_sections(web_results, rag_results)

    def _synthesize_intelligence_legacy(
        self,
        query: str,
        fused_context: str,
        web_results: List[Dict],
        rag_results: List[Dict]
    ) -> Dict[str, str]:
        """
        Legacy synthesis method (kept for backward compatibility)
        Used when SectionSynthesizer module is unavailable
        """
        prompt = f"""You are a pharmaceutical market intelligence analyst. Based on the retrieved information, provide a comprehensive market analysis.

USER QUERY: {query}

RETRIEVED INFORMATION:
{fused_context}

Generate a structured market intelligence report with these sections:

1. SUMMARY (2-3 sentences): High-level answer to the query
2. MARKET_OVERVIEW: Current market size, CAGR, and key metrics
3. KEY_METRICS: Specific numbers, forecasts, and data points
4. DRIVERS_AND_TRENDS: Market drivers, trends, and dynamics
5. COMPETITIVE_LANDSCAPE: Key players, market share, product landscape
6. RISKS_AND_OPPORTUNITIES: Challenges and opportunities
7. FUTURE_OUTLOOK: Forecasts and pipeline developments

IMPORTANT RULES:
- Use ONLY information from the retrieved sources above
- Cite source labels ([WEB-1], [RAG-2], etc.) after each fact
- Prefer web sources for recent numbers and RAG sources for background
- Do NOT hallucinate facts not present in the sources
- If a section lacks data, write "Insufficient data in retrieved sources"
- Be concise but comprehensive

Return your response as JSON with keys: summary, market_overview, key_metrics, drivers_and_trends, competitive_landscape, risks_and_opportunities, future_outlook"""

        try:
            response = generate_llm_response(
                prompt=prompt,
                system_prompt="You are a market intelligence analyst. Return ONLY valid JSON, no markdown formatting.",
                temperature=0.3,
                max_tokens=1500
            )

            # Parse JSON response
            try:
                # Remove markdown code blocks if present
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()

                sections = json.loads(response)
                return sections

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                # Fallback: parse as plain text and structure manually
                return self._fallback_structure(response)

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return self._create_fallback_sections(web_results, rag_results)

    def _fallback_structure(self, text: str) -> Dict[str, str]:
        """Structure plain text response into sections"""
        return {
            "summary": text[:500] if text else "Analysis unavailable",
            "market_overview": "See summary",
            "key_metrics": "See summary",
            "drivers_and_trends": "See summary",
            "competitive_landscape": "See summary",
            "risks_and_opportunities": "See summary",
            "future_outlook": "See summary"
        }

    def _create_fallback_sections(
        self,
        web_results: List[Dict],
        rag_results: List[Dict]
    ) -> Dict[str, str]:
        """Create basic sections when LLM synthesis fails"""
        web_summary = " ".join([r.get("snippet", "")[:200] for r in web_results[:2]])
        rag_summary = " ".join([r["content"][:200] for r in rag_results[:2]])

        return {
            "summary": web_summary or rag_summary or "Analysis unavailable",
            "market_overview": web_summary,
            "key_metrics": "LLM synthesis unavailable",
            "drivers_and_trends": rag_summary,
            "competitive_landscape": "See retrieved sources",
            "risks_and_opportunities": "See retrieved sources",
            "future_outlook": "See retrieved sources"
        }

    def _format_web_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Format web search result for output"""
        return {
            "title": result.get("title", ""),
            "snippet": result.get("snippet", ""),
            "url": result.get("url", ""),
            "date": result.get("date", "")
        }

    def _format_rag_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Format RAG result for output"""
        return {
            "doc_id": result.get("id", ""),
            "title": result["metadata"].get("title", ""),
            "source": result["metadata"].get("source", "Internal"),
            "snippet": result["content"][:300] + "..."
        }

    def _calculate_confidence_fallback(
        self,
        web_results: List[Dict],
        rag_results: List[Dict]
    ) -> float:
        """
        Simple fallback confidence calculation (legacy)
        Used only when ConfidenceScorer is unavailable

        Returns: float between 0.0 and 1.0
        """
        confidence = 0.0

        # Web search contributes up to 0.5
        if web_results:
            web_score = min(len(web_results) / 10.0, 0.5)
            confidence += web_score

        # RAG contributes up to 0.5
        if rag_results:
            scores = [r.get("relevance_score", 0.2) for r in rag_results]
            avg_relevance = sum(scores) / len(scores)
            rag_score = avg_relevance * 0.5
            confidence += rag_score

        return min(confidence, 1.0)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize hybrid agent
    agent = MarketAgentHybrid(
        use_rag=True,
        use_web_search=True,
        initialize_corpus=True
    )

    # Test queries
    test_queries = [
        "What is the latest GLP-1 market size and forecast for 2024?",
        "Tell me about the oncology immunotherapy market landscape",
        "What are recent developments in Alzheimer's disease treatments?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        result = agent.process(query)

        print(f"\n📊 Retrieval Used:")
        print(f"   Web Search: {result['retrieval_used']['web_search']}")
        print(f"   RAG: {result['retrieval_used']['rag']}")

        print(f"\n📝 Summary:")
        print(f"   {result['sections']['summary']}")

        print(f"\n📈 Confidence: {result['confidence_score']:.2%}")
        print(f"\n🔗 Sources:")
        print(f"   Web: {len(result['sources']['web'])} sources")
        print(f"   Internal: {len(result['sources']['internal'])} documents")

        # Print full JSON (commented out for brevity)
        # print(f"\n💾 Full JSON Output:")
        # print(json.dumps(result, indent=2))
