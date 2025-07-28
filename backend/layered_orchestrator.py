"""
Layered Orchestrator - Main orchestrator that integrates all layers
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid

from layers import (
    RecoveryLayer, FeedbackLayer, IntelligenceLayer, MemoryLayer,
    ToolsLayer, ValidationLayer, ControlLayer
)
from layers.intelligence_layer import LLMRequest, ResponseFormat
from layers.control_layer import UserInput, SystemResponse, InputType, ResponseType
from layers.feedback_layer import FeedbackType

class LayeredOrchestrator:
    """Main orchestrator that coordinates all layers for robust AI workflow"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_id = str(uuid.uuid4())
        
        # Initialize all layers
        self.recovery = RecoveryLayer()
        self.feedback = FeedbackLayer()
        self.intelligence = IntelligenceLayer()
        self.memory = MemoryLayer()
        self.tools = ToolsLayer()
        self.validation = ValidationLayer()
        self.control = ControlLayer()
        
        # Session state
        self.session_state = {
            "session_id": self.session_id,
            "created_at": datetime.now(),
            "current_phase": "initial",
            "selected_category": None,
            "user_preferences": {},
            "conversation_context": [],
            "project_state": {},
            "validation_results": [],
            "tool_calls": []
        }
        
        # Initialize session in memory
        self.memory.create_session_context(self.session_id, self.session_state)
        
        self.logger.info(f"Layered Orchestrator initialized with session ID: {self.session_id}")
    
    async def process_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main entry point for processing user messages"""
        
        try:
            # Step 1: Control Layer - Process and classify user input
            user_input = self.control.process_user_input(message, context)
            
            # Step 2: Validation Layer - Validate user input
            validation_results = self.validation.validate_user_input(message, user_input.input_type.value)
            
            # Step 3: Memory Layer - Store conversation context
            self.memory.store_conversation_context(
                self.session_id,
                self.session_state["conversation_context"] + [{"role": "user", "content": message}]
            )
            
            # Step 4: Control Layer - Generate initial response
            system_response = self.control.generate_response(user_input, context)
            
            # Step 5: Intelligence Layer - Enhance response with LLM if needed
            enhanced_response = await self._enhance_response_with_llm(user_input, system_response, context)
            
            # Step 6: Tools Layer - Execute any required tools
            tool_results = await self._execute_tools(system_response.actions)
            
            # Step 7: Update session state
            self._update_session_state(user_input, enhanced_response, tool_results)
            
            # Step 8: Memory Layer - Store updated state
            self.memory.store_project_state(self.session_id, self.session_state)
            
            # Step 9: Validation Layer - Validate final response
            final_validation = self.validation.validate_api_response(
                {"response": enhanced_response.content, "actions": tool_results},
                "json"
            )
            
            # Convert ValidationResult objects to dictionaries
            validation_results_dict = []
            for result in validation_results + final_validation:
                validation_results_dict.append({
                    "is_valid": result.is_valid,
                    "level": result.level.value,
                    "message": result.message,
                    "field": result.field,
                    "value": result.value,
                    "suggestions": result.suggestions,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None
                })
            
            return {
                "success": True,
                "session_id": self.session_id,
                "response": enhanced_response.content,
                "actions": tool_results,
                "validation_results": validation_results_dict,
                "session_state": self.session_state,
                "metadata": {
                    "input_type": user_input.input_type.value,
                    "confidence": user_input.confidence,
                    "response_type": enhanced_response.response_type.value,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            # Recovery Layer - Handle errors
            recovery_actions = self.recovery.handle_critical_error(e, {
                "operation": "process_user_message",
                "session_id": self.session_id,
                "message": message
            })
            
            self.logger.error(f"Error processing user message: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "recovery_actions": recovery_actions,
                "session_id": self.session_id
            }
    
    async def _enhance_response_with_llm(self, user_input: UserInput, system_response: SystemResponse, context: Optional[Dict[str, Any]] = None) -> SystemResponse:
        """Enhance system response with LLM intelligence"""
        
        # Only enhance certain types of responses
        if system_response.response_type in [ResponseType.ANSWER, ResponseType.GUIDANCE, ResponseType.SUGGESTION]:
            
            # Get conversation context from memory
            conversation_context = self.memory.retrieve_conversation_context(self.session_id)
            
            # Create enhanced prompt
            enhanced_prompt = self._create_enhanced_prompt(user_input, system_response, conversation_context, context)
            
            # Call LLM with retry logic
            llm_response = await self.recovery.async_retry_with_backoff(
                lambda: self.intelligence.call_llm(LLMRequest(
                    prompt=enhanced_prompt,
                    system_prompt=self._get_system_prompt(),
                    response_format=ResponseFormat.TEXT,
                    max_tokens=500,
                    temperature=0.7
                )),
                max_retries=3,
                base_delay=1.0
            )
            
            if llm_response.error:
                self.logger.warning(f"LLM enhancement failed: {llm_response.error}")
                return system_response
            
            # Update response content
            system_response.content = llm_response.content
            
        return system_response
    
    async def _execute_tools(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tools based on system actions"""
        tool_results = []
        
        for action in actions:
            try:
                if action["type"] == "set_category":
                    # Update session state
                    self.session_state["selected_category"] = action["data"]["category"]
                    tool_results.append({
                        "action": "set_category",
                        "success": True,
                        "data": action["data"]
                    })
                
                elif action["type"] == "start_requirements_gathering":
                    # Create feedback request for requirements
                    feedback_request = self.feedback.create_feedback_request(
                        feedback_type=FeedbackType.CONTENT_REVIEW,
                        title="Requirements Gathering",
                        description="Gather user requirements for template generation",
                        data=action["data"],
                        deadline_hours=24
                    )
                    tool_results.append({
                        "action": "start_requirements_gathering",
                        "success": True,
                        "feedback_request_id": feedback_request.id
                    })
                
                elif action["type"] == "reset_conversation":
                    # Reset conversation state
                    self.control.clear_conversation_history()
                    self.session_state["conversation_context"] = []
                    self.session_state["current_phase"] = "initial"
                    self.session_state["selected_category"] = None
                    tool_results.append({
                        "action": "reset_conversation",
                        "success": True
                    })
                
                elif action["type"] == "log_complaint":
                    # Log complaint for analysis
                    tool_results.append({
                        "action": "log_complaint",
                        "success": True,
                        "data": action["data"]
                    })
                
                else:
                    # Try to execute as a registered tool
                    if action["type"] in self.tools.registered_tools:
                        tool_call = self.tools.execute_tool(action["type"], action.get("data", {}))
                        tool_results.append({
                            "action": action["type"],
                            "success": not bool(tool_call.error),
                            "result": tool_call.result,
                            "error": tool_call.error
                        })
                    else:
                        tool_results.append({
                            "action": action["type"],
                            "success": False,
                            "error": f"Unknown action type: {action['type']}"
                        })
                        
            except Exception as e:
                self.logger.error(f"Error executing action {action['type']}: {e}")
                tool_results.append({
                    "action": action["type"],
                    "success": False,
                    "error": str(e)
                })
        
        return tool_results
    
    def _create_enhanced_prompt(self, user_input: UserInput, system_response: SystemResponse, conversation_context: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> str:
        """Create enhanced prompt for LLM"""
        
        prompt_parts = []
        
        # Add conversation context
        if conversation_context:
            context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_context[-5:]])  # Last 5 messages
            prompt_parts.append(f"Conversation Context:\n{context_text}\n")
        
        # Add user input
        prompt_parts.append(f"User Input: {user_input.text}")
        
        # Add session state context
        if self.session_state["selected_category"]:
            prompt_parts.append(f"Selected Category: {self.session_state['selected_category']}")
        
        # Add system response template
        prompt_parts.append(f"System Response Type: {system_response.response_type.value}")
        prompt_parts.append(f"Current Response: {system_response.content}")
        
        # Add enhancement instructions
        prompt_parts.append("""
Please enhance the system response to be more helpful, specific, and engaging. Consider:
1. The user's input type and confidence level
2. The selected category and context
3. Previous conversation history
4. Making the response more natural and conversational
5. Adding specific suggestions or next steps when appropriate

Provide an enhanced version of the response that maintains the same intent but is more helpful and engaging.
""")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are an AI assistant helping users create UI mockups. You are part of a layered system that includes:

