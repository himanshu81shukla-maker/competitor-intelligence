import streamlit as st
import json
import os
import tempfile
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline import run_full_pipeline, DEFAULT_JOBS
from pdf_export import generate_pdf

st.set_page_config(
    page_title="Competitor Intelligence Platform",
    page_icon="",
    layout="wide"
)

with open("demo_data.json") as f:
    DEMO_DATA = json.load(f)


def render_gtm_radar(analysis):
    categories = ["PLG strength", "SLG strength", "Free tier", "Enterprise focus", "Channel presence"]

    def gtm_to_scores(company):
        gtm = company.get("gtm_motion", {})
        pricing = company.get("pricing_intel", {})
        c = gtm.get("classification", "")
        plg = 5 if c == "PLG" else (3 if "hybrid" in c.lower() else 1)
        slg = 5 if c == "SLG" else (3 if "hybrid" in c.lower() else 1)
        free = 5 if pricing.get("has_free_tier") else 1
        ent = 5 if pricing.get("icp_signal") == "enterprise" else (3 if pricing.get("icp_signal") == "mid-market" else 1)
        channel = 4 if "channel" in c.lower() else 1
        return [plg, slg, free, ent, channel]

    fig = go.Figure()
    colors = px.colors.qualitative.Set2

    for i, company in enumerate(analysis):
        scores = gtm_to_scores(company)
        scores_closed = scores + [scores[0]]
        cats_closed = categories + [categories[0]]
        fig.add_trace(go.Scatterpolar(
            r=scores_closed,
            theta=cats_closed,
            fill="toself",
            name=company["name"],
            line_color=colors[i % len(colors)],
            opacity=0.65
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=True,
        height=420,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig


def render_feature_gap_chart(analysis, jobs):
    rows = []
    for company in analysis:
        for item in company.get("job_scores", []):
            rows.append({
                "Company": company["name"],
                "Job": item["job"][:40] + "..." if len(item["job"]) > 40 else item["job"],
                "Score": item["score"],
                "Rationale": item.get("rationale", "")
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()

    fig = px.bar(
        df,
        x="Job",
        y="Score",
        color="Company",
        barmode="group",
        range_y=[0, 2.2],
        height=480,
        color_discrete_sequence=px.colors.qualitative.Set2,
        hover_data={"Rationale": True}
    )
    fig.update_layout(
        xaxis_tickangle=-35,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=20, r=20, t=60, b=180),
        yaxis=dict(tickvals=[0, 1, 2], ticktext=["0 - None", "1 - Friction", "2 - Does well"])
    )
    return fig


def render_pricing_table(analysis):
    rows = []
    for company in analysis:
        p = company.get("pricing_intel", {})
        rows.append({
            "Company": company["name"],
            "Value metric": p.get("value_metric", "N/A"),
            "ICP": p.get("icp_signal", "N/A"),
            "Free tier": "Yes" if p.get("has_free_tier") else "No",
            "Entry price": p.get("entry_price") or "N/A",
            "Strategy": p.get("competitive_strategy", "N/A")
        })
    return pd.DataFrame(rows)


def render_news_timeline(analysis):
    rows = []
    for company in analysis:
        news = company.get("news_summary", "")
        if news and news != "News data unavailable.":
            rows.append({
                "Company": company["name"],
                "Summary": news[:300] + "..." if len(news) > 300 else news
            })
    return rows


def build_pdf_bytes(data):
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "report.pdf")
        from fpdf import FPDF
        from pdf_export import (
            clean_text, PDF, add_cover, add_executive_summary,
            add_gtm_analysis, add_pricing_table, add_feature_gap_matrix
        )
        from datetime import datetime
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        generated_date = datetime.now().strftime("%B %d, %Y")
        add_cover(pdf, data["target_company"], data["competitors"], generated_date)
        add_executive_summary(pdf, data.get("executive_summary", ""))
        add_gtm_analysis(pdf, data.get("analysis", []))
        add_pricing_table(pdf, data.get("analysis", []))
        add_feature_gap_matrix(pdf, data.get("analysis", []), data.get("jobs_to_be_done", []))
        pdf.output(filename)
        with open(filename, "rb") as f:
            return f.read()


st.title("Competitor Intelligence Platform")
st.caption("GTM and AI Product Portfolio Project | Himanshu | ESCP Business School Paris")
st.divider()

mode = st.radio("Mode", ["Demo (instant load)", "Live analysis"], horizontal=True)

if mode == "Demo (instant load)":
    if not DEMO_DATA:
        st.warning("demo_data.json is empty. Run the pipeline on some companies first.")
        st.stop()
    selected_company = st.selectbox(
        "Choose a pre-analysed company",
        options=list(DEMO_DATA.keys())
    )
    data = DEMO_DATA[selected_company]
    st.caption("Pre-loaded analysis. Toggle to live mode to run on any company.")

else:
    with st.form("live_form"):
        st.subheader("Run a live analysis")
        target = st.text_input("Target company", placeholder="e.g. Asana")
        competitors_raw = st.text_area(
            "Competitors (one per line, max 4)",
            placeholder="Notion\nLinear\nMonday.com\nClickUp",
            height=120
        )
        custom_jobs = st.text_area(
            "Jobs to score (one per line, leave blank for defaults)",
            height=120
        )
        submitted = st.form_submit_button("Run analysis")

    if submitted and target:
        competitor_list = [c.strip() for c in competitors_raw.split("\n") if c.strip()][:4]
        jobs_list = [j.strip() for j in custom_jobs.split("\n") if j.strip()] or DEFAULT_JOBS
        with st.spinner("Running pipeline, this takes 60-90 seconds..."):
            data = run_full_pipeline(target, competitor_list, jobs_list)
        st.session_state.live_data = data
        st.success("Analysis complete.")
    elif "live_data" in st.session_state:
        data = st.session_state.live_data
    else:
        st.info("Enter a target company and click Run analysis.")
        st.stop()

analysis = data.get("analysis", [])
jobs = data.get("jobs_to_be_done", DEFAULT_JOBS)

if not analysis:
    st.warning("No analysis data found.")
    st.stop()

all_names = [c["name"] for c in analysis]
selected_names = st.multiselect(
    "Select companies to display (max 5)",
    options=all_names,
    default=all_names[:5],
    max_selections=5
)

filtered = [c for c in analysis if c["name"] in selected_names]

if not filtered:
    st.warning("Select at least one company to display.")
    st.stop()

st.divider()

st.subheader("Executive summary")
st.write(data.get("executive_summary", "No summary available."))

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "GTM positioning",
    "Pricing intelligence",
    "Feature gaps",
    "News and signals"
])

