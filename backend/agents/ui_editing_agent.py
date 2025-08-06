from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
import re
from tools.tool_utility import ToolUtility
from config.keyword_config import KeywordManager
from bs4 import BeautifulSoup
import html

class UIEditingAgent(BaseAgent):
    """Advanced UI Editing Agent with sophisticated multi-step architecture"""
    
    def __init__(self):
        # Initialize the main agent (will be used for coordination)
        system_message = """You are an Advanced UI mockup Editing Agent specialized in:
1. Coordinating between planning and execution phases
2. Managing user interactions and clarifications
3. Ensuring high-quality UI modifications

You focus on sophisticated mockup UI modifications and improvements."""
        
        super().__init__("UIEditing", system_message, model="claude-3-5-haiku-20241022")
        self.tool_utility = ToolUtility("ui_editing_agent")
        self.keyword_manager = KeywordManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized agents
        self.planner_agent = PlannerAgent()
        self.executor_agent = ExecutorAgent()
    
    def _analyze_html_structure_with_beautifulsoup(self, html_content: str) -> Dict[str, Any]:
        """Enhanced HTML structure analysis using BeautifulSoup for robust DOM parsing"""
        analysis = {
            "elements_by_text": {},
            "elements_by_class": {},
            "elements_by_id": {},
            "header_elements": [],
            "navigation_elements": [],
            "content_elements": [],
            "debug_info": {
                "total_elements_found": 0,
                "text_elements_found": 0,
                "sample_texts": [],
                "dom_structure": {}
            }
        }
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all text elements with their context
            # Focus on elements that are likely to contain meaningful text
            text_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div', 'a', 'button', 'label'])
            
            for element in text_elements:
                # Get the direct text content of this element (not from children)
                direct_text = ''.join([text for text in element.contents if isinstance(text, str)]).strip()
                
                # If no direct text, get the full text content
                if not direct_text:
                    direct_text = element.get_text(strip=True)
                
                if direct_text and len(direct_text) > 0:
                    # Get element information
                    tag_name = element.name
                    classes = element.get('class', [])
                    element_id = element.get('id')
                    
                    # Handle cases where class is a string instead of list
                    if isinstance(classes, str):
                        classes = [classes]
                    
                    # Get full attributes for context
                    attrs = dict(element.attrs)
                    
                    # Store by text content (use text as key)
                    analysis["elements_by_text"][direct_text] = {
                        "tag": tag_name,
                        "classes": classes,
                        "id": element_id,
                        "full_attrs": attrs,
                        "parent_context": self._get_parent_context(element),
                        "siblings": self._get_sibling_context(element)
                    }
                    
                    # Store by class
                    for cls in classes:
                        if cls not in analysis["elements_by_class"]:
                            analysis["elements_by_class"][cls] = []
                        analysis["elements_by_class"][cls].append({
                            "text": direct_text,
                            "tag": tag_name,
                            "id": element_id,
                            "parent_context": self._get_parent_context(element)
                        })
                    
                    # Store by ID if present
                    if element_id:
                        analysis["elements_by_id"][element_id] = {
                            "text": direct_text,
                            "tag": tag_name,
                            "classes": classes,
                            "full_attrs": attrs,
                            "parent_context": self._get_parent_context(element)
                        }
                    
                    # Add to debug info
                    analysis["debug_info"]["total_elements_found"] += 1
                    if len(analysis["debug_info"]["sample_texts"]) < 20:
                        analysis["debug_info"]["sample_texts"].append(direct_text)
            
            analysis["debug_info"]["text_elements_found"] = len(analysis["elements_by_text"])
            
            # Build DOM structure for better context
            analysis["debug_info"]["dom_structure"] = self._build_dom_structure(soup)
            
            # Identify header-related elements
            header_keywords = ["header", "nav", "logo", "menu", "navigation", "hero", "banner"]
            for text, info in analysis["elements_by_text"].items():
                try:
                    for keyword in header_keywords:
                        if (keyword.lower() in text.lower() or 
                            any(keyword.lower() in cls.lower() for cls in info.get("classes", [])) or
                            keyword.lower() in str(info.get("parent_context", "")).lower()):
                            analysis["header_elements"].append({
                                "text": text,
                                "tag": info.get("tag", "unknown"),
                                "classes": info.get("classes", []),
                                "id": info.get("id"),
                                "parent_context": info.get("parent_context")
                            })
                            break
                except Exception as e:
                    self.logger.warning(f"Error processing header element {text}: {e}")
                    continue
            
            # Identify navigation elements
            nav_keywords = ["nav", "menu", "ul", "li", "a"]
            for text, info in analysis["elements_by_text"].items():
                try:
                    if info.get("tag", "").lower() in nav_keywords:
                        analysis["navigation_elements"].append({
                            "text": text,
                            "tag": info.get("tag", "unknown"),
                            "classes": info.get("classes", []),
                            "id": info.get("id"),
                            "parent_context": info.get("parent_context")
                        })
                except Exception as e:
                    self.logger.warning(f"Error processing navigation element {text}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error analyzing HTML structure with BeautifulSoup: {e}")
        
        return analysis
    
    def _get_parent_context(self, element) -> str:
        """Get context from parent elements"""
        context_parts = []
        parent = element.parent
        
        # Go up to 3 levels to get context
        for i in range(3):
            if parent and parent.name:
                context_parts.append(f"{parent.name}")
                if parent.get('class'):
                    classes = parent.get('class')
                    if isinstance(classes, list):
                        context_parts.append(f".{'.'.join(classes)}")
                    else:
                        context_parts.append(f".{classes}")
                if parent.get('id'):
                    context_parts.append(f"#{parent.get('id')}")
                parent = parent.parent
            else:
                break
        
        return " > ".join(reversed(context_parts))
    
    def _get_sibling_context(self, element) -> List[str]:
        """Get context from sibling elements"""
        siblings = []
        if element.parent:
            for sibling in element.parent.find_all(recursive=False):
                if sibling != element and sibling.name:
                    sibling_text = sibling.get_text(strip=True)
                    if sibling_text:
                        siblings.append(f"{sibling.name}: {sibling_text[:50]}")
        return siblings[:3]  # Limit to 3 siblings
    
    def _build_dom_structure(self, soup) -> Dict[str, Any]:
        """Build a simplified DOM structure for context"""
        structure = {}
        
        # Get main sections
        main_sections = soup.find_all(['header', 'nav', 'main', 'section', 'div'], class_=True)
        
        for section in main_sections[:10]:  # Limit to 10 main sections
            section_classes = section.get('class', [])
            if isinstance(section_classes, str):
                section_classes = [section_classes]
            
            section_key = f"{section.name}.{'.'.join(section_classes)}"
            structure[section_key] = {
                "tag": section.name,
                "classes": section_classes,
                "text_elements": [elem.strip() for elem in section.get_text().split('\n') if elem.strip()][:5]
            }
        
        return structure
    
    def _find_element_by_text_content(self, target_text: str, html_analysis: Dict[str, Any]) -> List[str]:
        """Find CSS selectors for elements containing specific text"""
        selectors = []
        
        # Direct text match
        if target_text in html_analysis["elements_by_text"]:
            element_info = html_analysis["elements_by_text"][target_text]
            if element_info.get("classes"):
                for cls in element_info["classes"]:
                    selectors.append(f".{cls}")
            else:
                selectors.append(element_info.get("tag", "div"))
        
        # Partial text match
        for text, element_info in html_analysis["elements_by_text"].items():
            if target_text.lower() in text.lower():
                if element_info.get("classes"):
                    for cls in element_info["classes"]:
                        selectors.append(f".{cls}")
                else:
                    selectors.append(element_info.get("tag", "div"))
        
        # Look for elements in header/navigation that might contain the text
        for element in html_analysis["header_elements"]:
            if target_text.lower() in element["text"].lower():
                if element.get("classes"):
                    for cls in element["classes"]:
                        selectors.append(f".{cls}")
        
        return list(set(selectors))  # Remove duplicates
    
    def _generate_css_selector_strategy(self, target_text: str, html_analysis: Dict[str, Any]) -> List[str]:
        """Generate multiple CSS selector strategies for finding an element"""
        strategies = []
        
        # Strategy 1: Direct text content match
        direct_selectors = self._find_element_by_text_content(target_text, html_analysis)
        strategies.extend(direct_selectors)
        
        # Strategy 2: Look for common patterns
        if "logo" in target_text.lower():
            logo_selectors = []
            for cls in html_analysis["elements_by_class"].keys():
                if "logo" in cls.lower():
                    logo_selectors.append(f".{cls}")
            strategies.extend(logo_selectors)
        
        # Strategy 3: Header-specific selectors
        if any(keyword in target_text.lower() for keyword in ["header", "nav", "menu"]):
            header_selectors = []
            for cls in html_analysis["elements_by_class"].keys():
                if any(keyword in cls.lower() for keyword in ["header", "nav", "menu", "logo"]):
                    header_selectors.append(f".{cls}")
            strategies.extend(header_selectors)
        
        # Strategy 4: Text-based selectors
        text_selectors = []
        for text, info in html_analysis["elements_by_text"].items():
            if target_text.lower() in text.lower():
                if info["classes"]:
                    text_selectors.extend([f".{cls}" for cls in info["classes"]])
        strategies.extend(text_selectors)
        
        return list(set(strategies))  # Remove duplicates
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove control characters and fix common issues"""
        # Remove control characters but preserve newlines and tabs in string values
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        # Escape unescaped newlines and tabs within strings
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        return json_str
    
    def _extract_json_from_response(self, response: str, context: str = "response") -> Optional[Dict[str, Any]]:
        """Robust JSON extraction from LLM responses"""
        try:
            self.logger.debug(f"Extracting JSON from {context}: {response[:200]}...")
            
            # Strategy 1: Find JSON block with markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    json_str = self._clean_json_string(json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Strategy 2: Find first complete JSON object with proper brace matching
            if "{" in response and "}" in response:
                brace_count = 0
                start_pos = -1
                
                for i, char in enumerate(response):
                    if char == "{":
                        if brace_count == 0:
                            start_pos = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_pos >= 0:
                            # Found complete JSON object
                            json_str = response[start_pos:i+1]
                            json_str = self._clean_json_string(json_str)
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
            
            # Strategy 3: Extract content between first { and last } (fallback)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                json_str = self._clean_json_string(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON in {context}: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from {context}: {e}")
            return None
    
    def process_modification_request(self, user_feedback: str, current_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Multi-step modification workflow using Planner-Executor architecture.
        
        This replaces the single-prompt approach with:
        1. BeautifulSoup HTML analysis
        2. Planner Agent creates detailed plan
        3. Executor Agent executes plan step by step
        4. Maintains same input/output interface
        """
        try:
            self.logger.info(f"Starting multi-step modification process for: {user_feedback}")
            
            # Step 1: Enhanced HTML analysis with BeautifulSoup
            html_content = current_template.get('html_export', '')
            html_analysis = self._analyze_html_structure_with_beautifulsoup(html_content)
            
            print(f"DEBUG: BeautifulSoup analysis found {html_analysis['debug_info']['text_elements_found']} text elements")
            
            # Step 2: Planner Agent creates detailed plan
            print(f"DEBUG: Creating modification plan with Planner Agent...")
            plan_result = self.planner_agent.create_modification_plan(
                user_feedback, current_template, html_analysis
            )
            
            if not plan_result.get('success', False):
                return {
                    "success": False,
                    "error": plan_result.get('error', 'Failed to create modification plan'),
                    "original_template": current_template,
                    "user_feedback": user_feedback
                }
            
            modification_plan = plan_result.get('plan', {})
            print(f"DEBUG: Plan created with {len(modification_plan.get('steps', []))} steps")
            
            # Step 3: Check for ambiguity and handle clarification if needed
            if modification_plan.get('requires_clarification', False):
                clarification_options = modification_plan.get('clarification_options', [])
                return {
                    "success": False,
                    "error": "Multiple possible targets found",
                    "original_template": current_template,
                    "user_feedback": user_feedback,
                    "clarification_needed": True,
                    "clarification_options": clarification_options
                }
            
            # Step 4: Executor Agent executes the plan
            print(f"DEBUG: Executing modification plan with Executor Agent...")
            execution_result = self.executor_agent.execute_modification_plan(
                modification_plan, current_template
            )
            
            if not execution_result.get('success', False):
                return {
                    "success": False,
                    "error": execution_result.get('error', 'Failed to execute modification plan'),
                    "original_template": current_template,
                    "user_feedback": user_feedback
                }
            
            # Step 5: Return the successful result
            modified_template = execution_result.get('modified_template', current_template)
            changes_summary = execution_result.get('changes_summary', [])
            
            return {
                "success": True,
                "modified_template": modified_template,
                "changes_summary": changes_summary
            }
            
        except Exception as e:
            self.logger.error(f"Error in multi-step modification process: {e}")
            return {
                "success": False,
                "error": f"Modification process failed: {str(e)}",
                "original_template": current_template,
                "user_feedback": user_feedback
            }
    
    def _parse_final_output_from_response(self, response: str, original_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the final JSON response containing the complete modified code for all three files.
        This method is kept for backward compatibility but is not used in the new architecture.
        """
        try:
            print(f"DEBUG: Parsing final output response (length: {len(response)})")
            parsed_response = self._extract_json_from_response(response, "final_output")
            
            if parsed_response:
                print(f"DEBUG: Successfully extracted JSON with keys: {list(parsed_response.keys())}")
                
                # Validate that all required sections are present
                required_keys = ["html_export", "style_css", "globals_css", "changes_summary"]
                missing_keys = [key for key in required_keys if key not in parsed_response]
                
                if not missing_keys:
                    # Check if the response contains placeholder text (which should not happen with our improved prompt)
                    html_content = parsed_response["html_export"]
                    style_content = parsed_response["style_css"]
                    globals_content = parsed_response["globals_css"]
                    
                    placeholder_indicators = [
                        "/* Same as original",
                        "(Same as original",
                        "/* No changes",
                        "/* Unchanged",
                        "/* Original code",
                        "<!-- Same as original",
                        "<!-- No changes",
                        "<!-- Unchanged"
                    ]
                    
                    has_placeholders = any(indicator in html_content or indicator in style_content or indicator in globals_content 
                                         for indicator in placeholder_indicators)
                    
                    if has_placeholders:
                        print(f"WARNING: Placeholder text detected in response, this should not happen with improved prompt")
                        # Return original template with error message
                        return {
                            "success": False,
                            "error": "LLM returned placeholder text instead of actual code. This indicates a prompt compliance issue.",
                            "original_template": original_template,
                            "suggestion": "The system will retry with a stronger prompt."
                        }
                    
                    # Create the modified template structure with complete code replacement
                    modified_template = original_template.copy()
                    
                    # Replace all three files with the complete code from LLM
                    modified_template["html_export"] = parsed_response["html_export"]
                    modified_template["style_css"] = parsed_response["style_css"]
                    modified_template["globals_css"] = parsed_response["globals_css"]
                    
                    # Add modification metadata
                    modified_template["modification_metadata"] = {
                        "changes_applied": parsed_response.get("changes_summary", []),
                        "modification_type": "complete_code_replacement",
                        "modified_at": "2025-01-27T12:00:00Z"
                    }
                    
                    # Check if this was a "no changes" response (text not found)
                    changes_summary = parsed_response.get("changes_summary", [])
                    if any("not found" in summary.lower() or "could not find" in summary.lower() or "no direct match" in summary.lower() 
                           for summary in changes_summary):
                        print(f"INFO: Target text not found, returning original template with error message")
                        return {
                            "success": False,
                            "error": "Target text not found in the HTML structure",
                            "original_template": original_template,
                            "changes_summary": changes_summary,
                            "suggestion": "Please check the exact text you want to modify or provide more context about the element location."
                        }
                    
                    return {
                        "success": True,
                        "modified_template": modified_template,
                        "changes_summary": parsed_response["changes_summary"]
                    }
                else:
                    print(f"ERROR: Missing required sections in final output: {missing_keys}")
                    self.logger.warning(f"Missing required sections in final output: {missing_keys}")
                    return {
                        "success": False,
                        "error": f"Missing required sections: {missing_keys}"
                    }
            else:
                print(f"ERROR: Failed to extract JSON from final output response")
                self.logger.warning("Failed to extract JSON from final output response")
                return {
                    "success": False,
                    "error": "Failed to parse LLM response"
                }
            
        except Exception as e:
            self.logger.error(f"Error parsing final output from response: {e}")
            return {
                "success": False,
                "error": f"Parsing error: {str(e)}"
            }
    
    def _build_single_prompt_modification(self, user_feedback: str, current_template: Dict[str, Any]) -> str:
        """
        [LEGACY METHOD] This method is kept for backward compatibility but is not used in the new architecture.
        The new system uses the Planner-Executor approach instead.
        """
        # This method is deprecated in favor of the new multi-step architecture
        return "This method is deprecated. Use the new Planner-Executor architecture instead."


class PlannerAgent(BaseAgent):
    """Specialized agent for creating detailed modification plans"""
    
    def __init__(self):
        system_message = """You are an expert UI/UX modification planner with deep understanding of web development and user intent analysis.

Your role is to:
1. Analyze user requests with sophisticated understanding of intent
2. Create detailed, step-by-step modification plans
3. Handle ambiguity by identifying multiple possible targets
4. Generate precise instructions for the executor agent

**CRITICAL CSS SELECTOR REQUIREMENTS:**
- ✅ ONLY use valid CSS selectors: `.class-name`, `#id-name`, `tag.class`, `tag#id`
- ❌ NEVER use jQuery selectors: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
- ✅ Every selector must be valid CSS that works in a real stylesheet
- ✅ Use exact classes/IDs from HTML analysis - don't invent or guess
- ✅ Validate every selector before including it in your plan

You use the Claude-3-5-Sonnet model for complex reasoning and planning."""
        
        super().__init__("Planner", system_message, model="claude-3-5-sonnet-20241022")
        self.logger = logging.getLogger(__name__)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove control characters and fix common issues"""
        # Remove control characters but preserve newlines and tabs in string values
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        # Escape unescaped newlines and tabs within strings
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        return json_str
    
    def _extract_json_from_response(self, response: str, context: str = "response") -> Optional[Dict[str, Any]]:
        """Robust JSON extraction from LLM responses"""
        try:
            self.logger.debug(f"Extracting JSON from {context}: {response[:200]}...")
            
            # Strategy 1: Find JSON block with markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    json_str = self._clean_json_string(json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Strategy 2: Find first complete JSON object with proper brace matching
            if "{" in response and "}" in response:
                brace_count = 0
                start_pos = -1
                
                for i, char in enumerate(response):
                    if char == "{":
                        if brace_count == 0:
                            start_pos = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_pos >= 0:
                            # Found complete JSON object
                            json_str = response[start_pos:i+1]
                            json_str = self._clean_json_string(json_str)
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
            
            # Strategy 3: Extract content between first { and last } (fallback)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                json_str = self._clean_json_string(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON in {context}: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from {context}: {e}")
            return None
    
    def create_modification_plan(self, user_feedback: str, current_template: Dict[str, Any], html_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed modification plan based on user feedback and HTML analysis"""
        try:
            prompt = self._build_planning_prompt(user_feedback, current_template, html_analysis)
            
            self.logger.debug("Sending planning request to Claude Sonnet...")
            response = self.call_claude_with_cot(prompt, enable_cot=True)
            
            # Parse the planning response
            plan = self._parse_planning_response(response)
            
            if plan:
                return {
                    "success": True,
                    "plan": plan
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create modification plan"
                }
                
        except Exception as e:
            self.logger.error(f"Error creating modification plan: {e}")
            return {
                "success": False,
                "error": f"Planning failed: {str(e)}"
            }
    
    def _build_planning_prompt(self, user_feedback: str, current_template: Dict[str, Any], html_analysis: Dict[str, Any]) -> str:
        """Build sophisticated prompt for modification planning with comprehensive HTML analysis"""
        
        template_name = current_template.get('name', 'Unknown Template')
        template_category = current_template.get('category', 'general')
        
        # Build comprehensive HTML structure analysis
        structure_analysis = []
        
        # 1. Overall statistics
        debug_info = html_analysis.get("debug_info", {})
        structure_analysis.append(f"## HTML STRUCTURE OVERVIEW")
        structure_analysis.append(f"Total elements analyzed: {debug_info.get('total_elements_found', 0)}")
        structure_analysis.append(f"Text elements found: {debug_info.get('text_elements_found', 0)}")
        structure_analysis.append(f"Sample texts: {', '.join(debug_info.get('sample_texts', [])[:10])}")
        structure_analysis.append("")
        
        # 2. All text elements with their details
        if html_analysis.get("elements_by_text"):
            structure_analysis.append("## ALL TEXT ELEMENTS")
            structure_analysis.append("This is the complete list of all text elements found in the HTML:")
            structure_analysis.append("")
            
            for text, info in html_analysis["elements_by_text"].items():
                tag = info.get('tag', 'unknown')
                classes = info.get('classes', [])
                element_id = info.get('id', 'none')
                full_attrs = info.get('full_attrs', '')
                
                structure_analysis.append(f"**Text**: '{text}'")
                structure_analysis.append(f"  - Tag: {tag}")
                structure_analysis.append(f"  - Classes: {classes}")
                structure_analysis.append(f"  - ID: {element_id}")
                if full_attrs:
                    structure_analysis.append(f"  - Full attributes: {full_attrs}")
                structure_analysis.append("")
        
        # 3. Elements organized by class
        if html_analysis.get("elements_by_class"):
            structure_analysis.append("## ELEMENTS BY CSS CLASS")
            structure_analysis.append("Elements organized by their CSS classes:")
            structure_analysis.append("")
            
            for class_name, elements in html_analysis["elements_by_class"].items():
                structure_analysis.append(f"**Class**: .{class_name}")
                for element in elements:
                    text = element.get('text', '')
                    tag = element.get('tag', 'unknown')
                    element_id = element.get('id', 'none')
                    structure_analysis.append(f"  - '{text}' (tag: {tag}, id: {element_id})")
                structure_analysis.append("")
        
        # 4. Elements organized by ID
        if html_analysis.get("elements_by_id"):
            structure_analysis.append("## ELEMENTS BY ID")
            structure_analysis.append("Elements with specific IDs:")
            structure_analysis.append("")
            
            for element_id, info in html_analysis["elements_by_id"].items():
                text = info.get('text', '')
                tag = info.get('tag', 'unknown')
                classes = info.get('classes', [])
                structure_analysis.append(f"**ID**: #{element_id}")
                structure_analysis.append(f"  - Text: '{text}'")
                structure_analysis.append(f"  - Tag: {tag}")
                structure_analysis.append(f"  - Classes: {classes}")
                structure_analysis.append("")
        
        # 5. Header and navigation elements
        if html_analysis.get("header_elements"):
            structure_analysis.append("## HEADER ELEMENTS")
            structure_analysis.append("Elements identified as header-related:")
            structure_analysis.append("")
            
            for element in html_analysis["header_elements"]:
                text = element.get('text', '')
                tag = element.get('tag', 'unknown')
                classes = element.get('classes', [])
                element_id = element.get('id', 'none')
                structure_analysis.append(f"  - '{text}' (tag: {tag}, classes: {classes}, id: {element_id})")
            structure_analysis.append("")
        
        if html_analysis.get("navigation_elements"):
            structure_analysis.append("## NAVIGATION ELEMENTS")
            structure_analysis.append("Elements identified as navigation-related:")
            structure_analysis.append("")
            
            for element in html_analysis["navigation_elements"]:
                text = element.get('text', '')
                tag = element.get('tag', 'unknown')
                classes = element.get('classes', [])
                element_id = element.get('id', 'none')
                structure_analysis.append(f"  - '{text}' (tag: {tag}, classes: {classes}, id: {element_id})")
            structure_analysis.append("")
        
        # 6. DOM structure overview
        if html_analysis.get("dom_structure"):
            structure_analysis.append("## DOM STRUCTURE OVERVIEW")
            structure_analysis.append("Main sections and their content:")
            structure_analysis.append("")
            
            for section_key, section_info in html_analysis["dom_structure"].items():
                tag = section_info.get('tag', 'unknown')
                classes = section_info.get('classes', [])
                text_elements = section_info.get('text_elements', [])
                structure_analysis.append(f"**Section**: {section_key}")
                structure_analysis.append(f"  - Tag: {tag}")
                structure_analysis.append(f"  - Classes: {classes}")
                if text_elements:
                    structure_analysis.append(f"  - Text elements: {text_elements}")
                structure_analysis.append("")
        
        structure_analysis_text = "\n".join(structure_analysis)
        
        prompt = f"""You are an expert UI/UX modification planner. You have access to a comprehensive analysis of the HTML structure. Use this detailed information to create precise modification plans.

## USER REQUEST
{user_feedback}

## TEMPLATE CONTEXT
- Template Name: {template_name}
- Category: {template_category}

## COMPREHENSIVE HTML STRUCTURE ANALYSIS
{structure_analysis_text}

## CRITICAL CSS SELECTOR RULES - READ CAREFULLY

**VALID CSS SELECTORS ONLY:**
- ✅ `.class-name` (targets elements with class)
- ✅ `#id-name` (targets element with ID)
- ✅ `tag.class` (e.g., `button.btn-primary`)
- ✅ `tag#id` (e.g., `div#header`)
- ✅ `.class1.class2` (multiple classes)

**INVALID SELECTORS - NEVER USE:**
- ❌ `:contains('text')` (jQuery selector)
- ❌ `:has()` (jQuery selector)
- ❌ `:text()` (jQuery selector)
- ❌ `:first`, `:last` (jQuery selectors)
- ❌ `:eq()` (jQuery selector)

## FEW-SHOT EXAMPLES

**Example 1: Valid CSS Selector**
**User Request**: "change the color of the login button to blue"

**HTML Analysis**: Found button with text "Login" and class "btn-primary"

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Change the visual appearance of a login button",
    "target_element_type": "button",
    "modification_type": "styling",
    "specific_change": "color change to blue"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Login",
      "css_selector": ".btn-primary",
      "confidence": 0.95,
      "reasoning": "Exact text match found with button class"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "modify_css",
      "target_selector": ".btn-primary",
      "property": "background-color",
      "new_value": "#007bff",
      "description": "Change button background color to blue"
    }}
  ],
  "expected_outcome": "Login button will have a blue background color"
}}
```

**Example 2: Multiple Classes**
**User Request**: "change the connect link color to red"

**HTML Analysis**: Found link with text "Connect" and classes "nav-link text-wrapper-10"

**Plan**:
```json
{{
  "intent_analysis": {{
    "user_goal": "Change the color of a navigation link",
    "target_element_type": "link",
    "modification_type": "styling",
    "specific_change": "text color change to red"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "Connect",
      "css_selector": ".text-wrapper-10",
      "confidence": 0.95,
      "reasoning": "Unique class identifier for the Connect link"
    }},
    "alternative_targets": []
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "modify_css",
      "target_selector": ".text-wrapper-10",
      "property": "color",
      "new_value": "#ff0000",
      "description": "Change Connect link text color to red"
    }}
  ],
  "expected_outcome": "The Connect link will appear in red color"
}}
```

**Example 3: What NOT to do (INVALID)**
**User Request**: "change the connect button color to red"

**WRONG Plan (DO NOT USE):**
```json
{{
  "steps": [
    {{
      "target_selector": ".text-wrapper-10:contains('Connect')",
      "property": "color",
      "new_value": "#ff0000"
    }}
  ]
}}
```

**CORRECT Plan (USE THIS):**
```json
{{
  "steps": [
    {{
      "target_selector": ".text-wrapper-10",
      "property": "color", 
      "new_value": "#ff0000"
    }}
  ]
}}
```

## MANDATORY VALIDATION CHECKLIST

Before generating any CSS selector, verify:
1. ✅ Does it start with `.` (class), `#` (ID), or tag name?
2. ✅ Does it contain ONLY valid CSS syntax?
3. ✅ Does it NOT contain `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`?
4. ✅ Can it be used in a real CSS file?
5. ✅ Does it target the specific element from the HTML analysis?

