import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import re
from backend.database_service import DatabaseService


def validate_email(email):
    """Simple email validation"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def validate_password(password):
    """
    Password validation:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    """
    return (
            len(password) >= 8 and
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password)
    )


def login_page():
    """Login page UI"""
    st.title("🏦Login to Finsage")

    # Initialize database
    db = DatabaseService()

    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if not username or not password:
                st.error("Please fill in all fields")
            else:
                result = db.login_user(username, password)
                if result["success"]:
                    # Store login state
                    st.session_state.logged_in = True
                    st.session_state.username = result["username"]
                    st.session_state.user_id = result["user_id"]
                    st.session_state.session_token = result["session_token"]
                    st.rerun()
                else:
                    st.error(result["message"])

    # Signup link
    if st.button("Create New Account"):
        st.session_state.page = 'signup'
        st.rerun()


def signup_page():
    """Signup page UI"""
    st.title("🏦 Loan Approval Prediction App - Sign Up")

    # Initialize database
    db = DatabaseService()

    # Signup form
    with st.form("signup_form"):
        new_username = st.text_input("Choose a Username")
        email = st.text_input("Email Address")
        new_password = st.text_input("Create Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        signup_button = st.form_submit_button("Sign Up")

        if signup_button:
            # Validation checks
            if not new_username or not email or not new_password or not confirm_password:
                st.error("Please fill in all fields")
            elif not validate_email(email):
                st.error("Invalid email address")
            elif not validate_password(new_password):
                st.error("Password must be at least 8 characters long and contain uppercase, lowercase, and number")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                # Attempt to register user
                result = db.register_user(new_username, email, new_password)
                if result["success"]:
                    st.success("Account created successfully! Please log in.")
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(result["message"])

    # Back to login
    if st.button("Back to Login"):
        st.session_state.page = 'login'
        st.rerun()


def homepage():
    st.markdown("""
        <style>
        .finsage-header {
            font-size: 2.7rem;
            font-weight: 800;
            color: #2563eb;
            text-align: center;
            margin-top: 30px;
            margin-bottom: 8px;
            letter-spacing: -1px;
        }
        .finsage-tagline {
            font-size: 1.15rem;
            color: #3b4a5a;
            text-align: center;
            margin-bottom: 30px;
        }
        .feature-row {
            display: flex;
            justify-content: center;
            gap: 32px;
            margin-bottom: 30px;
        }
        .feature-card {
            background: #fff;
            border-radius: 16px;
            padding: 28px 24px;
            box-shadow: 0 4px 24px rgba(44,62,80,0.10);
            min-width: 260px;
            max-width: 320px;
            text-align: center;
            border: 1px solid #e6eaf1;
            transition: box-shadow 0.2s;
        }
        .feature-card:hover {
            box-shadow: 0 8px 32px rgba(44,62,80,0.16);
        }
        .feature-icon {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }
        .feature-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1a2639;
            margin-bottom: 6px;
        }
        .feature-desc {
            color: #4e5d6c;
            font-size: 1rem;
        }
        .center-btn-row {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        /* Style Streamlit buttons */
        div.stButton > button {
            background-color: #2563eb;
            color: #fff;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            padding: 12px 36px;
            margin: 0 12px;
            border: none;
            transition: background 0.2s;
        }
        div.stButton > button:hover {
            background-color: #1746a2;
            color: #fff;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="finsage-header">FinSage: Explainable AI Loan Approval</div>', unsafe_allow_html=True)
    st.markdown('<div class="finsage-tagline">Instant, transparent, and actionable loan insights powered by AI and explainable machine learning.</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="feature-row">
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <div class="feature-title">Explainable ML Decisions</div>
                <div class="feature-desc">Get clear approval/rejection reasons with SHAP-based feature importance for every application.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI Financial Assistant</div>
                <div class="feature-desc">Chat with an AI advisor for personalized financial guidance and Q&A.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <div class="feature-title">Secure & Private</div>
                <div class="feature-desc">Your data is protected with strong encryption, session tokens, and user isolation.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Centered blue Streamlit buttons
    st.markdown('<div class="center-btn-row">', unsafe_allow_html=True)
    center = st.columns([1, 2, 1])[1]
    with center:
        btn1, btn2 = st.columns([1, 1])
        with btn1:
            if st.button("Login", key="login_btn_home"):
                st.session_state.page = 'login'
                st.rerun()
        with btn2:
            if st.button("Sign Up", key="signup_btn_home"):
                st.session_state.page = 'signup'
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application flow"""
    # Initialize session state variables if not exist
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Routing based on session state
    if st.session_state.logged_in:
        # Import the main app here to avoid circular imports
        from frontend.app import main as app_main
        app_main()
    else:
        # Routing for authentication pages
        if st.session_state.page == 'home':
            homepage()
        elif st.session_state.page == 'login':
            login_page()
        elif st.session_state.page == 'signup':
            signup_page()


if __name__ == "__main__":
    main()