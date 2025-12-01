from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import tool
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn
import re

import warnings 
warnings.filterwarnings("ignore")

# Khởi tạo môi trường chạy code
repl = PythonREPL()

@tool
def python_repl_tool(code: str):
    """
    Python execution tool with pandas, matplotlib, seaborn, sklearn, numpy.
    RULES: Always print results, save charts as PNG, do NOT use plt.show().
    """
    try:
        result = repl.run(code)
        return f"Execution Result:\n{result}"
    except Exception as e:
        return f"Execution Error:\n{str(e)}"

def extract_code(text: str) -> str:
    """Extract Python code from LLM response"""
    pattern = r"```python\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    pattern_generic = r"```\n(.*?)```"
    match_generic = re.search(pattern_generic, text, re.DOTALL)
    if match_generic:
        return match_generic.group(1).strip()
        
    return text.strip()