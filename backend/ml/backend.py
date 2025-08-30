"""
Deprecated: This module is kept for backward compatibility only.

- Chat: use `backend/ml/ai_service.py` (LoanInsightsGenerator) which delegates to
  the LangGraph conversation workflow.
- Utilities: import directly from `backend/ml/llm_utils.py`.

This file re-exports commonly used utilities to avoid breaking imports during the
transition and contains no duplicated logic.
"""
from backend.ml.llm_utils import (
    load_model,
    get_exchange_rate,
    calculate_loan_grade,
    calculate_ltv_ratio,
    calculate_dti_ratio,
    prepare_user_data,
    generate_shap_feature_importance as generate_shap_insights,
)

# Compatibility class import (chat goes through LangGraph)
from backend.ml.ai_service import LoanInsightsGenerator