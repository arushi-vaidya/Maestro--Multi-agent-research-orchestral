# backend/data_sources/patent_scraper.py

import requests
from typing import List, Dict

class PatentAPI:
    BASE_URL = "https://api.patentsview.org/patents/query"
    
    def search(self, keyword: str) -> List[Dict]:
        query = {
            "q": {"_text_any": {"patent_abstract": keyword}},
            "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"]
        }
        response = requests.post(self.BASE_URL, json=query)
        return response.json().get("patents", [])