**REMEMBER**: If you're unsure about a selector, use the simplest valid option (e.g., `.class-name`).

## YOUR TASK
Create a detailed modification plan for the user request above. You have access to the complete HTML structure analysis above. Use this information to:

1. **Find Exact Matches**: Look for exact text matches in the "ALL TEXT ELEMENTS" section
2. **Identify Target Elements**: Use the detailed element information to find the best targets
3. **Generate Precise Selectors**: Use the class and ID information to create accurate CSS selectors
4. **Handle Ambiguity**: If multiple elements match, identify them for clarification

## ANALYSIS GUIDELINES - EXACT CODE REQUIREMENTS

**CRITICAL: You must return EXACT, VALID code that works immediately**

- **Text Matching**: Look for exact text matches first, then partial matches
- **CSS Selectors**: 
  - ✅ **MUST USE ONLY**: `.class-name`, `#id-name`, `tag.class`, `tag#id`, `.class1.class2`
  - ❌ **NEVER USE**: `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`
  - **Prefer classes over IDs** for better maintainability
  - **Use the EXACT class/ID from HTML analysis** - don't guess or invent
  - **If targeting by text content**, use the class/ID of the element containing that text
- **Context**: Consider the element's position (header, navigation, etc.)
- **Confidence**: Base confidence on how well the target matches the request
- **Code Quality**: Every selector must be valid CSS that can be used in a real stylesheet

