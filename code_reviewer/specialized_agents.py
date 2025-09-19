#!/usr/bin/env python3
"""
Specialized Code Review Agents - Individual agents focused on specific aspects of code review.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from .llm_manager import SandboxInstances
from .util.llm import AzureClient, OllamaClient

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Severity levels for review findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ReviewFinding:
    """Represents a single finding from a code review agent."""
    agent_type: str
    severity: Severity
    title: str
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    category: Optional[str] = None


@dataclass
class AgentReview:
    """Represents the complete review from a single agent."""
    agent_name: str
    agent_type: str
    overall_score: int  # 1-10 scale
    summary: str
    findings: List[ReviewFinding]
    recommendations: List[str]


class BaseReviewAgent(ABC):
    """Base class for all specialized review agents."""
    
    def __init__(self, is_local: bool = False, creativity_level: float = 0.1):
        """
        Initialize the review agent.
        
        Args:
            is_local: Whether to use local Ollama (True) or Azure OpenAI (False)
            creativity_level: Temperature for AI responses (0.0-1.0)
        """
        self.is_local = is_local
        self.creativity_level = creativity_level
        self.agent_name = self.__class__.__name__
        self.agent_type = self.get_agent_type()
        
        # Get LLM instance through the sandbox manager
        self.llm_client = SandboxInstances.get_instance(
            name=f"{self.agent_type}_agent",
            is_local=is_local,
            creativity_level=creativity_level
        )
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """Return the type of this agent."""
        pass
    
    @abstractmethod
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        """Generate the specialized prompt for this agent."""
        pass
    
    def _make_api_request(self, prompt: str) -> Optional[str]:
        """Make a request to the AI model through the LLM client."""
        try:
            # Prepare messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": f"You are a {self.agent_type} expert conducting a thorough code review. CRITICAL REQUIREMENTS: 1) ALWAYS scan the ENTIRE code thoroughly for ALL potential issues, 2) NEVER miss obvious problems, 3) ALWAYS provide specific line numbers for each issue you identify, 4) Format your response to clearly indicate the line number for each finding (e.g., 'Line 15: Issue description'), 5) Be comprehensive and consistent in your analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Make request through the LLM client
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=max(0.2, self.creativity_level)  # Minimum 0.2 for consistency
            )
            
            if response:
                logger.debug(f"{self.agent_name} completed successfully")
                return response
            else:
                logger.error(f"{self.agent_name} returned empty response")
                return None
                
        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {e}")
            return None
    
    def review_code(self, code: str, diff_only: bool = False) -> Optional[AgentReview]:
        """Perform specialized review of the code."""
        prompt = self.get_specialized_prompt(code, diff_only)
        response = self._make_api_request(prompt)
        
        if not response:
            return None
        
        return self._parse_response(response, code)
    
    def _parse_response(self, response: str, code: str) -> AgentReview:
        """Parse the AI response into structured review data."""
        # This is a simplified parser - in production, you might want more sophisticated parsing
        findings = []
        recommendations = []
        
        # Extract findings and recommendations from response
        # This is a basic implementation - you can enhance this based on your needs
        lines = response.split('\n')
        current_finding = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for common patterns in AI responses
            if any(keyword in line.lower() for keyword in ['critical', 'severe', 'vulnerability']):
                severity = Severity.CRITICAL
            elif any(keyword in line.lower() for keyword in ['high', 'important', 'major']):
                severity = Severity.HIGH
            elif any(keyword in line.lower() for keyword in ['medium', 'moderate']):
                severity = Severity.MEDIUM
            elif any(keyword in line.lower() for keyword in ['low', 'minor']):
                severity = Severity.LOW
            else:
                severity = Severity.INFO
            
            # Simple heuristic to identify findings
            if any(indicator in line.lower() for indicator in ['issue:', 'problem:', 'vulnerability:', 'warning:']):
                finding = ReviewFinding(
                    agent_type=self.agent_type,
                    severity=severity,
                    title=line,
                    description=line,
                    category=self.agent_type
                )
                findings.append(finding)
            
            # Look for recommendations
            if any(indicator in line.lower() for indicator in ['recommend:', 'suggest:', 'should:', 'fix:']):
                recommendations.append(line)
        
        # Calculate overall score based on findings
        score = 10
        for finding in findings:
            if finding.severity == Severity.CRITICAL:
                score -= 3
            elif finding.severity == Severity.HIGH:
                score -= 2
            elif finding.severity == Severity.MEDIUM:
                score -= 1
        
        score = max(1, score)  # Minimum score of 1
        
        return AgentReview(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            overall_score=score,
            summary=response[:200] + "..." if len(response) > 200 else response,
            findings=findings,
            recommendations=recommendations
        )


class SecurityAgent(BaseReviewAgent):
    """Agent specialized in security code review."""
    
    def get_agent_type(self) -> str:
        return "security"
    
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        if diff_only:
            return f"""You are a cybersecurity expert conducting a security code review.

