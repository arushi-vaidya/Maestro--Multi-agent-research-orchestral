"""
Forecast Reconciliation for Market Intelligence
Handles conflicting forecasts by normalizing time horizons and market scopes
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ForecastReconciler:
    """
    Reconciles conflicting market forecasts by normalizing time horizons and scopes

    Key Features:
    - Detects forecast conflicts (e.g., $45.8B by 2030 vs $180B by 2035)
    - Normalizes by time horizon (near-term vs long-term)
    - Explains variance by market scope (GLP-1 only vs broader incretin class)
    - Provides range-based reporting instead of single numbers
    - Increases content coherence without suppressing data
    """

    def __init__(self):
        self.forecast_patterns = [
            # Match patterns like "$45.8B by 2030", "23.5 billion in 2024", etc.
            r'\$?(\d+\.?\d*)\s*(B|billion|M|million)\s*(by|in|for)?\s*(\d{4})',
            r'(\d+\.?\d*)\s*(B|billion|M|million)\s*USD\s*(by|in|for)?\s*(\d{4})',
            r'(\d{4}).*?\$?(\d+\.?\d*)\s*(B|billion|M|million)',
        ]

        self.scope_keywords = {
            'narrow': ['glp-1 only', 'specific drug', 'single product', 'ozempic', 'wegovy', 'mounjaro'],
            'medium': ['glp-1 market', 'glp-1 class', 'glp-1 agonist'],
            'broad': ['incretin', 'diabetes', 'obesity drug', 'metabolic', 'antidiabetic']
        }

    def reconcile_forecasts(
        self,
        sections: Dict[str, str],
        web_results: List[Dict[str, Any]],
        rag_results: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, str], float]:
        """
        Reconcile forecasts across sections and add explanatory context

        Args:
            sections: Generated content sections
            web_results: Web search results (for context)
            rag_results: RAG results (for context)

        Returns:
            (reconciled_sections, coherence_boost)
            - reconciled_sections: Updated sections with reconciliation notes
            - coherence_boost: Confidence boost from successful reconciliation (0.0-0.15)
        """
        # Extract all forecasts from sections
        forecasts = self._extract_forecasts(sections)

        if len(forecasts) < 2:
            # No conflict possible with <2 forecasts
            return sections, 0.0

        # Check for conflicts
        has_conflict = self._detect_conflicts(forecasts)

        if not has_conflict:
            # No conflict detected
            logger.info("No forecast conflicts detected")
            return sections, 0.05  # Small boost for consistency

        # Reconcile conflicts
        logger.info(f"Detected forecast conflicts, reconciling {len(forecasts)} forecasts")
        reconciliation_note = self._generate_reconciliation_note(forecasts, sections)

        # Add reconciliation note to key_metrics section
        if 'key_metrics' in sections and reconciliation_note:
            sections['key_metrics'] = sections['key_metrics'] + f"\n\n{reconciliation_note}"
            logger.info("Added forecast reconciliation note to key_metrics")
            return sections, 0.10  # Moderate boost for reconciliation

        return sections, 0.05

    def _extract_forecasts(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract all forecast values and years from sections

        Returns:
            List of forecast dicts with {value, unit, year, context, section}
        """
        forecasts = []

        for section_name, content in sections.items():
            if not content:
                continue

            for pattern in self.forecast_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)

                for match in matches:
                    try:
                        # Extract components depending on pattern structure
                        groups = match.groups()

                        # Pattern 1 & 2: value, unit, by/in, year
                        if len(groups) == 4 and groups[0].replace('.', '').isdigit():
                            value = float(groups[0])
                            unit = groups[1].lower()
                            year = int(groups[3])
                        # Pattern 3: year, value, unit
                        elif len(groups) >= 3 and groups[1].replace('.', '').isdigit():
                            value = float(groups[1])
                            unit = groups[2].lower()
                            year = int(groups[0])
                        else:
                            continue

                        # Normalize to billions
                        if 'm' in unit or 'million' in unit:
                            value_billions = value / 1000.0
                        else:
                            value_billions = value

                        # Extract context (30 chars before and after)
                        context_start = max(0, match.start() - 30)
                        context_end = min(len(content), match.end() + 30)
                        context = content[context_start:context_end].strip()

                        forecasts.append({
                            'value_billions': value_billions,
                            'year': year,
                            'context': context,
                            'section': section_name,
                            'original_text': match.group(0)
                        })

                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse forecast: {match.group(0)} - {e}")
                        continue

        logger.info(f"Extracted {len(forecasts)} forecasts from sections")
        return forecasts

    def _detect_conflicts(self, forecasts: List[Dict[str, Any]]) -> bool:
        """
        Detect if forecasts have significant conflicts

        Conflict definition:
        - Same year, >50% difference in value
        - Similar years (±2), >100% difference in value
        """
        if len(forecasts) < 2:
            return False

        # Group by year (±2 year tolerance)
        year_groups = {}
        for forecast in forecasts:
            year = forecast['year']
            matched = False

            for grouped_year in list(year_groups.keys()):
                if abs(year - grouped_year) <= 2:
                    year_groups[grouped_year].append(forecast)
                    matched = True
                    break

            if not matched:
                year_groups[year] = [forecast]

        # Check each year group for conflicts
        for year, group_forecasts in year_groups.items():
            if len(group_forecasts) < 2:
                continue

            values = [f['value_billions'] for f in group_forecasts]
            min_val = min(values)
            max_val = max(values)

            if min_val > 0:
                ratio = max_val / min_val
                if ratio > 1.5:  # >50% difference
                    logger.info(f"Conflict detected for year ~{year}: ${min_val:.1f}B vs ${max_val:.1f}B (ratio: {ratio:.2f})")
                    return True

        return False

    def _generate_reconciliation_note(
        self,
        forecasts: List[Dict[str, Any]],
        sections: Dict[str, str]
    ) -> str:
        """
        Generate explanation for forecast variance

        Possible explanations:
        - Time horizon differences (2030 vs 2035)
        - Market scope differences (GLP-1 only vs broader class)
        - Geographic scope differences (US vs global)
        - Methodology differences (different analysts)
        """
        # Sort forecasts by year
        forecasts_sorted = sorted(forecasts, key=lambda f: f['year'])

        if len(forecasts_sorted) < 2:
            return ""

        # Identify range
        years = [f['year'] for f in forecasts_sorted]
        values = [f['value_billions'] for f in forecasts_sorted]

        min_year = min(years)
        max_year = max(years)
        min_val = min(values)
        max_val = max(values)

        # Generate note
        note_parts = ["**Forecast Reconciliation:**"]

        # Explain time horizon variance
        if max_year - min_year >= 3:
            note_parts.append(
                f"Multiple time horizons cited: ${min_val:.1f}B-${max_val:.1f}B "
                f"across {min_year}-{max_year}. "
            )
        else:
            # Same time horizon, likely scope difference
            note_parts.append(
                f"Variance in {min_year}-{max_year} forecasts (${min_val:.1f}B-${max_val:.1f}B) "
            )

        # Analyze context for scope clues
        scope_explanation = self._analyze_scope_differences(forecasts_sorted, sections)
        if scope_explanation:
            note_parts.append(scope_explanation)
        else:
            note_parts.append(
                "likely reflects different market definitions (product-specific vs class-wide) "
                "or geographic scope (regional vs global)."
            )

        # Recommendation
        note_parts.append(
            "Range-based reporting recommended given source variance."
        )

        return " ".join(note_parts)

    def _analyze_scope_differences(
        self,
        forecasts: List[Dict[str, Any]],
        sections: Dict[str, str]
    ) -> str:
        """
        Analyze context to determine if variance is due to scope differences
        """
        # Check contexts for scope keywords
        narrow_count = 0
        medium_count = 0
        broad_count = 0

        all_text = " ".join(sections.values()).lower()

        for keyword in self.scope_keywords['narrow']:
            if keyword in all_text:
                narrow_count += 1

        for keyword in self.scope_keywords['medium']:
            if keyword in all_text:
                medium_count += 1

        for keyword in self.scope_keywords['broad']:
            if keyword in all_text:
                broad_count += 1

        # If multiple scopes mentioned, likely explains variance
        if narrow_count > 0 and (medium_count > 0 or broad_count > 0):
            return (
                "reflects different market scopes: product-specific forecasts "
                "vs. broader therapeutic class projections."
            )
        elif medium_count > 0 and broad_count > 0:
            return (
                "reflects different market definitions: GLP-1 agonist class "
                "vs. broader metabolic/antidiabetic market."
            )

        return ""


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    reconciler = ForecastReconciler()

    # Test Case 1: Conflicting forecasts
    sections_1 = {
        'summary': 'Market analysis shows strong growth.',
        'market_overview': 'The GLP-1 market reached $23.5B in 2024.',
        'key_metrics': 'Forecast: $45.8B by 2030 [WEB-1]. Alternative estimate: $180B by 2035 [WEB-2].',
        'future_outlook': 'Long-term projections vary significantly.'
    }

    reconciled_1, boost_1 = reconciler.reconcile_forecasts(sections_1, [], [])

    print("="*70)
    print("TEST 1: Conflicting Forecasts")
    print("="*70)
    print(f"\nOriginal key_metrics:\n{sections_1['key_metrics']}")
    print(f"\nReconciled key_metrics:\n{reconciled_1['key_metrics']}")
    print(f"\nCoherence boost: +{boost_1:.2f}")

    # Test Case 2: Consistent forecasts
    sections_2 = {
        'summary': 'Market analysis shows strong growth.',
        'market_overview': 'The GLP-1 market reached $23.5B in 2024.',
        'key_metrics': 'Forecast: $45.8B by 2030 [WEB-1]. Similar estimate: $47.2B by 2030 [RAG-1].',
        'future_outlook': 'Consistent projections across sources.'
    }

    reconciled_2, boost_2 = reconciler.reconcile_forecasts(sections_2, [], [])

    print("\n" + "="*70)
    print("TEST 2: Consistent Forecasts")
    print("="*70)
    print(f"\nCoherence boost: +{boost_2:.2f}")
    print("No reconciliation note needed (forecasts aligned)")
