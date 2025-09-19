#!/usr/bin/env python3
"""
PR Review Formatter - Converts multi-agent code review results into GitHub/GitLab style PR comments
"""

import json
import re
from typing import Dict, List, Any, Tuple

class PRReviewFormatter:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_lines = []
        self.load_file_content()
        
    def load_file_content(self):
        """Load the file content to map issues to specific lines."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.file_lines = f.readlines()
        except Exception as e:
            print(f"Warning: Could not load file {self.file_path}: {e}")
            self.file_lines = []
    
    def find_line_number(self, code_snippet: str, function_name: str = None) -> int:
        """Find the line number for a specific code snippet or function."""
        if not self.file_lines:
            return 0
            
        # Try to find exact code match first
        for i, line in enumerate(self.file_lines, 1):
            if code_snippet.strip() in line.strip():
                return i
                
        # Try to find function name
        if function_name:
            for i, line in enumerate(self.file_lines, 1):
                if f"function {function_name}" in line or f"{function_name} =" in line:
                    return i
                    
        # Try pattern matching for common issues
        patterns = {
            "sql injection": r"SELECT.*FROM.*WHERE.*\+",
            "loose equality": r"==(?!=)",
            "var declaration": r"^\s*var\s+",
            "for loop": r"for\s*\(\s*var\s+\w+\s*=",
            "dom manipulation": r"innerHTML|outerHTML",
            "synchronous": r"\.execute\(|\.sync\(",
        }
        
        snippet_lower = code_snippet.lower()
        for pattern_name, pattern in patterns.items():
            if pattern_name in snippet_lower:
                for i, line in enumerate(self.file_lines, 1):
                    if re.search(pattern, line):
                        return i
        
        return 0
    
    def extract_issues_from_summary(self, summary: str, agent_type: str) -> List[Dict]:
        """Extract specific issues from agent summary text."""
        issues = []
        
        # Define patterns for different types of issues
        issue_patterns = {
            'security': [
                (r"SQL Injection.*?`([^`]+)`", "🔐 **SQL Injection Vulnerability**", "critical"),
                (r"XSS.*?`([^`]+)`", "🔐 **Cross-Site Scripting (XSS)**", "high"),
                (r"input validation.*?`([^`]+)`", "🔐 **Missing Input Validation**", "high"),
                (r"hardcoded.*?`([^`]+)`", "🔐 **Hardcoded Credentials**", "critical"),
            ],
            'performance': [
                (r"synchronous.*?`([^`]+)`", "⚡ **Synchronous Operation**", "medium"),
                (r"inefficient.*?loop.*?`([^`]+)`", "⚡ **Inefficient Loop**", "medium"),
                (r"memory leak.*?`([^`]+)`", "⚡ **Memory Leak**", "high"),
                (r"O\(n²\).*?`([^`]+)`", "⚡ **Quadratic Time Complexity**", "medium"),
            ],
            'coding_practices': [
                (r"loose equality.*?`([^`]+)`", "📋 **Use Strict Equality**", "low"),
                (r"var.*?instead.*?`([^`]+)`", "📋 **Use Modern Variable Declaration**", "low"),
                (r"magic number.*?`([^`]+)`", "📋 **Magic Number**", "low"),
                (r"global variable.*?`([^`]+)`", "📋 **Global Variable**", "medium"),
            ],
            'readability': [
                (r"cryptic.*?name.*?`([^`]+)`", "📖 **Unclear Variable Name**", "low"),
                (r"missing.*?comment.*?`([^`]+)`", "📖 **Missing Documentation**", "low"),
                (r"inconsistent.*?format.*?`([^`]+)`", "📖 **Inconsistent Formatting**", "low"),
            ],
            'architecture': [
                (r"mixed concerns.*?`([^`]+)`", "🏗️ **Mixed Concerns**", "medium"),
                (r"tight coupling.*?`([^`]+)`", "🏗️ **Tight Coupling**", "medium"),
                (r"no error handling.*?`([^`]+)`", "🏗️ **Missing Error Handling**", "high"),
            ],
            'testability': [
                (r"hard to test.*?`([^`]+)`", "🧪 **Hard to Test**", "medium"),
                (r"dependency injection.*?`([^`]+)`", "🧪 **Missing Dependency Injection**", "medium"),
                (r"no unit test.*?`([^`]+)`", "🧪 **Missing Unit Tests**", "low"),
            ]
        }
        
        if agent_type in issue_patterns:
            for pattern, title, severity in issue_patterns[agent_type]:
                matches = re.finditer(pattern, summary, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    code_snippet = match.group(1) if match.groups() else ""
                    issues.append({
                        'title': title,
                        'code': code_snippet,
                        'severity': severity,
                        'description': self._extract_description_around_match(summary, match)
                    })
        
        # Fallback: extract issues from common patterns
        if not issues:
            issues = self._extract_fallback_issues(summary, agent_type)
            
        return issues
    
    def _extract_description_around_match(self, text: str, match) -> str:
        """Extract description around a regex match."""
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 200)
        context = text[start:end].strip()
        
        # Clean up the context
        lines = context.split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        return ' '.join(clean_lines[:3])  # First 3 meaningful lines
    
    def _extract_fallback_issues(self, summary: str, agent_type: str) -> List[Dict]:
        """Fallback method to extract issues when patterns don't match."""
        issues = []
        
        # Common function names and issues
        function_issues = {
            'getUserData': {
                'title': '🔐 **SQL Injection Risk**',
                'severity': 'critical',
                'description': 'Function constructs SQL query using string concatenation, vulnerable to SQL injection attacks.'
            },
            'processUsers': {
                'title': '📋 **Use Modern Array Methods**', 
                'severity': 'low',
                'description': 'Consider using modern array methods like filter(), map(), or forEach() instead of traditional for loops.'
            },
            'calculateTotal': {
                'title': '🏗️ **Missing Error Handling**',
                'severity': 'medium', 
                'description': 'Function lacks error handling for edge cases and invalid inputs.'
            },
            'updateUserList': {
                'title': '⚡ **DOM Manipulation Optimization**',
                'severity': 'medium',
                'description': 'Consider batching DOM updates or using document fragments for better performance.'
            }
        }
        
        for func_name, issue_info in function_issues.items():
            if func_name.lower() in summary.lower():
                issues.append({
                    'title': issue_info['title'],
                    'code': func_name,
                    'severity': issue_info['severity'],
                    'description': issue_info['description']
                })
        
        return issues
    
    def format_pr_review(self, review_data: Dict) -> str:
        """Format the review data as PR comments."""
        if isinstance(review_data, str):
            try:
                review_data = json.loads(review_data)
            except:
                return "Error: Invalid review data format"
        
        output = []
        output.append("# 🤖 Multi-Agent Code Review")
        output.append("")
        output.append(f"**File:** `{self.file_path.split('/')[-1]}`")
        output.append(f"**Overall Score:** {review_data.get('overall_score', 'N/A')}/10")
        output.append("")
        
        # Group issues by severity
        critical_issues = []
        high_issues = []
        medium_issues = []
        low_issues = []
        
        # Process each agent's review
        for agent_review in review_data.get('agent_reviews', []):
            agent_name = agent_review.get('agent_name', 'Unknown')
            agent_type = agent_review.get('agent_type', '').lower()
            summary = agent_review.get('summary', '')
            
            # Extract issues from the agent's summary
            issues = self.extract_issues_from_summary(summary, agent_type)
            
            for issue in issues:
                line_num = self.find_line_number(issue['code'], issue['code'])
                
                comment = {
                    'agent': agent_name,
                    'title': issue['title'],
                    'description': issue['description'],
                    'line': line_num,
                    'code': issue['code'],
                    'severity': issue['severity']
                }
                
                # Group by severity
                if issue['severity'] == 'critical':
                    critical_issues.append(comment)
                elif issue['severity'] == 'high':
                    high_issues.append(comment)
                elif issue['severity'] == 'medium':
                    medium_issues.append(comment)
                else:
                    low_issues.append(comment)
        
        # Format issues by severity
        all_issues = [
            ("🚨 Critical Issues", critical_issues),
            ("⚠️ High Priority Issues", high_issues), 
            ("📝 Medium Priority Issues", medium_issues),
            ("💡 Low Priority Issues", low_issues)
        ]
        
        for section_title, issues in all_issues:
            if issues:
                output.append(f"## {section_title}")
                output.append("")
                
                for i, issue in enumerate(issues, 1):
                    line_info = f" (Line {issue['line']})" if issue['line'] > 0 else ""
                    output.append(f"### {i}. {issue['title']}{line_info}")
                    output.append(f"**Agent:** {issue['agent']}")
                    output.append("")
                    
                    if issue['line'] > 0 and issue['line'] <= len(self.file_lines):
                        # Show the problematic code
                        start_line = max(1, issue['line'] - 2)
                        end_line = min(len(self.file_lines), issue['line'] + 2)
                        
                        output.append("**Code:**")
                        output.append("```javascript")
                        for line_num in range(start_line, end_line + 1):
                            prefix = "➤ " if line_num == issue['line'] else "  "
                            line_content = self.file_lines[line_num - 1].rstrip()
                            output.append(f"{prefix}{line_num:2d}: {line_content}")
                        output.append("```")
                        output.append("")
                    
                    output.append(f"**Issue:** {issue['description']}")
                    output.append("")
                    
                    # Add specific recommendations
                    recommendations = self._get_recommendations(issue['title'], issue['code'])
                    if recommendations:
                        output.append("**Recommended Fix:**")
                        output.append(recommendations)
                        output.append("")
                    
                    output.append("---")
                    output.append("")
        
        # Summary statistics
        total_issues = len(critical_issues) + len(high_issues) + len(medium_issues) + len(low_issues)
        if total_issues > 0:
            output.append("## 📊 Review Summary")
            output.append("")
            output.append(f"- **Total Issues Found:** {total_issues}")
            output.append(f"- **Critical:** {len(critical_issues)}")
            output.append(f"- **High Priority:** {len(high_issues)}")
            output.append(f"- **Medium Priority:** {len(medium_issues)}")
            output.append(f"- **Low Priority:** {len(low_issues)}")
            output.append("")
            
            if critical_issues or high_issues:
                output.append("⚠️ **Action Required:** Please address critical and high priority issues before merging.")
            else:
                output.append("✅ **Good to merge** after addressing medium/low priority improvements.")
        
        return "\n".join(output)
    
    def _get_recommendations(self, issue_title: str, code: str) -> str:
        """Get specific recommendations based on the issue type."""
        recommendations = {
            "SQL Injection": """
```javascript
// Instead of:
var query = "SELECT * FROM users WHERE id = '" + userId + "'";

// Use parameterized queries:
var query = "SELECT * FROM users WHERE id = ?";
var result = database.execute(query, [userId]);
```""",
            "Strict Equality": """
```javascript
// Instead of: if (value == null)
// Use: if (value === null)

// Instead of: if (count == 0) 
// Use: if (count === 0)
```""",
            "Modern Variable": """
```javascript
// Instead of: var users = [];
// Use: const users = []; or let users = [];

// Prefer const for values that don't change
// Use let for values that will be reassigned
```""",
            "Modern Array": """
```javascript
// Instead of traditional for loop:
for (var i = 0; i < users.length; i++) {
    if (users[i].active) data.push(users[i]);
}

// Use modern array methods:
const data = users.filter(user => user.active);
```""",
            "Error Handling": """
```javascript
function calculateTotal(items) {
    try {
        if (!Array.isArray(items)) {
            throw new Error('Items must be an array');
        }
        return items.reduce((sum, item) => sum + (item.price || 0), 0);
    } catch (error) {
        console.error('Error calculating total:', error);
        return 0;
    }
}
```"""
        }
        
        for key, recommendation in recommendations.items():
            if key.lower() in issue_title.lower():
                return recommendation
                
        return "Consider following best practices for this type of issue."


def main():
    """Main function for command line usage."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Format multi-agent code review as PR comments')
    parser.add_argument('--file', required=True, help='Source file that was reviewed')
    parser.add_argument('--review-json', required=True, help='JSON file containing review results')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Load review data
    try:
        with open(args.review_json, 'r') as f:
            review_data = json.load(f)
    except Exception as e:
        print(f"Error loading review data: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Format as PR review
    formatter = PRReviewFormatter(args.file)
    pr_review = formatter.format_pr_review(review_data)
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(pr_review)
        print(f"PR review written to {args.output}")
    else:
        print(pr_review)


if __name__ == "__main__":
    main()
