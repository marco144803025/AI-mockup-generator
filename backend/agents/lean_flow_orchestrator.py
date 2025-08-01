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

class LeanFlowOrchestrator:
    """Intelligent orchestrator for the lean UI mockup generation workflow"""
    
    def __init__(self):
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
        
        # Session state
        self.session_state = {
            "current_phase": "initial",
            "conversation_history": [],
            "requirements": {},
            "recommendations": [],
            "questions": {},
            "selected_template": None,
            "modifications": [],
            "report": None,
            "created_at": datetime.now()
        }
        
        # Session ID
        self.session_id = str(uuid.uuid4())
        
        # Phase definitions
        self.phases = ["initial", "requirements", "template_recommendation", "template_selection", "editing", "report_generation"]
    
    def _add_to_conversation_history(self, message: str, role: str):
        """Add message to conversation history"""
        self.session_state["conversation_history"].append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
    
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
        
        # If no template is selected, try to select one from recommendations
        if not selected_template:
            recommendations = self.session_state.get("recommendations", [])
            if recommendations:
                # Auto-select the first/best template
                selected_template = recommendations[0]
                self.session_state["selected_template"] = selected_template
        
        # If still no template, go back to recommendation phase
        if not selected_template:
            self.session_state["current_phase"] = "template_recommendation"
            return await self._handle_recommendation_phase(message, context)
        
        # Use LLM to detect user intent
        user_intent = await self._detect_user_intent(message, "template_selection", context)
        
        if user_intent == "editing":
            # User wants to edit the template
            self.session_state["current_phase"] = "editing"
            return await self._handle_editing_phase(message, context)
        
        elif user_intent == "report":
            # User wants to generate a report
            return await self._handle_report_generation(message, context)
        
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
                "intent": "not_understand"
            }
        
        else:
            # Default: confirm selection and ask for next steps
            response = self.user_proxy_agent.template_selected_confirmation(selected_template)
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "template_selection",
                "selected_template": selected_template
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

1. "editing" - User wants to modify the selected template (e.g., "change the color", "make it more modern", "edit this", "modify")
2. "report" - User wants to generate a report or summary (e.g., "generate report", "create summary", "show me the details")
3. "confirmation" - User is confirming the selection (e.g., "yes", "perfect", "that's good", "proceed")
4. "not_understand" - User's intent is unclear, ambiguous, or cannot be determined
5. "general" - General conversation that doesn't fit other categories

Return ONLY the intent type (e.g., "editing").
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
                valid_intents = ["editing", "report", "confirmation", "not_understand", "general"]
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
- Number references: "1", "first", "option 1"
- Name references: "landing 1", "login template"
- Implicit references: "that one", "this template", "the first option"
- Partial matches: "landing" when there's only one landing template

If the user's selection is unclear, ambiguous, or doesn't match any template, return "unclear".

Return ONLY the template number (1, 2, 3, etc.) or "unclear" if the selection cannot be determined.
"""

            # Call LLM for parsing
            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=False)
            
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
                        return recommendations[template_index].get("template", {})
                
                # Try to match by name
                for rec in recommendations:
                    template = rec.get("template", {})
                    template_name = template.get("name", "").lower()
                    if template_name in selection.lower():
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
                        templates = current_output or self.session_state.get("recommendations", [])
                        requirements = self.session_state.get("requirements", {})
                        result = self.question_agent.generate_questions(templates, requirements)
                        # Standardize the output
                        result = self.question_agent.enhance_agent_output(result, agent_context)
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    except Exception as e:
                        self.logger.error(f"Error in question_generation: {e}")
                        # Create error response
                        result = self.question_agent.create_standardized_response(
                            success=False,
                            data={
                                "primary_result": {"questions": [], "focus_areas": []},
                                "error": str(e),
                                "requires_clarification": True,
                                "clarification_questions": ["Could you please provide more details?"]
                            },
                            metadata={"context_used": agent_context}
                        )
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    
                elif agent_name == "user_proxy":
                    # UserProxyAgent handles response formatting - this should be the final output
                    result = self.user_proxy_agent.create_response_from_instructions(
                        "template recommendations",
                        {
                            "requirements": self.session_state.get("requirements"),
                            "templates": self.session_state.get("recommendations"),
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
        
        return {
            "success": True,
            "message": "Session reset successfully",
            "session_id": self.session_id
        } 