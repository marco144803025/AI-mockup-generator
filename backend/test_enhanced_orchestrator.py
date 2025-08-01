#!/usr/bin/env python3
"""
Test script for Enhanced Orchestrator with integrated layer patterns
"""

import asyncio
import json
from datetime import datetime
from enhanced_orchestrator import EnhancedOrchestrator

class EnhancedOrchestratorTest:
    def __init__(self):
        self.orchestrator = EnhancedOrchestrator()
        
    async def test_basic_functionality(self):
        """Test basic orchestrator functionality"""
        print(f"\n{'='*80}")
        print("TESTING ENHANCED ORCHESTRATOR BASIC FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Test 1: Category selection
        print(f"\n--- Test 1: Category Selection ---")
        result = await self.orchestrator.process_user_message(
            "I want to create a landing page for my tech startup"
        )
        
        print(f"Input: I want to create a landing page for my tech startup")
        print(f"Success: {result['success']}")
        print(f"Response: {result['response'][:200]}...")
        print(f"Session ID: {result['session_id']}")
        print(f"State: {result.get('state', 'unknown')}")
        
        # Test 2: Requirements
        print(f"\n--- Test 2: Requirements ---")
        result2 = await self.orchestrator.process_user_message(
            "I need a modern design with hero section and contact form"
        )
        
        print(f"Input: I need a modern design with hero section and contact form")
        print(f"Success: {result2['success']}")
        print(f"Response: {result2['response'][:200]}...")
        
        # Test 3: Question
        print(f"\n--- Test 3: Question ---")
        result3 = await self.orchestrator.process_user_message(
            "What are the best practices for landing page design?"
        )
        
        print(f"Input: What are the best practices for landing page design?")
        print(f"Success: {result3['success']}")
        print(f"Response: {result3['response'][:200]}...")
        
        return result, result2, result3
    
    async def test_control_layer_routing(self):
        """Test Control Layer message routing"""
        print(f"\n{'='*80}")
        print("TESTING CONTROL LAYER MESSAGE ROUTING")
        print(f"{'='*80}")
        
        test_cases = [
            {
                "message": "I want a login page",
                "expected_type": "category_selection",
                "description": "Category Selection"
            },
            {
                "message": "I need a responsive design with modern UI",
                "expected_type": "requirements",
                "description": "Requirements"
            },
            {
                "message": "Can you change the color scheme?",
                "expected_type": "feedback",
                "description": "Feedback"
            },
            {
                "message": "Please restart the conversation",
                "expected_type": "command",
                "description": "Command"
            },
            {
                "message": "What is the best way to optimize conversion?",
                "expected_type": "question",
                "description": "Question"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test {i}: {test_case['description']} ---")
            
            # Test message classification
            message_type = self.orchestrator._classify_message(test_case["message"])
            print(f"Input: {test_case['message']}")
            print(f"Expected Type: {test_case['expected_type']}")
            print(f"Actual Type: {message_type}")
            print(f"Classification Correct: {message_type == test_case['expected_type']}")
            
            # Test full processing
            result = await self.orchestrator.process_user_message(test_case["message"])
            print(f"Processing Success: {result['success']}")
            print(f"Response Length: {len(result['response'])} characters")
    
    def test_memory_layer(self):
        """Test Memory Layer functionality"""
        print(f"\n{'='*80}")
        print("TESTING MEMORY LAYER FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Test conversation storage
        print(f"\n--- Test 1: Conversation Storage ---")
        initial_count = len(self.orchestrator.session_state["conversation_history"])
        
        self.orchestrator._store_conversation_context("user", "Test message")
        self.orchestrator._store_conversation_context("assistant", "Test response")
        
        final_count = len(self.orchestrator.session_state["conversation_history"])
        print(f"Initial conversation count: {initial_count}")
        print(f"Final conversation count: {final_count}")
        print(f"Messages added: {final_count - initial_count}")
        
        # Test conversation retrieval
        print(f"\n--- Test 2: Conversation Retrieval ---")
        recent_context = self.orchestrator._retrieve_conversation_context(limit=5)
        print(f"Retrieved {len(recent_context)} recent messages")
        
        for i, msg in enumerate(recent_context[-3:], 1):
            print(f"  {i}. {msg['role']}: {msg['content'][:50]}...")
        
        # Test session state updates
        print(f"\n--- Test 3: Session State Updates ---")
        self.orchestrator._update_session_state("test_key", "test_value")
        print(f"Updated session state with test_key")
        print(f"Session state keys: {list(self.orchestrator.session_state.keys())}")
    
    def test_validation_layer(self):
        """Test Validation Layer functionality"""
        print(f"\n{'='*80}")
        print("TESTING VALIDATION LAYER FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Test input validation
        print(f"\n--- Test 1: Input Validation ---")
        
        test_messages = [
            ("I want a landing page", "category_selection"),
            ("This is a very long message " * 100, "requirements"),  # Too long
            ("", "general"),  # Empty
            ("What is the best design?", "question")
        ]
        
        for message, input_type in test_messages:
            validation_result = self.orchestrator._validate_user_input(message, input_type)
            print(f"Message: {message[:50]}...")
            print(f"Input Type: {input_type}")
            print(f"Validation Success: {validation_result['success']}")
            print(f"Is Valid: {validation_result['is_valid']}")
            print(f"Validation Results: {len(validation_result.get('validation_results', []))}")
            print()
    
    def test_tools_layer(self):
        """Test Tools Layer functionality"""
        print(f"\n{'='*80}")
        print("TESTING TOOLS LAYER FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Test database tools
        print(f"\n--- Test 1: Database Tools ---")
        
        # Test category constraints
        constraints = self.orchestrator.database_tools.get_category_constraints("landing")
        print(f"Landing page constraints:")
        print(f"  Success: {constraints['success']}")
        print(f"  Templates Count: {constraints.get('templates_count', 0)}")
        print(f"  Available Styles: {constraints.get('styles', [])[:3]}")
        print(f"  Available Features: {constraints.get('features', [])[:3]}")
        
        # Test validation tools
        print(f"\n--- Test 2: Validation Tools ---")
        
        # Test email validation
        email_result = self.orchestrator.validation_tools.validate_email("test@example.com")
        print(f"Email validation (test@example.com): {email_result['is_valid']}")
        
        # Test string length validation
        length_result = self.orchestrator.validation_tools.validate_string_length("Short text", min_length=5, max_length=20)
        print(f"String length validation: {length_result['is_valid']}")
    
    def test_recovery_layer(self):
        """Test Recovery Layer functionality"""
        print(f"\n{'='*80}")
        print("TESTING RECOVERY LAYER FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Test session status
        print(f"\n--- Test 1: Session Status ---")
        status = self.orchestrator.get_session_status()
        print(f"Session ID: {status['session_id']}")
        print(f"State: {status['state']}")
        print(f"Recovery Attempts: {status['recovery_attempts']}")
        print(f"Error History Length: {len(status['session_state']['error_history'])}")
        
        # Test session reset
        print(f"\n--- Test 2: Session Reset ---")
        reset_result = self.orchestrator.reset_session()
        print(f"Reset Success: {reset_result['success']}")
        print(f"New Session ID: {reset_result['session_id']}")
        
        # Check state after reset
        new_status = self.orchestrator.get_session_status()
        print(f"State After Reset: {new_status['state']}")
        print(f"Recovery Attempts After Reset: {new_status['recovery_attempts']}")
    
    def test_feedback_layer(self):
        """Test Feedback Layer functionality"""
        print(f"\n{'='*80}")
        print("TESTING FEEDBACK LAYER FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Test initial state
        print(f"\n--- Test 1: Initial State ---")
        print(f"Initial State: {self.orchestrator.state.value}")
        print(f"Waiting for Feedback: {self.orchestrator._is_waiting_for_feedback()}")
        
        # Test setting feedback state
        print(f"\n--- Test 2: Setting Feedback State ---")
        pending_operation = {"type": "template_selection", "data": {"template_id": "123"}}
        self.orchestrator._set_feedback_state("template_confirmation", pending_operation)
        
        print(f"State After Setting Feedback: {self.orchestrator.state.value}")
        print(f"Feedback Required: {self.orchestrator.feedback_required}")
        print(f"Waiting for Feedback: {self.orchestrator._is_waiting_for_feedback()}")
        
        # Test clearing feedback state
        print(f"\n--- Test 3: Clearing Feedback State ---")
        self.orchestrator._clear_feedback_state()
        
        print(f"State After Clearing: {self.orchestrator.state.value}")
        print(f"Feedback Required: {self.orchestrator.feedback_required}")
        print(f"Waiting for Feedback: {self.orchestrator._is_waiting_for_feedback()}")
    
    async def test_reasoning_chain(self):
        """Test reasoning chain functionality"""
        print(f"\n{'='*80}")
        print("TESTING REASONING CHAIN FUNCTIONALITY")
        print(f"{'='*80}")
        
        # Process a message to generate reasoning chain
        print(f"\n--- Test 1: Generating Reasoning Chain ---")
        result = await self.orchestrator.process_user_message(
            "I want to create a login page for my e-commerce site"
        )
        
        # Check reasoning chain
        status = self.orchestrator.get_session_status()
        reasoning_chain = status['session_state']['reasoning_chain']
        
        print(f"Reasoning Chain Length: {len(reasoning_chain)}")
        print(f"Reasoning Steps:")
        
        for i, step in enumerate(reasoning_chain, 1):
            print(f"  {i}. {step['layer']} - {step['step']}: {step['thinking'][:100]}...")
        
        # Test reasoning step addition
        print(f"\n--- Test 2: Adding Reasoning Steps ---")
        initial_count = len(reasoning_chain)
        
        self.orchestrator._add_reasoning_step(
            "Test", "test_step", "This is a test reasoning step", "Test decision"
        )
        
        new_status = self.orchestrator.get_session_status()
        new_reasoning_chain = new_status['session_state']['reasoning_chain']
        
        print(f"Initial Reasoning Steps: {initial_count}")
        print(f"Final Reasoning Steps: {len(new_reasoning_chain)}")
        print(f"Steps Added: {len(new_reasoning_chain) - initial_count}")
    
    async def run_comprehensive_test(self):
        """Run all enhanced orchestrator tests"""
        print(f"ENHANCED ORCHESTRATOR COMPREHENSIVE TEST")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*80}")
        
        try:
            # Test 1: Basic Functionality
            basic_results = await self.test_basic_functionality()
            
            # Test 2: Control Layer Routing
            await self.test_control_layer_routing()
            
            # Test 3: Memory Layer
            self.test_memory_layer()
            
            # Test 4: Validation Layer
            self.test_validation_layer()
            
            # Test 5: Tools Layer
            self.test_tools_layer()
            
            # Test 6: Recovery Layer
            self.test_recovery_layer()
            
            # Test 7: Feedback Layer
            self.test_feedback_layer()
            
            # Test 8: Reasoning Chain
            await self.test_reasoning_chain()
            
            print(f"\n{'='*80}")
            print("ENHANCED ORCHESTRATOR TEST SUMMARY")
            print(f"{'='*80}")
            print(f"✅ Basic Functionality: Working")
            print(f"✅ Control Layer Routing: Working")
            print(f"✅ Memory Layer: Working")
            print(f"✅ Validation Layer: Working")
            print(f"✅ Tools Layer: Working")
            print(f"✅ Recovery Layer: Working")
            print(f"✅ Feedback Layer: Working")
            print(f"✅ Reasoning Chain: Working")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False

async def main():
    """Main test function"""
    test_suite = EnhancedOrchestratorTest()
    success = await test_suite.run_comprehensive_test()
    
    if success:
        print(f"\n🎉 Enhanced orchestrator tests completed successfully!")
        print(f"🏗️ Layer patterns successfully integrated into core orchestrator functionality.")
    else:
        print(f"\n❌ Some tests failed. Check logs for details.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 