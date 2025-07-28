"""
Validation Layer - QA, structured data enforcement, schema validation
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Represents a validation result"""
    is_valid: bool
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestions: Optional[List[str]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ValidationLayer:
    """Handles validation, QA, and structured data enforcement"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validators: Dict[str, Callable] = {}
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.validation_history: List[ValidationResult] = []
        
        # Register default validators and schemas
        self._register_default_validators()
        self._register_default_schemas()
    
    def register_validator(self, name: str, validator_func: Callable) -> bool:
        """Register a custom validator"""
        try:
            self.validators[name] = validator_func
            self.logger.info(f"Registered validator: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register validator {name}: {e}")
            return False
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> bool:
        """Register a JSON schema"""
        try:
            # Validate the schema itself
            jsonschema.Draft7Validator.check_schema(schema)
            self.schemas[name] = schema
            self.logger.info(f"Registered schema: {name}")
            return True
        except ValidationError as e:
            self.logger.error(f"Invalid schema {name}: {e}")
            return False
    
    def validate_data(self, data: Any, schema_name: str) -> List[ValidationResult]:
        """Validate data against a registered schema"""
        results = []
        
        if schema_name not in self.schemas:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Schema '{schema_name}' not found",
                field="schema"
            ))
            return results
        
        try:
            schema = self.schemas[schema_name]
            validate(instance=data, schema=schema)
            
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message=f"Data validated successfully against schema '{schema_name}'"
            ))
            
        except ValidationError as e:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=str(e.message),
                field=".".join(str(p) for p in e.path),
                value=e.instance
            ))
        
        self.validation_history.extend(results)
        return results
    
    def validate_template_data(self, template_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate template data"""
        results = []
        
        # Required fields validation
        required_fields = ["name", "category", "html_export"]
        for field in required_fields:
            if field not in template_data:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Required field '{field}' is missing",
                    field=field
                ))
        
        # Category validation
        if "category" in template_data:
            valid_categories = ["landing", "login", "signup", "profile", "dashboard", "about"]
            if template_data["category"] not in valid_categories:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Invalid category '{template_data['category']}'. Must be one of: {valid_categories}",
                    field="category",
                    value=template_data["category"]
                ))
        
        # HTML validation
        if "html_export" in template_data:
            html_results = self._validate_html(template_data["html_export"])
            results.extend(html_results)
        
        # CSS validation
        if "style_css" in template_data:
            css_results = self._validate_css(template_data["style_css"])
            results.extend(css_results)
        
        self.validation_history.extend(results)
        return results
    
    def validate_user_input(self, user_input: str, input_type: str) -> List[ValidationResult]:
        """Validate user input"""
        results = []
        
        if input_type == "category_selection":
            results.extend(self._validate_category_selection(user_input))
        elif input_type == "requirements":
            results.extend(self._validate_requirements(user_input))
        elif input_type == "feedback":
            results.extend(self._validate_feedback(user_input))
        else:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"Unknown input type: {input_type}",
                field="input_type"
            ))
        
        self.validation_history.extend(results)
        return results
    
    def validate_api_response(self, response: Dict[str, Any], expected_format: str) -> List[ValidationResult]:
        """Validate API response format"""
        results = []
        
        if expected_format == "json":
            if not isinstance(response, dict):
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="Response must be a JSON object",
                    field="response"
                ))
            else:
                # Check for required fields
                if "success" not in response:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message="Response missing 'success' field",
                        field="success"
                    ))
        
        elif expected_format == "template":
            template_results = self.validate_template_data(response)
            results.extend(template_results)
        
        self.validation_history.extend(results)
        return results
    
    def _validate_html(self, html_content: str) -> List[ValidationResult]:
        """Validate HTML content"""
        results = []
        
        # Basic HTML structure validation
        if not html_content.strip():
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="HTML content is empty",
                field="html_export"
            ))
        
        # Check for basic HTML tags
        if "<html" not in html_content.lower():
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="HTML content missing <html> tag",
                field="html_export"
            ))
        
        if "<body" not in html_content.lower():
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="HTML content missing <body> tag",
                field="html_export"
            ))
        
        # Check for unclosed tags (basic check)
        open_tags = re.findall(r'<([^/][^>]*)>', html_content)
        close_tags = re.findall(r'</([^>]*)>', html_content)
        
        if len(open_tags) != len(close_tags):
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Possible unclosed HTML tags detected",
                field="html_export"
            ))
        
        return results
    
    def _validate_css(self, css_content: str) -> List[ValidationResult]:
        """Validate CSS content"""
        results = []
        
        if not css_content.strip():
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="CSS content is empty",
                field="style_css"
            ))
        
        # Check for basic CSS syntax
        if "{" in css_content and "}" in css_content:
            # Basic validation passed
            pass
        else:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="CSS content missing proper syntax (curly braces)",
                field="style_css"
            ))
        
        return results
    
    def _validate_category_selection(self, category: str) -> List[ValidationResult]:
        """Validate category selection"""
        results = []
        
        valid_categories = ["landing", "login", "signup", "profile", "about", "dashboard"]
        
        if not category:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Category selection is required",
                field="category"
            ))
        elif category.lower() not in valid_categories:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid category '{category}'. Must be one of: {valid_categories}",
                field="category",
                value=category
            ))
        
        return results
    
    def _validate_requirements(self, requirements: str) -> List[ValidationResult]:
        """Validate user requirements"""
        results = []
        
        if not requirements or len(requirements.strip()) < 5:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Requirements seem too short. Please provide more details.",
                field="requirements"
            ))
        else:
            # Requirements are valid if they have reasonable length
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Requirements received successfully",
                field="requirements"
            ))
        
        # Check for common requirement keywords (optional suggestions)
        requirement_keywords = ["modern", "minimal", "responsive", "user-friendly", "professional", "colorful", "dark", "light", "simple", "elegant"]
        found_keywords = [kw for kw in requirement_keywords if kw.lower() in requirements.lower()]
        
        if not found_keywords:
            results.append(ValidationResult(
                is_valid=True,  # Changed from False to True - this is just a suggestion
                level=ValidationLevel.INFO,
                message="Consider adding specific design preferences for better results",
                field="requirements",
                suggestions=requirement_keywords
            ))
        
        return results
    
    def _validate_feedback(self, feedback: str) -> List[ValidationResult]:
        """Validate user feedback"""
        results = []
        
        if not feedback or len(feedback.strip()) < 5:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Feedback is too short. Please provide more details.",
                field="feedback"
            ))
        
        # Check for constructive feedback indicators
        constructive_indicators = ["like", "dislike", "change", "improve", "better", "good", "bad"]
        found_indicators = [ind for ind in constructive_indicators if ind.lower() in feedback.lower()]
        
        if not found_indicators:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.INFO,
                message="Consider providing more specific feedback with clear preferences",
                field="feedback"
            ))
        
        return results
    
    def _register_default_validators(self):
        """Register default validators"""
        
        def validate_email(email: str) -> ValidationResult:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, email):
                return ValidationResult(True, ValidationLevel.INFO, "Valid email format")
            else:
                return ValidationResult(False, ValidationLevel.ERROR, "Invalid email format", value=email)
        
        def validate_url(url: str) -> ValidationResult:
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if re.match(pattern, url):
                return ValidationResult(True, ValidationLevel.INFO, "Valid URL format")
            else:
                return ValidationResult(False, ValidationLevel.ERROR, "Invalid URL format", value=url)
        
        self.register_validator("email", validate_email)
        self.register_validator("url", validate_url)
    
    def _register_default_schemas(self):
        """Register default JSON schemas"""
        
        # Template schema
        template_schema = {
            "type": "object",
            "required": ["name", "category", "html_export"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "category": {"type": "string", "enum": ["landing", "login", "signup", "profile", "dashboard", "about"]},
                "html_export": {"type": "string", "minLength": 1},
                "style_css": {"type": "string"},
                "globals_css": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object"}
            }
        }
        
        # User requirements schema
        requirements_schema = {
            "type": "object",
            "required": ["page_type", "style_preferences"],
            "properties": {
                "page_type": {"type": "string", "enum": ["landing", "login", "signup", "profile", "dashboard", "about"]},
                "style_preferences": {"type": "array", "items": {"type": "string"}},
                "key_features": {"type": "array", "items": {"type": "string"}},
                "target_audience": {"type": "string"},
                "brand_elements": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        self.register_schema("template", template_schema)
        self.register_schema("requirements", requirements_schema)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics"""
        total_validations = len(self.validation_history)
        successful_validations = len([r for r in self.validation_history if r.is_valid])
        
        level_counts = {}
        for level in ValidationLevel:
            level_counts[level.value] = len([r for r in self.validation_history if r.level == level])
        
        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0,
            "level_counts": level_counts,
            "recent_validations": [r for r in self.validation_history[-10:]]  # Last 10 validations
        }
    
    def clear_validation_history(self):
        """Clear validation history"""
        self.validation_history.clear()
        self.logger.info("Validation history cleared") 