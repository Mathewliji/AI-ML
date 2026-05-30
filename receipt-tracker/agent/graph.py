from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.nodes import extract_node, categorise_node, save_node, query_node, respond_node


def _route(state: AgentState) -> str:
    if state.get("error"):
        return "respond"
    return state["task"]


workflow = StateGraph(AgentState)

workflow.add_node("extract", extract_node)
workflow.add_node("categorise", categorise_node)
workflow.add_node("save", save_node)
workflow.add_node("query", query_node)
workflow.add_node("respond", respond_node)

workflow.add_conditional_edges(START, _route, {
    "upload": "extract",
    "query": "query",
    "respond": "respond",
})

workflow.add_edge("extract", "categorise")
workflow.add_edge("categorise", "save")
workflow.add_edge("save", "respond")
workflow.add_edge("query", "respond")
workflow.add_edge("respond", END)

graph = workflow.compile()
