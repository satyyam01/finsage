"""
Main entry point for FinSage - LangGraph-Powered Loan Analysis Platform
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """Main entry point for the application"""
    print("🚀 FinSage - LangGraph-Powered Loan Analysis Platform")
    print("=" * 60)
    print()
    print("📁 Project Structure:")
    print("├── frontend/")
    print("│   ├── auth/          # Authentication (login/signup)")
    print("│   ├── core/          # Main application")
    print("│   └── ai/            # AI chatbot")
    print("├── backend/")
    print("│   ├── core/          # Core backend (LangGraph, config)")
    print("│   ├── ml/            # Machine learning models")
    print("│   ├── database/      # Database services")
    print("│   ├── models/        # Database models")
    print("│   ├── workflows/     # LangGraph workflows")
    print("│   └── nodes/         # Workflow execution nodes")
    print()
    print("🚀 To run the application:")
    print()
    print("Option 1: Full app with login (Recommended)")
    print("  streamlit run frontend/auth/simple_langgraph_homepage.py")
    print()
    print("Option 2: Direct app (No login)")
    print("  streamlit run frontend/core/simple_langgraph_app.py")
    print()
    print("📚 For detailed documentation, see the 'documentation/' folder")
    print("📁 For archived code, see the 'old_flow/' folder")

if __name__ == "__main__":
    main() 