from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from utils.file_manager import UICodeFileManager

class ReportGenerationAgent(BaseAgent):
    """Professional Business Report Generation Agent for UI Mockup Documentation"""
    
    def __init__(self):
        system_message = """You are a Professional Business Report Generation Agent specializing in UI mockup documentation. You create comprehensive, business-focused reports that document UI design projects with:

1. Executive summaries for stakeholder communication
2. Technical documentation for design decisions
3. Visual comparisons and project metrics
4. Professional formatting suitable for business presentations
5. Clear analysis of user requirements and design choices
6. Chronological documentation of modifications
7. Project success metrics and achievements

You focus on business value, design decisions, and project outcomes rather than technical implementation details."""
        
        super().__init__("ReportGeneration", system_message)
        
        # Add logger
        import logging
        self.logger = logging.getLogger(__name__)
    
    def generate_project_report_advanced(self, project_data: Dict[str, Any]) -> str:
        """Deprecated LLM-based path retained for compatibility. Redirects to file-based generator."""
        session_id = project_data.get('session_id') or 'unknown'
        report_options = project_data.get('report_options') or {}
        project_info = project_data.get('selected_template') or {}
        # Redirect to new tool
        from tools.report_generator import ReportGenerator
        return ReportGenerator().generate(session_id=session_id, report_options=report_options, project_info=project_info)

        session_id = project_data.get('session_id') or 'unknown'
        report_options = project_data.get('report_options') or {}
        project_info = project_data.get('selected_template') or {}
        from tools.report_generator import ReportGenerator
        return ReportGenerator().generate(session_id=session_id, report_options=report_options, project_info=project_info)
    
    def analyze_project_data_advanced(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project data for business report insights"""
        
        prompt = self._build_business_analysis_prompt(project_data)
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        return self._parse_business_analysis_response(response, project_data)
    
    def _build_business_analysis_prompt(self, project_data: Dict[str, Any]) -> str:
        """Build prompt for business-focused project analysis"""
        
        template_info = project_data.get('selected_template', {})
        requirements = project_data.get('user_requirements', {})
        conversation_history = project_data.get('conversation_history', [])
        
        prompt = f"""
You are a business analyst specializing in UI design projects. Analyze this UI mockup project and provide insights for a professional business report.

## PROJECT DATA
- Project Name: {project_data.get('project_name', 'UI Mockup Project')}
- Created Date: {project_data.get('created_date', 'Unknown')}
- Template: {template_info.get('name', 'Unknown')}
- Category: {template_info.get('category', 'Unknown')}
- Figma URL: {template_info.get('figma_url', 'Not provided')}

## USER REQUIREMENTS
{self._format_requirements_for_analysis(requirements)}

## CONVERSATION HISTORY
{self._format_conversation_for_analysis(conversation_history)}

## ANALYSIS TASK
Provide business-focused analysis in this JSON format:
{{
    "project_overview": "Brief description of what was created",
    "key_achievements": ["List of major accomplishments"],
    "project_metrics": {{
        "template_category": "string",
        "modifications_count": number,
        "completion_time": "string",
        "user_satisfaction": "string"
    }},
    "template_analysis": {{
        "selection_reasoning": "Why this template was chosen",
        "template_features": ["Key features of the template"],
        "competitive_advantages": "Why this template over others"
    }},
    "modification_analysis": {{
        "major_changes": ["List of significant modifications"],
        "design_decisions": ["Key design choices made"],
        "user_impact": "How modifications improved user experience"
    }},
    "requirements_fulfillment": {{
        "requirements_met": ["List of requirements successfully addressed"],
        "interpretation_accuracy": "How well requirements were understood",
        "additional_value": "Extra value provided beyond requirements"
    }}
}}

Focus on business value, user experience, and project success metrics.
"""
        
        return prompt
    
    def _format_requirements_for_analysis(self, requirements: Dict[str, Any]) -> str:
        """Format requirements for analysis"""
        if not requirements:
            return "No specific requirements documented"
        
        formatted = []
        for key, value in requirements.items():
            if isinstance(value, list):
                formatted.append(f"- {key}: {', '.join(value)}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_conversation_for_analysis(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Format conversation history for analysis"""
        if not conversation_history:
            return "No conversation history available"
        
        formatted = []
        for msg in conversation_history[-10:]:  # Last 10 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]  # First 200 chars
            formatted.append(f"{role.upper()}: {content}...")
        
        return "\n".join(formatted)
    
    def _parse_business_analysis_response(self, response: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse business analysis response"""
        try:
            result = self._extract_json_from_response(response, "business analysis")
            if result:
                return result
        except Exception as e:
            self.logger.error(f"Error parsing business analysis: {e}")
        
        # Return default analysis if parsing fails
        return self._get_default_business_analysis(project_data)
    
    def _get_default_business_analysis(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get default business analysis when parsing fails"""
        template_info = project_data.get('selected_template', {})
        
        return {
            "project_overview": f"UI mockup created using {template_info.get('name', 'selected template')}",
            "key_achievements": [
                "Template selected and customized",
                "UI mockup generated successfully",
                "Project completed within timeline"
            ],
            "project_metrics": {
                "template_category": template_info.get('category', 'Unknown'),
                "modifications_count": 0,
                "completion_time": "Standard",
                "user_satisfaction": "Project completed successfully"
            },
            "template_analysis": {
                "selection_reasoning": "Template matched user requirements",
                "template_features": ["Professional design", "User-friendly interface"],
                "competitive_advantages": "Best fit for project requirements"
            },
            "modification_analysis": {
                "major_changes": ["Template customization completed"],
                "design_decisions": ["Maintained professional appearance"],
                "user_impact": "Improved user experience through customization"
            },
            "requirements_fulfillment": {
                "requirements_met": ["UI mockup created", "Template selected"],
                "interpretation_accuracy": "Requirements successfully interpreted",
                "additional_value": "Professional quality mockup delivered"
            }
        }
    
    def generate_report_content_advanced(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate professional business report content"""
        
        prompt = self._build_business_content_prompt(project_data, analysis_result)
        response = self.call_claude_with_cot(prompt, enable_cot=True)
        return self._parse_business_content_response(response, project_data, analysis_result)
    
    def _build_business_content_prompt(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """Build prompt for business report content generation"""
        
        template_info = project_data.get('selected_template', {})
        
        prompt = f"""
You are a professional business report writer. Create content for a UI mockup project report using this analysis:

## ANALYSIS DATA
{json.dumps(analysis_result, indent=2)}

## PROJECT CONTEXT
- Template: {template_info.get('name', 'Unknown')}
- Category: {template_info.get('category', 'Unknown')}
- Figma URL: {template_info.get('figma_url', 'Not provided')}

## CONTENT REQUIREMENTS
Generate professional business report content in this JSON format:
{{
    "executive_summary": {{
        "project_overview": "Professional description of the UI mockup project",
        "key_achievements": ["List of major accomplishments in business terms"],
        "project_metrics": {{
            "template_category": "string",
            "modifications_count": number,
            "completion_time": "string",
            "success_indicators": ["List of success metrics"]
        }}
    }},
    "technical_documentation": {{
        "template_analysis": {{
            "template_details": "Comprehensive template information",
            "selection_reasoning": "Professional explanation of template choice",
            "template_features": "Key features and characteristics",
            "competitive_analysis": "Why this template was chosen over alternatives"
        }},
        "modification_history": {{
            "chronological_changes": ["List of changes in order"],
            "before_after_comparison": "Professional comparison of changes",
            "impact_assessment": "Business impact of modifications"
        }},
        "design_decisions": {{
            "requirements_analysis": "How user requirements were interpreted",
            "design_choices": "Professional explanation of design decisions",
            "user_experience_impact": "How decisions improved user experience"
        }}
    }}
}}

Write in professional business language suitable for stakeholders and executives.
Focus on business value, user experience, and project success.
"""
        
        return prompt
    
    def _parse_business_content_response(self, response: str, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse business content response"""
        try:
            result = self._extract_json_from_response(response, "business content")
            if result:
                return result
        except Exception as e:
            self.logger.error(f"Error parsing business content: {e}")
        
        # Return default content if parsing fails
        return self._get_default_business_content(project_data, analysis_result)
    
    def _get_default_business_content(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get default business content when parsing fails"""
        template_info = project_data.get('selected_template', {})
        
        return {
            "executive_summary": {
                "project_overview": f"Successfully created a professional UI mockup using the {template_info.get('name', 'selected template')} template, delivering a high-quality user interface design that meets project requirements.",
                "key_achievements": [
                    "Completed UI mockup generation within project timeline",
                    "Selected optimal template based on user requirements",
                    "Delivered professional-quality design ready for implementation"
                ],
                "project_metrics": {
                    "template_category": template_info.get('category', 'Professional'),
                    "modifications_count": 0,
                    "completion_time": "Efficient project completion",
                    "success_indicators": ["Template selection completed", "Mockup generated successfully"]
                }
            },
            "technical_documentation": {
                "template_analysis": {
                    "template_details": f"The {template_info.get('name', 'selected template')} template was chosen for its professional design and user-friendly interface.",
                    "selection_reasoning": "Template selection was based on alignment with user requirements and project objectives.",
                    "template_features": "Professional design, responsive layout, user-friendly interface",
                    "competitive_analysis": "This template provided the best balance of functionality and design quality for the project requirements."
                },
                "modification_history": {
                    "chronological_changes": ["Template selection completed", "UI mockup generated"],
                    "before_after_comparison": "Project progressed from requirements analysis to completed mockup",
                    "impact_assessment": "Successfully delivered a professional UI mockup that meets user needs"
                },
                "design_decisions": {
                    "requirements_analysis": "User requirements were carefully analyzed and incorporated into the final design",
                    "design_choices": "Design decisions focused on user experience and professional appearance",
                    "user_experience_impact": "The final design provides an intuitive and engaging user experience"
                }
            }
        }
    
    def create_professional_pdf_report(self, report_content: Dict[str, Any], project_data: Dict[str, Any]) -> str:
        """Create a professional business PDF report"""
        
        try:
            # Create report directory if it doesn't exist
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = project_data.get('session_id', 'unknown')[:8]
            filename = f"UI_Mockup_Report_{session_id}_{timestamp}.pdf"
            filepath = os.path.join(report_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            
            # Build story (content)
            story = []
            
            # Add content sections
            story.extend(self._create_executive_summary(report_content, project_data))
            story.append(PageBreak())
            story.extend(self._create_technical_documentation(report_content))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"Professional PDF report created: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating PDF report: {e}")
            return "report_creation_failed.pdf"
    
    def _create_executive_summary(self, report_content: Dict[str, Any], project_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("UI MOCKUP REPORT", title_style))
        story.append(Spacer(1, 20))
        
        # Add current UI screenshot if available
        current_ui_state = project_data.get('current_ui_state', {})
        screenshot_preview = current_ui_state.get('screenshot_preview')
        
        if screenshot_preview:
            try:
                # Convert base64 screenshot to image
                import base64
                from io import BytesIO
                from PIL import Image
                
                # Decode base64 image
                image_data = base64.b64decode(screenshot_preview)
                image = Image.open(BytesIO(image_data))
                
                # Save to temporary file
                session_id = project_data.get('session_id', 'unknown')[:8]
                temp_image_path = f"temp_screenshot_{session_id}.png"
                image.save(temp_image_path)
                
                # Add screenshot to report
                story.append(Paragraph("Current UI Mockup", styles['Heading3']))
                story.append(Spacer(1, 12))
                
                # Add image to report (scale to fit page width)
                img = Image(temp_image_path, width=5*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 20))
                
                # Clean up temporary file
                os.remove(temp_image_path)
                
            except Exception as e:
                self.logger.error(f"Error adding screenshot to report: {e}")
                # Continue without screenshot if there's an error
        
        # Executive Summary Header
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Project Overview
        exec_summary = report_content.get('executive_summary', {})
        overview = exec_summary.get('project_overview', 'Project overview not available.')
        story.append(Paragraph(f"<b>Project Overview:</b> {overview}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Key Achievements
        achievements = exec_summary.get('key_achievements', [])
        if achievements:
            story.append(Paragraph("<b>Key Achievements:</b>", styles['Normal']))
            for achievement in achievements:
                story.append(Paragraph(f"• {achievement}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Project Metrics
        metrics = exec_summary.get('project_metrics', {})
        if metrics:
            story.append(Paragraph("<b>Project Metrics:</b>", styles['Normal']))
            metrics_data = [
                ["Template Category", metrics.get('template_category', 'N/A')],
                ["Modifications Count", str(metrics.get('modifications_count', 0))],
                ["Completion Time", metrics.get('completion_time', 'N/A')]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2*inch, 3*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metrics_table)
        
        return story
    
    def _create_technical_documentation(self, report_content: Dict[str, Any]) -> List:
        """Create technical documentation section"""
        story = []
        styles = getSampleStyleSheet()
        
        # Technical Documentation Header
        story.append(Paragraph("Technical Documentation", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        tech_doc = report_content.get('technical_documentation', {})
        
        # Template Analysis
        template_analysis = tech_doc.get('template_analysis', {})
        if template_analysis:
            story.append(Paragraph("Template Analysis", styles['Heading3']))
            story.append(Spacer(1, 12))
            
            details = template_analysis.get('template_details', '')
            if details:
                story.append(Paragraph(f"<b>Template Details:</b> {details}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            reasoning = template_analysis.get('selection_reasoning', '')
            if reasoning:
                story.append(Paragraph(f"<b>Selection Reasoning:</b> {reasoning}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            features = template_analysis.get('template_features', '')
            if features:
                story.append(Paragraph(f"<b>Template Features:</b> {features}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            competitive = template_analysis.get('competitive_analysis', '')
            if competitive:
                story.append(Paragraph(f"<b>Competitive Analysis:</b> {competitive}", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Modification History
        modification_history = tech_doc.get('modification_history', {})
        if modification_history:
            story.append(Paragraph("Modification History", styles['Heading3']))
            story.append(Spacer(1, 12))
            
            changes = modification_history.get('chronological_changes', [])
            if changes:
                story.append(Paragraph("<b>Chronological Changes:</b>", styles['Normal']))
                for change in changes:
                    story.append(Paragraph(f"• {change}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            comparison = modification_history.get('before_after_comparison', '')
            if comparison:
                story.append(Paragraph(f"<b>Before/After Comparison:</b> {comparison}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            impact = modification_history.get('impact_assessment', '')
            if impact:
                story.append(Paragraph(f"<b>Impact Assessment:</b> {impact}", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Design Decisions
        design_decisions = tech_doc.get('design_decisions', {})
        if design_decisions:
            story.append(Paragraph("Design Decisions", styles['Heading3']))
            story.append(Spacer(1, 12))
            
            requirements = design_decisions.get('requirements_analysis', '')
            if requirements:
                story.append(Paragraph(f"<b>Requirements Analysis:</b> {requirements}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            choices = design_decisions.get('design_choices', '')
            if choices:
                story.append(Paragraph(f"<b>Design Choices:</b> {choices}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            ux_impact = design_decisions.get('user_experience_impact', '')
            if ux_impact:
                story.append(Paragraph(f"<b>User Experience Impact:</b> {ux_impact}", styles['Normal']))
        
        return story 
    
    def _extract_json_from_response(self, response: str, context: str = "response") -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        try:
            # Find JSON content in the response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                # Clean the JSON string
                json_str = self._clean_json_string(json_str)
                
                # Parse JSON
                return json.loads(json_str)
            else:
                self.logger.warning(f"No JSON found in {context}")
                return None
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from {context}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting JSON from {context}: {e}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string for parsing"""
        # Remove any markdown formatting
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        
        # Remove any leading/trailing whitespace
        json_str = json_str.strip()
        
        return json_str 