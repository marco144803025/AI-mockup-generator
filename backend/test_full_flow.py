#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from agents.lean_flow_orchestrator import LeanFlowOrchestrator
import asyncio

async def test_full_flow():
    try:
        print("=== TESTING FULL FLOW ===")
        
        # Create orchestrator
        orchestrator = LeanFlowOrchestrator(session_id="test_session")
        
        # Test message
        message = "I want to build a login UI mockup"
        
        print(f"\n1. User message: {message}")
        
        # Step 1: Detect initial intent
        print("\n2. Detecting initial intent...")
        initial_intent = await orchestrator._detect_initial_intent(message)
        print(f"Initial intent: {initial_intent}")
        print(f"Detected page type: {orchestrator.session_state.get('detected_page_type')}")
        
        # Step 2: Handle initial intent phase
        print("\n3. Handling initial intent phase...")
        result = await orchestrator._handle_initial_intent_phase(message, initial_intent)
        print(f"Phase: {result.get('phase')}")
        print(f"Response: {result.get('response')[:200]}...")
        
        # Step 3: Check session state
        print("\n4. Session state after initial phase:")
        print(f"Current phase: {orchestrator.session_state.get('current_phase')}")
        print(f"Detected page type: {orchestrator.session_state.get('detected_page_type')}")
        print(f"Initial intent: {orchestrator.session_state.get('initial_intent')}")
        
        # Step 4: If we're in requirements phase, test requirements analysis
        if orchestrator.session_state.get('current_phase') == 'requirements':
            print("\n5. Testing requirements phase...")
            
            # Build context with detected page type
            context = {}
            if orchestrator.session_state.get('detected_page_type'):
                context["page_type"] = orchestrator.session_state.get('detected_page_type')
                context["selected_category"] = orchestrator.session_state.get('detected_page_type')
            
            print(f"Context: {context}")
            
            # Test requirements analysis
            requirements_result = await orchestrator._handle_requirements_phase(message, context)
            print(f"Requirements result: {requirements_result.get('response')[:200]}...")
            
            # Check session state after requirements
            print(f"\n6. Session state after requirements:")
            print(f"Requirements: {orchestrator.session_state.get('requirements')}")
            print(f"Recommendations: {len(orchestrator.session_state.get('recommendations', []))} templates")
            
            # Check if recommendations have the right category
            recommendations = orchestrator.session_state.get('recommendations', [])
            if recommendations:
                print("\n7. Template recommendations:")
                for i, rec in enumerate(recommendations[:3]):
                    template = rec.get('template', {})
                    print(f"  {i+1}. {template.get('name', 'Unknown')} - Category: {template.get('category', 'Unknown')}")
            else:
                print("\n7. No template recommendations found!")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_flow()) 