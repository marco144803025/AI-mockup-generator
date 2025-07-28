#!/usr/bin/env python3
"""
Debug script to show detailed agent thought processes and responses
"""

import logging
import json
from datetime import datetime
from layered_orchestrator import LayeredOrchestrator

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_debug.log'),
        logging.StreamHandler()
    ]
)

class AgentDebugger:
    def __init__(self):
        self.orchestrator = LayeredOrchestrator()
        self.logger = logging.getLogger(__name__)
        
    async def debug_user_message(self, message: str, context: dict = None):
        """Debug a user message through the entire agent pipeline"""
        
        print(f"\n{'='*80}")
        print(f"DEBUGGING USER MESSAGE: {message}")
        print(f"CONTEXT: {json.dumps(context, indent=2) if context else 'None'}")
        print(f"{'='*80}")
        
        # Step 1: Control Layer - Process and classify user input
        print(f"\n1. CONTROL LAYER - Input Classification:")
        print(f"{'-'*50}")
        user_input = self.orchestrator.control.process_user_input(message, context)
        print(f"Input Type: {user_input.input_type.value}")
        print(f"Confidence: {user_input.confidence}")
        print(f"Extracted Data: {json.dumps(user_input.extracted_data, indent=2)}")
        
        # Step 2: Validation Layer
        print(f"\n2. VALIDATION LAYER - Input Validation:")
        print(f"{'-'*50}")
        validation_results = self.orchestrator.validation.validate_user_input(message, user_input.input_type.value)
        for result in validation_results:
            print(f"Validation: {result.level.value} - {result.message}")
            if result.field:
                print(f"  Field: {result.field}")
            if result.value:
                print(f"  Value: {result.value}")
        
        # Step 3: Control Layer - Generate initial response
        print(f"\n3. CONTROL LAYER - Response Generation:")
        print(f"{'-'*50}")
        system_response = self.orchestrator.control.generate_response(user_input, context)
        print(f"Response Type: {system_response.response_type.value}")
        print(f"Content: {system_response.content}")
        print(f"Actions: {json.dumps(system_response.actions, indent=2)}")
        
        # Step 4: Intelligence Layer - LLM Enhancement
        print(f"\n4. INTELLIGENCE LAYER - LLM Enhancement:")
        print(f"{'-'*50}")
        enhanced_response = await self.orchestrator._enhance_response_with_llm(user_input, system_response, context)
        print(f"Enhanced Content: {enhanced_response.content}")
        
        # Step 5: Tools Layer - Tool Execution
        print(f"\n5. TOOLS LAYER - Tool Execution:")
        print(f"{'-'*50}")
        tool_results = await self.orchestrator._execute_tools(system_response.actions)
        for result in tool_results:
            print(f"Tool: {result.get('action', 'unknown')}")
            print(f"  Success: {result.get('success', False)}")
            if 'result' in result:
                print(f"  Result: {result['result']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        # Step 6: Final Response
        print(f"\n6. FINAL RESPONSE:")
        print(f"{'-'*50}")
        final_result = await self.orchestrator.process_user_message(message, context)
        print(f"Success: {final_result['success']}")
        print(f"Response: {final_result['response']}")
        print(f"Session ID: {final_result['session_id']}")
        
        # Step 7: Session State
        print(f"\n7. SESSION STATE:")
        print(f"{'-'*50}")
        session_status = self.orchestrator.get_session_status()
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        session_status_serializable = convert_datetime(session_status)
        print(json.dumps(session_status_serializable, indent=2))
        
        return final_result
    
    def show_conversation_history(self):
        """Show the conversation history from the control layer"""
        print(f"\n{'='*80}")
        print("CONVERSATION HISTORY")
        print(f"{'='*80}")
        
        history = self.orchestrator.control.conversation_history
        for entry in history:
            print(f"\nTimestamp: {entry['timestamp']}")
            print(f"Type: {entry['type']}")
            if entry['type'] == 'user_input':
                print(f"Input Type: {entry['input_type']}")
                print(f"Text: {entry['text']}")
                print(f"Confidence: {entry['confidence']}")
                print(f"Extracted Data: {json.dumps(entry['extracted_data'], indent=2)}")
            elif entry['type'] == 'system_response':
                print(f"Response Type: {entry['response_type']}")
                print(f"Content: {entry['content']}")
                print(f"Actions: {json.dumps(entry['actions'], indent=2)}")
            print(f"{'-'*40}")
    
    def show_validation_summary(self):
        """Show validation summary"""
        print(f"\n{'='*80}")
        print("VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        summary = self.orchestrator.validation.get_validation_summary()
        print(json.dumps(summary, indent=2))
    
    def show_tool_statistics(self):
        """Show tool execution statistics"""
        print(f"\n{'='*80}")
        print("TOOL EXECUTION STATISTICS")
        print(f"{'='*80}")
        
        stats = self.orchestrator.tools.get_execution_statistics()
        print(json.dumps(stats, indent=2))

async def main():
    """Main debug function"""
    debugger = AgentDebugger()
    
    # Test with a sample message
    test_message = "I want to create a login UI mockup. Please help me design and build this interface."
    test_context = {
        "selected_category": "login",
        "current_phase": "requirements_gathering"
    }
    
    print("Starting agent debugging...")
    result = await debugger.debug_user_message(test_message, test_context)
    
    # Show additional debug information
    debugger.show_conversation_history()
    debugger.show_validation_summary()
    debugger.show_tool_statistics()
    
    print(f"\n{'='*80}")
    print("DEBUG COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 