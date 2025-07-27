import autogen
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import os

from .user_proxy_agent import UserProxyAgent
from .requirement_understanding_agent import RequirementUnderstandingAgent
from .ui_recommender_agent import UIRecommenderAgent
from .ui_modification_agent import UIModificationAgent
from .ui_editing_agent import UIEditingAgent
from .report_generation_agent import ReportGenerationAgent

class AutoGenOrchestrator:
    """Main orchestrator that coordinates all agents for UI mockup generation"""
    
    def __init__(self):
        # Initialize all agents
        self.user_proxy = UserProxyAgent()
        self.requirement_understanding = RequirementUnderstandingAgent()
        self.ui_recommender = UIRecommenderAgent()
        self.ui_modification = UIModificationAgent()
        self.ui_editing = UIEditingAgent()
        self.report_generation = ReportGenerationAgent()
        
        # Create AutoGen group chat
        self.groupchat = autogen.GroupChat(
            agents=[
                self.user_proxy.agent,
                self.requirement_understanding.agent,
                self.ui_recommender.agent,
                self.ui_modification.agent,
                self.ui_editing.agent,
                self.report_generation.agent
            ],
            messages=[],
            max_round=50
        )
        
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config={
                "config_list": [{"model": "claude-3-5-sonnet-20241022", "api_key": os.getenv("CLAUDE_API_KEY")}],
                "temperature": 0.7
            }
        )
        
        # Project state
        self.project_state = {
            "project_name": "",
            "user_requirements": {},
            "ui_specifications": {},
            "selected_template": {},
            "template_selection_reasoning": "",
            "alternative_templates": [],
            "modifications": [],
            "final_template": {},
            "validation_results": {},
            "phase": "initial",
            "conversation_history": []
        }
    
    def start_project(self, project_name: str, user_prompt: str, logo_image: Optional[str] = None) -> Dict[str, Any]:
        """Start a new UI mockup generation project"""
        
        self.project_state["project_name"] = project_name
        self.project_state["phase"] = "phase_1"
        
        # Phase 1: Requirements Analysis and Template Selection
        phase_1_result = self._execute_phase_1(user_prompt, logo_image)
        
        return {
            "status": "phase_1_complete",
            "project_state": self.project_state,
            "next_action": "template_confirmation",
            "message": phase_1_result["message"]
        }
    
    def _execute_phase_1(self, user_prompt: str, logo_image: Optional[str] = None) -> Dict[str, Any]:
        """Execute Phase 1: Requirements Analysis and Template Selection"""
        
        # Step 1: Understand user requirements
        user_requirements = self.user_proxy.understand_requirements(user_prompt, logo_image)
        self.project_state["user_requirements"] = user_requirements
        
        # Step 2: Analyze requirements for UI specifications
        ui_specifications = self.requirement_understanding.analyze_requirements(user_prompt, logo_image)
        self.project_state["ui_specifications"] = ui_specifications
        
        # Step 3: Generate search criteria
        search_criteria = self.requirement_understanding.generate_template_search_criteria(ui_specifications)
        search_criteria["category"] = user_requirements.get("page_type", "landing")
        
        # Step 4: Find suitable templates
        recommendations = self.ui_recommender.find_suitable_templates(search_criteria, search_criteria["category"])
        
        if not recommendations:
            return {
                "status": "error",
                "message": "No suitable templates found for your requirements."
            }
        
        # Step 5: Select best template
        best_recommendation = recommendations[0]
        selected_template = best_recommendation["template"]
        self.project_state["selected_template"] = selected_template
        self.project_state["template_selection_reasoning"] = best_recommendation["reasoning"]
        self.project_state["alternative_templates"] = recommendations[1:4]  # Top 3 alternatives
        
        # Step 6: Generate confirmation message
        confirmation_message = self.user_proxy.confirm_template_selection(
            selected_template, 
            best_recommendation["reasoning"]
        )
        
        return {
            "status": "success",
            "message": confirmation_message,
            "selected_template": selected_template,
            "alternatives": self.project_state["alternative_templates"]
        }
    
    def confirm_template_selection(self, template_id: Optional[str] = None) -> Dict[str, Any]:
        """Confirm template selection and proceed to Phase 2"""
        
        if template_id:
            # User selected a different template
            template_details = self.ui_recommender.get_template_details(template_id)
            if template_details:
                self.project_state["selected_template"] = template_details
        
        self.project_state["phase"] = "phase_2"
        
        # Generate master style confirmation
        master_style_message = self.user_proxy.confirm_master_style(self.project_state["selected_template"])
        
        return {
            "status": "phase_2_ready",
            "project_state": self.project_state,
            "next_action": "additional_pages",
            "message": master_style_message
        }
    
    def get_additional_pages_suggestions(self) -> Dict[str, Any]:
        """Get suggestions for additional pages based on the selected template"""
        
        page_type = self.project_state["user_requirements"].get("page_type", "landing")
        suggestions = self.user_proxy.get_additional_pages_suggestions(page_type)
        
        return {
            "status": "suggestions_ready",
            "suggestions": suggestions,
            "message": f"Based on your {page_type} page, I suggest these additional pages: {', '.join(suggestions)}"
        }
    
    def process_modification_request(self, user_feedback: str) -> Dict[str, Any]:
        """Process user modification request in Phase 2"""
        
        current_template = self.project_state["selected_template"]
        
        # Step 1: Analyze modification request
        modification_request = self.ui_modification.analyze_modification_request(user_feedback, current_template)
        
        # Step 2: Generate modification plan
        modification_plan = self.ui_modification.generate_modification_plan(modification_request, current_template)
        
        # Step 3: Apply modifications
        modified_template = self.ui_editing.apply_modifications(current_template, modification_plan)
        
        # Step 4: Validate modifications
        validation_results = self.ui_editing.validate_modifications(current_template, modified_template)
        
        # Step 5: Update project state
        self.project_state["modifications"].append(modification_request)
        self.project_state["selected_template"] = modified_template
        self.project_state["validation_results"] = validation_results
        
        # Step 6: Generate preview
        preview_html = self.ui_editing.generate_preview(modified_template)
        
        return {
            "status": "modification_applied",
            "project_state": self.project_state,
            "modification_request": modification_request,
            "validation_results": validation_results,
            "preview_html": preview_html,
            "message": f"Modification applied successfully. {len(validation_results.get('errors', []))} errors, {len(validation_results.get('warnings', []))} warnings."
        }
    
    def finalize_project(self) -> Dict[str, Any]:
        """Finalize the project and generate report (Phase 3)"""
        
        self.project_state["phase"] = "phase_3"
        self.project_state["final_template"] = self.project_state["selected_template"]
        
        # Generate comprehensive report
        report_filepath = self.report_generation.generate_project_report(self.project_state)
        
        # Generate summary
        summary = self.report_generation.generate_summary_report(self.project_state)
        
        return {
            "status": "project_complete",
            "project_state": self.project_state,
            "report_filepath": report_filepath,
            "summary": summary,
            "message": "Project completed successfully! Report generated and ready for download."
        }
    
    def get_project_status(self) -> Dict[str, Any]:
        """Get current project status"""
        
        return {
            "project_name": self.project_state["project_name"],
            "phase": self.project_state["phase"],
            "selected_template": self.project_state["selected_template"].get("title", "None"),
            "total_modifications": len(self.project_state["modifications"]),
            "validation_status": "Valid" if self.project_state.get("validation_results", {}).get("is_valid", True) else "Invalid"
        }
    
    def reset_project(self) -> Dict[str, Any]:
        """Reset the project to initial state"""
        
        self.project_state = {
            "project_name": "",
            "user_requirements": {},
            "ui_specifications": {},
            "selected_template": {},
            "template_selection_reasoning": "",
            "alternative_templates": [],
            "modifications": [],
            "final_template": {},
            "validation_results": {},
            "phase": "initial",
            "conversation_history": []
        }
        
        return {
            "status": "reset",
            "message": "Project reset successfully."
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        
        return self.project_state["conversation_history"]
    
    def add_conversation_entry(self, role: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Add entry to conversation history"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message,
            "data": data or {}
        }
        
        self.project_state["conversation_history"].append(entry)
    
    def export_project_data(self) -> Dict[str, Any]:
        """Export complete project data"""
        
        return {
            "project_state": self.project_state,
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0"
        } 