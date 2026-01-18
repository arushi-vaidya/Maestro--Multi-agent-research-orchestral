"""
Test Fixtures for Agent Testing
Provides mock data and utilities for testing agents offline
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List


# ============================================================================
# CLINICAL AGENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_clinical_trials_response():
    """Mock response from ClinicalTrials.gov API"""
    return {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT12345678",
                        "briefTitle": "Phase 3 Study of GLP-1 Agonist in Type 2 Diabetes",
                        "officialTitle": "A Randomized, Double-Blind Study of GLP-1 Agonist"
                    },
                    "statusModule": {
                        "overallStatus": "RECRUITING"
                    },
                    "designModule": {
                        "phases": ["PHASE3"],
                        "studyType": "INTERVENTIONAL"
                    },
                    "armsInterventionsModule": {
                        "interventions": [
                            {"name": "GLP-1 Agonist", "type": "DRUG"}
                        ]
                    },
                    "conditionsModule": {
                        "conditions": ["Type 2 Diabetes Mellitus"]
                    },
                    "descriptionModule": {
                        "briefSummary": "This is a Phase 3 trial evaluating efficacy and safety."
                    }
                }
            },
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT87654321",
                        "briefTitle": "Phase 2 GLP-1 Study",
                        "officialTitle": "Phase 2 Study"
                    },
                    "statusModule": {
                        "overallStatus": "COMPLETED"
                    },
                    "designModule": {
                        "phases": ["PHASE2"],
                        "studyType": "INTERVENTIONAL"
                    },
                    "armsInterventionsModule": {
                        "interventions": [
                            {"name": "Placebo", "type": "OTHER"}
                        ]
                    },
                    "conditionsModule": {
                        "conditions": ["Diabetes"]
                    },
                    "descriptionModule": {
                        "briefSummary": "Phase 2 trial summary."
                    }
                }
            }
        ],
        "totalCount": 2
    }


@pytest.fixture
def mock_groq_keyword_response():
    """Mock Groq API response for keyword extraction"""
    return {
        "choices": [
            {
                "message": {
                    "content": "GLP-1 diabetes"
                }
            }
        ]
    }


@pytest.fixture
def mock_gemini_summary_response():
    """Mock Gemini API response for summary generation"""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """COMPREHENSIVE CLINICAL TRIALS ANALYSIS

1. OVERVIEW

Total Trials Found: 2
Search Keywords: GLP-1 diabetes
Data Source: ClinicalTrials.gov Database

2. THERAPEUTIC AREAS AND CONDITIONS

Primary Conditions Being Studied:
- Type 2 Diabetes Mellitus: 2 trials

3. INTERVENTION MECHANISMS AND APPROACHES

Intervention Types Being Investigated:
- DRUG: 1 trial
- OTHER: 1 trial

4. CLINICAL TRIAL PHASES AND DEVELOPMENT PIPELINE

Phase Distribution:
- PHASE3: 1 trial
- PHASE2: 1 trial

5. KEY FINDINGS AND PATTERNS

Trial Status Distribution:
- RECRUITING: 1 trial
- COMPLETED: 1 trial

6. METHODOLOGICAL APPROACHES

Study Design Types:
- INTERVENTIONAL: 2 trials

7. IMPLICATIONS FOR CLINICAL PRACTICE

The 2 trials identified represent significant research investment in GLP-1 diabetes.

8. SUMMARY AND CONCLUSIONS

