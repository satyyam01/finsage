"""
LangGraph-powered conversation workflow for chat assistant
"""
from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from backend.core.config import GROQ_API_KEY


class ConversationState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: Optional[str]
    session_id: Optional[str]
    context: Dict[str, Any]
    current_step: str
    workflow_status: str
    errors: list[str]


async def input_node(state: ConversationState) -> ConversationState:
    # No-op: HumanMessage is already appended by caller
    state["current_step"] = "llm_call"
    return state


async def llm_node(state: ConversationState) -> ConversationState:
    try:
        # Build prompts similar to the previous chat_with_loan_assistant
        system_prompt = (
            "You are a supportive loan advisor for borrowers. Be clear, empathetic, and actionable."
        )
        user_query = ""
        for msg in state["messages"][::-1]:
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break

        context = state.get("context", {})
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {user_query}"},
        ]
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            max_tokens=600,
            temperature=0.6,
        )
        reply = response.choices[0].message.content
        state["messages"] = list(state["messages"]) + [AIMessage(content=reply)]
        state["current_step"] = "output"
        return state
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"LLM error: {e}")
        state["messages"] = list(state["messages"]) + [AIMessage(content=f"Sorry, I hit an error: {e}")]
        return state


async def output_node(state: ConversationState) -> ConversationState:
    state["workflow_status"] = "completed"
    state["current_step"] = "completed"
    return state


def create_conversation_graph():
    workflow = StateGraph(ConversationState)
    workflow.add_node("input", input_node)
    workflow.add_node("llm_call", llm_node)
    workflow.add_node("output", output_node)
    workflow.set_entry_point("input")
    workflow.add_edge("input", "llm_call")
    workflow.add_edge("llm_call", "output")
    workflow.add_edge("output", END)
    return workflow.compile()


def run_chat_turn(messages: Sequence[BaseMessage], context: Dict[str, Any], user_id: Optional[str] = None, session_id: Optional[str] = None) -> Sequence[BaseMessage]:
    graph = create_conversation_graph()
    initial: ConversationState = {
        "messages": messages,
        "user_id": user_id,
        "session_id": session_id,
        "context": context or {},
        "current_step": "start",
        "workflow_status": "running",
        "errors": [],
    }
    result = graph.invoke(initial)
    return result["messages"] 