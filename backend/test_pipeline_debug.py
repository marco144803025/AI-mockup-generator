#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from agents.lean_flow_orchestrator import LeanFlowOrchestrator
import asyncio

async def test_pipeline_debug():
    try:
        print("=== TESTING PIPELINE DEBUG ===")
        
        # Create orchestrator
        orchestrator = LeanFlowOrchestrator(session_id="test_pipeline_session")
        
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
        
        # Step 3: Check session state after initial phase
        print("\n4. Session state after initial phase:")
        print(f"Current phase: {orchestrator.session_state.get('current_phase')}")
        print(f"Detected page type: {orchestrator.session_state.get('detected_page_type')}")
        print(f"Requirements: {orchestrator.session_state.get('requirements')}")
        
        # Step 4: If we're in requirements phase, test the pipeline directly
        if orchestrator.session_state.get('current_phase') == 'requirements':
            print("\n5. Testing pipeline execution...")
            
            # Build context with detected page type
            context = {}
            if orchestrator.session_state.get('detected_page_type'):
                context["page_type"] = orchestrator.session_state.get('detected_page_type')
                context["selected_category"] = orchestrator.session_state.get('detected_page_type')
            
            print(f"Context: {context}")
            
            # Test the pipeline execution directly
            pipeline_result = orchestrator._execute_agent_pipeline(
                ["requirements_analysis", "template_recommendation", "question_generation", "user_proxy"],
                message,
                context
            )
            
            print(f"\n6. Pipeline result:")
            print(f"Success: {pipeline_result.get('success')}")
            print(f"Error: {pipeline_result.get('error', 'None')}")
            
            # Check agent results
            agent_results = pipeline_result.get('agent_results', {})
            print(f"\n7. Agent results:")
            
            if "requirements_analysis" in agent_results:
                req_result = agent_results["requirements_analysis"]
                print(f"Requirements analysis: {type(req_result)}")
                if isinstance(req_result, dict) and "data" in req_result:
                    primary_result = req_result["data"]["primary_result"]
                    print(f"Primary result: {primary_result}")
                    print(f"Page type in primary result: {primary_result.get('page_type')}")
            
            if "template_recommendation" in agent_results:
                rec_result = agent_results["template_recommendation"]
                print(f"Template recommendation: {type(rec_result)}")
                if isinstance(rec_result, dict) and "data" in rec_result:
                    primary_result = rec_result["data"]["primary_result"]
                    print(f"Primary result: {type(primary_result)}")
                    if isinstance(primary_result, list):
                        print(f"Number of templates: {len(primary_result)}")
                        for i, template in enumerate(primary_result[:2]):
                            print(f"  Template {i+1}: {template.get('name', 'Unknown')} - {template.get('category', 'Unknown')}")
            
            # Check final output
            final_output = pipeline_result.get('final_output', 'No output')
            print(f"\n8. Final output: {final_output[:200]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline_debug()) 