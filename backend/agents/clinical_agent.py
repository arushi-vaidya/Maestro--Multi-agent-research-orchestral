import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalAgent:
    def __init__(self):
        self.groq_api_key = GROQ_API_KEY
        logger.info("ClinicalAgent initialized")

    def extract_keywords(self, query: str) -> str:
        logger.info(f"Starting keyword extraction for query: '{query}'")
        # Call Groq API to extract keywords
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical keyword extractor for clinical trials search. Extract ONLY medical, clinical, and therapeutic keywords from the query. EXCLUDE business terms like 'market', 'opportunity', 'analysis', 'revenue', etc. Focus on: diseases, conditions, drugs, therapeutic areas, treatments. Return only the medical keywords separated by commas."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.3,
            "max_tokens": 100
        }
        try:
            logger.info("Sending request to Groq API for keyword extraction")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            keywords = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.info(f"Extracted keywords: '{keywords}'")
            return keywords or query
        except Exception as e:
            logger.error(f"Groq keyword extraction failed: {e}")
            print(f"Groq keyword extraction failed: {e}")
            logger.info(f"Falling back to original query: '{query}'")
            return query

    def search_trials(self, keywords: str, page_size: int = 1000) -> dict:
        logger.info(f"Searching clinical trials for keywords: '{keywords}' (page_size={page_size})")
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {"query.term": keywords, "pageSize": page_size}
        logger.info(f"Making request to ClinicalTrials.gov API: {url}")
        response = requests.get(url, params=params, timeout=100)
        response.raise_for_status()
        data = response.json()
        trial_count = len(data.get('studies', []))
        logger.info(f"Successfully retrieved {trial_count} clinical trials")
        return data

    def get_trial_details(self, nct_id: str) -> dict:
        logger.info(f"Fetching detailed information for trial: {nct_id}")
        url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully retrieved details for trial: {nct_id}")
        return response.json()

    def generate_comprehensive_summary(self, trials_data: dict, keywords: str) -> str:
        """Generate a comprehensive summary of all trials using Groq"""
        logger.info("Starting comprehensive summary generation")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        
        # Prepare a concise representation of the trials data
        trials_list = []
        total_trials = len(trials_data.get('studies', []))
        logger.info(f"Processing {total_trials} trials for summary")
        
        for study in trials_data.get('studies', [])[:50]:  # Limit to first 50 to avoid token limits
            try:
                nct_id = study['protocolSection']['identificationModule']['nctId']
                title = study['protocolSection']['identificationModule']['briefTitle']
                status = study['protocolSection']['statusModule'].get('overallStatus', 'Unknown')
                trials_list.append(f"NCT ID: {nct_id}, Title: {title}, Status: {status}")
            except KeyError:
                continue
        
        logger.info(f"Prepared {len(trials_list)} trial summaries for analysis")
        trials_text = "\n".join(trials_list)
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical research analyst. Provide a comprehensive, professional summary of clinical trials data. Include key insights about trial statuses, common themes, and notable findings. Keep it concise but informative."
                },
                {
                    "role": "user",
                    "content": f"Search keywords: {keywords}\n\nTotal trials found: {total_trials}\n\nSample of trials (showing up to 50):\n{trials_text}\n\nProvide a comprehensive summary of these clinical trials."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            logger.info("Sending request to Groq API for summary generation")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            summary = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.info("Successfully generated comprehensive summary")
            return summary or f"Found {total_trials} clinical trials related to {keywords}."
        except Exception as e:
            logger.error(f"Groq summary generation failed: {e}")
            print(f"Groq summary generation failed: {e}")
            fallback_summary = f"Found {total_trials} clinical trials related to {keywords}. Unable to generate detailed summary."
            logger.info("Using fallback summary")
            return fallback_summary

    def process(self, user_query: str) -> dict:
        logger.info("="*50)
        logger.info(f"Starting ClinicalAgent process for query: '{user_query}'")
        logger.info("="*50)
        
        # Step 1: Extract keywords
        logger.info("Step 1/4: Extracting keywords")
        keywords = self.extract_keywords(user_query)
        
        # Step 2: Search trials
        logger.info("Step 2/4: Searching clinical trials")
        trials_result = self.search_trials(keywords)
        
        # Step 3: Generate comprehensive summary
        logger.info("Step 3/4: Generating comprehensive summary")
        comprehensive_summary = self.generate_comprehensive_summary(trials_result, keywords)
        
        # Step 4: Prepare response
        logger.info("Step 4/4: Preparing final response")
        basic_summary = f"Found {len(trials_result.get('studies', []))} trials for: {keywords}"
        
        trials = []
        for study in trials_result.get('studies', []):
            nct_id = study['protocolSection']['identificationModule']['nctId']
            title = study['protocolSection']['identificationModule']['briefTitle']
            trials.append({"nct_id": nct_id, "title": title})
        
        logger.info(f"Prepared {len(trials)} trial entries")
        logger.info("="*50)
        logger.info("ClinicalAgent process completed successfully")
        logger.info("="*50)
        
        return {
            "summary": basic_summary,
            "comprehensive_summary": comprehensive_summary,
            "trials": trials,
            "raw": trials_result
        }

    def get_trial_summary(self, nct_id: str) -> dict:
        logger.info(f"Getting trial summary for NCT ID: {nct_id}")
        details = self.get_trial_details(nct_id)
        id_mod = details['protocolSection']['identificationModule']
        title = id_mod.get('briefTitle', 'N/A')
        summary = details['protocolSection'].get('descriptionModule', {}).get('briefSummary', 'No summary available.')
        logger.info(f"Successfully retrieved trial summary for: {nct_id}")
        return {
            "nct_id": nct_id,
            "title": title,
            "summary": summary
        }