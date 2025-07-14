import bcrypt
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.models import User, Session as UserSession, ChatHistory, LoanAnalysis, get_db, generate_session_token
from backend.config import SESSION_EXPIRY_HOURS

class DatabaseService:
    """Database service for PostgreSQL operations"""
    
    def __init__(self):
        self.db = next(get_db())
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verify provided password against stored hash"""
        try:
            return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception:
            return False
    
    def register_user(self, username: str, email: str, password: str) -> dict:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return {"success": False, "message": "Username or email already exists"}
            
            # Create new user
            hashed_password = self.hash_password(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            return {"success": True, "message": "User registered successfully", "user_id": new_user.id}
            
        except IntegrityError:
            self.db.rollback()
            return {"success": False, "message": "Username or email already exists"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Registration failed: {str(e)}"}
    
    def login_user(self, username: str, password: str) -> dict:
        """Authenticate user and create session"""
        try:
            # Find user by username or email
            user = self.db.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                return {"success": False, "message": "Invalid credentials"}
            
            if not user.is_active:
                return {"success": False, "message": "Account is deactivated"}
            
            # Verify password
            if not self.verify_password(user.password_hash, password):
                return {"success": False, "message": "Invalid credentials"}
            
            # Create session
            session_token = generate_session_token()
            expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
            
            new_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at
            )
            
            self.db.add(new_session)
            self.db.commit()
            
            return {
                "success": True,
                "message": "Login successful",
                "session_token": session_token,
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Login failed: {str(e)}"}
    
    def validate_session(self, session_token: str) -> dict:
        """Validate session token and return user info"""
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if not session:
                return {"success": False, "message": "Invalid session"}
            
            if session.expires_at < datetime.utcnow():
                # Delete expired session
                self.db.delete(session)
                self.db.commit()
                return {"success": False, "message": "Session expired"}
            
            user = self.db.query(User).filter(User.id == session.user_id).first()
            if not user or not user.is_active:
                return {"success": False, "message": "User not found or inactive"}
            
            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
            
        except Exception as e:
            return {"success": False, "message": f"Session validation failed: {str(e)}"}
    
    def logout_user(self, session_token: str) -> dict:
        """Logout user by deleting session"""
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                self.db.delete(session)
                self.db.commit()
                return {"success": True, "message": "Logged out successfully"}
            
            return {"success": False, "message": "Session not found"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Logout failed: {str(e)}"}
    
    def save_chat_message(self, user_id: int, session_id: int, role: str, content: str) -> dict:
        """Save a chat message to the database"""
        try:
            chat_message = ChatHistory(
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=content
            )
            
            self.db.add(chat_message)
            self.db.commit()
            self.db.refresh(chat_message)
            
            return {"success": True, "message_id": chat_message.id}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Failed to save chat message: {str(e)}"}
    
    def get_chat_history(self, user_id: int, session_id: int = None, limit: int = 50) -> dict:
        """Get chat history for a user or session"""
        try:
            query = self.db.query(ChatHistory).filter(ChatHistory.user_id == user_id)
            
            if session_id:
                query = query.filter(ChatHistory.session_id == session_id)
            
            chat_history = query.order_by(ChatHistory.timestamp.desc()).limit(limit).all()
            
            return {
                "success": True,
                "chat_history": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in chat_history
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get chat history: {str(e)}"}
    
    def save_loan_analysis(self, user_id: int, analysis_data: dict, prediction: int, 
                          feature_importance: dict = None, insights: str = None) -> dict:
        """Save loan analysis results"""
        try:
            # Convert numpy types to native Python types
            import numpy as np
            
            def convert_numpy_types(obj):
                """Recursively convert numpy types to native Python types"""
                if isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
            
            # Convert the data
            converted_analysis_data = convert_numpy_types(analysis_data)
            converted_feature_importance = convert_numpy_types(feature_importance) if feature_importance else None
            converted_prediction = convert_numpy_types(prediction)
            
            loan_analysis = LoanAnalysis(
                user_id=user_id,
                analysis_data=converted_analysis_data,
                prediction=converted_prediction,
                feature_importance=converted_feature_importance,
                insights=insights
            )
            
            self.db.add(loan_analysis)
            self.db.commit()
            self.db.refresh(loan_analysis)
            
            return {"success": True, "analysis_id": loan_analysis.id}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Failed to save loan analysis: {str(e)}"}
    
    def get_loan_analyses(self, user_id: int, limit: int = 10) -> dict:
        """Get loan analysis history for a user"""
        try:
            analyses = self.db.query(LoanAnalysis).filter(
                LoanAnalysis.user_id == user_id
            ).order_by(LoanAnalysis.created_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "analyses": [
                    {
                        "id": analysis.id,
                        "prediction": analysis.prediction,
                        "analysis_data": analysis.analysis_data,
                        "feature_importance": analysis.feature_importance,
                        "insights": analysis.insights,
                        "created_at": analysis.created_at.isoformat()
                    }
                    for analysis in analyses
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get loan analyses: {str(e)}"}
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        user = self.db.query(User).filter(User.username == username).first()
        return user is not None
    
    def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        user = self.db.query(User).filter(User.email == email).first()
        return user is not None 