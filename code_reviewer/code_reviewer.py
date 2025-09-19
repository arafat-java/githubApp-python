#!/usr/bin/env python3
"""
Code Review Bot - A Python application that provides code reviews using a local AI model.
"""

import requests
import json
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path


class CodeReviewer:
    def __init__(self, model_url: str = "http://localhost:11434/api/generate", model_name: str = "llama3.2"):
        """
        Initialize the Code Reviewer.
        
        Args:
            model_url: URL of the local AI model API
            model_name: Name of the model to use
        """
        self.model_url = model_url
        self.model_name = model_name
        
    def _make_api_request(self, prompt: str, stream: bool = True) -> Optional[str]:
        """
        Make a request to the local AI model with streaming support.
        
        Args:
            prompt: The prompt to send to the AI model
            stream: Whether to use streaming output
            
        Returns:
            The AI model's response or None if request failed
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream
        }
        
        try:
            if stream:
                return self._handle_streaming_response(payload)
            else:
                response = requests.post(self.model_url, json=payload, timeout=180)
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to AI model: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing AI model response: {e}")
            return None
    
    def _handle_streaming_response(self, payload: dict) -> Optional[str]:
        """
        Handle streaming response from Ollama.
        
        Args:
            payload: The request payload
            
        Returns:
            Complete response text or None if failed
        """
        try:
            print("🔄 Connecting to Ollama for streaming response...")
            response = requests.post(
                self.model_url, 
                json=payload, 
                timeout=180,
                stream=True
            )
            response.raise_for_status()
            
            print("\n" + "="*80)
            print("📋 CODE REVIEW RESULTS (Streaming)")
            print("="*80)
            
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk:
                            chunk_text = chunk['response']
                            print(chunk_text, end='', flush=True)
                            full_response += chunk_text
                        
                        # Check if this is the final chunk
                        if chunk.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            print("\n" + "="*80)
            print("✅ Review completed!")
            
            return full_response.strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Error during streaming request: {e}")
            return None
    
    def review_code(self, code: str, review_type: str = "general", stream: bool = True, minimal: bool = False) -> Optional[str]:
        """
        Review the provided code using the AI model.
        
        Args:
            code: The code to review
            review_type: Type of review to perform
            stream: Whether to use streaming output
            minimal: Whether to provide minimal, concise output
            
        Returns:
            The code review or None if request failed
        """
        if minimal:
            prompts = {
                "general": f"""Code review - be concise and actionable:

Code:
```
{code}
```

Provide only:
- 3 most critical issues
- Quick fixes (1-2 lines each)
- No explanations, just solutions""",

                "security": f"""Security review - be brief:

Code:
```
{code}
```

List only:
- Critical vulnerabilities found
- One-line fix for each
- Risk level (High/Medium/Low)""",

                "performance": f"""Performance review - quick summary:

Code:
```
{code}
```

Provide:
- 2-3 main bottlenecks
- Simple optimization fixes
- Expected impact""",

                "modern": f"""Modernization - essential changes:

Code:
```
{code}
```

Show:
- Replace old syntax with modern equivalent
- Most important upgrades only
- Before/after code snippets (brief)"""
            }
        else:
            prompts = {
                "general": f"""Please provide a comprehensive code review for the following code. Include:
1. Code quality issues
2. Potential bugs or security vulnerabilities
3. Performance improvements
4. Best practices recommendations
5. Refactoring suggestions

Code to review:
```
{code}
```

Please provide detailed feedback with explanations and examples where applicable.""",
            
            "security": f"""Please perform a security-focused code review for the following code. Look for:
1. Security vulnerabilities (XSS, SQL injection, etc.)
2. Input validation issues
3. Authentication/authorization problems
4. Data exposure risks
5. Secure coding practices

Code to review:
```
{code}
```

Provide specific security recommendations and fixes.""",
            
            "performance": f"""Please perform a performance-focused code review for the following code. Analyze:
1. Time complexity issues
2. Memory usage optimization
3. Algorithm efficiency
4. Resource management
5. Scalability concerns

Code to review:
```
{code}
```

Suggest specific performance improvements with examples.""",
            
            "modern": f"""Please suggest modern improvements for the following code. Focus on:
1. Modern language features and syntax
2. Best practices and conventions
3. Code readability and maintainability
4. Updated patterns and approaches
5. Framework/library recommendations

Code to review:
```
{code}
```

