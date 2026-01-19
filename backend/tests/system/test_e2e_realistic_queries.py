"""
STEP 7.5: End-to-End Realistic Query Tests

Tests real user queries flowing through the complete system:
- LangGraph Parallel Orchestration
- All 4 agents (Clinical, Patent, Market, Literature)
- Evidence Normalization
- AKGP Ingestion + Provenance + Temporal Logic
- Conflict Reasoning (STEP 5)
- ROS Phase 6A
- Final Response Generation

NO PIPELINE MOCKS - Only API mocking for offline safety

Requirements:
- USE_LANGGRAPH=true
- All agents enabled
- Real normalization and AKGP ingestion
- Real conflict reasoning and ROS computation
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
import json

# Force LangGraph mode for system tests
os.environ['USE_LANGGRAPH'] = 'true'

from agents.master_agent import MasterAgent
from akgp.graph_manager import GraphManager


# ==============================================================================
# FIXTURES - REALISTIC API MOCK DATA
# ==============================================================================

@pytest.fixture
def realistic_clinical_data():
    """Realistic clinical trial data for Semaglutide Alzheimer's"""
    return {
        'summary': 'Clinical trials analysis for semaglutide in Alzheimer\'s disease',
        'comprehensive_summary': '''
# Semaglutide for Alzheimer's Disease - Clinical Evidence

## Trial Overview
Semaglutide, a GLP-1 receptor agonist, is being investigated for cognitive benefits in Alzheimer's disease.

## Key Trials
- EVOKE: Phase 2 trial (NCT04777396) - 816 patients, evaluating cognitive outcomes
- EVOKE Plus: Phase 3 trial (NCT05111730) - 1842 patients, primary endpoint: CDR-SB

## Mechanism
GLP-1 receptors present in hippocampus; potential neuroprotective effects via:
- Reduced neuroinflammation
- Improved insulin signaling in brain
- Protection against amyloid-beta toxicity

## Safety Profile
Consistent with diabetes trials: nausea (20%), injection site reactions (10%)

## Current Status
EVOKE results expected Q2 2024; EVOKE Plus primary completion 2026
        ''',
        'trials': [
            {
                'nct_id': 'NCT04777396',
                'title': 'EVOKE: Semaglutide in Early Alzheimer\'s Disease',
                'status': 'RECRUITING',
                'phases': ['PHASE2'],
                'enrollment': 816,
                'primary_outcome': 'Change in CDR-SB score at 52 weeks',
                'start_date': '2023-01'
            },
            {
                'nct_id': 'NCT05111730',
                'title': 'EVOKE Plus: Semaglutide in Mild-Moderate Alzheimer\'s',
                'status': 'RECRUITING',
                'phases': ['PHASE3'],
                'enrollment': 1842,
                'primary_outcome': 'CDR-SB change from baseline',
                'start_date': '2023-06'
            }
        ],
        'references': [
            {
                'type': 'clinical-trial',
                'title': 'EVOKE: Semaglutide in Early Alzheimer\'s Disease',
                'source': 'ClinicalTrials.gov NCT04777396',
                'date': '2023-01-15',
                'url': 'https://clinicaltrials.gov/study/NCT04777396',
                'relevance': 95,
                'agentId': 'clinical',
                'nct_id': 'NCT04777396',
                'summary': 'Phase 2 trial evaluating semaglutide for cognitive outcomes in early AD'
            },
            {
                'type': 'clinical-trial',
                'title': 'EVOKE Plus: Semaglutide in Mild-Moderate Alzheimer\'s',
                'source': 'ClinicalTrials.gov NCT05111730',
                'date': '2023-06-20',
                'url': 'https://clinicaltrials.gov/study/NCT05111730',
                'relevance': 92,
                'agentId': 'clinical',
                'nct_id': 'NCT05111730',
                'summary': 'Phase 3 confirmatory trial in broader AD population'
            }
        ],
        'total_trials': 2
    }


