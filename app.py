import streamlit as st
import os
import time
import uuid
from PIL import Image
from fpdf import FPDF
from langchain_core.messages import HumanMessage
from src.graph import app as agent_graph

# Cau hinh trang
st.set_page_config(page_title="Intelligent Data Analyst", layout="wide", initial_sidebar_state="expanded")

# CSS Custom
st.markdown("""
<style>
    .main-header {font-size: 28px; font-weight: bold; color: #1E88E5; margin-bottom: 20px;}
    .upload-box {border: 2px dashed #1E88E5; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;}
    .report-card {background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px; border-left: 5px solid #1E88E5;}
    .report-title {font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;}
    .report-text {font-size: 16px; line-height: 1.6; color: #34495e;}
</style>
""", unsafe_allow_html=True)

# SESSION STATE MANAGEMENT 
if "history" not in st.session_state:
    st.session_state.history = []
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

def create_pdf(p1, p2, p3):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists('DejaVuSans.ttf'):
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 14)
    else:
        pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="DATA ANALYSIS REPORT", ln=1, align='C')
    pdf.ln(10)
    
    def write_section(title, body):
        if os.path.exists('DejaVuSans.ttf'):
            pdf.set_font('DejaVu', '', 14)
            pdf.cell(200, 10, txt=title, ln=1)
            pdf.set_font('DejaVu', '', 11)
            pdf.multi_cell(0, 8, txt=body)
        else:
             # Fallback cho font Arial
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=title.encode('latin-1', 'replace').decode('latin-1'), ln=1)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, txt=body.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)

    write_section("1. Trends & Overview", p1)
    if os.path.exists("chart_1.png"):
        pdf.image("chart_1.png", x=10, w=170)
        pdf.ln(5)

    write_section("2. Detailed Analysis", p2)
    if os.path.exists("chart_2.png"):
        pdf.image("chart_2.png", x=10, w=170)
        pdf.ln(5)
        
    write_section("3. Insights & Recommendations", p3)
    
    return pdf.output(dest='S').encode('latin-1')

# SIDEBAR
with st.sidebar:
    st.title("Analysis History")
    if st.button("New Session", use_container_width=True):
        st.session_state.current_report = None
        st.rerun()
    
    st.markdown("---")
    
    # Hien thi danh sach cac bai phan tich cu
    for idx, item in enumerate(reversed(st.session_state.history)):
        # item format: {'id': ..., 'timestamp': ..., 'query': ..., 'report': ...}
        label = f"{item['timestamp']} - {item['query'][:20]}..."
        if st.button(label, key=f"hist_{item['id']}", use_container_width=True):
            st.session_state.current_report = item['report']
            st.rerun()

# MAIN UI
st.markdown('<div class="main-header">Intelligent Data Analyst Agent</div>', unsafe_allow_html=True)

# UPLOAD SECTION 
st.markdown("### Step 1: Upload File")
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    # Luu file
    file_path = "uploaded_data.csv"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.uploaded_file_path = file_path
    
    # Display preview
    import pandas as pd
    df_preview = pd.read_csv(file_path)
    with st.expander(f"Preview: {uploaded_file.name} ({df_preview.shape[0]} rows)"):
        st.dataframe(df_preview.head())
else:
    st.info("Please upload a CSV file to begin.")

# ANALYSIS SECTION 
st.markdown("---")
st.markdown("### Step 2: Analysis Request")

# Input form
with st.form(key="analysis_form"):
    user_query = st.text_area(
        "Enter your specific request (or leave blank for general analysis):",
        placeholder="Example: Analyze monthly revenue trends and compare product groups..."
    )
    
    cols = st.columns([1, 5])
    with cols[0]:
        submit_button = st.form_submit_button(label="Analyze Now", use_container_width=True)

# PROCESSING LOGIC
if submit_button:
    if not st.session_state.uploaded_file_path:
        st.error("Please upload a file to analyze")
    else:
        # Handle default prompt if user leaves blank
        final_query = user_query.strip()
        if not final_query:
            final_query = "Perform a general analysis of this dataset"
        
        # Start agent execution
        with st.spinner("Agent is reading data, creating charts, and writing report... Please wait"):
            try:
                # Goi Graph
                inputs = {
                    "messages": [HumanMessage(content=final_query)], 
                    "csv_file_path": st.session_state.uploaded_file_path
                }
                
                result = agent_graph.invoke(inputs)
                
                # Kiem tra tu choi
                if result.get("refusal_reason"):
                    st.warning(f"{result.get('refusal_reason')}")
                    st.stop()

                raw_report = result.get("final_report", "")
                
                if not raw_report:
                    st.error("Error: Unable to generate report (possible system error).")
                    st.stop()
                
                # Parse results
                parts = raw_report.split("|||")
                if len(parts) < 3: parts = [raw_report, "No Data", "No Data"]
                
                report_data = {
                    "p1": parts[0],
                    "p2": parts[1],
                    "p3": parts[2],
                    "img1": "chart_1.png" if os.path.exists("chart_1.png") else None,
                    "img2": "chart_2.png" if os.path.exists("chart_2.png") else None
                }
                
                session_id = str(uuid.uuid4())
                timestamp = time.strftime("%H:%M")
                st.session_state.history.append({
                    "id": session_id,
                    "timestamp": timestamp,
                    "query": final_query,
                    "report": report_data
                })
                
                st.session_state.current_report = report_data
                st.rerun()
                
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")

# RESULTS DISPLAY SECTION
if st.session_state.current_report:
    report = st.session_state.current_report
    
    st.markdown("### Analysis Results")
    
    with st.container():
        st.markdown('<div class="report-title">1. Data Overview</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-text">{report["p1"]}</div>', unsafe_allow_html=True)
        if report.get("img1") and os.path.exists(report["img1"]):
            image = Image.open(report["img1"])
            st.image(image, caption="Analysis Chart 1", use_container_width=True)

        st.markdown('<div class="report-title">2. Detailed Analysis</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-text">{report["p2"]}</div>', unsafe_allow_html=True)
        if report.get("img2") and os.path.exists(report["img2"]):
            image = Image.open(report["img2"])
            st.image(image, caption="Analysis Chart 2", use_container_width=True)

        st.markdown('<div class="report-title">3. Insights & Recommendations</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-text">{report["p3"]}</div>', unsafe_allow_html=True)

    # Download button
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        pdf_bytes = create_pdf(report["p1"], report["p2"], report["p3"])
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name="analysis_report.pdf",
            mime="application/pdf"
        )