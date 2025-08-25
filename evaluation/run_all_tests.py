#!/usr/bin/env python3
"""
Test Runner Script
Runs all active testing scripts and generates a comprehensive summary report
"""

import asyncio
import os
from datetime import datetime

# Import test classes
try:
    from test_latency_inference import LatencyInferenceTester
except ImportError as e:
    print(f"❌ Error importing test classes: {e}")
    exit(1)

async def run_all_tests():
    """Run all active tests and generate comprehensive summary"""
    print("🚀 LAUNCHING COMPREHENSIVE TESTING SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_results = {}
    
    # 1. API Reliability Testing - SKIPPED
    print("\n" + "=" * 70)
    print("🔧 TEST 1: API RELIABILITY TESTING - SKIPPED")
    print("=" * 70)
    print("⏭️  Skipping API Reliability Testing (already tested)")
    all_results["api_reliability"] = {"status": "skipped", "reason": "already tested"}
    
    # 2. Context Retention Testing - SKIPPED
    print("\n" + "=" * 70)
    print("🧠 TEST 2: CONTEXT RETENTION TESTING - SKIPPED")
    print("=" * 70)
    print("⏭️  Skipping Context Retention Testing (temporarily disabled)")
    all_results["context_retention"] = {"status": "skipped", "reason": "temporarily disabled"}
    
    # 3. Latency/Inference Time Testing
    print("\n" + "=" * 70)
    print("⏱️  TEST 3: LATENCY/INFERENCE TIME TESTING")
    print("=" * 70)
    try:
        latency_tester = LatencyInferenceTester()
        latency_results = await latency_tester.run_latency_tests()
        all_results["latency_inference"] = latency_results
        print("✅ Latency/Inference Time Testing completed successfully")
    except Exception as e:
        print(f"❌ Latency/Inference Time Testing failed: {e}")
        all_results["latency_inference"] = {"error": str(e)}
    
    # 4. Schema Compliance Testing - REMOVED
    print("\n" + "=" * 70)
    print("🔍 TEST 4: SCHEMA COMPLIANCE TESTING - REMOVED")
    print("=" * 70)
    print("⏭️  Schema Compliance Testing removed as requested")
    all_results["schema_compliance"] = {"status": "removed", "reason": "user request"}
    
    # Generate comprehensive summary report
    await generate_comprehensive_report(all_results)
    
    print("\n" + "=" * 80)
    print("🎯 COMPREHENSIVE TESTING SUITE COMPLETED")
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def generate_comprehensive_report(all_results):
    """Generate a comprehensive summary report"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"evaluation_result/comprehensive_test_report_{timestamp}.txt"
    
    # Ensure results directory exists
    os.makedirs("evaluation_result", exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE TESTING SUITE REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Evaluation Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Tests: 4 (1 active, 2 skipped, 1 removed)\n\n")
        
        # API Reliability Summary
        f.write("1. API RELIABILITY TESTING\n")
        f.write("-" * 40 + "\n")
        if "api_reliability" in all_results and "status" in all_results["api_reliability"] and all_results["api_reliability"]["status"] == "skipped":
            f.write(f"   Status: ⏭️  Skipped\n")
            f.write(f"   Reason: {all_results['api_reliability'].get('reason', 'N/A')}\n")
        elif "api_reliability" in all_results and "error" not in all_results["api_reliability"]:
            api_results = all_results["api_reliability"]
            f.write(f"   Status: ✅ Completed\n")
            f.write(f"   Total Trials: {api_results.get('total_trials', 'N/A')}\n")
            f.write(f"   Success Rate: {api_results.get('success_rate', 'N/A')}\n")
        else:
            f.write(f"   Status: ❌ Failed\n")
            f.write(f"   Error: {all_results['api_reliability'].get('error', 'Unknown error')}\n")
        f.write("\n")
        
        # Context Retention Summary
        f.write("2. CONTEXT RETENTION TESTING\n")
        f.write("-" * 40 + "\n")
        if "context_retention" in all_results and "status" in all_results["context_retention"] and all_results["context_retention"]["status"] == "skipped":
            f.write(f"   Status: ⏭️  Skipped\n")
            f.write(f"   Reason: {all_results['context_retention'].get('reason', 'N/A')}\n")
        elif "context_retention" in all_results and "error" not in all_results["context_retention"]:
            context_results = all_results["context_retention"]
            f.write(f"   Status: ✅ Completed\n")
            f.write(f"   Total Trials: {context_results.get('total_trials', 'N/A')}\n")
            f.write(f"   Context Recall Rate: {context_results.get('context_recall_rate', 'N/A')}\n")
        else:
            f.write(f"   Status: ❌ Failed\n")
            f.write(f"   Error: {all_results['context_retention'].get('error', 'Unknown error')}\n")
        f.write("\n")
        
        # Latency/Inference Time Summary
        f.write("3. LATENCY/INFERENCE TIME TESTING\n")
        f.write("-" * 40 + "\n")
        if "latency_inference" in all_results and "error" not in all_results["latency_inference"]:
            latency_results = all_results["latency_inference"]
            f.write(f"   Status: ✅ Completed\n")
            f.write(f"   Phase 1 Trials: {latency_results.get('phase1', {}).get('total_trials', 'N/A')}\n")
            f.write(f"   Phase 2 Trials: {latency_results.get('phase2', {}).get('total_trials', 'N/A')}\n")
            f.write(f"   Phase 1 Average: {latency_results.get('phase1', {}).get('overall_stats', {}).get('average', 'N/A')}s\n")
            f.write(f"   Phase 2 Average: {latency_results.get('phase2', {}).get('overall_stats', {}).get('average', 'N/A')}s\n")
        else:
            f.write(f"   Status: ❌ Failed\n")
            f.write(f"   Error: {all_results['latency_inference'].get('error', 'Unknown error')}\n")
        f.write("\n")
        
        # Schema Compliance Summary
        f.write("4. SCHEMA COMPLIANCE TESTING\n")
        f.write("-" * 40 + "\n")
        if "schema_compliance" in all_results and "status" in all_results["schema_compliance"] and all_results["schema_compliance"]["status"] == "removed":
            f.write(f"   Status: 🗑️  Removed\n")
            f.write(f"   Reason: {all_results['schema_compliance'].get('reason', 'N/A')}\n")
        elif "schema_compliance" in all_results and "error" not in all_results["schema_compliance"]:
            schema_results = all_results["schema_compliance"]
            f.write(f"   Status: ✅ Completed\n")
            f.write(f"   Total Trials: {schema_results.get('overall_stats', {}).get('total_trials', 'N/A')}\n")
            f.write(f"   Compliance Rate: {schema_results.get('overall_stats', {}).get('overall_compliance_rate', 'N/A')}%\n")
        else:
            f.write(f"   Status: ❌ Failed\n")
            f.write(f"   Error: {all_results['schema_compliance'].get('error', 'Unknown error')}\n")
        f.write("\n")
        
        # Overall System Health Assessment
        f.write("OVERALL SYSTEM HEALTH ASSESSMENT\n")
        f.write("=" * 80 + "\n\n")
        
        completed_tests = sum(1 for test in all_results.values() if "error" not in test and test.get("status") not in ["skipped", "removed"])
        skipped_tests = sum(1 for test in all_results.values() if test.get("status") == "skipped")
        removed_tests = sum(1 for test in all_results.values() if test.get("status") == "removed")
        failed_tests = sum(1 for test in all_results.values() if "error" in test)
        total_tests = len(all_results)
        
        f.write(f"Test Completion Rate: {completed_tests}/{total_tests-skipped_tests-removed_tests} ({completed_tests/(total_tests-skipped_tests-removed_tests)*100:.1f}%)\n")
        f.write(f"Skipped Tests: {skipped_tests}\n")
        f.write(f"Removed Tests: {removed_tests}\n")
        f.write(f"Failed Tests: {failed_tests}\n\n")
        
        if failed_tests == 0:
            f.write("🎉 All active tests completed successfully!\n")
            f.write("📊 System appears to be functioning normally\n")
            f.write("🔍 Review individual test results for detailed performance metrics\n")
        else:
            f.write("⚠️  Some tests failed. Review individual test results for details.\n")
            f.write("🔍 Check system logs and individual test outputs for troubleshooting\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF COMPREHENSIVE TESTING SUITE REPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"📁 Comprehensive report saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())