This analysis identified 2 clinical trials related to GLP-1 diabetes."""
                        }
                    ]
                }
            }
        ]
    }


# ============================================================================
# PATENT AGENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_uspto_patents_response():
    """Mock response from USPTO PatentsView API"""
    return [
        {
            "patent_number": "US11234567B2",
            "patent_title": "GLP-1 Receptor Agonist Formulation",
            "patent_date": "2022-03-15",
            "patent_abstract": "Novel GLP-1 formulation for diabetes treatment",
            "assignees": [
                {
                    "assignee_organization": "Pharma Corp",
                    "assignee_type": "US Company"
                }
            ],
            "cpcs": [
                {
                    "cpc_section": "A61K",
                    "cpc_subsection": "A61K38"
                }
            ],
            "citedby_patent_count": 15
        },
        {
            "patent_number": "US10987654B1",
            "patent_title": "Method for Synthesizing GLP-1 Analogs",
            "patent_date": "2021-06-20",
            "patent_abstract": "Synthesis method for GLP-1 analogs",
            "assignees": [
                {
                    "assignee_organization": "BioTech Inc",
                    "assignee_type": "US Company"
                }
            ],
            "cpcs": [
                {
                    "cpc_section": "C07K",
                    "cpc_subsection": "C07K14"
                }
            ],
            "citedby_patent_count": 8
        }
    ]


# ============================================================================
# MARKET AGENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_web_search_results():
    """Mock web search results"""
    return [
        {
            "title": "GLP-1 Market Reaches $10B in 2024",
            "snippet": "The global GLP-1 market reached $10 billion in 2024, driven by increased adoption of diabetes treatments.",
            "url": "https://example.com/glp1-market-2024",
            "date": "2024-03-15",
            "domain": "example.com",
            "tier": 2
        },
        {
            "title": "Novo Nordisk Leads GLP-1 Market",
            "snippet": "Novo Nordisk maintains market leadership with 40% share in the GLP-1 segment.",
            "url": "https://pharmanews.com/novo-glp1",
            "date": "2024-02-10",
            "domain": "pharmanews.com",
            "tier": 1
        }
    ]


@pytest.fixture
def mock_rag_results():
    """Mock RAG retrieval results"""
    return [
        {
            "id": "doc_001",
            "content": "GLP-1 receptor agonists represent a $15B market opportunity with CAGR of 12% through 2028.",
            "metadata": {
                "title": "GLP-1 Market Analysis 2024",
                "date": "2024-01-01",
                "source": "Internal Research",
                "doc_type": "market_report"
            },
            "relevance_score": 0.92
        },
        {
            "id": "doc_002",
            "content": "Key players include Novo Nordisk, Eli Lilly, and AstraZeneca with combined 75% market share.",
            "metadata": {
                "title": "GLP-1 Competitive Landscape",
                "date": "2023-12-15",
                "source": "Internal Research",
                "doc_type": "competitive_analysis"
            },
            "relevance_score": 0.88
        }
    ]


@pytest.fixture
def mock_llm_synthesis_response():
    """Mock LLM response for market intelligence synthesis"""
    return """SUMMARY
The GLP-1 market reached $10 billion in 2024 with strong growth driven by diabetes treatments [WEB-1]. Market leader Novo Nordisk holds 40% market share [WEB-2].

MARKET OVERVIEW
The global GLP-1 receptor agonist market is valued at $15B with projected CAGR of 12% through 2028 [RAG-1]. Market expansion driven by increasing diabetes prevalence.

KEY METRICS
Total market size: $10B (2024) [WEB-1]
Market leader share: 40% (Novo Nordisk) [WEB-2]
Projected CAGR: 12% [RAG-1]

DRIVERS AND TRENDS
Increasing diabetes prevalence and obesity rates driving market growth. Novel once-weekly formulations expanding market access.

COMPETITIVE LANDSCAPE
Novo Nordisk leads with 40% share [WEB-2]. Top 3 players (Novo, Lilly, AstraZeneca) control 75% market [RAG-2].

RISKS AND OPPORTUNITIES
Patent expirations may create biosimilar opportunities. Pricing pressure from payers remains key challenge.

