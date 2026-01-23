"""
Document Ingestion Pipeline
Loads market intelligence documents from various sources and formats
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from vector_store.rag_engine import RAGEngine, DocumentProcessor

logger = logging.getLogger(__name__)


class DocumentIngestion:
    """
    Handles ingestion of documents from various sources into RAG system
    """

    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize document ingestion

        Args:
            rag_engine: RAGEngine instance to store documents
        """
        self.rag_engine = rag_engine
        self.processor = DocumentProcessor()

    def ingest_json_documents(
        self,
        json_path: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> int:
        """
        Ingest documents from JSON file

        Args:
            json_path: Path to JSON file
            chunk_size: Size of text chunks
            overlap: Overlap between chunks

        Returns:
            Number of documents ingested

        Expected JSON format:
        [
            {
                "id": "doc_1",
                "title": "Document Title",
                "content": "Full document text...",
                "date": "2024-01-01",
                "therapy_area": "Oncology",
                "source": "Market Report",
                ... other metadata
            },
            ...
        ]
        """
        logger.info(f"Loading documents from: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            raw_docs = json.load(f)

        logger.info(f"Loaded {len(raw_docs)} documents from JSON")

        # Process and chunk documents
        all_chunks = []
        for doc in raw_docs:
            if "content" not in doc or "id" not in doc:
                logger.warning(f"Skipping invalid document: {doc.get('id', 'unknown')}")
                continue

            # Extract metadata
            metadata = {k: v for k, v in doc.items() if k not in ["content", "id"]}

            # Chunk document
            chunks = self.processor.create_document_from_text(
                text=doc["content"],
                doc_id=doc["id"],
                metadata=metadata,
                chunk_size=chunk_size,
                overlap=overlap
            )
            all_chunks.extend(chunks)

        # Add to RAG engine
        count = self.rag_engine.add_documents(all_chunks)
        logger.info(f"✅ Ingested {count} document chunks from JSON")
        return count

    def ingest_pdf(
        self,
        pdf_path: str,
        doc_id: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> int:
        """
        Ingest a PDF document

        Args:
            pdf_path: Path to PDF file
            doc_id: Unique document ID
            metadata: Document metadata
            chunk_size: Size of text chunks
            overlap: Overlap between chunks

        Returns:
            Number of chunks created
        """
        if not PDF_AVAILABLE:
            raise ImportError("pypdf not installed. Install with: pip install pypdf")

        logger.info(f"Processing PDF: {pdf_path}")

        # Extract text from PDF
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        logger.info(f"Extracted {len(text)} characters from PDF")

        # Create chunks
        chunks = self.processor.create_document_from_text(
            text=text,
            doc_id=doc_id,
            metadata=metadata,
            chunk_size=chunk_size,
            overlap=overlap
        )

        # Add to RAG engine
        count = self.rag_engine.add_documents(chunks)
        logger.info(f"✅ Ingested {count} chunks from PDF")
        return count

    def ingest_docx(
        self,
        docx_path: str,
        doc_id: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> int:
        """
        Ingest a DOCX document

        Args:
            docx_path: Path to DOCX file
            doc_id: Unique document ID
            metadata: Document metadata
            chunk_size: Size of text chunks
            overlap: Overlap between chunks

        Returns:
            Number of chunks created
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")

        logger.info(f"Processing DOCX: {docx_path}")

        # Extract text from DOCX
        doc = Document(docx_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        logger.info(f"Extracted {len(text)} characters from DOCX")

        # Create chunks
        chunks = self.processor.create_document_from_text(
            text=text,
            doc_id=doc_id,
            metadata=metadata,
            chunk_size=chunk_size,
            overlap=overlap
        )

        # Add to RAG engine
        count = self.rag_engine.add_documents(chunks)
        logger.info(f"✅ Ingested {count} chunks from DOCX")
        return count

    def ingest_text_file(
        self,
        txt_path: str,
        doc_id: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> int:
        """
        Ingest a plain text file

        Args:
            txt_path: Path to text file
            doc_id: Unique document ID
            metadata: Document metadata
            chunk_size: Size of text chunks
            overlap: Overlap between chunks

        Returns:
            Number of chunks created
        """
        logger.info(f"Processing text file: {txt_path}")

        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()

        logger.info(f"Loaded {len(text)} characters from text file")

        # Create chunks
        chunks = self.processor.create_document_from_text(
            text=text,
            doc_id=doc_id,
            metadata=metadata,
            chunk_size=chunk_size,
            overlap=overlap
        )

        # Add to RAG engine
        count = self.rag_engine.add_documents(chunks)
        logger.info(f"✅ Ingested {count} chunks from text file")
        return count

    def ingest_directory(
        self,
        directory: str,
        file_types: List[str] = [".pdf", ".txt", ".json"],
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> int:
        """
        Ingest all documents from a directory

        Args:
            directory: Path to directory
            file_types: List of file extensions to process
            chunk_size: Size of text chunks
            overlap: Overlap between chunks

        Returns:
            Total number of chunks created
        """
        logger.info(f"Ingesting documents from directory: {directory}")

        total_count = 0
        directory_path = Path(directory)

        for file_path in directory_path.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in file_types:
                continue

            # Generate doc_id from filename
            doc_id = file_path.stem

            # Extract basic metadata from file
            metadata = {
                "filename": file_path.name,
                "file_path": str(file_path),
                "ingestion_date": datetime.now().isoformat()
            }

            try:
                if suffix == ".json":
                    count = self.ingest_json_documents(
                        str(file_path),
                        chunk_size=chunk_size,
                        overlap=overlap
                    )
                elif suffix == ".pdf":
                    count = self.ingest_pdf(
                        str(file_path),
                        doc_id=doc_id,
                        metadata=metadata,
                        chunk_size=chunk_size,
                        overlap=overlap
                    )
                elif suffix == ".txt":
                    count = self.ingest_text_file(
                        str(file_path),
                        doc_id=doc_id,
                        metadata=metadata,
                        chunk_size=chunk_size,
                        overlap=overlap
                    )
                elif suffix == ".docx":
                    count = self.ingest_docx(
                        str(file_path),
                        doc_id=doc_id,
                        metadata=metadata,
                        chunk_size=chunk_size,
                        overlap=overlap
                    )
                else:
                    continue

                total_count += count

            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
                continue

        logger.info(f"✅ Total ingested: {total_count} chunks from directory")
        return total_count


def create_sample_market_corpus(output_path: str = "./vector_store/documents/market_corpus.json"):
    """
    Create a sample market intelligence corpus for testing

    Args:
        output_path: Path to save JSON corpus
    """
    logger.info("Creating sample market intelligence corpus...")

    corpus = [
        {
            "id": "glp1_market_2024_q1",
            "title": "GLP-1 Agonist Market Analysis Q1 2024",
            "content": """
            The GLP-1 receptor agonist market has experienced unprecedented growth in 2024,
            reaching a total market size of $23.5 billion with a compound annual growth rate (CAGR)
            of 18.2%. This growth is driven primarily by strong demand for obesity treatment and
            the expanding indication portfolio beyond diabetes.

            Market Leaders:
            Novo Nordisk dominates the market with two blockbuster products: Ozempic (semaglutide)
            generating $14.2 billion in annual sales (59% year-over-year growth) and Wegovy
            (semaglutide for obesity) achieving $4.5 billion (320% growth since launch).

            Eli Lilly has rapidly gained market share with Mounjaro (tirzepatide), which has generated
            $5.1 billion since its 2022 launch. The drug's dual GIP/GLP-1 mechanism shows superior
            efficacy in both glucose control and weight loss compared to pure GLP-1 agonists.

            AstraZeneca maintains a presence with their once-weekly exenatide formulation, though
            facing increasing pressure from newer agents.

            Regional Breakdown:
            - North America: 62% of global market ($14.6B)
            - Europe: 24% ($5.6B)
            - Asia-Pacific: 11% ($2.6B)
            - Rest of World: 3% ($0.7B)

            Market Dynamics:
            The obesity indication has become the primary growth driver, with estimates suggesting
            70% of new prescriptions are for weight loss rather than diabetes. Supply constraints
            have been a significant challenge, with both Novo Nordisk and Eli Lilly reporting
            backorders and production scale-up investments exceeding $6 billion.

            Future Outlook:
            Market forecasts project the GLP-1 market to reach $45.8 billion by 2030, driven by:
            - Expansion into cardiovascular disease prevention
            - Potential approval for NASH/MASH treatment
            - Oral formulation development (Novo's oral semaglutide in Phase 3)
            - Next-generation molecules with improved dosing profiles
            - Biosimilar entry expected post-2028 (first patent expiries)
            """,
            "date": "2024-03-15",
            "therapy_area": "Diabetes & Obesity",
            "source": "IQVIA Market Intelligence",
            "document_type": "market_analysis",
            "geography": "Global",
            "forecast_year": "2030"
        },
        {
            "id": "oncology_immunotherapy_2024",
            "title": "Oncology Immunotherapy Market Landscape 2024",
            "content": """
            The global oncology therapeutics market reached $185.3 billion in 2024, with immunotherapy
            representing the largest segment at $78.2 billion (42% market share). The market is
            growing at a robust 11.7% CAGR, driven by novel mechanisms and combination therapies.

            Market Segments:
            1. Immunotherapy: $78.2B (checkpoint inhibitors, CAR-T, bispecific antibodies)
            2. Targeted Therapy: $62.1B (kinase inhibitors, antibody-drug conjugates)
            3. Chemotherapy: $32.5B (declining market share)
            4. Hormone Therapy: $12.5B (stable in breast/prostate cancer)

            Key Players and Products:
            Roche leads with Tecentriq (PD-L1 inhibitor) and Herceptin franchise generating
            combined revenues of $18.4 billion. Bristol Myers Squibb's Opdivo and Yervoy
            combination therapy dominates lung cancer with $12.8 billion in sales.

            Merck's Keytruda (pembrolizumab) remains the top-selling oncology drug at $25.0 billion,
            with approvals across 20+ tumor types. The drug has become first-line therapy in
            multiple indications including NSCLC, melanoma, and triple-negative breast cancer.

            CAR-T Therapy Growth:
            CAR-T therapies have exceeded expectations, with the segment reaching $5.2 billion:
            - Kymriah (Novartis): $850M in hematologic malignancies
            - Yescarta (Gilead): $1.2B in lymphoma
            - Breyanzi (BMS): $680M in large B-cell lymphoma
            - Abecma (BMS/bluebird): $450M in multiple myeloma
            - Carvykti (J&J): $720M in multiple myeloma

            Emerging Trends:
            Bispecific antibodies are gaining traction with Roche's Lunsumio and AbbVie's Epcoritamab
            showing strong efficacy. These off-the-shelf products may challenge CAR-T in some indications.

            Antibody-drug conjugates (ADCs) represent the fastest-growing segment (48% CAGR):
            - Enhertu (Daiichi/AstraZeneca): $2.8B, multiple solid tumor indications
            - Trodelvy (Gilead): $1.1B in breast cancer
            - Padcev (Astellas/Seagen): $900M in bladder cancer

            Market Forecast:
            The oncology market is projected to reach $356.2 billion by 2030, driven by:
            - Precision medicine expansion (biomarker-driven therapy selection)
            - Combination immunotherapy protocols
            - Earlier-line treatment adoption
            - Adjuvant/neoadjuvant immunotherapy expansion
            - Novel targets (KRAS G12C, claudin 18.2, TROP2)
            """,
            "date": "2024-02-20",
            "therapy_area": "Oncology",
            "source": "EvaluatePharma Oncology Report",
            "document_type": "market_analysis",
            "geography": "Global",
            "forecast_year": "2030"
        },
        {
            "id": "alzheimers_market_2024",
            "title": "Alzheimer's Disease Therapeutics Market Update 2024",
            "content": """
            The Alzheimer's disease therapeutics market is experiencing a renaissance following
            the approval of disease-modifying treatments. The market size reached $4.8 billion
            in 2024 and is projected to grow at an exceptional 35.2% CAGR to reach $28.5 billion
            by 2030.

            Approved Anti-Amyloid Therapies:
            Leqembi (lecanemab, Eisai/Biogen) received full FDA approval in July 2023 and has
            rapidly captured market share, generating $1.8 billion in its first full year. The
            monthly IV infusion shows 27% slowing of cognitive decline in early Alzheimer's.

            Donanemab (Eli Lilly) received FDA approval in Q2 2024 following positive Phase 3
            TRAILBLAZER-ALZ 2 results showing 35% slowing of disease progression. Launch sales
            of $420 million suggest strong uptake, aided by the drug's quarterly dosing after
            initial monthly phase.

            Aduhelm (aducanumab, Biogen) was voluntarily withdrawn in Q1 2024 following poor
            commercial uptake and reimbursement challenges.

            Market Dynamics:
            The approval of anti-amyloid therapies has transformed the diagnostic landscape,
            driving increased adoption of:
            - Amyloid PET imaging (up 240% year-over-year)
            - Plasma biomarker testing (p-tau217, p-tau181, Aβ42/40 ratio)
            - MRI monitoring for ARIA (amyloid-related imaging abnormalities)

            Key Players:
            1. Eisai/Biogen: Leqembi franchise, next-gen candidates in development
            2. Eli Lilly: Donanemab, anti-tau antibodies in Phase 2
            3. Roche: Gantenerumab (Phase 3 ongoing despite mixed results)
            4. AbbVie: Tau-targeting programs in early development

            Pipeline Opportunities:
            Beyond anti-amyloid approaches, the pipeline includes:
            - Tau-targeting therapies (10+ Phase 2/3 programs)
            - Anti-inflammatory approaches (microglia modulators)
            - Neuroprotective agents (GLP-1 agonists showing promise)
            - Gene therapies (APOE modulation, TREM2 enhancement)
            - Combination therapies (amyloid + tau targeting)

            Market Challenges:
            - High treatment costs ($26,500/year for Leqembi)
            - Limited reimbursement (CMS requires registry participation)
            - Infrastructure requirements (infusion centers, monitoring)
            - ARIA risk management (10-15% incidence of symptomatic events)
            - Patient identification (need for early diagnosis)

            Forecast:
            Market growth will be driven by:
            - Expanded labeling (mild cognitive impairment)
            - Improved biomarker accessibility (blood-based tests)
            - Subcutaneous formulations in development
            - Combination therapy adoption
            - Global expansion (Japan, Europe regulatory pathways advancing)
            """,
            "date": "2024-04-10",
            "therapy_area": "Neurology",
            "indication": "Alzheimer's Disease",
            "source": "Alzforum Market Analysis",
            "document_type": "market_analysis",
            "geography": "Global",
            "forecast_year": "2030"
        },
        {
            "id": "gene_therapy_market_2024",
            "title": "Gene Therapy and CRISPR Market Outlook 2024",
            "content": """
            The gene therapy market has reached an inflection point in 2024, with total market
            size of $2.1 billion growing at 42.8% CAGR. The approval of the first CRISPR therapy
            (Casgevy for sickle cell disease) marks a watershed moment for genetic medicine.

            Market Segments:
            1. Ex vivo gene therapies: $1.2B
               - CAR-T (oncology): covered in oncology report
               - Stem cell modification (hemoglobinopathies): $280M
            2. In vivo gene therapies: $640M
               - AAV-based therapies (hemophilia, rare diseases)
               - mRNA therapeutics (rare metabolic disorders)
            3. CRISPR/gene editing: $260M
               - Ex vivo editing for sickle cell and beta-thalassemia

            Approved Products:
            Casgevy (exagamglogene autotemcel, Vertex/CRISPR Therapeutics): First CRISPR therapy
            approved in December 2023 for sickle cell disease and beta-thalassemia. Launched at
            $2.2 million per treatment with strong payer coverage. Q1 2024 sales: $18M with
            expanding treatment centers.

            Lyfgenia (lovotibeglogene autotemcel, bluebird bio): Gene therapy for sickle cell
            disease approved concurrently with Casgevy. Priced at $3.1 million but facing
            reimbursement challenges. Q1 sales: $4M.

            Hemgenix (etranacogene dezaparvovec, CSL Behring): AAV gene therapy for hemophilia B
            priced at $3.5 million. Second full year sales: $95M with 27 patients treated.

            Zynteglo (betibeglogene autotemcel, bluebird bio): Gene therapy for beta-thalassemia
            re-launched in 2023 after European withdrawal. Current sales: $38M (8 patients).

            Roctavian (valoctocogene roxaparvovec, BioMarin): AAV gene therapy for hemophilia A
            facing uptake challenges. 2024 sales: $22M (6 patients) below expectations.

            Pipeline Highlights:
            78 gene therapy and gene editing trials are ongoing globally:
            - Duchenne muscular dystrophy (Sarepta, Pfizer AAV programs in Phase 3)
            - Spinal muscular atrophy (next-generation AAV vectors)
            - Inherited retinal diseases (multiple AAV therapies in late-stage)
            - Cardiovascular diseases (in vivo CRISPR for PCSK9 in Phase 1)
            - Cancer (in vivo CAR-T approaches in early development)

            Technology Evolution:
            Base editing and prime editing represent next-generation CRISPR:
            - Verve Therapeutics: In vivo base editing for cardiovascular disease (Phase 1/2)
            - Beam Therapeutics: Base editing for sickle cell in Phase 1/2
            - Prime Medicine: Prime editing platform with multiple programs in preclinical

            Market Challenges:
            - Ultra-high pricing ($2-3.5M per treatment)
            - Manufacturing complexity and capacity constraints
            - Reimbursement uncertainty (outcomes-based agreements emerging)
            - Durability concerns (need for long-term follow-up data)
            - Competition from traditional therapies (incremental improvements)

            Investment Trends:
            Gene therapy sector has attracted $8.4 billion in venture funding in 2023-2024:
            - In vivo delivery technologies (AAV alternatives: LNPs, exosomes)
            - Tissue-specific targeting approaches
            - Gene regulation (epigenetic editing)
            - Manufacturing platforms (suspension cell culture, purification)

            Market Forecast:
            Gene therapy market projected to reach $18.9 billion by 2030, driven by:
            - Expanding indications (common genetic diseases)
            - Improved manufacturing (reduced costs from $2M to $500K)
            - Better delivery vectors (tissue-specific targeting)
            - Regulatory streamlining (accelerated approval pathways)
            - Payer acceptance (outcomes-based contracting)
            """,
            "date": "2024-03-28",
            "therapy_area": "Gene Therapy",
            "source": "Gene Therapy Market Intelligence",
            "document_type": "market_analysis",
            "geography": "Global",
            "forecast_year": "2030"
        },
        {
            "id": "obesity_market_expansion_2024",
            "title": "Obesity Therapeutics Market Expansion Beyond GLP-1",
            "content": """
            The obesity therapeutics market has exploded beyond GLP-1 agonists, reaching
            $31.2 billion in 2024 (growing from $8.4B in 2022). While GLP-1s dominate with
            75% market share, emerging mechanisms are gaining traction.

            GLP-1 Dominance:
            Wegovy and Mounjaro (approved for obesity in 2024) represent the current standard,
            achieving 15-22% total body weight loss. However, supply constraints and the need
            for continuous treatment are driving development of alternatives and combinations.

            Next-Generation Approaches:
            1. Triple Agonists (GLP-1/GIP/Glucagon):
                - Retatrutide (Eli Lilly, Phase 3): 24% weight loss at 48 weeks
                - Survodutide (Boehringer Ingelheim, Phase 2): 20% weight loss
                - Market potential: $15B+ by 2030

            2. Oral GLP-1 Agonists:
                - Rybelsus (Novo Nordisk, oral semaglutide): $2.1B sales, expanding to obesity
                - Orforglipron (Eli Lilly, oral GLP-1, Phase 3): 14.7% weight loss
                - Patient preference driving 40% market share by 2028

            3. Amylin Analogs:
                - Cagrilintide (Novo Nordisk): In combination with semaglutide (CagriSema)
                - Phase 3 data: 25.3% weight loss (combination vs 16.1% semaglutide alone)
                - Approval expected Q4 2025

            4. Bimagrumab (BYM338, Novartis):
                - Activin receptor II antibody
                - Phase 2: 20.5% fat mass reduction with muscle preservation
                - Differentiation: body composition improvement vs pure weight loss

            5. Small Molecule MC4R Agonists:
                - Rhythm Pharmaceuticals (setmelanotide): $180M in rare obesity
                - Next-gen MC4R programs in development (avoiding off-target effects)

            Market Dynamics:
            Patient population expansion:
            - FDA indication expansion to BMI >27 with comorbidities (from >30)
            - Pediatric populations (wegovy approved age 12+)
            - MASH/NASH treatment (liver benefit beyond weight loss)
            - Cardiovascular risk reduction (SELECT trial results for semaglutide)

            Reimbursement Evolution:
            CMS announced intention to cover obesity medications in Medicare Part D starting 2026,
            potentially adding 7 million covered lives and $10B annual market expansion.

            Commercial payers expanding coverage:
            - 65% now cover GLP-1s for obesity (up from 25% in 2021)
            - Prior authorization requirements easing
            - Outcomes-based contracts emerging

            Pricing Pressure:
            Current list prices ($13,000-16,000 annually) face pressure from:
            - Compounding pharmacy competition (FDA crackdown ongoing)
            - Biosimilar entry expected 2029-2030
            - Value-based pricing negotiations
            - International reference pricing

            Combination Therapy Future:
            Rational combinations in development:
            - GLP-1 + Amylin (Novo: CagriSema)
            - GLP-1 + Bimagrumab (muscle preservation)
            - GLP-1 + FGF21 (metabolic benefit)
            - Triple agonist + selective agents

            Market Forecast:
            Obesity therapeutics market to reach $77 billion by 2030:
            - GLP-1 single agents: $42B (54% share)
            - Next-gen multi-agonists: $20B (26%)
            - Oral agents: $10B (13%)
            - Specialty mechanisms: $5B (7%)

            Untapped potential: 650 million adults with obesity globally, <5% currently treated
            with pharmacotherapy, representing massive market opportunity.
            """,
            "date": "2024-04-02",
            "therapy_area": "Metabolic Disorders",
            "indication": "Obesity",
            "source": "Barclays Biopharma Report",
            "document_type": "market_analysis",
            "geography": "Global",
            "forecast_year": "2030"
        }
    ]

    # Create directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save corpus
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Created sample corpus with {len(corpus)} documents at: {output_path}")
    return output_path


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create sample corpus
    corpus_path = create_sample_market_corpus()

    # Initialize RAG and ingestion
    rag = RAGEngine()
    ingestion = DocumentIngestion(rag)

    # Ingest sample corpus
    count = ingestion.ingest_json_documents(corpus_path)

    print(f"\n✅ Ingested {count} document chunks")

    # Test search
    results = rag.search("What is the GLP-1 market size?", top_k=3)
    print(f"\n🔍 Found {len(results)} relevant documents")
    for doc in results:
        print(f"\nTitle: {doc['metadata'].get('title')}")
        print(f"Relevance: {doc['relevance_score']:.3f}")
        print(f"Content preview: {doc['content'][:150]}...")
