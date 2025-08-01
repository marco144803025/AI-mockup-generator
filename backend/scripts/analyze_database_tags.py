#!/usr/bin/env python3
"""
Database Tag Analysis Script
Analyzes the actual tags in the database and generates a report for keyword configuration.
"""

import sys
import os
import json
from collections import Counter, defaultdict
from typing import Dict, List, Set, Any

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from pymongo import MongoClient
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Missing required packages. Please install: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

class DatabaseTagAnalyzer:
    """Analyzes tags in the database to understand what's actually available"""
    
    def __init__(self):
        """Initialize the analyzer with database connection"""
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.db_name = os.getenv('MONGODB_DB_NAME', 'ui_templates')
        self.client = None
        self.db = None
        
    def connect_to_database(self):
        """Connect to MongoDB database"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            print(f"✅ Connected to database: {self.db_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates from the database"""
        try:
            templates = list(self.db.templates.find({}))
            print(f"📊 Found {len(templates)} templates in database")
            return templates
        except Exception as e:
            print(f"❌ Error fetching templates: {e}")
            return []
    
    def extract_all_tags(self, templates: List[Dict[str, Any]]) -> List[str]:
        """Extract all tags from templates"""
        all_tags = []
        for template in templates:
            tags = template.get('tags', [])
            if isinstance(tags, list):
                all_tags.extend(tags)
            elif isinstance(tags, str):
                # Handle case where tags might be a comma-separated string
                all_tags.extend([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        return all_tags
    
    def analyze_tags(self, tags: List[str], templates: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze the tags and categorize them"""
        if not tags:
            return {"error": "No tags found in database"}
        
        # Count tag frequency
        tag_counter = Counter(tags)
        
        # Categorize tags based on patterns
        categories = defaultdict(list)
        
        for tag in tag_counter.keys():
            tag_lower = tag.lower()
            
            # Visual/Style tags
            if any(style in tag_lower for style in ['modern', 'minimal', 'clean', 'bold', 'colorful', 'dark', 'light', 'elegant', 'sleek', 'professional', 'playful', 'soft', 'natural', 'futuristic']):
                categories['visual_style'].append(tag)
            
            # Color tags
            elif any(color in tag_lower for color in ['blue', 'green', 'red', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray', 'black', 'white', 'gradient', 'neutral']):
                categories['colors'].append(tag)
            
            # Layout tags
            elif any(layout in tag_lower for layout in ['single', 'grid', 'sidebar', 'centered', 'full-width', 'narrow', 'wide', 'compact', 'spacious']):
                categories['layout'].append(tag)
            
            # Component tags
            elif any(comp in tag_lower for comp in ['header', 'footer', 'navigation', 'hero', 'form', 'button', 'image', 'card', 'section', 'main', 'aside']):
                categories['components'].append(tag)
            
            # Page type tags
            elif any(page in tag_lower for page in ['landing', 'login', 'signup', 'profile', 'about', 'contact', 'dashboard', 'gallery', 'portfolio', 'blog', 'shop']):
                categories['page_types'].append(tag)
            
            # Feature tags
            elif any(feature in tag_lower for feature in ['responsive', 'mobile', 'desktop', 'tablet', 'interactive', 'animated', 'static']):
                categories['features'].append(tag)
            
            # Business context tags
            elif any(business in tag_lower for business in ['business', 'corporate', 'startup', 'agency', 'ecommerce', 'saas', 'portfolio', 'personal', 'blog']):
                categories['business_context'].append(tag)
            
            # Content type tags
            elif any(content in tag_lower for content in ['text-heavy', 'image-heavy', 'video', 'minimal-content', 'rich-content']):
                categories['content_types'].append(tag)
            
            # Unclassified tags
            else:
                categories['unclassified'].append(tag)
        
        # Calculate statistics
        template_count = len(templates) if templates else 1
        unique_template_tags = set()
        if templates:
            for template in templates:
                template_tags = template.get('tags', [])
                if isinstance(template_tags, list):
                    unique_template_tags.update(template_tags)
                elif isinstance(template_tags, str):
                    unique_template_tags.update([tag.strip() for tag in template_tags.split(',') if tag.strip()])
        
        return {
            "total_unique_tags": len(tag_counter),
            "total_tag_occurrences": len(tags),
            "tag_frequency": dict(tag_counter.most_common()),
            "categories": dict(categories),
            "most_common_tags": tag_counter.most_common(20),
            "least_common_tags": tag_counter.most_common()[-20:],
            "tag_statistics": {
                "avg_tags_per_template": len(tags) / template_count if template_count > 0 else 0,
                "tags_with_single_occurrence": len([tag for tag, count in tag_counter.items() if count == 1]),
                "tags_with_multiple_occurrences": len([tag for tag, count in tag_counter.items() if count > 1])
            }
        }
    
    def analyze_categories(self, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze template categories"""
        category_counter = Counter()
        category_tag_mapping = defaultdict(set)
        
        for template in templates:
            category = template.get('category', 'unknown')
            category_counter[category] += 1
            
            tags = template.get('tags', [])
            if isinstance(tags, list):
                category_tag_mapping[category].update(tags)
            elif isinstance(tags, str):
                category_tag_mapping[category].update([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        return {
            "category_distribution": dict(category_counter),
            "tags_per_category": {cat: list(tags) for cat, tags in category_tag_mapping.items()},
            "category_statistics": {
                "total_categories": len(category_counter),
                "most_common_category": category_counter.most_common(1)[0] if category_counter else None,
                "categories_with_most_tags": sorted(category_tag_mapping.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            }
        }
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for keyword configuration"""
        recommendations = {
            "suggested_keyword_categories": {},
            "unused_current_keywords": [],
            "missing_keyword_categories": [],
            "configuration_suggestions": []
        }
        
        # Current hardcoded keywords (from the config)
        current_keywords = {
            "visual_style": ["visual", "style", "design", "color", "layout"],
            "modern_styles": ["modern", "minimal", "clean", "bold", "colorful", "dark", "light"],
            "professional_styles": ["sleek", "elegant", "professional", "playful", "soft", "natural", "futuristic"],
            "ui_components": ["hero", "navigation", "footer", "sidebar", "form", "button", "image"],
            "responsive_features": ["responsive", "mobile", "desktop", "tablet"],
            "business_styles": ["business", "professional", "casual", "creative", "tech"]
        }
        
        # Check which current keywords are actually used
        actual_tags = set(analysis.get("tag_frequency", {}).keys())
        
        for category, keywords in current_keywords.items():
            used_keywords = [kw for kw in keywords if kw in actual_tags]
            unused_keywords = [kw for kw in keywords if kw not in actual_tags]
            
            if used_keywords:
                recommendations["suggested_keyword_categories"][category] = used_keywords
            if unused_keywords:
                recommendations["unused_current_keywords"].extend(unused_keywords)
        
        # Suggest new categories based on actual data
        actual_categories = analysis.get("categories", {})
        for category, tags in actual_categories.items():
            if category not in recommendations["suggested_keyword_categories"]:
                recommendations["suggested_keyword_categories"][category] = tags[:10]  # Top 10 tags
        
        # Configuration suggestions
        if analysis.get("total_unique_tags", 0) < 50:
            recommendations["configuration_suggestions"].append("Database has relatively few unique tags - consider expanding tag vocabulary")
        
        if len(analysis.get("categories", {}).get("unclassified", [])) > 10:
            recommendations["configuration_suggestions"].append("Many unclassified tags - consider adding new keyword categories")
        
        return recommendations
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report"""
        print("🔍 Starting database tag analysis...")
        
        if not self.connect_to_database():
            return {"error": "Failed to connect to database"}
        
        templates = self.get_all_templates()
        if not templates:
            return {"error": "No templates found in database"}
        
        # Extract and analyze tags
        all_tags = self.extract_all_tags(templates)
        tag_analysis = self.analyze_tags(all_tags, templates)
        category_analysis = self.analyze_categories(templates)
        recommendations = self.generate_recommendations(tag_analysis)
        
        # Compile final report
        report = {
            "summary": {
                "total_templates": len(templates),
                "total_unique_tags": tag_analysis.get("total_unique_tags", 0),
                "total_tag_occurrences": tag_analysis.get("total_tag_occurrences", 0),
                "total_categories": category_analysis.get("category_statistics", {}).get("total_categories", 0)
            },
            "tag_analysis": tag_analysis,
            "category_analysis": category_analysis,
            "recommendations": recommendations,
            "generated_at": str(datetime.now())
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "database_tag_analysis.json"):
        """Save the analysis report to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ Report saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a summary of the analysis"""
        if "error" in report:
            print(f"❌ Analysis failed: {report['error']}")
            return
        
        summary = report["summary"]
        print("\n" + "="*60)
        print("📊 DATABASE TAG ANALYSIS SUMMARY")
        print("="*60)
        print(f"📁 Total Templates: {summary['total_templates']}")
        print(f"🏷️  Total Unique Tags: {summary['total_unique_tags']}")
        print(f"📈 Total Tag Occurrences: {summary['total_tag_occurrences']}")
        print(f"📂 Total Categories: {summary['total_categories']}")
        
        # Show top tags
        top_tags = report["tag_analysis"].get("most_common_tags", [])[:10]
        if top_tags:
            print(f"\n🏆 Top 10 Most Common Tags:")
            for tag, count in top_tags:
                print(f"   • {tag}: {count} occurrences")
        
        # Show category distribution
        categories = report["tag_analysis"].get("categories", {})
        if categories:
            print(f"\n📂 Tag Categories Found:")
            for category, tags in categories.items():
                print(f"   • {category}: {len(tags)} tags")
        
        # Show recommendations
        recommendations = report["recommendations"]
        if recommendations["configuration_suggestions"]:
            print(f"\n💡 Configuration Suggestions:")
            for suggestion in recommendations["configuration_suggestions"]:
                print(f"   • {suggestion}")
        
        print("="*60)

def main():
    """Main function to run the analysis"""
    analyzer = DatabaseTagAnalyzer()
    report = analyzer.generate_report()
    
    if "error" not in report:
        analyzer.print_summary(report)
        analyzer.save_report(report)
        
        # Also save a simplified version for easy review
        simplified_report = {
            "summary": report["summary"],
            "top_tags": report["tag_analysis"].get("most_common_tags", [])[:20],
            "categories": report["tag_analysis"].get("categories", {}),
            "recommendations": report["recommendations"]
        }
        analyzer.save_report(simplified_report, "database_tag_analysis_simplified.json")
        
        print("\n✅ Analysis complete! Check the generated JSON files for detailed results.")
    else:
        print(f"❌ Analysis failed: {report['error']}")

if __name__ == "__main__":
    from datetime import datetime
    main() 