CRITICAL RESTRICTION: You are reviewing a DIFF with context. You MUST ONLY comment on the lines that are being ADDED or CHANGED in the diff (lines starting with '+' or modified lines). DO NOT comment on context lines or unchanged code.

The content below contains:
1. DIFF TO REVIEW: The actual changes you should analyze
2. FULL FILE CONTEXT: Additional context to understand the changes (DO NOT REVIEW THESE LINES)

{code}

INSTRUCTIONS:
- ONLY review the lines that are being added/changed in the DIFF section
- Use the FULL FILE CONTEXT only to understand the broader context
- For each security issue found in the DIFF changes, provide:
  * Exact line number from the diff
  * Vulnerability type and impact level (Critical/High/Medium/Low)
  * Specific remediation steps
  * Start with "Line X:" format

Focus on security aspects in the CHANGED LINES ONLY:
- Input validation, authentication, data protection
- Injection attacks (SQL, XSS, command injection)
- Error handling, cryptography, session management
- OWASP Top 10 vulnerabilities

Example: "Line 15: SQL Injection vulnerability - user input concatenated into query..."

Be concise and actionable. IGNORE unchanged context lines."""
        else:
            # Add line numbers to the code for full file review
            lines = code.split('\n')
            numbered_code = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
            
            return f"""You are a cybersecurity expert conducting a thorough security code review. 

Analyze this code for security vulnerabilities and provide specific, actionable feedback with EXACT LINE NUMBERS:

```
{numbered_code}
```

CRITICAL: For each security issue found, you MUST:
- Start with "Line X:" where X is the specific line number
- Clearly state the vulnerability type
- Explain the potential impact and risk level (Critical/High/Medium/Low)
- Provide specific remediation steps

Focus on these security aspects:
1. **Input Validation**: Check for proper sanitization and validation of user inputs
2. **Authentication & Authorization**: Verify access controls and permission checks
3. **Data Protection**: Look for sensitive data exposure, encryption issues
4. **Injection Attacks**: SQL injection, XSS, command injection vulnerabilities
5. **Error Handling**: Information disclosure through error messages
6. **Cryptography**: Weak encryption, insecure random number generation
7. **Session Management**: Session fixation, hijacking vulnerabilities
8. **OWASP Top 10**: Check against common web application security risks

Example format: "Line 15: SQL Injection vulnerability - user input is directly concatenated into query string..."

Be thorough but concise. Focus on actionable security improvements with specific line references."""


class PerformanceAgent(BaseReviewAgent):
    """Agent specialized in performance optimization review."""
    
    def get_agent_type(self) -> str:
        return "performance"
    
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        if diff_only:
            return f"""You are a performance optimization expert reviewing code changes.

CRITICAL RESTRICTION: You are reviewing a DIFF with context. You MUST ONLY comment on the lines that are being ADDED or CHANGED in the diff (lines starting with '+' or modified lines). DO NOT comment on context lines or unchanged code.

The content below contains:
1. DIFF TO REVIEW: The actual changes you should analyze
2. FULL FILE CONTEXT: Additional context to understand the changes (DO NOT REVIEW THESE LINES)

{code}

INSTRUCTIONS:
- ONLY review the lines that are being added/changed in the DIFF section
- Use the FULL FILE CONTEXT only to understand the broader context
- For each performance issue found in the DIFF changes, provide:
  * Exact line number from the diff
  * Performance bottleneck identification
  * Impact on application performance (High/Medium/Low)
  * Specific optimization suggestions
  * Start with "Line X:" format

Focus on performance aspects in the CHANGED LINES ONLY:
- Algorithm complexity, data structures, memory management
- Database operations, caching, I/O operations
- Concurrency, resource usage, scalability

Example: "Line 25: Inefficient loop - O(n²) complexity due to nested iteration..."

Be specific about measurable performance gains. IGNORE unchanged context lines."""
        else:
            # Add line numbers to the code for full file review
            lines = code.split('\n')
            numbered_code = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
            
            return f"""You are a performance optimization expert reviewing code for efficiency and scalability.

Analyze this code for performance issues and optimization opportunities with EXACT LINE NUMBERS:

```
{numbered_code}
```

CRITICAL: For each performance issue found, you MUST:
- Start with "Line X:" where X is the specific line number
- Identify the bottleneck or inefficiency
- Explain the performance impact (High/Medium/Low)
- Provide specific optimization suggestions

Focus on these performance aspects:
1. **Algorithm Complexity**: Time and space complexity analysis
2. **Data Structures**: Optimal data structure usage
3. **Memory Management**: Memory leaks, unnecessary allocations
4. **Database Operations**: Query optimization, N+1 problems, indexing
5. **Caching**: Missing caching opportunities, cache invalidation
6. **I/O Operations**: File handling, network calls optimization
7. **Concurrency**: Threading issues, async/await usage
8. **Resource Usage**: CPU-intensive operations, blocking calls
9. **Scalability**: Code that won't scale with increased load

