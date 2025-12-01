# Intelligent Data Analyst Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?style=for-the-badge&logo=streamlit)
![OpenAI](https://img.shields.io/badge/LLM-GPT--4o-green?style=for-the-badge&logo=openai)
![License](https://img.shields.io/badge/License-MIT-grey?style=for-the-badge)

## Overview

**Intelligent Data Analyst Agent** is an enterprise-grade AI system designed to automate the end-to-end data analysis workflow. Unlike simple chatbots, this system employs a **Multi-Agent Architecture** orchestrated by **LangGraph**.

It simulates a real-world Data Team, where specialized agents (Cleaner, Analyst, Visualizer, Manager) collaborate to transform raw CSV data into professional, actionable business reports with visualizations.

### Key Differentiators
* **Dynamic Context Awareness:** The system adapts its analysis strategy based on data domain (e.g., Sales vs. Healthcare vs. Education) automatically.
* **Parallel Execution:** EDA and Visualization agents run concurrently for optimal performance.
* **Self-Correction & Robustness:** Agents act aggressively to clean "dirty" data and have fail-safe mechanisms for code execution.

---

## System Architecture

The system follows a directed cyclic graph (DAG) workflow with conditional routing and parallel processing.

```mermaid
graph LR
    %% Define Styles
    classDef user fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    classDef guard fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef worker fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef manager fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    %% Main Flow
    A[User Input + CSV File]:::user --> B{Gatekeeper Agent}:::guard
    
    B -->|Valid Request| C[Data Cleaner Agent]:::guard
    B -->|Spam/Irrelevant| Z[Refusal Response]:::output
    
    C --> D[EDA Agent]:::worker
    C --> E[Visualization Agent]:::worker
    
    D --> F{Validation Node}:::manager
    E --> F
    
    F --> G[Reporting Agent]:::manager
    
    G --> H[Streamlit UI]:::output
    G --> I[PDF Export]:::output
```

### Agent Roles

1.  **Gatekeeper (Query Rewriter):** Validates user intent, blocks irrelevant queries to save tokens, and refines technical requirements.
2.  **Data Cleaner:** Uses Python to aggressively clean data (type casting, handling missing values, removing duplicates) and creates a `cleaned_data.csv` artifact.
3.  **EDA Agent:** Scans the cleaned data to auto-detect the "Topic", "Primary Target" (Numeric), and "Primary Group" (Categorical). It passes this context to other agents to avoid assumption bias.
4.  **Viz Agent:** Automatically selects the best chart type (Line, Bar, Histogram, Scatter) based on data characteristics and generates high-quality PNG images using `matplotlib`/`seaborn`.
5.  **Reporting Agent:** Synthesizes insights from EDA and Visualizations into a structured business report (Overview -\> Detail -\> Strategy), adapting the tone to the data domain.

-----

## Features

  * **Guardrails & Safety:** Prevents processing of non-data related queries.
  * **Python Sandbox Execution:** Agents write and execute Python code in a safe environment to perform accurate calculations (no math hallucinations).
  * **Smart Visualization:**
      * *Trend Analysis:* Auto-detects Date columns and aggregates data by Month/Week.
      * *Ranking:* Automatically limits Bar Charts to Top 10 to avoid clutter.
      * *Fail-Safe:* Fallback mechanisms if specific chart types fail.
  * **Professional Reporting:**
      * Generates multi-section reports with embedded images.
      * **PDF Export** with full Unicode (Vietnamese) support.
  * **Session History:** Sidebar navigation to review past analysis sessions.

-----

## Project Structure

```bash
intelligent-data-analyst/
├── .env                    # API Keys 
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── app.py                  # Main Streamlit Application (UI Logic)
├── DejaVuSans.ttf          # Font for PDF Unicode support
└── src/
    ├── __init__.py
    ├── state.py            # Graph State definition (Shared Memory)
    ├── graph.py            # LangGraph Workflow definition
    ├── tools/
    │   └── base.py         # Python REPL Tool & Code Extractor
    └── agents/
        ├── prep.py         # Gatekeeper & Cleaner Agents
        ├── analysis.py     # EDA & Visualization Agents
        └── reporting.py    # Validation & Reporting Agents
```

-----

## Installation & Setup

### Prerequisites
  * Python 3.10 or higher
  * OpenAI API Key

### Steps

1.  **Clone the repository**

    ```bash
    git clone https://github.com/nggiabao19/intelligent-data-analyst-agent.git
    cd intelligent-data-analyst
    ```

2.  **Create and Activate Virtual Environment**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file in the root directory:

    ```env
    OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

5.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

-----



## Future Improvements
  * Add support for Local LLMs (Llama 3, Mistral) via Ollama.
  * Integrate "Human-in-the-loop" to allow users to modify the analysis plan before execution.
  * Support more data formats (Excel, JSON, SQL Databases).

## Author
*Nguyen Gia Bao*

