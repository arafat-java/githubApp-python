#!/usr/bin/env python3
"""
Example usage of the Multi-Agent Code Review System.
This script demonstrates how to use the specialized agents and consolidation features.
"""

from multi_agent_reviewer import MultiAgentCodeReviewer


def example_code_review():
    """Example of reviewing a code snippet with all agents."""
    
    # Sample code with various issues for demonstration
    sample_code = '''
import hashlib
import sqlite3

def login_user(username, password):
    # Security issue: SQL injection vulnerability
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    
    # Performance issue: creating new connection each time
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    
    # Security issue: storing plain text passwords
    if result:
        return True
    return False

def process_data(data_list):
    # Performance issue: inefficient loop
    result = []
    for i in range(len(data_list)):
        for j in range(len(data_list)):
            if data_list[i] == data_list[j] and i != j:
                result.append(data_list[i])
    return result

# Readability issue: unclear variable names
def calc(x, y, z):
    return x * y + z
    '''
    
    print("🚀 Multi-Agent Code Review Example")
    print("="*50)
    
    # Initialize the multi-agent reviewer
    reviewer = MultiAgentCodeReviewer()
    
    # Show available agents
    stats = reviewer.get_agent_statistics()
    print(f"Available agents: {len(stats['available_agent_types'])}")
    for agent in stats['available_agent_types']:
        print(f"  - {agent.replace('_', ' ').title()}")
    
    print("\n" + "="*50)
    print("Sample code to review:")
    print("="*50)
    print(sample_code[:300] + "..." if len(sample_code) > 300 else sample_code)
    
    print("\n" + "="*50)
    print("Starting multi-agent review...")
    print("="*50)
    
    # Perform the review
    consolidated_review = reviewer.review_code(sample_code, parallel=True)
    
    if consolidated_review:
        # Print detailed report
        reviewer.print_report(consolidated_review, "detailed")
        
        print("\n" + "="*50)
        print("Summary Report:")
        print("="*50)
        reviewer.print_report(consolidated_review, "summary")
    else:
        print("❌ Review failed. Please check your Ollama setup.")


def example_specific_agents():
    """Example of using only specific agents."""
    
    sample_code = '''
def unsafe_function(user_input):
    # This function has security issues
    import os
    command = "ls " + user_input
    os.system(command)  # Command injection vulnerability
    return "Command executed"
    '''
    
    print("\n" + "="*80)
    print("🔒 SECURITY-FOCUSED REVIEW EXAMPLE")
    print("="*80)
    
    # Initialize reviewer with only security agent
    reviewer = MultiAgentCodeReviewer(enabled_agents=['security'])
    
    consolidated_review = reviewer.review_code(sample_code)
    
    if consolidated_review:
        reviewer.print_report(consolidated_review, "summary")


def example_file_review():
    """Example of reviewing the current file."""
    
    print("\n" + "="*80)
    print("📁 FILE REVIEW EXAMPLE")
    print("="*80)
    
    # Review this example file itself
    reviewer = MultiAgentCodeReviewer(enabled_agents=['readability', 'coding_practices'])
    
    try:
        consolidated_review = reviewer.review_file(__file__)
        if consolidated_review:
            reviewer.print_report(consolidated_review, "summary")
    except Exception as e:
        print(f"File review example failed: {e}")


def example_json_output():
    """Example of getting JSON output."""
    
    simple_code = '''
def add_numbers(a, b):
    return a + b
    '''
    
    print("\n" + "="*80)
    print("📊 JSON OUTPUT EXAMPLE")
    print("="*80)
    
    reviewer = MultiAgentCodeReviewer(enabled_agents=['coding_practices'])
    consolidated_review = reviewer.review_code(simple_code)
    
    if consolidated_review:
        json_report = reviewer.generate_report(consolidated_review, "json")
        print("JSON Report (first 500 chars):")
        print(json_report[:500] + "..." if len(json_report) > 500 else json_report)


def example_performance_focused():
    """Example focusing on performance issues."""
    
    performance_code = '''
def inefficient_search(items, target):
    # O(n²) algorithm - very inefficient for large datasets
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == target and items[j] == target:
                return True
    return False

def memory_leak_example():
    # Potential memory issues
    big_list = []
    while True:
        big_list.append([0] * 1000000)  # Continuously growing list
        if len(big_list) > 100:
            break
    return big_list
    '''
    
    print("\n" + "="*80)
    print("⚡ PERFORMANCE-FOCUSED REVIEW EXAMPLE")
    print("="*80)
    
    reviewer = MultiAgentCodeReviewer(enabled_agents=['performance'])
    consolidated_review = reviewer.review_code(performance_code)
    
    if consolidated_review:
        reviewer.print_report(consolidated_review, "summary")


if __name__ == "__main__":
    try:
        # Run all examples
        example_code_review()
        example_specific_agents()
        example_file_review()
        example_json_output()
        example_performance_focused()
        
        print("\n" + "="*80)
        print("✅ All examples completed!")
        print("="*80)
        print("\nTo use the multi-agent reviewer in your own code:")
        print("```python")
        print("from multi_agent_reviewer import MultiAgentCodeReviewer")
        print("reviewer = MultiAgentCodeReviewer()")
        print("review = reviewer.review_code(your_code)")
        print("reviewer.print_report(review)")
        print("```")
        
    except KeyboardInterrupt:
        print("\n⏹ Examples interrupted by user.")
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        print("\nMake sure Ollama is running with a compatible model:")
        print("ollama serve")
        print("ollama pull llama3.2")
