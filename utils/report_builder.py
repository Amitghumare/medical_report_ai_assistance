"""
Step 5: Download Report
Builds a polished PDF report containing patient info, the lab results
table, and the AI-generated summary, returned as in-memory bytes so it
can be served via st.download_button without touching disk.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def build_pdf_report(patient_info: dict, results: list, summary: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1a237e")
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"], textColor=colors.HexColor("#1a237e")
    )
    normal_style = styles["Normal"]

    story = []

    # Title
    story.append(Paragraph("Medical Report AI Assistant", title_style))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M')}",
            normal_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # Patient info
    story.append(Paragraph("Patient Information", heading_style))
    info_rows = [
        ["Patient ID", patient_info.get("patient_id") or "N/A"],
        ["Name", patient_info.get("name") or "N/A"],
        ["Age", patient_info.get("age") or "N/A"],
        ["Gender", patient_info.get("gender") or "N/A"],
    ]
    info_table = Table(info_rows, colWidths=[5 * cm, 10 * cm])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.7 * cm))

    # Lab results
    story.append(Paragraph("Lab Results", heading_style))
    if results:
        header = ["Test", "Value", "Unit", "Reference Range", "Status"]
        table_data = [header] + [
            [r["Test"], str(r["Value"]), r["Unit"], r["Reference Range"], r["Status"]]
            for r in results
        ]
        result_table = Table(
            table_data, colWidths=[4.5 * cm, 2 * cm, 2 * cm, 3.5 * cm, 3 * cm]
        )

        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ]
        # Highlight abnormal rows
        for i, r in enumerate(results, start=1):
            if r["Status"] in ("High", "Low"):
                style_commands.append(
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fff3e0"))
                )
                style_commands.append(
                    ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#e65100"))
                )
            elif r["Status"] == "Normal":
                style_commands.append(
                    ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#2e7d32"))
                )

        result_table.setStyle(TableStyle(style_commands))
        story.append(result_table)
    else:
        story.append(Paragraph("No structured lab values were detected.", normal_style))

    story.append(Spacer(1, 0.7 * cm))

    # AI Summary
    story.append(Paragraph("AI-Generated Summary", heading_style))
    for para in summary.split("\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), normal_style))
            story.append(Spacer(1, 0.15 * cm))

    story.append(Spacer(1, 0.7 * cm))
    disclaimer = (
        "<i>Disclaimer: This report is AI-generated for informational purposes "
        "only and does not constitute medical advice, diagnosis, or treatment. "
        "Please consult a licensed physician regarding any health concerns.</i>"
    )
    story.append(Paragraph(disclaimer, normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