## OUTPUT FORMAT
Return ONLY this JSON structure:
```json
{{
  "intent_analysis": {{
    "user_goal": "string describing what the user wants to achieve",
    "target_element_type": "string (text|button|image|section|etc)",
    "modification_type": "string (styling|content|layout|structure)",
    "specific_change": "string describing the exact change needed"
  }},
  "target_identification": {{
    "primary_target": {{
      "text_content": "string (exact text found)",
      "css_selector": "string (best CSS selector)",
      "confidence": 0.95,
      "reasoning": "string explaining why this target was chosen"
    }},
    "alternative_targets": [
      {{
        "text_content": "string",
        "css_selector": "string",
        "confidence": 0.7,
        "reasoning": "string"
      }}
    ]
  }},
  "requires_clarification": false,
  "clarification_options": [],
  "steps": [
    {{
      "step_number": 1,
      "action": "string (modify_text|modify_css|modify_html|add_element|remove_element)",
      "target_selector": "string (CSS selector)",
      "property": "string (for CSS modifications)",
      "new_value": "string (new value to set)",
      "description": "string (what this step does)"
    }}
  ],
  "expected_outcome": "string describing what the user will see after changes"
}}
```

## FINAL VALIDATION - BEFORE SUBMITTING

**STOP AND CHECK YOUR CSS SELECTORS:**

