from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import base64
from io import BytesIO

class ReportGenerationAgent(BaseAgent):
    """Agent that generates PDF reports documenting the UI generation process"""
    
    def __init__(self):
        system_message = """You are a Report Generation Agent specialized in:
1. Creating comprehensive PDF reports documenting UI generation processes
2. Explaining reasoning behind design decisions and template selections
3. Documenting modification choices and their impact
4. Providing professional, well-structured reports
5. Including visual elements and code snippets in reports

Always create clear, professional reports that explain the decision-making process."""
        
        super().__init__("ReportGeneration", system_message)
    
    def generate_project_report(self, project_data: Dict[str, Any]) -> str:
        """Generate a comprehensive PDF report for the UI project"""
        
        # Create PDF file
        filename = f"ui_project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("reports", filename)
        
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("UI Mockup Generation Report", title_style))
        story.append(Spacer(1, 20))
        
        # Project Overview
        story.extend(self._create_project_overview(project_data, styles))
        story.append(Spacer(1, 20))
        
        # Requirements Analysis
        story.extend(self._create_requirements_section(project_data, styles))
        story.append(Spacer(1, 20))
        
        # Template Selection
        story.extend(self._create_template_selection_section(project_data, styles))
        story.append(Spacer(1, 20))
        
        # Modifications Applied
        story.extend(self._create_modifications_section(project_data, styles))
        story.append(Spacer(1, 20))
        
        # Final Result
        story.extend(self._create_final_result_section(project_data, styles))
        story.append(Spacer(1, 20))
        
        # Technical Details
        story.extend(self._create_technical_details_section(project_data, styles))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def _create_project_overview(self, project_data: Dict[str, Any], styles) -> List:
        """Create project overview section"""
        
        story = []
        
        # Section title
        story.append(Paragraph("Project Overview", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Project details table
        overview_data = [
            ["Project Name", project_data.get("project_name", "UI Mockup Project")],
            ["Generated Date", datetime.now().strftime("%B %d, %Y")],
            ["Project Type", project_data.get("project_type", "Web UI")],
            ["Status", "Completed"]
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_requirements_section(self, project_data: Dict[str, Any], styles) -> List:
        """Create requirements analysis section"""
        
        story = []
        
        # Section title
        story.append(Paragraph("Requirements Analysis", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # User requirements
        user_requirements = project_data.get("user_requirements", {})
        
        story.append(Paragraph("User Requirements:", styles['Heading3']))
        story.append(Spacer(1, 6))
        
        requirements_text = f"""
        <b>Page Type:</b> {user_requirements.get('page_type', 'Not specified')}<br/>
        <b>Style Preferences:</b> {', '.join(user_requirements.get('style_preferences', ['Not specified']))}<br/>
        <b>Key Features:</b> {', '.join(user_requirements.get('key_features', ['Not specified']))}<br/>
        <b>Target Audience:</b> {user_requirements.get('target_audience', 'Not specified')}<br/>
        <b>Brand Elements:</b> {', '.join(user_requirements.get('brand_elements', ['Not specified']))}
        """
        
        story.append(Paragraph(requirements_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # UI Specifications
        ui_specs = project_data.get("ui_specifications", {})
        if ui_specs:
            story.append(Paragraph("UI Specifications:", styles['Heading3']))
            story.append(Spacer(1, 6))
            
            specs_text = f"""
            <b>Layout Type:</b> {ui_specs.get('layout_type', 'Not specified')}<br/>
            <b>Overall Style:</b> {ui_specs.get('style_preferences', {}).get('overall_style', 'Not specified')}<br/>
            <b>Required Components:</b> {', '.join(ui_specs.get('components', {}).get('required_elements', ['Not specified']))}<br/>
            <b>Interactive Elements:</b> {', '.join(ui_specs.get('components', {}).get('interactive_elements', ['Not specified']))}
            """
            
            story.append(Paragraph(specs_text, styles['Normal']))
        
        return story
    
    def _create_template_selection_section(self, project_data: Dict[str, Any], styles) -> List:
        """Create template selection section"""
        
        story = []
        
        # Section title
        story.append(Paragraph("Template Selection", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Selected template
        selected_template = project_data.get("selected_template", {})
        if selected_template:
            story.append(Paragraph("Selected Template:", styles['Heading3']))
            story.append(Spacer(1, 6))
            
            template_text = f"""
            <b>Template Name:</b> {selected_template.get('title', 'Unknown')}<br/>
            <b>Category:</b> {selected_template.get('category', 'Unknown')}<br/>
            <b>Description:</b> {selected_template.get('description', 'No description available')}<br/>
            <b>Tags:</b> {', '.join(selected_template.get('tags', []))}
            """
            
            story.append(Paragraph(template_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Selection reasoning
        reasoning = project_data.get("template_selection_reasoning", "")
        if reasoning:
            story.append(Paragraph("Selection Reasoning:", styles['Heading3']))
            story.append(Spacer(1, 6))
            story.append(Paragraph(reasoning, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Alternative templates considered
        alternatives = project_data.get("alternative_templates", [])
        if alternatives:
            story.append(Paragraph("Alternative Templates Considered:", styles['Heading3']))
            story.append(Spacer(1, 6))
            
            alt_data = [["Template", "Score", "Reasoning"]]
            for alt in alternatives[:3]:  # Top 3 alternatives
                template = alt.get("template", {})
                alt_data.append([
                    template.get("title", "Unknown"),
                    f"{alt.get('score', 0):.1%}",
                    alt.get("reasoning", "No reasoning provided")
                ])
            
            alt_table = Table(alt_data, colWidths=[2*inch, 1*inch, 3*inch])
            alt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(alt_table)
        
        return story
    
    def _create_modifications_section(self, project_data: Dict[str, Any], styles) -> List:
        """Create modifications section"""
        
        story = []
        
        # Section title
        story.append(Paragraph("Modifications Applied", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        modifications = project_data.get("modifications", [])
        if modifications:
            for i, mod in enumerate(modifications, 1):
                story.append(Paragraph(f"Modification {i}:", styles['Heading3']))
                story.append(Spacer(1, 6))
                
                mod_text = f"""
                <b>Type:</b> {mod.get('modification_type', 'Unknown')}<br/>
                <b>Priority:</b> {mod.get('priority', 'Medium')}<br/>
                <b>Overall Intent:</b> {mod.get('overall_intent', 'Not specified')}<br/>
                <b>Confidence Score:</b> {mod.get('confidence_score', 0):.1%}
                """
                
                story.append(Paragraph(mod_text, styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Specific changes
                specific_changes = mod.get("specific_changes", [])
                if specific_changes:
                    story.append(Paragraph("Specific Changes:", styles['Heading4']))
                    story.append(Spacer(1, 6))
                    
                    changes_data = [["Element", "Change Type", "New Value", "Reasoning"]]
                    for change in specific_changes:
                        changes_data.append([
                            change.get("element_selector", "Unknown"),
                            change.get("change_type", "Unknown"),
                            change.get("new_value", "Not specified"),
                            change.get("reasoning", "No reasoning provided")
                        ])
                    
                    changes_table = Table(changes_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
                    changes_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(changes_table)
                
                story.append(Spacer(1, 12))
        else:
            story.append(Paragraph("No modifications were applied to the template.", styles['Normal']))
        
        return story
    
    def _create_final_result_section(self, project_data: Dict[str, Any], styles) -> List:
        """Create final result section"""
        
        story = []
        
        # Section title
        story.append(Paragraph("Final Result", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Final template info
        final_template = project_data.get("final_template", {})
        if final_template:
            story.append(Paragraph("Final Template Details:", styles['Heading3']))
            story.append(Spacer(1, 6))
            
            final_text = f"""
            <b>Template Name:</b> {final_template.get('title', 'Unknown')}<br/>
            <b>Category:</b> {final_template.get('category', 'Unknown')}<br/>
            <b>Total Modifications:</b> {len(final_template.get('modification_history', []))}<br/>
            <b>Final Status:</b> Approved and Complete
            """
            
            story.append(Paragraph(final_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Validation results
        validation = project_data.get("validation_results", {})
        if validation:
            story.append(Paragraph("Validation Results:", styles['Heading3']))
            story.append(Spacer(1, 6))
            
            validation_text = f"""
            <b>Overall Status:</b> {'Valid' if validation.get('is_valid', False) else 'Invalid'}<br/>
            <b>Errors:</b> {len(validation.get('errors', []))}<br/>
            <b>Warnings:</b> {len(validation.get('warnings', []))}<br/>
            <b>Changes Summary:</b> {', '.join(validation.get('changes_summary', []))}
            """
            
            story.append(Paragraph(validation_text, styles['Normal']))
            
            # Show errors and warnings if any
            errors = validation.get('errors', [])
            warnings = validation.get('warnings', [])
            
            if errors:
                story.append(Spacer(1, 6))
                story.append(Paragraph("Errors:", styles['Heading4']))
                for error in errors:
                    story.append(Paragraph(f"• {error}", styles['Normal']))
            
            if warnings:
                story.append(Spacer(1, 6))
                story.append(Paragraph("Warnings:", styles['Heading4']))
                for warning in warnings:
                    story.append(Paragraph(f"• {warning}", styles['Normal']))
        
        return story
    
    def _create_technical_details_section(self, project_data: Dict[str, Any], styles) -> List:
        """Create technical details section"""
        
        story = []
        
        # Section title
        story.append(Paragraph("Technical Details", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Agent information
        story.append(Paragraph("Agent Information:", styles['Heading3']))
        story.append(Spacer(1, 6))
        
        agents_used = [
            "User Proxy Agent",
            "Requirement Understanding Agent", 
            "UI Recommender Agent",
            "UI Modification Agent",
            "UI Editing Agent",
            "Report Generation Agent"
        ]
        
        agent_text = "<br/>".join([f"• {agent}" for agent in agents_used])
        story.append(Paragraph(agent_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Process timeline
        story.append(Paragraph("Process Timeline:", styles['Heading3']))
        story.append(Spacer(1, 6))
        
        timeline = [
            "Phase 1: Requirements Analysis and Template Selection",
            "Phase 2: Template Modification and User Feedback",
            "Phase 3: Final Validation and Report Generation"
        ]
        
        timeline_text = "<br/>".join([f"• {step}" for step in timeline])
        story.append(Paragraph(timeline_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # File information
        story.append(Paragraph("Generated Files:", styles['Heading3']))
        story.append(Spacer(1, 6))
        
        files = [
            "HTML Template",
            "CSS Stylesheet", 
            "Preview HTML",
            "Project Report (this document)"
        ]
        
        files_text = "<br/>".join([f"• {file}" for file in files])
        story.append(Paragraph(files_text, styles['Normal']))
        
        return story
    
    def generate_summary_report(self, project_data: Dict[str, Any]) -> str:
        """Generate a brief summary report"""
        
        summary = {
            "project_name": project_data.get("project_name", "UI Mockup Project"),
            "generated_date": datetime.now().isoformat(),
            "template_selected": project_data.get("selected_template", {}).get("title", "Unknown"),
            "total_modifications": len(project_data.get("modifications", [])),
            "final_status": "Completed",
            "validation_status": "Valid" if project_data.get("validation_results", {}).get("is_valid", False) else "Invalid"
        }
        
        return json.dumps(summary, indent=2) 