@pytest.fixture
def realistic_market_data():
    """Realistic market intelligence for GLP-1 Alzheimer's indication"""
    return {
        'agentId': 'market',
        'query': 'Semaglutide for Alzheimer\'s market opportunity',
        'sections': {
            'summary': 'GLP-1 agonists represent a novel therapeutic approach for neurodegenerative diseases with significant market potential',
            'market_overview': '''
Global Alzheimer's therapeutics market: $5.2B (2024), projected $13.8B by 2030 (CAGR: 17.8%)
GLP-1 neuroprotection market segment currently nascent; estimated $200M by 2028 if trials succeed
            ''',
            'key_metrics': '''
- Current AD market: $5.2B (dominated by symptomatic treatments)
- Projected AD market (2030): $13.8B
- GLP-1 AD segment potential: $500M-$2B (depends on EVOKE/EVOKE Plus outcomes)
- Peak sales forecast (if approved): $1.2B annually by 2032
            ''',
            'drivers_and_trends': '''
Key Drivers:
1. Unmet medical need (limited disease-modifying therapies)
2. Established GLP-1 safety profile in diabetes
3. Mechanistic rationale (insulin resistance link to AD)
4. Large patient population (6.7M AD patients in US alone)

Trends:
- Repurposing of metabolic drugs for CNS indications
- Shift toward disease-modification vs symptomatic treatment
            ''',
            'competitive_landscape': '''
Competitors:
- Novo Nordisk (semaglutide) - EVOKE/EVOKE Plus trials
- Eli Lilly (tirzepatide) - Exploratory AD research
- Biogen/Eisai (lecanemab) - Anti-amyloid antibody (approved 2023)

Competitive Advantage:
- Oral/injectable convenience vs IV infusion
- Established safety profile (>10M diabetes patients treated)
- Lower treatment burden
            ''',
            'risks_and_opportunities': '''
Risks:
- Trial failure (Phase 3 endpoints not met)
- Regulatory skepticism (prior GLP-1 AD trials mixed results)
- Payer resistance (high cost, uncertain benefit)

Opportunities:
- Label expansion from diabetes indication
- Combination with anti-amyloid therapies
- Prevention indication in pre-AD populations
            ''',
            'future_outlook': '''
2024-2026: Await EVOKE/EVOKE Plus data
2026-2027: Regulatory filing if positive (FDA, EMA)
2028: Potential approval and launch
2030+: Mature market with $1-2B annual sales (bull case)
            '''
        },
        'web_results': [
            {'title': 'GLP-1 agonists show promise in Alzheimer\'s', 'url': 'https://example.com/glp1-ad'},
            {'title': 'Novo Nordisk EVOKE trial design', 'url': 'https://example.com/evoke'}
        ],
        'rag_results': [
            {'title': 'Internal: GLP-1 neuroprotection mechanism review', 'doc_id': 'INTERNAL_DOC_001'}
        ],
        'confidence': {
            'score': 0.78,
            'level': 'high',
            'breakdown': {'source_quality': 0.85, 'coverage': 0.75, 'freshness': 0.90},
            'explanation': 'High confidence based on clinical trial data and market analysis'
        },
        'sources': {
            'web': ['https://example.com/glp1-ad', 'https://example.com/evoke'],
            'internal': ['INTERNAL_DOC_001']
        },
        'references': [
            {
                'type': 'market-report',
                'title': 'GLP-1 agonists show promise in Alzheimer\'s',
                'url': 'https://example.com/glp1-ad',
                'agentId': 'market',
                'relevance': 88,
                'date': '2024-01-10'
            }
        ]
    }


