"""
Control Layer - Business logic for handling different user inputs and generating responses
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class InputType(Enum):
    """Types of user input"""
    QUESTION = "question"
    REQUEST = "request"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    COMMAND = "command"
    CATEGORY_SELECTION = "category_selection"
    REQUIREMENTS = "requirements"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"

class ResponseType(Enum):
    """Types of system responses"""
    ANSWER = "answer"
    ACTION = "action"
    QUESTION = "question"
    CONFIRMATION = "confirmation"
    ERROR = "error"
    GUIDANCE = "guidance"
    SUGGESTION = "suggestion"

@dataclass
class UserInput:
    """Represents user input with classification"""
    text: str
    input_type: InputType
    confidence: float
    extracted_data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SystemResponse:
    """Represents system response"""
    response_type: ResponseType
    content: str
    actions: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ControlLayer:
    """Handles business logic and user input processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.input_processors: Dict[InputType, Callable] = {}
        self.response_generators: Dict[ResponseType, Callable] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Register default processors and generators
        self._register_default_processors()
        self._register_default_generators()
    
    def process_user_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> UserInput:
        """Process and classify user input"""
        # Check if category is already selected in context (button-based approach)
        if context and context.get("selected_category"):
            # If category is already selected, treat this as requirements gathering
            input_type = InputType.REQUIREMENTS
            confidence = 0.9
        else:
            # Classify input type normally
            input_type, confidence = self._classify_input(text)
        
        # Extract relevant data
        extracted_data = self._extract_data(text, input_type, context)
        
        user_input = UserInput(
            text=text,
            input_type=input_type,
            confidence=confidence,
            extracted_data=extracted_data
        )
        
        # Process with specific processor if available
        if input_type in self.input_processors:
            try:
                processed_input = self.input_processors[input_type](user_input, context)
                if processed_input:
                    user_input = processed_input
            except Exception as e:
                self.logger.error(f"Error processing input with {input_type} processor: {e}")
        
        # Log conversation
        self.conversation_history.append({
            "timestamp": user_input.timestamp,
            "type": "user_input",
            "input_type": input_type.value,
            "text": text,
            "confidence": confidence,
            "extracted_data": extracted_data
        })
        
        return user_input
    
    def generate_response(self, user_input: UserInput, context: Optional[Dict[str, Any]] = None) -> SystemResponse:
        """Generate appropriate system response"""
        
        # Determine response type based on input type
        response_type = self._determine_response_type(user_input)
        
        # Generate response content
        content = self._generate_response_content(user_input, response_type, context)
        
        # Determine actions to take
        actions = self._determine_actions(user_input, response_type, context)
        
        # Create response
        response = SystemResponse(
            response_type=response_type,
            content=content,
            actions=actions,
            metadata={
                "input_type": user_input.input_type.value,
                "confidence": user_input.confidence,
                "context": context or {}
            }
        )
        
        # Log conversation
        self.conversation_history.append({
            "timestamp": response.timestamp,
            "type": "system_response",
            "response_type": response_type.value,
            "content": content,
            "actions": actions
        })
        
        return response
    
    def _classify_input(self, text: str) -> tuple[InputType, float]:
        """Classify user input type"""
        text_lower = text.lower().strip()
        
        # Category selection patterns
        category_patterns = [
            r"\b(landing|login|signup|sign-up|profile|about|dashboard)\b",
            r"\b(want|need|create|build|make)\s+(a\s+)?(landing|login|signup|profile|about|dashboard)\b"
        ]
        
        for pattern in category_patterns:
            if re.search(pattern, text_lower):
                return InputType.CATEGORY_SELECTION, 0.9
        
        # Question patterns
        question_patterns = [
            r"\b(what|how|why|when|where|which|can|could|would|should)\b",
            r"\?$",
            r"\b(explain|tell me|show me|help)\b"
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                return InputType.QUESTION, 0.8
        
        # Request patterns
        request_patterns = [
            r"\b(please|can you|could you|would you)\b",
            r"\b(create|build|make|generate|design)\b",
            r"\b(i want|i need|i would like)\b"
        ]
        
        for pattern in request_patterns:
            if re.search(pattern, text_lower):
                return InputType.REQUEST, 0.7
        
        # Complaint patterns
        complaint_patterns = [
            r"\b(don't like|hate|dislike|not working|broken|error|problem)\b",
            r"\b(bad|terrible|awful|horrible)\b",
            r"\b(complaint|issue|bug)\b"
        ]
        
        for pattern in complaint_patterns:
            if re.search(pattern, text_lower):
                return InputType.COMPLAINT, 0.8
        
        # Feedback patterns
        feedback_patterns = [
            r"\b(feedback|suggestion|improve|better|change)\b",
            r"\b(like|love|good|great|excellent)\b",
            r"\b(not bad|okay|fine)\b"
        ]
        
        for pattern in feedback_patterns:
            if re.search(pattern, text_lower):
                return InputType.FEEDBACK, 0.7
        
        # Command patterns
        command_patterns = [
            r"\b(start|stop|restart|reset|clear|delete|remove)\b",
            r"\b(save|export|download|upload)\b",
            r"\b(next|previous|back|forward)\b"
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, text_lower):
                return InputType.COMMAND, 0.6
        
        # Default to question if uncertain
        return InputType.QUESTION, 0.5
    
    def _extract_data(self, text: str, input_type: InputType, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract relevant data from user input"""
        extracted_data = {}
        
        if input_type == InputType.CATEGORY_SELECTION:
            # Extract category
            categories = ["landing", "login", "signup", "sign-up", "profile", "about", "dashboard"]
            for category in categories:
                if category in text.lower():
                    extracted_data["category"] = category
                    break
        
        elif input_type == InputType.REQUEST:
            # Extract requirements
            requirement_keywords = ["modern", "minimal", "responsive", "user-friendly", "professional", "colorful", "dark", "light"]
            found_keywords = [kw for kw in requirement_keywords if kw in text.lower()]
            if found_keywords:
                extracted_data["style_preferences"] = found_keywords
            
            # Extract features
            feature_keywords = ["social login", "form", "gallery", "hero section", "navigation", "footer"]
            found_features = [feature for feature in feature_keywords if feature in text.lower()]
            if found_features:
                extracted_data["features"] = found_features
        
        elif input_type == InputType.COMPLAINT:
            # Extract complaint details
            extracted_data["complaint_type"] = "general"
            if "not working" in text.lower() or "broken" in text.lower():
                extracted_data["complaint_type"] = "technical"
            elif "don't like" in text.lower() or "hate" in text.lower():
                extracted_data["complaint_type"] = "preference"
        
        elif input_type == InputType.FEEDBACK:
            # Extract sentiment
            positive_words = ["like", "love", "good", "great", "excellent", "amazing"]
            negative_words = ["don't like", "hate", "bad", "terrible", "awful"]
            
            if any(word in text.lower() for word in positive_words):
                extracted_data["sentiment"] = "positive"
            elif any(word in text.lower() for word in negative_words):
                extracted_data["sentiment"] = "negative"
            else:
                extracted_data["sentiment"] = "neutral"
        
        return extracted_data
    
    def _determine_response_type(self, user_input: UserInput) -> ResponseType:
        """Determine appropriate response type"""
        if user_input.input_type == InputType.QUESTION:
            return ResponseType.ANSWER
        elif user_input.input_type == InputType.REQUEST:
            return ResponseType.ACTION
        elif user_input.input_type == InputType.COMPLAINT:
            return ResponseType.GUIDANCE
        elif user_input.input_type == InputType.FEEDBACK:
            return ResponseType.CONFIRMATION
        elif user_input.input_type == InputType.COMMAND:
            return ResponseType.ACTION
        elif user_input.input_type == InputType.CATEGORY_SELECTION:
            return ResponseType.CONFIRMATION
        else:
            return ResponseType.GUIDANCE
    
    def _generate_response_content(self, user_input: UserInput, response_type: ResponseType, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response content based on input and type"""
        
        if response_type in self.response_generators:
            try:
                return self.response_generators[response_type](user_input, context)
            except Exception as e:
                self.logger.error(f"Error generating response with {response_type} generator: {e}")
        
        # Default response generation
        if user_input.input_type == InputType.CATEGORY_SELECTION:
            category = user_input.extracted_data.get("category", "unknown")
            return f"Great choice! I'll help you create a {category} page. Let me ask you a few questions to understand your requirements better."
        
        elif user_input.input_type == InputType.QUESTION:
            return "I'd be happy to help! Could you please provide more details about what you'd like to know?"
        
        elif user_input.input_type == InputType.REQUEST:
            return "I understand you'd like me to help with that. Let me gather some information to better assist you."
        
        elif user_input.input_type == InputType.COMPLAINT:
            return "I'm sorry to hear that. Let me help you resolve this issue. Could you provide more details?"
        
        elif user_input.input_type == InputType.FEEDBACK:
            sentiment = user_input.extracted_data.get("sentiment", "neutral")
            if sentiment == "positive":
                return "Thank you for your positive feedback! I'm glad I could help."
            elif sentiment == "negative":
                return "I appreciate your feedback. Let me know how I can improve to better serve you."
            else:
                return "Thank you for your feedback. I'll use it to improve my responses."
        
        else:
            return "I'm here to help! How can I assist you today?"
    
    def _determine_actions(self, user_input: UserInput, response_type: ResponseType, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Determine actions to take based on input and response type"""
        actions = []
        
        if user_input.input_type == InputType.CATEGORY_SELECTION:
            category = user_input.extracted_data.get("category")
            if category:
                actions.append({
                    "type": "set_category",
                    "data": {"category": category}
                })
                actions.append({
                    "type": "start_requirements_gathering",
                    "data": {"category": category}
                })
        
        elif user_input.input_type == InputType.COMMAND:
            command = user_input.text.lower()
            if "restart" in command or "reset" in command:
                actions.append({
                    "type": "reset_conversation",
                    "data": {}
                })
            elif "save" in command or "export" in command:
                actions.append({
                    "type": "export_project",
                    "data": {}
                })
        
        elif user_input.input_type == InputType.COMPLAINT:
            actions.append({
                "type": "log_complaint",
                "data": {
                    "complaint_type": user_input.extracted_data.get("complaint_type", "general"),
                    "text": user_input.text
                }
            })
        
        return actions
    
    def _register_default_processors(self):
        """Register default input processors"""
        
        def process_category_selection(user_input: UserInput, context: Optional[Dict[str, Any]] = None) -> UserInput:
            """Process category selection input"""
            category = user_input.extracted_data.get("category")
            if category:
                # Normalize category name
                if category == "sign-up":
                    category = "signup"
                
                user_input.extracted_data["category"] = category
                user_input.confidence = 0.95  # High confidence for category selection
            
            return user_input
        
        def process_requirements(user_input: UserInput, context: Optional[Dict[str, Any]] = None) -> UserInput:
            """Process requirements input"""
            # Extract more detailed requirements
            text_lower = user_input.text.lower()
            
            # Extract target audience
            audience_patterns = [
                r"for\s+(business|corporate|startup|personal|portfolio)",
                r"target\s+(audience|users?)\s+(?:is|are)\s+([^,.]+)",
                r"aimed\s+at\s+([^,.]+)"
            ]
            
            for pattern in audience_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    user_input.extracted_data["target_audience"] = match.group(1)
                    break
            
            return user_input
        
        self.input_processors[InputType.CATEGORY_SELECTION] = process_category_selection
        self.input_processors[InputType.REQUIREMENTS] = process_requirements
    
    def _register_default_generators(self):
        """Register default response generators"""
        
        def generate_confirmation_response(user_input: UserInput, context: Optional[Dict[str, Any]] = None) -> str:
            """Generate confirmation response"""
            if user_input.input_type == InputType.CATEGORY_SELECTION:
                category = user_input.extracted_data.get("category", "page")
                return f"Perfect! I'll help you create a {category} page. Let me ask you a few questions to understand your specific requirements and preferences."
            
            return "I understand. Let me help you with that."
        
        def generate_guidance_response(user_input: UserInput, context: Optional[Dict[str, Any]] = None) -> str:
            """Generate guidance response"""
            if user_input.input_type == InputType.COMPLAINT:
                complaint_type = user_input.extracted_data.get("complaint_type", "general")
                if complaint_type == "technical":
                    return "I understand there's a technical issue. Let me help you troubleshoot this. Could you provide more details about what's not working?"
                elif complaint_type == "preference":
                    return "I understand your preference. Let me help you find a better solution. What specific aspects would you like to change?"
                else:
                    return "I'm sorry to hear that. Let me help you resolve this issue. Could you provide more details?"
            
            return "I'm here to help! How can I assist you today?"
        
        def generate_action_response(user_input: UserInput, context: Optional[Dict[str, Any]] = None) -> str:
            """Generate action response"""
            if user_input.input_type == InputType.REQUEST:
                return "I'll help you with that request. Let me gather the necessary information and take the appropriate actions."
            
            elif user_input.input_type == InputType.COMMAND:
                command = user_input.text.lower()
                if "restart" in command or "reset" in command:
                    return "I'll restart our conversation. We can begin fresh with your requirements."
                elif "save" in command or "export" in command:
                    return "I'll help you save/export your project. Let me prepare the necessary files."
            
            return "I'll take care of that for you."
        
        self.response_generators[ResponseType.CONFIRMATION] = generate_confirmation_response
        self.response_generators[ResponseType.GUIDANCE] = generate_guidance_response
        self.response_generators[ResponseType.ACTION] = generate_action_response
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        total_interactions = len(self.conversation_history)
        
        input_type_counts = {}
        response_type_counts = {}
        
        for entry in self.conversation_history:
            if entry["type"] == "user_input":
                input_type = entry["input_type"]
                input_type_counts[input_type] = input_type_counts.get(input_type, 0) + 1
            elif entry["type"] == "system_response":
                response_type = entry["response_type"]
                response_type_counts[response_type] = response_type_counts.get(response_type, 0) + 1
        
        return {
            "total_interactions": total_interactions,
            "input_type_distribution": input_type_counts,
            "response_type_distribution": response_type_counts,
            "recent_interactions": self.conversation_history[-10:] if self.conversation_history else []
        }
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared") 