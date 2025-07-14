import pickle
import shap
import numpy as np
import pandas as pd
import streamlit as st
from groq import Groq
import json
import logging
from backend.config import GROQ_API_KEY


# Setup basic logging
# logging.basicConfig(filename='app.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')


class LoanInsightsGenerator:
    def __init__(self):
        # Debug: Check if API key is loaded
        if not GROQ_API_KEY:
            pass  # Could raise an error or warning if desired
        try:
            self.client = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            pass  # Could raise/log error if desired

    def generate_shap_insights(self, model, X):
        try:
            # Extensive error checking
            if model is None:
                st.error("Model is None. Cannot generate SHAP insights.")
                return {}

            if X is None or len(X) == 0:
                st.error("Input data is empty or None. Cannot generate SHAP insights.")
                return {}

            # Extract the final estimator from the pipeline
            if hasattr(model, 'named_steps'):
                # Find the classifier step
                classifier_key = None
                for key, step in model.named_steps.items():
                    if hasattr(step, 'predict_proba'):
                        classifier_key = key
                        break

                if classifier_key is None:
                    st.error("No classifier found in the pipeline")
                    return {}

                final_estimator = model.named_steps[classifier_key]
            else:
                final_estimator = model

            # Ensure transformed features for SHAP
            if hasattr(model, 'named_steps'):
                # Find the preprocessor step
                preprocessor_key = None
                for key, step in model.named_steps.items():
                    if hasattr(step, 'transform'):
                        preprocessor_key = key
                        break

                if preprocessor_key:
                    X_transformed = model.named_steps[preprocessor_key].transform(X)
                else:
                    X_transformed = X
            else:
                X_transformed = X

            # Now use the final estimator with TreeExplainer
            explainer = shap.TreeExplainer(final_estimator)
            shap_values = explainer.shap_values(X_transformed)

            # Get feature names
            feature_names = X.columns.tolist()

            # Prepare feature importance dictionary
            feature_importance = {}

            # Convert shap_values to numpy array if it's a list
            if isinstance(shap_values, list):
                shap_values = np.array(shap_values)
            
            # For binary classification, use the second class if available
            if len(shap_values.shape) > 2:
                shap_values = shap_values[1]
            elif len(shap_values.shape) == 2 and shap_values.shape[0] > 1:
                # If we have multiple classes, use the second class (index 1)
                shap_values = shap_values[1]

            # Calculate absolute mean SHAP values for feature importance
            mean_shap_values = np.abs(shap_values[0])

            for name, value in zip(feature_names, mean_shap_values):
                feature_importance[name] = float(value)

            # Sort features by importance
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

            return dict(sorted_features)

        except Exception as e:
            st.error(f"Detailed Error in SHAP explanation: {e}")
            import traceback
            st.error(traceback.format_exc())
            logging.error(f"SHAP explanation error: {e}\n{traceback.format_exc()}")
            return {}

    def generate_initial_insights(self, prediction, user_data, feature_importance):
        # Format property value and LTV ratio based on home ownership
        property_value_text = "N/A" if user_data.get(
            'person_home_ownership') == "RENT" else f"₹{user_data.get('property_value_inr', 'N/A'):,}"
        ltv_ratio_text = "N/A" if user_data.get(
            'person_home_ownership') == "RENT" else f"{user_data.get('ltv_ratio', 'N/A'):.2f}%"

        # Enhanced system prompt with different approaches for approved vs rejected applications
        if prediction == 0:  # Likely to be approved
            system_prompt = f"""You are a senior loan consultant with 20 years of experience helping borrowers optimize their loan applications.
            Your job is to provide CONGRATULATORY FEEDBACK and MAINTENANCE ADVICE to the borrower.

            CRITICAL: The AI model predicts this application is LIKELY TO BE APPROVED. Focus on:
            1. Congratulating them on their strong application
            2. Explaining why their application looks good
            3. Suggesting how to maintain their strong financial position
            4. Providing tips for future loan applications
            5. Highlighting their strengths from the SHAP analysis

            IMPORTANT GUIDELINES:
            1. Start with congratulations and positive reinforcement
            2. Explain which factors are working in their favor
            3. Suggest ways to maintain or improve their already strong position
            4. Be encouraging and supportive
            5. Focus on the positive SHAP factors that are helping their application
            6. Provide advice for maintaining good financial habits
            """
        else:  # At risk of rejection
            system_prompt = f"""You are a senior loan consultant with 20 years of experience helping borrowers optimize their loan applications.
            Your job is to provide CONSTRUCTIVE FEEDBACK and IMPROVEMENT ADVICE to the borrower.

            CRITICAL: The AI model predicts this application is AT RISK OF REJECTION. Focus on:
            1. Acknowledging the challenges while maintaining hope
            2. Providing specific, actionable steps to improve their application
            3. Explaining which factors need attention based on SHAP analysis
            4. Suggesting alternative approaches or loan options
            5. Maintaining a supportive, solution-oriented tone

            IMPORTANT GUIDELINES:
            1. Acknowledge the challenges but frame them as opportunities for improvement
            2. Provide specific, practical steps they can take
            3. Focus on the most impactful factors from the SHAP analysis
            4. Suggest alternative loan options or approaches
            5. Be empathetic and supportive throughout
            6. Emphasize that many applications can be improved with the right approach
            """

        # Format SHAP feature importance for better understanding
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        feature_analysis = "\n".join([f"- {feature}: {importance:.4f} (High Impact)" for feature, importance in top_features])
        
        # Calculate loan-to-income ratio for better analysis
        loan_to_income_ratio = (user_data.get('original_loan_amnt_inr', 0) / user_data.get('original_income_inr', 1)) * 100 if user_data.get('original_income_inr', 0) > 0 else 0
        
        # Interest rate context
        interest_rate = user_data.get('loan_int_rate', 0)
        interest_rate_note = ''
        if interest_rate == 0:
            interest_rate_note = '(Note: This rate seems unrealistic for personal loans)'
        elif interest_rate < 8:
            interest_rate_note = '(Note: This is unusually low for unsecured loans in India. Typical rates are 8-25%.)'
        
        # LTI interpretation
        if loan_to_income_ratio < 30:
            lti_comment = f"Your requested loan amount of ₹{user_data.get('original_loan_amnt_inr', 0):,} is only {loan_to_income_ratio:.1f}% of your annual income, which is favorable and well within most lenders' comfort zone (typically up to 30-40%)."
        else:
            lti_comment = f"Your loan-to-income (LTI) ratio is {loan_to_income_ratio:.1f}%. Most lenders prefer this below 30-40%. Consider reducing your loan amount or increasing your income."
        
        # Home improvement while renting
        home_improvement_note = ''
        if user_data.get('person_home_ownership') == 'RENT' and user_data.get('loan_intent') == 'HOMEIMPROVEMENT':
            home_improvement_note = 'Since you are renting, clarify if the improvements are for a property you own, or if you have landlord approval for the work. Lenders may ask for this.'
        
        # More comprehensive and borrower-focused context prompt with SHAP analysis
        if prediction == 0:  # Likely to be approved
            context_prompt = f"""### 🏦 Your Loan Application Details
            - **Name:** {user_data.get('borrower_name', 'N/A')}
            - **CIBIL Score:** {user_data.get('cibil_score', 'N/A')} (Grade: {user_data.get('loan_grade', 'N/A')})
            - **Annual Income:** ₹{user_data.get('original_income_inr', 'N/A'):,}
            - **Requested Loan Amount:** ₹{user_data.get('original_loan_amnt_inr', 'N/A'):,}
            - **Loan-to-Income Ratio:** {loan_to_income_ratio:.2f}% (Loan amount as % of annual income)
            - **Loan Purpose:** {user_data.get('loan_intent', 'N/A')}
            - **Property Value:** {property_value_text}
            - **Total Existing Debt:** ₹{user_data.get('total_debt_inr', 'N/A'):,}
            - **Loan-to-Value (LTV) Ratio:** {ltv_ratio_text}
            - **Debt-to-Income (DTI) Ratio:** {user_data.get('dti_ratio', 'N/A'):.2f}%
            - **Home Ownership Status:** {user_data.get('person_home_ownership', 'N/A')}
            - **Age:** {user_data.get('person_age', 'N/A')}
            - **Employment Length:** {user_data.get('person_emp_length', 'N/A')} years
            - **Credit History Length:** {user_data.get('cb_person_cred_hist_length', 'N/A')} years
            - **Interest Rate:** {interest_rate}% {interest_rate_note}
            - **Model Prediction:** ✅ LIKELY TO BE APPROVED

            ### 🎯 AI Model Analysis - Most Important Factors (SHAP Analysis):
            {feature_analysis}

            ### Personalized Contextual Notes:
            {lti_comment}
            {home_improvement_note}

            Based on your loan application details and the AI model's analysis, I need you to:

            1. **Start with congratulations** on your strong application
            2. **Explain why your application looks promising** based on the SHAP analysis
            3. **Highlight your key strengths** that are working in your favor
            4. **Suggest ways to maintain your strong financial position** for future applications
            5. **Provide tips for the loan process** and what to expect
            6. **Explain how your positive factors** (especially the top SHAP factors) are helping your application

            The response MUST be structured with clear sections and bullet points for easy reading.
            Always address the borrower directly using "you" and "your".
            **Focus on the positive SHAP factors that are working in their favor.**
            """
        else:  # At risk of rejection
            context_prompt = f"""### 🏦 Your Loan Application Details
            - **Name:** {user_data.get('borrower_name', 'N/A')}
            - **CIBIL Score:** {user_data.get('cibil_score', 'N/A')} (Grade: {user_data.get('loan_grade', 'N/A')})
            - **Annual Income:** ₹{user_data.get('original_income_inr', 'N/A'):,}
            - **Requested Loan Amount:** ₹{user_data.get('original_loan_amnt_inr', 'N/A'):,}
            - **Loan-to-Income Ratio:** {loan_to_income_ratio:.2f}% (Loan amount as % of annual income)
            - **Loan Purpose:** {user_data.get('loan_intent', 'N/A')}
            - **Property Value:** {property_value_text}
            - **Total Existing Debt:** ₹{user_data.get('total_debt_inr', 'N/A'):,}
            - **Loan-to-Value (LTV) Ratio:** {ltv_ratio_text}
            - **Debt-to-Income (DTI) Ratio:** {user_data.get('dti_ratio', 'N/A'):.2f}%
            - **Home Ownership Status:** {user_data.get('person_home_ownership', 'N/A')}
            - **Age:** {user_data.get('person_age', 'N/A')}
            - **Employment Length:** {user_data.get('person_emp_length', 'N/A')} years
            - **Credit History Length:** {user_data.get('cb_person_cred_hist_length', 'N/A')} years
            - **Interest Rate:** {interest_rate}% {interest_rate_note}
            - **Model Prediction:** ⚠️ AT RISK OF REJECTION

            ### 🎯 AI Model Analysis - Most Important Factors (SHAP Analysis):
            {feature_analysis}

            ### Personalized Contextual Notes:
            {lti_comment}
            {home_improvement_note}

            Based on your loan application details and the AI model's analysis, I need you to:

            1. **Acknowledge the challenges** while maintaining hope and support
            2. **Identify the specific factors** that need attention based on the SHAP analysis
            3. **Provide specific, actionable steps** to improve your application, prioritizing the factors with highest impact
            4. **Suggest alternative approaches** or loan options that might work better
            5. **Explain how each factor** (especially the top SHAP factors) affects your application
            6. **Provide realistic options** based on your current financial situation

            The response MUST be structured with clear sections and bullet points for easy reading.
            Always address the borrower directly using "you" and "your".
            **Pay special attention to the SHAP feature importance analysis above when providing recommendations.**
            """

        try:
            # Using a try-except with fallback options to ensure we always get a response
            try:
                response = self.client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context_prompt}
                    ],
                    max_tokens=750,
                    temperature=0.5
                )
                return response.choices[0].message.content
            except Exception as e:
                # First fallback - try with simpler prompt
                try:
                    simplified_prompt = f"""As a loan consultant, provide advice to a borrower with:
                    - CIBIL Score: {user_data.get('cibil_score', 'N/A')}
                    - Annual Income: ₹{user_data.get('original_income_inr', 'N/A'):,}
                    - Loan Amount: ₹{user_data.get('original_loan_amnt_inr', 'N/A'):,}
                    - Purpose: {user_data.get('loan_intent', 'N/A')}
                    - Debt-to-Income: {user_data.get('dti_ratio', 'N/A'):.2f}%

                    How can they improve their application?"""

                    response = self.client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[
                            {"role": "user", "content": simplified_prompt}
                        ],
                        max_tokens=500,
                        temperature=0.5
                    )
                    return response.choices[0].message.content
                except:
                    # Final fallback - hardcoded response
                    return """
Loan Application Analysis

Thank you for submitting your loan application. Based on the information provided, here are some general recommendations:

## Key Factors to Consider

- **Your credit score** is one of the most important factors in loan approval
- **Debt-to-income ratio** significantly impacts your borrowing capacity
- **Loan purpose** can affect risk assessment and interest rates
- **Employment history** demonstrates stability to lenders

## Recommendations

1. Consider paying down existing debt before applying
2. Check your credit report for errors that might be affecting your score
3. Maintain consistent employment history
4. Save for a larger down payment if possible

Please use the chat feature below to ask specific questions about your application.
"""
        except Exception as e:
            return f"Error generating insights: {str(e)}"

    def chat_with_loan_assistant(self, context, user_query):
        # Borrower-focused system prompt with error handling guidance
        system_prompt = """You are a supportive loan advisor dedicated to helping borrowers navigate the loan application process. Your approach is:

1. BORROWER-FOCUSED: You represent the borrower's interests, not the lender's. Your primary goal is to help them secure approval or improve their financial situation.

2. EDUCATIONAL: Explain financial concepts in simple terms without financial jargon.

3. CONSTRUCTIVE: Even when discussing challenges in their application, always frame feedback as opportunities for improvement.

4. PRACTICAL: Provide specific, actionable advice that can be implemented, not vague suggestions.

5. EMPATHETIC: Acknowledge that loan applications can be stressful and maintain a supportive tone.

If you cannot confidently answer a specific question about loan requirements or processes, acknowledge this and suggest the borrower verify with their specific lender, as requirements vary between institutions.

DO NOT take the perspective of a lender or underwriter evaluating the application. You are the borrower's advocate and consultant."""

        # Enhanced chat context with better structure
        chat_context = f"""📋 COMPREHENSIVE LOAN APPLICATION ANALYSIS:
{context}

🎯 YOUR ROLE: You are a supportive loan advisor helping THE BORROWER improve their application. You have access to:
- Complete application details
- AI model prediction results
- SHAP feature importance analysis (showing which factors most impact approval)
- Financial ratios and metrics
- Initial analysis insights

💬 BORROWER'S QUESTION: {user_query}

📝 RESPONSE GUIDELINES:
- Use the SHAP feature importance data to prioritize your advice
- Reference specific numbers and metrics from their application
- Provide actionable, specific recommendations
- Be supportive and solution-oriented
- Explain financial concepts clearly
- Focus on helping them improve their approval chances

Provide detailed, personalized advice based on their specific application data and the AI analysis."""

        try:
            # Primary attempt with full context
            try:
                # Check if API key is available
                if not hasattr(self, 'client') or self.client is None:
                    return "Error: Groq client not initialized. Please check API configuration."
                
                response = self.client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chat_context}
                    ],
                    max_tokens=750,
                    temperature=0.6
                )
                return response.choices[0].message.content
            except Exception as primary_error:
                # Log the specific error for debugging
                error_msg = f"Primary API call failed: {str(primary_error)}"
                
                # Fallback with simplified prompt if the first attempt fails
                try:
                    simplified_prompt = f"""As a loan advisor helping a borrower: {user_query}"""

                    response = self.client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[
                            {"role": "system", "content": "You are a helpful loan advisor for borrowers."},
                            {"role": "user", "content": simplified_prompt}
                        ],
                        max_tokens=400,
                        temperature=0.6
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    # Log the fallback error too
                    fallback_error = f"Fallback API call also failed: {str(e)}"
                    
                    # Final fallback for complete API failure
                    return f"""I apologize, but I'm currently having trouble accessing the loan advisory system. 

Here's a general response to your question about "{user_query}":

When applying for loans, it's important to maintain a good credit score, keep your debt-to-income ratio low, and have stable employment history. Consider speaking with a financial advisor for personalized advice on your specific situation.

Please try asking your question again in a moment."""
        except Exception as e:
            return f"Error generating response: {str(e)}"