1. **Does every `target_selector` start with `.`, `#`, or a tag name?**
2. **Does every `target_selector` NOT contain `:contains()`, `:has()`, `:text()`, `:first`, `:last`, `:eq()`?**
3. **Can every `target_selector` be used in a real CSS file?**
4. **Does every `target_selector` match an element from the HTML analysis above?**

**IF ANY SELECTOR FAILS THESE CHECKS, FIX IT BEFORE SUBMITTING.**

## IMPORTANT RULES
- **Use the HTML Analysis**: Reference specific elements from the analysis above
- **Be Precise**: Use exact text content and CSS selectors from the analysis
- **Handle Ambiguity**: If multiple elements match, set requires_clarification to true
- **Provide Clear Reasoning**: Explain why you chose specific targets
- **VALIDATE EVERY SELECTOR**: Ensure it's valid CSS before including it
- **Consider Context**: Use header/navigation information when relevant"""
        
        return prompt
    
    def _parse_planning_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the planning response"""
        try:
            parsed_response = self._extract_json_from_response(response, "planning")
            
            if parsed_response:
                # Validate required fields
                required_fields = ["intent_analysis", "target_identification", "steps", "expected_outcome"]
                missing_fields = [field for field in required_fields if field not in parsed_response]
                
                if not missing_fields:
                    return parsed_response
                else:
                    self.logger.warning(f"Missing required fields in plan: {missing_fields}")
                    return None
            else:
                self.logger.warning("Failed to parse planning response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing planning response: {e}")
            return None