1. Recovery Layer - Handles errors and retries
2. Feedback Layer - Manages human oversight
3. Intelligence Layer - Provides LLM capabilities
4. Memory Layer - Maintains context
5. Tools Layer - Executes external actions
6. Validation Layer - Ensures quality
7. Control Layer - Manages business logic

Your role is to enhance system responses to be more helpful, natural, and engaging while maintaining the original intent. You should:

- Be conversational and friendly
- Provide specific, actionable advice
- Consider the user's context and preferences
- Suggest relevant next steps
- Maintain consistency with the system's capabilities

Available categories: landing, login, signup, profile, about, dashboard
Available styles: modern, minimal, responsive, user-friendly, professional, colorful, dark, light

Always work within these constraints and suggest only available options."""
    
    def _update_session_state(self, user_input: UserInput, system_response: SystemResponse, tool_results: List[Dict[str, Any]]):
        """Update session state based on processing results"""
        
        # Update conversation context
        self.session_state["conversation_context"].append({
            "role": "user",
            "content": user_input.text,
            "timestamp": user_input.timestamp.isoformat()
        })
        
        self.session_state["conversation_context"].append({
            "role": "assistant",
            "content": system_response.content,
            "timestamp": system_response.timestamp.isoformat()
        })
        
        # Update based on tool results
        for result in tool_results:
            if result["action"] == "set_category" and result["success"]:
                self.session_state["selected_category"] = result["data"]["category"]
                self.session_state["current_phase"] = "requirements_gathering"
            
            elif result["action"] == "reset_conversation" and result["success"]:
                self.session_state["current_phase"] = "initial"
                self.session_state["selected_category"] = None
        
        # Store tool calls
        self.session_state["tool_calls"].extend(tool_results)
        
        # Update last activity
        self.session_state["last_activity"] = datetime.now().isoformat()
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        return {
            "session_id": self.session_id,
            "session_state": self.session_state,
            "memory_stats": self.memory.get_memory_stats(),
            "validation_summary": self.validation.get_validation_summary(),
            "tool_statistics": self.tools.get_tool_statistics(),
            "conversation_summary": self.control.get_conversation_summary(),
            "pending_feedback": len(self.feedback.get_pending_feedback())
        }
    
    def reset_session(self) -> Dict[str, Any]:
        """Reset the current session"""
        self.session_id = str(uuid.uuid4())
        self.session_state = {
            "session_id": self.session_id,
            "created_at": datetime.now(),
            "current_phase": "initial",
            "selected_category": None,
            "user_preferences": {},
            "conversation_context": [],
            "project_state": {},
            "validation_results": [],
            "tool_calls": []
        }
        
        # Clear all layer histories
        self.control.clear_conversation_history()
        self.validation.clear_validation_history()
        
        # Create new session in memory
        self.memory.create_session_context(self.session_id, self.session_state)
        
        self.logger.info(f"Session reset. New session ID: {self.session_id}")
        
        return {
            "success": True,
            "new_session_id": self.session_id,
            "message": "Session reset successfully"
        }
    
    def get_available_categories(self) -> List[str]:
        """Get available categories from database"""
        try:
            # Use tools layer to query database
            tool_call = self.tools.execute_tool("query_database", {
                "query_type": "distinct",
                "collection": "templates",
                "filters": {"field": "category"}
            })
            
            if tool_call.result and tool_call.result.get("success"):
                return tool_call.result.get("results", [])
            else:
                return ["landing", "login", "signup", "profile", "about", "dashboard"]
                
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            return ["landing", "login", "signup", "profile", "about", "dashboard"] 