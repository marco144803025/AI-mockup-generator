from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

class UserProxyAgent(BaseAgent):
    """User Proxy Agent - Handles user interactions and formats responses"""
    
    def __init__(self):
        system_message = """You are a User Proxy Agent specialized in:
1. Understanding user intent and context
2. Formatting responses for optimal user experience
3. Managing conversation flow and state
4. Providing clear, actionable feedback

You focus on user interaction and response formatting.
Do NOT use any emojis or special characters - use plain text only."""
        
        super().__init__("UserProxy", system_message)
        self.tool_utility = ToolUtility("user_proxy_agent")
        self.keyword_manager = KeywordManager()
        
        # Initialize logger
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Now that self.db is available, get database constraints
        try:
            categories = self.db.templates.distinct('category')
            metadata_categories = self.db.templates.distinct('metadata.category')
            all_categories = list(set(categories + metadata_categories))
            all_categories = [cat for cat in all_categories if cat]
            
            # Get available tags
            all_tags = []
            templates = list(self.db.templates.find())
            for template in templates:
                tags = template.get('tags', [])
                if tags:
                    all_tags.extend(tags)
            unique_tags = list(set(all_tags))
            
            # Update system message with database constraints
            updated_system_message = f"""You are a User Proxy Agent responsible for:
1. Understanding user requirements and confirming them
2. Coordinating the workflow between different phases
3. Managing user approvals and feedback
4. Ensuring smooth transitions between agents
5. Providing clear explanations for agent decisions

DATABASE CONSTRAINTS - You can ONLY work with these available options:
- Available Categories: {', '.join(all_categories)}
- Available Design Tags: {', '.join(unique_tags[:50])}... (and {len(unique_tags)-50} more)

IMPORTANT RULES:
1. Only ask questions about categories and design elements that exist in the database
2. If user requests something not available, suggest alternatives from the available options
3. Always be conversational, helpful, and explain the reasoning behind recommendations
4. Ask for user confirmation before proceeding with critical decisions
5. Guide users toward the available design options in your database
6. Do NOT use any emojis or special characters - use plain text only"""
            
            # Update the system message in the base agent
            self.system_message = updated_system_message
            
        except Exception as e:
            print(f"Warning: Could not load database constraints for UserProxyAgent: {e}")
            # Continue with basic system message

    def create_response_from_instructions(self, instructions, final_data=None):
        """Create user-friendly responses based on instructions - backward compatible"""
        try:
            # Handle backward compatibility - old format had 3 arguments
            if final_data is not None:
                # Old format: create_response_from_instructions(instructions, final_data)
                return self._create_legacy_response(instructions, final_data)
            else:
                # New format: create_response_from_instructions(instructions)
                if isinstance(instructions, dict):
                    return self._create_enhanced_response(instructions)
                else:
                    # Fallback for string instructions
                    return self._create_legacy_response(instructions, {})
                    
        except Exception as e:
            self.logger.error(f"Error creating response from instructions: {e}")
            return "I understand your request. Let me process that for you."

    def _create_legacy_response(self, instructions: str, final_data: Dict[str, Any]) -> str:
        """Create response using the old format for backward compatibility"""
        try:
            # Use the instructions to create a conversational response
            if "template recommendations" in instructions.lower():
                templates = final_data.get("templates", [])
                targeted_questions = final_data.get("targeted_questions", {})
                
                if templates and len(templates) > 0:
                    questions = targeted_questions.get("questions", [])
                    template_count = len(templates)
                    
                    if questions and template_count > 1:
                        # Interactive questioning approach
                        response = f"I found {template_count} great templates that match your requirements! To help you choose the perfect one, I'd like to ask a few quick questions:\n\n"
                        
                        for i, question_data in enumerate(questions[:2]):  # Show top 2 questions
                            question = question_data.get("question", "")
                            response += f"{i+1}. {question}\n"
                        
                        response += f"\nYou can also:\n- Answer any of these questions to narrow down your options\n- Say 'show me all templates' to see the full list\n- Choose a template directly by name or number"
                        
                    else:
                        # Direct template presentation
                        response = f"I found {template_count} great templates for you! Here are the top recommendations:\n\n"
                        for i, template_data in enumerate(templates[:3]):
                            # Handle both direct template objects and scored template objects
                            if isinstance(template_data, dict):
                                if "template" in template_data:
                                    # This is a scored template object
                                    template = template_data["template"]
                                    score = template_data.get("score", 0)
                                else:
                                    # This is a direct template object
                                    template = template_data
                                    score = 0
                            else:
                                template = template_data
                                score = 0
                            
                            template_name = template.get('name', 'Template')
                            template_description = template.get('description', 'No description')
                            
                            response += f"{i+1}. {template_name} - {template_description}"
                            if score > 0:
                                response += f" (Match: {score:.1%})"
                            response += "\n"
                        
                        response += "\nTo proceed, please choose a template by saying its name or number, or ask for more details about any template."
                else:
                    response = "I couldn't find any templates that match your requirements. Could you please provide more specific details about what you're looking for?"
            
            elif "clarification_needed" in instructions.lower():
                error_type = final_data.get("error_type", "general_error")
                error_message = final_data.get("error_message", "")
                clarification_questions = final_data.get("clarification_questions", [])
                
                if error_type == "agent_execution_failed":
                    response = f"I encountered an issue while processing your request: {error_message}\n\n"
                else:
                    response = "I need some clarification to better assist you.\n\n"
                
                if clarification_questions:
                    response += "Please help me understand:\n"
                    for i, question in enumerate(clarification_questions, 1):
                        response += f"{i}. {question}\n"
                else:
                    response += "Could you please provide more specific details about what you're looking for?"
            
            elif "no_templates_found" in instructions.lower():
                response = "I couldn't find any templates that match your requirements. Let me show you all available options or you can modify your requirements."
            
            elif "template_selection_error" in instructions.lower():
                available_templates = final_data.get("available_templates", [])
                
                response = "I couldn't determine which template you want to select. Could you please be more specific?\n\n"
                
                if available_templates:
                    response += "Available options:\n"
                    for i, template in enumerate(available_templates[:3], 1):
                        template_name = template.get("name", f"Template {i}")
                        response += f"{i}. {template_name}\n"
                
                response += "\nYou can:\n- Choose by number: 'I want template 1' or 'option 2'\n- Choose by name: 'I want Landing 1' or 'Login 2'\n- Ask for different options: 'show me other templates'"
            
            elif "present_filtered_recommendations" in instructions.lower():
                templates = final_data.get("templates", [])
                targeted_questions = final_data.get("targeted_questions", {})
                
                if templates and len(templates) > 0:
                    questions = targeted_questions.get("questions", [])
                    template_count = len(templates)
                    
                    if template_count == 1:
                        # Only one template left - suggest selection
                        template = templates[0].get("template", templates[0])
                        template_name = template.get("name", "Template")
                        template_description = template.get("description", "No description")
                        
                        response = f"Perfect! Based on your preferences, I found the ideal template for you:\n\n{template_name} - {template_description}\n\nThis template matches all your requirements perfectly. Would you like to select this template? You can say 'yes' or the template name to proceed."
                    
                    elif questions and template_count > 1:
                        # Still multiple templates - continue questioning
                        response = f"Great! I've narrowed it down to {template_count} templates based on your preferences. Let me ask one more question to find the perfect match:\n\n"
                        
                        for i, question_data in enumerate(questions[:1]):  # Show top 1 question
                            question = question_data.get("question", "")
                            response += f"{question}\n"
                        
                        response += f"\nYou can also:\n- Answer this question to narrow down further\n- Say 'show me all {template_count} templates' to see the full list\n- Choose a template directly by name or number"
                    
                    else:
                        # No more questions - show templates
                        response = f"Based on your preferences, here are the {template_count} best templates:\n\n"
                        for i, template_data in enumerate(templates[:3]):
                            if isinstance(template_data, dict):
                                if "template" in template_data:
                                    template = template_data["template"]
                                    score = template_data.get("score", 0)
                                else:
                                    template = template_data
                                    score = 0
                            else:
                                template = template_data
                                score = 0
                            
                            template_name = template.get('name', 'Template')
                            template_description = template.get('description', 'No description')
                            
                            response += f"{i+1}. {template_name} - {template_description}"
                            if score > 0:
                                response += f" (Match: {score:.1%})"
                            response += "\n"
                        
                        response += "\nPlease choose a template by saying its name or number."
                else:
                    response = "I couldn't find any templates that match your specific preferences. Let me show you all available options."
            
            elif "template selection" in instructions.lower() or "selected_template" in final_data:
                selected_template = final_data.get("selected_template", {})
                
                if selected_template:
                    template_name = selected_template.get("name", "the selected template")
                    
                    response = f"Perfect! I've confirmed your selection of {template_name}.\n\nYour template is ready! I've generated a complete UI mockup with all the features you requested.\n\nYou can now:\n- View the preview of your mockup\n- Download the code files\n- Make any modifications you'd like\n- Get a detailed report of the project\n\nWhat would you like to do next?"
                else:
                    response = "I couldn't identify which template you selected. Please specify the template name or number (1, 2, 3, etc.)."
            
            elif "modification_success" in instructions.lower():
                modification_result = final_data.get("modification_result", {})
                changes_summary = final_data.get("changes_summary", [])
                
                response = "Great news - your modification was successful! The changes you requested have been applied smoothly and everything is set up just as you wanted.\n\nWhat's next?\n- Your updates are now live and ready to go\n- You can continue working on your project with the new modifications in place\n- Feel free to review the changes to confirm everything looks perfect\n\nIs there anything else I can help you with today? I'm here to make your experience as smooth as possible!"
                
                if changes_summary and len(changes_summary) > 0:
                    response = "I've successfully applied your modifications!\n\nChanges Made:\n"
                    for change in changes_summary[:5]:  # Limit to 5 changes
                        response += f"- {change}\n"
                    response += "\nThe changes have been applied to your template. You can continue making modifications or ask me to generate a report when you're satisfied."
            
            else:
                response = instructions
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creating legacy response: {e}")
            return f"I'm having trouble processing that right now. Could you please try again? (Error: {str(e)})"

    def _create_enhanced_response(self, instructions: Dict[str, Any]) -> str:
        """Create response using the new enhanced format for Phase 2 editing"""
        try:
            response_type = instructions.get("type", "general")
            
            if response_type == "modification_success":
                return self._create_modification_success_response(instructions)
            elif response_type == "phase_transition_complete":
                selected_template = instructions.get("selected_template", {})
                
                response = f"Perfect! I've successfully prepared your selected template for editing.\n\nTemplate Selected: {selected_template.get('name', 'Unknown')}\nCategory: {selected_template.get('category', 'Unknown')}\n\nI've automatically:\n- Saved our conversation history\n- Fetched the template code from the database\n- Created a JSON file with all the UI components\n- Prepared everything for the editing phase\n\nYou're now ready to move to the UI Editor where you can:\n- View your template in real-time\n- Make modifications through our chat interface\n- See the code changes instantly\n- Export your final design\n\nThe system will now transition you to the editing interface. You'll see your template loaded and ready for customization!"
                return response
            elif response_type == "editing_clarification_needed":
                return self._create_clarification_needed_response(instructions)
            elif response_type == "editing_clarification_invalid_choice":
                return self._create_clarification_invalid_choice_response(instructions)
            elif response_type == "clarification_needed":
                return self._create_requirements_clarification_response(instructions)
            elif response_type == "requirements_analysis_complete":
                return self._create_requirements_complete_response(instructions)
            else:
                return self._create_default_response(instructions)
                
        except Exception as e:
            self.logger.error(f"Error creating enhanced response: {e}")
            return "I understand your request. Let me process that for you."

    def _create_modification_success_response(self, instructions: Dict[str, Any]) -> str:
        """Create precise, tailored response for successful modifications"""
        try:
            user_message = instructions.get("user_message", "")
            
            # Simple, direct response without emojis
            if user_message:
                return f"Perfect! I've applied the changes you requested ('{user_message}'). The modifications have been successfully implemented. What would you like to change next, or would you like me to generate a detailed report?"
            else:
                return "Perfect! I've applied your modifications successfully. What would you like to change next, or would you like me to generate a detailed report?"
                
        except Exception as e:
            self.logger.error(f"Error creating modification success response: {e}")
            return "Perfect! I've applied your modifications successfully. What would you like to change next?"

    def _create_clarification_needed_response(self, instructions: Dict[str, Any]) -> str:
        """Create response when clarification is needed for UI editing"""
        try:
            error_message = instructions.get("error_message", "Multiple possible targets found")
            clarification_options = instructions.get("clarification_options", [])
            original_request = instructions.get("original_request", "")
            
            response = f"I found multiple elements that could match your request '{original_request}'. Please specify which one you'd like me to modify:\n\n"
            
            for i, option in enumerate(clarification_options, 1):
                text_content = option.get("text_content", f"Option {i}")
                css_selector = option.get("css_selector", "")
                description = option.get("description", "")
                
                response += f"{i}. {text_content}"
                if css_selector:
                    response += f" (CSS: {css_selector})"
                if description:
                    response += f" - {description}"
                response += "\n"
            
            response += "\nPlease choose by number (1, 2, 3, etc.) or describe which element you want to modify."
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creating clarification needed response: {e}")
            return "I found multiple possible targets for your request. Please specify which element you'd like me to modify."

    def _create_clarification_invalid_choice_response(self, instructions: Dict[str, Any]) -> str:
        """Create response when user's clarification choice is invalid"""
        try:
            clarification_options = instructions.get("clarification_options", [])
            user_message = instructions.get("user_message", "")
            original_request = instructions.get("original_request", "")
            
            response = f"I didn't understand your choice '{user_message}'. Please select one of the following options:\n\n"
            
            for i, option in enumerate(clarification_options, 1):
                text_content = option.get("text_content", f"Option {i}")
                css_selector = option.get("css_selector", "")
                description = option.get("description", "")
                
                response += f"{i}. {text_content}"
                if css_selector:
                    response += f" (CSS: {css_selector})"
                if description:
                    response += f" - {description}"
                response += "\n"
            
            response += "\nYou can choose by:\n- Number (1, 2, 3, etc.)\n- Text content\n- CSS selector\n- Description"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creating clarification invalid choice response: {e}")
            return "I didn't understand your choice. Please select one of the numbered options above."

    def _create_requirements_clarification_response(self, instructions: Dict[str, Any]) -> str:
        """Create response when clarification questions are needed for requirements"""
        try:
            clarification_questions = instructions.get("clarification_questions", [])
            requirements_data = instructions.get("requirements_data", {})
            page_type = requirements_data.get("page_type", "UI")
            
            response = f"Great! I've analyzed your requirements for the {page_type} UI. To help you choose the perfect template, I have a few questions:\n\n"
            
            for i, question in enumerate(clarification_questions[:3], 1):
                response += f"{i}. {question}\n"
            
            response += "\nPlease answer any of these questions to help me find the best template for you."
            
            return response
             
        except Exception as e:
            self.logger.error(f"Error creating requirements clarification response: {e}")
            return "I need some clarification to better understand your requirements. Could you please provide more specific details?"

    def _create_requirements_complete_response(self, instructions: Dict[str, Any]) -> str:
        """Create response when requirements analysis is complete"""
        try:
            requirements_data = instructions.get("requirements_data", {})
            page_type = requirements_data.get("page_type", "UI")
            
            response = f"Perfect! I've analyzed your requirements for the {page_type} UI. "
            
            # Add some context about what was analyzed
            if "target_audience" in requirements_data:
                response += f"Based on your target audience ({requirements_data['target_audience']}) and "
            
            if "style_preferences" in requirements_data:
                styles = ", ".join(requirements_data["style_preferences"])
                response += f"style preferences ({styles}), "
            
            response += "I'm ready to show you the best templates that match your needs. Let me fetch the available options for you."
            
            return response
             
        except Exception as e:
            self.logger.error(f"Error creating requirements complete response: {e}")
            return "I've processed your requirements. Let me show you the available templates."

    def _create_default_response(self, instructions: Dict[str, Any]) -> str:
        """Create default response when type is not recognized"""
        try:
            user_message = instructions.get("user_message", "")
             
            if user_message:
                return f"I understand you want to '{user_message}'. Let me help you with that!"
            else:
                return "I'm here to help you edit your UI. What would you like to change?"
                 
        except Exception as e:
            self.logger.error(f"Error creating default response: {e}")
            return "I'm here to help you edit your UI. What would you like to change?"