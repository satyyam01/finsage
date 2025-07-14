import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from backend.backend import LoanInsightsGenerator
from backend.database_service import DatabaseService
from backend.config import GROQ_API_KEY

def initialize_chat_session():
    """Initialize chat session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    
    # Initialize database service
    if 'db_service' not in st.session_state:
        st.session_state.db_service = DatabaseService()

def display_chat_history():
    """Display existing chat messages"""
    # Load chat history from database if user is logged in and no current session
    user_id = st.session_state.get('user_id')
    if user_id and 'chat_history_loaded' not in st.session_state and not st.session_state.current_session_id:
        try:
            db_service = st.session_state.db_service
            result = db_service.get_chat_history(user_id, limit=20)
            if result["success"]:
                # Convert database format to display format
                st.session_state.chat_history = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in result["chat_history"]
                ]
                st.session_state.chat_history_loaded = True
        except Exception as e:
            st.error(f"Failed to load chat history: {e}")
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_chat_interaction(context):
    """Handle chat input and generate AI responses"""
    # Chat input
    if prompt := st.chat_input("Ask a question about your loan application"):
        # Get user info from session
        user_id = st.session_state.get('user_id')
        session_id = st.session_state.get('session_token')
        
        if not user_id:
            st.error("User session not found. Please log in again.")
            return
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        insights_generator = LoanInsightsGenerator()
        with st.chat_message("assistant"):
            response = insights_generator.chat_with_loan_assistant(context, prompt)
            st.markdown(response)

        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Save messages to database immediately
        try:
            db_service = st.session_state.db_service
            # Use current session ID if available, otherwise use user session token
            chat_session_id = st.session_state.current_session_id or session_id
            
            # Save user message
            user_msg_result = db_service.save_chat_message(user_id, chat_session_id, "user", prompt)
            if not user_msg_result["success"]:
                st.error(f"Failed to save user message: {user_msg_result['message']}")
            
            # Save assistant response
            assistant_msg_result = db_service.save_chat_message(user_id, chat_session_id, "assistant", response)
            if not assistant_msg_result["success"]:
                st.error(f"Failed to save assistant message: {assistant_msg_result['message']}")
                
        except Exception as e:
            st.error(f"Failed to save chat message: {e}")

def start_new_chat():
    """Start a new chat session"""
    # Clear current chat history
    st.session_state.chat_history = []
    st.session_state.chat_history_loaded = False
    
    # Generate a new session ID for this chat
    import uuid
    st.session_state.current_session_id = str(uuid.uuid4())
    
    # Reset analysis state to start fresh
    st.session_state.analysis_done = False
    st.session_state.prediction = None
    st.session_state.feature_importance = None
    st.session_state.user_data = None
    st.session_state.initial_insights = None
    st.session_state.analysis_id = None
    
    # Reset page state to return to main analysis form
    st.session_state.show_history = False
    
    st.success("🆕 New chat started! Previous chat history is saved.")