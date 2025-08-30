"""
AI Service shim for chat interactions routed through the LangGraph conversation workflow.

This module exposes a compatibility class `LoanInsightsGenerator` so existing callers
(e.g., Streamlit chat UI) can continue using a simple interface while the actual
LLM interaction is executed by the LangGraph `conversation_graph`.

It intentionally contains no duplicate ML utilities. Use `backend/ml/llm_utils.py`
for model loading, data prep, and SHAP utilities.
"""
from typing import Dict, List
from langchain_core.messages import HumanMessage, BaseMessage
from backend.workflows.conversation_graph import run_chat_turn


class LoanInsightsGenerator:
    """Compatibility shim that delegates chat to the LangGraph conversation workflow.

    Methods
    -------
    chat_with_loan_assistant(context: Dict, user_query: str) -> str
        Run one chat turn using the LangGraph conversation graph and return the
        assistant's reply as plain text.
    """

    def __init__(self) -> None:
        """Initialize the AI service shim.

        Currently stateless. Kept as a class for drop-in compatibility with the
        existing frontend integration.
        """
        pass

    def chat_with_loan_assistant(self, context: Dict, user_query: str) -> str:
        """Execute a single chat turn via LangGraph and return the assistant reply.

        Parameters
        ----------
        context : Dict
            Structured context to pass into the conversation workflow (e.g., user/session
            metadata or most recent analysis details). Must be JSON-serializable values.
        user_query : str
            The user's message to the loan assistant.

        Returns
        -------
        str
            The assistant's textual reply produced by the conversation workflow.
        """
        try:
            messages: List[BaseMessage] = [HumanMessage(content=user_query)]
            result_messages = run_chat_turn(messages, context)
            return result_messages[-1].content if result_messages else ""
        except Exception as error:
            return (
                "I couldn't process that right now. As a general tip: review your credit report, "
                f"reduce unsecured debt, and keep EMI affordability under 30% of income. ({error})"
            ) 