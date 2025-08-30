"""
Conditional Insight Generation Nodes for LangGraph Workflow
"""
from langchain_core.messages import AIMessage
from backend.core.langgraph_core import LoanWorkflowState
from backend.core.config import GROQ_API_KEY


async def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 800, temperature: float = 0.5) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM error: {e}"


def _format_top_features(feature_importance: dict, top_k: int = 5) -> str:
    items = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return "\n".join([f"- {k}: {v:.4f} (High Impact)" for k, v in items])


async def generate_approval_insights(state: LoanWorkflowState) -> LoanWorkflowState:
    """Generate insights for APPROVED loan applications"""
    try:
        if "prediction" not in state or "user_data" not in state or "feature_importance" not in state:
            state["workflow_status"] = "error"
            state["errors"].append("Missing data from previous steps")
            state["messages"].append(AIMessage(content="❌ Error: Missing data from previous steps"))
            print(f"❌ Missing data in state. Available keys: {list(state.keys())}")
            return state
        
        prediction = state["prediction"]
        user_data = state["user_data"]
        feature_importance = state["feature_importance"]

        property_value_text = "N/A" if user_data.get('person_home_ownership') == "RENT" else f"₹{user_data.get('property_value_inr', 'N/A'):,}"
        ltv_ratio_text = "N/A" if user_data.get('person_home_ownership') == "RENT" else f"{user_data.get('ltv_ratio', 0.0):.2f}%"
        top_features = _format_top_features(feature_importance)
        loan_to_income_ratio = (user_data.get('original_loan_amnt_inr', 0) / max(user_data.get('original_income_inr', 1), 1)) * 100
        interest_rate = user_data.get('loan_int_rate', 0)
        if interest_rate == 0:
            interest_rate_note = '(Note: This rate seems unrealistic for personal loans)'
        elif interest_rate < 8:
            interest_rate_note = '(Note: This is unusually low for unsecured loans in India. Typical rates are 8-25%.)'
        else:
            interest_rate_note = ''
        if loan_to_income_ratio < 30:
            lti_comment = f"Your requested loan amount of ₹{user_data.get('original_loan_amnt_inr', 0):,} is only {loan_to_income_ratio:.1f}% of your annual income, which is favorable."
        else:
            lti_comment = f"Your loan-to-income (LTI) ratio is {loan_to_income_ratio:.1f}%. Most lenders prefer this below 30-40%."
        home_improvement_note = ''
        if user_data.get('person_home_ownership') == 'RENT' and user_data.get('loan_intent') == 'HOMEIMPROVEMENT':
            home_improvement_note = 'Since you are renting, clarify ownership/approval for improvements; lenders may ask.'

        system_prompt = (
            "You are a senior loan consultant. Provide congratulatory feedback and maintenance advice.\n"
            "The AI model predicts LIKELY TO BE APPROVED. Be supportive, specific, and explain factors."
        )
        context_prompt = f"""### 🏦 Your Loan Application Details
- **Name:** {user_data.get('borrower_name', 'N/A')}
- **CIBIL Score:** {user_data.get('cibil_score', 'N/A')} (Grade: {user_data.get('loan_grade', 'N/A')})
- **Annual Income:** ₹{user_data.get('original_income_inr', 'N/A'):,}
- **Requested Loan Amount:** ₹{user_data.get('original_loan_amnt_inr', 'N/A'):,}
- **Loan-to-Income Ratio:** {loan_to_income_ratio:.2f}%
- **Loan Purpose:** {user_data.get('loan_intent', 'N/A')}
- **Property Value:** {property_value_text}
- **Total Existing Debt:** ₹{user_data.get('total_debt_inr', 'N/A'):,}
- **Loan-to-Value (LTV) Ratio:** {ltv_ratio_text}
- **Debt-to-Income (DTI) Ratio:** {user_data.get('dti_ratio', 0.0):.2f}%
- **Home Ownership Status:** {user_data.get('person_home_ownership', 'N/A')}
- **Age:** {user_data.get('person_age', 'N/A')}
- **Employment Length:** {user_data.get('person_emp_length', 'N/A')} years
- **Credit History Length:** {user_data.get('cb_person_cred_hist_length', 'N/A')} years
- **Interest Rate:** {interest_rate}% {interest_rate_note}
- **Model Prediction:** ✅ LIKELY TO BE APPROVED

### 🎯 AI Model Analysis - Most Important Factors (SHAP Analysis):
{top_features}

### Personalized Contextual Notes:
{lti_comment}
{home_improvement_note}

Start with congratulations; explain strengths and how to maintain them. Structure with clear sections and bullet points.
"""
        
        # Primary call with fallback
        primary = await _call_groq(system_prompt, context_prompt, max_tokens=750, temperature=0.5)
        if primary.startswith("LLM error:"):
            simplified = f"As a loan consultant, advise an approved-like profile. Top factors: {top_features}"
            fallback = await _call_groq("You are a helpful loan advisor.", simplified, max_tokens=500, temperature=0.5)
            approval_insights = fallback if not fallback.startswith("LLM error:") else (
                "Loan Application Analysis\n\nCongratulations on a strong application. Maintain timely repayments, stable income, and low DTI."
            )
        else:
            approval_insights = primary
        
        state["initial_insights"] = approval_insights
        state["insight_type"] = "approval"
        state["completed_steps"].append("generate_approval_insights")
        state["current_step"] = "format_response"
        state["messages"].append(AIMessage(content="✅ Approval Insights Generated - Your application looks strong!"))
        print(f"✅ Approval insights generated: {len(approval_insights)} characters")
        print(f"✅ State keys after approval insights: {list(state.keys())}")
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"Approval insights generation error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error generating approval insights: {str(e)}"))
        print(f"❌ Approval insights generation error: {e}")
    return state