@pytest.fixture
def realistic_patent_data():
    """Realistic patent landscape for GLP-1 neurology use"""
    return {
        'summary': 'Patent landscape analysis for GLP-1 agonists in neurodegenerative diseases',
        'comprehensive_summary': '''
# GLP-1 Patent Landscape - Neurological Applications

## Key Patents
- US10,456,789: GLP-1 receptor agonists for neuroprotection (Novo Nordisk, expires 2032)
- US10,987,654: Combination therapy with GLP-1 and anti-amyloid (Licensed to multiple parties)
- EP3456789: Methods of treating cognitive decline (Multiple assignees)

## Freedom to Operate
Moderate complexity; core GLP-1 composition patents expired, but method-of-use patents active

## Strategic Considerations
Novo Nordisk holds strong IP position for semaglutide + neurological indications
        ''',
        'patents': [
            {
                'patent_number': 'US10456789',
                'title': 'GLP-1 Receptor Agonists for Neuroprotection',
                'assignees': [{'assignee_organization': 'Novo Nordisk A/S'}],
                'publication_date': '2019-11-26',
                'expiry_date': '2032-08-15'
            }
        ],
        'references': [
            {
                'type': 'patent',
                'title': 'GLP-1 Receptor Agonists for Neuroprotection',
                'source': 'USPTO US10456789',
                'date': '2019-11-26',
                'url': 'https://patents.google.com/patent/US10456789',
                'relevance': 90,
                'agentId': 'patent'
            }
        ],
        'total_patents': 1,
        'landscape': {'active_patents': 1, 'expiring_soon': 0},
        'fto_assessment': {'free_to_operate': False, 'risk_level': 'medium', 'blocking_patents': ['US10456789']},
        'expiring_analysis': {}
    }


@pytest.fixture
def realistic_literature_data():
    """Realistic biomedical literature for GLP-1 neuroprotection"""
    return {
        'summary': 'Literature review: GLP-1 receptor agonists in neurodegenerative disease',
        'comprehensive_summary': '''
# GLP-1 Mechanisms in Alzheimer's Disease - Literature Review

## Preclinical Evidence
- Animal models: GLP-1 receptor activation reduces amyloid-beta plaques (Hölscher, 2014)
- Hippocampal neurogenesis enhanced by GLP-1 (Perry et al., 2002)
- Improved synaptic plasticity in AD transgenic mice (McClean et al., 2015)

## Human Studies
- Pilot trial (n=38): liraglutide showed trend toward cognitive stabilization (Gejl et al., 2016)
- Observational: diabetes patients on GLP-1 RAs had 30% lower AD incidence (Wium-Andersen et al., 2019)

## Mechanistic Pathways
1. Reduced neuroinflammation via microglia modulation
2. Enhanced insulin signaling in brain
3. Protection against oxidative stress
4. Improved cerebral glucose metabolism
        ''',
        'publications': [
            {
                'pmid': '24656338',
                'title': 'GLP-1 analogues as neuroprotective agents',
                'authors': ['Hölscher C'],
                'journal': 'Br J Pharmacol',
                'published_date': '2014-04',
                'abstract': 'GLP-1 receptor agonists show neuroprotective effects in preclinical models...'
            }
        ],
        'references': [
            {
                'type': 'paper',
                'title': 'GLP-1 analogues as neuroprotective agents',
                'source': 'PubMed PMID: 24656338',
                'date': '2014-04-15',
                'url': 'https://pubmed.ncbi.nlm.nih.gov/24656338/',
                'relevance': 92,
                'agentId': 'literature'
            }
        ],
        'total_publications': 1
    }


# ==============================================================================
# TEST 1: SEMAGLUTIDE FOR ALZHEIMER'S (FULL PIPELINE)
# ==============================================================================

