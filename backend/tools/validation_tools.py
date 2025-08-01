"""
Validation Tools - Functions for data validation that can be called by LLM
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class ValidationTools:
    """Tools for data validation that can be called by LLM"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email format"""
        try:
            # Basic email validation regex
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if re.match(email_pattern, email):
                return {
                    "success": True,
                    "email": email,
                    "is_valid": True,
                    "message": "Email format is valid"
                }
            else:
                return {
                    "success": True,
                    "email": email,
                    "is_valid": False,
                    "message": "Email format is invalid"
                }
                
        except Exception as e:
            self.logger.error(f"Error validating email {email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "email": email,
                "is_valid": False
            }
    
    def validate_phone_number(self, phone: str) -> Dict[str, Any]:
        """Validate phone number format"""
        try:
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', phone)
            
            # Check if it's a valid length (7-15 digits)
            if 7 <= len(digits_only) <= 15:
                return {
                    "success": True,
                    "phone": phone,
                    "is_valid": True,
                    "cleaned_phone": digits_only,
                    "message": "Phone number format is valid"
                }
            else:
                return {
                    "success": True,
                    "phone": phone,
                    "is_valid": False,
                    "message": "Phone number must be 7-15 digits"
                }
                
        except Exception as e:
            self.logger.error(f"Error validating phone {phone}: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone": phone,
                "is_valid": False
            }
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate URL format"""
        try:
            # Basic URL validation regex
            url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
            
            if re.match(url_pattern, url):
                return {
                    "success": True,
                    "url": url,
                    "is_valid": True,
                    "message": "URL format is valid"
                }
            else:
                return {
                    "success": True,
                    "url": url,
                    "is_valid": False,
                    "message": "URL format is invalid"
                }
                
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "is_valid": False
            }
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate that required fields are present and not empty"""
        try:
            missing_fields = []
            empty_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                elif data[field] is None or str(data[field]).strip() == "":
                    empty_fields.append(field)
            
            is_valid = len(missing_fields) == 0 and len(empty_fields) == 0
            
            return {
                "success": True,
                "is_valid": is_valid,
                "missing_fields": missing_fields,
                "empty_fields": empty_fields,
                "message": f"Validation {'passed' if is_valid else 'failed'}"
            }
            
        except Exception as e:
            self.logger.error(f"Error validating required fields: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_valid": False
            }
    
    def validate_string_length(self, text: str, min_length: int = 0, max_length: int = None) -> Dict[str, Any]:
        """Validate string length constraints"""
        try:
            if not isinstance(text, str):
                return {
                    "success": True,
                    "text": text,
                    "is_valid": False,
                    "message": "Input must be a string"
                }
            
            length = len(text)
            
            if length < min_length:
                return {
                    "success": True,
                    "text": text,
                    "is_valid": False,
                    "length": length,
                    "min_length": min_length,
                    "message": f"Text must be at least {min_length} characters long"
                }
            
            if max_length and length > max_length:
                return {
                    "success": True,
                    "text": text,
                    "is_valid": False,
                    "length": length,
                    "max_length": max_length,
                    "message": f"Text must be no more than {max_length} characters long"
                }
            
            return {
                "success": True,
                "text": text,
                "is_valid": True,
                "length": length,
                "min_length": min_length,
                "max_length": max_length,
                "message": "Text length is valid"
            }
            
        except Exception as e:
            self.logger.error(f"Error validating string length: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": text,
                "is_valid": False
            }
    
    def validate_numeric_range(self, value: Any, min_value: float = None, max_value: float = None) -> Dict[str, Any]:
        """Validate numeric value is within range"""
        try:
            # Try to convert to float
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                return {
                    "success": True,
                    "value": value,
                    "is_valid": False,
                    "message": "Value must be numeric"
                }
            
            if min_value is not None and numeric_value < min_value:
                return {
                    "success": True,
                    "value": numeric_value,
                    "is_valid": False,
                    "min_value": min_value,
                    "message": f"Value must be at least {min_value}"
                }
            
            if max_value is not None and numeric_value > max_value:
                return {
                    "success": True,
                    "value": numeric_value,
                    "is_valid": False,
                    "max_value": max_value,
                    "message": f"Value must be no more than {max_value}"
                }
            
            return {
                "success": True,
                "value": numeric_value,
                "is_valid": True,
                "min_value": min_value,
                "max_value": max_value,
                "message": "Numeric value is within valid range"
            }
            
        except Exception as e:
            self.logger.error(f"Error validating numeric range: {e}")
            return {
                "success": False,
                "error": str(e),
                "value": value,
                "is_valid": False
            }
    
    def validate_date_format(self, date_string: str, format: str = "%Y-%m-%d") -> Dict[str, Any]:
        """Validate date string format"""
        try:
            parsed_date = datetime.strptime(date_string, format)
            
            return {
                "success": True,
                "date_string": date_string,
                "is_valid": True,
                "parsed_date": parsed_date.isoformat(),
                "format": format,
                "message": "Date format is valid"
            }
            
        except ValueError:
            return {
                "success": True,
                "date_string": date_string,
                "is_valid": False,
                "format": format,
                "message": f"Date must be in format {format}"
            }
        except Exception as e:
            self.logger.error(f"Error validating date format: {e}")
            return {
                "success": False,
                "error": str(e),
                "date_string": date_string,
                "is_valid": False
            }
    
    def validate_json_structure(self, json_data: Dict[str, Any], expected_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON data structure against expected schema"""
        try:
            errors = []
            
            for field, field_info in expected_schema.items():
                if field not in json_data:
                    if field_info.get("required", False):
                        errors.append(f"Missing required field: {field}")
                else:
                    # Check field type
                    expected_type = field_info.get("type")
                    if expected_type:
                        actual_type = type(json_data[field]).__name__
                        if actual_type != expected_type:
                            errors.append(f"Field {field} should be {expected_type}, got {actual_type}")
                    
                    # Check nested validation if specified
                    if "validate" in field_info:
                        validation_result = field_info["validate"](json_data[field])
                        if not validation_result.get("is_valid", True):
                            errors.append(f"Field {field}: {validation_result.get('message', 'Validation failed')}")
            
            is_valid = len(errors) == 0
            
            return {
                "success": True,
                "is_valid": is_valid,
                "errors": errors,
                "message": f"JSON structure validation {'passed' if is_valid else 'failed'}"
            }
            
        except Exception as e:
            self.logger.error(f"Error validating JSON structure: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_valid": False
            } 