Provide modernized code examples and explanations."""
            }
        
        prompt = prompts.get(review_type, prompts["general"])
        return self._make_api_request(prompt, stream)
    
    def review_file(self, file_path: str, review_type: str = "general", stream: bool = True, minimal: bool = False) -> Optional[str]:
        """
        Review code from a file.
        
        Args:
            file_path: Path to the file to review
            review_type: Type of review to perform
            stream: Whether to use streaming output
            minimal: Whether to provide minimal, concise output
            
        Returns:
            The code review or None if file reading or request failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
            
            print(f"Reviewing file: {file_path}")
            return self.review_code(code, review_type, stream, minimal)
            
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return None
        except IOError as e:
            print(f"Error reading file '{file_path}': {e}")
            return None
    
    def review_diff(self, diff_content: str, stream: bool = True, minimal: bool = False) -> Optional[str]:
        """
        Review a git diff or code changes.
        
        Args:
            diff_content: The diff content to review
            stream: Whether to use streaming output
            minimal: Whether to provide minimal, concise output
            
        Returns:
            The code review or None if request failed
        """
        if minimal:
            prompt = f"""Diff review - brief summary:

Diff:
```
{diff_content}
```

Provide only:
- Main issues found
- Critical fixes needed
- Approval status (Approve/Request Changes)"""
        else:
            prompt = f"""Please review the following code changes/diff. Focus on:
1. Quality of the changes
2. Potential issues introduced
3. Best practices compliance
4. Impact on existing code
5. Suggestions for improvement

Diff to review:
```
{diff_content}
```

Provide specific feedback on the changes."""

        return self._make_api_request(prompt, stream)


def main():
    """Main function for CLI usage with streaming support."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Review Bot using local AI model with streaming")
    parser.add_argument("--file", "-f", help="Path to file to review")
    parser.add_argument("--code", "-c", help="Code string to review")
    parser.add_argument("--diff", "-d", help="Diff content to review")
    parser.add_argument("--type", "-t", choices=["general", "security", "performance", "modern"], 
                       default="general", help="Type of review to perform")
    parser.add_argument("--model-url", default="http://localhost:11434/api/generate", 
                       help="URL of the local AI model API")
    parser.add_argument("--model-name", default="llama3.2", help="Name of the AI model")
    parser.add_argument("--no-stream", action="store_true", 
                       help="Disable streaming output (get complete response at once)")
    parser.add_argument("--minimal", "-m", action="store_true", 
                       help="Provide minimal, concise output with only essential feedback")
    parser.add_argument("--multi-agent", action="store_true",
                       help="Use multi-agent review system for comprehensive analysis")
    parser.add_argument("--agents", nargs='+', 
                       choices=['security', 'performance', 'coding_practices', 
                               'architecture', 'readability', 'testability'],
                       help="Specific agents to use with --multi-agent (default: all agents)")
    parser.add_argument("--format", choices=["detailed", "summary", "json"], 
                       default="detailed", help="Report format for multi-agent reviews")
    
    args = parser.parse_args()
    
    if not any([args.file, args.code, args.diff]):
        print("Error: Please provide either --file, --code, or --diff")
        sys.exit(1)
    
    # Check if multi-agent mode is requested
    if args.multi_agent:
        # Import multi-agent system
        try:
            from multi_agent_reviewer import MultiAgentCodeReviewer
        except ImportError:
            print("❌ Multi-agent system not available. Please ensure all required files are present.")
            sys.exit(1)
        
        # Initialize multi-agent reviewer
        multi_reviewer = MultiAgentCodeReviewer(
            model_url=args.model_url,
            model_name=args.model_name,
            enabled_agents=args.agents
        )
        
        try:
            print("🚀 Starting multi-agent code review...")
            
            # Show agent configuration
            stats = multi_reviewer.get_agent_statistics()
            print(f"Running {stats['enabled_agents']}/{stats['total_agents']} specialized agents")
            
            # Perform multi-agent review
            if args.file:
                consolidated_review = multi_reviewer.review_file(args.file, parallel=True, report_format=args.format)
            elif args.code:
                consolidated_review = multi_reviewer.review_code(args.code, parallel=True, report_format=args.format)
            elif args.diff:
                consolidated_review = multi_reviewer.review_diff(args.diff, parallel=True, report_format=args.format)
            
            if consolidated_review:
                print("\n" + "="*80)
                print("📋 MULTI-AGENT CODE REVIEW RESULTS")
                print("="*80)
                multi_reviewer.print_report(consolidated_review, args.format)
            else:
                print("❌ Multi-agent review failed. Please check your AI model connection.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n⏹ Multi-agent review cancelled by user.")
            sys.exit(0)
    
    else:
        # Use original single-agent reviewer
        reviewer = CodeReviewer(args.model_url, args.model_name)
        use_streaming = not args.no_stream
        use_minimal = args.minimal
        
        try:
            print(f"🚀 Starting {args.type} code review...")
            if use_minimal:
                print("⚡ Using minimal mode for concise output")
            if use_streaming:
                print("💫 Using streaming mode for real-time output")
            else:
                print("⏳ Using non-streaming mode")
            
            if args.file:
                result = reviewer.review_file(args.file, args.type, stream=use_streaming, minimal=use_minimal)
            elif args.code:
                result = reviewer.review_code(args.code, args.type, stream=use_streaming, minimal=use_minimal)
            elif args.diff:
                result = reviewer.review_diff(args.diff, stream=use_streaming, minimal=use_minimal)
            
            if result:
                if not use_streaming:
                    # Only print results if not streaming (streaming already prints)
                    print("\n" + "="*80)
                    print("📋 CODE REVIEW RESULTS")
                    print("="*80)
                    print(result)
                    print("="*80)
                    print("✅ Review completed!")
            else:
                print("❌ Failed to get code review. Please check your AI model connection.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n⏹ Review cancelled by user.")
            sys.exit(0)


if __name__ == "__main__":
    main()
