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

You focus on user interaction and response formatting."""
        
        super().__init__("UserProxy", system_message)
        self.tool_utility = ToolUtility("user_proxy_agent")
        self.keyword_manager = KeywordManager()
        
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
5. Guide users toward the available design options in your database"""
            
            # Update the system message in the base agent
            self.system_message = updated_system_message
            
        except Exception as e:
            print(f"Warning: Could not load database constraints for UserProxyAgent: {e}")
            # Continue with basic system message
    
    def understand_requirements(self, user_prompt: str, logo_image: Optional[str] = None) -> Dict[str, Any]:
        """Phase 1: Understand user requirements and get confirmation"""
        
        # Get database constraints
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
        
        prompt = f"""
        Analyze the user's requirements for a UI mockup:
        
        User Request: {user_prompt}
        
        DATABASE CONSTRAINTS - You can ONLY work with these available options:
        - Available Categories: {', '.join(all_categories)}
        - Available Design Tags: {', '.join(unique_tags[:30])}... (and {len(unique_tags)-30} more)
        
        Please provide a structured analysis including:
        1. Page Type: What type of page they want (MUST be one of: {', '.join(all_categories)})
        2. Style Preferences: Any style mentions (MUST be from available tags)
        3. Key Features: What functionality they need (MUST be from available tags)
        4. Target Audience: Who the page is for
        5. Brand Elements: Any brand-specific requirements (MUST be from available tags)
        
        IMPORTANT: Only suggest categories and design elements that exist in the database.
        If the user requests something not available, suggest the closest alternative from the available options.
        
        Format your response as JSON with these fields:
        {{
            "page_type": "string (must be from available categories)",
            "style_preferences": ["list", "of", "available", "tags"],
            "key_features": ["list", "of", "available", "features"],
            "target_audience": "string",
            "brand_elements": ["list", "of", "available", "elements"],
            "confidence_score": 0.85,
            "questions_for_clarification": ["list", "of", "questions", "within", "database", "constraints"]
        }}
        """
        
        if logo_image:
            prompt += f"\n\nA logo image has been provided. Please analyze it for brand colors, style, and design elements."
        
        # Use CoT-enabled Claude call
        response = self.call_claude_with_cot(prompt, logo_image, enable_cot=True)
        
        # Process the CoT response
        cot_result = self.process_cot_response(response)
        
        try:
            # Try to extract JSON from the answer section
            answer_text = cot_result["answer"]
            if "{" in answer_text and "}" in answer_text:
                start = answer_text.find("{")
                end = answer_text.rfind("}") + 1
                json_str = answer_text[start:end]
                parsed_result = json.loads(json_str)
                
                # Add reasoning to the result
                parsed_result["reasoning"] = cot_result["thinking"]
                return parsed_result
            else:
                # Fallback if no JSON found
                return {
                    "page_type": "landing",
                    "style_preferences": ["modern"],
                    "key_features": ["responsive"],
                    "target_audience": "general",
                    "brand_elements": [],
                    "confidence_score": 0.5,
                    "questions_for_clarification": ["Could you provide more details about your specific needs?"],
                    "reasoning": cot_result["thinking"]
                }
        except json.JSONDecodeError:
            return {
                "page_type": "landing",
                "style_preferences": ["modern"],
                "key_features": ["responsive"],
                "target_audience": "general",
                "brand_elements": [],
                "confidence_score": 0.5,
                "questions_for_clarification": ["Could you provide more details about your specific needs?"],
                "reasoning": cot_result["thinking"],
                "error": "Failed to parse JSON response"
            }
    
    def confirm_requirements(self, requirements: Dict[str, Any]) -> str:
        """Ask user to confirm the understood requirements"""
        
        confirmation_prompt = f"""
        Based on your request, here's what I understand:

        Page Type: {requirements.get('page_type', 'Not specified')}
        Style: {', '.join(requirements.get('style_preferences', ['Not specified']))}
        Key Features: {', '.join(requirements.get('key_features', ['Not specified']))}
        Target Audience: {requirements.get('target_audience', 'Not specified')}

        Is this correct? If so, I'll start finding the perfect templates for you!
        """
        
        return confirmation_prompt
    
    def confirm_template_selection(self, template_info: Dict[str, Any], reasoning: str) -> str:
        """Ask user to confirm template selection"""
        
        confirmation_prompt = f"""
        Template: {template_info.get('title', 'Unknown')}
        Category: {template_info.get('category', 'Unknown')}
        Description: {template_info.get('description', 'No description available')}

        Reasoning for Selection:
        {reasoning}

        Would you like to proceed with this template?
        """
        
        return confirmation_prompt
    
    def template_selected_confirmation(self, template_info: Dict[str, Any]) -> str:
        """Confirm that a template has been selected and provide next steps"""
        
        template_name = template_info.get('name', template_info.get('title', 'the selected template'))
        
        confirmation_prompt = f"""Perfect! I've confirmed your selection of {template_name}.

        I'll now generate a UI preview and prepare the code for you. This may take a moment..."""
        
        return confirmation_prompt
    
    def confirm_master_style(self, template_info: Dict[str, Any]) -> str:
        """Confirm the master style for the template"""
        
        template_name = template_info.get('name', 'Template')
        template_description = template_info.get('description', 'No description')
        
        confirmation_prompt = f"""
        I've selected {template_name} as your template:

        Description: {template_description}

        I'm now generating your UI mockup with all the features you requested. This will include:
        • Responsive design that works on all devices
        • Modern, clean code structure
        • All the functionality you specified
        • Professional styling and layout

        Please wait while I create your mockup...
        """
        
        return confirmation_prompt
    
    def confirm_functionality_requirements(self, interactive_elements: List[str]) -> str:
        """Ask user about functionality requirements for interactive elements"""
        
        confirmation_prompt = f"""
        Great! Let me ask you a few questions to understand your needs better:

        1. Forms: What data should be collected? Where should it be sent?
        2. Buttons: What should happen when clicked?
        3. Navigation: Any special routing requirements?
        4. Authentication: Any login/signup requirements?

        Please let me know what functionality you need!"""
        
        return confirmation_prompt 
    
    def get_database_constraints(self) -> Dict[str, Any]:
        """Get current database constraints for prompt engineering"""
        
        # Get categories
        categories = self.db.templates.distinct('category')
        metadata_categories = self.db.templates.distinct('metadata.category')
        all_categories = list(set(categories + metadata_categories))
        all_categories = [cat for cat in all_categories if cat]
        
        # Get tags
        all_tags = []
        templates = list(self.db.templates.find())
        for template in templates:
            tags = template.get('tags', [])
            if tags:
                all_tags.extend(tags)
        unique_tags = list(set(all_tags))
        
        return {
            'categories': all_categories,
            'tags': unique_tags,
            'templates_count': len(templates)
        }
    
    def ask_constrained_questions(self, category: str) -> List[str]:
        """Ask questions based on available database constraints"""
        constraints = self.get_database_constraints()
        available_tags = constraints.get("available_tags", [])
        
        # Categorize available tags using keyword manager
        styles = []
        themes = []
        features = []
        
        for tag in available_tags:
            if not tag or len(tag) < 2:
                continue
            tag_lower = tag.lower()
            
            # Use keyword manager to categorize tags
            if any(style in tag_lower for style in self.keyword_manager.get_design_style_keywords()["professional_styles"]):
                styles.append(tag)
            elif any(theme in tag_lower for theme in self.keyword_manager.get_design_style_keywords()["theme_keywords"]):
                themes.append(tag)
            elif any(feature in tag_lower for feature in self.keyword_manager.get_component_keywords()["functional_components"]):
                features.append(tag)
        
        questions = []
        
        # Style questions
        if styles:
            questions.append(f"What style do you prefer for your {category} page? Available styles: {', '.join(styles[:5])}...")
        
        # Theme questions
        if themes:
            questions.append(f"What theme would you like? Available themes: {', '.join(themes)}")
        
        # Feature questions
        if features:
            questions.append(f"What key features are most important for your {category} page? Available features: {', '.join(features[:5])}...")
        
        # General questions
        questions.extend([
            f"Who is your target audience for this {category} page?",
            f"Any specific color preferences for your {category} page?"
        ])
        
        return questions[:5]  # Limit to 5 questions
    
    def create_response_from_instructions(self, instructions: str, final_data: Dict[str, Any]) -> str:
        """Create a natural language response from orchestrator instructions"""
        try:
            # Use the instructions to create a conversational response
            if "template recommendations" in instructions.lower():
                templates = final_data.get("templates", [])
                targeted_questions = final_data.get("targeted_questions", {})
                print(f"DEBUG: Templates data: {templates}")
                print(f"DEBUG: Targeted questions: {targeted_questions}")
                
                if templates and len(templates) > 0:
                    questions = targeted_questions.get("questions", [])
                    template_count = len(templates)
                    
                    if questions and template_count > 1:
                        # Interactive questioning approach
                        response = f"""I found {template_count} great templates that match your requirements! To help you choose the perfect one, I'd like to ask a few quick questions:\n\n"""
                        
                        for i, question_data in enumerate(questions[:2]):  # Show top 2 questions
                            question = question_data.get("question", "")
                            tag = question_data.get("tag", "")
                            response += f"{i+1}. {question}\n"
                        
                        response += f"\nYou can also:\n• Answer any of these questions to narrow down your options\n• Say 'show me all templates' to see the full list\n• Choose a template directly by name or number"
                        
                    else:
                        # Direct template presentation
                        response = f"""I found {template_count} great templates for you! Here are the top recommendations:\n\n"""
                        for i, template_data in enumerate(templates[:3]):
                            # Handle both direct template objects and scored template objects
                            if isinstance(template_data, dict):
                                if "template" in template_data:
                                    # This is a scored template object
                                    template = template_data["template"]
                                    score = template_data.get("score", 0)
                                    reasoning = template_data.get("reasoning", "")
                                else:
                                    # This is a direct template object
                                    template = template_data
                                    score = 0
                                    reasoning = ""
                            else:
                                template = template_data
                                score = 0
                                reasoning = ""
                            
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
            
            elif "template_selection_error" in instructions.lower():
                available_templates = final_data.get("available_templates", [])
                user_message = final_data.get("user_message", "")
                
                response = "I couldn't determine which template you want to select. Could you please be more specific?\n\n"
                
                if available_templates:
                    response += "Available options:\n"
                    for i, template in enumerate(available_templates[:3], 1):
                        template_name = template.get("name", f"Template {i}")
                        response += f"{i}. {template_name}\n"
                
                response += "\nYou can:\n• Choose by number: 'I want template 1' or 'option 2'\n• Choose by name: 'I want Landing 1' or 'Login 2'\n• Ask for different options: 'show me other templates'"
            
            elif "intent_detection_error" in instructions.lower():
                current_phase = final_data.get("current_phase", "unknown")
                user_message = final_data.get("user_message", "")
                
                response = f"I'm not sure I understood what you want to do in the {current_phase} phase. Could you please clarify?\n\n"
                
                if current_phase == "template_recommendation":
                    response += "You can:\n• Choose a template by saying 'I want template 1' or 'landing 1'\n• Ask for different options by saying 'show me other templates'\n• Modify your requirements by saying 'make it more modern' or 'change the style'"
                elif current_phase == "template_selection":
                    response += "You can:\n• Edit the template by saying 'change the color' or 'make it more modern'\n• Generate a report by saying 'create a report' or 'show me the details'\n• Confirm your selection by saying 'yes' or 'that's perfect'"
                else:
                    response += "Please let me know what you'd like to do next."
            
            elif "phase_transition" in instructions.lower():
                current_phase = final_data.get("current_phase", "unknown")
                next_phase = final_data.get("next_phase", "unknown")
                reasoning = final_data.get("reasoning", "")
                
                response = f"Great! I'm transitioning from {current_phase} to {next_phase}.\n\n"
                
                if reasoning:
                    response += f"Reasoning: {reasoning}\n\n"
                
                if next_phase == "template_recommendation":
                    response += "I'll now show you template recommendations based on your requirements."
                elif next_phase == "template_selection":
                    response += "Please select a template from the options I've provided."
                elif next_phase == "editing":
                    response += "You can now make modifications to your selected template."
                else:
                    response += "Let's continue with the next step."
            
            elif "more specific requirements" in instructions.lower():
                response = """I'd like to understand your needs better. Could you tell me:

1. What type of page you want to create (e.g., signup, landing, profile)?
2. Any specific style preferences (e.g., modern, minimal, colorful)?
3. Who is your target audience?

This will help me find the perfect template for you!"""
            
            elif "present_filtered_recommendations" in instructions.lower():
                templates = final_data.get("templates", [])
                targeted_questions = final_data.get("targeted_questions", {})
                user_response = final_data.get("user_response", "")
                
                if templates and len(templates) > 0:
                    questions = targeted_questions.get("questions", [])
                    template_count = len(templates)
                    
                    if template_count == 1:
                        # Only one template left - suggest selection
                        template = templates[0].get("template", templates[0])
                        template_name = template.get("name", "Template")
                        template_description = template.get("description", "No description")
                        
                        response = f"""Perfect! Based on your preferences, I found the ideal template for you:

        {template_name} - {template_description}

        This template matches all your requirements perfectly. Would you like to select this template? You can say 'yes' or the template name to proceed."""
                    
                    elif questions and template_count > 1:
                        # Still multiple templates - continue questioning
                        response = f"""Great! I've narrowed it down to {template_count} templates based on your preferences. Let me ask one more question to find the perfect match:\n\n"""
                        
                        for i, question_data in enumerate(questions[:1]):  # Show top 1 question
                            question = question_data.get("question", "")
                            response += f"{question}\n"
                        
                        response += f"\nYou can also:\n• Answer this question to narrow down further\n• Say 'show me all {template_count} templates' to see the full list\n• Choose a template directly by name or number"
                    
                    else:
                        # No more questions - show templates
                        response = f"""Based on your preferences, here are the {template_count} best templates:\n\n"""
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
            
            elif "modified template" in instructions.lower():
                response = "Perfect! I've applied the changes to your template. Here's what I modified:\n\n"
                modifications = final_data.get("modifications", {})
                if modifications.get("changes"):
                    for change in modifications["changes"]:
                        response += f"• {change}\n"
                response += "\nAre you satisfied with these changes, or would you like me to make any adjustments?"
            
            elif "template selection" in instructions.lower() or "selected_template" in final_data:
                selected_template = final_data.get("selected_template", {})
                ui_preview = final_data.get("ui_preview", {})
                
                if selected_template:
                    template_name = selected_template.get("name", "the selected template")
                    
                    if ui_preview and ui_preview.get("preview_url"):
                        # Show UI preview with embedded iframe
                        preview_url = ui_preview["preview_url"]
                        code_summary = ui_preview.get("code_summary", {})
                        
                        response = f"""Perfect! I've confirmed your selection of {template_name}.

        🎨 UI Preview Generated!

        Your template is ready! Here's what I've created for you:

        Code Summary:
        • HTML structure with semantic markup
        • CSS styling with responsive design
        • Interactive elements and animations
        • Mobile-friendly layout
        • Clean, maintainable code

        You can now view your UI mockup and make any adjustments you'd like!"""
                    else:
                        response = f"""Perfect! I've confirmed your selection of {template_name}.

        Your template is ready! I've generated a complete UI mockup with all the features you requested.

        You can now:
        • View the preview of your mockup
        • Download the code files
        • Make any modifications you'd like
        • Get a detailed report of the project

        What would you like to do next?"""
                else:
                    response = "I couldn't identify which template you selected. Please specify the template name or number (1, 2, 3, etc.)."
            
            elif "phase 2" in instructions.lower():
                response = """Welcome to Phase 2: Template Editing!

        Now you can customize your template to make it perfect for your needs. You can:
        • Change colors and styling
        • Modify text and content
        • Add or remove elements
        • Adjust layout and spacing
        • Add new features

        Just tell me what changes you'd like to make!"""
            
            else:
                response = instructions
            
            return response
            
        except Exception as e:
            return f"I'm having trouble processing that right now. Could you please try again? (Error: {str(e)})" 