class ExecutorAgent(BaseAgent):
    """Specialized agent for executing modification plans"""
    
    def __init__(self):
        system_message = """You are an expert web development executor with precise code modification skills.

Your role is to:
1. Execute modification plans step by step
2. Generate precise, syntactically correct code
3. Maintain code quality and structure
4. Return complete modified files

You use the Claude-3-5-Haiku model for fast, efficient execution."""
        
        super().__init__("Executor", system_message, model="claude-3-5-haiku-20241022")
        self.logger = logging.getLogger(__name__)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to remove control characters and fix common issues"""
        # Remove control characters but preserve newlines and tabs in string values
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        # Escape unescaped newlines and tabs within strings
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        return json_str
    
    def _extract_json_from_response(self, response: str, context: str = "response") -> Optional[Dict[str, Any]]:
        """Robust JSON extraction from LLM responses"""
        try:
            self.logger.debug(f"Extracting JSON from {context}: {response[:200]}...")
            
            # Strategy 1: Find JSON block with markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    json_str = self._clean_json_string(json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Strategy 2: Find first complete JSON object with proper brace matching
            if "{" in response and "}" in response:
                brace_count = 0
                start_pos = -1
                
                for i, char in enumerate(response):
                    if char == "{":
                        if brace_count == 0:
                            start_pos = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_pos >= 0:
                            # Found complete JSON object
                            json_str = response[start_pos:i+1]
                            json_str = self._clean_json_string(json_str)
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
            
            # Strategy 3: Extract content between first { and last } (fallback)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                json_str = self._clean_json_string(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON in {context}: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from {context}: {e}")
            return None
    
    def execute_modification_plan(self, modification_plan: Dict[str, Any], current_template: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a modification plan step by step"""
        try:
            # Extract template content
            html_content = current_template.get('html_export', '')
            style_css = current_template.get('style_css', '')
            globals_css = current_template.get('globals_css', '')
            
            # Create working copies
            modified_html = html_content
            modified_style_css = style_css
            modified_globals_css = globals_css
            
            steps = modification_plan.get('steps', [])
            changes_summary = []
            
            # Execute each step
            for step in steps:
                step_result = self._execute_single_step(step, modified_html, modified_style_css, modified_globals_css)
                
                if step_result.get('success', False):
                    # Update our working copies
                    modified_html = step_result.get('html', modified_html)
                    modified_style_css = step_result.get('style_css', modified_style_css)
                    modified_globals_css = step_result.get('globals_css', modified_globals_css)
                    changes_summary.append(step_result.get('description', f"Step {step.get('step_number', 'unknown')} completed"))
                else:
                    return {
                        "success": False,
                        "error": f"Step {step.get('step_number', 'unknown')} failed: {step_result.get('error', 'Unknown error')}"
                    }
            
            # Create modified template
            modified_template = current_template.copy()
            modified_template["html_export"] = modified_html
            modified_template["style_css"] = modified_style_css
            modified_template["globals_css"] = modified_globals_css
            
            # Add modification metadata
            modified_template["modification_metadata"] = {
                "changes_applied": changes_summary,
                "modification_type": "planned_execution",
                "modified_at": "2025-01-27T12:00:00Z",
                "plan_executed": modification_plan
            }
            
            return {
                "success": True,
                "modified_template": modified_template,
                "changes_summary": changes_summary
            }
            
        except Exception as e:
            self.logger.error(f"Error executing modification plan: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }
    
    def _execute_single_step(self, step: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Execute a single modification step"""
        try:
            action = step.get('action', '')
            target_selector = step.get('target_selector', '')
            description = step.get('description', '')
            
            if action == 'modify_text':
                return self._modify_text(step, html_content, style_css, globals_css)
            elif action == 'modify_css':
                return self._modify_css(step, html_content, style_css, globals_css)
            elif action == 'modify_html':
                return self._modify_html(step, html_content, style_css, globals_css)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing step: {e}")
            return {
                "success": False,
                "error": f"Step execution failed: {str(e)}"
            }
    
    def _modify_text(self, step: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Modify text content in HTML"""
        try:
            target_selector = step.get('target_selector', '')
            new_value = step.get('new_value', '')
            
            # Use BeautifulSoup to modify text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find elements by CSS selector
            elements = soup.select(target_selector)
            
            if not elements:
                return {
                    "success": False,
                    "error": f"No elements found with selector: {target_selector}"
                }
            
            # Modify the first matching element
            element = elements[0]
            element.string = new_value
            
            return {
                "success": True,
                "html": str(soup),
                "style_css": style_css,
                "globals_css": globals_css,
                "description": f"Modified text in {target_selector} to '{new_value}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Text modification failed: {str(e)}"
            }
    
    def _modify_css(self, step: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Modify CSS properties"""
        try:
            target_selector = step.get('target_selector', '')
            property_name = step.get('property', '')
            new_value = step.get('new_value', '')
            
            # Validate CSS selector - check for invalid jQuery-style selectors
            invalid_selectors = [':contains(', ':has(', ':text(', ':first', ':last', ':eq(']
            if any(invalid_sel in target_selector for invalid_sel in invalid_selectors):
                return {
                    "success": False,
                    "error": f"Invalid CSS selector '{target_selector}' contains jQuery-style pseudo-selectors. Use only valid CSS selectors like .class-name or #id-name.",
                    "suggestion": "The planner should generate valid CSS selectors based on element classes or IDs."
                }
            
            # Test if the selector actually matches elements in the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            matching_elements = soup.select(target_selector)
            
            if not matching_elements:
                return {
                    "success": False,
                    "error": f"CSS selector '{target_selector}' does not match any elements in the HTML",
                    "suggestion": "Check the HTML structure and use a valid class or ID selector."
                }
            
            # Build the CSS rule
            css_rule = f"{target_selector} {{\n  {property_name}: {new_value};\n}}"
            
            # Add to style_css
            modified_style_css = style_css + "\n" + css_rule
            
            return {
                "success": True,
                "html": html_content,
                "style_css": modified_style_css,
                "globals_css": globals_css,
                "description": f"Added CSS rule: {target_selector} {{ {property_name}: {new_value}; }} (matched {len(matching_elements)} elements)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSS modification failed: {str(e)}"
            }
    
    def _modify_html(self, step: Dict[str, Any], html_content: str, style_css: str, globals_css: str) -> Dict[str, Any]:
        """Modify HTML structure"""
        try:
            # This is a placeholder for HTML structure modifications
            # Can be expanded based on specific needs
            
            return {
                "success": False,
                "error": "HTML structure modification not yet implemented"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"HTML modification failed: {str(e)}"
            }