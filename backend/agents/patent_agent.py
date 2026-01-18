"""
Patent Intelligence Agent
Analyzes patent landscapes, Freedom-to-Operate (FTO), and IP strategy
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# Import LLM configuration
try:
    from config.llm.llm_config_sync import generate_llm_response
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Import USPTO client
try:
    from data_sources.patents import USPTOClient
    USPTO_AVAILABLE = True
except ImportError:
    USPTO_AVAILABLE = False

# Import utilities
try:
    from utils.confidence_scoring import ConfidenceScorer
    CONFIDENCE_SCORING_AVAILABLE = True
except ImportError:
    CONFIDENCE_SCORING_AVAILABLE = False

try:
    from utils.web_search import WebSearchEngine
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class PatentAgent:
    """
    Patent Intelligence Agent

    Features:
    - Patent landscape analysis using USPTO PatentsView API
    - Freedom-to-Operate (FTO) assessment
    - Patent expiration cliff analysis
    - Key player identification
    - White space opportunity detection
    - Litigation risk assessment
    - LLM-powered comprehensive summaries
    - Confidence scoring
    """

    def __init__(self, use_web_search: bool = True):
        """Initialize Patent Agent"""
        self.name = "Patent Intelligence Agent"
        self.agent_id = "patent"

        # API keys
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY", "")

        # Initialize USPTO client
        if USPTO_AVAILABLE:
            try:
                self.uspto_client = USPTOClient()
                logger.info("✅ USPTO PatentsView client initialized")
            except Exception as e:
                logger.error(f"USPTO client initialization failed: {e}")
                self.uspto_client = None
        else:
            logger.warning("⚠️  USPTO client not available")
            self.uspto_client = None

        # Initialize web search (for patent landscape intelligence)
        self.use_web_search = use_web_search and WEB_SEARCH_AVAILABLE
        if self.use_web_search:
            try:
                self.web_search = WebSearchEngine()
                logger.info("✅ Web search initialized for patent intelligence")
            except Exception as e:
                logger.error(f"Web search initialization failed: {e}")
                self.use_web_search = False

        # Initialize confidence scorer
        if CONFIDENCE_SCORING_AVAILABLE:
            self.confidence_scorer = ConfidenceScorer()
            logger.info("✅ Confidence scoring initialized")
        else:
            self.confidence_scorer = None

        # Patent classification codes for pharma
        self.pharma_cpc_codes = {
            'A61K': 'Pharmaceutical preparations',
            'A61P': 'Therapeutic activity of compounds',
            'C07D': 'Heterocyclic compounds',
            'C07K': 'Peptides',
            'C12N': 'Microorganisms or enzymes',
            'A61K38': 'Peptides',
            'A61K39': 'Medicinal preparations containing antigens or antibodies'
        }

        logger.info(f"Patent Agent initialized (USPTO: {self.uspto_client is not None}, Web: {self.use_web_search})")

    def extract_keywords(self, query: str) -> str:
        """
        Extract patent-specific keywords from query using LLM

        Args:
            query: User query

        Returns:
            Extracted keywords (clean, sanitized)
        """
        import re
        
        logger.info(f"Extracting keywords from query: '{query}'")

        # Try Groq first
        if self.groq_api_key:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a patent keyword extractor. Extract ONLY 2-5 simple technical/therapeutic keywords from the query. NO explanations, NO lists, NO patent numbers. Return ONLY comma-separated keywords. Examples: 'GLP-1, diabetes' or 'CRISPR gene therapy' or 'cancer immunotherapy'. Keep it SHORT and CLEAN."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 50
                }

                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                keywords = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

                if keywords:
                    # Sanitize the output
                    keywords = self._sanitize_patent_keywords(keywords)
                    logger.info(f"Extracted keywords: '{keywords}'")
                    return keywords

            except Exception as e:
                logger.warning(f"Groq keyword extraction failed: {e}")

        # Fallback: Extract key terms from query manually
        logger.info(f"Using fallback keyword extraction for query: '{query}'")
        keywords = self._sanitize_patent_keywords(query)
        return keywords
    
    def _sanitize_patent_keywords(self, keywords: str) -> str:
        """
        Sanitize patent keywords for USPTO API.
        
        Removes:
        - Numbered lists (1., 2., etc.)
        - Bullet points
        - Patent numbers
        - Explanatory text
        - Multiple lines
        - Excess whitespace
        
        Returns clean keyword string suitable for USPTO search.
        """
        import re
        
        # Keep only first line
        keywords = keywords.split('\n')[0].strip()
        
        # Remove numbered lists (1., 2., etc.)
        keywords = re.sub(r'^\d+\.\s*', '', keywords)
        
        # Remove bullet points
        keywords = re.sub(r'^[\-\*\•]\s*', '', keywords)
        
        # Remove patent numbers like "US 11,517,870" or "US11046"
        keywords = re.sub(r'\bUS\s*[\d,]+\b', '', keywords, flags=re.IGNORECASE)
        
        # Remove "Based on available information" and similar prefixes
        keywords = re.sub(r'^(Based on|Here are|Some|Recent|Latest)\s+.*?:\s*', '', keywords, flags=re.IGNORECASE)
        
        # Remove explanatory text in parentheses
        keywords = re.sub(r'\([^)]*\)', '', keywords)
        
        # Remove markdown formatting
        keywords = re.sub(r'\*\*', '', keywords)
        keywords = re.sub(r'`', '', keywords)
        
        # Collapse multiple spaces
        keywords = re.sub(r'\s+', ' ', keywords)
        
        # Limit to 100 chars for USPTO API
        if len(keywords) > 100:
            # If too long, take first meaningful part (before comma if exists)
            parts = keywords.split(',')
            keywords = parts[0].strip()
        
        return keywords.strip()

    def search_patents(self, keywords: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search patents using USPTO PatentsView API

        Args:
            keywords: Search keywords
            limit: Maximum number of results

        Returns:
            List of patents
        """
        if not self.uspto_client:
            logger.error("USPTO client not available")
            return []

        try:
            logger.info(f"Searching USPTO patents for: {keywords}")
            patents = self.uspto_client.search_by_keywords(
                keywords=keywords,
                limit=limit,
                years_back=15  # Last 15 years
            )
            logger.info(f"Found {len(patents)} patents")
            return patents

        except Exception as e:
            logger.error(f"Patent search failed: {e}")
            return []

    def analyze_patent_landscape(
        self,
        patents: List[Dict[str, Any]],
        keywords: str
    ) -> Dict[str, Any]:
        """
        Analyze patent landscape from search results

        Args:
            patents: List of patent records
            keywords: Search keywords

        Returns:
            Landscape analysis with key metrics
        """
        logger.info(f"Analyzing patent landscape for {len(patents)} patents")

        if not patents:
            return {
                "total_patents": 0,
                "active_patents": 0,
                "key_players": [],
                "filing_trends": {},
                "classification_distribution": {}
            }

        # Extract assignees
        assignees = []
        for patent in patents:
            for assignee in patent.get('assignees', []):
                org = assignee.get('assignee_organization', '')
                if org:
                    assignees.append(org)

        # Count top assignees
        assignee_counts = Counter(assignees)
        top_assignees = [
            {"organization": org, "patent_count": count}
            for org, count in assignee_counts.most_common(10)
        ]

        # Analyze filing trends by year
        filing_trends = {}
        for patent in patents:
            patent_date = patent.get('patent_date', '')
            if patent_date:
                year = patent_date[:4]
                filing_trends[year] = filing_trends.get(year, 0) + 1

        # Analyze classifications
        classifications = []
        for patent in patents:
            for cpc in patent.get('cpcs', []):
                section = cpc.get('cpc_section', '')
                if section:
                    classifications.append(section)

        classification_counts = Counter(classifications)

        # Calculate active patents (granted in last 15 years, likely not expired)
        current_year = datetime.now().year
        active_patents = sum(
            1 for p in patents
            if p.get('patent_date', '')[: 4].isdigit()
            and current_year - int(p.get('patent_date', '')[:4]) < 20
        )

        landscape = {
            "total_patents": len(patents),
            "active_patents": active_patents,
            "key_players": top_assignees,
            "filing_trends": dict(sorted(filing_trends.items())),
            "classification_distribution": dict(classification_counts.most_common(5))
        }

        logger.info(f"Landscape analysis complete: {landscape['total_patents']} total, {landscape['active_patents']} active")
        return landscape

    def analyze_expiring_patents(
        self,
        keywords: str,
        years_from_now: int = 3
    ) -> Dict[str, Any]:
        """
        Identify patents expiring within specified timeframe

        Args:
            keywords: Search keywords
            years_from_now: Find patents expiring in next N years

        Returns:
            Expiring patent analysis
        """
        if not self.uspto_client:
            logger.error("USPTO client not available")
            return {"expiring_patents": [], "count": 0}

        try:
            logger.info(f"Searching for patents expiring in next {years_from_now} years")
            expiring = self.uspto_client.search_expiring_patents(
                keywords=keywords,
                years_from_now=years_from_now
            )

            # Group by assignee
            by_assignee = {}
            for patent in expiring:
                for assignee in patent.get('assignees', []):
                    org = assignee.get('assignee_organization', 'Unknown')
                    if org not in by_assignee:
                        by_assignee[org] = []
                    by_assignee[org].append({
                        "patent_number": patent.get('patent_number'),
                        "title": patent.get('patent_title'),
                        "grant_date": patent.get('patent_date')
                    })

            logger.info(f"Found {len(expiring)} expiring patents")
            return {
                "expiring_patents": expiring[:20],  # Top 20
                "count": len(expiring),
                "by_assignee": by_assignee
            }

        except Exception as e:
            logger.error(f"Expiring patent analysis failed: {e}")
            return {"expiring_patents": [], "count": 0}

    def assess_freedom_to_operate(
        self,
        patents: List[Dict[str, Any]],
        keywords: str
    ) -> Dict[str, Any]:
        """
        Assess Freedom-to-Operate (FTO) based on patent landscape

        Args:
            patents: List of patents
            keywords: Technology keywords

        Returns:
            FTO assessment
        """
        logger.info("Assessing Freedom-to-Operate (FTO)")

        if not patents:
            return {
                "risk_level": "Unknown",
                "analysis": "No patent data available for FTO assessment",
                "recommendations": []
            }

        # Count active patents (potential blocking patents)
        current_year = datetime.now().year
        active_blocking_patents = [
            p for p in patents
            if p.get('patent_date', '')[:4].isdigit()
            and current_year - int(p.get('patent_date', '')[:4]) < 20
        ]

        # Identify key patent holders
        assignees = []
        for patent in active_blocking_patents:
            for assignee in patent.get('assignees', []):
                org = assignee.get('assignee_organization', '')
                if org:
                    assignees.append(org)

        dominant_players = Counter(assignees).most_common(5)

        # Assess risk based on active patents and concentration
        active_count = len(active_blocking_patents)
        if active_count < 10:
            risk_level = "Low"
            risk_description = "Limited patent coverage in this space"
        elif active_count < 50:
            risk_level = "Medium"
            risk_description = "Moderate patent coverage; careful FTO required"
        else:
            risk_level = "High"
            risk_description = "Dense patent coverage; significant FTO challenges"

        # Check for concentration (monopoly risk)
        if dominant_players and dominant_players[0][1] > active_count * 0.5:
            risk_level = "High"
            risk_description += f"; Dominated by {dominant_players[0][0]}"

        recommendations = []
        if risk_level in ["Medium", "High"]:
            recommendations.append("Conduct detailed FTO analysis with patent counsel")
            recommendations.append("Consider design-around strategies")
            recommendations.append("Evaluate licensing opportunities")

        if dominant_players:
            top_player = dominant_players[0][0]
            recommendations.append(f"Engage with {top_player} for potential licensing")

        fto_assessment = {
            "risk_level": risk_level,
            "analysis": risk_description,
            "active_blocking_patents": active_count,
            "total_patents_analyzed": len(patents),
            "dominant_players": [
                {"organization": org, "patent_count": count}
                for org, count in dominant_players
            ],
            "recommendations": recommendations
        }

        logger.info(f"FTO Assessment: {risk_level} risk")
        return fto_assessment

    def identify_white_space(
        self,
        patents: List[Dict[str, Any]],
        keywords: str
    ) -> List[str]:
        """
        Identify white space opportunities (areas with low patent coverage)

        Args:
            patents: List of patents
            keywords: Technology keywords

        Returns:
            List of white space opportunities
        """
        logger.info("Identifying white space opportunities")

        # Domain knowledge: common innovation areas in pharma
        innovation_areas = [
            "oral delivery formulations",
            "extended-release formulations",
            "once-monthly administration",
            "combination therapies",
            "biosimilar development",
            "gene therapy delivery",
            "personalized medicine",
            "biomarker-driven therapy",
            "digital therapeutics integration",
            "novel drug-device combinations"
        ]

        # Simple heuristic: Check which areas are underrepresented in patent titles/abstracts
        white_space = []
        for area in innovation_areas:
            # Count how many patents mention this area
            mentions = sum(
                1 for p in patents
                if area.lower() in p.get('patent_title', '').lower()
                or area.lower() in p.get('patent_abstract', '').lower()
            )

            # If fewer than 5% of patents mention this, it's potential white space
            if mentions < len(patents) * 0.05:
                white_space.append(area.title())

        logger.info(f"Identified {len(white_space)} white space opportunities")
        return white_space[:5]  # Top 5

    def assess_litigation_risk(
        self,
        patents: List[Dict[str, Any]]
    ) -> str:
        """
        Assess litigation risk based on patent landscape

        Args:
            patents: List of patents

        Returns:
            Risk level (Low/Medium/High)
        """
        # Simplified heuristic based on:
        # 1. High citation count = valuable patents = higher litigation risk
        # 2. Multiple assignees = competitive space = higher risk

        if not patents:
            return "Unknown"

        avg_citations = sum(
            p.get('citedby_patent_count', 0) for p in patents
        ) / len(patents)

        assignees = set()
        for patent in patents:
            for assignee in patent.get('assignees', []):
                org = assignee.get('assignee_organization', '')
                if org:
                    assignees.add(org)

        if avg_citations > 20 or len(assignees) > 10:
            return "High"
        elif avg_citations > 10 or len(assignees) > 5:
            return "Medium"
        else:
            return "Low"

    def generate_comprehensive_summary(
        self,
        patents: List[Dict[str, Any]],
        landscape: Dict[str, Any],
        fto_assessment: Dict[str, Any],
        expiring_analysis: Dict[str, Any],
        white_space: List[str],
        litigation_risk: str,
        keywords: str
    ) -> str:
        """
        Generate comprehensive patent intelligence summary using LLM

        Args:
            patents: Patent data
            landscape: Landscape analysis
            fto_assessment: FTO assessment
            expiring_analysis: Expiring patent analysis
            white_space: White space opportunities
            litigation_risk: Litigation risk level
            keywords: Search keywords

        Returns:
            Comprehensive summary
        """
        logger.info("Generating comprehensive patent intelligence summary")

        # Prepare patent data for LLM
        patent_summaries = []
        for i, patent in enumerate(patents[:50], 1):  # Top 50 patents
            assignees = [
                a.get('assignee_organization', 'Unknown')
                for a in patent.get('assignees', [])
            ]
            patent_summaries.append(
                f"{i}. {patent.get('patent_number', 'N/A')}: {patent.get('patent_title', 'N/A')}\n"
                f"   Assignee: {', '.join(assignees[:2]) if assignees else 'N/A'}\n"
                f"   Grant Date: {patent.get('patent_date', 'N/A')}\n"
                f"   Citations: {patent.get('citedby_patent_count', 0)}\n"
            )

        patents_text = "\n".join(patent_summaries)

        # Try Gemini first (better for long-form content)
        if self.gemini_api_key:
            summary = self._generate_with_gemini(
                keywords, landscape, fto_assessment, expiring_analysis,
                white_space, litigation_risk, patents_text
            )
            if summary and "Unable to generate" not in summary:
                return summary

        # Fallback to Groq
        if self.groq_api_key:
            summary = self._generate_with_groq(
                keywords, landscape, fto_assessment, expiring_analysis,
                white_space, litigation_risk, patents_text
            )
            if summary and "Unable to generate" not in summary:
                return summary

        # Final fallback: Structured summary
        return self._generate_structured_fallback(
            keywords, landscape, fto_assessment, expiring_analysis,
            white_space, litigation_risk
        )

    def _generate_with_gemini(
        self,
        keywords: str,
        landscape: Dict[str, Any],
        fto: Dict[str, Any],
        expiring: Dict[str, Any],
        white_space: List[str],
        litigation_risk: str,
        patents_text: str
    ) -> str:
        """Generate summary with Gemini"""
        logger.info("Generating summary with Gemini")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}

        prompt = f"""You are a patent intelligence analyst. Analyze the following patent landscape data and provide a comprehensive report.

Search Keywords: {keywords}
Total Patents: {landscape.get('total_patents', 0)}
Active Patents: {landscape.get('active_patents', 0)}

Key Players:
{chr(10).join(f"- {p['organization']}: {p['patent_count']} patents" for p in landscape.get('key_players', [])[:5])}

Freedom-to-Operate (FTO) Assessment:
Risk Level: {fto.get('risk_level', 'Unknown')}
Analysis: {fto.get('analysis', 'N/A')}
Recommendations: {', '.join(fto.get('recommendations', []))}

Patent Expiration Analysis:
Patents expiring in next 3 years: {expiring.get('count', 0)}

White Space Opportunities:
{', '.join(white_space) if white_space else 'None identified'}

Litigation Risk: {litigation_risk}

Top Patents:
{patents_text}

Provide a comprehensive analysis with the following sections:

1. EXECUTIVE SUMMARY
Brief overview of the patent landscape for {keywords}.

2. PATENT LANDSCAPE OVERVIEW
Analysis of total patents, key players, and market concentration.

3. FREEDOM-TO-OPERATE ANALYSIS
Detailed FTO assessment with risk factors and recommendations.

4. PATENT EXPIRATION CLIFF
Analysis of expiring patents and implications for generic entry.

5. WHITE SPACE OPPORTUNITIES
Areas with low patent coverage representing innovation opportunities.

6. KEY PATENTS AND TECHNOLOGIES
Analysis of most important patents and their technological contributions.

7. LITIGATION RISK ASSESSMENT
Evaluation of IP litigation risk in this space.

8. STRATEGIC RECOMMENDATIONS
Actionable IP strategy recommendations.

Use plain text format without markdown. Use UPPERCASE for section headers."""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8000,
                "topP": 0.95
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()

            if 'candidates' in result and len(result['candidates']) > 0:
                summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                logger.info(f"Generated summary with Gemini ({len(summary)} chars)")
                return summary
            else:
                logger.error("No candidates in Gemini response")
                return ""

        except Exception as e:
            logger.error(f"Gemini summary generation failed: {e}")
            return ""

    def _generate_with_groq(
        self,
        keywords: str,
        landscape: Dict[str, Any],
        fto: Dict[str, Any],
        expiring: Dict[str, Any],
        white_space: List[str],
        litigation_risk: str,
        patents_text: str
    ) -> str:
        """Generate summary with Groq"""
        logger.info("Generating summary with Groq")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"""Analyze this patent landscape and provide a comprehensive IP intelligence report for {keywords}.

Total Patents: {landscape.get('total_patents', 0)}
Active Patents: {landscape.get('active_patents', 0)}
Key Players: {', '.join(p['organization'] for p in landscape.get('key_players', [])[:5])}

FTO Risk: {fto.get('risk_level', 'Unknown')}
Litigation Risk: {litigation_risk}
Patents Expiring (3y): {expiring.get('count', 0)}
White Space: {', '.join(white_space[:3])}

Top Patents:
{patents_text[:2000]}

Provide comprehensive analysis with these sections:
1. EXECUTIVE SUMMARY
2. PATENT LANDSCAPE OVERVIEW
3. FREEDOM-TO-OPERATE ANALYSIS
4. PATENT EXPIRATION CLIFF
5. WHITE SPACE OPPORTUNITIES
6. KEY PATENTS
7. LITIGATION RISK
8. STRATEGIC RECOMMENDATIONS

Use plain text, UPPERCASE for headers."""

        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a patent intelligence analyst providing comprehensive IP landscape analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 6000
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            summary = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.info(f"Generated summary with Groq ({len(summary)} chars)")
            return summary or ""

        except Exception as e:
            logger.error(f"Groq summary generation failed: {e}")
            return ""

    def _generate_structured_fallback(
        self,
        keywords: str,
        landscape: Dict[str, Any],
        fto: Dict[str, Any],
        expiring: Dict[str, Any],
        white_space: List[str],
        litigation_risk: str
    ) -> str:
        """Generate structured fallback summary"""
        logger.info("Generating structured fallback summary")

        sections = []

        sections.append("PATENT INTELLIGENCE REPORT")
        sections.append("")
        sections.append("")

        sections.append("1. EXECUTIVE SUMMARY")
        sections.append("")
        sections.append(f"This report analyzes the patent landscape for {keywords}. ")
        sections.append(f"A total of {landscape.get('total_patents', 0)} patents were identified, ")
        sections.append(f"with {landscape.get('active_patents', 0)} currently active patents. ")
        sections.append(f"Freedom-to-Operate risk is assessed as {fto.get('risk_level', 'Unknown')}, ")
        sections.append(f"and litigation risk is {litigation_risk}.")
        sections.append("")
        sections.append("")

        sections.append("2. PATENT LANDSCAPE OVERVIEW")
        sections.append("")
        sections.append(f"Total Patents Identified: {landscape.get('total_patents', 0)}")
        sections.append(f"Active Patents: {landscape.get('active_patents', 0)}")
        sections.append("")
        sections.append("Key Players:")
        for player in landscape.get('key_players', [])[:5]:
            sections.append(f"  - {player['organization']}: {player['patent_count']} patents")
        sections.append("")
        sections.append("")

        sections.append("3. FREEDOM-TO-OPERATE ANALYSIS")
        sections.append("")
        sections.append(f"FTO Risk Level: {fto.get('risk_level', 'Unknown')}")
        sections.append(f"Analysis: {fto.get('analysis', 'No analysis available')}")
        sections.append("")
        sections.append("Recommendations:")
        for rec in fto.get('recommendations', []):
            sections.append(f"  - {rec}")
        sections.append("")
        sections.append("")

        sections.append("4. PATENT EXPIRATION CLIFF")
        sections.append("")
        sections.append(f"Patents expiring in next 3 years: {expiring.get('count', 0)}")
        sections.append("")
        if expiring.get('count', 0) > 0:
            sections.append("Patent expirations may create opportunities for generic entry and biosimilar development.")
        else:
            sections.append("Limited patent expirations expected in the near term.")
        sections.append("")
        sections.append("")

        sections.append("5. WHITE SPACE OPPORTUNITIES")
        sections.append("")
        if white_space:
            sections.append("Areas with low patent coverage representing innovation opportunities:")
            for area in white_space:
                sections.append(f"  - {area}")
        else:
            sections.append("Dense patent coverage; limited white space identified.")
        sections.append("")
        sections.append("")

        sections.append("6. LITIGATION RISK ASSESSMENT")
        sections.append("")
        sections.append(f"Litigation Risk Level: {litigation_risk}")
        sections.append("")
        sections.append("")

        sections.append("7. STRATEGIC RECOMMENDATIONS")
        sections.append("")
        sections.append("  - Conduct detailed patent-by-patent FTO analysis with IP counsel")
        sections.append("  - Monitor expiring patents for generic/biosimilar opportunities")
        sections.append("  - Explore white space areas for novel innovation")
        sections.append("  - Consider licensing agreements with dominant players")
        sections.append("  - Implement robust IP clearance processes before market entry")
        sections.append("")

        return "\n".join(sections)

    def process(self, user_query: str) -> Dict[str, Any]:
        """
        Main processing method for Patent Agent

        Args:
            user_query: User's patent query

        Returns:
            Comprehensive patent intelligence report
        """
        logger.info("="*50)
        logger.info(f"Starting Patent Agent processing for: '{user_query}'")
        logger.info("="*50)

        try:
            # Step 1: Extract keywords
            logger.info("Step 1/7: Extracting keywords")
            keywords = self.extract_keywords(user_query)

            # Step 2: Search patents
            logger.info("Step 2/7: Searching patents")
            patents = self.search_patents(keywords, limit=100)

            if not patents:
                logger.warning("No patents found")
                return {
                    "summary": f"No patents found for: {keywords}",
                    "comprehensive_summary": "Unable to generate patent intelligence report due to lack of patent data.",
                    "patents": [],
                    "landscape": {},
                    "fto_assessment": {"risk_level": "Unknown"},
                    "confidence_score": 0.0
                }

            # Step 3: Analyze landscape
            logger.info("Step 3/7: Analyzing patent landscape")
            landscape = self.analyze_patent_landscape(patents, keywords)

            # Step 4: Assess FTO
            logger.info("Step 4/7: Assessing Freedom-to-Operate")
            fto_assessment = self.assess_freedom_to_operate(patents, keywords)

            # Step 5: Analyze expiring patents
            logger.info("Step 5/7: Analyzing patent expirations")
            expiring_analysis = self.analyze_expiring_patents(keywords, years_from_now=3)

            # Step 6: Identify white space and assess litigation risk
            logger.info("Step 6/7: Identifying white space and litigation risk")
            white_space = self.identify_white_space(patents, keywords)
            litigation_risk = self.assess_litigation_risk(patents)

            # Step 7: Generate comprehensive summary
            logger.info("Step 7/7: Generating comprehensive summary")
            comprehensive_summary = self.generate_comprehensive_summary(
                patents=patents,
                landscape=landscape,
                fto_assessment=fto_assessment,
                expiring_analysis=expiring_analysis,
                white_space=white_space,
                litigation_risk=litigation_risk,
                keywords=keywords
            )

            # Calculate confidence score
            confidence_score = 0.85  # Default confidence for USPTO data
            if self.confidence_scorer and patents:
                try:
                    # Simple confidence based on data completeness
                    data_completeness = min(len(patents) / 50, 1.0)  # Max at 50 patents
                    confidence_score = 0.7 + (0.2 * data_completeness)
                except Exception as e:
                    logger.warning(f"Confidence scoring failed: {e}")

            # Prepare response
            basic_summary = (
                f"Found {len(patents)} patents for {keywords}. "
                f"Key players: {', '.join(p['organization'] for p in landscape.get('key_players', [])[:3])}. "
                f"FTO risk: {fto_assessment.get('risk_level', 'Unknown')}. "
                f"Litigation risk: {litigation_risk}."
            )

            logger.info("="*50)
            logger.info("Patent Agent processing completed successfully")
            logger.info("="*50)

            return {
                "summary": basic_summary,
                "comprehensive_summary": comprehensive_summary,
                "patents": patents[:50],  # Return top 50 patents
                "landscape": landscape,
                "fto_assessment": fto_assessment,
                "expiring_analysis": expiring_analysis,
                "white_space": white_space,
                "litigation_risk": litigation_risk,
                "confidence_score": confidence_score
            }

        except Exception as e:
            logger.error(f"Patent Agent processing failed: {e}", exc_info=True)
            return {
                "summary": f"Patent analysis failed: {str(e)}",
                "comprehensive_summary": f"Unable to generate patent intelligence report due to error: {str(e)}",
                "patents": [],
                "landscape": {},
                "fto_assessment": {"risk_level": "Unknown"},
                "confidence_score": 0.0
            }