def load_model(model_path):
    try:
        with open(model_path, "rb") as file:
            model = pickle.load(file)
        return model
    except FileNotFoundError:
        st.error("❌ Model file not found. Please ensure 'pipeline_1.pkl' is in the correct directory.")
        logging.error(f"Model file not found: {model_path}")
        return None
    except (pickle.UnpicklingError, ImportError) as e:
        st.error(f"❌ Error loading model: {e}")
        logging.error(f"Error loading model: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error loading model: {e}")
        logging.error(f"Unexpected error loading model: {e}")
        return None


def get_exchange_rate():
    """
    Fetch current INR to USD exchange rate.
    Fallback to a recent approximate rate if API fails.
    """
    import requests
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/INR", timeout=5)
        response.raise_for_status()
        return response.json()['rates']['USD']
    except requests.RequestException as e:
        st.warning("⚠️ Could not fetch live exchange rate. Using fallback value.")
        logging.error(f"Exchange rate API error: {e}")
        return 0.012  # As of 2024, 1 INR ≈ 0.012 USD
    except Exception as e:
        st.warning("⚠️ Unexpected error fetching exchange rate. Using fallback value.")
        logging.error(f"Unexpected exchange rate error: {e}")
        return 0.012

def calculate_loan_grade(cibil_score):
    if cibil_score < 580:
        return 'G'
    elif cibil_score < 670:
        return 'F'
    elif cibil_score < 740:
        return 'D'
    elif cibil_score < 800:
        return 'B'
    else:
        return 'A'

