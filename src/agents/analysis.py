import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Headless mode
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from src.state import AgentState
from src.tools.base import python_repl_tool, extract_code

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ROBUST EDA AGENT
def eda_agent_node(state: AgentState):
    print("--- EDA AGENT STARTED ---")
    csv_path = state.get("cleaned_csv_path", "cleaned_data.csv")
    
    # Force JSON output for column identification
    prompt = f"""You are a Senior Data Analyst with 10+ years of experience in business intelligence.
    Data file: '{csv_path}'.
    
    MISSION:
    1. Read and analyze the dataset.
    2. Identify the 3 most important columns (return "None" if not found):
       - "date_col": Time-based column (e.g., Date, Time, Year).
       - "target_col": Primary numeric metric (e.g., Revenue, Score, Price).
       - "group_col": Primary categorical dimension (e.g., Product, Region, Category).
    3. Calculate descriptive statistics for the target column.
    
    REQUIRED PYTHON OUTPUT:
    - Print results as JSON string.
    - Format: print(json.dumps({{\"date_col\": \"...\", \"target_col\": \"...\", \"group_col\": \"...\", \"summary\": \"...\"}}))
    """
    
    try:
        raw_content = llm.invoke([SystemMessage(content=prompt)]).content
        code = extract_code(raw_content)
        # Ensure required imports
        code = "import json\nimport pandas as pd\n" + code
        
        result_str = python_repl_tool.invoke(code)
        
        # Parse JSON from output
        import re
        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
        
        data = {}
        if json_match:
            try:
                data = json.loads(json_match.group(0))
            except: pass
            
        target = data.get("target_col", "None")
        group = data.get("group_col", "None")
        date = data.get("date_col", "None")
        summary = data.get("summary", result_str)

        print(f"Auto-detected: Date='{date}', Target='{target}', Group='{group}'")
        
        return {
            "eda_report": summary,
            "primary_target": target,
            "primary_group": group
        }
    except Exception as e:
        print(f"EDA Error: {str(e)}")
        return {"eda_report": "Error in EDA."}

