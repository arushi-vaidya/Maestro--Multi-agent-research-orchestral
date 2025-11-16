# backend/data_sources/clinicaltrials_api.py

import aiohttp
from typing import List, Dict

class ClinicalTrialsAPI:
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    
    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            params = {
                "query.term": query,
                "pageSize": max_results,
                "format": "json"
            }
            async with session.get(self.BASE_URL, params=params) as response:
                data = await response.json()
                return data.get("studies", [])