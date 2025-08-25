#!/usr/bin/env python3
"""
Latency/Inference Time Testing Script
Tests response times across different scenarios to evaluate multi-agent system responsiveness
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any
import statistics

class LatencyInferenceTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results_dir = "evaluation_result"
        self.trials_per_scenario = 2
        
        # Phase 1: Template recommendation intents (from flow orchestrator)
        self.phase1_intents = [
            "requirements_analysis",
            "template_recommendation", 
            "template_selection",
            "general",
            "create_ui_mockup"
        ]
        
        # Phase 1 test prompts for each intent
        self.phase1_prompts = {
            "requirements_analysis": [
                "I want to discuss the requirements for my website first",
                "Let me analyze what I need for my project"
            ],
            "template_recommendation": [
                "Can you recommend templates for my website?",
                "Show me some template options"
            ],
            "template_selection": [
                "I want to select from existing templates",
                "Show me templates I can choose from"
            ],
            "general": [
                "Hello, how are you?",
                "What can you help me with?"
            ],
            "create_ui_mockup": [
                "I want to build a login page mockup",
                "Create a landing page for me"
            ]
        }
        
        # Phase 2: UI editing scenarios
        self.phase2_scenarios = {
            "single_request": [
                "Change button color to blue",
                "Make the text larger"
            ],
            "multi_request": [
                "Change button color to blue and make it larger",
                "Add more padding and change the font"
            ],
            "report_generation": [
                "Generate a PDF report of my design",
                "Create a report with screenshots"
            ]
        }
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
        
    async def test_phase1_latency(self, session: aiohttp.ClientSession) -> Dict[str, List[Dict[str, Any]]]:
        """Test Phase 1: Template recommendation latency for different intents"""
        print(f"🔄 Starting Phase 1: Template Recommendation Latency Testing")
        print("=" * 70)
        
        all_results = {}
        
        for intent in self.phase1_intents:
            print(f"\n📊 Testing Intent: {intent}")
            print("-" * 40)
            
            intent_results = []
            prompts = self.phase1_prompts[intent]
            
            for trial_num in range(self.trials_per_scenario):
                prompt = prompts[trial_num]
                print(f"  🔄 Trial {trial_num + 1}/{self.trials_per_scenario}: {prompt[:50]}...")
                
                start_time = time.time()
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json={"message": prompt, "session_id": f"latency_test_{intent}_{trial_num}"}
                    ) as response:
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        if response.status == 200:
                            response_data = await response.json()
                            success = response_data.get("success", False)
                            
                            trial_result = {
                                "prompt": prompt,
                                "response_time": response_time,
                                "success": success,
                                "status_code": response.status,
                                "response_data": response_data
                            }
                            
                            if success:
                                print(f"    ✅ Success ({response_time:.3f}s)")
                            else:
                                print(f"    ❌ Failed ({response_time:.3f}s)")
                            
                        else:
                            trial_result = {
                                "prompt": prompt,
                                "response_time": response_time,
                                "success": False,
                                "status_code": response.status,
                                "response_data": None
                            }
                            print(f"    ❌ HTTP Error {response.status} ({response_time:.3f}s)")
                        
                        intent_results.append(trial_result)
                        
                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    trial_result = {
                        "prompt": prompt,
                        "response_time": response_time,
                        "success": False,
                        "status_code": None,
                        "response_data": None,
                        "error": str(e)
                    }
                    print(f"    ❌ Exception ({response_time:.3f}s): {e}")
                    intent_results.append(trial_result)
            
            all_results[intent] = intent_results
            
            # Calculate intent-specific stats
            successful_trials = [r for r in intent_results if r["success"]]
            if successful_trials:
                avg_time = statistics.mean([r["response_time"] for r in successful_trials])
                median_time = statistics.median([r["response_time"] for r in successful_trials])
                print(f"  📊 {len(successful_trials)}/{len(intent_results)} successful trials")
                print(f"  ⏱️  Average: {avg_time:.3f}s, Median: {median_time:.3f}s")
            else:
                print(f"  📊 0/{len(intent_results)} successful trials")
        
        return all_results
    
    async def test_phase2_latency(self, session: aiohttp.ClientSession) -> Dict[str, List[Dict[str, Any]]]:
        """Test Phase 2: UI editing latency for different scenarios"""
        print(f"\n🔄 Starting Phase 2: UI Editing Latency Testing")
        print("=" * 70)
        
        all_results = {}
        
        for scenario, prompts in self.phase2_scenarios.items():
            print(f"\n📊 Testing Scenario: {scenario.replace('_', ' ').title()}")
            print("-" * 40)
            
            scenario_results = []
            
            for trial_num in range(self.trials_per_scenario):
                prompt = prompts[trial_num]
                print(f"  🔄 Trial {trial_num + 1}/{self.trials_per_scenario}: {prompt[:50]}...")
                
                start_time = time.time()
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/ui-editor/chat",
                        json={"message": prompt, "session_id": f"latency_test_phase2_{scenario}_{trial_num}"}
                    ) as response:
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        if response.status == 200:
                            response_data = await response.json()
                            success = response_data.get("success", False)
                            
                            trial_result = {
                                "prompt": prompt,
                                "response_time": response_time,
                                "success": success,
                                "status_code": response.status,
                                "response_data": response_data
                            }
                            
                            if success:
                                print(f"    ✅ Success ({response_time:.3f}s)")
                            else:
                                print(f"    ❌ Failed ({response_time:.3f}s)")
                            
                        else:
                            trial_result = {
                                "prompt": prompt,
                                "response_time": response_time,
                                "success": False,
                                "status_code": response.status,
                                "response_data": None
                            }
                            print(f"    ❌ HTTP Error {response.status} ({response_time:.3f}s)")
                        
                        scenario_results.append(trial_result)
                        
                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    trial_result = {
                        "prompt": prompt,
                        "response_time": response_time,
                        "success": False,
                        "status_code": None,
                        "response_data": None,
                        "error": str(e)
                    }
                    print(f"    ❌ Exception ({response_time:.3f}s): {e}")
                    scenario_results.append(trial_result)
            
            all_results[scenario] = scenario_results
            
            # Calculate scenario-specific stats
            successful_trials = [r for r in scenario_results if r["success"]]
            if successful_trials:
                avg_time = statistics.mean([r["response_time"] for r in successful_trials])
                median_time = statistics.median([r["response_time"] for r in successful_trials])
                print(f"  📊 {len(successful_trials)}/{len(scenario_results)} successful trials")
                print(f"  ⏱️  Average: {avg_time:.3f}s, Median: {median_time:.3f}s")
            else:
                print(f"  📊 0/{len(scenario_results)} successful trials")
        
        return all_results
    
    def calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a set of results"""
        if not results:
            return {
                "total_trials": 0,
                "successful_trials": 0,
                "failed_trials": 0,
                "success_rate": 0.0,
                "average": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "min": 0.0,
                "max": 0.0
            }
        
        successful_trials = [r for r in results if r["success"]]
        failed_trials = [r for r in results if not r["success"]]
        
        if successful_trials:
            response_times = [r["response_time"] for r in successful_trials]
            response_times.sort()
            
            stats = {
                "total_trials": len(results),
                "successful_trials": len(successful_trials),
                "failed_trials": len(failed_trials),
                "success_rate": len(successful_trials) / len(results),
                "average": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": response_times[int(len(response_times) * 0.95)] if len(response_times) > 0 else 0.0,
                "min": min(response_times),
                "max": max(response_times)
            }
        else:
            stats = {
                "total_trials": len(results),
                "successful_trials": 0,
                "failed_trials": len(failed_trials),
                "success_rate": 0.0,
                "average": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "min": 0.0,
                "max": 0.0
            }
        
        return stats
    
    async def save_detailed_results(self, phase1_results: Dict, phase2_results: Dict):
        """Save detailed test results to file"""
        timestamp = datetime.now().isoformat()
        filename = os.path.join(self.results_dir, "latency_inference_detailed_results.txt")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("LATENCY/INFERENCE TIME TESTING - DETAILED RESULTS\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Completed: {timestamp}\n\n")
            
            # Phase 1 Results
            f.write("PHASE 1: TEMPLATE RECOMMENDATION LATENCY\n")
            f.write("=" * 50 + "\n\n")
            
            for intent, results in phase1_results.items():
                f.write(f"Intent: {intent}\n")
                f.write("-" * 30 + "\n")
                
                stats = self.calculate_statistics(results)
                f.write(f"  Trials: {stats['successful_trials']}/{stats['total_trials']}\n")
                f.write(f"  Average: {stats['average']:.3f}s\n")
                f.write(f"  Median: {stats['median']:.3f}s\n")
                f.write(f"  P95: {stats['p95']:.3f}s\n")
                f.write(f"  Range: {stats['min']:.3f}s - {stats['max']:.3f}s\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"    Trial {i}:\n")
                    f.write(f"      Prompt: {result['prompt']}\n")
                    f.write(f"      Response Time: {result['response_time']:.3f}s\n")
                    f.write(f"      Success: {result['success']}\n")
                    f.write(f"      Status Code: {result['status_code']}\n")
                    if 'error' in result:
                        f.write(f"      Error: {result['error']}\n")
                    f.write("\n")
                
                f.write("\n" + "-" * 50 + "\n\n")
            
            # Phase 2 Results
            f.write("PHASE 2: UI EDITING LATENCY\n")
            f.write("=" * 50 + "\n\n")
            
            for scenario, results in phase2_results.items():
                f.write(f"Scenario: {scenario.replace('_', ' ').title()}\n")
                f.write("-" * 30 + "\n")
                
                stats = self.calculate_statistics(results)
                f.write(f"  Trials: {stats['successful_trials']}/{stats['total_trials']}\n")
                f.write(f"  Average: {stats['average']:.3f}s\n")
                f.write(f"  Median: {stats['median']:.3f}s\n")
                f.write(f"  P95: {stats['p95']:.3f}s\n")
                f.write(f"  Range: {stats['min']:.3f}s - {stats['max']:.3f}s\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"    Trial {i}:\n")
                    f.write(f"      Prompt: {result['prompt']}\n")
                    f.write(f"      Response Time: {result['response_time']:.3f}s\n")
                    f.write(f"      Success: {result['success']}\n")
                    f.write(f"      Status Code: {result['status_code']}\n")
                    if 'error' in result:
                        f.write(f"      Error: {result['error']}\n")
                    f.write("\n")
                
                f.write("\n" + "-" * 50 + "\n\n")
        
        print(f"📁 Detailed results saved to: {filename}")
    
    async def save_summary(self, phase1_results: Dict, phase2_results: Dict):
        """Save test summary to file"""
        timestamp = datetime.now().isoformat()
        filename = os.path.join(self.results_dir, "latency_inference_summary.txt")
        
        # Calculate overall stats for each phase
        all_phase1_results = []
        for results in phase1_results.values():
            all_phase1_results.extend(results)
        
        all_phase2_results = []
        for results in phase2_results.values():
            all_phase2_results.extend(results)
        
        phase1_stats = self.calculate_statistics(all_phase1_results)
        phase2_stats = self.calculate_statistics(all_phase2_results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("LATENCY/INFERENCE TIME TESTING - SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Completed: {timestamp}\n\n")
            
            # Phase 1 Summary
            f.write("PHASE 1: TEMPLATE RECOMMENDATION\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Trials: {phase1_stats['total_trials']}\n")
            f.write(f"Average Response Time: {phase1_stats['average']:.3f}s\n")
            f.write(f"Median Response Time: {phase1_stats['median']:.3f}s\n")
            f.write(f"P95 Response Time: {phase1_stats['p95']:.3f}s\n")
            f.write(f"Response Time Range: {phase1_stats['min']:.3f}s - {phase1_stats['max']:.3f}s\n\n")
            
            f.write("Intent-Specific Performance:\n")
            for intent, results in phase1_results.items():
                stats = self.calculate_statistics(results)
                f.write(f"  {intent.replace('_', ' ').title()}: {stats['average']:.3f}s avg, {stats['median']:.3f}s median\n")
            
            f.write("\n")
            
            # Phase 2 Summary
            f.write("PHASE 2: UI EDITING\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Trials: {phase2_stats['total_trials']}\n")
            f.write(f"Average Response Time: {phase2_stats['average']:.3f}s\n")
            f.write(f"Median Response Time: {phase2_stats['median']:.3f}s\n")
            f.write(f"P95 Response Time: {phase2_stats['p95']:.3f}s\n")
            f.write(f"Response Time Range: {phase2_stats['min']:.3f}s - {phase2_stats['max']:.3f}s\n\n")
            
            f.write("Scenario-Specific Performance:\n")
            for scenario, results in phase2_results.items():
                stats = self.calculate_statistics(results)
                f.write(f"  {scenario.replace('_', ' ').title()}: {stats['average']:.3f}s avg, {stats['median']:.3f}s median\n")
        
        print(f"📁 Summary saved to: {filename}")
    
    async def run_latency_tests(self) -> Dict[str, Any]:
        """Run all latency tests and return results"""
        print("⏱️  Starting Latency/Inference Time Testing")
        print(f"📊 Phase 1: {len(self.phase1_intents)} intents × {self.trials_per_scenario} trials each")
        print(f"📊 Phase 2: {len(self.phase2_scenarios)} scenarios × {self.trials_per_scenario} trials each")
        print(f"🌐 Testing endpoints: {self.base_url}/api/chat and {self.base_url}/api/ui-editor/chat\n")
        
        async with aiohttp.ClientSession() as session:
            # Test Phase 1
            phase1_results = await self.test_phase1_latency(session)
            
            # Test Phase 2
            phase2_results = await self.test_phase2_latency(session)
            
            # Save results
            await self.save_detailed_results(phase1_results, phase2_results)
            await self.save_summary(phase1_results, phase2_results)
            
            # Calculate overall statistics
            all_phase1_results = []
            for results in phase1_results.values():
                all_phase1_results.extend(results)
            
            all_phase2_results = []
            for results in phase2_results.values():
                all_phase2_results.extend(results)
            
            phase1_stats = self.calculate_statistics(all_phase1_results)
            phase2_stats = self.calculate_statistics(all_phase2_results)
            
            # Print summary
            print("\n" + "=" * 70)
            print("⏱️  LATENCY/INFERENCE TIME TESTING COMPLETED")
            print("=" * 70)
            
            print(f"📊 Phase 1 (Template Recommendation):")
            print(f"   📈 Total Trials: {phase1_stats['total_trials']}")
            print(f"   ⏱️  Average: {phase1_stats['average']:.3f}s")
            print(f"   ⏱️  Median: {phase1_stats['median']:.3f}s")
            print(f"   ⏱️  P95: {phase1_stats['p95']:.3f}s")
            
            print(f"\n📊 Phase 2 (UI Editing):")
            print(f"   📈 Total Trials: {phase2_stats['total_trials']}")
            print(f"   ⏱️  Average: {phase2_stats['average']:.3f}s")
            print(f"   ⏱️  Median: {phase2_stats['median']:.3f}s")
            print(f"   ⏱️  P95: {phase2_stats['p95']:.3f}s")
            
            return {
                "phase1": {
                    "total_trials": phase1_stats['total_trials'],
                    "overall_stats": phase1_stats,
                    "intent_results": phase1_results
                },
                "phase2": {
                    "total_trials": phase2_stats['total_trials'],
                    "overall_stats": phase2_stats,
                    "scenario_results": phase2_results
                }
            }

if __name__ == "__main__":
    tester = LatencyInferenceTester()
    asyncio.run(tester.run_latency_tests())
