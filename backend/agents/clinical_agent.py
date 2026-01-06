import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalAgent:
    def __init__(self):
        self.groq_api_key = GROQ_API_KEY
        self.gemini_api_key = GEMINI_API_KEY
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

    def search_trials(self, keywords: str, page_size: int = 100000) -> dict:
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
        """Generate a comprehensive, detailed summary of all trials suitable for literature review"""
        logger.info("Starting comprehensive summary generation")
        
        # Prepare a detailed representation of the trials data
        trials_list = []
        total_trials = len(trials_data.get('studies', []))
        logger.info(f"Processing {total_trials} trials for summary")
        
        for study in trials_data.get('studies', [])[:100]:  # Process up to 100 trials for comprehensive analysis
            try:
                protocol = study['protocolSection']
                id_module = protocol['identificationModule']
                status_module = protocol['statusModule']
                
                nct_id = id_module['nctId']
                title = id_module['briefTitle']
                official_title = id_module.get('officialTitle', '')
                status = status_module.get('overallStatus', 'Unknown')
                
                # Extract additional details
                design_module = protocol.get('designModule', {})
                phases = design_module.get('phases', [])
                study_type = design_module.get('studyType', 'Unknown')
                
                # Get intervention details
                arms_module = protocol.get('armsInterventionsModule', {})
                interventions = arms_module.get('interventions', [])
                intervention_names = [i.get('name', '') for i in interventions[:3]]
                
                # Get condition/disease
                conditions_module = protocol.get('conditionsModule', {})
                conditions = conditions_module.get('conditions', [])
                
                # Get description if available
                desc_module = protocol.get('descriptionModule', {})
                brief_summary = desc_module.get('briefSummary', '')
                
                trial_info = {
                    'nct_id': nct_id,
                    'title': title,
                    'official_title': official_title,
                    'status': status,
                    'phases': ', '.join(phases) if phases else 'N/A',
                    'study_type': study_type,
                    'conditions': ', '.join(conditions[:3]) if conditions else 'N/A',
                    'interventions': ', '.join(intervention_names) if intervention_names else 'N/A',
                    'summary': brief_summary[:200] + '...' if len(brief_summary) > 200 else brief_summary
                }
                
                trial_entry = f"""
Trial {nct_id}:
- Title: {title}
- Status: {status}
- Phase: {trial_info['phases']}
- Study Type: {study_type}
- Conditions: {trial_info['conditions']}
- Interventions: {trial_info['interventions']}
- Summary: {trial_info['summary']}
"""
                trials_list.append(trial_entry)
            except KeyError as e:
                logger.warning(f"Skipping trial due to missing data: {e}")
                continue
        
        logger.info(f"Prepared {len(trials_list)} detailed trial summaries for analysis")
        trials_text = "\n".join(trials_list)
        
        # Try Gemini first (better for long-form content), then fall back to Groq, then structured fallback
        if self.gemini_api_key:
            summary = self._generate_with_gemini(keywords, total_trials, trials_text, trials_data)
            if summary and "Unable to generate detailed summary" not in summary:
                return summary
            logger.warning("Gemini generation failed, falling back to Groq")
        
        summary = self._generate_with_groq(keywords, total_trials, trials_text, trials_data)
        if summary and "Unable to generate detailed summary" not in summary:
            return summary
        
        # Final fallback: Generate structured summary from trial data
        logger.warning("All AI generation failed, creating structured summary from trial data")
        return self._generate_structured_fallback(keywords, trials_data)
    
    def _format_summary(self, summary: str) -> str:
        """Post-process summary to remove markdown formatting and ensure proper formatting"""
        # Remove all markdown formatting characters
        summary = summary.replace('##', '')
        summary = summary.replace('**', '')
        summary = summary.replace('__', '')
        summary = summary.replace('*', '')
        summary = summary.replace('_', '')
        summary = summary.replace('`', '')
        # Remove bullet points
        summary = summary.replace('- ', '')
        summary = summary.replace('• ', '')
        # Clean up excessive blank lines (more than 3)
        while '\n\n\n\n' in summary:
            summary = summary.replace('\n\n\n\n', '\n\n\n')
        return summary.strip()
    
    def _generate_structured_fallback(self, keywords: str, trials_data: dict) -> str:
        """Generate a structured summary directly from trial data when AI APIs fail"""
        logger.info("Generating structured fallback summary from trial data")
        
        studies = trials_data.get('studies', [])
        total_trials = len(studies)
        
        # Analyze trial data
        phases = {}
        conditions = {}
        statuses = {}
        interventions = {}
        study_types = {}
        
        for study in studies:
            try:
                protocol = study['protocolSection']
                
                # Count phases
                design = protocol.get('designModule', {})
                for phase in design.get('phases', []):
                    phases[phase] = phases.get(phase, 0) + 1
                
                # Count conditions
                conds = protocol.get('conditionsModule', {}).get('conditions', [])
                for cond in conds[:2]:
                    conditions[cond] = conditions.get(cond, 0) + 1
                
                # Count statuses
                status = protocol.get('statusModule', {}).get('overallStatus', 'Unknown')
                statuses[status] = statuses.get(status, 0) + 1
                
                # Count interventions
                arms = protocol.get('armsInterventionsModule', {})
                for intervention in arms.get('interventions', [])[:2]:
                    int_type = intervention.get('type', 'Unknown')
                    interventions[int_type] = interventions.get(int_type, 0) + 1
                
                # Count study types
                st = design.get('studyType', 'Unknown')
                study_types[st] = study_types.get(st, 0) + 1
                
            except (KeyError, TypeError) as e:
                logger.warning(f"Error processing trial for stats: {e}")
                continue
        
        # Build comprehensive structured summary
        summary_parts = []
        
        summary_parts.append("COMPREHENSIVE CLINICAL TRIALS ANALYSIS")
        summary_parts.append("")
        summary_parts.append("")
        
        # 1. Overview
        summary_parts.append("1. OVERVIEW")
        summary_parts.append("")
        summary_parts.append(f"* Total Clinical Trials Found: {total_trials}")
        summary_parts.append(f"* Search Keywords: {keywords}")
        summary_parts.append(f"* Data Source: ClinicalTrials.gov Database")
        summary_parts.append("")
        summary_parts.append("This analysis encompasses clinical trials focused on " + keywords + 
                           f", representing current research efforts and therapeutic development in this area.")
        summary_parts.append("")
        summary_parts.append("")
        
        # 2. Therapeutic Areas
        summary_parts.append("2. THERAPEUTIC AREAS AND CONDITIONS")
        summary_parts.append("")
        if conditions:
            summary_parts.append("* Primary Conditions Being Studied:")
            for cond, count in sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:10]:
                summary_parts.append(f"  - {cond}: {count} trial(s)")
        else:
            summary_parts.append("* Condition data not fully available in retrieved trials")
        summary_parts.append("")
        summary_parts.append("")
        
        # 3. Intervention Approaches
        summary_parts.append("3. INTERVENTION MECHANISMS AND APPROACHES")
        summary_parts.append("")
        if interventions:
            summary_parts.append("* Intervention Types Being Investigated:")
            for int_type, count in sorted(interventions.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"  - {int_type}: {count} trial(s)")
        summary_parts.append("")
        summary_parts.append(f"The trials employ diverse therapeutic modalities targeting {keywords}, " +
                           "including novel and established approaches.")
        summary_parts.append("")
        summary_parts.append("")
        
        # 4. Clinical Trial Phases
        summary_parts.append("4. CLINICAL TRIAL PHASES AND DEVELOPMENT PIPELINE")
        summary_parts.append("")
        if phases:
            summary_parts.append("* Phase Distribution:")
            for phase, count in sorted(phases.items()):
                percentage = (count / total_trials * 100) if total_trials > 0 else 0
                summary_parts.append(f"  - {phase}: {count} trials ({percentage:.1f}%)")
        else:
            summary_parts.append("* Phase information not available for all trials")
        summary_parts.append("")
        summary_parts.append("")
        
        # 5. Trial Status
        summary_parts.append("5. KEY FINDINGS AND PATTERNS")
        summary_parts.append("")
        summary_parts.append("* Trial Status Distribution:")
        if statuses:
            for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_trials * 100) if total_trials > 0 else 0
                summary_parts.append(f"  - {status}: {count} trials ({percentage:.1f}%)")
        summary_parts.append("")
        active_count = sum(count for status, count in statuses.items() 
                          if status in ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION'])
        summary_parts.append(f"* {active_count} trials are currently active, indicating ongoing research activity")
        summary_parts.append("")
        summary_parts.append("")
        
        # 6. Methodological Approaches
        summary_parts.append("6. METHODOLOGICAL APPROACHES")
        summary_parts.append("")
        if study_types:
            summary_parts.append("* Study Design Types:")
            for st, count in sorted(study_types.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"  - {st}: {count} trial(s)")
        summary_parts.append("")
        summary_parts.append("")
        
        # 7. Clinical Implications
        summary_parts.append("7. IMPLICATIONS FOR CLINICAL PRACTICE")
        summary_parts.append("")
        summary_parts.append(f"* The {total_trials} trials identified represent significant research investment in {keywords}")
        summary_parts.append("* Active trials suggest evolving treatment paradigms and emerging therapeutic options")
        summary_parts.append("* Diverse intervention approaches indicate multiple pathways being explored")
        summary_parts.append("* Results from these trials may inform future clinical guidelines and treatment standards")
        summary_parts.append("")
        summary_parts.append("")
        
        # 8. Summary
        summary_parts.append("8. SUMMARY AND CONCLUSIONS")
        summary_parts.append("")
        summary_parts.append(f"This analysis identified {total_trials} clinical trials related to {keywords}. ")
        summary_parts.append("")
        if phases:
            early_phase = sum(count for phase, count in phases.items() if 'PHASE1' in phase or 'EARLY' in phase)
            late_phase = sum(count for phase, count in phases.items() if 'PHASE3' in phase or 'PHASE4' in phase)
            summary_parts.append(f"The research pipeline includes {early_phase} early-phase and {late_phase} late-phase trials, " +
                               "demonstrating both foundational research and near-market therapeutic development.")
        summary_parts.append("")
        summary_parts.append("The diversity of approaches and active recruitment status of many trials indicates this " +
                           "is an active area of clinical research with significant therapeutic potential.")
        summary_parts.append("")
        
        # Add trial list
        summary_parts.append("")
        summary_parts.append("DETAILED TRIAL LIST")
        summary_parts.append("")
        for idx, study in enumerate(studies, 1):
            try:
                protocol = study['protocolSection']
                nct_id = protocol['identificationModule']['nctId']
                title = protocol['identificationModule']['briefTitle']
                status = protocol.get('statusModule', {}).get('overallStatus', 'Unknown')
                summary_parts.append(f"{idx}. **{nct_id}**: {title}")
                summary_parts.append(f"   Status: {status}")
                summary_parts.append("")
            except (KeyError, TypeError):
                continue
        
        return "\n".join(summary_parts)
    
    def _generate_with_gemini(self, keywords: str, total_trials: int, trials_text: str, trials_data: dict) -> str:
        """Generate summary using Google Gemini API"""
        logger.info("Attempting to generate summary with Gemini")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        
        prompt = f"""You are a medical research analyst conducting a comprehensive literature review. Analyze the following clinical trials data and provide a detailed, well-structured summary suitable for academic literature review.

Search Keywords: {keywords}
Total Trials Found: {total_trials}

Clinical Trials Data (showing up to 100 trials):
{trials_text}

CRITICAL FORMATTING RULES - FOLLOW EXACTLY:
- OUTPUT ONLY PLAIN TEXT - NO MARKDOWN FORMATTING
- NO asterisks, NO hashtags, NO bold, NO italics, NO special formatting characters
- NO bullet points using asterisks or dashes
- For headings: Write them in UPPERCASE followed by a blank line
- After each heading, leave ONE blank line, then write the content
- Use simple sentences and paragraphs
- Start each point on a new line without any special characters
- Be extremely detailed and specific about mechanisms, findings, and clinical data
- Include specific trial IDs (NCT numbers) when discussing trials
- Discuss molecular mechanisms, drug targets, and biological pathways in detail

Provide a comprehensive literature review summary with the following structure:

COMPREHENSIVE CLINICAL TRIALS ANALYSIS

1. OVERVIEW

Total number of trials found and overall scope. Geographic and temporal distribution of trials. Key research institutions and sponsors involved. Relevance to the search keywords.

2. THERAPEUTIC AREAS AND CONDITIONS

Primary diseases and conditions being studied with prevalence data. Disease classifications and subtypes being targeted. Emerging therapeutic targets and biomarkers. Patient populations and disease severity levels.

3. INTERVENTION MECHANISMS AND APPROACHES

Detailed analysis of intervention types including drugs, biologics, devices, and gene therapy. Specific mechanisms of action being investigated including molecular pathways, targets, and binding sites. Novel versus established therapeutic approaches with comparative analysis. Combination therapies and scientific rationale. Dose regimens and administration routes.

4. CLINICAL TRIAL PHASES AND DEVELOPMENT PIPELINE

Distribution across phases including Phase I, II, III, and IV with specific numbers. Development stage analysis and progression patterns. Trial status including recruiting, active, and completed with completion rates. Success indicators and trial outcomes where available.

5. KEY FINDINGS AND PATTERNS

Common themes across trials. Innovative approaches or breakthrough therapies identified. Safety and efficacy trends. Gaps in current research. Convergence of evidence across multiple trials.

6. METHODOLOGICAL APPROACHES

Study designs being employed including randomized, controlled, and open-label trials. Patient populations and specific inclusion and exclusion criteria. Primary and secondary endpoints. Outcome measures and assessment tools. Statistical methods and sample sizes.

7. IMPLICATIONS FOR CLINICAL PRACTICE

Potential impact on treatment paradigms and standard of care. Emerging evidence for new therapeutic options. Clinical relevance and translational potential. Areas requiring further investigation. Regulatory and approval considerations.

8. SUMMARY AND CONCLUSIONS

Synthesis of major insights from the trial landscape. Research landscape overview and current state of the field. Future directions and promising areas. Clinical and translational implications.

REMEMBER: Output only plain text with headings in UPPERCASE, one blank line after each heading, then content. No markdown, no asterisks, no special formatting. Write in clear paragraphs and sentences."""

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 16000,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        try:
            logger.info("Sending request to Gemini API")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                # Ensure proper formatting with line breaks
                summary = self._format_summary(summary)
                logger.info(f"Successfully generated comprehensive summary with Gemini ({len(summary)} characters)")
                return summary
            else:
                logger.error("No candidates in Gemini response")
                return ""
        except Exception as e:
            logger.error(f"Gemini summary generation failed: {e}")
            print(f"Gemini API error details: {e}")
            return ""
    
    def _generate_with_groq(self, keywords: str, total_trials: int, trials_text: str, trials_data: dict) -> str:
        """Generate summary using Groq API (fallback)"""
        logger.info("Generating summary with Groq")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        
        prompt = f"""You are a medical research analyst conducting a comprehensive literature review. Analyze the following clinical trials data and provide a detailed, well-structured summary.

Search Keywords: {keywords}
Total Trials Found: {total_trials}

Clinical Trials Data:
{trials_text}

CRITICAL FORMATTING RULES - FOLLOW EXACTLY:
- OUTPUT ONLY PLAIN TEXT - NO MARKDOWN FORMATTING
- NO asterisks, NO hashtags, NO bold, NO italics, NO special formatting characters
- NO bullet points using asterisks or dashes
- For headings: Write them in UPPERCASE followed by a blank line
- After each heading, leave ONE blank line, then write the content
- Use simple sentences and paragraphs
- Start each point on a new line without any special characters
- Be extremely detailed about mechanisms, targets, and clinical data
- Include specific NCT IDs when referencing trials

Provide comprehensive analysis with these sections:

COMPREHENSIVE CLINICAL TRIALS ANALYSIS

1. OVERVIEW

Total trials, scope, geographic distribution. Relevance to search keywords.

2. THERAPEUTIC AREAS AND CONDITIONS

Diseases, conditions, patient populations.

3. INTERVENTION MECHANISMS AND APPROACHES

Detailed mechanisms of action, molecular targets, pathways. Drug types, delivery methods, combination therapies.

4. CLINICAL TRIAL PHASES

Phase distribution, development pipeline.

5. KEY FINDINGS AND PATTERNS

Common themes, breakthrough therapies, efficacy data.

6. METHODOLOGICAL APPROACHES

Study designs, endpoints, patient criteria.

7. CLINICAL IMPLICATIONS

Impact on treatment paradigms.

8. SUMMARY AND CONCLUSIONS

Major insights, future directions.

REMEMBER: Output only plain text with headings in UPPERCASE, one blank line after each heading, then content. No markdown, no asterisks, no special formatting."""

        payload = {
            "model": "llama-3.1-70b-versatile",  # Using larger model for better analysis
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical research analyst providing detailed literature review summaries. Be comprehensive, specific, and academic in your analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 8000  # Increased for comprehensive output
        }
        
        try:
            logger.info("Sending request to Groq API for summary generation")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            summary = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            # Ensure proper formatting with line breaks
            summary = self._format_summary(summary)
            logger.info(f"Successfully generated comprehensive summary with Groq ({len(summary)} characters)")
            return summary or ""
        except Exception as e:
            logger.error(f"Groq summary generation failed: {e}")
            print(f"Groq API error details: {e}")
            logger.info("Groq API failed, will use structured fallback")
            return ""

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