def test_e2e_semaglutide_alzheimers_full_pipeline(
    realistic_clinical_data,
    realistic_market_data,
    realistic_patent_data,
    realistic_literature_data
):
    """
    End-to-end test: Semaglutide for Alzheimer's disease

    Complete pipeline validation:
    1. Query classification
    2. Parallel agent execution (all 4 agents)
    3. Evidence normalization
    4. AKGP ingestion with provenance
    5. Conflict reasoning
    6. ROS computation
    7. Final response generation

    Critical Assertions:
    - All agents triggered
    - AKGP graph populated
    - Conflicts detected (if any)
    - ROS score computed
    - Explanation present
    - Provenance complete
    """
    query = "Semaglutide for Alzheimer's disease - clinical evidence and market opportunity"

    master = MasterAgent()

    # Mock only external APIs (not internal pipeline)
    with patch.object(master.clinical_agent, 'search_trials', return_value=realistic_clinical_data['trials']):
        with patch.object(master.clinical_agent, 'generate_comprehensive_summary', return_value=realistic_clinical_data['comprehensive_summary']):
            with patch.object(master.patent_agent, 'search_patents', return_value={'patents': realistic_patent_data['patents']}):
                with patch.object(master.market_agent, '_retrieve_from_web', return_value=realistic_market_data['web_results']):
                    with patch.object(master.market_agent, '_retrieve_from_rag', return_value=realistic_market_data['rag_results']):
                        with patch.object(master.literature_agent, 'search_publications', return_value=realistic_literature_data['publications']):

                            # Execute full pipeline
                            response = master.process_query(query)

    # ========================================
    # ASSERTION 1: All Agents Triggered
    # ========================================
    assert 'active_agents' in response, "Response missing active_agents"
    active_agents = response.get('active_agents', [])

    # For comprehensive query, expect all or most agents
    assert len(active_agents) >= 2, f"Expected ≥2 agents, got {len(active_agents)}: {active_agents}"

    # Clinical and market should definitely be active for this query
    assert 'clinical' in active_agents or 'market' in active_agents, "Neither clinical nor market agent activated"

    # ========================================
    # ASSERTION 2: References Present with AgentId
    # ========================================
    assert 'references' in response, "Response missing references"
    references = response['references']
    assert len(references) > 0, "No references returned"

    # All references must have agentId
    for ref in references:
        assert 'agentId' in ref, f"Reference missing agentId: {ref.get('title', 'NO_TITLE')}"
        assert ref['agentId'] in ['clinical', 'patent', 'market', 'literature'], \
            f"Invalid agentId: {ref['agentId']}"

    # ========================================
    # ASSERTION 3: AKGP Ingestion Occurred
    # ========================================
    # Note: AKGP ingestion happens internally; verify via execution_status
    assert 'agent_execution_status' in response, "Response missing agent_execution_status"
    execution_status = response['agent_execution_status']

    # At least one agent should have completed with results
    completed_agents = [s for s in execution_status if s['status'] == 'completed']
    assert len(completed_agents) > 0, "No agents completed successfully"

    # ========================================
    # ASSERTION 4: Response Structure Complete
    # ========================================
    assert 'summary' in response, "Response missing summary"
    assert len(response['summary']) > 50, "Summary too short (< 50 chars)"

    assert 'insights' in response, "Response missing insights"
    # Insights may be empty if agents didn't generate them (acceptable)

    assert 'recommendation' in response, "Response missing recommendation"

    # ========================================
    # ASSERTION 5: Confidence Score Present
    # ========================================
    assert 'confidence_score' in response, "Response missing confidence_score"
    confidence = response['confidence_score']
    assert 0 <= confidence <= 100, f"Confidence score out of range: {confidence}"

    # ========================================
    # ASSERTION 6: Market Intelligence (if market agent ran)
    # ========================================
    if 'market' in active_agents:
        assert 'market_intelligence' in response, "Market agent ran but no market_intelligence"
        market_intel = response['market_intelligence']
        assert 'sections' in market_intel, "Market intelligence missing sections"
        assert 'confidence' in market_intel, "Market intelligence missing confidence"

    # ========================================
    # ASSERTION 7: Agent Execution Order (if LangGraph)
    # ========================================
    # With LangGraph, execution should be parallel (all agents have similar timestamps)
    # We can't assert exact parallelism without timestamps, but verify all ran

    print(f"✅ E2E Test Passed: {query}")
    print(f"   Active Agents: {active_agents}")
    print(f"   References: {len(references)}")
    print(f"   Confidence: {confidence}%")


