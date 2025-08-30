"""
Simple Loan Analysis Workflow - Mirrors Original App Exactly
"""
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from backend.core.langgraph_core import LoanWorkflowState
from backend.nodes.simple_loan_nodes import (
    prepare_loan_data,
    run_ml_prediction,
    generate_shap_insights,
    format_final_response
)
from backend.nodes.conditional_insight_nodes import (
    generate_approval_insights,
    generate_rejection_insights,
    route_insights_generation
)

def create_simple_loan_workflow():
    """Create a simple workflow that mirrors the original app"""
    
    # Create the workflow graph
    workflow = StateGraph(LoanWorkflowState)
    
    # Add nodes
    workflow.add_node("prepare_data", prepare_loan_data)
    workflow.add_node("ml_prediction", run_ml_prediction)
    workflow.add_node("shap_analysis", generate_shap_insights)
    workflow.add_node("generate_approval_insights", generate_approval_insights)
    workflow.add_node("generate_rejection_insights", generate_rejection_insights)
    workflow.add_node("format_response", format_final_response)
    
    # Set entry point
    workflow.set_entry_point("prepare_data")
    
    # Add edges with conditional routing
    workflow.add_edge("prepare_data", "ml_prediction")
    workflow.add_edge("ml_prediction", "shap_analysis")
    workflow.add_conditional_edges(
        "shap_analysis",
        route_insights_generation,
        {
            "generate_approval_insights": "generate_approval_insights",
            "generate_rejection_insights": "generate_rejection_insights"
        }
    )
    workflow.add_edge("generate_approval_insights", "format_response")
    workflow.add_edge("generate_rejection_insights", "format_response")
    workflow.add_edge("format_response", END)
    
    return workflow.compile()

# Workflow factory function
def get_simple_loan_workflow():
    """Get the compiled simple loan analysis workflow"""
    return create_simple_loan_workflow() 