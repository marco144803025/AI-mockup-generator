"""
Lean Flow Orchestrator - Coordinates workflow between focused agents
Follows single responsibility principle: Only handles coordination
"""

import logging
import uuid
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import asyncio

from .requirements_analysis_agent import RequirementsAnalysisAgent
from .template_recommendation_agent import TemplateRecommendationAgent
from .question_generation_agent import QuestionGenerationAgent
from .user_proxy_agent import UserProxyAgent
from .ui_editing_agent import UIEditingAgent
from .report_generation_agent import ReportGenerationAgent
from config.keyword_config import KeywordManager
from session_manager import session_manager

class LeanFlowOrchestrator:
    """Intelligent orchestrator for the lean UI mockup generation workflow"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.requirements_agent = RequirementsAnalysisAgent()
        self.recommendation_agent = TemplateRecommendationAgent()
        self.question_agent = QuestionGenerationAgent()
        self.user_proxy_agent = UserProxyAgent()
        self.editing_agent = UIEditingAgent()
        self.report_agent = ReportGenerationAgent()
        
        # Initialize keyword manager
        self.keyword_manager = KeywordManager()
        
        # Session management
        if session_id:
            self.session_id = session_id
            # Load existing session
            session_data = session_manager.get_session(session_id)
            if session_data:
                self.session_state = session_data
            else:
                # Create new session if not found
                self.session_id = session_manager.create_session()
                self.session_state = session_manager.get_session(self.session_id)
        else:
            # Create new session
            self.session_id = session_manager.create_session()
            self.session_state = session_manager.get_session(self.session_id)
        
        # Phase definitions
        self.phases = ["initial", "requirements", "template_recommendation", "template_selection", "editing", "report_generation"]
    
    def _add_to_conversation_history(self, message: str, role: str):
        """Add message to conversation history"""
        self.session_state["conversation_history"].append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        # Update session in global manager
        session_manager.update_session(self.session_id, self.session_state)
    
    async def process_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main entry point: Coordinate workflow between focused agents"""
        
        try:
            # Add user message to history
            self._add_to_conversation_history(message, "user")
            
            # Step 1: Detect initial intent (new phase)
            initial_intent = await self._detect_initial_intent(message, context)
            
            # Step 2: Determine current phase and execute appropriate workflow
            current_phase = self.session_state["current_phase"]
            
            if current_phase == "initial":
                return await self._handle_initial_intent_phase(message, initial_intent, context)
            elif current_phase == "requirements":
                return await self._handle_requirements_phase(message, context)
            elif current_phase == "template_recommendation":
                return await self._handle_recommendation_phase(message, context)
            elif current_phase == "template_selection":
                return await self._handle_selection_phase(message, context)
            elif current_phase == "editing":
                return await self._handle_editing_phase(message, context)
            elif current_phase == "report_generation":
                return await self._handle_report_generation(message, context)
            else:
                # Default to initial intent detection
                return await self._handle_initial_intent_phase(message, initial_intent, context)
                
        except Exception as e:
            self.logger.error(f"Error in process_user_message: {e}")
            return {
                "success": False,
                "response": f"I encountered an error: {str(e)}",
                "session_id": self.session_id,
                "error": str(e)
            }
    
    async def _handle_initial_intent_phase(self, message: str, initial_intent: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the initial intent detection phase"""
        
        # Update session state with detected intent
        self.session_state["initial_intent"] = initial_intent
        
        if initial_intent == "create_ui_mockup":
            # User wants to create a UI mockup - automatically transition to requirements analysis
            detected_page_type = self.session_state.get("detected_page_type")
            
            # Build context with detected page type
            enhanced_context = context or {}
            if detected_page_type:
                enhanced_context["page_type"] = detected_page_type
                enhanced_context["selected_category"] = detected_page_type
            
            # Transition to requirements analysis phase
            self.session_state["current_phase"] = "requirements"
            
            # Call requirements analysis directly
            return await self._handle_requirements_phase(message, enhanced_context)
            
        elif initial_intent == "requirements_analysis":
            # User explicitly wants requirements analysis
            self.session_state["current_phase"] = "requirements"
            response = "Great! Let's start with requirements analysis. Please tell me what kind of UI mockup you want to create and any specific requirements you have."
            
        elif initial_intent == "template_recommendation":
            # User wants template recommendations
            self.session_state["current_phase"] = "template_recommendation"
            response = "I'll help you with template recommendations. First, let me understand your requirements to suggest the best templates."
            
        elif initial_intent == "template_selection":
            # User wants to select templates
            self.session_state["current_phase"] = "template_selection"
            response = "I'll help you select a template. Let me first understand your requirements to show you the most suitable options."
            
        elif initial_intent == "editing":
            # User wants to edit templates
            self.session_state["current_phase"] = "editing"
            response = "I'll help you edit a template. Please tell me which template you want to edit and what changes you'd like to make."
            
        elif initial_intent == "report":
            # User wants to generate a report
            self.session_state["current_phase"] = "report_generation"
            response = "I'll help you generate a report. Let me gather the project information and create a comprehensive report for you."
            
        else:
            # General conversation or unclear intent
            response = "Hello! I'm here to help you create UI mockups. You can:\n" \
                      "- Say 'I want to build a [page type] UI mockup' to get started\n" \
                      "- Ask for template recommendations\n" \
                      "- Request help with editing existing templates\n" \
                      "- Generate project reports\n" \
                      "What would you like to do?"
        
        self._add_to_conversation_history(response, "assistant")
        
        return {
            "success": True,
            "response": response,
            "session_id": self.session_id,
            "phase": self.session_state["current_phase"],
            "initial_intent": initial_intent
        }
    
    async def _handle_requirements_phase(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle requirements analysis phase using intelligent orchestration"""
        
        # Step 1: Analyze what agents are needed
        phase_decision = await self._analyze_phase_requirements(message, context)
        
        # Step 2: Update session state with context updates
        if phase_decision.get("context_updates"):
            self.session_state.update(phase_decision["context_updates"])
        
        # Step 3: Execute required agents in order
        pipeline_result = self._execute_agent_pipeline(
            phase_decision["required_agents"], 
            message, 
            context or {}
        )
        
        if not pipeline_result["success"]:
            # Handle error - ask for clarification
            response = self.user_proxy_agent.create_response_from_instructions(
                "clarification_needed",
                {
                    "error_type": "agent_execution_failed",
                    "error_message": pipeline_result["error"],
                    "clarification_questions": pipeline_result["clarification_questions"],
                    "session_state": self.session_state
                }
            )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": False,
                "response": response,
                "session_id": self.session_id,
                "phase": "requirements",
                "error": pipeline_result["error"],
                "requires_clarification": True
            }
        
        # Step 4: Update session state with agent results
        agent_results = pipeline_result["agent_results"]
        
        if "requirements_analysis" in agent_results:
            # Extract primary_result from standardized response
            requirements_result = agent_results["requirements_analysis"]
            if isinstance(requirements_result, dict) and "data" in requirements_result:
                self.session_state["requirements"] = requirements_result["data"]["primary_result"]
            else:
                self.session_state["requirements"] = requirements_result
        
        if "template_recommendation" in agent_results:
            # Extract primary_result from standardized response
            recommendations_result = agent_results["template_recommendation"]
            if isinstance(recommendations_result, dict) and "data" in recommendations_result:
                self.session_state["recommendations"] = recommendations_result["data"]["primary_result"]
            else:
                self.session_state["recommendations"] = recommendations_result
        
        if "question_generation" in agent_results:
            # Extract primary_result from standardized response
            questions_result = agent_results["question_generation"]
            if isinstance(questions_result, dict) and "data" in questions_result:
                self.session_state["questions"] = questions_result["data"]["primary_result"]
            else:
                self.session_state["questions"] = questions_result
        
        # Step 5: Get final response from user proxy
        response = pipeline_result["final_output"]
        
        # Step 6: Update phase based on decision
        next_phase = phase_decision.get("next_phase", "template_recommendation")
        self.session_state["current_phase"] = next_phase
        
        self._add_to_conversation_history(response, "assistant")
        
        return {
            "success": True,
            "response": response,
            "session_id": self.session_id,
            "phase": "requirements",
            "next_phase": next_phase,
            "agent_results": agent_results,
            "reasoning": phase_decision.get("reasoning", ""),
            "requires_clarification": phase_decision.get("requires_clarification", False)
        }
    
    async def _handle_recommendation_phase(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle template recommendation phase"""
        
        # Use LLM to detect user intent
        user_intent = await self._detect_user_intent(message, "template_recommendation", context)
        
        if user_intent == "template_selection":
            # User is selecting a template - use LLM to parse which one
            selected_template = await self._parse_template_selection_llm(message, self.session_state["recommendations"])
            if selected_template:
                self.session_state["selected_template"] = selected_template
                self.session_state["current_phase"] = "template_selection"
                
                response = self.user_proxy_agent.confirm_template_selection(selected_template, "Template selected successfully")
                self._add_to_conversation_history(response, "assistant")
                
                return {
                    "success": True,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "template_selection",
                    "selected_template": selected_template
                }
            else:
                # Template parsing failed - use UserProxyAgent
                response = self.user_proxy_agent.create_response_from_instructions(
                    "template_selection_error",
                    {
                        "available_templates": self.session_state["recommendations"],
                        "user_message": message,
                        "session_state": self.session_state
                    }
                )
                
                self._add_to_conversation_history(response, "assistant")
                
                return {
                    "success": True,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "template_recommendation",
                    "intent": "not_understand"
                }
        
        elif user_intent == "question_answer":
            # User is answering questions about preferences - filter templates based on their answers
            current_recommendations = self.session_state.get("recommendations", [])
            current_requirements = self.session_state.get("requirements", {})
            
            # Update requirements with user's answers
            updated_requirements = self.requirements_agent.analyze_requirements(
                f"Additional requirements: {message}", 
                context={"existing_requirements": current_requirements}
            )
            
            # Filter templates based on updated requirements
            filtered_recommendations = self.recommendation_agent.recommend_templates(
                updated_requirements, 
                context={"existing_templates": current_recommendations}
            )
            
            # Generate new questions for the filtered templates
            new_questions = self.question_agent.generate_questions(filtered_recommendations, updated_requirements)
            
            # Update session state
            self.session_state["requirements"] = updated_requirements
            self.session_state["recommendations"] = filtered_recommendations
            self.session_state["questions"] = new_questions
            
            # If we have a clear winner (1 template) or no more questions needed, present the results
            if len(filtered_recommendations) == 1 or not new_questions.get("questions"):
                response = self.user_proxy_agent.create_response_from_instructions(
                    "present_filtered_recommendations",
                    {
                        "templates": filtered_recommendations,
                        "user_response": message,
                        "requirements": updated_requirements
                    }
                )
            else:
                response = self.user_proxy_agent.create_response_from_instructions(
                    "template recommendations",
                    {
                        "requirements": updated_requirements,
                        "templates": filtered_recommendations,
                        "targeted_questions": new_questions
                    }
                )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "template_recommendation",
                "recommendations": filtered_recommendations,
                "questions": new_questions
            }
        
        elif user_intent == "not_understand":
            # User's intent is unclear - use UserProxyAgent
            response = self.user_proxy_agent.create_response_from_instructions(
                "intent_detection_error",
                {
                    "current_phase": "template_recommendation",
                    "user_message": message,
                    "session_state": self.session_state
                }
            )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "template_recommendation",
                "intent": "not_understand"
            }
        
        # User is asking for clarification, modification, or general conversation
        # Regenerate recommendations with updated context
        requirements = self.session_state["requirements"]
        updated_requirements = self.requirements_agent.analyze_requirements(message, context=context)
        
        recommendations = self.recommendation_agent.recommend_templates(updated_requirements, context=context)
        questions_data = self.question_agent.generate_questions(recommendations, updated_requirements)
        
        # Update session state with the results
        self.session_state["requirements"] = updated_requirements
        self.session_state["recommendations"] = recommendations
        self.session_state["questions"] = questions_data
        
        response = self.user_proxy_agent.create_response_from_instructions(
            "template recommendations",
            {
                "requirements": updated_requirements,
                "templates": recommendations,
                "targeted_questions": questions_data
            }
        )
        
        self._add_to_conversation_history(response, "assistant")
        
        return {
            "success": True,
            "response": response,
            "session_id": self.session_id,
            "phase": "template_recommendation",
            "recommendations": recommendations,
            "questions": questions_data
        }
    
    async def _handle_selection_phase(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle template selection phase"""
        
        selected_template = self.session_state.get("selected_template")
        recommendations = self.session_state.get("recommendations", [])
        
        self.logger.info(f"Selection phase - Message: '{message}', Current selected_template: {selected_template}, Recommendations count: {len(recommendations)}")
        
        # Check if user is selecting a template
        if not selected_template and recommendations:
            # Try to detect template selection from user message
            selected_template = await self._parse_template_selection_llm(message, recommendations)
            
            self.logger.info(f"Template selection result: {selected_template}")
            
            if selected_template:
                self.session_state["selected_template"] = selected_template
                # Store in global session manager
                session_manager.set_selected_template(self.session_id, selected_template)
                self.logger.info(f"Template selected: {selected_template.get('name', 'Unknown')}")
                
                # Immediately trigger Phase 2 transition when template is first selected
                self.logger.info("Triggering immediate phase transition...")
                return await self._handle_phase_transition(selected_template)
        
        # If no template is selected, try to select one from recommendations
        if not selected_template and recommendations:
            # Auto-select the first/best template
            selected_template = recommendations[0]
            self.session_state["selected_template"] = selected_template
            # Store in global session manager
            session_manager.set_selected_template(self.session_id, selected_template)
            self.logger.info(f"Auto-selected template: {selected_template.get('name', 'Unknown')}")
            
            # Immediately trigger Phase 2 transition when template is auto-selected
            return await self._handle_phase_transition(selected_template)
        
        # If still no template, go back to recommendation phase
        if not selected_template:
            self.session_state["current_phase"] = "template_recommendation"
            return await self._handle_recommendation_phase(message, context)
        
        # If we already have a selected template, handle additional user input
        # Use LLM to detect user intent
        user_intent = await self._detect_user_intent(message, "template_selection", context)
        
        if user_intent == "editing":
            # User wants to edit the template
            self.session_state["current_phase"] = "editing"
            return await self._handle_editing_phase(message, context)
        
        elif user_intent == "report":
            # User wants to generate a report
            return await self._handle_report_generation(message, context)
        
        elif user_intent == "template_confirmation" or user_intent == "template_selection":
            # User confirmed template selection - trigger Phase 2 transition
            return await self._handle_phase_transition(selected_template)
        
        elif user_intent == "not_understand":
            # User's intent is unclear - use UserProxyAgent
            response = self.user_proxy_agent.create_response_from_instructions(
                "intent_detection_error",
                {
                    "current_phase": "template_selection",
                    "user_message": message,
                    "selected_template": selected_template,
                    "session_state": self.session_state
                }
            )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "template_selection",
                "intent": "not_understand",
                "selected_template": selected_template,
                "session_state": self.session_state
            }
        
        else:
            # Default: confirm selection and ask for next steps
            response = self.user_proxy_agent.create_response_from_instructions(
                "template_selected_confirmation",
                {
                    "selected_template": selected_template,
                    "next_steps": "You can now edit this template or generate a report"
                }
            )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "template_selection",
                "selected_template": selected_template,
                "session_state": self.session_state,
                "transition_ready": True  # Signal that transition is ready
            }
    
    async def _handle_editing_phase(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle template editing phase"""
        
        selected_template = self.session_state["selected_template"]
        
        # Use UI editing agent to process modification request
        modification_result = self.editing_agent.process_modification_request(message, selected_template)
        
        response = self.user_proxy_agent.create_response_from_instructions(
            "modified template",
            {
                "modification_result": modification_result,
                "selected_template": selected_template
            }
        )
        
        self._add_to_conversation_history(response, "assistant")
        
        return {
            "success": True,
            "response": response,
            "session_id": self.session_id,
            "phase": "editing",
            "modification_result": modification_result
        }
    
    async def _handle_report_generation(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle report generation"""
        
        # Prepare project data
        project_data = {
            "project_name": f"UI Project {self.session_id[:8]}",
            "created_date": self.session_state["created_at"].isoformat(),
            "user_requirements": self.session_state["requirements"],
            "selected_template": self.session_state["selected_template"],
            "conversation_history": self.session_state["conversation_history"]
        }
        
        # Generate report using focused agent
        report_filepath = self.report_agent.generate_project_report_advanced(project_data)
        
        response = f"Report generated successfully! You can find it at: {report_filepath}"
        
        self._add_to_conversation_history(response, "assistant")
        
        return {
            "success": True,
            "response": response,
            "session_id": self.session_id,
            "phase": "report_generation",
            "report_filepath": report_filepath
        }
    
    async def _detect_initial_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM to detect the initial intent and page type from user message"""
        try:
            prompt = f"""
You are an initial intent detection system for a UI mockup generation workflow.

User message: "{message}"

Analyze this message to determine:
1. The user's initial intent
2. The page type they want to create (if mentioned)

INTENT OPTIONS:
- "create_ui_mockup" - User wants to create a new UI mockup (e.g., "I want to build a login UI mockup", "create a landing page")
- "requirements_analysis" - User wants to discuss requirements first
- "template_recommendation" - User wants template recommendations
- "template_selection" - User wants to select from existing templates
- "editing" - User wants to edit an existing template
- "report" - User wants to generate a report
- "general" - General conversation

PAGE TYPE OPTIONS (if creating UI mockup):
- "login" - Login page, sign in page, authentication page
- "signup" - Signup page, registration page, sign up page
- "landing" - Landing page, homepage, main page
- "profile" - Profile page, user account page
- "about" - About page, about us page

Return your response in this format:
INTENT: [intent_type]
PAGE_TYPE: [page_type or "none"]

Examples:
- "I want to build a login UI mockup" → INTENT: create_ui_mockup, PAGE_TYPE: login
- "Create a landing page" → INTENT: create_ui_mockup, PAGE_TYPE: landing
- "Show me some templates" → INTENT: template_recommendation, PAGE_TYPE: none
- "Hello" → INTENT: general, PAGE_TYPE: none
"""

            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=False)
            
            # Parse the response
            intent = "general"
            page_type = None
            
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith("INTENT:"):
                    intent = line.split(":", 1)[1].strip().lower()
                elif line.startswith("PAGE_TYPE:"):
                    page_type = line.split(":", 1)[1].strip().lower()
                    if page_type == "none":
                        page_type = None
            
            # Validate intent
            valid_intents = list(self.keyword_manager.get_intent_keywords().keys())
            if intent not in valid_intents:
                intent = "general"
            
            # Store page type in session state if detected
            if page_type:
                self.session_state["detected_page_type"] = page_type
            
            return intent
                
        except Exception as e:
            self.logger.error(f"Error in initial intent detection: {e}")
            return "general"
    
    async def _detect_user_intent(self, message: str, current_phase: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM to detect user intent"""
        try:
            recommendations = self.session_state.get("recommendations", [])
            requirements = self.session_state.get("requirements", {})
            questions = self.session_state.get("questions", {})
            
            # Build context for LLM
            context_info = ""
            if recommendations:
                template_names = [rec.get("template", {}).get("name", "Unknown") for rec in recommendations[:3]]
                context_info = f"Available templates: {', '.join(template_names)}"
            
            # Check if we recently asked questions
            recent_questions = questions.get("questions", []) if questions else []
            question_context = ""
            if recent_questions:
                question_texts = [q.get("question", "") for q in recent_questions[:3]]
                question_context = f"Recent questions asked: {'; '.join(question_texts)}"
            
            # Different prompts for different phases
            if current_phase == "template_recommendation":
                prompt = f"""
You are an intent detection system for a UI mockup generation workflow.

Current phase: {current_phase}
User message: "{message}"
{context_info}
{question_context}

IMPORTANT: If the user is answering questions we recently asked (like preferences for features, styles, etc.), classify this as "question_answer" to filter templates based on their preferences.

Determine the user's intent from this message. Choose from:

1. "question_answer" - User is answering questions about preferences (e.g., "I need form-based", "no banner", "modern style", "yes to that feature")
2. "template_selection" - User is selecting a specific template (e.g., "I choose template 1", "landing 1", "option 2", "that one")
3. "clarification" - User wants more information or different options (e.g., "show me other options", "I want something different", "more templates")
4. "modification" - User wants to modify requirements (e.g., "make it more modern", "change the color", "different style")
5. "confirmation" - User is confirming a choice (e.g., "yes", "perfect", "that's good")
6. "not_understand" - User's intent is unclear, ambiguous, or cannot be determined
7. "general" - General conversation that doesn't fit other categories

Return ONLY the intent type (e.g., "question_answer").
"""
            elif current_phase == "template_selection":
                prompt = f"""
You are an intent detection system for a UI mockup generation workflow.

Current phase: {current_phase}
User message: "{message}"
Selected template: {self.session_state.get("selected_template", {}).get("name", "Unknown")}

Determine the user's intent from this message. Choose from:

1. "template_confirmation" - User is confirming the selection and wants to proceed (e.g., "yes", "perfect", "that's good", "proceed", "view the preview", "show me the preview", "let's see it", "continue", "go ahead")
2. "editing" - User wants to modify the selected template (e.g., "change the color", "make it more modern", "edit this", "modify")
3. "report" - User wants to generate a report or summary (e.g., "generate report", "create summary", "show me the details")
4. "not_understand" - User's intent is unclear, ambiguous, or cannot be determined
5. "general" - General conversation that doesn't fit other categories

Return ONLY the intent type (e.g., "template_confirmation").
"""
            else:
                prompt = f"""
You are an intent detection system for a UI mockup generation workflow.

Current phase: {current_phase}
User message: "{message}"

Determine the user's intent from this message. Choose from:

1. "clarification" - User wants more information or different options
2. "modification" - User wants to modify requirements
3. "confirmation" - User is confirming a choice
4. "not_understand" - User's intent is unclear, ambiguous, or cannot be determined
5. "general" - General conversation that doesn't fit other categories

Return ONLY the intent type (e.g., "clarification").
"""

            # Call LLM for intent detection
            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=False)
            
            # Parse response
            intent = response.strip().lower()
            
            # Validate intent based on phase
            if current_phase == "template_recommendation":
                valid_intents = ["question_answer", "template_selection", "clarification", "modification", "confirmation", "not_understand", "general"]
                if intent in valid_intents:
                    return intent
                else:
                    return "general"
            elif current_phase == "template_selection":
                valid_intents = ["template_confirmation", "editing", "report", "not_understand", "general"]
                if intent in valid_intents:
                    return intent
                else:
                    return "general"
            else:
                valid_intents = ["clarification", "modification", "confirmation", "not_understand", "general"]
                if intent in valid_intents:
                    return intent
                else:
                    return "general"
                
        except Exception as e:
            self.logger.error(f"Error in intent detection: {e}")
            return "not_understand"
    
    async def _parse_template_selection_llm(self, message: str, recommendations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Use LLM to parse which template the user is selecting"""
        try:
            self.logger.info(f"Parsing template selection from message: '{message}'")
            self.logger.info(f"Available recommendations: {[rec.get('template', {}).get('name', 'Unknown') for rec in recommendations]}")
            
            # Build template list for LLM
            template_list = []
            for i, rec in enumerate(recommendations, 1):
                template = rec.get("template", {})
                template_list.append(f"{i}. {template.get('name', 'Unknown')} - {template.get('description', 'No description')}")
            
            template_info = "\n".join(template_list)
            
            prompt = f"""
You are a template selection parser for a UI mockup system.

User message: "{message}"

Available templates:
{template_info}

Parse which template the user is selecting. Consider:
- Number references: "1", "first", "option 1", "template 1"
- Ordinal references: "third one", "second option", "first template", "last one"
- Name references: "landing 1", "login template"
- Implicit references: "that one", "this template", "the first option"
- Partial matches: "landing" when there's only one landing template

If the user's selection is unclear, ambiguous, or doesn't match any template, return "unclear".

Return ONLY the template number (1, 2, 3, etc.) or "unclear" if the selection cannot be determined.
"""

            # Call LLM for parsing
            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=False)
            
            self.logger.info(f"LLM response for template selection: '{response}'")
            
            # Parse response
            try:
                selection = response.strip().lower()
                # Check if selection is unclear
                if selection in self.keyword_manager.get_template_selection_keywords()["unclear_responses"]:
                    self.logger.info(f"LLM could not parse template selection from: '{message}'")
                    return None
                
                # Try to extract number
                number_match = re.search(r'\d+', selection)
                if number_match:
                    template_index = int(number_match.group()) - 1
                    if 0 <= template_index < len(recommendations):
                        selected_template = recommendations[template_index].get("template", {})
                        self.logger.info(f"Selected template {template_index + 1}: {selected_template.get('name', 'Unknown')}")
                        return selected_template
                
                # Try to match by ordinal words
                ordinal_mapping = {
                    "first": 0, "1st": 0, "one": 0,
                    "second": 1, "2nd": 1, "two": 1,
                    "third": 2, "3rd": 2, "three": 2,
                    "fourth": 3, "4th": 3, "four": 3,
                    "fifth": 4, "5th": 4, "five": 4
                }
                
                for ordinal_word, index in ordinal_mapping.items():
                    if ordinal_word in selection and index < len(recommendations):
                        selected_template = recommendations[index].get("template", {})
                        self.logger.info(f"Selected template by ordinal '{ordinal_word}': {selected_template.get('name', 'Unknown')}")
                        return selected_template
                
                # Try to match by name
                for rec in recommendations:
                    template = rec.get("template", {})
                    template_name = template.get("name", "").lower()
                    if template_name in selection.lower():
                        self.logger.info(f"Selected template by name '{template_name}': {template.get('name', 'Unknown')}")
                        return template
                
                # If we get here, the selection was unclear
                self.logger.info(f"Could not match template selection '{selection}' to any available template")
                return None
                
            except Exception as e:
                self.logger.error(f"Error parsing template selection: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in template selection parsing: {e}")
            return None
    
    async def _analyze_phase_requirements(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Intelligent analysis to decide which agents to use and in what order"""
        
        try:
            current_phase = self.session_state["current_phase"]
            
            prompt = f"""
You are an intelligent orchestrator for a UI mockup generation system. Analyze the current situation and decide which agents should be used.

CURRENT CONTEXT:
- Phase: {current_phase}
- User Message: "{message}"
- Session State: {self.session_state}
- Previous Context: {context or {}}

AVAILABLE AGENTS:
1. requirements_analysis - Analyzes user requirements and extracts specifications
2. template_recommendation - Recommends templates based on requirements
3. question_generation - Generates clarifying questions to narrow down choices
4. user_proxy - Formats responses for user interaction

ANALYSIS TASK:
Determine which agents are needed and in what order based on:
- Current phase requirements
- User message content
- Existing session state
- Whether clarification is needed

Return a structured JSON response:

{{
    "required_agents": ["list", "of", "agent", "names", "in", "execution", "order"],
    "skip_agents": ["list", "of", "agents", "to", "skip"],
    "context_updates": {{
        "key": "value"  // Any context updates needed
    }},
    "next_phase": "string",  // What phase to transition to
    "reasoning": "string",   // Why these decisions were made
    "requires_clarification": boolean,  // Whether user clarification is needed
    "clarification_questions": ["list", "of", "questions", "if", "needed"]
}}

EXAMPLES:
- User says "I want a modern login page" → Use requirements_analysis, then template_recommendation
- User says "show me template 1" → Skip requirements_analysis, go directly to template selection
- User says "I'm not sure" → Use question_generation to get clarification
- User says "make it more colorful" → Skip requirements_analysis, go to editing phase
"""

            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=True)
            
            # Parse the structured response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # Clean up common JSON issues
                    json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                    decision = json.loads(json_str)
                else:
                    # Fallback to default decision
                    self.logger.warning("No JSON found in response, using default decision")
                    decision = self._get_default_phase_decision(current_phase, message)
                
                return decision
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {e}")
                self.logger.error(f"Response was: {response}")
                return self._get_default_phase_decision(current_phase, message)
            except Exception as e:
                self.logger.error(f"Error parsing orchestrator decision: {e}")
                return self._get_default_phase_decision(current_phase, message)
                
        except Exception as e:
            self.logger.error(f"Error in phase requirements analysis: {e}")
            return self._get_default_phase_decision(current_phase, message)
    
    def _get_default_phase_decision(self, current_phase: str, message: str) -> Dict[str, Any]:
        """Fallback decision when LLM analysis fails"""
        
        if current_phase == "requirements":
            return {
                "required_agents": ["requirements_analysis", "template_recommendation", "question_generation", "user_proxy"],
                "skip_agents": [],
                "context_updates": {},
                "next_phase": "template_recommendation",
                "reasoning": "Default: Full analysis pipeline with user response formatting",
                "requires_clarification": False,
                "clarification_questions": []
            }
        elif current_phase == "template_recommendation":
            return {
                "required_agents": ["template_recommendation", "question_generation", "user_proxy"],
                "skip_agents": ["requirements_analysis"],
                "context_updates": {},
                "next_phase": "template_recommendation",
                "reasoning": "Default: Template recommendation with questions and user response formatting",
                "requires_clarification": False,
                "clarification_questions": []
            }
        else:
            return {
                "required_agents": ["user_proxy"],
                "skip_agents": [],
                "context_updates": {},
                "next_phase": current_phase,
                "reasoning": "Default: User interaction only",
                "requires_clarification": True,
                "clarification_questions": ["What would you like to do next?"]
            }

    def _build_agent_context(self, agent_name: str, previous_output: Any, base_context: Dict) -> Dict:
        """Build appropriate context for each agent based on previous outputs"""
        
        context = {}
        
        if agent_name == "requirements_analysis":
            # Full context for requirements analysis
            context = base_context.copy()
            
        elif agent_name == "template_recommendation":
            # Minimal context + requirements output
            context = {
                "page_type": base_context.get("page_type"),
                "requirements": previous_output if previous_output else {}
            }
            
        elif agent_name == "question_generation":
            # Template recommendations + requirements
            context = {
                "templates": previous_output if previous_output else [],
                "requirements": self.session_state.get("requirements", {})
            }
            
        elif agent_name == "user_proxy":
            # All available data for response formatting
            context = {
                "session_state": self.session_state,
                "previous_output": previous_output,
                "base_context": base_context
            }
            
        return context

    def _execute_agent_pipeline(self, required_agents: List[str], message: str, context: Dict) -> Dict[str, Any]:
        """Execute agents in the specified order with proper data flow"""
        
        current_output = None
        agent_results = {}
        
        # Ensure user_proxy is always last if present
        if "user_proxy" in required_agents:
            # Remove user_proxy from the list and add it at the end
            required_agents = [agent for agent in required_agents if agent != "user_proxy"] + ["user_proxy"]
        
        for agent_name in required_agents:
            try:
                agent_context = self._build_agent_context(agent_name, current_output, context)
                
                if agent_name == "requirements_analysis":
                    try:
                        result = self.requirements_agent.analyze_requirements(message, context=agent_context)
                        # Standardize the output
                        result = self.requirements_agent.enhance_agent_output(result, agent_context)
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    except Exception as e:
                        self.logger.error(f"Error in requirements_analysis: {e}")
                        # Create error response
                        result = self.requirements_agent.create_standardized_response(
                            success=False,
                            data={
                                "primary_result": {},
                                "error": str(e),
                                "requires_clarification": True,
                                "clarification_questions": ["Could you please clarify your requirements?"]
                            },
                            metadata={"context_used": agent_context}
                        )
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    
                elif agent_name == "template_recommendation":
                    try:
                        requirements = self.session_state.get("requirements") or current_output
                        result = self.recommendation_agent.recommend_templates(requirements, context=agent_context)
                        # Standardize the output
                        result = self.recommendation_agent.enhance_agent_output(result, agent_context)
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    except Exception as e:
                        self.logger.error(f"Error in template_recommendation: {e}")
                        # Create error response
                        result = self.recommendation_agent.create_standardized_response(
                            success=False,
                            data={
                                "primary_result": [],
                                "error": str(e),
                                "requires_clarification": True,
                                "clarification_questions": ["Could you please provide more specific requirements?"]
                            },
                            metadata={"context_used": agent_context}
                        )
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    
                elif agent_name == "question_generation":
                    try:
                        # Extract templates from current_output (which is from template_recommendation agent)
                        templates = []
                        if isinstance(current_output, list):
                            templates = current_output
                        elif isinstance(current_output, dict) and "data" in current_output:
                            templates = current_output["data"].get("primary_result", [])
                        else:
                            templates = self.session_state.get("recommendations", [])
                        
                        requirements = self.session_state.get("requirements", {})
                        result = self.question_agent.generate_questions(templates, requirements)
                        # The result is already a dictionary, not standardized format
                        current_output = result
                        agent_results[agent_name] = result
                    except Exception as e:
                        self.logger.error(f"Error in question_generation: {e}")
                        # Create error response
                        result = {
                            "questions": [],
                            "focus_areas": [],
                            "template_count": 0,
                            "error": str(e)
                        }
                        current_output = result
                        agent_results[agent_name] = result
                    
                elif agent_name == "user_proxy":
                    # UserProxyAgent handles response formatting - this should be the final output
                    # Extract templates from agent results
                    templates = []
                    if "template_recommendation" in agent_results:
                        rec_result = agent_results["template_recommendation"]
                        if isinstance(rec_result, dict) and "data" in rec_result:
                            templates = rec_result["data"].get("primary_result", [])
                        else:
                            templates = rec_result
                    
                    result = self.user_proxy_agent.create_response_from_instructions(
                        "template recommendations",
                        {
                            "requirements": self.session_state.get("requirements"),
                            "templates": templates,
                            "targeted_questions": self.session_state.get("questions"),
                            "agent_results": agent_results
                        }
                    )
                    current_output = result  # This should be a string
                    agent_results[agent_name] = result
                    
            except Exception as e:
                self.logger.error(f"Error executing agent {agent_name}: {e}")
                # Ask user for clarification on failure
                return {
                    "success": False,
                    "error": f"Error in {agent_name}: {str(e)}",
                    "requires_clarification": True,
                    "clarification_questions": [f"I encountered an issue with {agent_name}. Could you please clarify your request?"]
                }
        
        # Ensure final output is always a string for the API response
        if isinstance(current_output, dict):
            # If we have a dictionary, try to convert it to a string representation
            try:
                if "questions" in current_output and "template_count" in current_output:
                    # This looks like question generation output - format it nicely
                    questions = current_output.get("questions", [])
                    template_count = current_output.get("template_count", 0)
                    
                    if questions:
                        response = f"I found {template_count} templates that match your requirements. To help you choose, let me ask a few questions:\n\n"
                        for i, question_data in enumerate(questions[:3]):
                            question = question_data.get("question", "")
                            response += f"{i+1}. {question}\n"
                        response += "\nPlease answer any of these questions to help me narrow down the best template for you."
                    else:
                        response = f"I found {template_count} templates that match your requirements. Would you like me to show you the options?"
                elif isinstance(current_output, list) and len(current_output) > 0 and isinstance(current_output[0], dict) and "template" in current_output[0]:
                    # This looks like template recommendations - format them nicely
                    template_count = len(current_output)
                    response = f"I found {template_count} great templates that match your requirements!\n\n"
                    
                    for i, template_data in enumerate(current_output[:3]):  # Show top 3
                        template = template_data.get("template", {})
                        template_name = template.get("name", f"Template {i+1}")
                        template_description = template.get("description", "No description available")
                        score = template_data.get("score", 0)
                        
                        response += f"{i+1}. {template_name} - {template_description}"
                        if score > 0:
                            response += f" (Match: {score:.1%})"
                        response += "\n"
                    
                    response += "\nTo proceed, please choose a template by saying its name or number, or ask for more details about any template."
                else:
                    # Generic dictionary to string conversion
                    response = str(current_output)
            except Exception as e:
                self.logger.error(f"Error converting dict to string: {e}")
                response = "I've processed your request and found some options. Let me know how you'd like to proceed."
        elif isinstance(current_output, list) and len(current_output) > 0:
            # Handle list output (like template recommendations)
            if isinstance(current_output[0], dict) and "template" in current_output[0]:
                # Template recommendations list
                template_count = len(current_output)
                response = f"I found {template_count} great templates that match your requirements!\n\n"
                
                for i, template_data in enumerate(current_output[:3]):  # Show top 3
                    template = template_data.get("template", {})
                    template_name = template.get("name", f"Template {i+1}")
                    template_description = template.get("description", "No description available")
                    score = template_data.get("score", 0)
                    
                    response += f"{i+1}. {template_name} - {template_description}"
                    if score > 0:
                        response += f" (Match: {score:.1%})"
                    response += "\n"
                
                response += "\nTo proceed, please choose a template by saying its name or number, or ask for more details about any template."
            else:
                # Generic list to string conversion
                response = f"I found {len(current_output)} items that match your requirements. Let me know how you'd like to proceed."
        else:
            response = str(current_output) if current_output is not None else "I've processed your request. Let me know how you'd like to proceed."
        
        # Final safety check: if user_proxy was not in the pipeline, format the response
        if "user_proxy" not in agent_results and not isinstance(response, str):
            # Try to format the response using user_proxy agent
            try:
                formatted_response = self.user_proxy_agent.create_response_from_instructions(
                    "template recommendations",
                    {
                        "requirements": self.session_state.get("requirements"),
                        "templates": self.session_state.get("recommendations"),
                        "targeted_questions": self.session_state.get("questions"),
                        "agent_results": agent_results
                    }
                )
                response = formatted_response
            except Exception as e:
                self.logger.error(f"Error formatting response with user_proxy: {e}")
                # Keep the fallback response we already created
        
        return {
            "success": True,
            "agent_results": agent_results,
            "final_output": response
        }
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        return {
            "session_id": self.session_id,
            "current_phase": self.session_state["current_phase"],
            "conversation_history_length": len(self.session_state["conversation_history"]),
            "has_requirements": self.session_state["requirements"] is not None,
            "has_recommendations": self.session_state["recommendations"] is not None,
            "has_selected_template": self.session_state["selected_template"] is not None,
            "created_at": self.session_state["created_at"].isoformat()
        }
    
    def reset_session(self) -> Dict[str, Any]:
        """Reset the session"""
        self.session_id = str(uuid.uuid4())
        self.session_state = {
            "current_phase": "initial",
            "conversation_history": [],
            "requirements": {},
            "recommendations": [],
            "questions": {},
            "selected_template": None,
            "modifications": [],
            "report": None
        }
        session_manager.update_session(self.session_id, self.session_state)
        
        return {
            "success": True,
            "message": "Session reset successfully",
            "session_id": self.session_id
        } 

    def handle_editing_phase(self, user_message: str, current_ui_state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle Phase 2: UI Editing - coordinate between UI Editing Agent and User Proxy Agent"""
        try:
            self.logger.info(f"Handling editing phase request for session {session_id}")
            
            # Step 1: Detect editing intent
            intent = self._detect_editing_intent(user_message)
            self.logger.info(f"Detected editing intent: {intent}")
            
            # Step 2: Route based on intent
            if intent == "modification_request":
                return self._handle_modification_request(user_message, current_ui_state, session_id)
            elif intent == "clarification_request":
                return self._handle_clarification_request(user_message, current_ui_state, session_id)
            elif intent == "completion_request":
                return self._handle_completion_request(user_message, current_ui_state, session_id)
            else:
                return self._handle_general_request(user_message, current_ui_state, session_id)
                
        except Exception as e:
            self.logger.error(f"Error in editing phase: {e}")
            return self._create_error_response(f"Error processing your request: {str(e)}")
    
    def _detect_editing_intent(self, user_message: str) -> str:
        """Detect the intent of the user's editing request"""
        try:
            message_lower = user_message.lower()
            
            # Completion indicators
            if any(phrase in message_lower for phrase in [
                "i'm done", "that's perfect", "finished", "complete", "good enough",
                "generate report", "show me the final", "create report"
            ]):
                return "completion_request"
            
            # Clarification indicators
            if any(phrase in message_lower for phrase in [
                "what can i change", "what options", "help", "what's possible",
                "show me options", "what else", "suggestions"
            ]):
                return "clarification_request"
            
            # General conversation indicators (should be checked before modification)
            if any(phrase in message_lower for phrase in [
                "hello", "hi", "hey", "how are you", "thank", "thanks",
                "how does this work", "what is this", "explain"
            ]):
                return "general_request"
            
            # Modification indicators (more specific)
            if any(phrase in message_lower for phrase in [
                "change", "modify", "update", "make", "set", "adjust", "edit",
                "color", "size", "font", "background", "button", "text"
            ]):
                return "modification_request"
            
            # Default to general request for unclear messages
            return "general_request"
            
        except Exception as e:
            self.logger.error(f"Error detecting editing intent: {e}")
            return "general_request"  # Safe default
    
    def _handle_modification_request(self, user_message: str, current_ui_state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle UI modification requests"""
        try:
            self.logger.info("Processing modification request")
            
            # Step 3: UI Editing Agent performs the modification
            ui_editing_result = self._process_ui_modification(user_message, current_ui_state)
            
            if not ui_editing_result["success"]:
                return self._create_error_response(ui_editing_result["error"])
            
            # Step 4: Orchestrator instructs User Proxy
            user_proxy_instruction = {
                "type": "modification_success",
                "modification_result": ui_editing_result,
                "user_message": user_message,
                "context": {
                    "session_id": session_id,
                    "previous_changes": self._get_previous_changes(session_id)
                }
            }
            
            # Step 5: User Proxy Agent responds to user
            user_response = self._generate_user_response(user_proxy_instruction)
            
            # Extract modifications for the response
            modifications = ui_editing_result.get("modifications")
            
            return {
                "success": True,
                "response": user_response,
                "modifications": modifications,  # Ensure modifications are included
                "metadata": {
                    "session_id": session_id,
                    "intent": "modification_request",
                    "change_summary": ui_editing_result.get("change_summary", "Changes analyzed successfully")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling modification request: {e}")
            return self._create_error_response(f"Error processing modification: {str(e)}")
    
    def _process_ui_modification(self, user_message: str, current_ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process UI modification using UI Editing Agent"""
        try:
            # Create UI Editing Agent instance
            from agents.ui_editing_agent import UIEditingAgent
            ui_agent = UIEditingAgent()
            
            # Create context for the agent
            context = {
                "current_ui_codes": current_ui_state,
                "session_id": "editing_session",
                "available_tools": ["css_change", "html_change", "js_change", "complete_change"]
            }
            
            # Analyze the request
            ui_response = ui_agent.analyze_ui_request(user_message, context)
            
            if not ui_response["success"]:
                return {
                    "success": False,
                    "error": ui_response["data"].get("response", "Failed to analyze request")
                }
            
            # Extract modifications
            modifications = ui_response["data"].get("modifications")
            
            if modifications:
                # For now, return the modifications without applying them
                # The actual application will be handled by the frontend calling the modify endpoint
                return {
                    "success": True,
                    "modifications": modifications,
                    "change_summary": ui_response["data"].get("response", "Changes analyzed successfully")
                }
            else:
                return {
                    "success": True,
                    "modifications": None,
                    "change_summary": ui_response["data"].get("response", "No changes needed")
                }
                
        except Exception as e:
            self.logger.error(f"Error processing UI modification: {e}")
            return {
                "success": False,
                "error": f"Error processing modification: {str(e)}"
            }
    
    def _handle_clarification_request(self, user_message: str, current_ui_state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle clarification requests"""
        try:
            # Create User Proxy Agent instance
            from agents.user_proxy_agent import UserProxyAgent
            user_proxy = UserProxyAgent()
            
            # Generate helpful suggestions
            suggestions = self._generate_editing_suggestions(current_ui_state)
            
            instruction = {
                "type": "clarification_response",
                "user_message": user_message,
                "suggestions": suggestions,
                "context": {"session_id": session_id}
            }
            
            response = user_proxy.create_response_from_instructions(instruction)
            
            return {
                "success": True,
                "response": response,
                "metadata": {
                    "session_id": session_id,
                    "intent": "clarification_request",
                    "suggestions": suggestions
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling clarification request: {e}")
            return self._create_error_response(f"Error providing suggestions: {str(e)}")
    
    def _handle_completion_request(self, user_message: str, current_ui_state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle completion requests"""
        try:
            # Create User Proxy Agent instance
            from agents.user_proxy_agent import UserProxyAgent
            user_proxy = UserProxyAgent()
            
            instruction = {
                "type": "completion_response",
                "user_message": user_message,
                "context": {
                    "session_id": session_id,
                    "final_ui_state": current_ui_state
                }
            }
            
            response = user_proxy.create_response_from_instructions(instruction)
            
            return {
                "success": True,
                "response": response,
                "metadata": {
                    "session_id": session_id,
                    "intent": "completion_request",
                    "final_ui_state": current_ui_state
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling completion request: {e}")
            return self._create_error_response(f"Error processing completion: {str(e)}")
    
    def _handle_general_request(self, user_message: str, current_ui_state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle general requests that don't fit other categories"""
        try:
            # Create User Proxy Agent instance
            from agents.user_proxy_agent import UserProxyAgent
            user_proxy = UserProxyAgent()
            
            instruction = {
                "type": "general_response",
                "user_message": user_message,
                "context": {"session_id": session_id}
            }
            
            response = user_proxy.create_response_from_instructions(instruction)
            
            return {
                "success": True,
                "response": response,
                "metadata": {
                    "session_id": session_id,
                    "intent": "general_request"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling general request: {e}")
            return self._create_error_response(f"Error processing request: {str(e)}")
    
    def _generate_user_response(self, instruction: Dict[str, Any]) -> str:
        """Generate user response using User Proxy Agent"""
        try:
            from agents.user_proxy_agent import UserProxyAgent
            user_proxy = UserProxyAgent()
            
            return user_proxy.create_response_from_instructions(instruction)
            
        except Exception as e:
            self.logger.error(f"Error generating user response: {e}")
            return "I've processed your request. Check the preview to see the changes!"
    
    def _generate_editing_suggestions(self, current_ui_state: Dict[str, Any]) -> List[str]:
        """Generate helpful editing suggestions based on current UI state"""
        suggestions = []
        
        # Analyze current UI to provide contextual suggestions
        html_content = current_ui_state.get("html_export", "")
        css_content = current_ui_state.get("style_css", "") + current_ui_state.get("globals_css", "")
        
        # Check for common elements and suggest modifications
        if "button" in html_content.lower():
            suggestions.extend([
                "Change button colors (e.g., 'make the button red')",
                "Adjust button size (e.g., 'make the button bigger')",
                "Modify button text (e.g., 'change button text to Submit')"
            ])
        
        if "title" in html_content.lower() or "h1" in html_content.lower():
            suggestions.extend([
                "Change title text (e.g., 'change the title to Welcome')",
                "Adjust title size (e.g., 'make the title bigger')",
                "Modify title color (e.g., 'make the title blue')"
            ])
        
        if "background" in css_content.lower():
            suggestions.extend([
                "Change background color (e.g., 'make background light blue')",
                "Adjust background style (e.g., 'add a gradient background')"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Change text colors (e.g., 'make text dark blue')",
            "Adjust font sizes (e.g., 'make text bigger')",
            "Modify spacing (e.g., 'add more space between elements')",
            "Change layout (e.g., 'center the content')"
        ])
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    def _get_previous_changes(self, session_id: str) -> List[Dict[str, Any]]:
        """Get previous changes for context"""
        try:
            # This would typically fetch from the session history
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting previous changes: {e}")
            return []
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "response": f"I'm sorry, I encountered an error: {error_message}",
            "metadata": {
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        } 

    async def _handle_phase_transition(self, selected_template: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the complete transition from Phase 1 to Phase 2"""
        try:
            self.logger.info(f"Starting Phase 1 → Phase 2 transition for template: {selected_template.get('name', 'Unknown')}")
            self.logger.info(f"Selected template structure: {selected_template}")
            
            # Step 1: Save conversation history to session
            self.session_state["phase1_conversation_history"] = self.session_state.get("conversation_history", [])
            
            # Step 2: Extract the actual template data from the recommendation structure
            # The selected_template might be a recommendation wrapper with template data inside
            actual_template = selected_template
            if "template" in selected_template:
                actual_template = selected_template["template"]
                self.logger.info(f"Extracted actual template from recommendation wrapper: {actual_template.get('name', 'Unknown')}")
            
            # Step 3: Create JSON file for the selected template
            template_id = actual_template.get('template_id') or actual_template.get('_id')
            if not template_id:
                self.logger.error(f"No template ID found in selected template: {actual_template}")
                raise ValueError("No template ID found in selected template")
            
            self.logger.info(f"Template ID for transition: {template_id}")
            
            # Step 4: Call the template-to-json endpoint to create the JSON file
            from tools.ui_preview_tools import UIPreviewTools
            ui_tools = UIPreviewTools()
            template_result = ui_tools.get_template_code(template_id)
            
            self.logger.info(f"Template result: {template_result}")
            
            if not template_result or not template_result.get("success", False):
                error_msg = template_result.get("error", "Unknown error") if template_result else "No result returned"
                raise ValueError(f"Failed to fetch template code for ID: {template_id}. Error: {error_msg}")
            
            # Step 5: Create the JSON structure for Phase 2
            ui_codes_data = {
                "template_id": template_id,
                "session_id": self.session_id,
                "last_updated": datetime.now().isoformat(),
                "current_codes": {
                    "html_export": template_result.get("html_export", ""),
                    "globals_css": template_result.get("global_css", ""),
                    "style_css": template_result.get("style_css", ""),
                    "js": "",
                    "complete_html": self._create_complete_html(template_result)
                },
                "history": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "modification": f"Template '{actual_template.get('name', 'Unknown')}' selected from Phase 1"
                    }
                ],
                "template_info": {
                    "name": actual_template.get("name", "Unknown"),
                    "category": actual_template.get("category", "unknown"),
                    "description": actual_template.get("description", ""),
                    "tags": actual_template.get("tags", [])
                }
            }
            
            # Step 6: Save the JSON file
            import json
            import os
            
            # Ensure temp_ui_files directory exists
            temp_dir = "temp_ui_files"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # Save the JSON file
            json_filename = f"ui_codes_{self.session_id}.json"
            json_filepath = os.path.join(temp_dir, json_filename)
            
            with open(json_filepath, 'w') as f:
                json.dump(ui_codes_data, f, indent=2)
            
            self.logger.info(f"JSON file created: {json_filepath}")
            
            # Step 7: Update session state
            self.session_state["current_phase"] = "editing"
            self.session_state["selected_template"] = selected_template
            self.session_state["ui_codes_file"] = json_filepath
            self.session_state["phase_transition_completed"] = True
            
            # Update global session manager
            session_manager.update_session(self.session_id, self.session_state)
            
            # Step 8: Create transition response
            transition_response = self.user_proxy_agent.create_response_from_instructions({
                "response_type": "phase_transition_complete",
                "selected_template": selected_template,
                "session_id": self.session_id,
                "transition_data": {
                    "fromPhase1": True,
                    "sessionId": self.session_id,
                    "selectedTemplate": selected_template,
                    "category": selected_template.get("category"),
                    "ui_codes_file": json_filename
                }
            })
            
            self.logger.info(f"Phase transition response: {transition_response}")
            
            final_response = {
                "success": True,
                "response": transition_response,
                "session_id": self.session_id,
                "phase": "editing",
                "intent": "phase_transition",
                "selected_template": selected_template,
                "session_state": self.session_state,
                "transition_data": {
                    "fromPhase1": True,
                    "sessionId": self.session_id,
                    "selectedTemplate": selected_template,
                    "category": selected_template.get("category"),
                    "ui_codes_file": json_filename
                }
            }
            
            self.logger.info(f"Final phase transition response: {final_response}")
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error during phase transition: {e}")
            return {
                "success": False,
                "response": f"Error during transition: {str(e)}",
                "session_id": self.session_id,
                "phase": "template_selection"
            }
    
    def _create_complete_html(self, template_result: Dict[str, Any]) -> str:
        """Create complete HTML with embedded CSS"""
        html_export = template_result.get("html_export", "")
        globals_css = template_result.get("globals_css", "")
        style_css = template_result.get("style_css", "")
        
        # Combine all CSS
        combined_css = f"{globals_css}\n{style_css}"
        
        # Create complete HTML
        complete_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Template</title>
    <style>
{combined_css}
    </style>
</head>
<body>
{html_export}
</body>
</html>"""
        
        return complete_html 