"""
Core LangGraph components for FinSage application
"""
from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
from datetime import datetime
import uuid

class LoanWorkflowState(TypedDict):
    """State for loan analysis workflow"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    session_id: str
    loan_data: Dict[str, Any]
    ml_prediction: Dict[str, Any]
    context: Dict[str, Any]
    current_step: str
    workflow_status: str
    completed_steps: list[str]
    errors: list[str]
    start_time: datetime
    end_time: Optional[datetime]
    # Additional fields for workflow execution
    user_input: Optional[Any]  # DataFrame from prepare_user_data
    user_data: Optional[Dict[str, Any]]  # User data dict
    loan_grade: Optional[str]  # Calculated loan grade
    ltv_ratio: Optional[float]  # Loan-to-value ratio
    dti_ratio: Optional[float]  # Debt-to-income ratio
    exchange_rate: Optional[float]  # Exchange rate
    prediction: Optional[int]  # ML prediction result
    model: Optional[Any]  # Loaded ML model
    feature_importance: Optional[Dict[str, float]]  # SHAP feature importance
    initial_insights: Optional[str]  # Generated insights
    insight_type: Optional[str]  # Type of insights (approval/rejection)
    results: Optional[Dict[str, Any]]  # Final results

class ConversationState(TypedDict):
    """State for conversation workflow"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    session_id: str
    context: Dict[str, Any]
    intent: Optional[str]
    entities: Dict[str, Any]
    conversation_history: list[Dict[str, Any]]
    memory: Dict[str, Any]

class WorkflowMetadata(TypedDict):
    """Metadata for workflow execution"""
    workflow_id: str
    workflow_type: str
    user_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    execution_time_ms: Optional[int]

def create_initial_loan_state(user_id: str, loan_data: Dict[str, Any]) -> LoanWorkflowState:
    """Create initial state for loan analysis workflow"""
    return LoanWorkflowState(
        messages=[],
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        loan_data=loan_data,
        ml_prediction={},
        context={},
        current_step="start",
        workflow_status="running",
        completed_steps=[],
        errors=[],
        start_time=datetime.now(),
        end_time=None,
        # Initialize additional fields with None
        user_input=None,
        user_data=None,
        loan_grade=None,
        ltv_ratio=None,
        dti_ratio=None,
        exchange_rate=None,
        prediction=None,
        model=None,
        feature_importance=None,
        initial_insights=None,
        insight_type=None,
        results=None
    )

def create_initial_conversation_state(user_id: str, message: str) -> ConversationState:
    """Create initial state for conversation workflow"""
    return ConversationState(
        messages=[HumanMessage(content=message)],
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        context={},
        intent=None,
        entities={},
        conversation_history=[],
        memory={}
    ) 