#!/usr/bin/env python3
"""
Deterministic file-based report generator (no LLM).
Reads UI code and metadata from temp_ui_files/{session_id} and embeds the latest
screenshot from temp_previews/{session_id} or default.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import logging

from utils.file_manager import UICodeFileManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    def generate(self, session_id: str, report_options: Dict[str, Any], project_info: Dict[str, Any]) -> str:
        logger.info(f"[Report] Generating file-based report for session: {session_id}")

        session_data = self._load_session_data(session_id)
        if not session_data:
            raise RuntimeError(f"Session files not found for {session_id}")

        # Force screenshot refresh to ensure latest preview is used
        screenshot_path = self._ensure_latest_screenshot(session_id)
        if not screenshot_path:
            logger.warning(f"[Report] No screenshot found for session {session_id}; proceeding without preview")

        pdf_filepath = self._create_pdf(
            session_id=session_id,
            report_options=report_options or {},
            session_data=session_data,
            screenshot_path=screenshot_path,
            project_info=project_info or {}
        )
        logger.info(f"[Report] PDF created at: {pdf_filepath}")
        return pdf_filepath

    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        base_dir = os.path.join(os.getcwd(), "temp_ui_files")
        fm = UICodeFileManager(base_dir=base_dir)
        return fm.load_session(session_id)

    def _ensure_latest_screenshot(self, session_id: str) -> Optional[str]:
        """Ensure the latest screenshot is available, generating if necessary"""
        try:
            # First try to find existing screenshots
            screenshot_path = self._find_latest_screenshot(session_id)
            
            # If no screenshot exists, try to generate one
            if not screenshot_path:
                logger.info(f"[Report] No screenshot found for session {session_id}, attempting to generate one...")
                screenshot_path = self._generate_screenshot_for_session(session_id)
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error ensuring latest screenshot for {session_id}: {e}")
            return None
    
    def _generate_screenshot_for_session(self, session_id: str) -> Optional[str]:
        """Generate a screenshot for the session if possible"""
        try:
            from services.screenshot_service import get_screenshot_service
            
            # Get screenshot service
            screenshot_service = get_screenshot_service()
            
            # Try to generate screenshot
            result = screenshot_service.generate_screenshot_for_session(session_id)
            
            if result and result.get("success"):
                # Find the newly generated screenshot
                return self._find_latest_screenshot(session_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating screenshot for session {session_id}: {e}")
            return None
    
    def _find_latest_screenshot(self, session_id: str) -> Optional[str]:
        try:
            previews_root = os.path.join(os.getcwd(), "temp_previews")
            candidates: List[str] = []
            session_dir = os.path.join(previews_root, session_id)
            if os.path.isdir(session_dir):
                for name in os.listdir(session_dir):
                    if name.lower().endswith((".png", ".jpg", ".jpeg")):
                        candidates.append(os.path.join(session_dir, name))
            default_dir = os.path.join(previews_root, "default")
            if not candidates and os.path.isdir(default_dir):
                for name in os.listdir(default_dir):
                    if name.lower().endswith((".png", ".jpg", ".jpeg")):
                        candidates.append(os.path.join(default_dir, name))
            if not candidates:
                return None
            candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return candidates[0]
        except Exception as e:
            logger.error(f"Error finding latest screenshot for {session_id}: {e}")
            return None

    def _create_pdf(
        self,
        session_id: str,
        report_options: Dict[str, Any],
        session_data: Dict[str, Any],
        screenshot_path: Optional[str],
        project_info: Dict[str, Any]
    ) -> str:

        
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)

        filename = f"UI_Mockup_Report_{session_id[:8]}.pdf"
        filepath = os.path.join(report_dir, filename)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=22, alignment=TA_CENTER, spaceAfter=16, textColor=colors.darkblue)
        section_header = styles['Heading2']
        normal = styles['Normal']

        story: List = []

        story.append(Paragraph("UI MOCKUP REPORT", title_style))
        story.append(Spacer(1, 12))

        template_info = session_data.get('template_info', {})
        metadata = session_data.get('metadata', {})
        
        info_rows = [
            ["Session ID", session_id],
            ["Template Name", project_info.get('template_name') or template_info.get('name', 'Unknown')],
            ["Category", project_info.get('category') or template_info.get('category', 'Unknown')],
            ["Created At", metadata.get('created_at', 'Unknown')],
            ["Last Updated", metadata.get('last_updated', 'Unknown')],
        ]
        info_table = Table(info_rows, colWidths=[1.7*inch, 4.3*inch])
        info_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 12))

        if report_options.get('uiPreview'):
            # Force UI Preview to start on its own page
            story.append(PageBreak())
            story.append(Paragraph("UI Preview", section_header))
            story.append(Spacer(1, 6))
            
            if screenshot_path:
                try:
                    # Preserve aspect ratio and fit to page width
                    # Compute max drawable area based on A4 and margins
                    page_w, page_h = landscape(A4)
                    max_w = page_w - (2 * 36)  # match doc left/right margins below
                    max_h = page_h - (2 * 36) - 96  # leave room for header spacing

                    # Load image dimensions to keep aspect ratio
                    try:
                        from PIL import Image as PILImage  # optional, improves sizing accuracy
                        with PILImage.open(screenshot_path) as im:
                            img_w_px, img_h_px = im.size
                    except Exception:
                        # Fallback to a safe default aspect ratio if PIL not available
                        img_w_px, img_h_px = (1920, 1080)

                    aspect = img_h_px / float(img_w_px) if img_w_px else 0.5625
                    target_w = max_w
                    target_h = target_w * aspect
                    if target_h > max_h:
                        target_h = max_h
                        target_w = target_h / aspect if aspect else max_w

                    story.append(Image(screenshot_path, width=target_w, height=target_h))
                    story.append(Spacer(1, 12))
                    # Add page break after UI Preview to ensure it's on its own page
                    story.append(PageBreak())
                except Exception as e:
                    logger.error(f"Failed to embed screenshot: {e}")
                    story.append(Paragraph("[Preview unavailable]", normal))
                    story.append(Spacer(1, 12))
                    # Add page break even if preview is unavailable
                    story.append(PageBreak())
            else:
                story.append(Paragraph("[No screenshot available]", normal))
                story.append(Spacer(1, 12))
                # Add page break even if no screenshot
                story.append(PageBreak())

        if report_options.get('uiCode'):
            # Force UI Code section to start on its own page
            story.append(PageBreak())
            story.append(Paragraph("UI Code (index.html)", section_header))
            story.append(Spacer(1, 6))
            current_codes = session_data.get('current_codes', {})
            html_code = current_codes.get('html_export', '')
            story.append(Paragraph(self._escape(html_code[:8000] or 'No HTML available'), normal))
            story.append(PageBreak())

            story.append(Paragraph("globals.css", section_header))
            story.append(Spacer(1, 6))
            globals_css = current_codes.get('globals_css', '')
            story.append(Paragraph(self._escape(globals_css[:8000] or 'No globals.css available'), normal))
            story.append(PageBreak())

            story.append(Paragraph("style.css", section_header))
            story.append(Spacer(1, 6))
            style_css = current_codes.get('style_css', '')
            story.append(Paragraph(self._escape(style_css[:8000] or 'No style.css available'), normal))
            story.append(Spacer(1, 12))

        if report_options.get('changesMade'):
            # Force Changes Made section to start on its own page
            story.append(PageBreak())
            # Try different possible keys for history data
            history_list = (
                session_data.get('history', []) or 
                session_data.get('modifications', []) or 
                []
            )
            story.append(Paragraph("Changes Made", section_header))
            story.append(Spacer(1, 6))
            if history_list:
                for entry in history_list[-20:]:
                    # Handle different timestamp formats and field names
                    entry_timestamp = entry.get('timestamp', '')
                    if entry_timestamp:
                        # Format timestamp for better readability
                        try:
                            from datetime import datetime
                            if 'T' in entry_timestamp:
                                dt = datetime.fromisoformat(entry_timestamp.replace('Z', '+00:00'))
                                formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                formatted_timestamp = entry_timestamp
                        except:
                            formatted_timestamp = entry_timestamp  # Keep original if parsing fails
                    else:
                        formatted_timestamp = ''
                    
                    # Try different possible field names for the modification description
                    modification = (
                        entry.get('user_request') or 
                        entry.get('modification') or 
                        entry.get('change', 'Unknown change')
                    )
                    
                    text = f"- {formatted_timestamp}: {modification}"
                    story.append(Paragraph(text, normal))
            else:
                story.append(Paragraph("No modifications recorded.", normal))
            story.append(Spacer(1, 12))

        if report_options.get('creationDate'):
            # Force Creation Date section to start on its own page
            story.append(PageBreak())
            story.append(Paragraph("Creation Date", section_header))
            story.append(Spacer(1, 6))
            story.append(Paragraph(metadata.get('created_at', 'Unknown'), normal))
            story.append(Spacer(1, 12))

        # Add Logo Analysis section if logo exists and option is enabled
        if report_options.get('logoAnalysis'):
            try:
                logo_analysis = self._get_logo_analysis(session_id)
                
                if logo_analysis and isinstance(logo_analysis, dict):
                    # Force Logo Analysis section to start on its own page
                    story.append(PageBreak())
                    story.append(Paragraph("Logo Analysis", section_header))
                    story.append(Spacer(1, 6))
                    
                    # Add logo image if available
                    logo_path = logo_analysis.get('logo_path')
                    if logo_path and os.path.exists(logo_path):
                        try:
                            # Display logo at reasonable size
                            logo_width = 2 * inch
                            logo_height = 1.5 * inch
                            story.append(Image(logo_path, width=logo_width, height=logo_height))
                            story.append(Spacer(1, 6))
                        except Exception as e:
                            logger.error(f"Failed to embed logo in report: {e}")
                    
                    # Add analysis details
                    analysis = logo_analysis.get('analysis', {})
                    if analysis and isinstance(analysis, dict):
                        # Logo properties
                        story.append(Paragraph("Logo Properties:", styles['Heading3']))
                        story.append(Spacer(1, 3))
                        dimensions = analysis.get('dimensions', {})
                        if dimensions and isinstance(dimensions, dict):
                            story.append(Paragraph(f"Dimensions: {dimensions.get('width', 0)} × {dimensions.get('height', 0)} pixels", normal))
                        story.append(Paragraph(f"Aspect Ratio: {analysis.get('aspect_ratio', 0)}", normal))
                        story.append(Spacer(1, 6))
                        
                        # Dominant colors
                        dominant_colors = analysis.get('dominant_colors', [])
                        if dominant_colors and isinstance(dominant_colors, list):
                            story.append(Paragraph("Dominant Colors:", styles['Heading3']))
                            story.append(Spacer(1, 3))
                            for i, color in enumerate(dominant_colors[:3]):  # Show top 3 colors
                                if isinstance(color, dict):
                                    hex_color = color.get('hex', '#000000')
                                    percentage = color.get('percentage', 0)
                                    story.append(Paragraph(f"• {hex_color} ({percentage}%)", normal))
                            story.append(Spacer(1, 6))
                        
                        # Color characteristics
                        color_dist = analysis.get('color_distribution', {})
                        if color_dist and isinstance(color_dist, dict):
                            story.append(Paragraph("Color Characteristics:", styles['Heading3']))
                            story.append(Spacer(1, 3))
                            story.append(Paragraph(f"Temperature: {color_dist.get('temperature', 'Unknown')}", normal))
                            story.append(Paragraph(f"Brightness: {analysis.get('brightness', 'Unknown')}", normal))
                            saturation = color_dist.get('saturation', {})
                            if saturation and isinstance(saturation, dict):
                                story.append(Paragraph(f"Saturation: {saturation.get('level', 'Unknown')} ({saturation.get('value', 0)})", normal))
                            story.append(Spacer(1, 6))
                    
                    # Add page break after logo analysis
                    story.append(PageBreak())
                    
            except Exception as e:
                logger.error(f"Error processing logo analysis: {e}")
                # Add a simple error message to the report instead of crashing
                story.append(PageBreak())
                story.append(Paragraph("Logo Analysis", section_header))
                story.append(Spacer(1, 6))
                story.append(Paragraph("Note: Logo analysis data could not be processed due to an error.", normal))
                story.append(Spacer(1, 6))

        # Add Agent Rationale section if option is enabled
        if report_options.get('agentRationale'):
            try:
                rationale_data = self._get_agent_rationale(session_id)
                
                if rationale_data and isinstance(rationale_data, dict):
                    # Force Agent Rationale section to start on its own page
                    story.append(PageBreak())
                    story.append(Paragraph("Agent Decision Rationale", section_header))
                    story.append(Spacer(1, 6))
                    
                    # Process each section with defensive programming
                    
                    # Template Selection Rationale
                    template_rationale = rationale_data.get('template_selection', {})
                    if template_rationale and isinstance(template_rationale, dict) and template_rationale.get('recommendations'):
                        recommendations = template_rationale['recommendations']
                        if isinstance(recommendations, list):
                            story.append(Paragraph("Template Selection Process:", styles['Heading3']))
                            story.append(Spacer(1, 3))
                            
                            # Show recommendations
                            story.append(Paragraph("Template Recommendations:", normal))
                            for i, rec in enumerate(recommendations[:5]):  # Show top 5
                                if isinstance(rec, dict):
                                    # Handle nested template structure
                                    template_data = rec.get('template', rec)
                                    template_name = template_data.get('name', 'Unknown')
                                    score = rec.get('score', 0)
                                    reasoning = rec.get('reasoning', '')
                                    
                                    story.append(Paragraph(f"• {template_name} (Score: {score:.2f})", normal))
                                    if reasoning:
                                        story.append(Paragraph(f"  Reasoning: {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}", normal))
                                    story.append(Spacer(1, 3))
                            
                            # Show final selection if available
                            final_selection = template_rationale.get('final_selection')
                            if final_selection and isinstance(final_selection, dict):
                                story.append(Paragraph("Final Selection:", normal))
                                # Handle nested template structure
                                template_data = final_selection.get('template', final_selection)
                                template_name = template_data.get('name', 'Unknown')
                                story.append(Paragraph(f"• {template_name}", normal))
                                selection_reasoning = final_selection.get('selection_reasoning', '')
                                if selection_reasoning:
                                    story.append(Paragraph(f"  Selection Reason: {selection_reasoning}", normal))
                            
                            story.append(Spacer(1, 6))
                    
                    # UI Editing Rationale
                    ui_rationale = rationale_data.get('ui_editing', {})
                    if ui_rationale and isinstance(ui_rationale, dict) and ui_rationale.get('planning_rationale'):
                        planning_rationale = ui_rationale['planning_rationale']
                        if isinstance(planning_rationale, list):
                            story.append(Paragraph("UI Modification Planning:", styles['Heading3']))
                            story.append(Spacer(1, 3))
                            
                            for i, planning in enumerate(planning_rationale[:3]):  # Show last 3
                                if isinstance(planning, dict):
                                    user_request = planning.get('user_request', 'Unknown')
                                    story.append(Paragraph(f"Request {i+1}: {user_request}", normal))
                                    
                                    intent = planning.get('intent_analysis', {})
                                    if intent and isinstance(intent, dict):
                                        story.append(Paragraph(f"  Intent: {intent.get('user_goal', 'Unknown')}", normal))
                                    
                                    target_identification = planning.get('target_identification', {})
                                    if target_identification and isinstance(target_identification, dict):
                                        primary_target = target_identification.get('primary_target', {})
                                        if primary_target and isinstance(primary_target, dict):
                                            story.append(Paragraph(f"  Target: {primary_target.get('text_content', 'Unknown')}", normal))
                                            story.append(Paragraph(f"  Reasoning: {primary_target.get('reasoning', 'Unknown')}", normal))
                                    
                                    story.append(Spacer(1, 3))
                            
                            story.append(Spacer(1, 6))
                    
                    # Requirements Analysis Rationale
                    requirements_rationale = rationale_data.get('requirements_analysis', [])
                    if requirements_rationale and isinstance(requirements_rationale, list):
                        story.append(Paragraph("Requirements Analysis Process:", styles['Heading3']))
                        story.append(Spacer(1, 3))
                        
                        for i, req in enumerate(requirements_rationale[:3]):  # Show last 3
                            if isinstance(req, dict):
                                analysis_summary = req.get('analysis_summary', 'Unknown')
                                story.append(Paragraph(f"Analysis {i+1}: {analysis_summary}", normal))
                                story.append(Spacer(1, 3))
                        
                        story.append(Spacer(1, 6))
                    
                    # Question Generation Rationale
                    question_rationale = rationale_data.get('question_generation', [])
                    if question_rationale and isinstance(question_rationale, list):
                        story.append(Paragraph("Question Generation Process:", styles['Heading3']))
                        story.append(Spacer(1, 3))
                        
                        for i, q in enumerate(question_rationale[:3]):  # Show last 3
                            if isinstance(q, dict):
                                reasoning = q.get('reasoning', 'Unknown')
                                question_count = len(q.get('questions', []))
                                story.append(Paragraph(f"Question Set {i+1}: Generated {question_count} questions", normal))
                                story.append(Paragraph(f"  Strategy: {reasoning}", normal))
                                story.append(Spacer(1, 3))
                        
                        story.append(Spacer(1, 6))
                    
                    # Workflow Decisions
                    workflow_rationale = rationale_data.get('overall_workflow', {})
                    if workflow_rationale and isinstance(workflow_rationale, dict):
                        # Phase Decisions
                        phase_decisions = workflow_rationale.get('phase_decisions', [])
                        if phase_decisions and isinstance(phase_decisions, list):
                            story.append(Paragraph("Workflow Decision Process:", styles['Heading3']))
                            story.append(Spacer(1, 3))
                            
                            for i, decision in enumerate(phase_decisions[:3]):  # Show last 3
                                if isinstance(decision, dict):
                                    story.append(Paragraph(f"Phase: {decision.get('phase', 'Unknown')}", normal))
                                    story.append(Paragraph(f"  Decision: {decision.get('decision', 'Unknown')}", normal))
                                    reasoning = decision.get('reasoning', '')
                                    if reasoning:
                                        story.append(Paragraph(f"  Reasoning: {reasoning}", normal))
                                    story.append(Spacer(1, 3))
                        
                        # Agent Coordination
                        agent_coordination = workflow_rationale.get('agent_coordination', [])
                        if agent_coordination and isinstance(agent_coordination, list):
                            story.append(Paragraph("Agent Coordination:", styles['Heading3']))
                            story.append(Spacer(1, 3))
                            
                            for i, coord in enumerate(agent_coordination[:3]):  # Show last 3
                                if isinstance(coord, dict):
                                    from_agent = coord.get('from_agent', 'Unknown')
                                    to_agent = coord.get('to_agent', 'Unknown')
                                    action = coord.get('action', 'Unknown')
                                    story.append(Paragraph(f"Coordination {i+1}: {from_agent} → {to_agent}", normal))
                                    story.append(Paragraph(f"  Action: {action}", normal))
                                    story.append(Spacer(1, 3))
                        
                        story.append(Spacer(1, 6))
                    
                    # Add page break after agent rationale
                    story.append(PageBreak())
                
            except Exception as e:
                logger.error(f"Error processing agent rationale: {e}")
                # Add a simple error message to the report instead of crashing
                story.append(PageBreak())
                story.append(Paragraph("Agent Decision Rationale", section_header))
                story.append(Spacer(1, 6))
                story.append(Paragraph("Note: Agent rationale data could not be processed due to an error.", normal))
                story.append(Spacer(1, 6))

        # Use landscape orientation and slightly smaller margins to maximize preview size
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        doc.build(story)
        return filepath

    def _escape(self, text: str) -> str:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def _get_logo_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve logo analysis for a session."""
        try:
            from utils.logo_manager import LogoManager
            logo_manager = LogoManager()
            logo_analysis = logo_manager.get_logo_analysis(session_id)
            return logo_analysis
        except Exception as e:
            logger.error(f"Error retrieving logo analysis for session {session_id}: {e}")
            return None
    
    def _get_agent_rationale(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get agent rationale data for the session"""
        try:
            from utils.rationale_manager import RationaleManager
            rationale_manager = RationaleManager(session_id)
            rationale_data = rationale_manager.load_rationale()
            return rationale_data
        except Exception as e:
            logger.error(f"Failed to get agent rationale: {e}")
            return None


