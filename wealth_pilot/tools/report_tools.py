"""
Report Tools — PDF report generation using ADK Artifacts
"""

import json
from datetime import datetime

from fpdf import FPDF
from google.genai import types
from google.adk.tools import ToolContext


def _clean(text: str) -> str:
    """Replace Unicode chars that Helvetica can't render and strip markdown."""
    return (
        text
        .replace("\u2014", "-")   # em-dash
        .replace("\u2013", "-")   # en-dash
        .replace("\u2018", "'")   # left single quote
        .replace("\u2019", "'")   # right single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u2022", "-")   # bullet
        .replace("\u2026", "...")  # ellipsis
        .replace("\u00a0", " ")   # non-breaking space
        .replace("**", "")        # markdown bold
        .replace("*", "")         # markdown italic
    )


class PortfolioReportPDF(FPDF):
    """Clean PDF layout for portfolio reports."""

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(26, 115, 232)
        self.cell(0, 12, "  WealthPilot - AI Wealth Advisor", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}  |  Google Agent Development Kit", align="C")


def _build_pdf(title: str, content: str, timestamp: str) -> bytes:
    """Build a PDF from the report content. Returns PDF bytes."""
    pdf = PortfolioReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 26, 26)
    pdf.multi_cell(0, 9, _clean(title))
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated on {timestamp}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Parse content line by line
    for line in content.strip().split("\n"):
        s = line.strip()
        if not s:
            pdf.ln(3)
            continue

        text = _clean(s)

        if s.startswith("## ") or s.startswith("# "):
            heading = text.lstrip("# ").strip()
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(26, 115, 232)
            pdf.multi_cell(0, 8, heading)
            y = pdf.get_y()
            pdf.set_draw_color(26, 115, 232)
            pdf.set_line_width(0.4)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(4)
        elif s.startswith("### "):
            heading = text.lstrip("# ").strip()
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(66, 133, 244)
            pdf.multi_cell(0, 7, heading)
            pdf.ln(2)
        elif s.startswith("- ") or s.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 51, 51)
            pdf.multi_cell(0, 6, f"  -  {text[2:].strip()}")
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 51, 51)
            pdf.multi_cell(0, 6, text)
            pdf.ln(2)

    # Disclaimer
    pdf.ln(6)
    pdf.set_fill_color(255, 243, 205)
    pdf.set_draw_color(255, 193, 7)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(133, 100, 4)
    pdf.cell(0, 8, "  DISCLAIMER", new_x="LMARGIN", new_y="NEXT", fill=True, border=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        "This report is AI-generated analysis for informational purposes only. "
        "It does not constitute financial advice. Always consult a qualified "
        "financial advisor before making investment decisions.",
        fill=True, border="LRB",
    )

    return pdf.output()


async def save_portfolio_report(
    report_title: str,
    report_content: str,
    tool_context: ToolContext,
) -> str:
    """Saves a portfolio analysis report as a downloadable PDF artifact.

    Args:
        report_title: Title of the report.
        report_content: The full report content as plain text or markdown.
      
    Returns:
        JSON confirmation with filename and version number.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        pdf_bytes = _build_pdf(report_title, report_content, timestamp)
    except Exception as e:
        # Fallback: save as markdown if PDF fails
        fallback = f"# {report_title}\n\nGenerated: {timestamp}\n\n{report_content}"
        artifact = types.Part.from_text(text=fallback)
        version = await tool_context.save_artifact(
            filename="portfolio_report.md", artifact=artifact,
        )
        return json.dumps({
            "status": "report_saved_as_text",
            "filename": "portfolio_report.md",
            "version": version,
            "note": f"PDF failed ({e}), saved as markdown instead.",
        })

    # Save as PDF artifact
    artifact = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
    version = await tool_context.save_artifact(
        filename="portfolio_report.pdf", artifact=artifact,
    )

    return json.dumps({
        "status": "report_saved",
        "filename": "portfolio_report.pdf",
        "version": version,
        "title": report_title,
        "timestamp": timestamp,
        "message": f"PDF report saved (version {version}). Download from the Artifacts panel.",
    })