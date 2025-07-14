# FinSage – Explainable AI Loan Approval Platform

## Overview
FinSage is an end-to-end, explainable AI platform for automated loan application analysis, approval prediction, and personalized financial guidance. It combines a modern Streamlit frontend, robust Python backend, machine learning (LightGBM), SHAP explainability, and a conversational AI assistant (Groq API) to deliver instant, transparent, and actionable insights to users.

---

## Features
- **User Authentication & Session Management**: Secure registration, login, and session handling with bcrypt-hashed passwords and session tokens.
- **Loan Application Input & Analysis**: Intuitive Streamlit UI for user data entry and real-time validation.
- **ML Model Prediction**: LightGBM model predicts loan approval with high accuracy.
- **Explainable AI (SHAP)**: SHAP values provide transparent, personalized explanations for each prediction.
- **Personalized Insights & Recommendations**: Actionable feedback and improvement steps based on user data and SHAP analysis.
- **Conversational AI Assistant**: Groq-powered chat assistant for contextual financial advice and Q&A.
- **Analysis History & Audit Trail**: Persistent storage of all analyses and chat history, linked to user accounts.
- **Secure Data Isolation**: All user data is isolated and protected using SQLAlchemy ORM and session validation.

---

## Tech Stack
- **Frontend**: Streamlit (Python)
- **Backend**: Flask-style Python modules, SQLAlchemy ORM
- **Database**: PostgreSQL (production), SQLite (local/testing)
- **Machine Learning**: LightGBM, SHAP
- **AI Assistant**: Groq API (LLM-powered chat)
- **Authentication**: bcrypt, session tokens
- **Other**: Pandas, NumPy, python-dotenv, logging

---

## Architecture
```
[User] ⇄ [Streamlit Frontend] ⇄ [Python Backend/Flask Modules]
         |                        |
         |                        └─ [ML Model (LightGBM) + SHAP]
         |                        └─ [Groq API (AI Assistant)]
         |                        └─ [SQLAlchemy ORM]
         |                        └─ [PostgreSQL/SQLite]
```

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/satyyam01/finsage
cd finsage
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Copy `.env.example` to `.env` and fill in your secrets (GROQ_API_KEY, DB credentials, etc.)

### 5. Initialize the Database
```bash
python backend/init_database.py
```

### 6. Train or Place the ML Model
- Place your trained LightGBM pipeline as `backend/pipeline_1.pkl` (or use the provided one).

### 7. Run the Application
```bash
streamlit run frontend/app.py
```

---

## Usage
- Register or log in as a user.
- Enter your loan application details in the form.
- Click "Analyze My Application" to get an instant, explainable prediction.
- View SHAP feature importance and personalized recommendations.
- Use the chat interface to ask the AI assistant for further advice.
- View your analysis and chat history in the sidebar.

---

## Security
- **Passwords** are hashed with bcrypt before storage.
- **Session tokens** are securely generated and validated for every request.
- **User data** is isolated by user ID and session.
- **Secrets** and credentials are managed via environment variables.

---

## Contribution Guidelines
1. Fork the repository and create a new branch for your feature or bugfix.
2. Write clear, well-documented code and add tests where appropriate.
3. Ensure all code passes linting and tests before submitting a PR.
4. Submit a pull request with a clear description of your changes.

---

## License
This project is licensed under the MIT License.

---

## Acknowledgements
- [LightGBM](https://github.com/microsoft/LightGBM)
- [SHAP](https://github.com/slundberg/shap)
- [Streamlit](https://streamlit.io/)
- [Groq API](https://groq.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [bcrypt](https://pypi.org/project/bcrypt/) 
