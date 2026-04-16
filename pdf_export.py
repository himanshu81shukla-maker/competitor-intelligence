import os
from datetime import datetime
from fpdf import FPDF


def clean_text(text):
    if not text:
        return ""
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
        "\u2192": "->",
        "\u2190": "<-",
        "\u2191": "^",
        "\u2193": "v",
        "\u2022": "-",
        "\u00b0": " degrees",
        "\u00e9": "e",
        "\u00e8": "e",
        "\u00ea": "e",
        "\u00e0": "a",
        "\u00e2": "a",
        "\u00f4": "o",
        "\u00fb": "u",
        "\u00fc": "u",
        "\u00ef": "i",
        "\u2154": "2/3",
        "\u00bd": "1/2",
        "\u00bc": "1/4",
        "\u00d7": "x",
        "\u00f7": "/",
        "\u2260": "!=",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u00b1": "+/-",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Competitor Intelligence Platform | Built by Himanshu | ESCP Business School Paris", align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def add_cover(pdf, target_company, competitors, generated_date):
    pdf.add_page()
    pdf.set_fill_color(26, 26, 46)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_y(80)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "Competitive Intelligence", align="C")
    pdf.ln(12)
    pdf.cell(0, 12, "Report", align="C")

    pdf.ln(16)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(180, 180, 220)
    competitors_str = clean_text(f"{target_company} vs {', '.join(competitors)}")
    pdf.cell(0, 10, competitors_str, align="C")

    pdf.ln(60)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(120, 120, 160)
    pdf.cell(0, 8, clean_text(f"Generated {generated_date}"), align="C")
    pdf.ln(6)
    pdf.cell(0, 8, "Himanshu | ESCP Business School Paris", align="C")


def add_section_title(pdf, title):
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, clean_text(title))
    pdf.ln(2)
    pdf.set_draw_color(26, 26, 46)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)


def add_executive_summary(pdf, summary):
    pdf.add_page()
    add_section_title(pdf, "Executive Summary")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.set_fill_color(240, 244, 255)
    pdf.rect(10, pdf.get_y(), 190, 4, "F")
    pdf.ln(4)
    pdf.multi_cell(190, 7, clean_text(summary))


def add_gtm_analysis(pdf, analysis):
    pdf.add_page()
    add_section_title(pdf, "GTM Motion Analysis")

    gtm_colors = {
        "PLG": (21, 87, 36),
        "SLG": (0, 64, 133),
        "PLG-SLG hybrid": (133, 100, 4),
        "Channel-led": (100, 30, 100),
        "Insufficient data": (80, 80, 80)
    }

    for company in analysis:
        gtm = company.get("gtm_motion", {})
        classification = gtm.get("classification", "N/A")
        confidence = gtm.get("confidence", "")
        rationale = gtm.get("rationale", "")
        plg = gtm.get("plg_signals", [])
        slg = gtm.get("slg_signals", [])

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 8, clean_text(company["name"]))
        pdf.ln(8)

        color = gtm_colors.get(classification, (80, 80, 80))
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*color)
        pdf.cell(60, 7, clean_text(f"  {classification}  "), border=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 7, clean_text(f"  {confidence} confidence"))
        pdf.ln(10)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(190, 6, clean_text(rationale))
        pdf.ln(2)

        if plg:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(21, 87, 36)
            pdf.cell(0, 6, "PLG signals:")
            pdf.ln(6)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(40, 40, 40)
            for s in plg[:3]:
                pdf.cell(10)
                pdf.cell(0, 5, clean_text(f"- {s}"))
                pdf.ln(5)

        if slg:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(0, 64, 133)
            pdf.cell(0, 6, "SLG signals:")
            pdf.ln(6)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(40, 40, 40)
            for s in slg[:3]:
                pdf.cell(10)
                pdf.cell(0, 5, clean_text(f"- {s}"))
                pdf.ln(5)

        pdf.ln(4)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)


def add_pricing_table(pdf, analysis):
    pdf.add_page()
    add_section_title(pdf, "Pricing Intelligence")

    headers = ["Company", "Value metric", "ICP", "Free tier", "Entry price", "Strategy"]
    widths = [35, 30, 25, 20, 35, 45]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(26, 26, 46)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, clean_text(h), border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    fill = False
    for company in analysis:
        p = company.get("pricing_intel", {})
        if fill:
            pdf.set_fill_color(245, 245, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(40, 40, 40)
        row = [
            clean_text(company["name"][:18]),
            clean_text(p.get("value_metric", "N/A")),
            clean_text(p.get("icp_signal", "N/A")),
            "Yes" if p.get("has_free_tier") else "No",
            clean_text(str(p.get("entry_price", "N/A"))[:18]),
            clean_text(p.get("competitive_strategy", "N/A"))
        ]
        for i, val in enumerate(row):
            pdf.cell(widths[i], 7, val, border=1, fill=True)
        pdf.ln()
        fill = not fill

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 8, "Pricing rationale per company:")
    pdf.ln(8)

    for company in analysis:
        p = company.get("pricing_intel", {})
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 6, clean_text(company["name"]))
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(190, 5, clean_text(p.get("rationale", "")))
        pdf.ln(4)


def add_feature_gap_matrix(pdf, analysis, jobs_to_be_done):
    pdf.add_page()
    add_section_title(pdf, "Feature Gap Matrix")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "0 = No capability   1 = With friction   2 = Does well")
    pdf.ln(8)

    company_names = [c["name"] for c in analysis]
    job_col_width = 80
    score_col_width = int((190 - job_col_width) / len(company_names))

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(26, 26, 46)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(job_col_width, 8, "Job to be done", border=1, fill=True)
    for name in company_names:
        pdf.cell(score_col_width, 8, clean_text(name[:12]), border=1, fill=True, align="C")
    pdf.ln()

    score_colors = {
        0: (192, 57, 43),
        1: (230, 126, 34),
        2: (39, 174, 96)
    }

    fill = False
    for i, job in enumerate(jobs_to_be_done):
        if fill:
            pdf.set_fill_color(245, 245, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(40, 40, 40)
        short_job = clean_text(job[:45] + "..." if len(job) > 45 else job)
        pdf.cell(job_col_width, 7, short_job, border=1, fill=True)

        for company in analysis:
            scores = company.get("job_scores", [])
            score = scores[i]["score"] if i < len(scores) else 1
            color = score_colors.get(score, (80, 80, 80))
            pdf.set_text_color(*color)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(score_col_width, 7, str(score), border=1, fill=True, align="C")

        pdf.ln()
        fill = not fill


def generate_pdf(data):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    generated_date = datetime.now().strftime("%B %d, %Y")

    add_cover(pdf, data["target_company"], data["competitors"], generated_date)
    add_executive_summary(pdf, data.get("executive_summary", ""))
    add_gtm_analysis(pdf, data.get("analysis", []))
    add_pricing_table(pdf, data.get("analysis", []))
    add_feature_gap_matrix(pdf, data.get("analysis", []), data.get("jobs_to_be_done", []))

    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/{data['target_company'].replace(' ', '_')}_report.pdf"
    pdf.output(filename)
    return filename


if __name__ == "__main__":
    import json
    with open("data/test_run.json") as f:
        data = json.load(f)
    path = generate_pdf(data)
    print(f"PDF saved to {path}")