with tab1:
    st.plotly_chart(render_gtm_radar(filtered), use_container_width=True)
    for company in filtered:
        gtm = company.get("gtm_motion", {})
        label = f"{company['name']}: {gtm.get('classification', 'N/A')} ({gtm.get('confidence', '')} confidence)"
        with st.expander(label):
            st.write(gtm.get("rationale", "No rationale available."))
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**PLG signals**")
                for s in gtm.get("plg_signals", []):
                    st.write(f"- {s}")
            with col_b:
                st.markdown("**SLG signals**")
                for s in gtm.get("slg_signals", []):
                    st.write(f"- {s}")

with tab2:
    st.dataframe(render_pricing_table(filtered), use_container_width=True, hide_index=True)
    st.divider()
    for company in filtered:
        p = company.get("pricing_intel", {})
        with st.expander(f"{company['name']} pricing rationale"):
            st.write(p.get("rationale", "No rationale available."))
            tiers = p.get("tier_names", [])
            if tiers:
                st.write("Tiers: " + ", ".join(tiers))

with tab3:
    st.plotly_chart(render_feature_gap_chart(filtered, jobs), use_container_width=True)
    st.divider()
    for company in filtered:
        with st.expander(f"{company['name']} job scores detail"):
            for item in company.get("job_scores", []):
                labels = {0: "No capability", 1: "With friction", 2: "Does well"}
                score = item.get("score", 1)
                color = {0: "red", 1: "orange", 2: "green"}.get(score, "gray")
                st.markdown(f"**{item['job']}**: :{color}[{labels.get(score, '')}]")
                st.caption(item.get("rationale", ""))

with tab4:
    news_items = render_news_timeline(filtered)
    if not news_items:
        st.info("No news data available for selected companies.")
    for item in news_items:
        with st.expander(item["Company"]):
            st.write(item["Summary"])
            reviews = next((c.get("top_reviews", {}) for c in filtered if c["name"] == item["Company"]), {})
            if reviews and (reviews.get("pros") or reviews.get("cons")):
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Customer pros**")
                    for p in reviews.get("pros", []):
                        st.write(f"- {p}")
                with col_b:
                    st.markdown("**Customer cons**")
                    for c in reviews.get("cons", []):
                        st.write(f"- {c}")

st.divider()

if st.button("Generate PDF report"):
    with st.spinner("Generating PDF..."):
        try:
            pdf_bytes = build_pdf_bytes(data)
            st.session_state.pdf_bytes = pdf_bytes
            st.session_state.pdf_company = data["target_company"]
            st.success("PDF ready.")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

if st.session_state.get("pdf_bytes"):
    st.download_button(
        label="Download PDF",
        data=st.session_state.pdf_bytes,
        file_name=f"{st.session_state.pdf_company.replace(' ', '_')}_report.pdf",
        mime="application/pdf",
        key="pdf_download"
    )