Example format: "Line 25: Inefficient loop - O(n²) complexity due to nested iteration..."

Be specific about measurable performance gains with exact line references."""


class CodingPracticesAgent(BaseReviewAgent):
    """Agent specialized in coding standards and best practices."""
    
    def get_agent_type(self) -> str:
        return "coding_practices"
    
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        if diff_only:
            return f"""You are a senior software engineer expert in coding standards and best practices.

CRITICAL RESTRICTION: You are reviewing a DIFF with context. You MUST ONLY comment on the lines that are being ADDED or CHANGED in the diff (lines starting with '+' or modified lines). DO NOT comment on context lines or unchanged code.

The content below contains:
1. DIFF TO REVIEW: The actual changes you should analyze
2. FULL FILE CONTEXT: Additional context to understand the changes (DO NOT REVIEW THESE LINES)

{code}

INSTRUCTIONS:
- ONLY review the lines that are being added/changed in the DIFF section
- Use the FULL FILE CONTEXT only to understand the broader context
- For each best practice issue found in the DIFF changes, provide:
  * Exact line number from the diff
  * Specific practice violation
  * Why it matters for code quality
  * Refactoring suggestions
  * Start with "Line X:" format

Focus on coding practice aspects in the CHANGED LINES ONLY:
- Code structure, naming conventions, function design
- Error handling, documentation, code duplication
- SOLID principles, design patterns, testability, maintainability

Example: "Line 42: Use 'const' instead of 'var' for variables that don't change..."

Focus on practical improvements that enhance code quality. IGNORE unchanged context lines."""
        else:
            # Add line numbers to the code for full file review
            lines = code.split('\n')
            numbered_code = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
            
            return f"""You are a senior software engineer expert in coding standards and best practices.

Review this code for adherence to best practices and clean code principles with EXACT LINE NUMBERS:

```
{numbered_code}
```

CRITICAL: For each best practice issue found, you MUST:
- Start with "Line X:" where X is the specific line number
- Identify the specific practice violation
- Explain why it matters for code quality
- Provide refactoring suggestions

Evaluate these coding practice areas:
1. **Code Structure**: Organization, modularity, separation of concerns
2. **Naming Conventions**: Variable, function, class naming clarity
3. **Function Design**: Single responsibility, function length, parameters
4. **Error Handling**: Proper exception handling, error propagation
5. **Documentation**: Comments, docstrings, code self-documentation
6. **Code Duplication**: DRY principle violations, repeated logic
7. **SOLID Principles**: Single responsibility, open/closed, etc.
8. **Design Patterns**: Appropriate pattern usage, anti-patterns
9. **Testability**: Code structure for easy testing
10. **Maintainability**: Code readability, future modification ease

Example format: "Line 42: Use 'const' instead of 'var' for variables that don't change..."

Focus on practical improvements that enhance code quality with specific line references."""


class ArchitectureAgent(BaseReviewAgent):
    """Agent specialized in software architecture and design review."""
    
    def get_agent_type(self) -> str:
        return "architecture"
    
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        if diff_only:
            return f"""You are a software architect reviewing code changes.

CRITICAL RESTRICTION: You are reviewing a DIFF with context. You MUST ONLY comment on the lines that are being ADDED or CHANGED in the diff (lines starting with '+' or modified lines). DO NOT comment on context lines or unchanged code.

The content below contains:
1. DIFF TO REVIEW: The actual changes you should analyze
2. FULL FILE CONTEXT: Additional context to understand the changes (DO NOT REVIEW THESE LINES)

{code}

INSTRUCTIONS:
- ONLY review the lines that are being added/changed in the DIFF section
- Use the FULL FILE CONTEXT only to understand the broader context
- For each architectural concern found in the DIFF changes, provide:
  * Exact line number from the diff
  * Design issues or opportunities
  * Architectural impact explanation
  * Design improvement suggestions
  * Start with "Line X:" format

Focus on architectural aspects in the CHANGED LINES ONLY:
- Design patterns, coupling & cohesion, abstraction levels
- Dependency management, layered architecture, scalability design
- Extensibility, component interactions, data flow, technical debt

Example: "Line 33: Tight coupling - direct database access should be abstracted..."

Focus on long-term architectural health. IGNORE unchanged context lines."""
        else:
            # Add line numbers to the code for full file review
            lines = code.split('\n')
            numbered_code = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
            
            return f"""You are a software architect reviewing code for architectural soundness and design quality.

Analyze this code from an architectural perspective with EXACT LINE NUMBERS:

```
{numbered_code}
```

