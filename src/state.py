from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
import operator

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    csv_file_path: str
    cleaned_csv_path: str
    refined_query: str
    refusal_reason: str
    primary_target: str
    primary_group: str
    eda_report: str
    viz_images: Annotated[List[str], operator.add] 
    validation_status: str
    final_report: str