import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class RationaleManager:
    """
    Minimal RationaleManager for tracking AI agent decision-making process.
    Only implements essential methods needed by the system.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.rationale_file = self._get_rationale_file_path()
        self._ensure_rationale_file_exists()
    
    def _get_rationale_file_path(self) -> Path:
        """Get the path to the rationale file for this session."""
        # Use the same directory structure as the existing system
        rationale_dir = Path("temp_ui_files") / self.session_id
        rationale_dir.mkdir(parents=True, exist_ok=True)
        return rationale_dir / "rationale.json"
    
    def _ensure_rationale_file_exists(self):
        """Create rationale file with default structure if it doesn't exist."""
        if not self.rationale_file.exists():
            default_rationale = {
                "session_id": self.session_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "requirements_analysis": [],
                "template_selection": {
                    "recommendations": [],
                    "final_selection": None,
                    "selection_reasoning": ""
                },
                "question_generation": [],
                "ui_editing": {
                    "planning_rationale": [],
                    "execution_summary": []
                },
                "overall_workflow": {
                    "phase_decisions": [],
                    "agent_coordination": []
                }
            }
            self._save_rationale(default_rationale)
    
    def _load_rationale(self) -> Dict[str, Any]:
        """Load rationale data from file."""
        try:
            if self.rationale_file.exists():
                with open(self.rationale_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Warning: Failed to load rationale: {e}")
            return {}
    
    def _save_rationale(self, rationale_data: Dict[str, Any]):
        """Save rationale data to file."""
        try:
            rationale_data["last_updated"] = datetime.now().isoformat()
            with open(self.rationale_file, 'w', encoding='utf-8') as f:
                json.dump(rationale_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save rationale: {e}")
    
    def add_template_recommendation_rationale(self, recommendations: List[Dict[str, Any]], selected_template: Optional[Dict[str, Any]] = None):
        """
        Store template recommendation rationale.
        
        Args:
            recommendations: List of template recommendations
            selected_template: The selected template (optional)
        """
        try:
            rationale_data = self._load_rationale()
            
            # Update recommendations
            rationale_data["template_selection"]["recommendations"] = recommendations
            
            # Update final selection if provided
            if selected_template:
                rationale_data["template_selection"]["final_selection"] = selected_template
                rationale_data["template_selection"]["selection_reasoning"] = f"Template selected at {datetime.now().isoformat()}"
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add template recommendation rationale: {e}")
    
    def add_ui_editing_planning_rationale(self, plan: Dict[str, Any], user_feedback: str):
        """
        Store UI editing planning rationale.
        
        Args:
            plan: The modification plan
            user_feedback: User's original request
        """
        try:
            rationale_data = self._load_rationale()
            
            planning_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_request": user_feedback,
                "plan": plan
            }
            
            rationale_data["ui_editing"]["planning_rationale"].append(planning_entry)
            
            # Keep only last 10 planning entries to prevent file bloat
            if len(rationale_data["ui_editing"]["planning_rationale"]) > 10:
                rationale_data["ui_editing"]["planning_rationale"] = rationale_data["ui_editing"]["planning_rationale"][-10:]
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add UI editing planning rationale: {e}")
    
    def add_ui_editing_execution_summary(self, result: Dict[str, Any], user_request: str):
        """
        Store UI editing execution summary.
        
        Args:
            result: The execution result
            user_request: User's original request
        """
        try:
            rationale_data = self._load_rationale()
            
            execution_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_request": user_request,
                "result": result
            }
            
            rationale_data["ui_editing"]["execution_summary"].append(execution_entry)
            
            # Keep only last 10 execution entries to prevent file bloat
            if len(rationale_data["ui_editing"]["execution_summary"]) > 10:
                rationale_data["ui_editing"]["execution_summary"] = rationale_data["ui_editing"]["execution_summary"][-10:]
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add UI editing execution summary: {e}")
    
    def add_requirements_rationale(self, requirements: Dict[str, Any], analysis_summary: str):
        """
        Store requirements analysis rationale.
        
        Args:
            requirements: The requirements data
            analysis_summary: Summary of the analysis
        """
        try:
            rationale_data = self._load_rationale()
            
            requirements_entry = {
                "timestamp": datetime.now().isoformat(),
                "requirements": requirements,
                "analysis_summary": analysis_summary
            }
            
            if "requirements_analysis" not in rationale_data:
                rationale_data["requirements_analysis"] = []
            
            rationale_data["requirements_analysis"].append(requirements_entry)
            
            # Keep only last 5 entries
            if len(rationale_data["requirements_analysis"]) > 5:
                rationale_data["requirements_analysis"] = rationale_data["requirements_analysis"][-5:]
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add requirements rationale: {e}")
    
    def add_workflow_decision(self, phase: str, decision: str, reasoning: str, context: Dict[str, Any] = None):
        """
        Store workflow decision rationale.
        
        Args:
            phase: The workflow phase
            decision: The decision made
            reasoning: Reasoning behind the decision
            context: Additional context
        """
        try:
            rationale_data = self._load_rationale()
            
            decision_entry = {
                "timestamp": datetime.now().isoformat(),
                "phase": phase,
                "decision": decision,
                "reasoning": reasoning,
                "context": context or {}
            }
            
            rationale_data["overall_workflow"]["phase_decisions"].append(decision_entry)
            
            # Keep only last 10 decisions
            if len(rationale_data["overall_workflow"]["phase_decisions"]) > 10:
                rationale_data["overall_workflow"]["phase_decisions"] = rationale_data["overall_workflow"]["phase_decisions"][-10:]
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add workflow decision: {e}")
    
    def add_agent_coordination(self, from_agent: str, to_agent: str, action: str, reasoning: str, data: Dict[str, Any] = None):
        """
        Store agent coordination rationale.
        
        Args:
            from_agent: Source agent
            to_agent: Target agent
            action: Action taken
            reasoning: Reasoning for the action
            data: Data passed between agents
        """
        try:
            rationale_data = self._load_rationale()
            
            coordination_entry = {
                "timestamp": datetime.now().isoformat(),
                "from_agent": from_agent,
                "to_agent": to_agent,
                "action": action,
                "reasoning": reasoning,
                "data": data or {}
            }
            
            rationale_data["overall_workflow"]["agent_coordination"].append(coordination_entry)
            
            # Keep only last 10 coordination entries
            if len(rationale_data["overall_workflow"]["agent_coordination"]) > 10:
                rationale_data["overall_workflow"]["agent_coordination"] = rationale_data["overall_workflow"]["agent_coordination"][-10:]
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add agent coordination: {e}")
    
    def add_question_generation_rationale(self, questions: List[Dict[str, Any]], reasoning: str):
        """
        Store question generation rationale.
        
        Args:
            questions: Generated questions
            reasoning: Reasoning for question generation
        """
        try:
            rationale_data = self._load_rationale()
            
            question_entry = {
                "timestamp": datetime.now().isoformat(),
                "questions": questions,
                "reasoning": reasoning
            }
            
            if "question_generation" not in rationale_data:
                rationale_data["question_generation"] = []
            
            rationale_data["question_generation"].append(question_entry)
            
            # Keep only last 5 entries
            if len(rationale_data["question_generation"]) > 5:
                rationale_data["question_generation"] = rationale_data["question_generation"][-5:]
            
            self._save_rationale(rationale_data)
            
        except Exception as e:
            print(f"Warning: Failed to add question generation rationale: {e}")
    
    def load_rationale(self) -> Dict[str, Any]:
        """
        Load all rationale data for the session.
        
        Returns:
            Dict containing all rationale data
        """
        try:
            return self._load_rationale()
        except Exception as e:
            print(f"Warning: Failed to load rationale: {e}")
            return {}
