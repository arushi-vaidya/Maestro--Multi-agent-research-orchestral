# Mock In-Memory Document Store for RAG

from typing import List, Dict, Any

MOCK_INTERNAL_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "id": "doc_1",
        "title": "Q3 2024 Diabetes Portfolio Strategy",
        "content": """Our diabetes portfolio focuses on three pillars:\n1. Next-gen GLP-1 formulations with improved dosing\n2. Combination therapies targeting multiple pathways\n3. Digital therapeutics integration...""",
        "date": "2024-09-15",
        "author": "Strategy Team",
        "tags": ["diabetes", "strategy", "glp-1"]
    },
    {
        "id": "doc_2",
        "title": "Patent Analysis: GLP-1 Competitive Landscape",
        "content": """Key findings from patent analysis:\n- Novo Nordisk holds 34% of active patents\n- Major expiration cliff in 2026-2028...""",
        "date": "2024-08-20",
        "author": "IP Team",
        "tags": ["patents", "glp-1", "competitive-intel"]
    },
]
# Add 20-30 more mock documents
authors = ["Strategy Team", "IP Team", "R&D", "Market Access", "Medical Affairs"]
tags_pool = ["diabetes", "glp-1", "oncology", "alzheimer", "patents", "strategy", "competitive-intel", "clinical", "market"]
for i in range(3, 25):
    MOCK_INTERNAL_DOCUMENTS.append({
        "id": f"doc_{i}",
        "title": f"Internal Report {i}",
        "content": f"This is the content of internal report {i} covering {tags_pool[i % len(tags_pool)]} and related topics.",
        "date": f"2024-{(i%12)+1:02d}-{(i%28)+1:02d}",
        "author": authors[i % len(authors)],
        "tags": [tags_pool[i % len(tags_pool)], tags_pool[(i+1) % len(tags_pool)]]
    })

def search_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Simple keyword-based search initially"""
    query_lower = query.lower()
    scored_docs = []
    for doc in MOCK_INTERNAL_DOCUMENTS:
        score = 0
        # Score by tag match
        score += sum(1 for tag in doc["tags"] if tag in query_lower)
        # Score by content match
        score += doc["content"].lower().count(query_lower)
        # Score by title match
        score += doc["title"].lower().count(query_lower)
        if score > 0:
            scored_docs.append((score, doc))
    # Sort by score descending
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    return [doc for score, doc in scored_docs[:top_k]]
