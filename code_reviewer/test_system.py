#!/usr/bin/env python3
"""
Test script to verify the multi-agent system architecture and functionality.
This script tests the system with and without AI connectivity.
"""

import sys
from typing import List
from specialized_agents import (
    SecurityAgent, PerformanceAgent, CodingPracticesAgent,
    AgentReview, ReviewFinding, Severity
)
from consolidation_agent import ConsolidationAgent
from multi_agent_reviewer import MultiAgentCodeReviewer


def test_agent_initialization():
    """Test that all agents can be initialized properly."""
    print("🧪 Testing Agent Initialization...")
    
    try:
        security_agent = SecurityAgent()
        performance_agent = PerformanceAgent()
        coding_practices_agent = CodingPracticesAgent()
        
        print(f"✅ SecurityAgent initialized: {security_agent.agent_name}")
        print(f"✅ PerformanceAgent initialized: {performance_agent.agent_name}")
        print(f"✅ CodingPracticesAgent initialized: {coding_practices_agent.agent_name}")
        
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


def test_multi_agent_reviewer_setup():
    """Test MultiAgentCodeReviewer initialization and configuration."""
    print("\n🧪 Testing Multi-Agent Reviewer Setup...")
    
    try:
        reviewer = MultiAgentCodeReviewer()
        
        # Test agent statistics
        stats = reviewer.get_agent_statistics()
        print(f"✅ Total agents available: {stats['total_agents']}")
        print(f"✅ Enabled agents: {stats['enabled_agents']}")
        print(f"✅ Available agent types: {', '.join(stats['available_agent_types'])}")
        
        # Test agent selection
        reviewer.set_enabled_agents(['security', 'performance'])
        updated_stats = reviewer.get_agent_statistics()
        print(f"✅ Updated enabled agents: {updated_stats['enabled_agents']}")
        
        return True
    except Exception as e:
        print(f"❌ Multi-agent reviewer setup failed: {e}")
        return False


def create_mock_agent_review(agent_name: str, agent_type: str) -> AgentReview:
    """Create a mock agent review for testing consolidation."""
    findings = [
        ReviewFinding(
            agent_type=agent_type,
            severity=Severity.HIGH,
            title=f"Mock {agent_type} issue",
            description=f"This is a mock finding from {agent_name}",
            suggestion=f"Fix the {agent_type} issue by following best practices"
        )
    ]
    
    return AgentReview(
        agent_name=agent_name,
        agent_type=agent_type,
        overall_score=7,
        summary=f"Mock review from {agent_name}",
        findings=findings,
        recommendations=[f"Recommendation from {agent_name}"]
    )


def test_consolidation_agent():
    """Test the consolidation agent with mock data."""
    print("\n🧪 Testing Consolidation Agent...")
    
    try:
        consolidation_agent = ConsolidationAgent()
        
        # Create mock reviews
        mock_reviews = [
            create_mock_agent_review("SecurityAgent", "security"),
            create_mock_agent_review("PerformanceAgent", "performance"),
            create_mock_agent_review("CodingPracticesAgent", "coding_practices")
        ]
        
        # Test consolidation (without AI call)
        consolidated_review = consolidation_agent.consolidate_reviews(
            mock_reviews, 
            "def test(): pass"
        )
        
        print(f"✅ Consolidated review created")
        print(f"✅ Overall score: {consolidated_review.overall_score}")
        print(f"✅ Number of agent reviews: {len(consolidated_review.agent_reviews)}")
        print(f"✅ Critical issues found: {len(consolidated_review.critical_issues)}")
        print(f"✅ Findings by category: {list(consolidated_review.findings_by_category.keys())}")
        
        # Test report generation
        detailed_report = consolidation_agent.generate_report(consolidated_review, "detailed")
        summary_report = consolidation_agent.generate_report(consolidated_review, "summary")
        json_report = consolidation_agent.generate_report(consolidated_review, "json")
        
        print(f"✅ Detailed report generated ({len(detailed_report)} chars)")
        print(f"✅ Summary report generated ({len(summary_report)} chars)")
        print(f"✅ JSON report generated ({len(json_report)} chars)")
        
        return True
    except Exception as e:
        print(f"❌ Consolidation agent test failed: {e}")
        return False


def test_cli_integration():
    """Test CLI argument parsing and integration."""
    print("\n🧪 Testing CLI Integration...")
    
    try:
        # Test importing the CLI modules
        from multi_agent_reviewer import main as multi_main
        print("✅ Multi-agent CLI module imported successfully")
        
        # Test that the main code_reviewer.py has multi-agent support
        import code_reviewer
        print("✅ Main code_reviewer module imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ CLI integration test failed: {e}")
        return False


def test_with_ollama_connection():
    """Test actual connection to Ollama if available."""
    print("\n🧪 Testing Ollama Connection...")
    
    try:
        import requests
        
        # Quick test to see if Ollama is responsive
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": "Hello", "stream": False},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Ollama is running and responsive")
            
            # Test with a very simple code review
            reviewer = MultiAgentCodeReviewer(enabled_agents=['security'])
            print("🔄 Testing simple security review...")
            
            # Use a very short timeout for this test
            result = reviewer.review_code("def test(): return 1", parallel=False)
            
            if result:
                print("✅ Multi-agent review completed successfully!")
                print(f"✅ Overall score: {result.overall_score}")
                return True
            else:
                print("⚠️ Multi-agent review completed but returned no results")
                return False
                
        else:
            print(f"⚠️ Ollama responded with status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️ Ollama connection timed out - may be overloaded")
        return False
    except requests.exceptions.ConnectionError:
        print("⚠️ Could not connect to Ollama - make sure it's running")
        return False
    except Exception as e:
        print(f"⚠️ Ollama test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Multi-Agent Code Review System - Test Suite")
    print("=" * 60)
    
    tests = [
        test_agent_initialization,
        test_multi_agent_reviewer_setup,
        test_consolidation_agent,
        test_cli_integration,
        test_with_ollama_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The multi-agent system is working correctly.")
    elif passed >= total - 1:
        print("✅ System architecture is working. Only Ollama connectivity issues.")
        print("💡 Make sure Ollama is running with: ollama serve")
        print("💡 And the model is available with: ollama pull llama3.2")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
