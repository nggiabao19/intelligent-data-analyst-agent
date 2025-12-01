from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from src.state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def validation_node(state: AgentState):
    """Validate analysis completeness - EDA is essential, visualization is optional"""
    eda = state.get("eda_report", "")
    if eda: return {"validation_status": "SUCCESS"}
    return {"validation_status": "PARTIAL"}

def reporting_node(state: AgentState):
    print("--- REPORTING AGENT ---")
    
    eda = state.get("eda_report", "")
    query = state.get("refined_query", "")
    
    # Base system prompt - adapts like a 10-year experienced data analyst
    base_instruction = f"""
    YOU ARE A SENIOR DATA ANALYST WITH 10+ YEARS OF EXPERIENCE.
    
    INPUT:
    - User Request: "{query}" (If empty, perform general analysis).
    - EDA Results: {eda}
    
    CRITICAL RULES - MUST FOLLOW:
    1. **ONLY USE ACTUAL DATA**: Never fabricate, assume, or guess numbers/statistics
    2. **CITE SPECIFIC VALUES**: Reference exact figures from EDA results
    3. **BE HONEST**: If data is insufficient, clearly state limitations
    4. **NO SPECULATION**: Don't make up trends, patterns, or insights not visible in data
    
    CORE PRINCIPLES:
    1. **Adapt to Data Context:**
       - Sales data -> Use business language and actual KPIs from data.
       - Healthcare data -> Use medical terminology with real statistics.
       - Simple data -> Focus on what's actually present, DON'T fabricate strategies.
       
    2. **Flexible Length:**
       - General question -> Write concise, fact-based summary with real numbers.
       - Detailed question -> Provide in-depth analysis citing specific data points.
       
    3. **No Redundant Headers:**
       - DO NOT write "Part 1", "## Overview". Only write content paragraphs.
       
    4. **Evidence-Based Writing:**
       - Every claim must be supported by actual data from EDA
       - Use phrases like "Based on the data...", "The analysis shows..."
       - If uncertain, say "The available data suggests..." or "Based on limited information..."
    """
    
    # Section 1: Overview
    prompt_p1 = f"""{base_instruction}
    Write SECTION 1 (Overview):
    - What does this dataset ACTUALLY contain? (Use real column names and data types)
    - EXACT data scale (state precise row and column counts from EDA)
    - ACTUAL data quality issues (missing values, outliers - cite specific percentages)
    - Keep objective tone, report ONLY what's in the data
    
    REMEMBER: Every statement must be verifiable from the EDA results above.
    """
    
    # Section 2: Detailed Analysis
    prompt_p2 = f"""{base_instruction}
    Write SECTION 2 (Detailed Analysis):
    - Report ACTUAL findings from the data (cite specific numbers, percentages, values)
    - Describe REAL distribution patterns with concrete examples
    - If data shows trends, state them with supporting numbers
    - If data is minimal (< 5 rows), describe what's actually there without extrapolation
    
    FORBIDDEN: Making up statistics, inventing trends, or stating conclusions not supported by data.
    REQUIRED: Every insight must reference actual values from the EDA.
    """
    
    # Section 3: Insights & Actions
    prompt_p3 = f"""{base_instruction}
    Write SECTION 3 (Insights & Recommendations):
    - If data reveals clear patterns -> State them with supporting evidence from EDA
    - Provide recommendations ONLY if they logically follow from the actual data
    - If data is limited/unclear -> State: "Based on the available data, [specific limitation]. More data needed for [specific aspect]."
    - If data is trivial -> State honestly: "This dataset contains basic information only and lacks sufficient depth for strategic recommendations."
    
    CRITICAL: 
    - Don't recommend actions unsupported by the data
    - Don't make bold claims without numerical evidence
    - Be transparent about data limitations
    - If you're uncertain, say so clearly
    """
    
    res_p1 = llm.invoke([SystemMessage(content=prompt_p1)]).content.strip()
    res_p2 = llm.invoke([SystemMessage(content=prompt_p2)]).content.strip()
    res_p3 = llm.invoke([SystemMessage(content=prompt_p3)]).content.strip()
    
    def clean_text(text):
        return text.replace("##", "").strip()

    final_combined = f"{clean_text(res_p1)}|||{clean_text(res_p2)}|||{clean_text(res_p3)}"
    
    return {"final_report": final_combined}