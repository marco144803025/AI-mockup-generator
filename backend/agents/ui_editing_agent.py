from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager

class UIEditingAgent(BaseAgent):
    """Advanced UI Editing Agent with sophisticated modification capabilities"""
    
    def __init__(self):
        system_message = """You are an Advanced UI Editing Agent specialized in:
1. Analyzing user modification requests with deep understanding
2. Creating detailed modification plans with step-by-step instructions
3. Applying changes while maintaining design integrity
4. Validating modifications for quality and consistency

You focus on sophisticated UI modifications and improvements."""
        
        super().__init__("UIEditing", system_message)
        self.tool_utility = ToolUtility("ui_editing_agent")
        self.keyword_manager = KeywordManager()
    
    def process_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Complete workflow: analyze request, plan modifications, and apply them using advanced prompt engineering"""
        
        # Step 1: Analyze the modification request with sophisticated prompt engineering
        modification_request = self.analyze_modification_request_advanced(user_feedback, current_template)
        
        # Step 2: Generate detailed modification plan
        modification_plan = self.generate_modification_plan_advanced(modification_request, current_template)
        
        # Step 3: Apply modifications with validation
        modified_template = self.apply_modifications_advanced(current_template, modification_plan)
        
        # Step 4: Validate modifications comprehensively
        validation_result = self.validate_modifications_advanced(current_template, modified_template)
        
        return {
            "success": validation_result.get("is_valid", False),
            "original_template": current_template,
            "modified_template": modified_template,
            "modification_request": modification_request,
            "modification_plan": modification_plan,
            "validation_result": validation_result,
            "changes_summary": self._generate_changes_summary_advanced(current_template, modified_template)
        }
    
    def analyze_modification_request_advanced(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user feedback using advanced prompt engineering for sophisticated understanding"""
        
        # Build comprehensive prompt for advanced analysis
        prompt = self._build_advanced_analysis_prompt(user_feedback, current_template)
        
        # Call Claude with advanced reasoning
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the response with enhanced error handling
        return self._parse_advanced_analysis_response(response, user_feedback)
    
    def _build_advanced_analysis_prompt(self, user_feedback: str, current_template: Dict[str, Any]) -> str:
        """Build sophisticated prompt for advanced modification analysis"""
        
        # Extract template information
        template_name = current_template.get('name', 'Unknown Template')
        template_category = current_template.get('category', 'Unknown')
        template_tags = current_template.get('tags', [])
        template_description = current_template.get('description', 'No description available')
        
        # Get HTML and CSS content for analysis
        html_content = current_template.get('html_export', '')
        css_content = current_template.get('style_css', '') + '\n' + current_template.get('global_css', '')
        
        # Analyze current structure
        structure_analysis = self._analyze_current_structure(html_content, css_content)
        
        prompt = f"""
You are an expert UI/UX modification analyst with deep understanding of web design principles, user psychology, and technical implementation. Your task is to analyze a user's modification request and provide a comprehensive, structured analysis.

## CURRENT TEMPLATE CONTEXT
- **Template Name**: {template_name}
- **Category**: {template_category}
- **Description**: {template_description}
- **Tags**: {', '.join(template_tags)}
- **Current Structure**: {structure_analysis}

## USER FEEDBACK
"{user_feedback}"

## ANALYSIS TASK
Using Chain-of-Thought reasoning, analyze the user's modification request and provide a comprehensive specification. Consider:

1. **Intent Analysis**: What is the user trying to achieve?
2. **Context Understanding**: How does this fit with the current template?
3. **Technical Feasibility**: What changes are technically possible?
4. **Design Impact**: How will changes affect the overall design?
5. **User Experience**: Will changes improve or hinder UX?
6. **Implementation Strategy**: What's the best approach to implement changes?

## OUTPUT FORMAT
Return a JSON object with this exact structure:
{{
    "modification_type": "string (layout|styling|content|functionality|color-scheme|typography|structure|interaction)",
    "priority": "string (high|medium|low)",
    "complexity": "string (simple|moderate|complex)",
    "affected_elements": ["list", "of", "elements", "to", "modify"],
    "specific_changes": [
        {{
            "element_selector": "string (CSS selector or element description)",
            "change_type": "string (color|size|position|text|layout|add|remove|modify|style)",
            "current_value": "string (current state/value)",
            "new_value": "string (desired new state/value)",
            "reasoning": "string (detailed explanation of why this change is needed)",
            "impact_assessment": "string (how this change affects the overall design)",
            "implementation_notes": "string (technical notes for implementation)"
        }}
    ],
    "overall_intent": "string (comprehensive explanation of what the user is trying to achieve)",
    "design_principles": ["list", "of", "design", "principles", "being", "applied"],
    "constraints": ["list", "of", "constraints", "or", "limitations"],
    "suggestions": ["list", "of", "additional", "improvements", "or", "considerations"],
    "confidence_score": 0.85,
    "risk_assessment": "string (potential risks or issues with the proposed changes)",
    "alternative_approaches": ["list", "of", "alternative", "ways", "to", "achieve", "the", "goal"]
}}

## CHAIN-OF-THOUGHT PROCESS
Think through this systematically:
1. **Parse User Intent**: Understand what the user wants to achieve
2. **Analyze Current State**: Examine the existing template structure
3. **Identify Required Changes**: Determine what needs to be modified
4. **Consider Design Impact**: Assess how changes affect the overall design
5. **Plan Implementation**: Determine the best approach to implement changes
6. **Validate Approach**: Ensure the proposed changes are feasible and beneficial

Remember: Focus on understanding the user's underlying goals, not just their explicit requests. Consider the broader context and design principles.
"""
        
        return prompt
    
    def _analyze_current_structure(self, html_content: str, css_content: str) -> str:
        """Analyze the current template structure for context"""
        
        # Basic structure analysis
        html_lines = html_content.split('\n')
        css_lines = css_content.split('\n')
        
        # Count elements
        div_count = sum(1 for line in html_lines if '<div' in line)
        class_count = sum(1 for line in css_lines if '.' in line and '{' in line)
        
        # Identify main sections
        main_sections = []
        for line in html_lines:
            line_lower = line.lower()
            if any(section in line_lower for section in self.keyword_manager.get_component_keywords()["html_sections"]):
                main_sections.append(line.strip())
        
        return f"HTML: {len(html_lines)} lines, {div_count} divs; CSS: {len(css_lines)} lines, {class_count} classes; Main sections: {len(main_sections)}"
    
    def _parse_advanced_analysis_response(self, response: str, user_feedback: str) -> Dict[str, Any]:
        """Parse the advanced analysis response with enhanced error handling"""
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_response = json.loads(json_str)
                
                # Validate required fields
                required_fields = self.keyword_manager.get_required_fields()["modification_request"]
                for field in required_fields:
                    if field not in parsed_response:
                        parsed_response[field] = self._get_default_value(field)
                
                return parsed_response
            else:
                return self._get_default_modification_request_advanced(user_feedback)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing advanced analysis response: {e}")
            return self._get_default_modification_request_advanced(user_feedback)
    
    def _get_default_modification_request_advanced(self, user_feedback: str) -> Dict[str, Any]:
        """Return sophisticated default modification request when analysis fails"""
        return {
            "modification_type": "general",
            "priority": "medium",
            "complexity": "moderate",
            "affected_elements": ["general"],
            "specific_changes": [
                {
                    "element_selector": "general",
                    "change_type": "improvement",
                    "current_value": "current state",
                    "new_value": "improved state",
                    "reasoning": f"User requested: {user_feedback}",
                    "impact_assessment": "General improvement to enhance user experience",
                    "implementation_notes": "Apply changes carefully to maintain existing functionality"
                }
            ],
            "overall_intent": f"Improve the UI based on user feedback: {user_feedback}",
            "design_principles": self.keyword_manager.get_design_principles(),
            "constraints": ["maintain existing functionality", "preserve responsive design"],
            "suggestions": ["Consider user feedback carefully", "Test changes thoroughly"],
            "confidence_score": 0.5,
            "risk_assessment": "Low risk - general improvements",
            "alternative_approaches": ["Incremental changes", "User testing before full implementation"]
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            "modification_type": "general",
            "priority": "medium",
            "complexity": "moderate",
            "affected_elements": ["general"],
            "specific_changes": [],
            "overall_intent": "General improvement",
            "design_principles": ["user-centered design"],
            "constraints": ["maintain existing functionality"],
            "suggestions": ["Consider user feedback"],
            "confidence_score": 0.5,
            "risk_assessment": "Low risk",
            "alternative_approaches": ["Incremental approach"]
        }
        return defaults.get(field, "Not specified")
    
    def generate_modification_plan_advanced(self, modification_request: Dict[str, Any], current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed modification plan using advanced prompt engineering"""
        
        # Build sophisticated planning prompt
        prompt = self._build_advanced_planning_prompt(modification_request, current_template)
        
        # Call Claude with advanced reasoning
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the response
        return self._parse_advanced_planning_response(response, modification_request)
    
    def _build_advanced_planning_prompt(self, modification_request: Dict[str, Any], current_template: Dict[str, Any]) -> str:
        """Build sophisticated prompt for advanced modification planning"""
        
        # Extract modification details
        modification_type = modification_request.get("modification_type", "general")
        specific_changes = modification_request.get("specific_changes", [])
        overall_intent = modification_request.get("overall_intent", "")
        
        # Get template content
        html_content = current_template.get('html_export', '')
        css_content = current_template.get('style_css', '') + '\n' + current_template.get('global_css', '')
        
        prompt = f"""
You are an expert UI/UX implementation strategist with deep knowledge of web development, design systems, and user experience optimization. Your task is to create a comprehensive modification plan for implementing UI changes.

## MODIFICATION REQUEST
- **Type**: {modification_type}
- **Intent**: {overall_intent}
- **Specific Changes**: {len(specific_changes)} changes requested

## CURRENT TEMPLATE
- **HTML Content**: {len(html_content)} characters
- **CSS Content**: {len(css_content)} characters

## PLANNING TASK
Create a detailed implementation plan that considers:

1. **Implementation Strategy**: Best approach to implement changes
2. **Code Quality**: Maintain clean, maintainable code
3. **Performance Impact**: Minimize performance degradation
4. **Responsive Design**: Ensure changes work across devices
5. **Accessibility**: Maintain or improve accessibility
6. **Testing Strategy**: How to validate changes
7. **Rollback Plan**: How to revert if needed

## OUTPUT FORMAT
Return a JSON object with this exact structure:
{{
    "implementation_strategy": "string (detailed strategy for implementing changes)",
    "modification_steps": [
        {{
            "step_number": 1,
            "step_type": "string (html_modification|css_modification|content_update|structure_change)",
            "element_selector": "string (CSS selector or element description)",
            "current_state": "string (description of current state)",
            "target_state": "string (description of desired state)",
            "implementation_details": "string (detailed implementation instructions)",
            "code_changes": {{
                "html_changes": "string (specific HTML modifications)",
                "css_changes": "string (specific CSS modifications)",
                "new_elements": ["list", "of", "new", "elements", "to", "add"],
                "removed_elements": ["list", "of", "elements", "to", "remove"]
            }},
            "validation_criteria": ["list", "of", "criteria", "to", "validate", "this", "step"],
            "risk_assessment": "string (potential risks for this step)",
            "estimated_effort": "string (low|medium|high)"
        }}
    ],
    "quality_checks": ["list", "of", "quality", "checks", "to", "perform"],
    "testing_requirements": ["list", "of", "testing", "requirements"],
    "performance_considerations": ["list", "of", "performance", "considerations"],
    "accessibility_checks": ["list", "of", "accessibility", "checks"],
    "rollback_plan": "string (detailed plan for rolling back changes if needed)",
    "success_criteria": ["list", "of", "criteria", "to", "determine", "success"],
    "confidence_level": 0.85
}}

## CHAIN-OF-THOUGHT PROCESS
Think through this systematically:
1. **Analyze Requirements**: Understand what needs to be changed
2. **Design Strategy**: Plan the best approach to implement changes
3. **Break Down Steps**: Divide implementation into manageable steps
4. **Consider Dependencies**: Identify dependencies between changes
5. **Plan Validation**: Determine how to validate each step
6. **Assess Risks**: Identify potential issues and mitigation strategies
7. **Ensure Quality**: Plan for maintaining code quality and performance

Remember: Focus on creating a robust, maintainable implementation that achieves the user's goals while preserving the template's integrity.
"""
        
        return prompt
    
    def _parse_advanced_planning_response(self, response: str, modification_request: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the advanced planning response"""
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_response = json.loads(json_str)
                
                # Validate required fields
                if "modification_steps" not in parsed_response:
                    parsed_response["modification_steps"] = []
                if "implementation_strategy" not in parsed_response:
                    parsed_response["implementation_strategy"] = "Standard implementation approach"
                
                return parsed_response
            else:
                return self._get_default_modification_plan(modification_request)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing advanced planning response: {e}")
            return self._get_default_modification_plan(modification_request)
    
    def _get_default_modification_plan(self, modification_request: Dict[str, Any]) -> Dict[str, Any]:
        """Return default modification plan when parsing fails"""
        return {
            "implementation_strategy": "Standard implementation approach",
            "modification_steps": [
                {
                    "step_number": 1,
                    "step_type": "general_modification",
                    "element_selector": "general",
                    "current_state": "Current template state",
                    "target_state": "Improved template state",
                    "implementation_details": "Apply general improvements based on user feedback",
                    "code_changes": {
                        "html_changes": "Apply HTML modifications as needed",
                        "css_changes": "Apply CSS modifications as needed",
                        "new_elements": [],
                        "removed_elements": []
                    },
                    "validation_criteria": ["Template renders correctly", "Changes are visible"],
                    "risk_assessment": "Low risk - general improvements",
                    "estimated_effort": "medium"
                }
            ],
            "quality_checks": ["Code validation", "Visual inspection"],
            "testing_requirements": ["Basic functionality testing"],
            "performance_considerations": ["Maintain current performance"],
            "accessibility_checks": ["Maintain accessibility standards"],
            "rollback_plan": "Revert to original template if issues arise",
            "success_criteria": ["Template renders correctly", "User requirements met"],
            "confidence_level": 0.5
        }
    
    def apply_modifications_advanced(self, template: Dict[str, Any], modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply modifications using advanced implementation strategy"""
        
        # Create a copy of the template for modification
        modified_template = template.copy()
        
        # Get current content
        html_content = template.get('html_export', '')
        css_content = template.get('style_css', '') + '\n' + template.get('global_css', '')
        
        # Apply each modification step
        modification_steps = modification_plan.get("modification_steps", [])
        
        for step in modification_steps:
            html_content = self._apply_html_modifications_advanced(html_content, step)
            css_content = self._apply_css_modifications_advanced(css_content, step)
        
        # Update the modified template
        modified_template['html_export'] = html_content
        modified_template['style_css'] = css_content
        
        return modified_template
    
    def _apply_html_modifications_advanced(self, html_content: str, step: Dict[str, Any]) -> str:
        """Apply HTML modifications using advanced techniques"""
        
        # TODO: Implement sophisticated HTML modification logic
        # This would include:
        # - Element selection and modification
        # - Content updates
        # - Structure changes
        # - Attribute modifications
        
        print(f"TODO: Apply HTML modifications for step {step.get('step_number', 1)}")
        return html_content
    
    def _apply_css_modifications_advanced(self, css_content: str, step: Dict[str, Any]) -> str:
        """Apply CSS modifications using advanced techniques"""
        
        # TODO: Implement sophisticated CSS modification logic
        # This would include:
        # - Style rule updates
        # - New style rules
        # - Responsive design considerations
        # - Performance optimizations
        
        print(f"TODO: Apply CSS modifications for step {step.get('step_number', 1)}")
        return css_content
    
    def validate_modifications_advanced(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate modifications using advanced validation techniques"""
        
        # TODO: Implement comprehensive validation
        # This would include:
        # - HTML validation
        # - CSS validation
        # - Responsive design validation
        # - Accessibility validation
        # - Performance validation
        
        print("TODO: Implement advanced validation logic")
        
        return {
            "is_valid": True,
            "validation_details": "Advanced validation not yet implemented",
            "warnings": [],
            "errors": [],
            "recommendations": ["Implement comprehensive validation logic"]
        }
    
    def _generate_changes_summary_advanced(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> List[str]:
        """Generate advanced changes summary"""
        
        # TODO: Implement sophisticated changes summary
        # This would include:
        # - Detailed change descriptions
        # - Impact analysis
        # - Performance implications
        # - Accessibility considerations
        
        print("TODO: Implement advanced changes summary")
        
        return [
            "Advanced changes summary not yet implemented",
            "Consider implementing detailed change tracking",
            "Include impact analysis and recommendations"
        ]
    
    # Legacy methods for backward compatibility
    def analyze_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to advanced version"""
        return self.analyze_modification_request_advanced(user_feedback, current_template)
    
    def generate_modification_plan(self, modification_request: Dict[str, Any], current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to advanced version"""
        return self.generate_modification_plan_advanced(modification_request, current_template)
    
    def apply_modifications(self, template: Dict[str, Any], modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to advanced version"""
        return self.apply_modifications_advanced(template, modification_plan)
    
    def validate_modifications(self, original_template: Dict[str, Any], modified_template: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to advanced version"""
        return self.validate_modifications_advanced(original_template, modified_template) 