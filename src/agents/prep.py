import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from src.state import AgentState
from src.tools.base import python_repl_tool, extract_code

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# GATEKEEPER QUERY REWRITER
def query_rewriter_node(state: AgentState):
    print("--- QUERY REWRITER (GATEKEEPER) STARTING ---")
    
    original_query = state["messages"][-1].content
    # Default query if user input is empty
    if not original_query or not original_query.strip():
        original_query = "Perform general data analysis."

    prompt = f"""You are a Gatekeeper AI for a Data Analysis System with 10 years of expertise.
    User Input: "{original_query}"
    
    MISSION:
    1. Evaluate if this request is related to: Data Analysis, Statistics, Chart Generation, or File Exploration.
    2. Social greetings (Hi, Hello) -> Mark as INVALID and respond politely.
    3. Off-topic requests (gaming, poetry, cooking, etc.) -> INVALID.
    4. Nonsense input (random characters) -> INVALID.
    
    OUTPUT JSON FORMAT (REQUIRED):
    {{
        "status": "VALID" | "INVALID",
        "content": "Refined query or rejection message"
    }}
    
    OUTPUT LOGIC:
    - If VALID: "content" should be the refined, technically clear query.
    - If INVALID: "content" should be a polite rejection guiding user back to data analysis.
    """
    
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        # Parse JSON tu response
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        status = data.get("status", "VALID")
        payload = data.get("content", original_query)
        
        if status == "INVALID":
            print(f"Request Rejected: {payload}")
            return {"refusal_reason": payload}
        
        print(f"Request Validated: {payload}")
        return {"refined_query": payload, "refusal_reason": ""}
        
    except Exception as e:
        # Fallback neu JSON loi
        print(f"JSON Parse Error: {e}. Proceeding as valid.")
        return {"refined_query": original_query, "refusal_reason": ""}

# DATA CLEANING 
def data_cleaning_node(state: AgentState):
    print("--- DATA CLEANING AGENT WORKING ---")
    csv_path = state.get("csv_file_path", "uploaded_data.csv")
    cleaned_path = "cleaned_data.csv"
    
    prompt = f"""You are a Senior Data Engineer with 10+ years of experience.
    Source data file: '{csv_path}'.
    TASK: Write a Python script to clean the data.
    REQUIRED CODE PATTERN (STRICT):
    ```python
    import pandas as pd
    import numpy as np
    try:
        df = pd.read_csv('{csv_path}')
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                     numeric_vals = pd.to_numeric(df[col], errors='coerce')
                     if numeric_vals.isna().mean() < 0.5:
                         df[col] = numeric_vals
                except: pass
        num_cols = df.select_dtypes(include=['float', 'int']).columns
        for c in num_cols: df[c] = df[c].fillna(df[c].mean())
        cat_cols = df.select_dtypes(include=['object']).columns
        for c in cat_cols: df[c] = df[c].fillna('Unknown')
        df.drop_duplicates(inplace=True)
        df.to_csv('{cleaned_path}', index=False)
        print("Cleaning Success. Columns: " + str(list(df.columns)))
    except Exception as e: print(f"Cleaning Error: {{str(e)}}")
    ```
    """
    code_gen = llm.invoke([SystemMessage(content=prompt)])
    code = extract_code(code_gen.content)
    result = python_repl_tool.invoke(code)
    
    # Return cleaned file path if successful, otherwise return original
    if os.path.exists(cleaned_path):
        return {"cleaned_csv_path": cleaned_path}
    else:
        return {"cleaned_csv_path": csv_path}