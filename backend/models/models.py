from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import uuid
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import database configuration from core module
from backend.core.config import DATABASE_URL

Base = declarative_base()

class User(Base):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    loan_analyses = relationship("LoanAnalysis", back_populates="user", cascade="all, delete-orphan")
    workflow_states = relationship("WorkflowState", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    """Session model for user session management"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class ChatHistory(Base):
    """Chat history model for storing conversation messages"""
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(255), nullable=True)  # Changed to String to handle UUIDs
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_histories")

class LoanAnalysis(Base):
    """Loan analysis model for storing analysis results"""
    __tablename__ = 'loan_analyses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    analysis_data = Column(JSON, nullable=False)  # Store user input data
    prediction = Column(Integer, nullable=False)  # 0 for approved, 1 for rejected
    feature_importance = Column(JSON, nullable=True)  # Store SHAP feature importance
    insights = Column(Text, nullable=True)  # Store AI-generated insights
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="loan_analyses")

class WorkflowState(Base):
    """Workflow state model for LangGraph workflow management"""
    __tablename__ = 'workflow_states'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(255), nullable=False)
    workflow_type = Column(String(100), nullable=False)
    state_data = Column(JSON, nullable=False)
    workflow_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="workflow_states")

class WorkflowExecution(Base):
    """Workflow execution model for audit trail"""
    __tablename__ = 'workflow_executions'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(255), nullable=False)
    step_name = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

# Database engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def generate_session_token():
    """Generate a unique session token"""
    return str(uuid.uuid4())

def is_session_expired(expires_at):
    """Check if session is expired"""
    return datetime.utcnow() > expires_at 