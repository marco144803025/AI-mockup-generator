from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

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
        
        return self._parse_question_response(response, templates)
    
    def _build_question_prompt(self, templates: List[Dict[str, Any]], requirements: Dict[str, Any]) -> str:
        """Build prompt for generating strategic questions"""
        
        # Extract template information
        template_info = "AVAILABLE TEMPLATES:\n"
        for i, template_data in enumerate(templates, 1):
            template = template_data.get("template", template_data)
            name = template.get("name", f"Template {i}")
            tags = template.get("tags", [])
            category = template.get("category", "unknown")
            
            template_info += f"""
{i}. {name} ({category})
   Tags: {', '.join(tags) if tags else 'None'}
"""
        
        # Extract current requirements
        current_style = requirements.get("style_preferences", [])
        current_components = requirements.get("key_features", [])
        current_audience = requirements.get("target_audience", "")
        
        prompt = f"""
You are an expert UX researcher specializing in user requirement gathering and template selection optimization. Generate 2-3 strategic questions to help narrow down template selection.

CURRENT CONTEXT:
- Available Templates: {len(templates)} templates
- Current Style Preferences: {', '.join(current_style) if current_style else 'Not specified'}
- Current Component Requirements: {', '.join(current_components) if current_components else 'Not specified'}
- Current Target Audience: {current_audience if current_audience else 'Not specified'}

{template_info}

OBJECTIVE:
Generate strategic questions that will:
1. **Maximize Differentiation**: Questions that best separate the available templates
2. **Gather Missing Information**: Focus on aspects not yet covered by current requirements
3. **Prioritize User Experience**: Questions that reveal user preferences and constraints
4. **Enable Informed Decisions**: Questions that lead to confident template selection

QUESTION GENERATION STRATEGY:
Consider these dimensions when crafting questions:
- Visual Design Preferences: Style, color schemes, layout preferences
- Business Context: Target audience, brand alignment, conversion goals

TASK:
Generate strategic questions and return a JSON object with this structure:

{{
    "questions": [
        {{
            "question": "Natural, conversational question that feels like a UX researcher asking",
            "focus_area": "The main aspect this question addresses (e.g., 'visual_style', 'functionality', 'user_experience')",
            "strategic_value": "Why this question is important for template selection",
            "expected_impact": "How this question will help narrow down choices",
            "follow_up_potential": "Whether this question can lead to deeper insights"
        }}
    ],
    "focus_areas": ["list", "of", "key", "focus", "areas"],
    "template_count": {len(templates)},
    "strategy_summary": "Brief explanation of the questioning strategy"
}}

IMPORTANT:
- Questions should be tidy and concise
- Focus on the most differentiating aspects
- Consider what information would be most valuable for making a confident choice
- Balance between being specific enough to be useful and general enough to be applicable
"""
        
        return prompt
    
    def _call_claude_with_tools(self, prompt: str) -> str:
        """Call Claude with tool calling capabilities"""
        try:
            client = self.claude_client
            messages = [{"role": "user", "content": prompt}]
            
            # Get available tools
            tools = self.tool_utility.get_tools()
            
            # Call Claude with tools
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=messages,
                tools=tools if tools else None,
                tool_choice={"type": "auto"} if tools else None
            )
            
            # Debug: Log LLM response
            print(f"DEBUG: Question Generation Agent LLM Response: {response.content[0].text[:500]}...")
            if len(response.content[0].text) > 500:
                print(f"DEBUG: Full Question Generation Response: {response.content[0].text}")
            
            return response.content[0].text
            
        except Exception as e:
            print(f"ERROR: Error calling Claude with tools: {e}")
            return f"Error: {str(e)}"
    
    def _parse_question_response(self, response: str, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse the LLM response for question generation"""
        
        try:
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return self._fallback_question_generation(templates)
            
            json_str = json_match.group()
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
        """Fallback question generation if LLM parsing fails"""
        
        # Extract tags for fallback questions
        all_tags = set()
        for template_data in templates:
            template = template_data.get("template", {})
            tags = template.get("tags", [])
            all_tags.update(tags)
        
        questions = []
        focus_areas = []
        
        # Generate basic questions based on available tags
        for tag in list(all_tags)[:3]:
            question = self.keyword_manager.generate_question_for_tag(tag, 0, len(templates))
            if question:
                questions.append({
                    "question": question,
                    "focus_area": tag,
                    "type": self.keyword_manager.categorize_tag(tag),
                    "count": 0,
                    "total": len(templates)
                })
                focus_areas.append(tag)
        
        return {
            "questions": questions,
            "focus_areas": focus_areas,
            "template_count": len(templates)
        } 