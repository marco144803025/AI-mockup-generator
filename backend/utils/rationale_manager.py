#!/usr/bin/env python3
"""
Rationale Manager - Handles storage and retrieval of agent decision rationale
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class RationaleManager:
    """Manages storage and retrieval of agent decision rationale"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.rationale_dir = "temp_ui_files"
        self.rationale_file = os.path.join(self.rationale_dir, session_id, "rationale.json")
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.rationale_file), exist_ok=True)
        
        # Initialize rationale file if it doesn't exist
        if not os.path.exists(self.rationale_file):
            self._initialize_rationale_file()
    
    def _initialize_rationale_file(self):
        """Initialize the rationale.json file with default structure"""
        initial_rationale = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "template_selection": {
                "recommendations": [],
                "final_selection": None,
                "selection_reasoning": ""
            },
            "ui_editing": {
                "planning_rationale": [],
                "execution_summary": []
            },
            "overall_workflow": {
                "phase_decisions": [],
                "agent_coordination": []
            }
        }
        
        try:
            with open(self.rationale_file, 'w') as f:
                json.dump(initial_rationale, f, indent=2)
            self.logger.info(f"Initialized rationale file: {self.rationale_file}")
        except Exception as e:
            self.logger.error(f"Failed to initialize rationale file: {e}")
    
    def load_rationale(self) -> Dict[str, Any]:
        """Load existing rationale data"""
        try:
            if os.path.exists(self.rationale_file):
                with open(self.rationale_file, 'r') as f:
                    return json.load(f)
            else:
                self._initialize_rationale_file()
                return self.load_rationale()
        except Exception as e:
            self.logger.error(f"Failed to load rationale: {e}")
            return {}
    
    def save_rationale(self, rationale_data: Dict[str, Any]):
        """Save rationale data to file"""
        try:
            rationale_data["last_updated"] = datetime.now().isoformat()
            with open(self.rationale_file, 'w') as f:
                json.dump(rationale_data, f, indent=2)
            self.logger.info(f"Saved rationale data to: {self.rationale_file}")
        except Exception as e:
            self.logger.error(f"Failed to save rationale: {e}")
    
    def add_template_recommendation_rationale(self, recommendations: List[Dict[str, Any]], final_selection: Optional[Dict[str, Any]] = None):
        """Store template recommendation rationale"""
        try:
            rationale = self.load_rationale()
            
            # Store detailed recommendations with reasoning
            template_rationale = []
            for rec in recommendations:
                template_rationale.append({
                    "template_id": rec.get("template_id", "unknown"),
                    "template_name": rec.get("template_name", "unknown"),
                    "overall_score": rec.get("overall_score", 0.0),
                    "detailed_reasoning": rec.get("detailed_reasoning", ""),
                    "strengths": rec.get("strengths", []),
                    "considerations": rec.get("considerations", []),
                    "suitability_level": rec.get("suitability_level", "unknown"),
                    "timestamp": datetime.now().isoformat()
                })
            
            rationale["template_selection"]["recommendations"] = template_rationale
            
            if final_selection:
                rationale["template_selection"]["final_selection"] = {
                    "template_id": final_selection.get("template_id", "unknown"),
                    "template_name": final_selection.get("template_name", "unknown"),
                    "selection_reasoning": final_selection.get("selection_reasoning", "User selected this template"),
                    "timestamp": datetime.now().isoformat()
                }
            
            self.save_rationale(rationale)
            self.logger.info(f"Added template recommendation rationale for {len(template_rationale)} templates")
            
        except Exception as e:
            self.logger.error(f"Failed to add template recommendation rationale: {e}")
    
    def add_ui_editing_planning_rationale(self, planning_data: Dict[str, Any], user_request: str):
        """Store UI editing planning rationale"""
        try:
            rationale = self.load_rationale()
            
            planning_entry = {
                "user_request": user_request,
                "timestamp": datetime.now().isoformat(),
                "intent_analysis": planning_data.get("intent_analysis", {}),
                "target_identification": planning_data.get("target_identification", {}),
                "modification_steps": planning_data.get("steps", []),
                "expected_outcome": planning_data.get("expected_outcome", ""),
                "requires_clarification": planning_data.get("requires_clarification", False),
                "clarification_options": planning_data.get("clarification_options", [])
            }
            
            rationale["ui_editing"]["planning_rationale"].append(planning_entry)
            self.save_rationale(rationale)
            
            self.logger.info(f"Added UI editing planning rationale for request: {user_request[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to add UI editing planning rationale: {e}")
    
    def add_ui_editing_execution_summary(self, execution_result: Dict[str, Any], user_request: str):
        """Store UI editing execution summary"""
        try:
            rationale = self.load_rationale()
            
            execution_entry = {
                "user_request": user_request,
                "timestamp": datetime.now().isoformat(),
                "success": execution_result.get("success", False),
                "changes_summary": execution_result.get("changes_summary", []),
                "error": execution_result.get("error", None)
            }
            
            rationale["ui_editing"]["execution_summary"].append(execution_entry)
            self.save_rationale(rationale)
            
            self.logger.info(f"Added UI editing execution summary for request: {user_request[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to add UI editing execution summary: {e}")
    
    def add_workflow_decision_rationale(self, phase: str, decision_data: Dict[str, Any]):
        """Store workflow decision rationale"""
        try:
            rationale = self.load_rationale()
            
            decision_entry = {
                "phase": phase,
                "timestamp": datetime.now().isoformat(),
                "decision": decision_data.get("decision", ""),
                "reasoning": decision_data.get("reasoning", ""),
                "required_agents": decision_data.get("required_agents", []),
                "skip_agents": decision_data.get("skip_agents", []),
                "context_updates": decision_data.get("context_updates", {})
            }
            
            rationale["overall_workflow"]["phase_decisions"].append(decision_entry)
            self.save_rationale(rationale)
            
            self.logger.info(f"Added workflow decision rationale for phase: {phase}")
            
        except Exception as e:
            self.logger.error(f"Failed to add workflow decision rationale: {e}")
    
    def get_rationale_summary(self) -> Dict[str, Any]:
        """Get a summary of all rationale data for reporting"""
        try:
            rationale = self.load_rationale()
            
            return {
                "session_id": rationale.get("session_id", self.session_id),
                "created_at": rationale.get("created_at", ""),
                "last_updated": rationale.get("last_updated", ""),
                "template_selection_count": len(rationale.get("template_selection", {}).get("recommendations", [])),
                "ui_editing_requests": len(rationale.get("ui_editing", {}).get("planning_rationale", [])),
                "workflow_decisions": len(rationale.get("overall_workflow", {}).get("phase_decisions", [])),
                "has_final_template": rationale.get("template_selection", {}).get("final_selection") is not None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get rationale summary: {e}")
            return {}

