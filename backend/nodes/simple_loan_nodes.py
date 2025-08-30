"""
Simple Loan Analysis Nodes - Mirrors Original App Exactly
"""
from langchain_core.messages import AIMessage
from backend.core.langgraph_core import LoanWorkflowState
from backend.ml.llm_utils import load_model, prepare_user_data, get_exchange_rate

async def prepare_loan_data(state: LoanWorkflowState) -> LoanWorkflowState:
    """Prepare loan data exactly like original app"""
    loan_data = state["loan_data"]
    
    try:
        # Get exchange rate
        exchange_rate = get_exchange_rate()
        
        # Prepare data exactly like original app with correct key names
        user_input, user_data, loan_grade, ltv_ratio, dti_ratio = prepare_user_data(
            person_age=loan_data.get("person_age", 30),
            home_ownership=loan_data.get("home_ownership", "RENT"),
            borrower_name=loan_data.get("borrower_name", "User"),
            loan_amnt_inr=loan_data.get("loan_amnt_inr", 100000),
            exchange_rate=exchange_rate,
            loan_intent=loan_data.get("loan_intent", "DEBTCONSOLIDATION"),
            cb_person_cred_hist_length=loan_data.get("cb_person_cred_hist_length", 5),
            property_value_inr=loan_data.get("property_value_inr", 0),
            person_income_inr=loan_data.get("person_income_inr", 500000),
            person_emp_length=loan_data.get("person_emp_length", 5),
            loan_int_rate=loan_data.get("loan_int_rate", 8.5),
            cibil_score=loan_data.get("cibil_score", 750),
            total_debt_inr=loan_data.get("total_debt_inr", 30000)
        )
        
        # Update state directly (LangGraph pattern)
        state["user_input"] = user_input
        state["user_data"] = user_data
        state["loan_grade"] = loan_grade
        state["ltv_ratio"] = ltv_ratio
        state["dti_ratio"] = dti_ratio
        state["exchange_rate"] = exchange_rate
        
        # Add to completed steps
        state["completed_steps"].append("prepare_data")
        state["current_step"] = "ml_prediction"
        state["messages"].append(AIMessage(content="✅ Data preparation completed"))
        
        print(f"🔧 Data prepared: user_input shape={user_input.shape if hasattr(user_input, 'shape') else 'no shape'}")
        print(f"🔧 State keys after prepare_data: {list(state.keys())}")
        print(f"🔧 Form data received: {loan_data}")
        
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"Data preparation error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error preparing data: {str(e)}"))
        print(f"❌ Data preparation error: {e}")
    
    return state

async def run_ml_prediction(state: LoanWorkflowState) -> LoanWorkflowState:
    """Run ML prediction exactly like original app"""
    try:
        # Check if we have the required data
        if "user_input" not in state:
            state["workflow_status"] = "error"
            state["errors"].append("Missing user_input from previous step")
            state["messages"].append(AIMessage(content="❌ Error: Missing data from previous step"))
            print(f"❌ Missing user_input in state. Available keys: {list(state.keys())}")
            return state
        
        # Load model exactly like original app
        model = load_model("backend/ml/pipeline_1.pkl")
        
        if model is None:
            state["workflow_status"] = "error"
            state["errors"].append("Model could not be loaded")
            state["messages"].append(AIMessage(content="❌ Error: Model could not be loaded"))
            return state
        
        # Get prepared data
        user_input = state["user_input"]
        
        # Make prediction exactly like original app
        prediction = model.predict(user_input)[0]
        
        # Update state directly (LangGraph pattern)
        state["prediction"] = prediction
        state["model"] = model
        
        # Add to completed steps
        state["completed_steps"].append("ml_prediction")
        state["current_step"] = "shap_analysis"
        state["messages"].append(AIMessage(content=f"🎯 ML Prediction: {'LIKELY TO BE APPROVED' if prediction == 0 else 'AT RISK OF REJECTION'}"))
        
        print(f"🎯 ML Prediction completed: prediction={prediction}")
        print(f"🎯 State keys after ml_prediction: {list(state.keys())}")
        
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"ML prediction error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error during ML prediction: {str(e)}"))
        print(f"❌ ML prediction error: {e}")
    
    return state

