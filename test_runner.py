#!/usr/bin/env python3
"""
WhatsApp Revenue Copilot - Test Runner & System Validator
Comprehensive testing suite for all system components
"""

import asyncio
import requests
import json
import time
import sys
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    error: str = None
    response: Any = None


class CopilotTester:
    """Comprehensive system tester"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        
        # Service endpoints
        self.endpoints = {
            "agentA": f"{base_url}:8001",
            "agentB": f"{base_url}:8002", 
            "classifier": f"{base_url}:8000",
            "chroma": f"{base_url}:8000",
            "n8n": f"{base_url}:5678"
        }
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"🧪 Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            test_result = TestResult(
                name=test_name,
                passed=True,
                duration=duration,
                response=result
            )
            print(f"✅ {test_name} passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                name=test_name,
                passed=False,
                duration=duration,
                error=str(e)
            )
            print(f"❌ {test_name} failed: {str(e)} ({duration:.2f}s)")
        
        self.results.append(test_result)
        return test_result
    
    def test_health_checks(self):
        """Test all service health endpoints"""
        health_endpoints = {
            "Agent A": f"{self.endpoints['agentA']}/health",
            "Agent B": f"{self.endpoints['agentB']}/health", 
            "Intent Classifier": f"{self.endpoints['classifier']}/health",
            "Chroma": f"{self.endpoints['chroma']}/api/v1/heartbeat"
        }
        
        results = {}
        for service, url in health_endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    results[service] = "✅ Healthy"
                else:
                    results[service] = f"❌ Status {response.status_code}"
            except Exception as e:
                results[service] = f"❌ Error: {str(e)}"
        
        return results
    
    def test_intent_classification(self):
        """Test intent classifier with various inputs"""
        test_cases = [
            ("What's our refund policy?", "knowledge_qa"),
            ("John from Acme wants a PoC, budget 10k", "lead_capture"),
            ("Draft a proposal for Acme", "proposal_request"),
            ("Schedule demo next Wed at 11am", "next_step"),
            ("We lost the deal - budget cut", "status_update"),
            ("Hello there", "smalltalk")
        ]
        
        results = {}
        for text, expected_intent in test_cases:
            try:
                response = requests.post(
                    f"{self.endpoints['classifier']}/classify",
                    json={"message": text, "has_attachments": False},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    actual_intent = data.get("intent")
                    confidence = data.get("confidence", 0)
                    
                    if actual_intent == expected_intent:
                        results[text] = f"✅ {actual_intent} (conf: {confidence:.2f})"
                    else:
                        results[text] = f"❌ Expected {expected_intent}, got {actual_intent}"
                else:
                    results[text] = f"❌ HTTP {response.status_code}"
                    
            except Exception as e:
                results[text] = f"❌ Error: {str(e)}"
        
        return results
    
    def test_agent_a_knowledge(self):
        """Test Agent A knowledge capabilities"""
        tests = {}
        
        # Test knowledge Q&A
        try:
            response = requests.post(
                f"{self.endpoints['agentA']}/agentA/ask",
                json={
                    "userId": "test_user",
                    "text": "What is our refund policy?"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Knowledge Q&A"] = f"✅ Answer: {data.get('answer', '')[:100]}..."
            else:
                tests["Knowledge Q&A"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Knowledge Q&A"] = f"❌ Error: {str(e)}"
        
        # Test document ingestion (mock)
        try:
            response = requests.post(
                f"{self.endpoints['agentA']}/agentA/ingest",
                json={"driveFileId": "test_document_id"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Document Ingestion"] = f"✅ Chunks: {data.get('chunks', 0)}"
            else:
                tests["Document Ingestion"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Document Ingestion"] = f"❌ Error: {str(e)}"
        
        # Test scheduling parsing
        try:
            response = requests.post(
                f"{self.endpoints['agentA']}/agentA/followup-parse",
                json={"text": "Schedule a call next Tuesday at 2 PM"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Schedule Parsing"] = f"✅ Title: {data.get('title', 'N/A')}"
            else:
                tests["Schedule Parsing"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Schedule Parsing"] = f"❌ Error: {str(e)}"
        
        return tests
    
    def test_agent_b_dealflow(self):
        """Test Agent B dealflow capabilities"""
        tests = {}
        
        # Test lead capture
        try:
            response = requests.post(
                f"{self.endpoints['agentB']}/agentB/newlead",
                json={"raw": "John Smith from Acme Corp wants a PoC, budget around 15k"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Lead Capture"] = f"✅ Name: {data.get('name')}, Company: {data.get('company')}"
            else:
                tests["Lead Capture"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Lead Capture"] = f"❌ Error: {str(e)}"
        
        # Test proposal generation
        try:
            lead_data = {
                "name": "John Smith",
                "company": "Acme Corp", 
                "intent": "PoC request",
                "budget": "15k"
            }
            
            response = requests.post(
                f"{self.endpoints['agentB']}/agentB/proposal-copy",
                json={"lead": lead_data},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Proposal Generation"] = f"✅ Title: {data.get('title', '')[:50]}..."
            else:
                tests["Proposal Generation"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Proposal Generation"] = f"❌ Error: {str(e)}"
        
        # Test next step parsing
        try:
            response = requests.post(
                f"{self.endpoints['agentB']}/agentB/nextstep-parse",
                json={"text": "Schedule demo next Wednesday at 11am"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Next Step Parsing"] = f"✅ Meeting: {data.get('title')}"
            else:
                tests["Next Step Parsing"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Next Step Parsing"] = f"❌ Error: {str(e)}"
        
        # Test status classification
        try:
            response = requests.post(
                f"{self.endpoints['agentB']}/agentB/status-classify",
                json={"label": "Lost", "reasonText": "budget constraints"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tests["Status Classification"] = f"✅ Status: {data.get('label')}, Category: {data.get('reason_category')}"
            else:
                tests["Status Classification"] = f"❌ HTTP {response.status_code}"
                
        except Exception as e:
            tests["Status Classification"] = f"❌ Error: {str(e)}"
        
        return tests
    
    def test_performance(self):
        """Test system performance under load"""
        results = {}
        
        # Measure response times for different operations
        operations = [
            ("Intent Classification", lambda: requests.post(
                f"{self.endpoints['classifier']}/classify",
                json={"message": "What's our refund policy?", "has_attachments": False}
            )),
            ("Knowledge Q&A", lambda: requests.post(
                f"{self.endpoints['agentA']}/agentA/ask",
                json={"userId": "perf_test", "text": "Test query"}
            )),
            ("Lead Parsing", lambda: requests.post(
                f"{self.endpoints['agentB']}/agentB/newlead",
                json={"raw": "Test lead from Test Company"}
            ))
        ]
        
        for op_name, op_func in operations:
            times = []
            for i in range(3):  # Run 3 times for average
                start = time.time()
                try:
                    response = op_func()
                    if response.status_code == 200:
                        times.append(time.time() - start)
                except:
                    pass
            
            if times:
                avg_time = sum(times) / len(times)
                results[op_name] = f"✅ Avg: {avg_time:.2f}s"
            else:
                results[op_name] = "❌ Failed all attempts"
        
        return results
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting WhatsApp Revenue Copilot Test Suite")
        print("=" * 60)
        
        # Run all test categories
        test_categories = [
            ("Health Checks", self.test_health_checks),
            ("Intent Classification", self.test_intent_classification), 
            ("Agent A - Knowledge", self.test_agent_a_knowledge),
            ("Agent B - Dealflow", self.test_agent_b_dealflow),
            ("Performance Tests", self.test_performance)
        ]
        
        for category_name, test_func in test_categories:
            self.run_test(category_name, test_func)
            print()
        
        # Generate summary report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed results
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.name} ({result.duration:.2f}s)")
            
            if result.passed and result.response:
                # Show successful test details
                if isinstance(result.response, dict):
                    for key, value in result.response.items():
                        print(f"    {key}: {value}")
            elif not result.passed:
                print(f"    Error: {result.error}")
            print()
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "error": r.error,
                    "response": r.response
                }
                for r in self.results
            ]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        sys.exit(0 if failed_tests == 0 else 1)


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp Revenue Copilot Test Suite")
    parser.add_argument("--base-url", default="http://localhost", 
                       help="Base URL for services (default: http://localhost)")
    parser.add_argument("--category", choices=["health", "intent", "agentA", "agentB", "performance", "all"],
                       default="all", help="Test category to run")
    
    args = parser.parse_args()
    
    tester = CopilotTester(base_url=args.base_url)
    
    if args.category == "all":
        tester.run_all_tests()
    elif args.category == "health":
        tester.run_test("Health Checks", tester.test_health_checks)
    elif args.category == "intent":
        tester.run_test("Intent Classification", tester.test_intent_classification)
    elif args.category == "agentA":
        tester.run_test("Agent A - Knowledge", tester.test_agent_a_knowledge)
    elif args.category == "agentB":
        tester.run_test("Agent B - Dealflow", tester.test_agent_b_dealflow)
    elif args.category == "performance":
        tester.run_test("Performance Tests", tester.test_performance)
    
    tester.generate_report()


if __name__ == "__main__":
    main()
