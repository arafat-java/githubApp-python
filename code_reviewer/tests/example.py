#!/usr/bin/env python3
"""
Example usage of the Code Reviewer Bot
"""

from code_reviewer import CodeReviewer

def main():
    # Initialize the code reviewer
    reviewer = CodeReviewer()
    
    # Example 1: Review the JavaScript code from your curl example
    js_code = """
var data = [];
for(var i=0; i<items.length; i++) {
    if(items[i].active == true) {
        data.push(items[i]);
    }
}
"""
    
    print("Example 1: Modern JavaScript Review")
    print("="*50)
    review = reviewer.review_code(js_code, review_type="modern")
    if review:
        print(review)
    else:
        print("Failed to get review. Check your AI model connection.")
    
    print("\n" + "="*80 + "\n")
    
    # Example 2: Security review of potentially vulnerable code
    vulnerable_code = """
import sqlite3
import sys

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Vulnerable SQL query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result

def main():
    if len(sys.argv) > 1:
        username = sys.argv[1]
        user = get_user(username)
        print(f"User data: {user}")

if __name__ == "__main__":
    main()
"""
    
    print("Example 2: Security Review")
    print("="*50)
    review = reviewer.review_code(vulnerable_code, review_type="security")
    if review:
        print(review)
    else:
        print("Failed to get review. Check your AI model connection.")

if __name__ == "__main__":
    main()