async def generate_shap_insights(state: LoanWorkflowState) -> LoanWorkflowState:
    """Generate SHAP insights exactly like original app"""
    try:
        # Check if we have the required data
        if "model" not in state or "user_input" not in state:
            state["workflow_status"] = "error"
            state["errors"].append("Missing model or user_input from previous steps")
            state["messages"].append(AIMessage(content="❌ Error: Missing data from previous steps"))
            print(f"❌ Missing data in state. Available keys: {list(state.keys())}")
            return state
        
        # Get data exactly like original app
        model = state["model"]
        user_input = state["user_input"]
        
        # Compute SHAP feature importance via utils
        from backend.ml.llm_utils import generate_shap_feature_importance
        feature_importance = generate_shap_feature_importance(model, user_input)
        
        # Update state directly (LangGraph pattern)
        state["feature_importance"] = feature_importance
        
        # Add to completed steps
        state["completed_steps"].append("shap_analysis")
        state["current_step"] = "generate_insights"
        state["messages"].append(AIMessage(content="📊 SHAP Analysis Complete"))
        
        print(f"📊 SHAP analysis completed: {len(feature_importance)} features")
        print(f"📊 State keys after shap_analysis: {list(state.keys())}")
        
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"SHAP analysis error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error during SHAP analysis: {str(e)}"))
        print(f"❌ SHAP analysis error: {e}")
    
    return state

async def generate_initial_insights(state: LoanWorkflowState) -> LoanWorkflowState:
    """Generate initial insights exactly like original app"""
    try:
        # Check if we have the required data
        if "prediction" not in state or "user_data" not in state or "feature_importance" not in state:
            state["workflow_status"] = "error"
            state["errors"].append("Missing data from previous steps")
            state["messages"].append(AIMessage(content="❌ Error: Missing data from previous steps"))
            print(f"❌ Missing data in state. Available keys: {list(state.keys())}")
            return state
        
        # Get data exactly like original app
        prediction = state["prediction"]
        user_data = state["user_data"]
        feature_importance = state["feature_importance"]
        
        # This legacy node remains for compatibility; conditional nodes handle LLM
        initial_insights = f"Prediction: {prediction}, Top features: {list(feature_importance)[:3]}"
        
        # Update state directly (LangGraph pattern)
        state["initial_insights"] = initial_insights
        
        # Add to completed steps
        state["completed_steps"].append("generate_insights")
        state["current_step"] = "format_response"
        state["messages"].append(AIMessage(content="💡 Initial Insights Generated"))
        
        print(f"💡 Insights generated: {len(initial_insights)} characters")
        print(f"💡 State keys after generate_insights: {list(state.keys())}")
        
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"Insights generation error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error generating insights: {str(e)}"))
        print(f"❌ Insights generation error: {e}")
    
    return state

async def format_final_response(state: LoanWorkflowState) -> LoanWorkflowState:
    """Format final response exactly like original app"""
    try:
        # Check if we have all required data
        required_keys = ["prediction", "user_data", "feature_importance", "initial_insights"]
        missing_keys = [key for key in required_keys if key not in state]
        
        if missing_keys:
            state["workflow_status"] = "error"
            state["errors"].append(f"Missing data: {missing_keys}")
            state["messages"].append(AIMessage(content=f"❌ Error: Missing data: {missing_keys}"))
            print(f"❌ Missing data in state. Available keys: {list(state.keys())}")
            return state
        
        # Mark workflow as completed
        state["workflow_status"] = "completed"
        state["current_step"] = "completed"
        
        # Store all results exactly like original app
        state["results"] = {
            "prediction": state["prediction"],
            "user_data": state["user_data"],
            "feature_importance": state["feature_importance"],
            "initial_insights": state["initial_insights"],
            "insight_type": state.get("insight_type", "unknown"),
            "loan_grade": state["loan_grade"],
            "ltv_ratio": state["ltv_ratio"],
            "dti_ratio": state["dti_ratio"],
            "exchange_rate": state["exchange_rate"]
        }
        
        # Add to completed steps
        state["completed_steps"].append("format_response")
        state["messages"].append(AIMessage(content="✅ Analysis Complete - All Results Ready"))
        
        print(f"✅ Workflow completed successfully with {len(state['completed_steps'])} steps")
        print(f"✅ Final state keys: {list(state.keys())}")
        
    except Exception as e:
        state["workflow_status"] = "error"
        state["errors"].append(f"Response formatting error: {str(e)}")
        state["messages"].append(AIMessage(content=f"❌ Error formatting response: {str(e)}"))
        print(f"❌ Response formatting error: {e}")
    
    return state 