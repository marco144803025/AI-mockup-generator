#!/usr/bin/env python3
"""
API Schema Compliance Testing Script
Validates API response structures against predefined schemas
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics
import re

class APISchemaComplianceTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results_dir = "evaluation_result"
        self.trials_per_agent = 2
        
        # Define expected schemas for each API endpoint (based on actual Pydantic models)
        self.api_schemas = {
            "requirements_analysis": {
                "required_fields": ["success", "response", "session_id", "phase"],
                "optional_fields": ["intent", "selected_template", "session_state", "transition_ready", "transition_data"],
                "field_types": {
                    "success": "boolean",
                    "response": "string",
                    "session_id": "string",
                    "phase": "string"
                }
            },
            "template_recommendation": {
                "required_fields": ["success", "response", "session_id", "phase"],
                "optional_fields": ["intent", "selected_template", "session_state", "transition_ready", "transition_data"],
                "field_types": {
                    "success": "boolean",
                    "response": "string",
                    "session_id": "string",
                    "phase": "string"
                }
            },
            "ui_editing": {
                "required_fields": ["success", "response", "ui_modifications", "session_id"],
                "optional_fields": ["metadata"],
                "field_types": {
                    "success": "boolean",
                    "response": "string",
                    "ui_modifications": "object",
                    "session_id": "string"
                }
            },
            "user_proxy": {
                "required_fields": ["success", "response", "session_id", "phase"],
                "optional_fields": ["intent", "selected_template", "session_state", "transition_ready", "transition_data"],
                "field_types": {
                    "success": "boolean",
                    "response": "string",
                    "session_id": "string",
                    "phase": "string"
                }
            },
            "question_generation": {
                "required_fields": ["success", "response", "session_id", "phase"],
                "optional_fields": ["intent", "selected_template", "session_state", "transition_ready", "transition_data"],
                "field_types": {
                    "success": "boolean",
                    "response": "string",
                    "session_id": "string",
                    "phase": "string"
                }
            }
        }
        
        # Test prompts for each API endpoint type
        self.api_test_prompts = {
            "requirements_analysis": [
                "I want to create a modern landing page",
                "I need a login page for my application"
            ],
            "template_recommendation": [
                "Recommend templates for a landing page",
                "Show me login page templates"
            ],
            "ui_editing": [
                "Change the button color to blue",
                "Make the text larger"
            ],
            "user_proxy": [
                "Hello, how can you help me?",
                "What should I do next?"
            ],
            "question_generation": [
                "I'm not sure what I want",
                "Can you ask me some questions?"
            ]
        }
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def validate_api_response_structure(self, response_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API response structure against expected schema"""
        if not response_data:
            return {
                "valid": False,
                "errors": ["No response data provided"],
                "compliance_score": 0.0
            }
        
        errors = []
        compliance_score = 0.0
        total_fields = 0
        valid_fields = 0
        
        # Check required fields
        for field in schema["required_fields"]:
            total_fields += 1
            if field in response_data:
                valid_fields += 1
                # Check field type if specified
                if field in schema["field_types"]:
                    expected_type = schema["field_types"][field]
                    actual_type = type(response_data[field]).__name__
                    
                    if expected_type == "boolean" and not isinstance(response_data[field], bool):
                        errors.append(f"Field '{field}' should be boolean, got {actual_type}")
                    elif expected_type == "string" and not isinstance(response_data[field], str):
                        errors.append(f"Field '{field}' should be string, got {actual_type}")
                    elif expected_type == "object" and not isinstance(response_data[field], dict):
                        errors.append(f"Field '{field}' should be object, got {actual_type}")
            else:
                errors.append(f"Required field '{field}' missing")
        
        # Check optional fields (don't count towards compliance score)
        for field in schema["optional_fields"]:
            if field in response_data:
                # Check field type if specified
                if field in schema["field_types"]:
                    expected_type = schema["field_types"][field]
                    actual_type = type(response_data[field]).__name__
                    
                    if expected_type == "boolean" and not isinstance(response_data[field], bool):
                        errors.append(f"Optional field '{field}' should be boolean, got {actual_type}")
                    elif expected_type == "string" and not isinstance(response_data[field], str):
                        errors.append(f"Optional field '{field}' should be string, got {actual_type}")
                    elif expected_type == "object" and not isinstance(response_data[field], dict):
                        errors.append(f"Optional field '{field}' should be object, got {actual_type}")
        
        # Calculate compliance score based on required fields only
        if total_fields > 0:
            compliance_score = (valid_fields / total_fields) * 100.0
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "compliance_score": compliance_score,
            "valid_fields": valid_fields,
            "total_required_fields": total_fields
        }
    
    def validate_json_structure(self, json_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON structure against expected schema"""
        if not json_data:
            return {
                "valid": False,
                "errors": ["No JSON data provided"],
                "compliance_score": 0.0
            }
        
        errors = []
        compliance_score = 0.0
        total_fields = 0
        valid_fields = 0
        
        # Check required fields
        for field in schema["required_fields"]:
            total_fields += 1
            if field in json_data:
                valid_fields += 1
                # Check field type if specified
                if field in schema["field_types"]:
                    expected_type = schema["field_types"][field]
                    actual_type = type(json_data[field]).__name__
                    
                    if expected_type == "boolean" and not isinstance(json_data[field], bool):
                        errors.append(f"Field '{field}' should be boolean, got {actual_type}")
                    elif expected_type == "string" and not isinstance(json_data[field], str):
                        errors.append(f"Field '{field}' should be string, got {actual_type}")
                    elif expected_type == "object" and not isinstance(json_data[field], dict):
                        errors.append(f"Field '{field}' should be object, got {actual_type}")
            else:
                errors.append(f"Required field '{field}' missing")
        
        # Check optional fields (don't count towards compliance score)
        for field in schema["optional_fields"]:
            if field in json_data:
                # Check field type if specified
                if field in schema["field_types"]:
                    expected_type = schema["field_types"][field]
                    actual_type = type(json_data[field]).__name__
                    
                    if expected_type == "boolean" and not isinstance(json_data[field], bool):
                        errors.append(f"Optional field '{field}' should be boolean, got {actual_type}")
                    elif expected_type == "string" and not isinstance(json_data[field], str):
                        errors.append(f"Optional field '{field}' should be string, got {actual_type}")
                    elif expected_type == "object" and not isinstance(json_data[field], dict):
                        errors.append(f"Optional field '{field}' should be object, got {actual_type}")
        
        # Calculate compliance score based on required fields only
        if total_fields > 0:
            compliance_score = (valid_fields / total_fields) * 100.0
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "compliance_score": compliance_score,
            "valid_fields": valid_fields,
            "total_required_fields": total_fields
        }
    
    async def test_api_schema_compliance(self, session: aiohttp.ClientSession, api_type: str) -> List[Dict[str, Any]]:
        """Test API response schema compliance for a specific endpoint type"""
        print(f"\n" + "=" * 70)
        print(f"🔍 Testing API Schema Compliance for: {api_type.replace('_', ' ').title()}")
        print("-" * 50)
        
        results = []
        prompts = self.api_test_prompts[api_type]
        schema = self.api_schemas[api_type]
        
        for trial_num in range(self.trials_per_agent):
            prompt = prompts[trial_num]
            print(f"  🔄 Trial {trial_num + 1}/{self.trials_per_agent}: {prompt[:50]}...")
            
            start_time = time.time()
            
            try:
                # Use appropriate endpoint based on API type
                if api_type == "ui_editing":
                    endpoint = "/api/ui-editor/chat"
                else:
                    endpoint = "/api/chat"
                
                async with session.post(
                    f"{self.base_url}{endpoint}",
                    json={"message": prompt, "session_id": f"schema_test_{api_type}_{trial_num}"}
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # Validate API response structure against schema
                        validation_result = self.validate_api_response_structure(response_data, schema)
                        
                        trial_result = {
                            "prompt": prompt,
                            "response_time": response_time,
                            "status_code": response.status,
                            "api_response_valid": validation_result["valid"],
                            "validation_result": validation_result,
                            "response_data": response_data
                        }
                        
                        if validation_result["valid"]:
                            print(f"    ✅ Valid API Response ({response_time:.3f}s)")
                        else:
                            print(f"    ❌ Invalid API Response ({response_time:.3f}s)")
                        
                    else:
                        trial_result = {
                            "prompt": prompt,
                            "response_time": response_time,
                            "status_code": response.status,
                            "api_response_valid": False,
                            "validation_result": {"valid": False, "errors": [f"HTTP {response.status}"], "compliance_score": 0.0},
                            "response_data": None
                        }
                        print(f"    ❌ HTTP Error {response.status} ({response_time:.3f}s)")
                    
                    results.append(trial_result)
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                
                trial_result = {
                    "prompt": prompt,
                    "response_time": response_time,
                    "status_code": None,
                    "api_response_valid": False,
                    "validation_result": {"valid": False, "errors": [str(e)], "compliance_score": 0.0},
                    "response_data": None,
                    "error": str(e)
                }
                print(f"    ❌ Exception ({response_time:.3f}s): {e}")
                results.append(trial_result)
        
        return results
    
    async def save_detailed_results(self, all_results: Dict[str, List[Dict[str, Any]]]):
        """Save detailed test results to file"""
        timestamp = datetime.now().isoformat()
        filename = os.path.join(self.results_dir, "schema_compliance_detailed_results.txt")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("API SCHEMA COMPLIANCE TESTING - DETAILED RESULTS\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Completed: {timestamp}\n\n")
            
            for api_type, results in all_results.items():
                f.write(f"API Endpoint: {api_type.replace('_', ' ').title()}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"Trial {i}:\n")
                    f.write(f"  Prompt: {result['prompt']}\n")
                    f.write(f"  Response Time: {result['response_time']:.3f}s\n")
                    f.write(f"  Status Code: {result['status_code']}\n")
                    f.write(f"  API Response Valid: {result['api_response_valid']}\n")
                    
                    validation = result['validation_result']
                    f.write(f"  Valid: {validation['valid']}\n")
                    f.write(f"  Compliance Score: {validation['compliance_score']:.1f}%\n")
                    
                    if validation['errors']:
                        f.write(f"  Errors:\n")
                        for error in validation['errors']:
                            f.write(f"    - {error}\n")
                    
                    if 'error' in result:
                        f.write(f"  Exception: {result['error']}\n")
                    
                    f.write("\n")
                
                f.write("\n" + "-" * 50 + "\n\n")
        
        print(f"📁 Detailed results saved to: {filename}")
    
    async def save_summary(self, all_results: Dict[str, List[Dict[str, Any]]]):
        """Save test summary to file"""
        timestamp = datetime.now().isoformat()
        filename = os.path.join(self.results_dir, "schema_compliance_summary.txt")
        
        # Calculate overall statistics
        total_trials = 0
        total_valid_responses = 0
        total_compliance_scores = []
        
        api_stats = {}
        
        for api_type, results in all_results.items():
            api_trials = len(results)
            api_valid = sum(1 for r in results if r['api_response_valid'])
            api_compliance_scores = [r['validation_result']['compliance_score'] for r in results if r['api_response_valid']]
            
            total_trials += api_trials
            total_valid_responses += api_valid
            total_compliance_scores.extend(api_compliance_scores)
            
            api_stats[api_type] = {
                "total_trials": api_trials,
                "valid_responses": api_valid,
                "compliance_rate": (api_valid / api_trials * 100) if api_trials > 0 else 0.0,
                "average_compliance_score": statistics.mean(api_compliance_scores) if api_compliance_scores else 0.0
            }
        
        overall_compliance_rate = (total_valid_responses / total_trials * 100) if total_trials > 0 else 0.0
        average_compliance_score = statistics.mean(total_compliance_scores) if total_compliance_scores else 0.0
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("API SCHEMA COMPLIANCE TESTING - SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Completed: {timestamp}\n\n")
            
            f.write("OVERALL RESULTS\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Trials: {total_trials}\n")
            f.write(f"Valid API Responses: {total_valid_responses}\n")
            f.write(f"Overall Compliance Rate: {overall_compliance_rate:.1f}%\n")
            f.write(f"Average Compliance Score: {average_compliance_score:.1f}%\n\n")
            
            f.write("API ENDPOINT-SPECIFIC RESULTS\n")
            f.write("-" * 30 + "\n")
            for api_type, stats in api_stats.items():
                f.write(f"{api_type.replace('_', ' ').title()}:\n")
                f.write(f"  Trials: {stats['total_trials']}\n")
                f.write(f"  Valid Responses: {stats['valid_responses']}\n")
                f.write(f"  Compliance Rate: {stats['compliance_rate']:.1f}%\n")
                f.write(f"  Average Compliance Score: {stats['average_compliance_score']:.1f}%\n\n")
        
        print(f"📁 Summary saved to: {filename}")
        
        return {
            "overall_stats": {
                "total_trials": total_trials,
                "total_valid_responses": total_valid_responses,
                "overall_compliance_rate": overall_compliance_rate,
                "average_compliance_score": average_compliance_score
            },
            "api_stats": api_stats
        }
    
    async def run_schema_compliance_tests(self) -> Dict[str, Any]:
        """Run all API schema compliance tests and return results"""
        print("🔍 Starting API Schema Compliance Testing")
        print(f"📊 Testing {len(self.api_schemas)} API endpoints × {self.trials_per_agent} trials each")
        print(f"🌐 Testing endpoints: {self.base_url}/api/chat and {self.base_url}/api/ui-editor/chat\n")
        
        all_results = {}
        
        async with aiohttp.ClientSession() as session:
            for api_type in self.api_schemas.keys():
                results = await self.test_api_schema_compliance(session, api_type)
                all_results[api_type] = results
        
        # Save results
        await self.save_detailed_results(all_results)
        summary_stats = await self.save_summary(all_results)
        
        # Print summary
        print("\n" + "=" * 70)
        print("🔍 API SCHEMA COMPLIANCE TESTING COMPLETED")
        print("=" * 70)
        
        overall = summary_stats["overall_stats"]
        print(f"📊 Overall Results:")
        print(f"   📈 Total Trials: {overall['total_trials']}")
        print(f"   ✅ Valid API Responses: {overall['total_valid_responses']}")
        print(f"   📊 Overall Compliance Rate: {overall['overall_compliance_rate']:.1f}%")
        print(f"   📊 Average Compliance Score: {overall['average_compliance_score']:.1f}%")
        
        print(f"\n📊 API Endpoint-Specific Results:")
        for api_type, stats in summary_stats["api_stats"].items():
            print(f"   {api_type.replace('_', ' ').title()}: {stats['compliance_rate']:.1f}% compliance")
        
        return summary_stats

if __name__ == "__main__":
    tester = APISchemaComplianceTester()
    asyncio.run(tester.run_schema_compliance_tests())
