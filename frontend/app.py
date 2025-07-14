import os
import sys

# Insert project root at the start of sys.path BEFORE any other imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import json
import requests
from backend.backend import load_model, LoanInsightsGenerator, prepare_user_data, get_exchange_rate
from backend.database_service import DatabaseService
from frontend.chatbot import initialize_chat_session, display_chat_history, handle_chat_interaction, start_new_chat
from dotenv import load_dotenv
from backend.config import GROQ_API_KEY




# Load environment variables from .env file
load_dotenv()

# Load the trained model pipeline
MODEL_PATH = r"backend/pipeline_1.pkl"  # Update this path as needed
model = load_model(MODEL_PATH)


def logout():
    """Logout functionality"""
    # Logout from database
    session_token = st.session_state.get('session_token')
    if session_token:
        try:
            db_service = DatabaseService()
            db_service.logout_user(session_token)
        except Exception as e:
            st.error(f"Logout error: {e}")
    
    # Clear session state
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.session_token = None
    st.session_state.chat_history = []
    st.session_state.chat_history_loaded = False
    st.session_state.current_session_id = None
    st.rerun()

def display_analysis_history():
    """Display user's loan analysis history"""
    st.title("📊 Your Loan Analysis History")
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("User session not found. Please log in again.")
        return
    
    try:
        db_service = DatabaseService()
        result = db_service.get_loan_analyses(user_id, limit=10)
        
        if result["success"] and result["analyses"]:
            st.write(f"Found {len(result['analyses'])} previous analyses:")
            
            for i, analysis in enumerate(result["analyses"]):
                with st.expander(f"Analysis #{analysis['id']} - {analysis['created_at'][:10]}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Prediction:**")
                        if analysis['prediction'] == 0:
                            st.markdown("""
                            <div style="background-color: #d4edda; border: 1px solid #28a745; border-radius: 5px; padding: 10px; text-align: center;">
                                <strong style="color: #155724;">🎉 LIKELY TO BE APPROVED</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background-color: #f8d7da; border: 1px solid #dc3545; border-radius: 5px; padding: 10px; text-align: center;">
                                <strong style="color: #721c24;">⚠️ AT RISK OF REJECTION</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.write("**Key Data:**")
                        data = analysis['analysis_data']
                        st.write(f"- Age: {data.get('person_age', 'N/A')}")
                        st.write(f"- Income: ₹{data.get('original_income_inr', 'N/A'):,}")
                        st.write(f"- Loan Amount: ₹{data.get('original_loan_amnt_inr', 'N/A'):,}")
                        st.write(f"- CIBIL Score: {data.get('cibil_score', 'N/A')}")
                    
                    with col2:
                        st.write("**Feature Importance:**")
                        if analysis['feature_importance']:
                            # Show top 3 features
                            sorted_features = sorted(analysis['feature_importance'].items(), 
                                                   key=lambda x: x[1], reverse=True)[:3]
                            for feature, importance in sorted_features:
                                st.write(f"- {feature}: {importance:.3f}")
                        else:
                            st.write("No feature importance data")
                    
                    st.write("**Insights:**")
                    st.write(analysis['insights'] or "No insights available")
        else:
            st.info("No previous analyses found. Run your first analysis to see it here!")
            
    except Exception as e:
        st.error(f"Failed to load analysis history: {e}")


def main():
    # Initialize session state variables if not exist
    if 'username' not in st.session_state:
        st.session_state.username = "Guest User"
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = True  # Set to True for direct access
    
    # Exchange rate (fetch or use fallback)
    exchange_rate = get_exchange_rate()

    # Add sidebar with user information
    st.sidebar.title(f"👤 Welcome, {st.session_state.username}")
    st.sidebar.markdown("---")

    # Add logout button in sidebar
    if st.sidebar.button("🚪 Logout"):
        logout()
    
    # Add analysis history button
    if st.sidebar.button("📊 View Analysis History"):
        st.session_state.show_history = True
        st.rerun()
    
    # Add new chat button
    if st.sidebar.button("🆕 New Chat", help="Start a fresh analysis and chat"):
        start_new_chat()
        st.rerun()

    st.title("🎯Loan Application Assistant")
    st.write("Get personalized advice to improve your loan approval chances")

    # Initialize session state for tracking analysis state
    if 'analysis_done' not in st.session_state:
        st.session_state.analysis_done = False
    
    # Show analysis history if requested
    if st.session_state.get('show_history', False):
        display_analysis_history()
        if st.button("← Back to Analysis"):
            st.session_state.show_history = False
            st.rerun()
        return

    # Loan Application Input Section
    st.markdown("### 📋 Your Information")

    # Create columns for input
    col1, col2 = st.columns(2)

    with col1:
        person_age = st.number_input("Age", min_value=18, max_value=100, value=30, help="Your current age")
        home_ownership = st.selectbox("Home Ownership", ["RENT", "MORTGAGE", "OWN", "OTHER"])
        borrower_name = st.text_input("Your Name", help="Enter your full name")
        loan_amnt_inr = st.number_input("Requested Loan Amount (₹)", min_value=0, value=10_00_000, step=50_000)
        loan_intent = st.selectbox("Loan Purpose",
                                   ["MEDICAL", "DEBTCONSOLIDATION", "HOME IMPROVEMENT", "VENTURE", "PERSONAL",
                                    "EDUCATION"])
        cb_person_cred_hist_length = st.number_input("Credit History Length (years)", min_value=0, value=10,
                                                     max_value=60)
        property_value_disabled = home_ownership == "RENT"
        property_value_help = "Not applicable for RENT status" if property_value_disabled else "Current market value of property"
        property_value_inr = st.number_input(
            "Property Value (₹)",
            min_value=0,
            value=0 if property_value_disabled else 50_00_000,
            step=1_00_000,
            disabled=property_value_disabled,
            help=property_value_help
        )
        if property_value_disabled:
            property_value_inr = 0

    with col2:
        person_income_inr = st.number_input("Annual Income (₹)", min_value=0, value=10_00_000, step=50_000)
        person_emp_length = st.number_input("Employment Length (years)", min_value=0, max_value=50, value=5)
        loan_int_rate = st.slider("Interest Rate (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.1)
        cibil_score = st.number_input("CIBIL Score", min_value=300, max_value=900, value=700,
                                      help="Credit score between 300-900")
        total_debt_inr = st.number_input("Total Existing Debt (₹)", min_value=0, value=5_00_000, step=50_000,
                                         help="Sum of all current outstanding debts")

    # Prepare all data using backend
    user_input, user_data, loan_grade, ltv_ratio, dti_ratio = prepare_user_data(
        person_age,
        home_ownership,
        borrower_name,
        loan_amnt_inr,
        exchange_rate,
        loan_intent,
        cb_person_cred_hist_length,
        property_value_inr,
        person_income_inr,
        person_emp_length,
        loan_int_rate,
        cibil_score,
        total_debt_inr
    )
    st.info(f"Calculated Loan Grade: {loan_grade}")
    
    # Validation warnings for unrealistic values
    if loan_int_rate == 0:
        st.warning("⚠️ **Interest Rate Warning**: 0% interest rate is unrealistic for personal loans. Typical rates range from 8-25% depending on credit score and loan terms.")
    
    if loan_amnt_inr < 10000:
        st.info("💡 **Small Loan Amount**: Your requested amount is relatively small. This may be viewed positively by lenders as it represents lower risk.")
    
    if dti_ratio > 40:
        st.warning(f"⚠️ **High DTI Ratio**: Your debt-to-income ratio of {dti_ratio:.1f}% is above the recommended 40% threshold. Consider reducing existing debt before applying.")

    # Display financial ratios in sidebar
    st.sidebar.markdown("### 📊 Your Financial Ratios")
    if home_ownership == "RENT":
        st.sidebar.markdown("LTV Ratio: Not Applicable (Rental)")
    else:
        st.sidebar.markdown(f"LTV Ratio: {ltv_ratio:.2f}%")
    st.sidebar.markdown(f"DTI Ratio: {dti_ratio:.2f}%")

    # Display current exchange rate
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"💱 Current Exchange Rate: 1 INR = {exchange_rate:.4f} USD")

    # Prediction and Insights Button
    if st.button("Analyze My Application") or st.session_state.analysis_done:
        if model is not None:
            try:
                # If analysis is not already done, perform the analysis
                if not st.session_state.analysis_done:
                    try:
                        # Make prediction
                        prediction = model.predict(user_input)[0]
                    except Exception as e:
                        st.error(f"❌ Error during prediction: {e}")
                        import traceback
                        st.error(traceback.format_exc())
                        return

                    # Display prominent prediction result
                    st.markdown("---")
                    
                    # Create a prominent prediction display
                    if prediction == 0:
                        st.balloons()
                        st.markdown("""
                        <div style="background-color: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                            <h2 style="color: #155724; margin: 0;">🎉 LIKELY TO BE APPROVED</h2>
                            <p style="color: #155724; font-size: 18px; margin: 10px 0;">Your loan application shows strong indicators for approval!</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                            <h2 style="color: #721c24; margin: 0;">⚠️ AT RISK OF REJECTION</h2>
                            <p style="color: #721c24; font-size: 18px; margin: 10px 0;">Your application may need improvements to increase approval chances.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")

                    # Initialize Insights Generator
                    insights_generator = LoanInsightsGenerator()

                    # Generate SHAP Feature Importance
                    try:
                        feature_importance = insights_generator.generate_shap_insights(model, user_input)
                    except Exception as e:
                        st.error(f"❌ Error generating feature importance: {e}")
                        import traceback
                        st.error(traceback.format_exc())
                        feature_importance = {}

                    # Store results in session state
                    st.session_state.prediction = prediction
                    st.session_state.feature_importance = feature_importance
                    st.session_state.user_data = user_data

                    # Generate and display initial insights
                    try:
                        initial_insights = insights_generator.generate_initial_insights(
                            prediction,
                            user_data,
                            feature_importance
                        )
                    except Exception as e:
                        st.error(f"❌ Error generating initial insights: {e}")
                        import traceback
                        st.error(traceback.format_exc())
                        initial_insights = "Error generating insights."
                    st.session_state.initial_insights = initial_insights
                    st.session_state.analysis_done = True
                    
                    # Save loan analysis to database
                    user_id = st.session_state.get('user_id')
                    if user_id:
                        try:
                            db_service = DatabaseService()
                            analysis_result = db_service.save_loan_analysis(
                                user_id=user_id,
                                analysis_data=user_data,
                                prediction=prediction,
                                feature_importance=feature_importance,
                                insights=initial_insights
                            )
                            if analysis_result["success"]:
                                st.session_state.analysis_id = analysis_result["analysis_id"]
                                st.success("✅ Analysis saved to your account")
                            else:
                                st.warning(f"⚠️ Could not save analysis: {analysis_result['message']}")
                        except Exception as e:
                            st.warning(f"⚠️ Could not save analysis: {e}")
                    
                    # Clear chat history for new analysis but keep session ID
                    st.session_state.chat_history = []
                    st.session_state.chat_history_loaded = False
                    # Keep current_session_id to maintain chat continuity
                    st.rerun()

                # If analysis is already done, use stored results
                prediction = st.session_state.prediction
                feature_importance = st.session_state.feature_importance
                user_data = st.session_state.user_data
                initial_insights = st.session_state.initial_insights

                # Display stored results
                # Show prediction result prominently
                st.markdown("---")
                
                # Create a prominent prediction display for stored results
                if prediction == 0:
                    st.markdown("""
                    <div style="background-color: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h2 style="color: #155724; margin: 0;">🎉 LIKELY TO BE APPROVED</h2>
                        <p style="color: #155724; font-size: 18px; margin: 10px 0;">Your loan application shows strong indicators for approval!</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h2 style="color: #721c24; margin: 0;">⚠️ AT RISK OF REJECTION</h2>
                        <p style="color: #721c24; font-size: 18px; margin: 10px 0;">Your application may need improvements to increase approval chances.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 🔍 Your Personalized Loan Application Insights")

                # Display feature importance as a bar chart with explanatory text
                st.subheader("Factors Affecting Your Application")
                st.write("These factors have the most impact on your loan approval chances:")
                try:
                    feat_df = pd.DataFrame.from_dict(feature_importance, orient='index', columns=['Importance'])
                    feat_df = feat_df.sort_values('Importance', ascending=False)
                    st.bar_chart(feat_df)
                except Exception as e:
                    st.error(f"❌ Error displaying feature importance: {e}")

                # Display initial insights with better formatting
                st.markdown("### 📝 Personalized Recommendations")
                st.markdown(initial_insights)

                # Chat interface for follow-up questions
                st.markdown("### 💬 Ask Questions About Your Application")
                st.write("Have questions about your loan application? Ask our loan advisor for personalized guidance.")

                # Chat interface for follow-up questions

                # Initialize chat session
                initialize_chat_session()

                # Display chat history
                display_chat_history()

                # Generate comprehensive context for chat
                context = f"""🏦 LOAN APPLICATION ANALYSIS CONTEXT

📊 PREDICTION RESULT:
- Model Prediction: {'LIKELY TO BE APPROVED' if prediction == 0 else 'AT RISK OF REJECTION'}
- Confidence Level: Based on ML model analysis

👤 APPLICANT PROFILE:
- Name: {user_data.get('borrower_name', 'N/A')}
- Age: {user_data.get('person_age', 'N/A')} years
- Annual Income: ₹{user_data.get('original_income_inr', 'N/A'):,}
- Employment Length: {user_data.get('person_emp_length', 'N/A')} years
- Credit History Length: {user_data.get('cb_person_cred_hist_length', 'N/A')} years
- CIBIL Score: {user_data.get('cibil_score', 'N/A')}
- Home Ownership: {user_data.get('person_home_ownership', 'N/A')}

💰 LOAN DETAILS:
- Requested Amount: ₹{user_data.get('original_loan_amnt_inr', 'N/A'):,}
- Loan Purpose: {user_data.get('loan_intent', 'N/A')}
- Interest Rate: {user_data.get('loan_int_rate', 'N/A')}%
- Loan Grade: {user_data.get('loan_grade', 'N/A')}
- Total Existing Debt: ₹{user_data.get('total_debt_inr', 'N/A'):,}

📈 FINANCIAL RATIOS:
- Debt-to-Income (DTI) Ratio: {user_data.get('dti_ratio', 'N/A'):.2f}%
- Loan-to-Value (LTV) Ratio: {user_data.get('ltv_ratio', 'N/A'):.2f}% if applicable
- Property Value: ₹{user_data.get('property_value_inr', 'N/A'):,} (if applicable)

🎯 SHAP FEATURE IMPORTANCE (Top Factors):
{chr(10).join([f"- {feature}: {importance:.4f}" for feature, importance in list(feature_importance.items())[:5]])}

💡 INITIAL ANALYSIS INSIGHTS:
{initial_insights}

🔍 CONTEXT FOR CHAT:
This data represents a comprehensive loan application analysis. The SHAP feature importance shows which factors most significantly impact the loan approval decision. The financial ratios provide key metrics lenders consider. Use this context to provide specific, actionable advice to the borrower."""

                # Handle chat interaction
                try:
                    handle_chat_interaction(context)
                except Exception as e:
                    st.error(f"❌ Error in chat interaction: {e}")
                    import traceback
                    st.error(traceback.format_exc())

            except Exception as e:
                st.error(f"❌ Error during assessment: {e}")
                import traceback
                st.error(traceback.format_exc())
        else:
            st.error("Model is not loaded. Cannot perform prediction.")


if __name__ == "__main__":
    main()