"""
Simple Session Manager for storing session state globally
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

class SessionManager:
    """Simple in-memory session manager"""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "current_phase": "initial",
            "conversation_history": [],
            "requirements": {},
            "recommendations": [],
            "questions": {},
            "selected_template": None,
            "modifications": [],
            "report": None,
            "created_at": datetime.now().isoformat()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session with new data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            return True
        return False
    
    def set_selected_template(self, session_id: str, template: Dict[str, Any]) -> bool:
        """Set selected template for a session"""
        if session_id in self.sessions:
            self.sessions[session_id]["selected_template"] = template
            self.sessions[session_id]["current_phase"] = "template_selection"
            return True
        return False
    
    def get_selected_template(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get selected template for a session"""
        session = self.get_session(session_id)
        return session.get("selected_template") if session else None
    
    def get_phase_status(self, session_id: str) -> Dict[str, Any]:
        """Get current phase status for frontend awareness"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "current_phase": session.get("current_phase"),
            "phase_transition_completed": session.get("phase_transition_completed", False),
            "can_edit": session.get("current_phase") == "editing" and 
                       session.get("phase_transition_completed", False)
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

# Global session manager instance
session_manager = SessionManager() 