def calculate_ltv_ratio(loan_amount, property_value, home_ownership):
    if home_ownership == "RENT":
        return 0
    if property_value <= 0:
        return 0
    return (loan_amount / property_value) * 100

def calculate_dti_ratio(total_debt, annual_income):
    if annual_income <= 0:
        return 0
    return (total_debt / annual_income) * 100

def prepare_user_data(
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
):
    loan_amnt = round(loan_amnt_inr * exchange_rate, 2)
    property_value = round(property_value_inr * exchange_rate, 2)
    person_income = round(person_income_inr * exchange_rate, 2)
    total_debt = round(total_debt_inr * exchange_rate, 2)
    loan_grade = calculate_loan_grade(cibil_score)
    cb_person_default_on_file = "N"
    ltv_ratio = calculate_ltv_ratio(loan_amnt_inr, property_value_inr, home_ownership)
    dti_ratio = calculate_dti_ratio(total_debt_inr, person_income_inr)
    user_input = pd.DataFrame([{
        'person_age': person_age,
        'person_income': person_income,
        'person_home_ownership': home_ownership,
        'person_emp_length': person_emp_length,
        'loan_intent': loan_intent,
        'loan_grade': loan_grade,
        'loan_amnt': loan_amnt,
        'loan_int_rate': loan_int_rate,
        'cb_person_default_on_file': cb_person_default_on_file,
        'cb_person_cred_hist_length': cb_person_cred_hist_length,
        # Add calculated financial ratios as features
        'dti_ratio': dti_ratio,
        'ltv_ratio': ltv_ratio,
        'cibil_score': cibil_score,
        'total_debt': total_debt,
        # Remove borrower_name as it shouldn't affect loan decisions
    }])
    user_data = user_input.iloc[0].to_dict()
    user_data['original_income_inr'] = person_income_inr
    user_data['original_loan_amnt_inr'] = loan_amnt_inr
    user_data['cibil_score'] = cibil_score
    user_data['property_value_inr'] = 0 if home_ownership == "RENT" else property_value_inr
    user_data['total_debt_inr'] = total_debt_inr
    user_data['ltv_ratio'] = ltv_ratio
    user_data['dti_ratio'] = dti_ratio
    return user_input, user_data, loan_grade, ltv_ratio, dti_ratio