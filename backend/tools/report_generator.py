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

        screenshot_path = self._find_latest_screenshot(session_id)
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

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"UI_Mockup_Report_{session_id[:8]}_{timestamp}.pdf"
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

        if report_options.get('uiPreview') and screenshot_path:
            story.append(Paragraph("UI Preview", section_header))
            story.append(Spacer(1, 6))
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
            except Exception as e:
                logger.error(f"Failed to embed screenshot: {e}")
                story.append(Paragraph("[Preview unavailable]", normal))
                story.append(Spacer(1, 12))

        if report_options.get('uiCode'):
            story.append(Paragraph("UI Code (index.html)", section_header))
            story.append(Spacer(1, 6))
            html_code = session_data.get('current_codes', {}).get('html_export', '')
            story.append(Paragraph(self._escape(html_code[:8000] or 'No HTML available'), normal))
            story.append(PageBreak())

            story.append(Paragraph("globals.css", section_header))
            story.append(Spacer(1, 6))
            globals_css = session_data.get('current_codes', {}).get('globals_css', '')
            story.append(Paragraph(self._escape(globals_css[:8000] or 'No globals.css available'), normal))
            story.append(PageBreak())

            story.append(Paragraph("style.css", section_header))
            story.append(Spacer(1, 6))
            style_css = session_data.get('current_codes', {}).get('style_css', '')
            story.append(Paragraph(self._escape(style_css[:8000] or 'No style.css available'), normal))
            story.append(Spacer(1, 12))

        if report_options.get('changesMade'):
            history_list = session_data.get('history', [])
            story.append(Paragraph("Changes Made", section_header))
            story.append(Spacer(1, 6))
            if history_list:
                for entry in history_list[-20:]:
                    text = f"- {entry.get('timestamp', '')}: {entry.get('user_request', entry.get('modification', 'change'))}"
                    story.append(Paragraph(text, normal))
            else:
                story.append(Paragraph("No modifications recorded.", normal))
            story.append(Spacer(1, 12))

        if report_options.get('creationDate'):
            story.append(Paragraph("Creation Date", section_header))
            story.append(Spacer(1, 6))
            story.append(Paragraph(metadata.get('created_at', 'Unknown'), normal))
            story.append(Spacer(1, 12))

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