# SMART AGGREGATION VIZ AGENT 
def viz_agent_node(state: AgentState):
    print("--- VIZ AGENT STARTED ---")
    csv_path = state.get("cleaned_csv_path", "cleaned_data.csv")
    
    # Suggestions from EDA phase
    target_col = state.get("primary_target", "None")
    group_col = state.get("primary_group", "None")
    
    # Clean up old charts
    for f in ["chart_1.png", "chart_2.png"]:
        if os.path.exists(f): os.remove(f)

    # Professional visualization workflow
    prompt = f"""You are a Visualization Expert with 10+ years in business analytics.
    Data file: '{csv_path}'.
    Suggested columns - Target: '{target_col}', Group: '{group_col}'.
    
    MISSION: Create 2 professional, data-driven charts with CLEAR LABELS and ACCURATE DATA.
    
    CRITICAL RULES:
    1. NEVER fabricate or assume data - ONLY use actual values from the dataset
    2. ALL charts MUST have: clear title, axis labels, legends (if needed), and proper formatting
    3. Column names MUST match actual columns in the CSV file
    4. Handle missing/invalid data gracefully
    
    VISUALIZATION LOGIC (MANDATORY):
    1. Setup:
       - `import pandas as pd`
       - `import matplotlib.pyplot as plt`
       - `import seaborn as sns`
       - `import numpy as np`
       - `df = pd.read_csv('{csv_path}')`
       - `sns.set_theme(style="whitegrid")`
    
    2. Auto-detect columns:
       - Find date column: Check for datetime-like columns or columns with 'date', 'time', 'year' in name
       - Find numeric column: Use `df.select_dtypes(include=['number']).columns` 
       - Find categorical column: Use `df.select_dtypes(include=['object']).columns`
    
    3. CHART 1: TIME SERIES or DISTRIBUTION
       - If date column found:
         + Convert to datetime: `df[date_col] = pd.to_datetime(df[date_col], errors='coerce')`
         + Drop NaT values: `df = df.dropna(subset=[date_col])`
         + Aggregate by month: `df_agg = df.groupby(pd.Grouper(key=date_col, freq='M'))[numeric_col].sum().reset_index()`
         + Plot line chart with proper x-axis formatting
         + Title: 'Trend Over Time'
       - Else: Plot histogram of first numeric column
       - Save as `chart_1.png` and close figure
    
    4. CHART 2: RANKING or BOXPLOT
       - If categorical column exists:
         + Group by category: `df_rank = df.groupby(cat_col)[numeric_col].sum().nlargest(10).reset_index()`
         + Plot horizontal bar chart (barh)
         + Title: 'Top 10 Categories'
       - Else: Plot boxplot of numeric column
       - Save as `chart_2.png` and close figure
    
    5. CODE STRUCTURE (REQUIRED):
    ```python
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    
    try:
        # Load and validate data
        df = pd.read_csv('{csv_path}')
        print(f"Dataset loaded: {{df.shape[0]}} rows, {{df.shape[1]}} columns")
        print(f"Columns: {{list(df.columns)}}")
        
        sns.set_theme(style="whitegrid")
        
        # Auto-detect columns ONLY from actual data
        date_col = None
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col], errors='raise')
                    date_col = col
                    print(f"Date column detected: {{date_col}}")
                    break
                except:
                    pass
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = [c for c in df.select_dtypes(include=['object']).columns.tolist() if c != date_col]
        
        val_col = numeric_cols[0] if numeric_cols else None
        cat_col = cat_cols[0] if cat_cols else None
        
        print(f"Selected columns - Numeric: {{val_col}}, Category: {{cat_col}}, Date: {{date_col}}")
        
        # Chart 1: Time series or histogram
        plt.figure(figsize=(10, 6))
        if date_col and val_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df_clean = df.dropna(subset=[date_col, val_col])
            df_agg = df_clean.groupby(pd.Grouper(key=date_col, freq='M'))[val_col].sum().reset_index()
            plt.plot(df_agg[date_col], df_agg[val_col], marker='o', linewidth=2, markersize=6)
            plt.title(f'Trend of {{val_col}} Over Time', fontsize=14, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel(f'Total {{val_col}}', fontsize=12)
            plt.grid(True, alpha=0.3)
            # Add value labels on points for clarity
            for idx, row in df_agg.iterrows():
                if idx % max(1, len(df_agg)//10) == 0:  # Show every 10th label to avoid clutter
                    plt.text(row[date_col], row[val_col], f'{{row[val_col]:.0f}}', 
                            fontsize=9, ha='center', va='bottom')
        elif val_col:
            df[val_col].hist(bins=min(20, len(df)//5), edgecolor='black')
            plt.title(f'Distribution of {{val_col}}', fontsize=14, fontweight='bold')
            plt.xlabel(val_col, fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('chart_1.png', dpi=100, bbox_inches='tight')
        plt.close()
        print("Chart 1 saved successfully")
        
        # Chart 2: Ranking or boxplot
        plt.figure(figsize=(10, 6))
        if cat_col and val_col:
            df_rank = df.groupby(cat_col)[val_col].sum().nlargest(10).sort_values().reset_index()
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_rank)))
            bars = plt.barh(df_rank[cat_col], df_rank[val_col], color=colors, edgecolor='black')
            plt.title(f'Top 10 {{cat_col}} by Total {{val_col}}', fontsize=14, fontweight='bold')
            plt.xlabel(f'Total {{val_col}}', fontsize=12)
            plt.ylabel(cat_col, fontsize=12)
            # Add value labels on bars
            for idx, (bar, val) in enumerate(zip(bars, df_rank[val_col])):
                plt.text(val, bar.get_y() + bar.get_height()/2, f' {{val:.0f}}', 
                        va='center', fontsize=10)
            plt.grid(True, alpha=0.3, axis='x')
        elif val_col:
            bp = df.boxplot(column=val_col, patch_artist=True, return_type='dict')
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
            plt.title(f'Distribution Analysis of {{val_col}}', fontsize=14, fontweight='bold')
            plt.ylabel(val_col, fontsize=12)
            plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig('chart_2.png', dpi=100, bbox_inches='tight')
        plt.close()
        print("Chart 2 saved successfully")
        
        print("All charts created successfully with actual data")
    except Exception as e:
        print(f"Visualization error: {{str(e)}}")
        import traceback
        traceback.print_exc()
    ```
    
    IMPORTANT: Return complete working code with proper error handling.
    """
    
    raw_content = llm.invoke([SystemMessage(content=prompt)]).content
    code = extract_code(raw_content)
    
    # Execute visualization code
    exec_result = python_repl_tool.invoke(code)
    print(f"Viz Log: {exec_result}")
    
    images = []
    if os.path.exists("chart_1.png"): images.append("chart_1.png")
    if os.path.exists("chart_2.png"): images.append("chart_2.png")
    
    return {"viz_images": images}