FUTURE OUTLOOK
Market expected to reach $15B+ by 2028 with 12% CAGR [RAG-1]. Oral formulations represent next innovation wave."""


# ============================================================================
# MASTER AGENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_clinical_agent_output():
    """Mock output from Clinical Agent"""
    return {
        "summary": "Found 2 trials for GLP-1 diabetes",
        "comprehensive_summary": "Comprehensive clinical trials analysis...",
        "trials": [
            {"nct_id": "NCT12345678", "title": "Phase 3 Study of GLP-1"},
            {"nct_id": "NCT87654321", "title": "Phase 2 GLP-1 Study"}
        ],
        "raw": {"studies": [], "totalCount": 2},
        "references": [
            {
                "agentId": "clinical",
                "type": "clinical_trial",
                "nct_id": "NCT12345678",
                "title": "Phase 3 Study of GLP-1",
                "url": "https://clinicaltrials.gov/study/NCT12345678"
            }
        ],
        "total_trials": 2
    }


@pytest.fixture
def mock_patent_agent_output():
    """Mock output from Patent Agent"""
    return {
        "summary": "Found 2 patents for GLP-1",
        "comprehensive_summary": "Patent intelligence report...",
        "patents": [],
        "landscape": {
            "total_patents": 2,
            "active_patents": 2,
            "key_players": [
                {"organization": "Pharma Corp", "patent_count": 1}
            ]
        },
        "fto_assessment": {
            "risk_level": "Medium",
            "analysis": "Moderate patent coverage"
        },
        "confidence_score": 0.85,
        "references": [
            {
                "agentId": "patent",
                "type": "patent",
                "patent_number": "US11234567B2",
                "title": "GLP-1 Receptor Agonist Formulation",
                "url": "https://patents.google.com/patent/US11234567B2"
            }
        ]
    }


@pytest.fixture
def mock_market_agent_output():
    """Mock output from Market Agent"""
    return {
        "agentId": "market",
        "query": "GLP-1 market size",
        "retrieval_used": {"web_search": True, "rag": True},
        "search_keywords": ["GLP-1 market", "diabetes drugs market"],
        "web_results": [
            {
                "title": "GLP-1 Market Reaches $10B",
                "snippet": "Market analysis...",
                "url": "https://example.com/article",
                "date": "2024-01-01"
            }
        ],
        "rag_results": [
            {
                "id": "doc_001",
                "content": "Market content...",
                "metadata": {"title": "Market Report", "date": "2024-01-01"}
            }
        ],
        "sections": {
            "summary": "GLP-1 market is valued at $10B...",
            "market_overview": "Market overview...",
            "key_metrics": "Key metrics...",
            "drivers_and_trends": "Drivers and trends...",
            "competitive_landscape": "Competitive landscape...",
            "risks_and_opportunities": "Risks and opportunities...",
            "future_outlook": "Future outlook..."
        },
        "confidence": {
            "score": 0.75,
            "breakdown": {},
            "explanation": "Good source coverage",
            "level": "high"
        },
        "confidence_score": 0.75,
        "sources": {
            "web": ["https://example.com/article"],
            "internal": ["doc_001"]
        }
    }


# ============================================================================
# AKGP FIXTURES
# ============================================================================

@pytest.fixture
def mock_agent_shaped_output_for_ingestion():
    """Mock agent output shaped for AKGP ingestion"""
    return {
        "agent_id": "clinical",
        "query": "GLP-1 diabetes trials",
        "timestamp": "2024-01-15T10:00:00Z",
        "entities": [
            {
                "name": "GLP-1",
                "type": "Drug",
                "properties": {
                    "mechanism": "GLP-1 receptor agonist",
                    "indication": "Type 2 Diabetes"
                }
            },
            {
                "name": "Type 2 Diabetes",
                "type": "Disease",
                "properties": {
                    "prevalence": "high"
                }
            }
        ],
        "relationships": [
            {
                "source": "GLP-1",
                "target": "Type 2 Diabetes",
                "type": "TREATS",
                "properties": {
                    "evidence_level": "high",
                    "phase": "Phase 3"
                }
            }
        ],
        "provenance": {
            "source": "clinical_agent",
            "source_url": "https://clinicaltrials.gov/study/NCT12345678",
            "confidence": 0.95,
            "timestamp": "2024-01-15T10:00:00Z"
        }
    }


@pytest.fixture
def mock_conflicting_agent_output():
    """Mock conflicting agent outputs for conflict detection"""
    return [
        {
            "agent_id": "market",
            "claim": "GLP-1 market size is $10B",
            "confidence": 0.8,
            "source": "market_report_2024.pdf"
        },
        {
            "agent_id": "clinical",
            "claim": "GLP-1 market size is $12B",
            "confidence": 0.7,
            "source": "clinical_database_2024"
        }
    ]


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def mock_requests_post():
    """Mock requests.post for API calls"""
    with patch('requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API calls"""
    with patch('requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def sample_queries():
    """Sample pharmaceutical queries for testing"""
    return {
        "market_only": "What is the GLP-1 market size in 2024?",
        "clinical_only": "Show me Phase 3 trials for GLP-1 agonists",
        "patent_only": "What is the patent landscape for GLP-1?",
        "multi_dimensional": "Provide freedom to operate analysis for GLP-1",
        "market_and_clinical": "GLP-1 market opportunity and clinical trial landscape",
        "all_agents": "Comprehensive GLP-1 analysis including FTO, market, and trials"
    }
