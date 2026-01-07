"""
Bulletproof Section-wise LLM Synthesis
Generates market intelligence sections independently to avoid JSON parsing failures
"""

import logging
from typing import Dict, List, Any
from config.llm.llm_config_sync import generate_llm_response

logger = logging.getLogger(__name__)


class SectionSynthesizer:
    """
    Robust section-by-section synthesis for market intelligence

    Key Benefits:
    - No JSON parsing errors (plain text only)
    - Guaranteed 100% section population
    - Graceful degradation (fallback per section)
    - Explicit corroboration instructions
    """

    def __init__(self):
        self.section_definitions = {
            'summary': {
                'instruction': "Provide a 2-3 sentence executive summary answering the query directly. Cite sources using [WEB-X] for web sources or [RAG-X] for internal documents.",
                'max_tokens': 200,
                'temperature': 0.3
            },
            'market_overview': {
                'instruction': "Provide current market size, CAGR, and growth trends. **Prefer web sources [WEB-X] for recent 2024 numbers**, RAG sources [RAG-X] for historical context. Include specific dollar amounts and percentages.",
                'max_tokens': 300,
                'temperature': 0.3
            },
            'key_metrics': {
                'instruction': "List specific market metrics: market size ($B), CAGR (%), forecast values, top product sales. Cite sources for each number [WEB-X] or [RAG-X].",
                'max_tokens': 250,
                'temperature': 0.2
            },
            'drivers_and_trends': {
                'instruction': "Describe key market drivers, trends, and dynamics. What is driving growth? What are emerging patterns? Cite sources [WEB-X] [RAG-X].",
                'max_tokens': 300,
                'temperature': 0.4
            },
            'competitive_landscape': {
                'instruction': "Identify key players, their market positions, major products, and competitive dynamics. Include company names and market share if available. Cite sources [WEB-X] [RAG-X].",
                'max_tokens': 300,
                'temperature': 0.3
            },
            'risks_and_opportunities': {
                'instruction': "Describe market risks, challenges, opportunities, and future potential. Include patent expiries, regulatory issues, emerging opportunities. Cite sources [WEB-X] [RAG-X].",
                'max_tokens': 250,
                'temperature': 0.4
            },
            'future_outlook': {
                'instruction': "Provide market outlook, forecasts, pipeline developments, and strategic implications. Focus on 2025-2030 timeframe. Cite sources [WEB-X] [RAG-X].",
                'max_tokens': 250,
                'temperature': 0.4
            }
        }

    def synthesize_all_sections(
        self,
        query: str,
        fused_context: str,
        web_results: List[Dict[str, Any]],
        rag_results: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate all 7 sections independently

        GUARANTEES:
        - All 7 sections will be populated
        - No JSON parsing errors
        - Graceful degradation if LLM fails

        Args:
            query: User query
            fused_context: Combined web + RAG context
            web_results: Web search results
            rag_results: RAG retrieval results

        Returns:
            Dict with all 7 sections (always complete)
        """
        sections = {}

        # Check if we have any sources
        has_sources = len(web_results) > 0 or len(rag_results) > 0

        if not has_sources:
            logger.warning("No sources available for synthesis")
            return self._create_no_data_sections()

        # Generate each section independently
        for section_name, section_config in self.section_definitions.items():
            logger.info(f"Generating section: {section_name}")

            try:
                section_content = self._generate_single_section(
                    section_name=section_name,
                    instruction=section_config['instruction'],
                    query=query,
                    context=fused_context,
                    max_tokens=section_config['max_tokens'],
                    temperature=section_config['temperature']
                )

                # Validate minimum quality
                if len(section_content.strip()) < 20:
                    logger.warning(f"Section {section_name} too short, using fallback")
                    section_content = f"Insufficient data in retrieved sources for {section_name.replace('_', ' ')}."

                sections[section_name] = section_content
                logger.debug(f"Section {section_name}: {len(section_content)} chars")

            except Exception as e:
                logger.error(f"Section {section_name} generation failed: {e}")
                sections[section_name] = f"Insufficient data in retrieved sources for {section_name.replace('_', ' ')}."

        # Final validation: ensure all 7 sections exist
        for section_name in self.section_definitions.keys():
            if section_name not in sections or not sections[section_name]:
                sections[section_name] = f"Insufficient data in retrieved sources for {section_name.replace('_', ' ')}."

        logger.info(f"✅ All {len(sections)} sections generated")
        return sections

    def _generate_single_section(
        self,
        section_name: str,
        instruction: str,
        query: str,
        context: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Generate a single section robustly

        Returns plain text only, no JSON
        """
        # Truncate context if too long (to fit in LLM context window)
        max_context_length = 4000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n...[context truncated]"

        prompt = f"""You are a pharmaceutical market intelligence analyst.

RETRIEVED INFORMATION:
{context}

USER QUERY:
{query}

TASK:
Generate ONLY the "{section_name.replace('_', ' ').title()}" section.

INSTRUCTIONS:
{instruction}

CRITICAL RULES:
- Return plain text ONLY (no JSON, no markdown formatting, no section headers)
- Be concise and data-driven
- Cite sources using [WEB-1], [WEB-2], [RAG-1], [RAG-2] etc.
- If data is insufficient, write "Insufficient data in retrieved sources"
- Maximum {max_tokens} tokens

Generate the section now:"""

        try:
            response = generate_llm_response(
                prompt=prompt,
                system_prompt="You are a market intelligence analyst. Return concise, well-cited analysis in plain text.",
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Clean response
            response = response.strip()

            # Remove any section headers the LLM might add
            response = self._clean_section_content(response, section_name)

            return response

        except Exception as e:
            logger.error(f"LLM call failed for {section_name}: {e}")
            raise

    def _clean_section_content(self, content: str, section_name: str) -> str:
        """
        Remove any formatting artifacts from LLM response
        """
        # Remove section headers if LLM added them
        header_variations = [
            f"{section_name}:",
            f"{section_name.replace('_', ' ')}:",
            f"{section_name.replace('_', ' ').title()}:",
            f"**{section_name.replace('_', ' ').title()}**:",
            f"# {section_name.replace('_', ' ').title()}"
        ]

        for header in header_variations:
            if content.lower().startswith(header.lower()):
                content = content[len(header):].strip()

        # Remove markdown formatting
        content = content.replace('**', '').replace('##', '').replace('#', '')

        return content.strip()

    def _create_no_data_sections(self) -> Dict[str, str]:
        """
        Create fallback sections when no sources available
        """
        return {
            section_name: f"Insufficient data in retrieved sources for {section_name.replace('_', ' ')}."
            for section_name in self.section_definitions.keys()
        }


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    synthesizer = SectionSynthesizer()

    # Mock data
    query = "What is the GLP-1 market size?"

    fused_context = """=== WEB SEARCH RESULTS ===
[WEB-1] GLP-1 Market Reaches $23.5B
The GLP-1 agonist market achieved $23.5 billion in 2024 with 18.2% CAGR.

=== INTERNAL KNOWLEDGE BASE ===
[RAG-1] GLP-1 Market Analysis Q1 2024
The GLP-1 receptor agonist market has experienced unprecedented growth, reaching $23.5B with 18.2% CAGR. Novo Nordisk dominates with Ozempic ($14.2B) and Wegovy ($4.5B)."""

    web_results = [{"title": "...", "url": "..."}]
    rag_results = [{"id": "...", "content": "..."}]

    sections = synthesizer.synthesize_all_sections(query, fused_context, web_results, rag_results)

    print("\n" + "="*70)
    print("GENERATED SECTIONS:")
    print("="*70)

    for section_name, content in sections.items():
        print(f"\n{section_name.upper().replace('_', ' ')}:")
        print(f"{content[:200]}...")

    print(f"\n✅ All {len(sections)} sections generated")
    print(f"Average length: {sum(len(s) for s in sections.values()) // len(sections)} chars")
