"""
Flow Orchestrator - Coordinates workflow between focused agents
Follows single responsibility principle: Only handles coordination
"""

import logging
import uuid
import re
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import asyncio

from .requirements_analysis_agent import RequirementsAnalysisAgent
from .template_recommendation_agent import TemplateRecommendationAgent
from .question_generation_agent import QuestionGenerationAgent
from .user_proxy_agent import UserProxyAgent
from .ui_editing_agent import UIEditingAgent
from tools.report_generator import ReportGenerator
from config.keyword_config import KeywordManager
from session_manager import session_manager

class FlowOrchestrator:
    """Intelligent orchestrator for the UI mockup generation workflow"""
    def __init__(self, session_id: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        # Initialize agents (except editing_agent which needs session_id)
        self.requirements_agent = RequirementsAnalysisAgent()
        self.recommendation_agent = TemplateRecommendationAgent()
        self.question_agent = QuestionGenerationAgent()
        self.user_proxy_agent = UserProxyAgent()
        self.report_agent = ReportGenerator()
        
        # Initialize keyword manager
        self.keyword_manager = KeywordManager()
        
        # Session management
        if session_id:
            self.session_id = session_id
            # Load existing session
            session_data = session_manager.get_session(session_id)
            if session_data:
                self.session_state = session_data
                print(f"DEBUG ORCHESTRATOR: Loaded existing session {session_id}")
                print(f"DEBUG ORCHESTRATOR: Session state keys: {list(self.session_state.keys())}")
                print(f"DEBUG ORCHESTRATOR: Current phase: {self.session_state.get('current_phase', 'NOT_SET')}")
                print(f"DEBUG ORCHESTRATOR: Session data loaded from manager with {len(session_data.keys())} keys")
            else:
                # Create new session if not found
                self.session_id = session_manager.create_session()
                self.session_state = session_manager.get_session(self.session_id)
                print(f"DEBUG ORCHESTRATOR: Created new session {self.session_id} (existing not found)")
                print(f"DEBUG ORCHESTRATOR: New session state created with {len(self.session_state.keys())} keys")
        else:
            # Create new session
            self.session_id = session_manager.create_session()
            self.session_state = session_manager.get_session(self.session_id)
            print(f"DEBUG ORCHESTRATOR: Created new session {self.session_id} (no session_id provided)")
        
        # Ensure current_phase is set
        if 'current_phase' not in self.session_state:
            self.session_state['current_phase'] = 'initial'
            print(f"DEBUG ORCHESTRATOR: Set default current_phase to 'initial'")
        
        # Initialize editing_agent after session_id is set
        self.editing_agent = UIEditingAgent(session_id=self.session_id)
        
        # Phase definitions
        self.phases = ["initial", "requirements", "template_recommendation", "template_selection", "editing", "report_generation"]
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Claude response, handling different content types"""
        if not response.content:
            return ""
        
        # Look for text content in any of the content blocks
        for content in response.content:
            # Handle text content
            if hasattr(content, 'text') and content.text:
                return content.text
        
        # If no text found, handle tool use blocks
        content = response.content[0]
        
        # Handle tool use blocks
        if hasattr(content, 'type') and content.type == 'tool_use':
            # Extract text from tool use block if available
            if hasattr(content, 'input') and content.input:
                return str(content.input)
            elif hasattr(content, 'name'):
                return f"Tool used: {content.name}"
            else:
                return "Tool used"
        
        # Handle other content types
        if hasattr(content, 'type'):
            return f"Content type: {content.type}"
        
        # Fallback
        return str(content)
    
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
            
            # Step 1: Check if this is a UI modification request regardless of current phase
            if await self._is_ui_modification_request(message):
                self.logger.info("Detected UI modification request, forcing editing phase")
                # If we have a selected template or UI codes, switch to editing phase
                if self.session_state.get("selected_template") or context and context.get("ui_codes"):
                    self.session_state["current_phase"] = "editing"
                    if context and context.get("ui_codes"):
                        # Set up editing context from UI codes
                        self.session_state["selected_template"] = context["ui_codes"].get("template_info", {})
                        self.session_state["ui_codes"] = context["ui_codes"]
                    return await self._handle_editing_phase(message, context)
            
            # Step 2: Determine current phase and execute appropriate workflow
            current_phase = self.session_state["current_phase"]
            
            # Only detect initial intent if we're in initial or unknown phase
            initial_intent = None
            if current_phase in ["initial", "unknown"]:
                initial_intent = await self._detect_initial_intent(message, context)
                print(f"DEBUG: Detected initial intent: {initial_intent}")
            else:
                print(f"DEBUG: Skipping initial intent detection for phase: {current_phase}")
                
            print(f"DEBUG: Current phase: {current_phase}")
            print(f"DEBUG: Session state keys: {list(self.session_state.keys())}")
            
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
            # Report generation is now handled directly by the main API
                return {
                    "success": False,
                    "response": "Report generation is handled through the dedicated report API endpoint.",
                    "session_id": self.session_id,
                    "phase": "report_generation"
                }
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
    
    async def _is_ui_modification_request(self, message: str) -> bool:
        """
        Quick detection of UI modification requests to bypass phase requirements.
        This allows users to make modifications even if they haven't gone through the full workflow.
        """
        try:
            # First, check for completion/report generation requests that should NOT be treated as modifications
            completion_patterns = [
                r'generate.*report', r'create.*report', r'show.*final', r'i.*done',
                r'that.*perfect', r'finished', r'complete', r'finalize', r'generate.*summary', r'create.*summary'
            ]
            
            import re
            message_lower = message.lower()
            
            # Check for completion requests first
            for pattern in completion_patterns:
                if re.search(pattern, message_lower):
                    self.logger.debug(f"Completion request detected with pattern: {pattern}, NOT treating as UI modification")
                    return False
            
            modification_patterns = [
                # Color changes
                r'change.*color', r'make.*color', r'background.*color', r'text.*color',
                r'color.*to', r'make.*blue', r'make.*green', r'make.*red',
                
                # Size and dimension changes  
                r'increase.*height', r'decrease.*height', r'make.*bigger', r'make.*smaller',
                r'increase.*width', r'decrease.*width', r'make.*larger', r'make.*taller',
                r'resize', r'size',
                
                # Style changes
                r'add.*padding', r'remove.*padding', r'add.*margin', r'change.*font',
                r'make.*bold', r'make.*italic', r'change.*style',
                
                # Layout changes  
                r'move.*', r'position.*', r'align.*', r'center.*',
                
                # General modification verbs (more specific to avoid false positives)
                r'change.*(color|size|font|style|layout|position)', r'modify.*', r'update.*', r'edit.*', r'adjust.*',
                r'fix.*', r'improve.*', r'alter.*'
            ]
            
            for pattern in modification_patterns:
                if re.search(pattern, message_lower):
                    self.logger.debug(f"UI modification detected with pattern: {pattern}")
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting UI modification request: {e}")
            return False
    
    async def _handle_initial_intent_phase(self, message: str, initial_intent: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the initial intent detection phase"""
        
        print(f"DEBUG: Entering _handle_initial_intent_phase with intent: {initial_intent}")
        
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
            print(f"DEBUG: Transitioning to requirements phase with enhanced_context: {enhanced_context}")
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
        
        phase_start_time = time.time()
        print(f"DEBUG: Starting requirements phase execution...")
        
        # Step 1: Analyze what agents are needed
        phase_decision = await self._analyze_phase_requirements(message, context)
        print(f"DEBUG: Phase decision for requirements phase: {phase_decision}")
        
        # Step 2: Update session state with context updates
        if phase_decision.get("context_updates"):
            self.session_state.update(phase_decision["context_updates"])
        
        # Step 3: Execute required agents in order
        print(f"DEBUG: Required agents for pipeline: {phase_decision['required_agents']}")
        pipeline_start_time = time.time()
        pipeline_result = self._execute_agent_pipeline(
            phase_decision["required_agents"], 
            message, 
            context or {}
        )
        pipeline_end_time = time.time()
        print(f"DEBUG: Agent pipeline completed in {pipeline_end_time - pipeline_start_time:.2f} seconds")
        print(f"DEBUG: Pipeline result success: {pipeline_result['success']}")
        print(f"DEBUG: Pipeline result keys: {pipeline_result.keys()}")
        print(f"DEBUG: Pipeline final_output: {pipeline_result.get('final_output', 'None')}")
        
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
            
            # Store template recommendation rationale
            try:
                from utils.rationale_manager import RationaleManager
                rationale_manager = RationaleManager(self.session_id)
                recommendations = self.session_state["recommendations"]
                rationale_manager.add_template_recommendation_rationale(recommendations)
                self.logger.info("Stored template recommendation rationale")
            except Exception as e:
                self.logger.error(f"Failed to store template recommendation rationale: {e}")
            
            # Check if we have only one template - if so, skip question generation
            recommendations = self.session_state["recommendations"]
            if isinstance(recommendations, list) and len(recommendations) == 1:
                self.logger.info(f"Only one template found ({recommendations[0].get('template', {}).get('name', 'Unknown')}), skipping question generation")
                # Remove question_generation from agent_results if it exists
                if "question_generation" in agent_results:
                    del agent_results["question_generation"]
                # Update session state to indicate no questions needed
                self.session_state["questions"] = {"questions": [], "reasoning": "Single template found, no questions needed"}
        
        if "question_generation" in agent_results:
            # Extract primary_result from standardized response
            questions_result = agent_results["question_generation"]
            if isinstance(questions_result, dict) and "data" in questions_result:
                self.session_state["questions"] = questions_result["data"]["primary_result"]
            else:
                self.session_state["questions"] = questions_result
        
        # Step 5: Get final response from user proxy
        final_output = pipeline_result["final_output"]
        
        # Use UserProxyAgent to create a proper response
        if isinstance(final_output, dict):
            # Check if we have only one template and should present it directly
            recommendations = self.session_state.get("recommendations", [])
            if isinstance(recommendations, list) and len(recommendations) == 1:
                # Present the single template directly
                response = self.user_proxy_agent.create_response_from_instructions(
                    "present_single_template",
                    {
                        "template": recommendations[0],
                        "requirements_data": final_output,
                        "session_state": self.session_state
                    }
                )
            elif "questions_for_clarification" in final_output and final_output.get("questions_for_clarification"):
                response = self.user_proxy_agent.create_response_from_instructions(
                    "clarification_needed",
                    {
                        "clarification_questions": final_output.get("questions_for_clarification", []),
                        "requirements_data": final_output,
                        "session_state": self.session_state
                    }
                )
            else:
                # Use requirements analysis result to create a proper response
                response = self.user_proxy_agent.create_response_from_instructions(
                    "requirements_analysis_complete",
                    {
                        "requirements_data": final_output,
                        "session_state": self.session_state
                    }
                )
        else:
            # Fallback for non-dict output
            response = str(final_output) if final_output else "I've processed your request. Let me know how you'd like to proceed."
        
        # Step 6: Update phase based on decision
        next_phase = phase_decision.get("next_phase", "template_recommendation")
        self.session_state["current_phase"] = next_phase
        
        self._add_to_conversation_history(response, "assistant")
        
        # Log total phase execution time
        phase_end_time = time.time()
        print(f"DEBUG: Requirements phase total execution time: {phase_end_time - phase_start_time:.2f} seconds")
        
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
                
                # Store final template selection rationale
                try:
                    from utils.rationale_manager import RationaleManager
                    rationale_manager = RationaleManager(self.session_id)
                    rationale_manager.add_template_recommendation_rationale(
                        self.session_state["recommendations"], 
                        selected_template
                    )
                    self.logger.info("Stored final template selection rationale")
                except Exception as e:
                    self.logger.error(f"Failed to store final template selection rationale: {e}")
                
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
        
        self.logger.info(f"Selection phase - Message: '{message}', Recommendations count: {len(recommendations)}")
        self.logger.info(f"Available recommendations: {[rec.get('template', {}).get('name', 'Unknown') for rec in recommendations]}")
        
        # Check if user is selecting a template
        if not selected_template and recommendations:
            # Try to detect template selection from user message
            self.logger.info(f"Attempting to parse template selection from message: '{message}'")
            selected_template = await self._parse_template_selection_llm(message, recommendations)
            
            self.logger.info(f"Template selection result: {selected_template.get('name', 'Unknown') if selected_template else 'None'}")
            
            if selected_template:
                self.session_state["selected_template"] = selected_template
                # Store in global session manager
                session_manager.set_selected_template(self.session_id, selected_template)
                self.logger.info(f"Template selected: {selected_template.get('name', 'Unknown')}")
                
                # Immediately trigger Phase 2 transition when template is first selected
                self.logger.info("Triggering immediate phase transition...")
                return await self._handle_phase_transition(selected_template)
            else:
                self.logger.warning(f"Failed to parse template selection from message: '{message}'")
        
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
            self.logger.warning("No template selected, going back to recommendation phase")
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
            # User wants to generate a report - redirect to dedicated API
            return {
                "success": True,
                "response": "To generate a report, please use the dedicated report generation feature in the UI.",
                "session_id": self.session_id,
                "phase": "template_selection",
                "intent": "report_request"
            }
        
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
        """Handle template editing phase with enhanced intent detection and coordination"""
        
        selected_template = self.session_state.get("selected_template")
        if not selected_template:
            return {
                "success": False,
                "response": "No template selected for editing. Please select a template first.",
                "session_id": self.session_id,
                "phase": "editing"
            }
        
        # Step 1: Check for pending clarification response
        pending_clarification = self.session_state.get("pending_clarification")
        if pending_clarification:
            print(f"DEBUG ORCHESTRATOR: Found pending clarification, handling user response")
            return await self._handle_editing_clarification_user_response(message, selected_template, context)
        
        # Step 2: Enhanced intent detection for editing phase
        editing_intent = await self._detect_editing_intent_advanced(message, selected_template)
        
        # Step 3: Route based on intent
        if editing_intent == "modification_request":
            return await self._handle_editing_modification_request(message, selected_template, context)
        elif editing_intent == "clarification_request":
            return await self._handle_editing_clarification_request(message, selected_template, context)
        elif editing_intent == "completion_request":
            return await self._handle_editing_completion_request(message, selected_template, context)
        elif editing_intent == "preview_request":
            return await self._handle_editing_preview_request(message, selected_template, context)
        else:
            return await self._handle_editing_general_request(message, selected_template, context)
    
    async def _detect_editing_intent_advanced(self, message: str, selected_template: Dict[str, Any]) -> str:
        """Enhanced intent detection specifically for editing phase using LLM"""
        try:
            template_name = selected_template.get("name", "Unknown Template")
            
            prompt = f"""
You are an advanced intent detection system for the UI editing phase.

Current template: {template_name}
User message: "{message}"

Analyze the user's intent and classify it as one of the following:

1. "modification_request" - User wants to make specific changes to the UI:
   - Text changes: "change the text", "change Home to homepage", "update text", "modify text"
   - Layout changes: "make wider", "resize", "change position", "adjust width", "prevent wrapping"
   - Color changes: "change the color", "make it blue", "red background"
   - Style changes: "make it modern", "change font", "add shadow"
   - Content changes: "add button", "remove element", "edit", "modify", "update"
   - Specific modifications: Any request that starts with "change", "make", "adjust", "modify", "update"

2. "clarification_request" - User wants to understand what can be changed:
   - "what can I change?", "what options do I have?", "help"
   - "show me what I can modify", "what's possible?"
   - "suggestions", "recommendations"

3. "preview_request" - User wants to see the current state:
   - "show me the preview", "how does it look?", "view current"
   - "see the result", "show me what I have"

4. "completion_request" - User is done editing:
   - "I'm done", "finished", "complete", "that's perfect"
   - "generate report", "create summary", "finalize"

5. "general_request" - General conversation or unclear intent:
   - Greetings, questions about the system, unclear requests

Return ONLY the intent type (e.g., "modification_request").

**EXAMPLES:**
- "Change the text Home to homepage" → modification_request
- "Make the section wider" → modification_request  
- "Adjust the width so it doesn't wrap" → modification_request
- "Change the color to blue" → modification_request
- "What can I change?" → clarification_request
- "Show me the preview" → preview_request
- "I'm done" → completion_request
- "Hello" → general_request
"""
            
            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=False)
            intent = response.strip().lower()
            
            print(f"DEBUG ORCHESTRATOR: Intent detection response: '{response}'")
            print(f"DEBUG ORCHESTRATOR: Parsed intent: '{intent}'")
            
            valid_intents = ["modification_request", "clarification_request", "preview_request", "completion_request", "general_request"]
            final_intent = intent if intent in valid_intents else "general_request"
            print(f"DEBUG ORCHESTRATOR: Final intent: '{final_intent}'")
            
            return final_intent
            
        except Exception as e:
            self.logger.error(f"Error in advanced editing intent detection: {e}")
            return "general_request"
    
    async def _handle_editing_modification_request(self, message: str, selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle specific modification requests with enhanced coordination"""
        try:
            print(f"DEBUG ORCHESTRATOR: _handle_editing_modification_request called with message: {message}")
            
            # Step 1: Get current UI state
            current_ui_state = await self._get_current_ui_state(selected_template)
            print(f"DEBUG ORCHESTRATOR: Current UI state loaded, HTML length: {len(current_ui_state.get('html_export', ''))}")
            print(f"DEBUG ORCHESTRATOR: Current UI state CSS length: {len(current_ui_state.get('style_css', ''))}")
            print(f"DEBUG ORCHESTRATOR: Current UI state keys: {list(current_ui_state.keys())}")
            
            # Step 2: Use UI editing agent to analyze and apply modifications
            print(f"DEBUG ORCHESTRATOR: Calling UI editing agent...")
            modification_result = self.editing_agent.process_modification_request(message, current_ui_state)
            print(f"DEBUG ORCHESTRATOR: UI editing agent returned: {bool(modification_result)}")
            if modification_result:
                print(f"DEBUG ORCHESTRATOR: Modification success: {modification_result.get('success', False)}")
                print(f"DEBUG ORCHESTRATOR: Has modified_template: {bool(modification_result.get('modified_template'))}")
                print(f"DEBUG ORCHESTRATOR: Clarification needed: {modification_result.get('clarification_needed', False)}")
            
            # Step 3: Check for clarification needed state
            if modification_result.get("clarification_needed", False):
                print(f"DEBUG ORCHESTRATOR: Clarification needed detected, handling clarification request")
                return await self._handle_editing_clarification_response(modification_result, selected_template, context)
            
            if not modification_result.get("success", False):
                # Handle modification failure
                response = self.user_proxy_agent.create_response_from_instructions(
                    "modification_error",
                    {
                        "error": modification_result.get("error", "Unknown error"),
                        "user_message": message,
                        "template": selected_template
                    }
                )
            else:
                # Step 4: Update session state with modifications
                modified_template = modification_result.get("modified_template", selected_template)
                self.session_state["modified_template"] = modified_template
                
                # Step 4.5: Prepare complete template data for saving
                complete_template_data = {
                    "html_export": modified_template.get("html_export", ""),
                    "style_css": modified_template.get("style_css", ""),
                    "globals_css": modified_template.get("globals_css", ""),
                    "template_id": selected_template.get("template_id", ""),
                    "template_name": selected_template.get("name", ""),
                    "template_category": selected_template.get("category", ""),
                    "modification_metadata": {
                        "user_request": message,
                        "modification_type": "ui_agent",
                        "changes_applied": modification_result.get("changes_summary", ["UI modifications applied"])
                    }
                }
                
                print(f"DEBUG ORCHESTRATOR: Prepared template data for saving - HTML length: {len(complete_template_data.get('html_export', ''))}")
                print(f"DEBUG ORCHESTRATOR: Template data keys: {list(complete_template_data.keys())}")
                
                # Save the modified template back to the temp_ui_files JSON file
                await self._save_modified_template_to_file(complete_template_data)
                
                # Step 5: Generate user response
                response = self.user_proxy_agent.create_response_from_instructions(
                    "modification_success",
                    {
                        "modification_result": modification_result,
                        "selected_template": selected_template,
                        "changes_summary": modification_result.get("changes_summary", [])
                    }
                )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "editing",
                "modification_result": modification_result,
                "intent": "modification_request"
            }
            
        except Exception as e:
            self.logger.error(f"Error handling editing modification request: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error while processing your modification request: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }
    
    async def _handle_editing_clarification_response(self, modification_result: Dict[str, Any], selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle clarification responses from the UI editing agent"""
        try:
            print(f"DEBUG ORCHESTRATOR: Handling clarification response")
            
            # Extract clarification information
            clarification_options = modification_result.get("clarification_options", [])
            error_message = modification_result.get("error", "Multiple possible targets found")
            
            # Store clarification context in session for later processing
            self.session_state["pending_clarification"] = {
                "original_request": modification_result.get("user_feedback", ""),
                "clarification_options": clarification_options,
                "original_template": modification_result.get("original_template", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate clarification response
            response = self.user_proxy_agent.create_response_from_instructions({
                "type": "editing_clarification_needed",
                "error_message": error_message,
                "clarification_options": clarification_options,
                "template": selected_template,
                "original_request": modification_result.get("user_feedback", "")
            })
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "editing",
                "intent": "clarification_needed",
                "clarification_options": clarification_options,
                "pending_clarification": True
            }
            
        except Exception as e:
            self.logger.error(f"Error handling editing clarification response: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error while processing the clarification: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }
    
    async def _handle_editing_clarification_user_response(self, message: str, selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle user response to clarification request"""
        try:
            print(f"DEBUG ORCHESTRATOR: Handling user clarification response: {message}")
            
            # Get pending clarification context
            pending_clarification = self.session_state.get("pending_clarification", {})
            clarification_options = pending_clarification.get("clarification_options", [])
            original_request = pending_clarification.get("original_request", "")
            original_template = pending_clarification.get("original_template", {})
            
            # Parse user's choice from the clarification options
            user_choice = self._parse_user_clarification_choice(message, clarification_options)
            
            if user_choice is None:
                # User didn't provide a clear choice, ask again
                response = self.user_proxy_agent.create_response_from_instructions({
                    "type": "editing_clarification_invalid_choice",
                    "clarification_options": clarification_options,
                    "user_message": message,
                    "template": selected_template,
                    "original_request": original_request
                })
                
                self._add_to_conversation_history(response, "assistant")
                
                return {
                    "success": True,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "editing",
                    "intent": "clarification_invalid_choice",
                    "pending_clarification": True
                }
            
            # Clear pending clarification
            self.session_state.pop("pending_clarification", None)
            
            # Create a refined request with the user's choice
            refined_request = f"{original_request} (targeting: {user_choice})"
            
            # Process the refined modification request
            print(f"DEBUG ORCHESTRATOR: Processing refined request: {refined_request}")
            
            # Get current UI state
            current_ui_state = await self._get_current_ui_state(selected_template)
            
            # Use UI editing agent with the refined request
            modification_result = self.editing_agent.process_modification_request(refined_request, current_ui_state)
            
            if modification_result.get("clarification_needed", False):
                # Still needs clarification, handle again
                return await self._handle_editing_clarification_response(modification_result, selected_template, context)
            
            if not modification_result.get("success", False):
                # Handle modification failure
                response = self.user_proxy_agent.create_response_from_instructions(
                    "modification_error",
                    {
                        "error": modification_result.get("error", "Unknown error"),
                        "user_message": refined_request,
                        "template": selected_template
                    }
                )
            else:
                # Update session state with modifications
                modified_template = modification_result.get("modified_template", selected_template)
                self.session_state["modified_template"] = modified_template
                
                # Save the modified template back to the temp_ui_files JSON file
                await self._save_modified_template_to_file(modified_template)
                
                # Generate success response
                response = self.user_proxy_agent.create_response_from_instructions(
                    "modification_success",
                    {
                        "modification_result": modification_result,
                        "selected_template": selected_template,
                        "changes_summary": modification_result.get("changes_summary", [])
                    }
                )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "editing",
                "modification_result": modification_result,
                "intent": "modification_request"
            }
            
        except Exception as e:
            self.logger.error(f"Error handling editing clarification user response: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error while processing your clarification: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }
    
    def _parse_user_clarification_choice(self, message: str, clarification_options: List[Dict[str, Any]]) -> Optional[str]:
        """Parse user's choice from clarification options"""
        try:
            message_lower = message.lower().strip()
            
            # Try to match by option number (1, 2, 3, etc.)
            for i, option in enumerate(clarification_options, 1):
                if str(i) in message_lower or f"option {i}" in message_lower:
                    return option.get("text_content", f"Option {i}")
            
            # Try to match by text content
            for option in clarification_options:
                text_content = option.get("text_content", "").lower()
                if text_content and text_content in message_lower:
                    return option.get("text_content", "")
            
            # Try to match by CSS selector
            for option in clarification_options:
                css_selector = option.get("css_selector", "").lower()
                if css_selector and css_selector in message_lower:
                    return option.get("text_content", "")
            
            # Try to match by description
            for option in clarification_options:
                description = option.get("description", "").lower()
                if description and description in message_lower:
                    return option.get("text_content", "")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing user clarification choice: {e}")
            return None
    
    async def _handle_editing_clarification_request(self, message: str, selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle clarification requests about what can be modified"""
        try:
            # Generate editing suggestions based on current template
            suggestions = self._generate_editing_suggestions_advanced(selected_template)
            
            response = self.user_proxy_agent.create_response_from_instructions(
                "editing_clarification",
                {
                    "suggestions": suggestions,
                    "template": selected_template,
                    "user_message": message
                }
            )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "editing",
                "intent": "clarification_request"
            }
            
        except Exception as e:
            self.logger.error(f"Error handling editing clarification request: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }
    
    async def _handle_editing_preview_request(self, message: str, selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle preview requests to show current state"""
        try:
            # Generate UI preview
            current_ui_state = await self._get_current_ui_state(selected_template)
            
            response = self.user_proxy_agent.create_response_from_instructions(
                "editing_preview",
                {
                    "current_ui_state": current_ui_state,
                    "template": selected_template,
                    "modifications": self.session_state.get("modifications", {})
                }
            )
            
            self._add_to_conversation_history(response, "assistant")
            
            return {
                "success": True,
                "response": response,
                "session_id": self.session_id,
                "phase": "editing",
                "intent": "preview_request"
            }
            
        except Exception as e:
            self.logger.error(f"Error handling editing preview request: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }
    
    async def _handle_editing_completion_request(self, message: str, selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle completion requests to finish editing"""
        try:
            # Transition to report generation phase
            self.session_state["current_phase"] = "report_generation"
            
            # Report generation is now handled by the dedicated API
            return {
                "success": True,
                "response": "Editing completed! To generate a report, please use the dedicated report generation feature in the UI.",
                "session_id": self.session_id,
                "phase": "editing",
                "intent": "completion_request",
                "phase_transition": True,
                "report_generated": False,
                "note": "Use the report generation feature in the UI"
            }
            
            if report_result.get("success", False):
                # Report was generated successfully
                response = f"Report generated successfully! Your project report is ready for download."
                
                result = {
                    "success": True,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "report_generation",
                    "intent": "completion_request",
                    "phase_transition": True,
                    "report_generated": True,
                    "report_file": report_result.get("report_file"),
                    "report_metadata": report_result.get("metadata", {})
                }
                
                return result
            else:
                # Report generation failed
                response = f"Sorry, I encountered an error while generating the report: {report_result.get('response', 'Unknown error')}"
                
                return {
                    "success": False,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "editing",
                    "intent": "completion_request",
                    "report_generated": False
                }
            
        except Exception as e:
            self.logger.error(f"Error handling editing completion request: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }
    
    async def _handle_editing_general_request(self, message: str, selected_template: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle general requests during editing phase using LLM for intelligent responses"""
        try:
            # For general questions, use the LLM to generate a helpful response
            try:
                # Get current UI state for context
                current_ui_state = await self._get_current_ui_state(selected_template)
                
                # Generate LLM response
                response = self._generate_llm_response_for_general_question(message, self.session_id, current_ui_state)
                
                self._add_to_conversation_history(response, "assistant")
                
                return {
                    "success": True,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "editing",
                    "intent": "general_request",
                    "response_type": "llm_generated"
                }
                
            except Exception as llm_error:
                self.logger.warning(f"LLM response generation failed, falling back to User Proxy Agent: {llm_error}")
                
                # Fallback to User Proxy Agent
                response = self.user_proxy_agent.create_response_from_instructions(
                    "editing_general",
                    {
                        "user_message": message,
                        "template": selected_template,
                        "available_actions": ["modify", "preview", "clarify", "complete"]
                    }
                )
                
                self._add_to_conversation_history(response, "assistant")
                
                return {
                    "success": True,
                    "response": response,
                    "session_id": self.session_id,
                    "phase": "editing",
                    "intent": "general_request",
                    "response_type": "fallback"
                }
            
        except Exception as e:
            self.logger.error(f"Error handling editing general request: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": self.session_id,
                "phase": "editing"
            }


    async def _get_current_ui_state(self, selected_template: Dict[str, Any]) -> Dict[str, Any]:
        """Get current UI state including any modifications"""
        try:
            print(f"DEBUG ORCHESTRATOR: Getting current UI state for session {self.session_id}")
            
            # Step 1: Always try to load from session files first (this contains the current state)
            print(f"DEBUG ORCHESTRATOR: Step 1 - Loading from session files for session: {self.session_id}")
            session_ui_state = await self._load_ui_state_from_session()
            if session_ui_state and session_ui_state.get("html_export"):
                print(f"DEBUG ORCHESTRATOR: Using session UI state - HTML length: {len(session_ui_state.get('html_export', ''))}")
                print(f"DEBUG ORCHESTRATOR: Session UI state CSS length: {len(session_ui_state.get('style_css', ''))}")
                
                # Check if the target text is in the session content
                html_content = session_ui_state.get("html_export", "")
                if "Welcome back!" in html_content or "Glad you're back!" in html_content:
                    print(f"DEBUG ORCHESTRATOR: Found welcome text in session HTML")
                else:
                    print(f"DEBUG ORCHESTRATOR: Welcome text NOT found in session HTML")
                
                return session_ui_state
            else:
                print(f"DEBUG ORCHESTRATOR: No session UI state loaded, falling back to MongoDB template")
            
            # Step 2: Fallback to MongoDB template if no session file exists
            print(f"DEBUG ORCHESTRATOR: No session file found, using MongoDB template")
            ui_state = {
                "template_id": selected_template.get("_id"),
                "template_name": selected_template.get("name"),
                "html_export": selected_template.get("html_export", ""),
                "style_css": selected_template.get("style_css", ""),
                "globals_css": selected_template.get("globals_css", "")
            }
            
            # Add debug logging to verify template content
            print(f"DEBUG TEMPLATE: Template name: {selected_template.get('name')}")
            print(f"DEBUG TEMPLATE: Template ID: {selected_template.get('_id')}")
            print(f"DEBUG TEMPLATE: HTML length: {len(selected_template.get('html_export', ''))}")
            print(f"DEBUG TEMPLATE: CSS length: {len(selected_template.get('style_css', ''))}")
            
            # Check if the target text is in the template
            if "Welcome back!" in selected_template.get("html_export", ""):
                print(f"DEBUG TEMPLATE: Found 'Welcome back!' in template HTML")
            else:
                print(f"DEBUG TEMPLATE: 'Welcome back!' NOT found in template HTML")
            
            # Apply any pending modifications to the complete template
            modifications = self.session_state.get("modifications", {})
            if modifications:
                ui_state["pending_modifications"] = modifications
            
            self.logger.info(f"Using MongoDB template - HTML: {len(ui_state.get('html_export', ''))}, CSS: {len(ui_state.get('style_css', ''))}")
            return ui_state
            
        except Exception as e:
            self.logger.error(f"Error getting current UI state: {e}")
            return {}
    


    async def _load_ui_state_from_session(self) -> Optional[Dict[str, Any]]:
        """Load UI state from the session using file manager"""
        try:
            from utils.file_manager import UICodeFileManager
            import os
            
            # Initialize file manager with absolute path to match main.py
            base_dir = os.path.join(os.getcwd(), "temp_ui_files")
            file_manager = UICodeFileManager(base_dir=base_dir)
            
            print(f"DEBUG ORCHESTRATOR: Loading UI state for session: {self.session_id}")
            
            # Check if session exists in new file-based format
            if file_manager.session_exists(self.session_id):
                print(f"DEBUG ORCHESTRATOR: Session {self.session_id} exists, loading data...")
                session_data = file_manager.load_session(self.session_id)
                if session_data and session_data.get("current_codes", {}).get("html_export"):
                    current_codes = session_data["current_codes"]
                    html_length = len(current_codes.get('html_export', ''))
                    css_length = len(current_codes.get('style_css', ''))
                    print(f"DEBUG ORCHESTRATOR: Loaded session data - HTML: {html_length}, CSS: {css_length}")
                    
                    # Check if the target text is in the loaded content
                    html_content = current_codes.get('html_export', '')
                    if "Glad you're back!" in html_content:
                        print(f"DEBUG ORCHESTRATOR: Found 'Glad you're back!' in session HTML")
                    elif "Welcome back!" in html_content:
                        print(f"DEBUG ORCHESTRATOR: Found 'Welcome back!' in session HTML")
                    else:
                        print(f"DEBUG ORCHESTRATOR: No welcome text found in session HTML")
                    
                    self.logger.info(f"Loaded UI codes from file-based session {self.session_id} with HTML length: {html_length}")
                    return {
                        "html_export": current_codes.get("html_export", ""),
                        "style_css": current_codes.get("style_css", ""),
                        "globals_css": current_codes.get("globals_css", ""),
                        "template_info": session_data.get("template_info", {}),
                        "session_file": f"temp_ui_files/{self.session_id}/"
                    }
                else:
                    print(f"DEBUG ORCHESTRATOR: Session data is empty or invalid")
            else:
                print(f"DEBUG ORCHESTRATOR: Session {self.session_id} does not exist")
            
            # Fallback: Check for old JSON format and migrate
            from pathlib import Path
            import json
            
            temp_dir = Path("temp_ui_files")
            
            # Try multiple session file patterns, prioritizing test_session
            session_patterns = [
                f"ui_codes_{self.session_id}.json",
                "ui_codes_test_session.json",  # Fallback for debugging
                "ui_codes_demo_session.json"   # Another fallback
            ]
            
            for pattern in session_patterns:
                session_file = temp_dir / pattern
                if session_file.exists():
                    try:
                        # Migrate from old JSON format to new file-based format
                        success = file_manager.migrate_from_json(self.session_id, str(session_file))
                        if success:
                            # Retry loading the migrated session
                            session_data = file_manager.load_session(self.session_id)
                            if session_data and session_data.get("current_codes", {}).get("html_export"):
                                current_codes = session_data["current_codes"]
                                self.logger.info(f"Migrated and loaded UI codes from {pattern} with HTML length: {len(current_codes.get('html_export', ''))}")
                                return {
                                    "html_export": current_codes.get("html_export", ""),
                                    "style_css": current_codes.get("style_css", ""),
                                    "globals_css": current_codes.get("globals_css", ""),
                                    "template_info": session_data.get("template_info", {}),
                                    "session_file": f"temp_ui_files/{self.session_id}/"
                                }
                    except Exception as e:
                        self.logger.warning(f"Failed to migrate session file {pattern}: {e}")
                        continue
            
            self.logger.warning("No valid session file found with UI codes")
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading UI state from session: {e}")
            return None
    
    def _generate_editing_suggestions_advanced(self, selected_template: Dict[str, Any]) -> List[str]:
        """Generate advanced editing suggestions based on template analysis"""
        try:
            suggestions = []
            
            # Analyze template structure
            html_content = selected_template.get("html_export", "")
            css_content = selected_template.get("style_css", "") + "\n" + selected_template.get("global_css", "")
            
            # Color-related suggestions
            if "background" in css_content.lower() or "color" in css_content.lower():
                suggestions.extend([
                    "Change the color scheme (e.g., 'make it blue', 'use a dark theme')",
                    "Modify background colors or gradients",
                    "Adjust text colors for better contrast"
                ])
            
            # Layout-related suggestions
            if "flex" in css_content.lower() or "grid" in css_content.lower():
                suggestions.extend([
                    "Adjust the layout spacing and alignment",
                    "Modify element positioning and sizing",
                    "Change the responsive behavior"
                ])
            
            # Typography suggestions
            if "font" in css_content.lower():
                suggestions.extend([
                    "Change the font family or size",
                    "Adjust text styling and weights",
                    "Modify heading styles"
                ])
            
            # Interactive elements
            if "button" in html_content.lower() or "input" in html_content.lower():
                suggestions.extend([
                    "Modify button styles and interactions",
                    "Change form element appearances",
                    "Adjust hover and focus effects"
                ])
            
            # General suggestions
            suggestions.extend([
                "Add or remove elements from the layout",
                "Modify the overall design style",
                "Adjust spacing and padding throughout",
                "Change the visual hierarchy"
            ])
            
            return suggestions[:8]  # Limit to top 8 suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating editing suggestions: {e}")
            return [
                "Change colors and styling",
                "Modify layout and positioning", 
                "Adjust typography and text",
                "Add or remove elements"
            ]
    

    
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

CRITICAL DISTINCTION: 
- If the user is providing information about their preferences, company, style, features, or answering any design-related questions → "question_answer"
- If the user is explicitly choosing a specific numbered template (with clear template references) → "template_selection"

QUESTION ANSWER EXAMPLES:
- "My company is tech-focused" → question_answer (describing company context)
- "I prefer modern design" → question_answer (style preference)
- "We need professional look" → question_answer (design preference)
- "Dark theme would be better" → question_answer (color preference)
- "Yes, that sounds good" → question_answer (preference confirmation)
- "More cutting-edge feeling" → question_answer (design direction)

TEMPLATE SELECTION EXAMPLES:
- "I choose template 1" → template_selection (explicit template choice)
- "Let's go with option 2" → template_selection (explicit option choice)
- "Template number 3 looks good" → template_selection (explicit template reference)

Determine the user's intent from this message. Choose from:

1. "question_answer" - User is providing preferences, requirements, or answering design questions (e.g., "I need modern style", "my company is tech-focused", "professional look", "dark design")
2. "template_selection" - User is explicitly selecting a numbered template or option (e.g., "I choose template 1", "option 2", "template number 3")
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
            self.logger.info(f"Template list for LLM: {len(template_list)} templates")
            
            prompt = f"""
You are a template selection parser for a UI mockup system.

User message: "{message}"

Available templates:
{template_info}

Parse which template the user is selecting. Consider:
- Number references: "1", "first", "option 1", "template 1"
- Ordinal references: "third one", "second option", "first template", "last one"
- Name references: "landing 1", "login template", "profile 1"
- Implicit references: "that one", "this template", "the first option"
- Partial matches: "landing" when there's only one landing template, "profile 1" for Profile 1

**CRITICAL**: If there's only one template available and the user's message could reasonably refer to it, select that template.

**EXAMPLES**:
- "i choose landing 1" with only "Landing 1" available → return "1"
- "i choose it" with only one template → return "1"
- "landing 1" with only "Landing 1" available → return "1"
- "the first one" with only one template → return "1"
- "that template" with only one template → return "1"

If the user's selection is truly unclear, ambiguous, or doesn't match any template, return "unclear".

Return ONLY the template number (1, 2, 3, etc.) or "unclear" if the selection cannot be determined.
"""

            # Call LLM for parsing
            self.logger.info(f"Calling LLM for template selection parsing")
            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=False)
            
            self.logger.info(f"LLM response for template selection: '{response[:100]}{'...' if len(response) > 100 else ''}'")
            
            # Parse response
            try:
                selection = response.strip().lower()
                self.logger.info(f"Parsed selection: '{selection}'")
                
                # Check if selection is unclear (use simple string check instead of hardcoded list)
                if selection == "unclear" or selection == "unclear_responses":
                    self.logger.info(f"LLM could not parse template selection from: '{message}'")
                    return None
                
                # Try to extract number
                number_match = re.search(r'\d+', selection)
                if number_match:
                    template_index = int(number_match.group()) - 1
                    self.logger.info(f"Extracted number: {number_match.group()}, template_index: {template_index}")
                    if 0 <= template_index < len(recommendations):
                        selected_template = recommendations[template_index].get("template", {})
                        self.logger.info(f"Selected template {template_index + 1}: {selected_template.get('name', 'Unknown')}")
                        return selected_template
                    else:
                        self.logger.warning(f"Template index {template_index} out of range (0-{len(recommendations)-1})")
                
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
                
                # Try to match by name (more flexible matching)
                message_lower = message.lower()
                self.logger.info(f"Trying flexible name matching with message: '{message_lower}'")
                for i, rec in enumerate(recommendations):
                    template = rec.get("template", {})
                    template_name = template.get("name", "").lower()
                    template_description = template.get("description", "").lower()
                    
                    self.logger.info(f"Checking template {i+1}: '{template_name}'")
                    
                    # Check for exact name match
                    if template_name in message_lower:
                        self.logger.info(f"Selected template by exact name '{template_name}': {template.get('name', 'Unknown')}")
                        return template
                    
                    # Check for partial name match (e.g., "profile 1" matches "Profile 1")
                    if template_name.replace(" ", "").replace("-", "").replace("_", "") in message_lower.replace(" ", ""):
                        self.logger.info(f"Selected template by partial name '{template_name}': {template.get('name', 'Unknown')}")
                        return template
                    
                    # Check for category + number pattern (e.g., "profile 1", "landing 2")
                    category_pattern = r'(\w+)\s*(\d+)'
                    match = re.search(category_pattern, message_lower)
                    if match:
                        category, number = match.groups()
                        self.logger.info(f"Category pattern match: category='{category}', number='{number}'")
                        if category in template_name and str(i + 1) == number:
                            self.logger.info(f"Selected template by category+number '{category} {number}': {template.get('name', 'Unknown')}")
                            return template
                    
                    # Check if template name contains the selection
                    if any(word in template_name for word in message_lower.split() if len(word) > 2):
                        self.logger.info(f"Selected template by word match: {template.get('name', 'Unknown')}")
                        return template
                
                # If we get here, the selection was unclear
                self.logger.info(f"Could not match template selection '{selection}' to any available template")
                
                # Fallback: If there's only one template and the message isn't clearly rejecting it, select it
                if len(recommendations) == 1:
                    # Check if the message contains clear rejection words
                    rejection_words = ["no", "not", "different", "other", "none", "don't", "doesn't", "wrong"]
                    message_lower = message.lower()
                    if not any(word in message_lower for word in rejection_words):
                        self.logger.info(f"Fallback: Selecting the only available template since user didn't clearly reject it")
                        selected_template = recommendations[0].get("template", {})
                        return selected_template
                
                return None
                
            except Exception as e:
                self.logger.error(f"Error parsing template selection: {e}")
                
                # Fallback: If there's only one template, select it
                if len(recommendations) == 1:
                    self.logger.info(f"Fallback after error: Selecting the only available template")
                    selected_template = recommendations[0].get("template", {})
                    return selected_template
                
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

**CRITICAL OPTIMIZATION**: Always include question_generation in required_agents for the requirements phase. The system will automatically skip question generation during execution if only one template is found.

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
- User says "I want a modern login page" → Use requirements_analysis, then template_recommendation, then question_generation (system will auto-skip if only 1 template)
"""

            response = self.requirements_agent.call_claude_with_cot(prompt, enable_cot=True, extract_json=True)
            
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
            # CRITICAL FIX: Prioritize page_type from requirements analysis output over base context
            page_type = None
            if isinstance(previous_output, dict) and previous_output.get("page_type"):
                # Use the page_type from requirements analysis (this is the correct one)
                page_type = previous_output["page_type"]
                print(f"DEBUG: _build_agent_context: Using page_type '{page_type}' from requirements analysis output")
            else:
                # Only fall back to base context if requirements analysis didn't provide page_type
                page_type = base_context.get("page_type")
                if page_type:
                    print(f"DEBUG: _build_agent_context: Fallback to page_type '{page_type}' from base context")
            
            context = {
                "page_type": page_type,
                "requirements": previous_output if previous_output else {}
            }
            
        elif agent_name == "question_generation":
            # Template recommendations + requirements
            # Get page_type from requirements if available
            requirements = self.session_state.get("requirements", {})
            page_type = None
            if isinstance(requirements, dict) and requirements.get("page_type"):
                page_type = requirements["page_type"]
            
            context = {
                "templates": previous_output if previous_output else [],
                "requirements": requirements,
                "page_type": page_type
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
                agent_start_time = time.time()
                print(f"DEBUG: Starting {agent_name} agent execution...")
                
                agent_context = self._build_agent_context(agent_name, current_output, context)
                
                if agent_name == "requirements_analysis":
                    try:
                        start_time = time.time()
                        result = self.requirements_agent.analyze_requirements(message, context=agent_context)
                        end_time = time.time()
                        print(f"DEBUG: Requirements Analysis Agent LLM call completed in {end_time - start_time:.2f} seconds")
                        
                        # Standardize the output
                        result = self.requirements_agent.enhance_agent_output(result, agent_context)
                        current_output = result["data"]["primary_result"]
                        agent_results[agent_name] = result
                    
                        # Log total time for this agent
                        agent_end_time = time.time()
                        print(f"DEBUG: {agent_name} total execution time: {agent_end_time - agent_start_time:.2f} seconds")
                        print(f"DEBUG: {agent_name} total execution time: {agent_end_time - agent_start_time:.2f} seconds")
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
                        
                        # CRITICAL FIX: Use page_type from requirements analysis output, not from old context
                        # The requirements analysis agent has already determined the correct page_type
                        print(f"DEBUG: Template Recommendation - Requirements from session: {self.session_state.get('requirements', {}).get('page_type', 'None')}")
                        print(f"DEBUG: Template Recommendation - Current output page_type: {current_output.get('page_type', 'None') if isinstance(current_output, dict) else 'Not a dict'}")
                        print(f"DEBUG: Template Recommendation - Agent context page_type: {agent_context.get('page_type', 'None')}")
                        
                        if isinstance(requirements, dict) and requirements.get("page_type"):
                            # Use the page_type from requirements analysis (this is the correct one)
                            print(f"DEBUG: Using page_type '{requirements['page_type']}' from requirements analysis")
                        elif agent_context.get("page_type") and isinstance(requirements, dict):
                            # Only fall back to context page_type if requirements doesn't have one
                            requirements["page_type"] = agent_context["page_type"]
                            print(f"DEBUG: Fallback: Added page_type '{agent_context['page_type']}' from context to requirements")
                        
                        start_time = time.time()
                        print(f"DEBUG: Template Recommendation - Calling recommend_templates with requirements: {requirements}")
                        result = self.recommendation_agent.recommend_templates(requirements, context=agent_context)
                        end_time = time.time()
                        print(f"DEBUG: Template Recommendation Agent LLM call completed in {end_time - start_time:.2f} seconds")
                        print(f"DEBUG: Template Recommendation - Raw result: {result}")
                        
                        # Standardize the output
                        result = self.recommendation_agent.enhance_agent_output(result, agent_context)
                        current_output = result["data"]["primary_result"]
                        print(f"DEBUG: Template Recommendation - Standardized result primary_result: {current_output}")
                        agent_results[agent_name] = result
                    
                    # Log total time for this agent
                        agent_end_time = time.time()
                        print(f"DEBUG: {agent_name} total execution time: {agent_end_time - agent_start_time:.2f} seconds")
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
                        # Check if we should skip question generation (only one template found)
                        recommendations = self.session_state.get("recommendations", [])
                        if isinstance(recommendations, list) and len(recommendations) == 1:
                            print(f"DEBUG: Skipping question generation - only one template found ({recommendations[0].get('template', {}).get('name', 'Unknown')})")
                            # Create a placeholder result indicating no questions needed
                            result = {
                                "questions": [],
                                "focus_areas": [],
                                "template_count": 1,
                                "reasoning": "Single template found, no questions needed"
                            }
                            current_output = result
                            agent_results[agent_name] = result
                            continue  # Skip to next agent
                        
                        # Extract templates from current_output (which is from template_recommendation agent)
                        templates = []
                        if isinstance(current_output, list):
                            templates = current_output
                        elif isinstance(current_output, dict) and "data" in current_output:
                            templates = current_output["data"].get("primary_result", [])
                        else:
                            templates = self.session_state.get("recommendations", [])
                        
                        # If no templates available, fetch them directly
                        if not templates:
                            print("DEBUG: No templates available for question generation, fetching templates...")
                            requirements = self.session_state.get("requirements", {})
                            print(f"DEBUG: Question Generation - Session requirements: {requirements}")
                            print(f"DEBUG: Question Generation - Session requirements page_type: {requirements.get('page_type', 'None') if isinstance(requirements, dict) else 'Not a dict'}")
                            
                            # Ensure page_type is included - get from requirements or session state
                            page_type = None
                            if isinstance(requirements, dict) and requirements.get("page_type"):
                                page_type = requirements["page_type"]
                                print(f"DEBUG: Using page_type '{page_type}' from requirements")
                            else:
                                # Try to get page_type from session state requirements if not in current requirements
                                session_requirements = self.session_state.get("requirements", {})
                                if isinstance(session_requirements, dict) and session_requirements.get("page_type"):
                                    page_type = session_requirements["page_type"]
                                    print(f"DEBUG: Using page_type '{page_type}' from session requirements")
                                    # Add it to current requirements for template fetching
                                    if isinstance(requirements, dict):
                                        requirements["page_type"] = page_type
                                else:
                                    # Last resort: try context
                                    page_type = self.session_state.get("context", {}).get("page_type")
                                    if page_type and isinstance(requirements, dict):
                                        requirements["page_type"] = page_type
                                        print(f"DEBUG: Fallback: Added page_type '{page_type}' from context to requirements")
                            
                            if page_type:
                                print(f"DEBUG: Template fetching with page_type: {page_type}")
                            else:
                                print(f"DEBUG: No page_type found, using default category")
                            
                            # Get templates and standardize the output like in normal flow
                            template_list = self.recommendation_agent.recommend_templates(requirements)
                            template_result = self.recommendation_agent.enhance_agent_output(template_list, {"page_type": page_type})
                            
                            if template_result.get("success") and "data" in template_result:
                                templates = template_result["data"].get("primary_result", [])
                                # Store in session for future use
                                self.session_state["recommendations"] = templates
                                print(f"DEBUG: Fetched {len(templates)} templates for question generation")
                        
                        requirements = self.session_state.get("requirements", {})
                        start_time = time.time()
                        result = self.question_agent.generate_questions(templates, requirements)
                        end_time = time.time()
                        print(f"DEBUG: Question Generation Agent LLM call completed in {end_time - start_time:.2f} seconds")
                        
                        # The result is already a dictionary, not standardized format
                        current_output = result
                        agent_results[agent_name] = result
                    
                    # Log total time for this agent
                        agent_end_time = time.time()
                        print(f"DEBUG: {agent_name} total execution time: {agent_end_time - agent_start_time:.2f} seconds")
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
                # Log total time for this agent
                agent_end_time = time.time()
                print(f"DEBUG: {agent_name} total execution time: {agent_end_time - agent_start_time:.2f} seconds")
                    
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
                # Check if this is question generation output or if questions were skipped
                if ("questions" in current_output and "template_count" in current_output):
                    # Check if question_generation was executed or skipped
                    if "question_generation" in agent_results:
                        # Question generation was executed - format questions
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
                    else:
                        # Question generation was skipped - present single template directly
                        template_count = current_output.get("template_count", 0)
                        if template_count == 1:
                            # Get the single template from session state
                            recommendations = self.session_state.get("recommendations", [])
                            if recommendations and len(recommendations) == 1:
                                template = recommendations[0].get("template", {})
                                template_name = template.get("name", "Template 1")
                                template_description = template.get("description", "No description available")
                                
                                response = f"I found 1 perfect template that matches your requirements!\n\n"
                                response += f"**{template_name}** - {template_description}\n\n"
                                response += "This template is an excellent match for your needs. Would you like me to show you this template or would you prefer to proceed with it?"
                            else:
                                response = f"I found {template_count} template that matches your requirements. Let me know how you'd like to proceed."
                        else:
                            response = f"I found {template_count} templates that match your requirements. Let me know how you'd like to proceed."
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
                # Only include questions if question_generation was executed
                targeted_questions = self.session_state.get("questions") if "question_generation" in agent_results else {"questions": []}
                
                formatted_response = self.user_proxy_agent.create_response_from_instructions(
                    "template recommendations",
                    {
                        "requirements": self.session_state.get("requirements"),
                        "templates": self.session_state.get("recommendations"),
                        "targeted_questions": targeted_questions,
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
        phase_start_time = time.time()
        try:
            self.logger.info(f"Handling editing phase request for session {session_id}")
            print(f"DEBUG: Starting editing phase execution...")
            
            # Create a context with the current UI state
            context_start_time = time.time()
            context = {
                "current_ui_codes": current_ui_state,
                "session_id": session_id
            }
            context_end_time = time.time()
            print(f"DEBUG: Context creation completed in {context_end_time - context_start_time:.2f} seconds")
            
            # Use the UI editing agent directly instead of trying to run async code
            ui_editing_start_time = time.time()
            print(f"DEBUG: Starting UI editing agent execution...")
            modification_result = self.editing_agent.process_modification_request(user_message, current_ui_state)
            ui_editing_end_time = time.time()
            print(f"DEBUG: UI editing agent completed in {ui_editing_end_time - ui_editing_start_time:.2f} seconds")
            
            if not modification_result.get("success", False):
                print(f"DEBUG: UI editing agent failed, total editing phase time: {time.time() - phase_start_time:.2f} seconds")
                return self._create_error_response("Failed to process modification request")
            
            # Generate user response using the user proxy agent
            user_proxy_start_time = time.time()
            print(f"DEBUG: Starting user proxy agent execution...")
            user_response = self.user_proxy_agent.create_response_from_instructions(
                "modification_success",
                {
                    "modification_result": modification_result,
                    "user_message": user_message,
                    "context": context
                }
            )
            user_proxy_end_time = time.time()
            print(f"DEBUG: User proxy agent completed in {user_proxy_end_time - user_proxy_start_time:.2f} seconds")
            
            # Log total editing phase execution time
            phase_end_time = time.time()
            print(f"DEBUG: Editing phase total execution time: {phase_end_time - phase_start_time:.2f} seconds")
            print(f"DEBUG: Breakdown:")
            print(f"  - Context creation: {context_end_time - context_start_time:.2f} seconds")
            print(f"  - UI editing agent: {ui_editing_end_time - ui_editing_start_time:.2f} seconds")
            print(f"  - User proxy agent: {user_proxy_end_time - user_proxy_start_time:.2f} seconds")
            print(f"  - Total overhead: {phase_end_time - phase_start_time - (context_end_time - context_start_time) - (ui_editing_end_time - ui_editing_start_time) - (user_proxy_end_time - user_proxy_start_time):.2f} seconds")
            
            return {
                "success": True,
                "response": user_response,
                "modifications": modification_result.get("modifications"),
                "modified_template": modification_result.get("modified_template"),
                "metadata": {
                    "session_id": session_id,
                    "intent": "modification_request",
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": phase_end_time - phase_start_time,
                    "timing_breakdown": {
                        "context_creation": context_end_time - context_start_time,
                        "ui_editing_agent": ui_editing_end_time - ui_editing_start_time,
                        "user_proxy_agent": user_proxy_end_time - user_proxy_start_time,
                        "total_overhead": phase_end_time - phase_start_time - (context_end_time - context_start_time) - (ui_editing_end_time - ui_editing_start_time) - (user_proxy_end_time - user_proxy_start_time)
                    }
                }
            }
                
        except Exception as e:
            phase_end_time = time.time()
            print(f"DEBUG: Editing phase failed after {phase_end_time - phase_start_time:.2f} seconds")
            self.logger.error(f"Error in editing phase: {e}")
            return self._create_error_response(f"Error processing your request: {str(e)}")

    def handle_logo_analysis(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logo analysis and apply design preferences to UI"""
        phase_start_time = time.time()
        try:
            self.logger.info(f"Handling logo analysis request for session {context.get('session_id')}")
            print(f"DEBUG: Starting logo analysis execution...")
            
            # Step 1: Use RequirementsAnalysisAgent to analyze the logo
            logo_analysis_start_time = time.time()
            print(f"DEBUG: Starting logo analysis with RequirementsAnalysisAgent...")
            logo_analysis_result = self.requirements_agent.analyze_logo_and_requirements(
                user_message, 
                context
            )
            logo_analysis_end_time = time.time()
            print(f"DEBUG: Logo analysis with RequirementsAnalysisAgent completed in {logo_analysis_end_time - logo_analysis_start_time:.2f} seconds")
            
            # Debug: Log the response structure
            self.logger.info(f"Logo analysis result structure: {list(logo_analysis_result.keys())}")
            self.logger.info(f"Logo analysis success: {logo_analysis_result.get('success')}")
            if 'data' in logo_analysis_result:
                self.logger.info(f"Logo analysis data keys: {list(logo_analysis_result['data'].keys())}")
            
            if not logo_analysis_result.get("success", False):
                print(f"DEBUG: Logo analysis failed, total logo analysis time: {time.time() - phase_start_time:.2f} seconds")
                return self._create_error_response("Failed to analyze logo")
            
            # Step 2: Extract design preferences from logo analysis
            data_extraction_start_time = time.time()
            print(f"DEBUG: Starting data extraction from logo analysis...")
            # The standardized response has data nested under 'data' key
            data = logo_analysis_result.get("data", {})
            logo_analysis = data.get("logo_analysis", {})
            design_preferences = data.get("design_preferences", {})
            data_extraction_end_time = time.time()
            print(f"DEBUG: Data extraction completed in {data_extraction_end_time - data_extraction_start_time:.2f} seconds")
            
            # Step 3: Create modification plan based on logo analysis
            plan_creation_start_time = time.time()
            print(f"DEBUG: Starting modification plan creation...")
            modification_plan = self._create_modification_plan_from_logo_analysis(
                logo_analysis, 
                design_preferences, 
                user_message
            )
            plan_creation_end_time = time.time()
            print(f"DEBUG: Modification plan creation completed in {plan_creation_end_time - plan_creation_start_time:.2f} seconds")
            
            # Step 4: Apply modifications using UI Editing Agent
            ui_modification_start_time = time.time()
            print(f"DEBUG: Starting UI modifications with UI Editing Agent...")
            current_ui_codes = context.get("current_ui_codes", {})
            
            # Ensure current_ui_codes has the expected structure
            if not current_ui_codes or not isinstance(current_ui_codes, dict):
                self.logger.warning("No valid UI codes found, skipping modification")
                modification_result = {
                    "success": False,
                    "error": "No valid UI codes available for modification"
                }
            else:
                modification_result = self.editing_agent.process_modification_request(
                    modification_plan, 
                    current_ui_codes
                )
            ui_modification_end_time = time.time()
            print(f"DEBUG: UI modifications completed in {ui_modification_end_time - ui_modification_start_time:.2f} seconds")
            
            if not modification_result.get("success", False):
                print(f"DEBUG: UI modifications failed, total logo analysis time: {time.time() - phase_start_time:.2f} seconds")
                return self._create_error_response("Failed to apply logo-based modifications")
            
            # Step 5: Generate user response
            user_response_start_time = time.time()
            print(f"DEBUG: Starting user response generation...")
            user_response = self.user_proxy_agent.create_response_from_instructions(
                "logo_analysis_success",
                {
                    "logo_analysis": logo_analysis,
                    "modification_result": modification_result,
                    "user_message": user_message,
                    "context": context
                }
            )
            user_response_end_time = time.time()
            print(f"DEBUG: User response generation completed in {user_response_end_time - user_response_start_time:.2f} seconds")
            
            # Log total logo analysis execution time
            phase_end_time = time.time()
            print(f"DEBUG: Logo analysis total execution time: {phase_end_time - phase_start_time:.2f} seconds")
            print(f"DEBUG: Breakdown:")
            print(f"  - Logo analysis (RequirementsAnalysisAgent): {logo_analysis_end_time - logo_analysis_start_time:.2f} seconds")
            print(f"  - Data extraction: {data_extraction_end_time - data_extraction_start_time:.2f} seconds")
            print(f"  - Modification plan creation: {plan_creation_end_time - plan_creation_start_time:.2f} seconds")
            print(f"  - UI modifications (UI Editing Agent): {ui_modification_end_time - ui_modification_start_time:.2f} seconds")
            print(f"  - User response generation: {user_response_end_time - user_response_start_time:.2f} seconds")
            print(f"  - Total overhead: {phase_end_time - phase_start_time - (logo_analysis_end_time - logo_analysis_start_time) - (data_extraction_end_time - data_extraction_start_time) - (plan_creation_end_time - plan_creation_start_time) - (ui_modification_end_time - ui_modification_start_time) - (user_response_end_time - user_response_start_time):.2f} seconds")
            
            return {
                "success": True,
                "response": user_response,
                "logo_analysis": logo_analysis,
                "ui_modifications": modification_result.get("modified_template"),
                "metadata": {
                    "session_id": context.get("session_id"),
                    "intent": "logo_analysis",
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": phase_end_time - phase_start_time,
                    "timing_breakdown": {
                        "logo_analysis_agent": logo_analysis_end_time - logo_analysis_start_time,
                        "data_extraction": data_extraction_end_time - data_extraction_start_time,
                        "modification_plan_creation": plan_creation_end_time - plan_creation_start_time,
                        "ui_modifications": ui_modification_end_time - ui_modification_start_time,
                        "user_response_generation": user_response_end_time - user_response_start_time,
                        "total_overhead": phase_end_time - phase_start_time - (logo_analysis_end_time - logo_analysis_start_time) - (data_extraction_end_time - data_extraction_start_time) - (plan_creation_end_time - plan_creation_start_time) - (ui_modification_end_time - ui_modification_start_time) - (user_response_end_time - user_response_start_time)
                    }
                }
            }
                
        except Exception as e:
            phase_end_time = time.time()
            print(f"DEBUG: Logo analysis failed after {phase_end_time - phase_start_time:.2f} seconds")
            self.logger.error(f"Error in logo analysis: {e}")
            return self._create_error_response(f"Error analyzing logo: {str(e)}")

    def _create_modification_plan_from_logo_analysis(self, logo_analysis: Dict[str, Any], design_preferences: Dict[str, Any], user_message: str) -> str:
        """Create a modification plan based on logo analysis results"""
        plan_parts = []
        
        # Add color modifications
        if logo_analysis.get("colors"):
            colors = logo_analysis["colors"]
            plan_parts.append(f"Apply the logo's color palette ({', '.join(colors)}) to the UI elements")
        
        # Add style modifications
        if logo_analysis.get("style"):
            style = logo_analysis["style"]
            plan_parts.append(f"Match the logo's {style} style throughout the UI")
        
        # Add font modifications
        if logo_analysis.get("fonts"):
            fonts = logo_analysis["fonts"]
            plan_parts.append(f"Use fonts that complement the logo: {', '.join(fonts)}")
        
        # Add user's specific request
        if user_message:
            plan_parts.append(f"User request: {user_message}")
        
        # Create a comprehensive modification plan
        if plan_parts:
            plan = " | ".join(plan_parts)
            # Add specific instructions for UI elements
            plan += " | Focus on updating colors, fonts, and styling to match the logo's design language"
            return plan
        else:
            return "Apply logo design preferences to the UI by updating colors, fonts, and styling to create visual consistency"
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "success": False,
            "response": error_message,
            "metadata": {
                "intent": "error",
                "timestamp": datetime.now().isoformat()
            }
        }
    
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
        """Process UI modification using NEW Two-Step UI Editing Agent"""
        try:
            self.logger.info(f"Processing UI modification with two-step agent: {user_message}")
            
            # Use the new two-step process_modification_request method
            modification_result = self.editing_agent.process_modification_request(user_message, current_ui_state)
            
            if not modification_result.get("success", False):
                return {
                    "success": False,
                    "error": modification_result.get("error", "Failed to process modification request")
                }
            
            # Extract the changes summary for response
            changes_summary = modification_result.get("changes_summary", [])
            change_summary = changes_summary[0] if changes_summary else "Changes applied successfully"
            
            return {
                "success": True,
                "modifications": modification_result.get("modified_template"),
                "change_summary": change_summary,
                "modification_result": modification_result  # Include full result for detailed responses
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
            # Check if this is a template-related question
            user_message_lower = user_message.lower()
            if any(keyword in user_message_lower for keyword in ["category", "template", "what is", "what's"]):
                # Try to get template information from session state or current UI state
                template_info = None
                
                # Check session state first
                if hasattr(self, 'session_state') and self.session_state.get('selected_template'):
                    template_info = self.session_state['selected_template']
                elif current_ui_state and current_ui_state.get('template_info'):
                    template_info = current_ui_state['template_info']
                
                if template_info:
                    # Use the User Proxy Agent to create a proper response
                    from agents.user_proxy_agent import UserProxyAgent
                    user_proxy = UserProxyAgent()
                    
                    instruction = {
                        "type": "template_info_request",
                        "user_message": user_message,
                        "template_info": template_info,
                        "context": {"session_id": session_id}
                    }
                    
                    response = user_proxy.create_response_from_instructions(instruction)
                    
                    return {
                        "success": True,
                        "response": response,
                        "metadata": {
                            "session_id": session_id,
                            "intent": "template_info_request",
                            "template_info": template_info
                        }
                    }
            
            # For general questions, use the LLM to generate a helpful response
            try:
                response = self._generate_llm_response_for_general_question(user_message, session_id, current_ui_state)
                
                return {
                    "success": True,
                    "response": response,
                    "metadata": {
                        "session_id": session_id,
                        "intent": "general_request",
                        "response_type": "llm_generated"
                    }
                }
                
            except Exception as llm_error:
                self.logger.warning(f"LLM response generation failed, falling back to User Proxy Agent: {llm_error}")
                
                # Fallback to User Proxy Agent if LLM fails
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
                        "intent": "general_request",
                        "response_type": "fallback"
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

    def _generate_llm_response_for_general_question(self, user_message: str, session_id: str, current_ui_state: Dict[str, Any] = None) -> str:
        """Generate LLM response for general questions using Claude API"""
        try:
            import os
            from anthropic import Anthropic
            
            # Get API key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise Exception("ANTHROPIC_API_KEY not found in environment variables")
            
            # Initialize Claude client
            client = Anthropic(api_key=api_key)
            
            # Build context for the LLM
            context_parts = []
            
            # Add session context if available
            if hasattr(self, 'session_state') and self.session_state:
                if self.session_state.get('current_phase'):
                    context_parts.append(f"Current phase: {self.session_state['current_phase']}")
                if self.session_state.get('selected_template'):
                    template = self.session_state['selected_template']
                    context_parts.append(f"Selected template: {template.get('name', 'Unknown')} ({template.get('category', 'Unknown')})")
            
            # Add UI state context if available
            if current_ui_state:
                if current_ui_state.get('template_info'):
                    template_info = current_ui_state['template_info']
                    context_parts.append(f"Current template: {template_info.get('name', 'Unknown')} ({template_info.get('category', 'Unknown')})")
            
            # Build the system message
            system_message = f"""You are a helpful AI assistant for a UI mockup generation system. 

Context:
- Session ID: {session_id}
- {' | '.join(context_parts) if context_parts else 'No specific context available'}

Your role is to:
1. Answer general questions about the system, UI design, web development, or any other topics
2. Provide helpful, accurate, and friendly responses
3. If the question is about the current template or session, use the context provided
4. If it's a general knowledge question, answer it helpfully
5. Keep responses concise but informative
6. Use plain text (no emojis or special characters)

Current user question: {user_message}"""
            
            # Call Claude API
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=system_message,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            # Extract and return the response
            response = self._extract_response_text(message) if message.content else "I'm sorry, I couldn't generate a response for that question."
            
            self.logger.info(f"Generated LLM response for general question: {user_message[:50]}...")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating LLM response: {e}")
            raise Exception(f"LLM response generation failed: {str(e)}")
    
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
    
    async def _handle_phase_transition(self, selected_template: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the complete transition from Phase 1 to Phase 2"""
        try:
            self.logger.info(f"Starting Phase 1 → Phase 2 transition for template: {selected_template.get('name', 'Unknown')}")
            
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
            
            self.logger.info(f"Template result received - success: {template_result.get('success', False)}")
            
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
                    "style_css": template_result.get("style_css", "")
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
            
            # Step 6: Save using file manager (new format)
            from utils.file_manager import UICodeFileManager
            import os
            
            # Use absolute path to match main.py
            base_dir = os.path.join(os.getcwd(), "temp_ui_files")
            file_manager = UICodeFileManager(base_dir=base_dir)
            
            # Create session with template data
            template_data = {
                "html_export": template_result.get("html_export", ""),
                "style_css": template_result.get("style_css", ""),
                "globals_css": template_result.get("global_css", ""),
                "template_id": template_id,
                "name": actual_template.get("name", "Unknown"),
                "category": actual_template.get("category", "unknown")
            }
            
            import time
            success = file_manager.create_session(self.session_id, template_data)
            
            if success:
                self.logger.info(f"[{time.strftime('%H:%M:%S')}] Session created using file manager: {self.session_id}")
                # Add longer delay to ensure files are fully written and accessible
                time.sleep(0.5)
                self.logger.info(f"[{time.strftime('%H:%M:%S')}] Files should now be accessible")
                
                # Verify that the session is actually accessible
                retry_count = 0
                max_retries = 5
                while retry_count < max_retries:
                    if file_manager.session_exists(self.session_id):
                        self.logger.info(f"[{time.strftime('%H:%M:%S')}] Session verified as accessible after {retry_count + 1} attempts")
                        break
                    else:
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.info(f"[{time.strftime('%H:%M:%S')}] Session not yet accessible, retrying in 0.2s... (attempt {retry_count})")
                            time.sleep(0.2)
                        else:
                            self.logger.warning(f"[{time.strftime('%H:%M:%S')}] Session still not accessible after {max_retries} attempts")
            else:
                self.logger.error(f"Failed to create session using file manager: {self.session_id}")
                # Fallback to old JSON format
                import json
                import os
                
                temp_dir = "temp_ui_files"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                
                json_filename = f"ui_codes_{self.session_id}.json"
                json_filepath = os.path.join(temp_dir, json_filename)
                
                with open(json_filepath, 'w') as f:
                    json.dump(ui_codes_data, f, indent=2)
                
                self.logger.info(f"Fallback JSON file created: {json_filepath}")
            
            # Step 7: Update session state
            self.session_state["current_phase"] = "editing"
            self.session_state["selected_template"] = selected_template
            self.session_state["ui_codes_file"] = f"temp_ui_files/{self.session_id}/"
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
                    "ui_codes_file": f"temp_ui_files/{self.session_id}/"
                }
            })
            
            self.logger.info(f"Phase transition response created successfully")
            
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
                    "ui_codes_file": f"temp_ui_files/{self.session_id}/"
                }
            }
            
            self.logger.info(f"Final phase transition response created successfully")
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
    
    async def _save_modified_template_to_file(self, modified_template: Dict[str, Any]) -> None:
        """Save the modified template using file manager"""
        try:
            from utils.file_manager import UICodeFileManager
            import os
            
            print(f"DEBUG SAVE: Starting save process for session {self.session_id}")
            print(f"DEBUG SAVE: Modified template keys: {list(modified_template.keys())}")
            
            # Initialize file manager with absolute path to match main.py
            base_dir = os.path.join(os.getcwd(), "temp_ui_files")
            file_manager = UICodeFileManager(base_dir=base_dir)
            
            # Check if session exists in new format, if not create it
            if not file_manager.session_exists(self.session_id):
                # Create new session with the modified template
                template_data = {
                    "html_export": modified_template.get("html_export", ""),
                    "style_css": modified_template.get("style_css", ""),
                    "globals_css": modified_template.get("globals_css", ""),
                    "template_id": modified_template.get("template_id", ""),
                    "name": modified_template.get("template_name", ""),
                    "category": modified_template.get("template_category", "")
                }
                success = file_manager.create_session(self.session_id, template_data)
                if not success:
                    self.logger.error(f"Failed to create new session {self.session_id}")
                    return
            else:
                # Save modifications to existing session
                modification_metadata = {
                    "user_request": modified_template.get("modification_metadata", {}).get("user_request", "UI modification"),
                    "modification_type": "ui_agent",
                    "changes_applied": modified_template.get("modification_metadata", {}).get("changes_applied", ["UI modifications applied"])
                }
                
                # Prepare the data structure expected by file_manager.save_session
                session_data = {
                    "html_export": modified_template.get("html_export", ""),
                    "style_css": modified_template.get("style_css", ""),
                    "globals_css": modified_template.get("globals_css", "")
                }
                
                success = file_manager.save_session(self.session_id, session_data, modification_metadata)
                if not success:
                    self.logger.error(f"Failed to save session {self.session_id}")
                    return
            
            self.logger.info(f"Modified template saved using file manager for session {self.session_id}")
            print(f"DEBUG SAVE: Template saved successfully")
            
            # Trigger screenshot regeneration
            try:
                from services.screenshot_service import get_screenshot_service
                screenshot_service = await get_screenshot_service()
                html_content = modified_template.get("html_export", "")
                css_content = modified_template.get("globals_css", "") + "\n" + modified_template.get("style_css", "")
                result = await screenshot_service.generate_screenshot(html_content, css_content, self.session_id)
                self.logger.info(f"Screenshot regenerated: {result['success']}")
            except Exception as e:
                self.logger.error(f"Error regenerating screenshot: {e}")
                
        except Exception as e:
            self.logger.error(f"Error saving modified template using file manager: {e}")
    
    async def process_ui_edit_request(self, message: str, current_ui_codes: Optional[Dict[str, Any]] = None, session_id: str = None) -> Dict[str, Any]:
        """
        Process UI editing requests through the agent system
        This method routes UI Editor chat requests to the proper agent workflow
        """
        try:
            self.logger.info(f"Processing UI edit request for session {session_id}: {message}")
            print(f"DEBUG ORCHESTRATOR: Processing UI edit request for session {session_id}: {message}")
            print(f"DEBUG ORCHESTRATOR: Orchestrator session ID: {self.session_id}")
            print(f"DEBUG ORCHESTRATOR: Request session ID: {session_id}")
            print(f"DEBUG ORCHESTRATOR: Session ID match: {self.session_id == session_id}")
            print(f"DEBUG ORCHESTRATOR: Current phase: {self.session_state.get('current_phase', 'unknown')}")
            print(f"DEBUG ORCHESTRATOR: Has selected template: {bool(self.session_state.get('selected_template'))}")
            
                        # Ensure we're in editing phase and have a selected template
            if self.session_state.get("current_phase") != "editing" or not self.session_state.get("selected_template"):
                print(f"DEBUG ORCHESTRATOR: Setting up editing phase - current phase: {self.session_state.get('current_phase', 'NOT_SET')}")
                
                # If no current_ui_codes provided, try to load from session file
                if not current_ui_codes:
                    current_ui_codes = await self._load_ui_state_from_session()
                    self.logger.info(f"Auto-loaded UI codes from session: {bool(current_ui_codes)}")
                
                # Try to load the session state from existing UI codes
                if current_ui_codes and current_ui_codes.get("template_info"):
                    # Set up the session state for editing
                    self.session_state["current_phase"] = "editing"
                    self.session_state["selected_template"] = current_ui_codes.get("template_info", {})
                    self.session_state["ui_codes"] = current_ui_codes
                    self.logger.info(f"Set up editing session with template: {current_ui_codes.get('template_info', {}).get('name', 'Unknown')}")
                    
                    # Update the session in the global manager
                    session_manager.update_session(self.session_id, self.session_state)
                    print(f"DEBUG ORCHESTRATOR: Updated session state in global manager")
                else:
                    return {
                        "success": False,
                        "response": "No template available for editing. Please select a template first.",
                        "session_id": session_id,
                        "metadata": {"error": "no_template_selected"}
                    }
            
            # Step 1: Detect the intent first
            editing_intent = await self._detect_editing_intent_advanced(message, self.session_state["selected_template"])
            print(f"DEBUG ORCHESTRATOR: UI Editor intent detected: {editing_intent}")
            
            # Step 2: Route based on intent
            if editing_intent == "modification_request":
                result = await self._handle_editing_modification_request(
                    message=message,
                    selected_template=self.session_state["selected_template"],
                    context={"ui_codes": current_ui_codes}
                )
            elif editing_intent == "clarification_request":
                result = await self._handle_editing_clarification_request(
                    message=message,
                    selected_template=self.session_state["selected_template"],
                    context={"ui_codes": current_ui_codes}
                )
            elif editing_intent == "completion_request":
                result = await self._handle_editing_completion_request(
                    message=message,
                    selected_template=self.session_state["selected_template"],
                    context={"ui_codes": current_ui_codes}
                )
            elif editing_intent == "preview_request":
                result = await self._handle_editing_preview_request(
                    message=message,
                    selected_template=self.session_state["selected_template"],
                    context={"ui_codes": current_ui_codes}
                )
            else:
                result = await self._handle_editing_general_request(
                    message=message,
                    selected_template=self.session_state["selected_template"],
                    context={"ui_codes": current_ui_codes}
                )
            
            # Format the response for the UI Editor API
            response = {
                "success": result.get("success", True),
                "response": result.get("response", "Processing your request..."),
                "ui_modifications": result.get("modification_result"),
                "session_id": session_id,
                "metadata": {
                    "intent": result.get("intent", "modification_request"),
                    "phase": "editing",
                    "feature": "ui_editor_agent"
                }
            }
            
            # Add report-related fields if they exist
            if result.get("report_generated"):
                response["report_generated"] = result.get("report_generated")
                response["report_file"] = result.get("report_file")
                response["report_metadata"] = result.get("report_metadata")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing UI edit request: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error while processing your request: {str(e)}",
                "session_id": session_id,
                "metadata": {"error": "processing_error"}
            } 


    

    

    
