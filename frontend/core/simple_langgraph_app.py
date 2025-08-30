"""
Simple LangGraph App - Exact Same UI/UX as Original App
"""
import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import asyncio
import uuid
from datetime import datetime
from backend.workflows import get_simple_loan_workflow
from backend.core.langgraph_core import create_initial_loan_state
from backend.database.database_service import DatabaseService
from frontend.ai.chatbot import initialize_chat_session, display_chat_history, handle_chat_interaction, start_new_chat
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SimpleLangGraphApp:
    """Simple LangGraph app that mirrors original app exactly"""
    
    def __init__(self):
        """Initialize the app"""
        self.workflow = get_simple_loan_workflow()
    
    async def process_loan_analysis(self, user_data: dict, user_id: str) -> dict:
        """Process loan analysis using simple LangGraph workflow"""
        
        # Create workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Initialize state
        initial_state = create_initial_loan_state(user_id, user_data)
        
        try:
            # Execute workflow
            print(f"🔄 Executing simple loan analysis workflow: {workflow_id}")
            result = await self.workflow.ainvoke(initial_state)
            
            # Check if workflow completed successfully
            if result.get("workflow_status") == "error":
                print(f"❌ Workflow failed: {result.get('errors', [])}")
                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": "Workflow execution failed",
                    "details": result.get("errors", [])
                }
            
            print(f"✅ Workflow completed: {workflow_id}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "result": result,
                "results": result.get("results", {}),
                "messages": result.get("messages", [])
            }
            
        except Exception as e:
            print(f"❌ Workflow error: {e}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }

def logout():
    """Logout functionality - exactly like original app"""
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
    """Display user's loan analysis history - exactly like original app"""
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
                        try:
                            data = analysis['analysis_data']
                            
                            # Debug: Show raw data structure
                            with st.expander("🔍 Debug: Raw Data Structure", expanded=False):
                                st.json(data)
                            
                            st.write(f"- Age: {data.get('person_age', 'N/A')}")
                            
                            # Safe number formatting for currency values
                            income = data.get('person_income_inr', 'N/A')
                            if isinstance(income, (int, float)):
                                st.write(f"- Income: ₹{income:,}")
                            else:
                                st.write(f"- Income: ₹{income}")
                                
                            loan_amount = data.get('loan_amnt_inr', 'N/A')
                            if isinstance(loan_amount, (int, float)):
                                st.write(f"- Loan Amount: ₹{loan_amount:,}")
                            else:
                                st.write(f"- Loan Amount: ₹{loan_amount}")
                                
                            st.write(f"- CIBIL Score: {data.get('cibil_score', 'N/A')}")
                            
                            total_debt = data.get('total_debt_inr', 'N/A')
                            if isinstance(total_debt, (int, float)):
                                st.write(f"- Total Debt: ₹{total_debt:,}")
                            else:
                                st.write(f"- Total Debt: ₹{total_debt}")
                                
                            st.write(f"- Home Ownership: {data.get('home_ownership', 'N/A')}")
                            st.write(f"- Loan Purpose: {data.get('loan_intent', 'N/A')}")
                            
                        except Exception as e:
                            st.error(f"Error displaying analysis data: {e}")
                            st.write("**Raw Analysis Data:**")
                            st.json(analysis)
                    
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
    """Main application - exactly like original app but with LangGraph backend"""
    # Initialize session state variables if not exist
    if 'username' not in st.session_state:
        st.session_state.username = "Guest User"
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = True  # Set to True for direct access
    
    # Initialize LangGraph app
    app = SimpleLangGraphApp()

    # Add sidebar with user information - exactly like original app
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

    # Loan Application Input Section - exactly like original app
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

    # Prediction and Insights Button - exactly like original app
    if st.button("Analyze My Application") or st.session_state.analysis_done:
        try:
            # If analysis is not already done, perform the analysis using LangGraph
            if not st.session_state.analysis_done:
                # Prepare user data for LangGraph workflow
                user_data = {
                    "person_age": person_age,
                    "home_ownership": home_ownership,
                    "borrower_name": borrower_name,
                    "loan_amnt_inr": loan_amnt_inr,
                    "loan_intent": loan_intent,
                    "cb_person_cred_hist_length": cb_person_cred_hist_length,
                    "property_value_inr": property_value_inr,
                    "person_income_inr": person_income_inr,
                    "person_emp_length": person_emp_length,
                    "loan_int_rate": loan_int_rate,
                    "cibil_score": cibil_score,
                    "total_debt_inr": total_debt_inr
                }
                
                # Debug: Print the data being sent
                print(f"🔍 Frontend sending data: {user_data}")
                
                # Process analysis using LangGraph
                with st.spinner("🔄 Analyzing your loan application with LangGraph..."):
                    result = asyncio.run(app.process_loan_analysis(user_data, st.session_state.get('user_id', '1')))
                
                if result["success"]:
                    # Store results in session state exactly like original app
                    results = result["results"]
                    
                    # Debug: Print the results structure
                    print(f"🔍 LangGraph results structure: {results}")
                    
                    # Store results in session state
                    st.session_state.prediction = results.get("prediction")
                    st.session_state.feature_importance = results.get("feature_importance")
                    st.session_state.user_data = results.get("user_data")
                    st.session_state.initial_insights = results.get("initial_insights")
                    st.session_state.loan_grade = results.get("loan_grade")
                    st.session_state.ltv_ratio = results.get("ltv_ratio")
                    st.session_state.dti_ratio = results.get("dti_ratio")
                    st.session_state.exchange_rate = results.get("exchange_rate")
                    st.session_state.analysis_done = True
                    
                    # Save loan analysis to database exactly like original app
                    user_id = st.session_state.get('user_id')
                    if user_id:
                        try:
                            db_service = DatabaseService()
                            
                            # Debug: Print what we're trying to save
                            print(f"🔍 Saving analysis to database:")
                            print(f"  - user_id: {user_id}")
                            print(f"  - analysis_data: {results.get('user_data')}")
                            print(f"  - prediction: {results.get('prediction')}")
                            print(f"  - feature_importance: {results.get('feature_importance')}")
                            print(f"  - insights: {results.get('initial_insights')}")
                            
                            analysis_result = db_service.save_loan_analysis(
                                user_id=int(user_id),
                                analysis_data=results.get("user_data", {}),
                                prediction=results.get("prediction", 1),
                                feature_importance=results.get("feature_importance", {}),
                                insights=results.get("initial_insights", "")
                            )
                            
                            if analysis_result["success"]:
                                st.session_state.analysis_id = analysis_result["analysis_id"]
                                st.success("✅ Analysis saved to your account")
                                print(f"✅ Analysis saved successfully with ID: {analysis_result['analysis_id']}")
                            else:
                                st.warning(f"⚠️ Could not save analysis: {analysis_result['message']}")
                                print(f"❌ Analysis save failed: {analysis_result['message']}")
                        except Exception as e:
                            st.warning(f"⚠️ Could not save analysis: {e}")
                            print(f"❌ Analysis save exception: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Clear chat history for new analysis but keep session ID exactly like original app
                    st.session_state.chat_history = []
                    st.session_state.chat_history_loaded = False
                    # Keep current_session_id to maintain chat continuity
                    st.rerun()
                else:
                    st.error(f"❌ Analysis failed: {result['error']}")
                    return

            # If analysis is already done, use stored results exactly like original app
            prediction = st.session_state.prediction
            feature_importance = st.session_state.feature_importance
            user_data = st.session_state.user_data
            initial_insights = st.session_state.initial_insights
            loan_grade = st.session_state.loan_grade
            ltv_ratio = st.session_state.ltv_ratio
            dti_ratio = st.session_state.dti_ratio
            exchange_rate = st.session_state.exchange_rate

            # Display stored results exactly like original app
            st.markdown("---")
            
            # Create a prominent prediction display for stored results exactly like original app
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
            st.markdown("### 🔍 Your Personalized Loan Application Insights")

            # Display feature importance as a bar chart with explanatory text exactly like original app
            st.subheader("Factors Affecting Your Application")
            st.write("These factors have the most impact on your loan approval chances:")
            try:
                feat_df = pd.DataFrame.from_dict(feature_importance, orient='index', columns=['Importance'])
                feat_df = feat_df.sort_values('Importance', ascending=False)
                st.bar_chart(feat_df)
            except Exception as e:
                st.error(f"❌ Error displaying feature importance: {e}")

            # Display initial insights with better formatting exactly like original app
            st.markdown("### 📝 Personalized Recommendations")
            st.markdown(initial_insights)

            # Chat interface for follow-up questions exactly like original app
            st.markdown("### 💬 Ask Questions About Your Application")
            st.write("Have questions about your loan application? Ask our loan advisor for personalized guidance.")

            # Initialize chat session exactly like original app
            initialize_chat_session()

            # Display chat history exactly like original app
            display_chat_history()

            # Generate comprehensive context for chat exactly like original app
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

            # Handle chat interaction exactly like original app
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

    # Display financial ratios in sidebar exactly like original app
    if 'analysis_done' in st.session_state and st.session_state.analysis_done:
        st.sidebar.markdown("### 📊 Your Financial Ratios")
        if st.session_state.user_data.get('person_home_ownership') == "RENT":
            st.sidebar.markdown("LTV Ratio: Not Applicable (Rental)")
        else:
            st.sidebar.markdown(f"LTV Ratio: {st.session_state.ltv_ratio:.2f}%")
        st.sidebar.markdown(f"DTI Ratio: {st.session_state.dti_ratio:.2f}%")

        # Display current exchange rate exactly like original app
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"💱 Current Exchange Rate: 1 INR = {st.session_state.exchange_rate:.4f} USD")

if __name__ == "__main__":
    main() 