CRITICAL: For each architectural concern found, you MUST:
- Start with "Line X:" where X is the specific line number
- Identify design issues or opportunities
- Explain architectural impact
- Suggest design improvements

Focus on these architectural aspects:
1. **Design Patterns**: Appropriate pattern usage, pattern violations
2. **Coupling & Cohesion**: Loose coupling, high cohesion principles
3. **Abstraction Levels**: Proper abstraction, interface design
4. **Dependency Management**: Dependency injection, inversion of control
5. **Layered Architecture**: Proper layer separation, architectural boundaries
6. **Scalability Design**: Code structure for horizontal/vertical scaling
7. **Extensibility**: Easy feature addition, modification points
8. **Component Interactions**: Service boundaries, API design
9. **Data Flow**: Information flow, state management
10. **Technical Debt**: Architectural shortcuts, future refactoring needs

Example format: "Line 33: Tight coupling - direct database access should be abstracted..."

Focus on long-term architectural health and system evolution with specific line references."""


class ReadabilityAgent(BaseReviewAgent):
    """Agent specialized in code readability and documentation."""
    
    def get_agent_type(self) -> str:
        return "readability"
    
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        if diff_only:
            return f"""You are a code readability expert reviewing code changes.

CRITICAL RESTRICTION: You are reviewing a DIFF with context. You MUST ONLY comment on the lines that are being ADDED or CHANGED in the diff (lines starting with '+' or modified lines). DO NOT comment on context lines or unchanged code.

The content below contains:
1. DIFF TO REVIEW: The actual changes you should analyze  
2. FULL FILE CONTEXT: Additional context to understand the changes (DO NOT REVIEW THESE LINES)

{code}

INSTRUCTIONS:
- ONLY review the lines that are being added/changed in the DIFF section
- Use the FULL FILE CONTEXT only to understand the broader context
- For each readability issue found in the DIFF changes, provide:
  * Exact line number from the diff
  * Readability concern identification
  * Impact on code maintainability
  * Specific improvement suggestions
  * Start with "Line X:" format

Focus on readability aspects in the CHANGED LINES ONLY:
- Variable/function naming, code clarity, documentation
- Comments quality, code organization, complexity reduction

Example: "Line 25: Variable name 'x' is unclear - consider using descriptive name..."

Focus on making code more readable and maintainable. IGNORE unchanged context lines."""
        else:
            # Add line numbers to the code for full file review
            lines = code.split('\n')
            numbered_code = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
        
        return f"""You are a technical documentation expert focused on code readability and clarity.

Review this code for readability and documentation quality with EXACT LINE NUMBERS:

```
{numbered_code}
```

CRITICAL: For each readability issue found, you MUST:
- Start with "Line X:" where X is the specific line number
- Identify clarity problems
- Explain impact on team productivity
- Provide clearer alternatives

Evaluate these readability aspects:
1. **Code Clarity**: Self-explanatory code, clear logic flow
2. **Variable Naming**: Descriptive, meaningful names
3. **Function Naming**: Clear purpose indication, verb-noun patterns
4. **Comments**: Helpful comments, avoiding obvious comments
5. **Code Organization**: Logical grouping, consistent formatting
6. **Documentation**: Function/class documentation, usage examples
7. **Complexity**: Overly complex expressions, nested logic
8. **Consistency**: Coding style consistency throughout
9. **Magic Numbers**: Hard-coded values without explanation
10. **Code Length**: Function/class length appropriateness

Example format: "Line 67: Variable name 'data' is too generic - consider 'filteredUsers'..."

Focus on making code more accessible to other developers with specific line references."""


class TestabilityAgent(BaseReviewAgent):
    """Agent specialized in code testability and test quality."""
    
    def get_agent_type(self) -> str:
        return "testability"
    
    def get_specialized_prompt(self, code: str, diff_only: bool = False) -> str:
        return f"""You are a test engineering expert reviewing code for testability and test coverage.

Analyze this code for testing concerns and testability improvements:

```
{code}
```

Focus on these testability aspects:
1. **Test Coverage**: Missing test scenarios, edge cases
2. **Dependency Injection**: Hard dependencies, mocking difficulties
3. **Function Design**: Pure functions, side effect isolation
4. **State Management**: Global state, stateful operations
5. **External Dependencies**: Database, API, file system dependencies
6. **Error Conditions**: Exception scenarios, error path testing
7. **Test Data**: Test data setup, fixture requirements
8. **Assertion Points**: Verifiable outcomes, observable behavior
9. **Test Isolation**: Test independence, cleanup requirements
10. **Mock Points**: Interfaces for mocking, testable boundaries

For each testability issue:
- Identify testing challenges
- Suggest refactoring for better testability
- Recommend test scenarios to add
- Provide testable code alternatives
- Explain testing strategy improvements

Focus on making code easier to test thoroughly."""
