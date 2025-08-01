"""
Enhanced Chain-of-Thought Orchestrator - Intelligently guides user proxy agent with strategic thinking
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
import anthropic
import os
import json

class SimpleOrchestrator:
    """Enhanced orchestrator with Chain-of-Thought reasoning to guide user proxy agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_id = str(uuid.uuid4())
        
        # Initialize Claude client
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Session state with reasoning tracking
        self.session_state = {
            "session_id": self.session_id,
            "created_at": datetime.now(),
            "current_phase": "phase_1_requirements",  # Start with phase 1
            "selected_category": None,
            "conversation_history": [],
            "project_state": {
                "phase_1": {
                    "requirements_gathered": False,
                    "template_selected": False,
                    "user_satisfied": False,
                    "selected_template": None,
                    "gathered_requirements": {}
                },
                "phase_2": {
                    "editing_requested": False,
                    "changes_made": [],
                    "user_satisfied": False
                },
                "phase_3": {
                    "report_generated": False,
                    "report_data": {}
                }
            },
            "reasoning_chain": [],
            "agent_guidance": {},
            "message_analysis": {}
        }
        
        self.logger.info(f"Enhanced COT Orchestrator initialized with session ID: {self.session_id}")
    
    async def process_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main entry point with Chain-of-Thought reasoning and phase management"""
        try:
            # Update context with current phase and project state
            if context is None:
                context = {}
            context["current_phase"] = self.session_state["current_phase"]
            context["project_state"] = self.session_state["project_state"]
            
            # Step 1: Orchestrator analyzes the message and context
            analysis_result = await self._analyze_message_with_cot(message, context)
            
            # Step 2: Orchestrator determines strategic response approach
            strategy_result = await self._determine_response_strategy_with_cot(analysis_result, context)
            
            # Step 3: Orchestrator generates guided response
            response_result = await self._generate_guided_response_with_cot(message, strategy_result, context)
            
            # Step 4: Check for phase transitions
            phase_transition = await self._check_phase_transition(message, analysis_result, context)
            
            # Step 5: Store reasoning chain
            self._store_reasoning_chain(analysis_result, strategy_result, response_result)
            
            return {
                "success": True,
                "response": response_result["response"],
                "session_id": self.session_id,
                "metadata": {
                    "category": self.session_state["selected_category"],
                    "phase": self.session_state["current_phase"],
                    "phase_transition": phase_transition,
                    "message_type": analysis_result.get("message_type"),
                    "reasoning_chain": self.session_state["reasoning_chain"][-3:],  # Last 3 reasoning steps
                    "orchestrator_thinking": {
                        "analysis": analysis_result.get("thinking"),
                        "strategy": strategy_result.get("thinking"),
                        "response_guidance": response_result.get("thinking")
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in enhanced COT process: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    async def _analyze_message_with_cot(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Step 1: Analyze message with Chain-of-Thought reasoning"""
        
        analysis_prompt = f"""You are an intelligent orchestrator analyzing a user message to determine how to guide a UI mockup assistant.

**MESSAGE TO ANALYZE:**
"{message}"

**CONTEXT:**
- Selected Category: {context.get('selected_category', 'None') if context else 'None'}
- Current Phase: {context.get('current_phase', 'phase_1_requirements') if context else 'phase_1_requirements'}

**PHASE CONTEXT:**
**Phase 1 - Requirements Gathering**: User selects category, assistant asks for requirements, system selects suitable template
**Phase 2 - Template Editing**: User can request changes to selected template (future development)
**Phase 3 - Report Generation**: System generates standardized report with template preview and reasoning

**ANALYSIS TASK:**
Use Chain-of-Thought reasoning to analyze this UI mockup message and determine:
1. What type of mockup-related message is this?
2. What is the user's mockup building intent?
3. What phase of the mockup creation process are they in?
4. What specific mockup requirements does the assistant need to gather?
5. Is this message indicating a phase transition?

**THINKING PROCESS:**
1. **ANALYZE**: What is the user saying about building a UI mockup?
2. **CLASSIFY**: What type of mockup message is this (question, requirement, feedback, command, phase_transition)?
3. **CONTEXTUALIZE**: How does the current phase and selected category affect interpretation?
4. **INTENT**: What mockup goal does the user want to achieve?
5. **PHASE_CHECK**: Is the user ready to move to the next phase or still in current phase?
6. **GUIDANCE**: What specific requirements should I ask the assistant to gather for template selection?

**RESPONSE FORMAT:**
**THINKING:**
[Your step-by-step reasoning about mockup requirement analysis and phase assessment]

**ANALYSIS:**
{{
    "message_type": "question|requirement|feedback|command|clarification|phase_transition",
    "user_intent": "string describing mockup building goal",
    "current_phase": "phase_1_requirements|phase_2_editing|phase_3_report",
    "phase_ready": true|false,
    "assistant_guidance": "specific mockup requirement gathering instructions",
    "priority_questions": ["list of key mockup requirement questions to ask"],
    "next_steps": ["list of recommended mockup building actions"]
}}"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": analysis_prompt}],
                system="You are an intelligent orchestrator that analyzes user messages with Chain-of-Thought reasoning.",
                max_tokens=1500
            )
            
            # Extract thinking and analysis
            response_text = response.content[0].text
            thinking, analysis_json = self._extract_thinking_and_json(response_text)
            
            return {
                "thinking": thinking,
                "analysis": json.loads(analysis_json) if analysis_json else {},
                "raw_response": response_text
            }
            
        except Exception as e:
            self.logger.error(f"Error in message analysis: {e}")
            return {
                "thinking": "Error in analysis",
                "analysis": {"message_type": "general", "user_intent": "unknown"},
                "raw_response": str(e)
            }
    
    async def _determine_response_strategy_with_cot(self, analysis_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Step 2: Determine strategic response approach with Chain-of-Thought reasoning"""
        
        analysis = analysis_result.get("analysis", {})
        
        strategy_prompt = f"""You are an intelligent orchestrator determining the best response strategy for a UI mockup assistant.

**MESSAGE ANALYSIS:**
{json.dumps(analysis, indent=2)}

**CONTEXT:**
- Selected Category: {context.get('selected_category', 'None') if context else 'None'}
- Current Phase: {context.get('current_phase', 'initial') if context else 'initial'}

**STRATEGY TASK:**
Use Chain-of-Thought reasoning to determine the optimal mockup building response strategy:

**THINKING PROCESS:**
1. **EVALUATE**: What is the user's current mockup building state and needs?
2. **CONSIDER**: What are the best practices for gathering mockup requirements and template selection?
3. **PLAN**: What sequence of mockup requirement gathering actions should the assistant take?
4. **PRIORITIZE**: What mockup requirements are most important to gather first?
5. **ADAPT**: How should the response be tailored to the mockup category and phase?

**RESPONSE FORMAT:**
**THINKING:**
[Your step-by-step reasoning about mockup building strategy]

**STRATEGY:**
{{
    "response_approach": "direct_answer|questioning|guidance|clarification|next_steps",
    "tone": "professional|friendly|technical|conversational",
    "focus_areas": ["list of key mockup requirement areas to address"],
    "assistant_instructions": "detailed mockup requirement gathering instructions",
    "expected_outcome": "what mockup requirement outcome should happen after this response",
    "follow_up_questions": ["list of mockup requirement questions to ask next"]
}}"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": strategy_prompt}],
                system="You are an intelligent orchestrator that determines response strategies with Chain-of-Thought reasoning.",
                max_tokens=1500
            )
            
            response_text = response.content[0].text
            thinking, strategy_json = self._extract_thinking_and_json(response_text)
            
            return {
                "thinking": thinking,
                "strategy": json.loads(strategy_json) if strategy_json else {},
                "raw_response": response_text
            }
            
        except Exception as e:
            self.logger.error(f"Error in strategy determination: {e}")
            return {
                "thinking": "Error in strategy",
                "strategy": {"response_approach": "direct_answer", "tone": "friendly"},
                "raw_response": str(e)
            }
    
    async def _generate_guided_response_with_cot(self, message: str, strategy_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Step 3: Generate guided response based on orchestrator's strategy"""
        
        strategy = strategy_result.get("strategy", {})
        analysis = strategy_result.get("analysis", {})
        
        guidance_prompt = f"""You are a UI mockup assistant being guided by an intelligent orchestrator.

**ORIGINAL USER MESSAGE:**
"{message}"

**ORCHESTRATOR GUIDANCE:**
- Response Approach: {strategy.get('response_approach', 'direct_answer')}
- Tone: {strategy.get('tone', 'friendly')}
- Focus Areas: {', '.join(strategy.get('focus_areas', ['mockup requirement gathering']))}
- Instructions: {strategy.get('assistant_instructions', 'Gather mockup requirements for template selection')}

**CONTEXT:**
- Selected Category: {context.get('selected_category', 'None') if context else 'None'}
- Current Phase: {context.get('current_phase', 'initial') if context else 'initial'}

**YOUR TASK:**
Generate a concise, focused response to gather basic mockup requirements for template selection.

**IMPORTANT CONSTRAINTS:**
- Keep responses SHORT and CONCISE (2-3 sentences max)
- Focus ONLY on basic visual/style preferences that help select templates
- Avoid asking about technical features, integrations, or complex requirements
- Templates are pre-built UI mockups with different visual styles and layouts
- Ask 1-2 simple questions maximum


**APPROPRIATE QUESTIONS FOR TEMPLATE SELECTION:**
- Style preference: "modern/minimal" vs "colorful/playful" vs "professional/corporate"
- Layout preference: "simple" vs "detailed" vs "hero section focused"
- Color scheme: "light theme" vs "dark theme" vs "colorful"
- Content focus: "text-heavy" vs "visual-focused" vs "balanced"

**AVOID ASKING ABOUT:**
- Technical features, integrations, backend requirements
- User demographics, target audience analysis
- Complex business logic or workflows
- Specific form fields or validation rules

**THINKING PROCESS:**
1. **UNDERSTAND**: What basic visual/style info do I need for template selection?
2. **SIMPLIFY**: What are the available options for the user to choose from within the category? Do I need to access the database to get the options?
3. **VALIDATE**: Is this question relevant to choosing a visual template?

**RESPONSE FORMAT:**
**THINKING:**
[Brief reasoning about template selection approach]

**ANSWER:**
[Short, focused response with 1-2 simple questions about visual preferences]"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": guidance_prompt}],
                system="You are a UI design assistant following intelligent orchestrator guidance with Chain-of-Thought reasoning.",
                max_tokens=2000
            )
            
            response_text = response.content[0].text
            thinking, answer = self._extract_thinking_and_answer(response_text)
            
            return {
                "thinking": thinking,
                "response": answer,
                "raw_response": response_text
            }
            
        except Exception as e:
            self.logger.error(f"Error in guided response generation: {e}")
            return {
                "thinking": "Error in response generation",
                "response": "I'm having trouble processing your request right now. Please try again.",
                "raw_response": str(e)
            }
    
    def _extract_thinking_and_json(self, response_text: str) -> tuple:
        """Extract thinking and JSON from response"""
        thinking = ""
        json_data = ""
        
        if "**THINKING:**" in response_text:
            parts = response_text.split("**THINKING:**")
            if len(parts) > 1:
                thinking_part = parts[1]
                if "**ANALYSIS:**" in thinking_part:
                    thinking = thinking_part.split("**ANALYSIS:**")[0].strip()
                    json_part = thinking_part.split("**ANALYSIS:**")[1].strip()
                    # Try to extract JSON
                    try:
                        start = json_part.find("{")
                        end = json_part.rfind("}") + 1
                        if start != -1 and end != 0:
                            json_data = json_part[start:end]
                    except:
                        pass
                else:
                    thinking = thinking_part.strip()
        
        return thinking, json_data
    
    def _extract_thinking_and_answer(self, response_text: str) -> tuple:
        """Extract thinking and answer from response"""
        thinking = ""
        answer = response_text
        
        if "**THINKING:**" in response_text and "**ANSWER:**" in response_text:
            parts = response_text.split("**THINKING:**")
            if len(parts) > 1:
                thinking_part = parts[1]
                if "**ANSWER:**" in thinking_part:
                    thinking = thinking_part.split("**ANSWER:**")[0].strip()
                    answer = thinking_part.split("**ANSWER:**")[1].strip()
        
        return thinking, answer
    
    async def _check_phase_transition(self, message: str, analysis_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check if the conversation should transition to the next phase"""
        current_phase = self.session_state["current_phase"]
        analysis = analysis_result.get("analysis", {})
        
        transition_prompt = f"""You are an intelligent orchestrator determining if the conversation should transition to the next phase.

**CURRENT PHASE:** {current_phase}
**USER MESSAGE:** "{message}"
**ANALYSIS:** {json.dumps(analysis, indent=2)}

**PHASE DEFINITIONS:**
**Phase 1 - Requirements Gathering**: 
- Goal: Gather requirements and select suitable template
- Complete when: User is satisfied with template selection
- Transition trigger: User expresses satisfaction with template

**Phase 2 - Template Editing**: 
- Goal: Allow user to request changes to selected template
- Complete when: User is satisfied with final template
- Transition trigger: User expresses satisfaction with final template

**Phase 3 - Report Generation**: 
- Goal: Generate standardized report with template preview and reasoning
- Complete when: Report is generated and delivered
- Transition trigger: User requests report or final confirmation

**TRANSITION TASK:**
Use Chain-of-Thought reasoning to determine if a phase transition should occur:

**THINKING PROCESS:**
1. **ASSESS**: What is the current phase and what needs to be completed?
2. **EVALUATE**: Has the current phase been completed successfully?
3. **DETECT**: Does the user message indicate readiness for next phase?
4. **DECIDE**: Should we transition to the next phase?

**RESPONSE FORMAT:**
**THINKING:**
[Your step-by-step reasoning about phase transition]

**TRANSITION:**
{{
    "should_transition": true|false,
    "current_phase": "phase_1_requirements|phase_2_editing|phase_3_report",
    "next_phase": "phase_2_editing|phase_3_report|complete",
    "transition_reason": "string explaining why transition should/should not occur",
    "phase_completion_status": "in_progress|ready|complete"
}}"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": transition_prompt}],
                system="You are an intelligent orchestrator that manages phase transitions with Chain-of-Thought reasoning.",
                max_tokens=1000
            )
            
            response_text = response.content[0].text
            thinking, transition_json = self._extract_thinking_and_json(response_text)
            
            transition_data = json.loads(transition_json) if transition_json else {
                "should_transition": False,
                "current_phase": current_phase,
                "next_phase": current_phase,
                "transition_reason": "No transition needed",
                "phase_completion_status": "in_progress"
            }
            
            # Update phase if transition is needed
            if transition_data.get("should_transition", False):
                self.session_state["current_phase"] = transition_data.get("next_phase", current_phase)
                self.logger.info(f"Phase transition: {current_phase} -> {self.session_state['current_phase']}")
            
            return {
                "thinking": thinking,
                "transition_data": transition_data,
                "raw_response": response_text
            }
            
        except Exception as e:
            self.logger.error(f"Error in phase transition check: {e}")
            return {
                "thinking": "Error in phase transition",
                "transition_data": {
                    "should_transition": False,
                    "current_phase": current_phase,
                    "next_phase": current_phase,
                    "transition_reason": f"Error: {str(e)}",
                    "phase_completion_status": "in_progress"
                },
                "raw_response": str(e)
            }
    
    def _store_reasoning_chain(self, analysis_result: Dict[str, Any], strategy_result: Dict[str, Any], response_result: Dict[str, Any]):
        """Store the reasoning chain for this interaction"""
        reasoning_step = {
            "timestamp": datetime.now().isoformat(),
            "step": "message_processing",
            "analysis_thinking": analysis_result.get("thinking", ""),
            "strategy_thinking": strategy_result.get("thinking", ""),
            "response_thinking": response_result.get("thinking", ""),
            "analysis_data": analysis_result.get("analysis", {}),
            "strategy_data": strategy_result.get("strategy", {})
        }
        
        self.session_state["reasoning_chain"].append(reasoning_step)
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status with reasoning chain"""
        return {
            "session_id": self.session_id,
            "state": "active",
            "session_state": self.session_state,
            "feedback_required": False,
            "recovery_attempts": 0,
            "reasoning_chain_length": len(self.session_state["reasoning_chain"])
        }
    
    def reset_session(self) -> Dict[str, Any]:
        """Reset the session"""
        self.session_id = str(uuid.uuid4())
        self.session_state = {
            "session_id": self.session_id,
            "created_at": datetime.now(),
            "current_phase": "phase_1_requirements",  # Start with phase 1
            "selected_category": None,
            "conversation_history": [],
            "project_state": {
                "phase_1": {
                    "requirements_gathered": False,
                    "template_selected": False,
                    "user_satisfied": False,
                    "selected_template": None,
                    "gathered_requirements": {}
                },
                "phase_2": {
                    "editing_requested": False,
                    "changes_made": [],
                    "user_satisfied": False
                },
                "phase_3": {
                    "report_generated": False,
                    "report_data": {}
                }
            },
            "reasoning_chain": [],
            "agent_guidance": {},
            "message_analysis": {}
        }
        
        return {
            "success": True,
            "message": "Session reset successfully",
            "session_id": self.session_id,
            "current_phase": "phase_1_requirements"
        } 