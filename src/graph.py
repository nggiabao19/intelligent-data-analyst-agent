from langgraph.graph import StateGraph, START, END
from src.state import AgentState

from src.agents.prep import query_rewriter_node, data_cleaning_node
from src.agents.analysis import eda_agent_node, viz_agent_node
from src.agents.reporting import validation_node, reporting_node

workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("rewriter", query_rewriter_node)
workflow.add_node("cleaner", data_cleaning_node)
workflow.add_node("eda", eda_agent_node)
workflow.add_node("viz", viz_agent_node)
workflow.add_node("validation", validation_node)
workflow.add_node("report", reporting_node)

def check_relevance(state: AgentState):
    if state.get("refusal_reason"):
        return END
    return "cleaner"

# Edges
workflow.add_edge(START, "rewriter")
workflow.add_conditional_edges(
    "rewriter",
    check_relevance,
    {
        END: END,
        "cleaner": "cleaner"
    }
)

workflow.add_edge("cleaner", "eda")
workflow.add_edge("cleaner", "viz")

workflow.add_edge("eda", "validation")
workflow.add_edge("viz", "validation")

workflow.add_edge("validation", "report")
workflow.add_edge("report", END)

app = workflow.compile()