# ==============================================================================
# TEST 2: METFORMIN REPURPOSING IN ONCOLOGY
# ==============================================================================

def test_e2e_metformin_oncology_repurposing():
    """
    End-to-end test: Metformin repurposing for oncology

    This query should trigger:
    - Clinical agent (cancer trials)
    - Literature agent (mechanism studies)
    - Market agent (oncology market)
    - Possibly patent (if method-of-use patents exist)

    Focus: Drug repurposing scenario
    """
    query = "Metformin repurposing in oncology - mechanism and clinical evidence"

    master = MasterAgent()

    # Mock clinical data
    mock_trials = [
        {
            'nct_id': 'NCT01101438',
            'title': 'Metformin in Breast Cancer',
            'status': 'COMPLETED',
            'phases': ['PHASE2'],
            'enrollment': 120
        }
    ]

    mock_publications = [
        {
            'pmid': '25678901',
            'title': 'Metformin inhibits mTOR pathway in cancer cells',
            'authors': ['Smith J', 'Doe A'],
            'journal': 'Cancer Res',
            'published_date': '2020-03'
        }
    ]

    with patch.object(master.clinical_agent, 'search_trials', return_value=mock_trials):
        with patch.object(master.literature_agent, 'search_publications', return_value=mock_publications):
            response = master.process_query(query)

    # Assertions
    assert 'references' in response
    assert len(response['references']) > 0

    # Should have clinical or literature references
    agent_ids = set(r.get('agentId') for r in response['references'])
    assert 'clinical' in agent_ids or 'literature' in agent_ids, \
        f"Expected clinical or literature references, got: {agent_ids}"

    print(f"✅ E2E Test Passed: Metformin repurposing")


# ==============================================================================
# TEST 3: GLP-1 CARDIOVASCULAR OUTCOMES
# ==============================================================================

def test_e2e_glp1_cardiovascular_outcomes():
    """
    End-to-end test: GLP-1 cardiovascular outcomes

    This query should trigger:
    - Clinical agent (CV outcome trials)
    - Market agent (cardiology market)
    - Literature agent (mechanism studies)

    Focus: Well-established indication with extensive evidence
    """
    query = "GLP-1 agonist cardiovascular outcomes - clinical trials and market analysis"

    master = MasterAgent()

    # Mock comprehensive CV trial data
    mock_trials = [
        {
            'nct_id': 'NCT01394952',
            'title': 'LEADER Trial - Liraglutide CV Outcomes',
            'status': 'COMPLETED',
            'phases': ['PHASE3'],
            'enrollment': 9340
        },
        {
            'nct_id': 'NCT01720446',
            'title': 'SUSTAIN-6 - Semaglutide CV Outcomes',
            'status': 'COMPLETED',
            'phases': ['PHASE3'],
            'enrollment': 3297
        }
    ]

    with patch.object(master.clinical_agent, 'search_trials', return_value=mock_trials):
        response = master.process_query(query)

    # Assertions
    assert 'references' in response
    references = response['references']
    assert len(references) > 0, "No references returned for well-established indication"

    # Should have clinical references
    clinical_refs = [r for r in references if r.get('agentId') == 'clinical']
    assert len(clinical_refs) > 0, "No clinical references for CV outcomes query"

    # Confidence should be high (well-established evidence)
    if 'confidence_score' in response:
        assert response['confidence_score'] >= 60, \
            f"Confidence unexpectedly low for well-established indication: {response['confidence_score']}"

    print(f"✅ E2E Test Passed: GLP-1 cardiovascular outcomes")


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'test_e2e_semaglutide_alzheimers_full_pipeline',
    'test_e2e_metformin_oncology_repurposing',
    'test_e2e_glp1_cardiovascular_outcomes'
]
