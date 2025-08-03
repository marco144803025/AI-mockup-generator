from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import os
import anthropic

class ReportGenerationAgent(BaseAgent):
    """Advanced Report Generation Agent with sophisticated prompt engineering for comprehensive project documentation"""
    
    def __init__(self):
        system_message = """You are an Advanced Report Generation Agent with deep expertise in:
1. Creating comprehensive PDF reports documenting UI generation processes using sophisticated analysis
2. Explaining reasoning behind design decisions and template selections with detailed insights
3. Documenting modification choices and their impact on user experience and technical implementation
4. Providing professional, well-structured reports with advanced formatting and organization
5. Including visual elements, code snippets, and detailed analysis in reports
6. Using Chain-of-Thought reasoning to explain complex decision-making processes
7. Generating executive summaries and technical documentation
8. Creating actionable insights and recommendations for future improvements
9. Analyzing project success metrics and user satisfaction indicators
10. Producing reports that serve both technical and business stakeholders

You use advanced prompt engineering techniques to analyze project data and generate insightful, comprehensive reports. Always create clear, professional reports that explain the decision-making process with deep technical and business insights."""
        
        super().__init__("ReportGeneration", system_message)
    
    def generate_project_report_advanced(self, project_data: Dict[str, Any]) -> str:
        """Generate a comprehensive PDF report using advanced prompt engineering"""
        
        # Step 1: Analyze project data with sophisticated prompt engineering
        analysis_result = self.analyze_project_data_advanced(project_data)
        
        # Step 2: Generate comprehensive report content
        report_content = self.generate_report_content_advanced(project_data, analysis_result)
        
        # Step 3: Create PDF with advanced formatting
        pdf_filepath = self.create_advanced_pdf_report(report_content, project_data)
        
        return pdf_filepath
    
    def analyze_project_data_advanced(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project data using advanced prompt engineering for comprehensive insights"""
        
        # Build sophisticated analysis prompt
        prompt = self._build_advanced_analysis_prompt(project_data)
        
        # Call Claude with advanced reasoning
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the response
        return self._parse_advanced_analysis_response(response, project_data)
    
    def _build_advanced_analysis_prompt(self, project_data: Dict[str, Any]) -> str:
        """Build sophisticated prompt for advanced project data analysis"""
        
        # Extract key project information
        project_name = project_data.get('project_name', 'Unknown Project')
        project_type = project_data.get('project_type', 'UI Mockup')
        created_date = project_data.get('created_date', datetime.now().isoformat())
        
        # Extract template information
        selected_template = project_data.get('selected_template', {})
        template_name = selected_template.get('name', 'Unknown Template')
        template_category = selected_template.get('category', 'Unknown')
        
        # Extract requirements information
        user_requirements = project_data.get('user_requirements', {})
        requirements_summary = self._summarize_requirements(user_requirements)
        
        # Extract modifications information
        modifications = project_data.get('modifications', [])
        modifications_summary = self._summarize_modifications(modifications)
        
        prompt = f"""
You are an expert project analyst and technical documentation specialist with deep understanding of UI/UX design, web development, and project management. Your task is to analyze a UI mockup project and provide comprehensive insights for report generation.

## PROJECT CONTEXT
- **Project Name**: {project_name}
- **Project Type**: {project_type}
- **Created Date**: {created_date}
- **Selected Template**: {template_name} ({template_category})

## PROJECT DATA ANALYSIS
Please analyze the following project data and provide comprehensive insights:

### User Requirements
{requirements_summary}

### Template Selection
- Template: {template_name}
- Category: {template_category}
- Selection Reasoning: {project_data.get('template_selection_reasoning', 'Not provided')}

### Modifications Applied
{modifications_summary}

### Project Outcomes
- Final Result: {project_data.get('final_result', 'Not specified')}
- User Satisfaction: {project_data.get('user_satisfaction', 'Not measured')}
- Technical Quality: {project_data.get('technical_quality', 'Not assessed')}

## ANALYSIS TASK
Using Chain-of-Thought reasoning, provide a comprehensive analysis that includes:

1. **Project Success Assessment**: How well did the project meet its objectives?
2. **Technical Implementation Quality**: Assessment of the technical approach and implementation
3. **User Experience Impact**: How the final result affects user experience
4. **Design Decision Analysis**: Reasoning behind key design and technical decisions
5. **Risk Assessment**: Identification of potential issues or areas for improvement
6. **Performance Analysis**: Technical performance and optimization opportunities
7. **Accessibility Compliance**: Assessment of accessibility standards and improvements
8. **Future Recommendations**: Suggestions for enhancements and optimizations

## OUTPUT FORMAT
Return a JSON object with this exact structure:
{{
    "project_success_metrics": {{
        "overall_success_score": 0.85,
        "requirements_fulfillment": 0.9,
        "technical_quality": 0.8,
        "user_experience_quality": 0.85,
        "timeline_adherence": 0.9,
        "budget_efficiency": 0.95
    }},
    "technical_analysis": {{
        "implementation_quality": "string (detailed assessment)",
        "code_quality_score": 0.85,
        "performance_metrics": ["list", "of", "performance", "indicators"],
        "security_assessment": "string (security considerations)",
        "scalability_analysis": "string (scalability assessment)",
        "maintainability_score": 0.8
    }},
    "design_analysis": {{
        "design_decision_quality": "string (assessment of design decisions)",
        "user_experience_impact": "string (UX impact analysis)",
        "accessibility_compliance": "string (accessibility assessment)",
        "responsive_design_quality": "string (responsive design analysis)",
        "visual_design_quality": "string (visual design assessment)",
        "brand_alignment": "string (brand consistency analysis)"
    }},
    "risk_assessment": {{
        "identified_risks": ["list", "of", "potential", "risks"],
        "risk_mitigation_strategies": ["list", "of", "mitigation", "approaches"],
        "critical_issues": ["list", "of", "critical", "issues", "if", "any"],
        "recommended_actions": ["list", "of", "recommended", "actions"]
    }},
    "performance_analysis": {{
        "loading_performance": "string (loading time analysis)",
        "rendering_performance": "string (rendering performance)",
        "optimization_opportunities": ["list", "of", "optimization", "opportunities"],
        "browser_compatibility": "string (browser compatibility assessment)"
    }},
    "accessibility_analysis": {{
        "wcag_compliance": "string (WCAG compliance assessment)",
        "accessibility_score": 0.85,
        "accessibility_improvements": ["list", "of", "accessibility", "improvements"],
        "screen_reader_compatibility": "string (screen reader assessment)"
    }},
    "future_recommendations": {{
        "immediate_improvements": ["list", "of", "immediate", "improvements"],
        "long_term_enhancements": ["list", "of", "long-term", "enhancements"],
        "technical_debt_considerations": ["list", "of", "technical", "debt", "items"],
        "scalability_recommendations": ["list", "of", "scalability", "recommendations"]
    }},
    "executive_summary": "string (comprehensive executive summary)",
    "technical_summary": "string (detailed technical summary)",
    "confidence_level": 0.85
}}

## CHAIN-OF-THOUGHT PROCESS
Think through this systematically:
1. **Data Analysis**: Examine all project data thoroughly
2. **Success Evaluation**: Assess how well objectives were met
3. **Technical Assessment**: Evaluate technical implementation quality
4. **User Impact Analysis**: Consider the impact on end users
5. **Risk Identification**: Identify potential issues and risks
6. **Performance Evaluation**: Assess technical performance
7. **Future Planning**: Provide actionable recommendations
8. **Stakeholder Communication**: Ensure insights are valuable for all stakeholders

Remember: Focus on providing actionable insights that can guide future projects and improvements.
"""
        
        return prompt
    
    def _summarize_requirements(self, user_requirements: Dict[str, Any]) -> str:
        """Summarize user requirements for analysis"""
        if not user_requirements:
            return "No user requirements provided"
        
        summary = []
        if 'page_type' in user_requirements:
            summary.append(f"Page Type: {user_requirements['page_type']}")
        if 'style_preferences' in user_requirements:
            summary.append(f"Style Preferences: {', '.join(user_requirements['style_preferences'])}")
        if 'key_features' in user_requirements:
            summary.append(f"Key Features: {', '.join(user_requirements['key_features'])}")
        if 'target_audience' in user_requirements:
            summary.append(f"Target Audience: {user_requirements['target_audience']}")
        
        return "\n".join(summary) if summary else "Basic requirements provided"
    
    def _summarize_modifications(self, modifications: List[Dict[str, Any]]) -> str:
        """Summarize modifications for analysis"""
        if not modifications:
            return "No modifications applied"
        
        summary = []
        for i, mod in enumerate(modifications, 1):
            mod_type = mod.get('modification_type', 'Unknown')
            priority = mod.get('priority', 'Medium')
            summary.append(f"Modification {i}: {mod_type} (Priority: {priority})")
        
        return "\n".join(summary)
    
    def _parse_advanced_analysis_response(self, response: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the advanced analysis response"""
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_response = json.loads(json_str)
                
                # Validate required fields
                required_sections = ["project_success_metrics", "technical_analysis", "design_analysis", "future_recommendations"]
                for section in required_sections:
                    if section not in parsed_response:
                        parsed_response[section] = self._get_default_section(section)
                
                return parsed_response
            else:
                return self._get_default_analysis_result(project_data)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing advanced analysis response: {e}")
            return self._get_default_analysis_result(project_data)
    
    def _get_default_section(self, section: str) -> Dict[str, Any]:
        """Get default content for missing sections"""
        defaults = {
            "project_success_metrics": {
                "overall_success_score": 0.7,
                "requirements_fulfillment": 0.7,
                "technical_quality": 0.7,
                "user_experience_quality": 0.7,
                "timeline_adherence": 0.7,
                "budget_efficiency": 0.7
            },
            "technical_analysis": {
                "implementation_quality": "Standard implementation",
                "code_quality_score": 0.7,
                "performance_metrics": ["Basic performance"],
                "security_assessment": "Standard security measures",
                "scalability_analysis": "Basic scalability",
                "maintainability_score": 0.7
            },
            "design_analysis": {
                "design_decision_quality": "Standard design decisions",
                "user_experience_impact": "Positive user experience",
                "accessibility_compliance": "Basic accessibility",
                "responsive_design_quality": "Responsive design implemented",
                "visual_design_quality": "Good visual design",
                "brand_alignment": "Brand alignment maintained"
            },
            "future_recommendations": {
                "immediate_improvements": ["Consider user feedback"],
                "long_term_enhancements": ["Plan for scalability"],
                "technical_debt_considerations": ["Monitor technical debt"],
                "scalability_recommendations": ["Plan for growth"]
            }
        }
        return defaults.get(section, {})
    
    def _get_default_analysis_result(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return default analysis result when parsing fails"""
        return {
            "project_success_metrics": self._get_default_section("project_success_metrics"),
            "technical_analysis": self._get_default_section("technical_analysis"),
            "design_analysis": self._get_default_section("design_analysis"),
            "risk_assessment": {
                "identified_risks": ["Analysis not available"],
                "risk_mitigation_strategies": ["Standard mitigation"],
                "critical_issues": [],
                "recommended_actions": ["Review project data"]
            },
            "performance_analysis": {
                "loading_performance": "Not assessed",
                "rendering_performance": "Not assessed",
                "optimization_opportunities": ["Consider performance optimization"],
                "browser_compatibility": "Not tested"
            },
            "accessibility_analysis": {
                "wcag_compliance": "Not assessed",
                "accessibility_score": 0.7,
                "accessibility_improvements": ["Consider accessibility testing"],
                "screen_reader_compatibility": "Not tested"
            },
            "future_recommendations": self._get_default_section("future_recommendations"),
            "executive_summary": "Project completed with standard implementation",
            "technical_summary": "Technical implementation follows standard practices",
            "confidence_level": 0.5
        }
    
    def generate_report_content_advanced(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report content using advanced prompt engineering"""
        
        # Build sophisticated content generation prompt
        prompt = self._build_advanced_content_prompt(project_data, analysis_result)
        
        # Call Claude with advanced reasoning
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        
        # Parse the response
        return self._parse_advanced_content_response(response, project_data, analysis_result)
    
    def _build_advanced_content_prompt(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """Build sophisticated prompt for advanced report content generation"""
        
        prompt = f"""
You are an expert technical writer and documentation specialist with deep knowledge of UI/UX design, web development, and project management. Your task is to create comprehensive, professional report content based on project data and analysis.

## PROJECT DATA
{json.dumps(project_data, indent=2)}

## ANALYSIS RESULTS
{json.dumps(analysis_result, indent=2)}

## CONTENT GENERATION TASK
Create comprehensive report content that includes:

1. **Executive Summary**: High-level overview for business stakeholders
2. **Project Overview**: Detailed project information and objectives
3. **Requirements Analysis**: Comprehensive analysis of user requirements
4. **Technical Implementation**: Detailed technical approach and decisions
5. **Design Analysis**: Analysis of design decisions and user experience
6. **Results and Outcomes**: Project results and success metrics
7. **Risk Assessment**: Identified risks and mitigation strategies
8. **Performance Analysis**: Technical performance and optimization
9. **Accessibility Analysis**: Accessibility compliance and improvements
10. **Recommendations**: Actionable recommendations for future improvements
11. **Technical Details**: Detailed technical specifications and code analysis
12. **Appendices**: Supporting documentation and references

## OUTPUT FORMAT
Return a JSON object with this exact structure:
{{
    "executive_summary": {{
        "overview": "string (high-level project overview)",
        "key_achievements": ["list", "of", "key", "achievements"],
        "success_metrics": "string (summary of success metrics)",
        "business_impact": "string (business impact assessment)"
    }},
    "project_overview": {{
        "project_details": "string (detailed project information)",
        "objectives": ["list", "of", "project", "objectives"],
        "timeline": "string (project timeline)",
        "stakeholders": ["list", "of", "stakeholders"]
    }},
    "requirements_analysis": {{
        "user_requirements": "string (detailed user requirements analysis)",
        "technical_requirements": "string (technical requirements analysis)",
        "constraints": ["list", "of", "constraints"],
        "assumptions": ["list", "of", "assumptions"]
    }},
    "technical_implementation": {{
        "approach": "string (technical approach description)",
        "architecture": "string (system architecture)",
        "technologies_used": ["list", "of", "technologies"],
        "implementation_details": "string (detailed implementation information)"
    }},
    "design_analysis": {{
        "design_decisions": "string (analysis of design decisions)",
        "user_experience": "string (user experience analysis)",
        "visual_design": "string (visual design analysis)",
        "interaction_design": "string (interaction design analysis)"
    }},
    "results_and_outcomes": {{
        "project_results": "string (detailed project results)",
        "success_metrics": "string (success metrics analysis)",
        "user_feedback": "string (user feedback analysis)",
        "quality_assessment": "string (quality assessment)"
    }},
    "risk_assessment": {{
        "identified_risks": "string (detailed risk analysis)",
        "mitigation_strategies": "string (risk mitigation strategies)",
        "risk_monitoring": "string (risk monitoring approach)"
    }},
    "performance_analysis": {{
        "performance_metrics": "string (performance metrics analysis)",
        "optimization_opportunities": "string (optimization opportunities)",
        "benchmarking": "string (performance benchmarking)"
    }},
    "accessibility_analysis": {{
        "compliance_assessment": "string (accessibility compliance assessment)",
        "improvements": "string (accessibility improvements)",
        "testing_results": "string (accessibility testing results)"
    }},
    "recommendations": {{
        "immediate_actions": "string (immediate action recommendations)",
        "long_term_strategy": "string (long-term strategy recommendations)",
        "continuous_improvement": "string (continuous improvement recommendations)"
    }},
    "technical_details": {{
        "code_analysis": "string (detailed code analysis)",
        "architecture_details": "string (architecture details)",
        "deployment_info": "string (deployment information)",
        "maintenance_guide": "string (maintenance guide)"
    }},
    "appendices": {{
        "references": ["list", "of", "references"],
        "glossary": "string (technical glossary)",
        "supporting_documents": ["list", "of", "supporting", "documents"]
    }}
}}

## CHAIN-OF-THOUGHT PROCESS
Think through this systematically:
1. **Data Synthesis**: Combine project data and analysis results
2. **Stakeholder Consideration**: Create content for different stakeholder types
3. **Technical Depth**: Provide appropriate technical detail
4. **Business Value**: Emphasize business impact and value
5. **Actionability**: Ensure recommendations are actionable
6. **Professional Tone**: Maintain professional, authoritative tone
7. **Completeness**: Ensure all aspects are covered comprehensively
8. **Clarity**: Ensure content is clear and accessible

Remember: Create content that serves both technical and business stakeholders while maintaining professional standards.
"""
        
        return prompt
    
    def _parse_advanced_content_response(self, response: str, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the advanced content response"""
        
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_response = json.loads(json_str)
                
                # Validate required sections
                required_sections = ["executive_summary", "project_overview", "requirements_analysis", "recommendations"]
                for section in required_sections:
                    if section not in parsed_response:
                        parsed_response[section] = self._get_default_content_section(section)
                
                return parsed_response
            else:
                return self._get_default_content_result(project_data, analysis_result)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing advanced content response: {e}")
            return self._get_default_content_result(project_data, analysis_result)
    
    def _get_default_content_section(self, section: str) -> Dict[str, Any]:
        """Get default content for missing sections"""
        defaults = {
            "executive_summary": {
                "overview": "Project completed successfully",
                "key_achievements": ["Project objectives met"],
                "success_metrics": "Standard success metrics achieved",
                "business_impact": "Positive business impact"
            },
            "project_overview": {
                "project_details": "Standard project implementation",
                "objectives": ["Meet user requirements"],
                "timeline": "Project completed on time",
                "stakeholders": ["Project team", "End users"]
            },
            "requirements_analysis": {
                "user_requirements": "User requirements analyzed and implemented",
                "technical_requirements": "Technical requirements met",
                "constraints": ["Standard constraints applied"],
                "assumptions": ["Standard assumptions made"]
            },
            "recommendations": {
                "immediate_actions": "Consider user feedback for improvements",
                "long_term_strategy": "Plan for scalability and growth",
                "continuous_improvement": "Implement continuous improvement process"
            }
        }
        return defaults.get(section, {})
    
    def _get_default_content_result(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Return default content result when parsing fails"""
        return {
            "executive_summary": self._get_default_content_section("executive_summary"),
            "project_overview": self._get_default_content_section("project_overview"),
            "requirements_analysis": self._get_default_content_section("requirements_analysis"),
            "technical_implementation": {
                "approach": "Standard technical approach",
                "architecture": "Standard architecture",
                "technologies_used": ["Standard technologies"],
                "implementation_details": "Standard implementation"
            },
            "design_analysis": {
                "design_decisions": "Standard design decisions",
                "user_experience": "Good user experience",
                "visual_design": "Good visual design",
                "interaction_design": "Good interaction design"
            },
            "results_and_outcomes": {
                "project_results": "Project completed successfully",
                "success_metrics": "Standard success metrics",
                "user_feedback": "Positive user feedback",
                "quality_assessment": "Good quality assessment"
            },
            "recommendations": self._get_default_content_section("recommendations"),
            "technical_details": {
                "code_analysis": "Standard code analysis",
                "architecture_details": "Standard architecture",
                "deployment_info": "Standard deployment",
                "maintenance_guide": "Standard maintenance"
            },
            "appendices": {
                "references": ["Standard references"],
                "glossary": "Standard glossary",
                "supporting_documents": ["Standard documents"]
            }
        }
    
    def create_advanced_pdf_report(self, report_content: Dict[str, Any], project_data: Dict[str, Any]) -> str:
        """Create advanced PDF report with sophisticated formatting"""
        
        # TODO: Implement sophisticated PDF generation
        # This would include:
        # - Advanced PDF formatting with professional styling
        # - Charts and graphs for metrics visualization
        # - Code syntax highlighting
        # - Interactive elements
        # - Professional branding and layout
        
        filename = f"advanced_ui_project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("reports", filename)
        
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)
        
        print(f"TODO: Generate advanced PDF report at {filepath}")
        print(f"Report content sections: {list(report_content.keys())}")
        
        # TODO: Implement advanced PDF generation with:
        # - Professional formatting and styling
        # - Data visualization and charts
        # - Code snippets with syntax highlighting
        # - Executive summary with key metrics
        # - Technical documentation with diagrams
        # - Appendices with supporting materials
        
        return filepath 