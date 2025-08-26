from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from tools.tool_utility import ToolUtility
from config.keyword_manager import KeywordManager

class QuestionGenerationAgent(BaseAgent):
    """Focused agent with single responsibility: Generate clarifying questions"""
    
    def __init__(self):
        system_message = """You are a Question Generation Agent specialized in:
1. Generating targeted questions to narrow down UI mockup selection (one page only)
2. Understanding user preferences and requirements gaps
3. Creating strategic questions that maximize differentiation
4. Focusing on the most important decision factors

You focus ONLY on question generation. You do not analyze requirements or recommend templates."""
        
        super().__init__("QuestionGeneration", system_message)
        self.tool_utility = ToolUtility("question_generation_agent")
        self.keyword_manager = KeywordManager()
    
    def generate_questions(self, templates: List[Dict[str, Any]], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Single job: Generate clarifying questions based on templates and requirements"""
        
        if not templates:
            return {"questions": [], "focus_areas": []}
        
        # Let the LLM generate strategic questions
        prompt = self._build_question_prompt(templates, requirements)
        response = self._call_claude_with_tools(prompt)
        
        # Parse the response
        result = self._parse_question_response(response, templates)
        
        # Record rationale for question generation
        try:
            from utils.rationale_manager import RationaleManager
            # Get session_id from requirements if available
            session_id = requirements.get("session_id") if isinstance(requirements, dict) else None
            if session_id:
                rationale_manager = RationaleManager(session_id)
                reasoning = f"Generated {len(result.get('questions', []))} strategic questions for {len(templates)} templates"
                rationale_manager.add_question_generation_rationale(result.get('questions', []), reasoning)
                print("INFO: Stored question generation rationale")
        except Exception as e:
            print(f"ERROR: Failed to store question generation rationale: {e}")
        
        return result
    
    def _build_question_prompt(self, templates: List[Dict[str, Any]], requirements: Dict[str, Any]) -> str:
        """Build prompt for generating strategic questions based on template differences"""
        
        # Extract template information with detailed analysis
        template_info = "AVAILABLE TEMPLATES:\n"
        template_tags = []
        
        for i, template_data in enumerate(templates, 1):
            template = template_data.get("template", template_data)
            name = template.get("name", f"Template {i}")
            tags = template.get("tags", [])
            category = template.get("category", "unknown")
            description = template.get("description", "")
            
            template_info += f"""
{i}. {name} ({category})
   Description: {description}
   Tags: {', '.join(tags) if tags else 'None'}
"""
            template_tags.append(tags)
        
        # Analyze template differences
        if len(template_tags) >= 2:
            # Find unique tags for each template
            template1_tags = set(template_tags[0])
            template2_tags = set(template_tags[1])
            
            # Find differentiating tags
            unique_to_template1 = template1_tags - template2_tags
            unique_to_template2 = template2_tags - template1_tags
            common_tags = template1_tags & template2_tags
            
            differences_analysis = f"""
TEMPLATE DIFFERENCES ANALYSIS:
Template 1 Unique Features: {', '.join(unique_to_template1) if unique_to_template1 else 'None'}
Template 2 Unique Features: {', '.join(unique_to_template2) if unique_to_template2 else 'None'}
Common Features: {', '.join(common_tags) if common_tags else 'None'}

KEY DIFFERENTIATORS:
"""
            
            # Add specific differentiators based on common patterns
            if 'light theme' in template1_tags and 'dark theme' in template2_tags:
                differences_analysis += "- Theme: Light vs Dark\n"
            if 'green accents' in template1_tags and 'purple accents' in template2_tags:
                differences_analysis += "- Color Scheme: Green vs Purple\n"
            if 'natural aesthetic' in template1_tags and 'futuristic aesthetic' in template2_tags:
                differences_analysis += "- Visual Style: Natural vs Futuristic\n"
            if 'image-heavy' in template1_tags and 'abstract gradients' in template2_tags:
                differences_analysis += "- Background: Image-heavy vs Abstract gradients\n"
        else:
            differences_analysis = "Single template available - focusing on requirement refinement."
        
        # Extract current requirements
        current_style = requirements.get("style_preferences", [])
        current_components = requirements.get("key_features", [])
        current_audience = requirements.get("target_audience", "")
        
        prompt = f"""
You are an expert UX researcher specializing in template selection optimization. Your goal is to generate 2-3 strategic questions that help users choose between the available templates based on their specific differences.

CURRENT CONTEXT:
- Available Templates: {len(templates)} templates
- Current Style Preferences: {', '.join(current_style) if current_style else 'Not specified'}
- Current Component Requirements: {', '.join(current_components) if current_components else 'Not specified'}
- Current Target Audience: {current_audience if current_audience else 'Not specified'}

{template_info}

{differences_analysis}

OBJECTIVE:
Generate strategic questions that will:
1. **Highlight Template Differences**: Questions that directly relate to the key differentiators between templates
2. **Reveal User Preferences**: Questions that help users understand which template characteristics align with their needs
3. **Enable Confident Selection**: Questions that lead to a clear choice based on actual template features

QUESTION GENERATION STRATEGY:
Focus on the most differentiating aspects between templates:
- If templates differ in theme (light vs dark), ask about theme preference
- If templates differ in color schemes, ask about color preferences
- If templates differ in visual style (natural vs futuristic), ask about brand personality
- If templates differ in layout approach, ask about user experience preferences

TASK:
Generate strategic questions and return ONLY a JSON object with this structure and NO extra text before or after:

{{
    "questions": [
        {{
            "question": "Specific question that directly relates to template differences (e.g., 'Do you prefer a light theme with natural aesthetics or a dark theme with futuristic elements?')",
            "focus_area": "The main aspect this question addresses (e.g., 'theme_preference', 'color_scheme', 'visual_style')",
            "strategic_value": "Why this question is important for choosing between these specific templates",
            "expected_impact": "How this question will help distinguish between the available options",
            "follow_up_potential": "Whether this question can lead to deeper insights"
        }}
    ],
    "focus_areas": ["list", "of", "key", "focus", "areas"],
    "template_count": {len(templates)},
    "strategy_summary": "Brief explanation of how these questions relate to the specific template differences"
}}

IMPORTANT:
- Questions MUST be specific to the actual differences between the available templates
- Focus on the most distinguishing characteristics (theme, colors, style, layout)
- Make questions actionable and relevant to the template selection decision
- Avoid generic questions that don't help differentiate between the specific templates
"""
        
        return prompt
    
    def _call_claude_with_tools(self, prompt: str) -> str:
        """Call Claude with tool calling capabilities"""
        try:
            # Use the base agent's COT method with JSON extraction
            response = self.call_claude_with_cot(prompt, enable_cot=True, extract_json=True)
            
            # Debug: Log JSON response for debugging
            print(f"DEBUG: Question Generation Agent JSON Response Length: {len(response)} chars")
            print(f"DEBUG: Question Generation Agent JSON Response Preview: {response[:200]}...")
            
            return response
            
        except Exception as e:
            print(f"ERROR: Error calling Claude with tools: {e}")
            return f"Error: {str(e)}"
    
    def _parse_question_response(self, response: str, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse the LLM response for question generation"""
        
        print(f"DEBUG: Question Generation Agent - Parsing response with {len(templates)} templates")
        print(f"DEBUG: Question Generation Agent - Raw response preview: {response[:200]}...")
        
        try:
            # Use the base agent's consolidated method
            parsed_response = self._extract_json_from_text(response)
            if parsed_response is None:
                # Fallback regex approach
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if not json_match:
                    print("DEBUG: Question Generation Agent - No JSON found, using fallback")
                    return self._fallback_question_generation(templates)
                json_str = json_match.group()
                print(f"DEBUG: Question Generation Agent - Extracted JSON: {json_str[:200]}...")
                parsed_response = json.loads(json_str)
            
            questions = parsed_response.get("questions", [])
            focus_areas = parsed_response.get("focus_areas", [])
            
            # Convert to expected format
            formatted_questions = []
            for q in questions:
                formatted_questions.append({
                    "question": q.get("question", ""),
                    "focus_area": q.get("focus_area", ""),
                    "strategic_value": q.get("strategic_value", ""),
                    "type": self.keyword_manager.categorize_focus_area(q.get("focus_area", "")),
                    "count": 0,  # Will be calculated if needed
                    "total": len(templates)
                })
            
            return {
                "questions": formatted_questions,
                "focus_areas": focus_areas,
                "template_count": len(templates),
                "strategy_summary": parsed_response.get("strategy_summary", "")
            }
            
        except Exception as e:
            print(f"ERROR: Error parsing question generation response: {e}")
            return self._fallback_question_generation(templates)
    
    def _fallback_question_generation(self, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback question generation if LLM parsing fails - now template-specific"""
        
        if len(templates) < 2:
            return self._generate_single_questions(templates)
        
        # Extract template information for comparison
        template1_data = templates[0].get("template", templates[0])
        template2_data = templates[1].get("template", templates[1])
        
        template1_tags = set(template1_data.get("tags", []))
        template2_tags = set(template2_data.get("tags", []))
        
        # Find key differences
        unique_to_template1 = template1_tags - template2_tags
        unique_to_template2 = template2_tags - template1_tags
        
        questions = []
        focus_areas = []
        
        # Generate questions based on actual template differences
        if 'light theme' in template1_tags and 'dark theme' in template2_tags:
            questions.append({
                "question": "Do you prefer a light theme with natural aesthetics or a dark theme with futuristic elements?",
                "focus_area": "theme_preference",
                "type": "visual_style",
                "count": 0,
                "total": len(templates)
            })
            focus_areas.append("theme_preference")
        
        if 'green accents' in template1_tags and 'purple accents' in template2_tags:
            questions.append({
                "question": "Which color scheme better represents your brand: green accents with natural elements or purple accents with futuristic design?",
                "focus_area": "color_scheme",
                "type": "brand_alignment",
                "count": 0,
                "total": len(templates)
            })
            focus_areas.append("color_scheme")
        
        if 'natural aesthetic' in template1_tags and 'futuristic aesthetic' in template2_tags:
            questions.append({
                "question": "Does your brand personality align more with natural, organic aesthetics or sleek, futuristic design?",
                "focus_area": "brand_personality",
                "type": "brand_identity",
                "count": 0,
                "total": len(templates)
            })
            focus_areas.append("brand_personality")
        
        if 'image-heavy' in template1_tags and 'abstract gradients' in template2_tags:
            questions.append({
                "question": "Would you prefer a design with prominent background images or one with abstract gradient backgrounds?",
                "focus_area": "background_style",
                "type": "visual_impact",
                "count": 0,
                "total": len(templates)
            })
            focus_areas.append("background_style")
        
        # If no specific differences found, generate questions based on common patterns
        if not questions:
            questions = self._generate_pattern_questions(template1_tags, template2_tags, len(templates))
            focus_areas = ["general_preferences", "user_experience"]
        
        return {
            "questions": questions,
            "focus_areas": focus_areas,
            "template_count": len(templates),
            "strategy_summary": "Fallback questions generated based on template differences analysis"
        }
    
    def _generate_single_questions(self, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate questions when only one template is available"""
        if not templates:
            return {"questions": [], "focus_areas": [], "template_count": 0}
        
        template = templates[0].get("template", templates[0])
        tags = template.get("tags", [])
        
        questions = []
        focus_areas = []
        
        # Generate questions to refine requirements for the single template
        if 'sign-up' in tags or 'registration' in tags:
            questions.append({
                "question": "What specific user data fields do you need in your signup form?",
                "focus_area": "form_requirements",
                "type": "functionality",
                "count": 0,
                "total": 1
            })
            focus_areas.append("form_requirements")
        
        if 'social authentication' in tags or 'social login' in tags:
            questions.append({
                "question": "Which social authentication providers do you want to integrate?",
                "focus_area": "authentication_methods",
                "type": "integration",
                "count": 0,
                "total": 1
            })
            focus_areas.append("authentication_methods")
        
        if 'purple accents' in tags or 'green accents' in tags:
            questions.append({
                "question": "Do you want to customize the accent colors to match your brand palette?",
                "focus_area": "color_customization",
                "type": "branding",
                "count": 0,
                "total": 1
            })
            focus_areas.append("color_customization")
        
        return {
            "questions": questions,
            "focus_areas": focus_areas,
            "template_count": 1,
            "strategy_summary": "Questions to refine requirements for the selected template"
        }
    
    def _generate_pattern_questions(self, tags1: set, tags2: set, template_count: int) -> List[Dict[str, Any]]:
        """Generate questions based on common template patterns"""
        questions = []
        
        # Check for common signup patterns
        if any(tag in tags1 for tag in ['sign-up', 'registration']) and any(tag in tags2 for tag in ['sign-up', 'registration']):
            questions.append({
                "question": "How many form fields do you want in your signup process?",
                "focus_area": "form_complexity",
                "type": "user_experience",
                "count": 0,
                "total": template_count
            })
        
        # Check for authentication patterns
        if any(tag in tags1 for tag in ['social authentication', 'social login']) and any(tag in tags2 for tag in ['social authentication', 'social login']):
            questions.append({
                "question": "Do you want social login options, traditional email/password, or both?",
                "focus_area": "authentication_preference",
                "type": "user_experience",
                "count": 0,
                "total": template_count
            })
        
        # Check for layout patterns
        if any(tag in tags1 for tag in ['form-centric', 'half-width']) and any(tag in tags2 for tag in ['form-centric', 'half-width']):
            questions.append({
                "question": "Do you prefer a form-focused layout or one with more visual elements and branding?",
                "focus_area": "layout_preference",
                "type": "visual_design",
                "count": 0,
                "total": template_count
            })
        
        return questions 