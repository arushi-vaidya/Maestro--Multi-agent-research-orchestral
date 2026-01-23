# Enhanced Knowledge Graph Mock Data (In-Memory)

from typing import List, Dict, Any, Optional

MOCK_KNOWLEDGE_GRAPH: Dict[str, Any] = {
    "nodes": {
        "drugs": [
            {"id": "drug_1", "name": "Semaglutide", "type": "GLP-1 agonist", "umls": "C2352009"},
            {"id": "drug_2", "name": "Metformin", "type": "Biguanide", "umls": "C0025598"}
        ],
        "diseases": [
            {"id": "disease_1", "name": "Type 2 Diabetes", "umls": "C0011860"},
            {"id": "disease_2", "name": "Colorectal Cancer", "umls": "C0009402"}
        ],
        "companies": [
            {"id": "company_1", "name": "Novo Nordisk", "country": "Denmark"}
        ]
    },
    "edges": [
        {
            "source": "drug_1",
            "target": "disease_1",
            "relation": "TREATS",
            "evidence_count": 45,
            "confidence": 0.95,
            "last_updated": "2024-03-15"
        },
        {
            "source": "drug_2",
            "target": "disease_2",
            "relation": "REPURPOSED_FOR",
            "evidence_count": 8,
            "confidence": 0.72,
            "last_updated": "2023-11-20"
        }
    ]
}

def query_graph(drug: Optional[str] = None, disease: Optional[str] = None) -> List[Dict[str, Any]]:
    """Query mock graph - returns matching triples"""
    results = []
    drug_id = None
    disease_id = None
    # Find node ids if names are given
    if drug:
        for d in MOCK_KNOWLEDGE_GRAPH["nodes"]["drugs"]:
            if d["name"].lower() == drug.lower():
                drug_id = d["id"]
                break
    if disease:
        for dis in MOCK_KNOWLEDGE_GRAPH["nodes"]["diseases"]:
            if dis["name"].lower() == disease.lower():
                disease_id = dis["id"]
                break
    for edge in MOCK_KNOWLEDGE_GRAPH["edges"]:
        if drug_id and edge["source"] != drug_id:
            continue
        if disease_id and edge["target"] != disease_id:
            continue
        results.append(edge)
    return results
