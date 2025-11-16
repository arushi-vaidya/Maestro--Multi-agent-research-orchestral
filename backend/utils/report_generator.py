# backend/utils/report_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
from io import BytesIO

class ReportGenerator:
    """
    Generate PDF/Excel reports from analysis results
    """
    
    def generate_pdf(self, results: Dict, filename: str):
        """
        Create professional PDF report
        """
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph(f"MAESTRO Analysis Report", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Query
        story.append(Paragraph(f"Query: {results['query']}", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Synthesis
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Paragraph(results['synthesis'], styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
    def generate_excel(self, results: Dict, filename: str):
        """
        Export data tables to Excel
        """
        import pandas as pd
        
        with pd.ExcelWriter(filename) as writer:
            for agent, data in results['agent_results'].items():
                df = pd.DataFrame(data.get('raw_data', {}))
                df.to_excel(writer, sheet_name=agent)