import pickle
import shap
import numpy as np
import pandas as pd
import logging
import streamlit as st


def load_model(model_path: str):
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


def get_exchange_rate() -> float:
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


def calculate_loan_grade(cibil_score: int) -> str:
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


def calculate_ltv_ratio(loan_amount: float, property_value: float, home_ownership: str) -> float:
    if home_ownership == "RENT":
        return 0
    if property_value <= 0:
        return 0
    return (loan_amount / property_value) * 100


def calculate_dti_ratio(total_debt: float, annual_income: float) -> float:
    if annual_income <= 0:
        return 0
    return (total_debt / annual_income) * 100


def prepare_user_data(
    person_age: int,
    home_ownership: str,
    borrower_name: str,
    loan_amnt_inr: float,
    exchange_rate: float,
    loan_intent: str,
    cb_person_cred_hist_length: int,
    property_value_inr: float,
    person_income_inr: float,
    person_emp_length: int,
    loan_int_rate: float,
    cibil_score: int,
    total_debt_inr: float
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
        # Calculated financial ratios as features
        'dti_ratio': dti_ratio,
        'ltv_ratio': ltv_ratio,
        'cibil_score': cibil_score,
        'total_debt': total_debt,
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


def generate_shap_feature_importance(model, X):
    try:
        if model is None or X is None or len(X) == 0:
            return {}

        # Extract the final estimator from the pipeline
        if hasattr(model, 'named_steps'):
            classifier_key = None
            for key, step in model.named_steps.items():
                if hasattr(step, 'predict_proba'):
                    classifier_key = key
                    break
            if classifier_key is None:
                return {}
            final_estimator = model.named_steps[classifier_key]
        else:
            final_estimator = model

        # Ensure transformed features for SHAP
        if hasattr(model, 'named_steps'):
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

        explainer = shap.TreeExplainer(final_estimator)
        shap_values = explainer.shap_values(X_transformed)

        feature_names = X.columns.tolist()
        feature_importance = {}

        if isinstance(shap_values, list):
            shap_values = np.array(shap_values)

        if len(shap_values.shape) > 2:
            shap_values = shap_values[1]
        elif len(shap_values.shape) == 2 and shap_values.shape[0] > 1:
            shap_values = shap_values[1]

        mean_shap_values = np.abs(shap_values[0])
        for name, value in zip(feature_names, mean_shap_values):
            feature_importance[name] = float(value)

        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_features)
    except Exception as e:
        logging.error(f"SHAP explanation error: {e}")
        return {} 