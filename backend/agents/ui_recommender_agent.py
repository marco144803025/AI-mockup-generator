from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
from difflib import SequenceMatcher

class UIRecommenderAgent(BaseAgent):
    """Agent that recommends UI pages based on requirements and database templates"""
    
    def __init__(self):
        system_message = """You are a UI Recommender Agent specialized in:
1. Matching user requirements with available UI templates
2. Analyzing template metadata (tags, descriptions, categories)
3. Scoring templates based on relevance and fit
4. Providing detailed reasoning for recommendations
5. Suggesting alternatives when exact matches aren't available

Always provide clear reasoning for your recommendations and consider multiple factors in your analysis."""
        
        super().__init__("UIRecommender", system_message)
    
    def find_suitable_templates(self, search_criteria: Dict[str, Any], category: str = None) -> List[Dict[str, Any]]:
        """Find suitable templates based on search criteria"""
        
        # Get templates from database
        if category:
            templates = self.get_templates_by_category(category)
        else:
            templates = list(self.db.templates.find())
        
        if not templates:
            return []
        
        # Score templates based on criteria
        scored_templates = []
        for template in templates:
            score = self._calculate_template_score(template, search_criteria)
            if score > 0.3:  # Minimum relevance threshold
                scored_templates.append({
                    "template": template,
                    "score": score,
                    "reasoning": self._generate_reasoning(template, search_criteria, score)
                })
        
        # Sort by score (highest first)
        scored_templates.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top 5 recommendations
        return scored_templates[:5]
    
    def _calculate_template_score(self, template: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate how well a template matches the search criteria"""
        
        score = 0.0
        max_score = 0.0
        
        # Category matching (high weight)
        if criteria.get("category") and template.get("category"):
            if criteria["category"].lower() == template["category"].lower():
                score += 0.4
            max_score += 0.4
        
        # Style matching (high weight)
        if criteria.get("style") and template.get("tags"):
            style_match = self._check_style_match(criteria["style"], template["tags"])
            score += style_match * 0.3
            max_score += 0.3
        
        # Component matching (medium weight)
        if criteria.get("components") and template.get("tags"):
            component_match = self._check_component_match(criteria["components"], template["tags"])
            score += component_match * 0.2
            max_score += 0.2
        
        # Brand personality matching (medium weight)
        if criteria.get("brand_personality") and template.get("tags"):
            personality_match = self._check_personality_match(criteria["brand_personality"], template["tags"])
            score += personality_match * 0.1
            max_score += 0.1
        
        # Tag matching (low weight)
        if criteria.get("tags") and template.get("tags"):
            tag_match = self._check_tag_match(criteria["tags"], template["tags"])
            score += tag_match * 0.1
            max_score += 0.1
        
        # Normalize score
        return score / max_score if max_score > 0 else 0.0
    
    def _check_style_match(self, required_style: str, template_tags: List[str]) -> float:
        """Check how well the template style matches requirements"""
        
        style_keywords = {
            "modern": ["modern", "contemporary", "clean", "minimal"],
            "minimal": ["minimal", "clean", "simple", "minimalist"],
            "corporate": ["corporate", "professional", "business", "formal"],
            "creative": ["creative", "artistic", "colorful", "playful"],
            "elegant": ["elegant", "sophisticated", "luxury", "premium"]
        }
        
        if required_style.lower() in style_keywords:
            keywords = style_keywords[required_style.lower()]
            matches = sum(1 for keyword in keywords if any(keyword in tag.lower() for tag in template_tags))
            return min(matches / len(keywords), 1.0)
        
        return 0.0
    
    def _check_component_match(self, required_components: List[str], template_tags: List[str]) -> float:
        """Check how well the template components match requirements"""
        
        if not required_components:
            return 0.0
        
        matches = 0
        for component in required_components:
            if any(component.lower() in tag.lower() for tag in template_tags):
                matches += 1
        
        return matches / len(required_components)
    
    def _check_personality_match(self, required_personality: str, template_tags: List[str]) -> float:
        """Check how well the template personality matches requirements"""
        
        personality_keywords = {
            "professional": ["professional", "corporate", "business", "formal"],
            "friendly": ["friendly", "warm", "approachable", "welcoming"],
            "creative": ["creative", "artistic", "innovative", "unique"],
            "trustworthy": ["trustworthy", "reliable", "secure", "stable"]
        }
        
        if required_personality.lower() in personality_keywords:
            keywords = personality_keywords[required_personality.lower()]
            matches = sum(1 for keyword in keywords if any(keyword in tag.lower() for tag in template_tags))
            return min(matches / len(keywords), 1.0)
        
        return 0.0
    
    def _check_tag_match(self, required_tags: List[str], template_tags: List[str]) -> float:
        """Check how well the template tags match requirements"""
        
        if not required_tags or not template_tags:
            return 0.0
        
        matches = 0
        for required_tag in required_tags:
            for template_tag in template_tags:
                similarity = SequenceMatcher(None, required_tag.lower(), template_tag.lower()).ratio()
                if similarity > 0.8:  # 80% similarity threshold
                    matches += 1
                    break
        
        return matches / len(required_tags)
    
    def _generate_reasoning(self, template: Dict[str, Any], criteria: Dict[str, Any], score: float) -> str:
        """Generate reasoning for why this template was recommended"""
        
        reasoning_parts = []
        
        # Category match
        if criteria.get("category") and template.get("category"):
            if criteria["category"].lower() == template["category"].lower():
                reasoning_parts.append(f"Perfect category match: {template['category']}")
        
        # Style match
        if criteria.get("style") and template.get("tags"):
            style_match = self._check_style_match(criteria["style"], template["tags"])
            if style_match > 0.5:
                reasoning_parts.append(f"Good style alignment with {criteria['style']} design")
        
        # Component match
        if criteria.get("components") and template.get("tags"):
            component_match = self._check_component_match(criteria["components"], template["tags"])
            if component_match > 0.5:
                reasoning_parts.append(f"Contains {int(component_match * 100)}% of required components")
        
        # Brand personality
        if criteria.get("brand_personality") and template.get("tags"):
            personality_match = self._check_personality_match(criteria["brand_personality"], template["tags"])
            if personality_match > 0.5:
                reasoning_parts.append(f"Matches {criteria['brand_personality']} brand personality")
        
        # Overall score
        reasoning_parts.append(f"Overall relevance score: {score:.1%}")
        
        return "; ".join(reasoning_parts)
    
    def get_template_details(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific template"""
        
        try:
            template = self.db.templates.find_one({"_id": template_id})
            if template:
                return {
                    "id": str(template["_id"]),
                    "title": template.get("title", "Untitled"),
                    "category": template.get("category", "Unknown"),
                    "description": template.get("description", ""),
                    "tags": template.get("tags", []),
                    "html_content": template.get("html_content", ""),
                    "css_content": template.get("css_content", ""),
                    "preview_image": template.get("preview_image", ""),
                    "created_at": template.get("created_at"),
                    "updated_at": template.get("updated_at")
                }
        except Exception as e:
            print(f"Error fetching template details: {e}")
        
        return None
    
    def recommend_alternatives(self, selected_template: Dict[str, Any], search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend alternative templates if the selected one doesn't meet all requirements"""
        
        # Get all templates except the selected one
        all_templates = list(self.db.templates.find({"_id": {"$ne": selected_template["_id"]}}))
        
        # Score them based on how well they complement the selected template
        alternatives = []
        for template in all_templates:
            score = self._calculate_alternative_score(template, selected_template, search_criteria)
            if score > 0.4:  # Higher threshold for alternatives
                alternatives.append({
                    "template": template,
                    "score": score,
                    "reasoning": f"Alternative option with different strengths; score: {score:.1%}"
                })
        
        # Sort and return top 3 alternatives
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        return alternatives[:3]
    
    def _calculate_alternative_score(self, template: Dict[str, Any], selected_template: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate score for alternative templates"""
        
        # Start with base score
        base_score = self._calculate_template_score(template, criteria)
        
        # Bonus for different strengths
        selected_tags = set(selected_template.get("tags", []))
        template_tags = set(template.get("tags", []))
        
        # Different strengths (tags that selected template doesn't have)
        different_strengths = len(template_tags - selected_tags)
        bonus = min(different_strengths * 0.05, 0.2)  # Max 20% bonus
        
        return min(base_score + bonus, 1.0) 