async def generate_rejection_insights(state: LoanWorkflowState) -> LoanWorkflowState:
    """Generate insights for REJECTED loan applications"""
    try:
        if "prediction" not in state or "user_data" not in state or "feature_importance" not in state:
            state["workflow_status"] = "error"
            state["errors"].append("Missing data from previous steps")
            state["messages"].append(AIMessage(content="❌ Error: Missing data from previous steps"))
            print(f"❌ Missing data in state. Available keys: {list(state.keys())}")
            return state
        
        prediction = state["prediction"]
        user_data = state["user_data"]
        feature_importance = state["feature_importance"]

        property_value_text = "N/A" if user_data.get('person_home_ownership') == "RENT" else f"₹{user_data.get('property_value_inr', 'N/A'):,}"
        ltv_ratio_text = "N/A" if user_data.get('person_home_ownership') == "RENT" else f"{user_data.get('ltv_ratio', 0.0):.2f}%"
        top_features = _format_top_features(feature_importance)
        loan_to_income_ratio = (user_data.get('original_loan_amnt_inr', 0) / max(user_data.get('original_income_inr', 1), 1)) * 100
        interest_rate = user_data.get('loan_int_rate', 0)
        if interest_rate == 0:
            interest_rate_note = '(Note: This rate seems unrealistic for personal loans)'
        elif interest_rate < 8:
            interest_rate_note = '(Note: This is unusually low for unsecured loans in India. Typical rates are 8-25%.)'
        else:
            interest_rate_note = ''
        if loan_to_income_ratio > 40:
            lti_comment = f"Your loan-to-income (LTI) ratio is {loan_to_income_ratio:.1f}%, above typical comfort (30-40%). Consider reducing amount or increasing income."
        else:
            lti_comment = f"Your LTI ratio is {loan_to_income_ratio:.1f}%, within acceptable limits. Focus on other factors."
        home_improvement_note = ''
        if user_data.get('person_home_ownership') == 'RENT' and user_data.get('loan_intent') == 'HOMEIMPROVEMENT':
            home_improvement_note = 'Since you are renting, clarify ownership/approval for improvements; lenders may ask.'

        system_prompt = (
            "You are a senior loan consultant. Provide constructive feedback and improvement advice.\n"
            "The AI model predicts AT RISK OF REJECTION. Be empathetic, specific, and actionable."
        )
        context_prompt = f"""### 🏦 Your Loan Application Details
- **Name:** {user_data.get('borrower_name', 'N/A')}
- **CIBIL Score:** {user_data.get('cibil_score', 'N/A')} (Grade: {user_data.get('loan_grade', 'N/A')})
- **Annual Income:** ₹{user_data.get('original_income_inr', 'N/A'):,}
- **Requested Loan Amount:** ₹{user_data.get('original_loan_amnt_inr', 'N/A'):,}
- **Loan-to-Income Ratio:** {loan_to_income_ratio:.2f}%
- **Loan Purpose:** {user_data.get('loan_intent', 'N/A')}
- **Property Value:** {property_value_text}
- **Total Existing Debt:** ₹{user_data.get('total_debt_inr', 'N/A'):,}
- **Loan-to-Value (LTV) Ratio:** {ltv_ratio_text}
- **Debt-to-Income (DTI) Ratio:** {user_data.get('dti_ratio', 0.0):.2f}%
- **Home Ownership Status:** {user_data.get('person_home_ownership', 'N/A')}
- **Age:** {user_data.get('person_age', 'N/A')}
- **Employment Length:** {user_data.get('person_emp_length', 'N/A')} years
- **Credit History Length:** {user_data.get('cb_person_cred_hist_length', 'N/A')} years
- **Interest Rate:** {interest_rate}% {interest_rate_note}
- **Model Prediction:** ⚠️ AT RISK OF REJECTION

### 🎯 AI Model Analysis - Most Important Factors (SHAP Analysis):
{top_features}

### Personalized Contextual Notes:
{lti_comment}
{home_improvement_note}

Acknowledge challenges; provide prioritized, actionable steps and alternatives. Structure with sections and bullets.
"""
        
        primary = await _call_groq(system_prompt, context_prompt, max_tokens=800, temperature=0.6)
        if primary.startswith("LLM error:"):
            simplified = f"Provide constructive feedback for at-risk application. Key factors: {top_features}"
            fallback = await _call_groq("You are a supportive loan advisor.", simplified, max_tokens=500, temperature=0.5)
            rejection_insights = fallback if not fallback.startswith("LLM error:") else (
                "Loan Application Analysis - Improvement Needed\n\nAddress key factors (credit score, DTI, loan amount). Reduce debt, check credit report, and consider smaller loan."
            )
        else:
            rejection_insights = primary

        state["initial_insights"] = rejection_insights
        state["insight_type"] = "rejection"
        state["completed_steps"].append("generate_rejection_insights")
        state["current_step"] = "format_response"
        state["messages"].append(AIMessage(content="⚠️ Rejection Insights Generated - Here's how to improve your application"))
        print(f"⚠️ Rejection insights generated: {len(rejection_insights)} characters")
        print(f"⚠️ State keys after rejection insights: {list(state.keys())}")
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"Rejection insights generation error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error generating rejection insights: {str(e)}"))
        print(f"❌ Rejection insights generation error: {e}")
    return state


def route_insights_generation(state: LoanWorkflowState) -> str:
    """Route to appropriate insights generation based on prediction"""
    try:
        if "prediction" not in state:
            print("❌ No prediction data available for routing")
            return "generate_rejection_insights"
        prediction = state["prediction"]
        if prediction == 0:
            print("✅ Routing to APPROVAL insights generation")
            return "generate_approval_insights"
        else:
            print("⚠️ Routing to REJECTION insights generation")
            return "generate_rejection_insights"
    except Exception as e:
        print(f"❌ Error in routing logic: {e}")
        return "generate_rejection_insights" 