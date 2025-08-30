# FinSage – Explainable AI Loan Approval Platform (LangGraph-Powered)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An intelligent, explainable AI platform for automated loan analysis and financial guidance**

[🚀 Quick Start](#quick-start) • [📚 Documentation](#documentation) • [🏗️ Architecture](#architecture) • [🛠️ Development](#development)

</div>

---

## 📖 Overview

FinSage is an end-to-end, explainable AI platform for automated loan application analysis, approval prediction, and personalized financial guidance. It combines a modern Streamlit frontend, **LangGraph workflow orchestration**, machine learning (LightGBM), SHAP explainability, and a conversational AI assistant (Groq API) to deliver instant, transparent, and actionable insights to users.

### ✨ Key Features

- **🔐 User Authentication & Session Management**: Secure registration, login, and session handling with bcrypt-hashed passwords
- **📊 Loan Application Analysis**: Intuitive Streamlit UI for user data entry and real-time validation
- **🤖 ML Model Prediction**: LightGBM model predicts loan approval with high accuracy
- **🔍 Explainable AI (SHAP)**: Transparent, personalized explanations for each prediction
- **💡 Personalized Insights**: Actionable feedback and improvement steps based on analysis
- **💬 Conversational AI Assistant**: Groq-powered chat assistant for contextual financial advice
- **📈 Analysis History**: Persistent storage of all analyses and chat history
- **🔄 LangGraph Workflows**: Advanced workflow orchestration for seamless loan analysis
- **🔒 Secure Data Isolation**: User data isolation using SQLAlchemy ORM and session validation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git
- 8GB+ RAM recommended

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd finsage
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy and edit environment file
cp .env.example .env
# Add your GROQ_API_KEY and other secrets
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Run the Application
```bash
# Option 1: Full app with authentication (Recommended)
streamlit run frontend/auth/simple_langgraph_homepage.py

# Option 2: Direct app (No login required)
streamlit run frontend/core/simple_langgraph_app.py
```

**🎯 The app will open at `http://localhost:8501`**

---

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Streamlit     │◄──►│  LangGraph Workflow  │◄──►│  Python Backend │
│    Frontend     │    │      Engine          │    │     Modules     │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
         │                       │                           │
         │                       │                           │
         ▼                       ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  User Interface │    │  Workflow Nodes      │    │  ML Model       │
│  (Forms, Chat)  │    │  (State Management)  │    │  (LightGBM)     │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
         │                       │                           │
         │                       │                           │
         ▼                       ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  Authentication │    │  Error Handling      │    │  SHAP Analysis  │
│  (bcrypt, JWT)  │    │  (Recovery, Logging) │    │  (Explainability)│
└─────────────────┘    └──────────────────────┘    └─────────────────┘
```

### LangGraph Workflow
```
prepare_loan_data → ml_prediction → shap_analysis → generate_insights → format_response
```

**Benefits:**
- **🔄 Better State Management**: Proper data flow between workflow nodes
- **🛡️ Improved Error Handling**: Better error management and recovery
- **🔧 Easy Extensibility**: Simple to add new workflow steps
- **📊 Better Monitoring**: Visibility into workflow execution

---

## 🛠️ Tech Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Frontend** | Streamlit | 1.28+ | Modern web interface |
| **Backend Engine** | LangGraph | 0.1+ | Workflow orchestration |
| **Database** | SQLAlchemy + SQLite | Latest | Data persistence |
| **ML Framework** | LightGBM + SHAP | Latest | Prediction & explainability |
| **AI Assistant** | Groq API | Latest | Conversational AI |
| **Authentication** | bcrypt + JWT | Latest | Security & sessions |
| **Data Processing** | Pandas + NumPy | Latest | Data manipulation |

---

## 📁 Project Structure

```
finsage/
├── 📁 frontend/                    # Streamlit frontend applications
│   ├── 🔐 auth/                    # Authentication system
│   │   └── simple_langgraph_homepage.py
│   ├── 🎯 core/                    # Main application
│   │   └── simple_langgraph_app.py
│   └── 🤖 ai/                      # AI chatbot interface
│       └── chatbot.py
├── ⚙️ backend/                     # Backend services and logic
│   ├── 🔧 core/                    # Core configuration and utilities
│   │   ├── config.py
│   │   └── langgraph_core.py
│   ├── 🗄️ database/               # Database services and models
│   │   ├── database.py
│   │   ├── database_service.py
│   │   ├── init_database.py
│   │   └── migrate_database.py
│   ├── 🤖 ml/                      # Machine learning services
│   │   ├── ai_service.py
│   │   ├── backend.py
│   │   └── llm_utils.py
│   ├── 📊 models/                  # Database models
│   │   └── models.py
│   ├── 🔄 nodes/                   # LangGraph workflow nodes
│   │   ├── conditional_insight_nodes.py
│   │   └── simple_loan_nodes.py
│   └── 🚀 workflows/               # LangGraph workflow definitions
│       ├── conversation_graph.py
│       └── simple_loan_workflow.py
├── 📚 documentation/                # Project documentation
├── 🗃️ unused_files/                # Archived/legacy code
├── 🐍 venv/                        # Python virtual environment
├── 📋 requirements.txt              # Python dependencies
├── 🚀 main.py                      # Project entry point
├── 🔧 init_db.py                   # Database initialization
├── 💥 force_init_db.py             # Force database reset
└── 📖 README.md                    # This file
```

---

## 🔧 Development Setup

### Local Development
```bash
# 1. Clone repository
git clone <repo-url>
cd finsage

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt  # if available
pip install black flake8 pytest

# 5. Set up pre-commit hooks
pre-commit install

# 6. Initialize database
python init_db.py

# 7. Run tests
pytest

# 8. Start development server
streamlit run frontend/core/simple_langgraph_app.py --server.port 8501
```

### Environment Variables
Create a `.env` file in the root directory:
```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///users.db
DATABASE_ECHO=false

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here

# LangGraph Settings
LANGGRAPH_TRACE_V2=true
LANGGRAPH_ENDPOINT=http://localhost:8123
```

---

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_ml_models.py

# Run with verbose output
pytest -v
```

### Test Structure
```
tests/
├── unit/                    # Unit tests
├── integration/             # Integration tests
├── fixtures/                # Test fixtures
└── conftest.py             # Test configuration
```

---

## 🚀 Deployment

### Production Deployment
```bash
# 1. Set production environment
export ENVIRONMENT=production
export DEBUG=false

# 2. Install production dependencies
pip install -r requirements.txt

# 3. Initialize production database
python init_db.py

# 4. Run with production settings
streamlit run frontend/core/simple_langgraph_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "frontend/core/simple_langgraph_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Solution: Reinitialize database
python force_init_db.py
```

#### 2. Import Errors
```bash
# Solution: Ensure you're in the project root
cd finsage
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

#### 3. Streamlit Port Already in Use
```bash
# Solution: Use different port
streamlit run frontend/core/simple_langgraph_app.py --server.port 8502
```

#### 4. Memory Issues
```bash
# Solution: Increase Streamlit memory limit
streamlit run frontend/core/simple_langgraph_app.py --server.maxUploadSize 200
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true
```

---

## 📚 Documentation

- **[Architecture Guide](documentation/ARCHITECTURE.md)** - Detailed system architecture
- **[LangGraph Setup](documentation/LANGGRAPH_SETUP.md)** - LangGraph configuration guide
- **[Module Documentation](documentation/MODULES.md)** - Backend module details
- **[Workflow Guide](documentation/CONDITIONAL_WORKFLOW.md)** - Workflow implementation

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints where possible
- Write comprehensive docstrings
- Include tests for new functionality
- Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **[LightGBM](https://github.com/microsoft/LightGBM)** - Gradient boosting framework
- **[SHAP](https://github.com/slundberg/shap)** - Model explainability
- **[Streamlit](https://streamlit.io/)** - Web application framework
- **[Groq API](https://groq.com/)** - High-performance LLM inference
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Database toolkit
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Workflow orchestration
- **[bcrypt](https://pypi.org/project/bcrypt/)** - Password hashing

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/finsage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/finsage/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/finsage/wiki)

---

<div align="center">

**Made with ❤️ by the FinSage Team**

[⬆️ Back to Top](#finsage--explainable-ai-loan-approval-platform-langgraph-powered)

</div> 