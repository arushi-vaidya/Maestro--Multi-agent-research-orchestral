# backend/processing/data_harmonizer.py

from typing import Dict, List
import pandas as pd
from sentence_transformers import SentenceTransformer

class DataHarmonizer:
    """
    Unify heterogeneous data sources into common schema
    """
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('dmis-lab/biobert-base-cased-v1.1')
        self.unified_schema = {
            'entity': str,
            'entity_type': str,  # drug, disease, company, etc.
            'source': str,
            'data': dict,
            'embedding': list,
            'confidence': float
        }
    
    def harmonize(self, raw_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Convert multiple data sources into unified format
        """
        harmonized = []
        
        for source_name, df in raw_data.items():
            processed = self._process_source(source_name, df)
            harmonized.extend(processed)
        
        return pd.DataFrame(harmonized)
    
    def _process_source(self, source: str, df: pd.DataFrame) -> List[Dict]:
        """
        Source-specific processing logic
        """
        if source == 'iqvia':
            return self._process_iqvia(df)
        elif source == 'clinical_trials':
            return self._process_clinical(df)
        # Add more sources
        
    def _process_iqvia(self, df: pd.DataFrame) -> List[Dict]:
        """
        Transform IQVIA data to unified schema
        """
        records = []
        for _, row in df.iterrows():
            records.append({
                'entity': row.get('drug_name', 'Unknown'),
                'entity_type': 'market_data',
                'source': 'iqvia',
                'data': row.to_dict(),
                'embedding': self._generate_embedding(row.to_dict()),
                'confidence': 0.9
            })
        return records
    
    def _generate_embedding(self, data: Dict) -> List[float]:
        """
        Generate semantic embeddings for data
        """
        text = ' '.join([str(v) for v in data.values()])
        return self.embedding_model.encode(text).tolist()