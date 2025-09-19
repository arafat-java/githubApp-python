#!/usr/bin/env python3
"""
PR Summarizer - Analyzes git diffs and generates comprehensive PR summaries.
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Add parent directory to path to import utilities
sys.path.append(str(Path(__file__).parent.parent / "code_reviewer"))

from util.llm import AzureClient
from util.config import get_secrets


@dataclass
class FileChange:
    """Represents changes to a single file."""
    filename: str
    status: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    old_filename: Optional[str] = None  # For renames
    diff_content: str = ""
    language: Optional[str] = None


@dataclass
class PRSummary:
    """Represents a complete PR summary."""
    title: str
    description: str
    changes_overview: str
    files_changed: int
    total_additions: int
    total_deletions: int
    file_changes: List[FileChange]
    key_changes: List[str]
    potential_impacts: List[str]
    testing_recommendations: List[str]
    breaking_changes: List[str]
    security_considerations: List[str]


class DiffParser:
    """Parses git diff output and extracts structured information."""
    
    def __init__(self):
        self.file_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.dockerfile': 'dockerfile'
        }
    
    def parse_diff(self, diff_content: str) -> List[FileChange]:
        """Parse git diff output and return list of file changes."""
        file_changes = []
        
        # Split diff into individual file sections
        file_sections = self._split_diff_by_files(diff_content)
        
        for section in file_sections:
            file_change = self._parse_file_section(section)
            if file_change:
                file_changes.append(file_change)
        
        return file_changes
    
    def _split_diff_by_files(self, diff_content: str) -> List[str]:
        """Split diff content into sections for each file."""
        # Split by 'diff --git' markers
        sections = re.split(r'^diff --git', diff_content, flags=re.MULTILINE)
        
        # Remove empty first section and add back 'diff --git' prefix
        sections = [f"diff --git{section}" for section in sections[1:] if section.strip()]
        
        return sections
    
    def _parse_file_section(self, section: str) -> Optional[FileChange]:
        """Parse a single file's diff section."""
        lines = section.strip().split('\n')
        if not lines:
            return None
        
        # Parse the diff header
        diff_header = lines[0]
        if not diff_header.startswith('diff --git'):
            return None
        
        # Extract file paths from header
        match = re.match(r'diff --git a/(.*?) b/(.*?)$', diff_header)
        if not match:
            return None
        
        old_path, new_path = match.groups()
        
        # Determine file status
        status = "modified"
        old_filename = None
        filename = new_path
        
        # Check for file status indicators
        for line in lines[1:10]:  # Check first few lines for status
            if line.startswith('new file mode'):
                status = "added"
            elif line.startswith('deleted file mode'):
                status = "deleted"
                filename = old_path
            elif line.startswith('rename from'):
                status = "renamed"
                old_filename = old_path
                filename = new_path
            elif line.startswith('similarity index'):
                if status != "renamed":
                    status = "modified"
        
        # Count additions and deletions
        additions = 0
        deletions = 0
        diff_content_lines = []
        
        in_diff_content = False
        for line in lines:
            if line.startswith('@@'):
                in_diff_content = True
                diff_content_lines.append(line)
            elif in_diff_content:
                diff_content_lines.append(line)
                if line.startswith('+') and not line.startswith('+++'):
                    additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deletions += 1
        
        # Determine language
        language = self._detect_language(filename)
        
        return FileChange(
            filename=filename,
            status=status,
            additions=additions,
            deletions=deletions,
            old_filename=old_filename,
            diff_content='\n'.join(diff_content_lines),
            language=language
        )
    
    def _detect_language(self, filename: str) -> Optional[str]:
        """Detect programming language from filename."""
        _, ext = os.path.splitext(filename.lower())
        return self.file_extensions.get(ext)


class PRSummaryAgent:
    """Specialized agent for generating PR summaries using Azure OpenAI."""
    
    def __init__(self, creativity_level: float = 0.1):
        """
        Initialize the PR summary agent.
        
        Args:
            creativity_level: Temperature for AI responses (0.0-1.0)
        """
        self.creativity_level = creativity_level
        self.llm_client = self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize the Azure OpenAI client."""
        secrets = get_secrets()
        if not secrets or not secrets.get('azure_client_id') or not secrets.get('azure_client_secret'):
            raise ValueError("Azure OpenAI credentials not found. Please set up environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_ENDPOINT")
        return AzureClient(secrets)
    
    def generate_summary(self, file_changes: List[FileChange], additional_context: str = "") -> PRSummary:
        """Generate a comprehensive PR summary from file changes."""
        
        # Calculate overall statistics
        total_files = len(file_changes)
        total_additions = sum(fc.additions for fc in file_changes)
        total_deletions = sum(fc.deletions for fc in file_changes)
        
        # Create context for the AI
        context = self._create_analysis_context(file_changes, additional_context)
        
        # Generate different aspects of the summary
        title = self._generate_title(context)
        description = self._generate_description(context)
        changes_overview = self._generate_changes_overview(context)
        key_changes = self._extract_key_changes(context)
        potential_impacts = self._analyze_potential_impacts(context)
        testing_recommendations = self._generate_testing_recommendations(context)
        breaking_changes = self._identify_breaking_changes(context)
        security_considerations = self._analyze_security_implications(context)
        
        return PRSummary(
            title=title,
            description=description,
            changes_overview=changes_overview,
            files_changed=total_files,
            total_additions=total_additions,
            total_deletions=total_deletions,
            file_changes=file_changes,
            key_changes=key_changes,
            potential_impacts=potential_impacts,
            testing_recommendations=testing_recommendations,
            breaking_changes=breaking_changes,
            security_considerations=security_considerations
        )
    
    def _create_analysis_context(self, file_changes: List[FileChange], additional_context: str) -> str:
        """Create analysis context from file changes."""
        context_parts = []
        
        # Add file changes summary
        context_parts.append("FILE CHANGES SUMMARY:")
        context_parts.append(f"Total files changed: {len(file_changes)}")
        
        # Group changes by status
        status_groups = {}
        for fc in file_changes:
            if fc.status not in status_groups:
                status_groups[fc.status] = []
            status_groups[fc.status].append(fc)
        
        for status, files in status_groups.items():
            context_parts.append(f"\n{status.upper()} FILES ({len(files)}):")
            for fc in files[:10]:  # Limit to first 10 files per status
                context_parts.append(f"  - {fc.filename} (+{fc.additions}/-{fc.deletions})")
                if fc.language:
                    context_parts.append(f"    Language: {fc.language}")
        
        # Add diff content (truncated for large diffs)
        context_parts.append("\nKEY DIFF CONTENT:")
        for fc in file_changes[:5]:  # Only include first 5 files
            if fc.diff_content:
                context_parts.append(f"\n--- {fc.filename} ---")
                # Truncate very long diffs
                diff_lines = fc.diff_content.split('\n')
                if len(diff_lines) > 50:
                    context_parts.append('\n'.join(diff_lines[:25]))
                    context_parts.append(f"... ({len(diff_lines) - 50} more lines) ...")
                    context_parts.append('\n'.join(diff_lines[-25:]))
                else:
                    context_parts.append(fc.diff_content)
        
        # Add additional context if provided
        if additional_context:
            context_parts.append(f"\nADDITIONAL CONTEXT:\n{additional_context}")
        
        return '\n'.join(context_parts)
    
    def _generate_title(self, context: str) -> str:
        """Generate a concise PR title focused on the importance of changes."""
        messages = [
            {
                "role": "system",
                "content": "You are an expert developer who writes impactful PR titles. Generate a title that captures the business value and importance of the changes in 8-12 words. Focus on what improvement or capability was added, not technical details."
            },
            {
                "role": "user",
                "content": f"Based on these code changes, generate a title that emphasizes the importance and value:\n\n{context[:2000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=150
        )
        
        return response.strip() if response else "Important system improvements"
    
    def _generate_description(self, context: str) -> str:
        """Generate a description focused on the importance and business value of changes."""
        messages = [
            {
                "role": "system",
                "content": "You are a product manager explaining changes to stakeholders. Focus on the importance and business value of the changes. Explain what capability was improved, what problem was solved, or what new functionality was enabled. Avoid technical jargon - focus on the 'why' and 'what it enables' in 2-3 crisp sentences."
            },
            {
                "role": "user",
                "content": f"Explain the importance and business value of these changes:\n\n{context[:4000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=300
        )
        
        return response.strip() if response else "Important improvements have been implemented."
    
    def _generate_changes_overview(self, context: str) -> str:
        """Generate an overview focused on why the changes matter."""
        messages = [
            {
                "role": "system",
                "content": "You are a technical lead explaining to the team why these changes are important. Focus on the significance and long-term benefits. Explain why this matters for the system, users, or business. Be crisp and impactful in 1-2 sentences."
            },
            {
                "role": "user",
                "content": f"Explain why these changes are important and their significance:\n\n{context[:3000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=250
        )
        
        return response.strip() if response else "These changes bring significant improvements to the system."
    
    def _extract_key_changes(self, context: str) -> List[str]:
        """Extract key improvements and their importance."""
        messages = [
            {
                "role": "system",
                "content": "You are a product owner highlighting key improvements to stakeholders. Focus on the value and importance of each change. Explain what capability was enhanced, what problem was solved, or what benefit was achieved. Avoid technical details - focus on the 'why it matters'. Each point should be one impactful sentence. Return only bullet points starting with '-'."
            },
            {
                "role": "user",
                "content": f"Extract the key improvements and explain why they matter:\n\n{context[:4000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=400
        )
        
        if response:
            # Parse bullet points
            lines = response.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        
        return ["Important system improvements have been implemented"]
    
    def _analyze_potential_impacts(self, context: str) -> List[str]:
        """Analyze potential impacts of the changes."""
        messages = [
            {
                "role": "system",
                "content": "You are a senior developer analyzing code changes. Identify potential impacts these changes might have on the system, users, performance, or other components. Focus on both positive and negative impacts. Return as bullet points starting with '-'."
            },
            {
                "role": "user",
                "content": f"Analyze potential impacts of these changes:\n\n{context[:4000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=400
        )
        
        if response:
            lines = response.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        
        return ["Impact analysis needed"]
    
    def _generate_testing_recommendations(self, context: str) -> List[str]:
        """Generate testing recommendations."""
        messages = [
            {
                "role": "system",
                "content": "You are a QA engineer. Based on the code changes, recommend specific testing approaches, test cases, or areas that need verification. Return as bullet points starting with '-'."
            },
            {
                "role": "user",
                "content": f"Recommend testing strategies for these changes:\n\n{context[:4000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=400
        )
        
        if response:
            lines = response.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        
        return ["Test the modified functionality"]
    
    def _identify_breaking_changes(self, context: str) -> List[str]:
        """Identify potential breaking changes."""
        messages = [
            {
                "role": "system",
                "content": "You are an API compatibility expert. Analyze the changes for potential breaking changes that could affect existing users, APIs, or integrations. If no breaking changes are found, return 'None identified'. Otherwise, return as bullet points starting with '-'."
            },
            {
                "role": "user",
                "content": f"Identify breaking changes in this diff:\n\n{context[:4000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=300
        )
        
        if response:
            if "none identified" in response.lower():
                return []
            lines = response.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        
        return []
    
    def _analyze_security_implications(self, context: str) -> List[str]:
        """Analyze security implications of the changes."""
        messages = [
            {
                "role": "system",
                "content": "You are a security expert. Analyze the code changes for potential security implications, vulnerabilities, or security improvements. If no security concerns are found, return 'None identified'. Otherwise, return as bullet points starting with '-'."
            },
            {
                "role": "user",
                "content": f"Analyze security implications of these changes:\n\n{context[:4000]}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=self.creativity_level,
            max_tokens=300
        )
        
        if response:
            if "none identified" in response.lower():
                return []
            lines = response.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        
        return []
    
    def _generate_diagrams(self, summary: PRSummary) -> List[str]:
        """Generate diagrams to illustrate code changes and architecture impact."""
        # Build context for diagram generation
        context_parts = []
        context_parts.append("FILES CHANGED:")
        for fc in summary.file_changes:
            context_parts.append(f"- {fc.filename} ({fc.status}): +{fc.additions}/-{fc.deletions}")
            if fc.diff_content:
                # Include a sample of the diff for context
                diff_sample = fc.diff_content[:500] + "..." if len(fc.diff_content) > 500 else fc.diff_content
                context_parts.append(f"  Diff sample: {diff_sample}")
        
        context_parts.append(f"\nKEY CHANGES:")
        for change in summary.key_changes:
            context_parts.append(f"- {change}")
        
        context = "\n".join(context_parts)
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert technical writer who creates helpful diagrams to illustrate code changes using proper Mermaid syntax.
                
Analyze the code changes and determine if diagrams would help understand:
1. Architecture changes (new components, modified relationships)
2. Data flow changes (API endpoints, database schema)  
3. Process flow changes (authentication, payment processing)
4. Component relationships (frontend-backend interactions)

If diagrams would be helpful, create them using ONLY proper Mermaid syntax with descriptive labels. Return ONLY the diagrams as markdown code blocks.
If no diagrams are needed, return "NO_DIAGRAMS_NEEDED".

IMPORTANT: Use correct Mermaid syntax with proper labels:
- flowchart TD or flowchart LR (not flowchart alone)
- sequenceDiagram (for API interactions)  
- classDiagram (for class relationships)
- erDiagram (for database schema)
- Always include a descriptive title/label before each diagram

Example correct syntax:
**New Payment Processing Flow**
```mermaid
flowchart TD
    A[Start Payment] --> B[Validate Request]
    B --> C[Process Payment]
    C --> D[Return Result]
```

**Enhanced Data Structure**
```mermaid
classDiagram
    class PaymentResult {
        +bool success
        +string transaction_id
        +string error_message
    }
```

**Database Schema Changes**
```mermaid
erDiagram
    ORDER {
        int id
        int user_id
        decimal total
    }
    ORDER_ITEM {
        int id
        int order_id
        int product_id
    }
    ORDER ||--o{ ORDER_ITEM : contains
```

CRITICAL SYNTAX RULES:
- For flowchart: Use simple node connections A --> B (no conditions or pipes)
- Node labels: A[Simple Text] - no parentheses, pipes, or special characters
- NO conditional syntax like -->|Yes| or -->|Contains|
- NO function calls in labels like [Call onCheckout()]
- For classDiagram: +type property_name (no colons)
- Methods: +return_type method_name() 
- For erDiagram: Use simple relationships like TABLE1 ||--o{ TABLE2 : has
- NO quotes in ER relationships, use: PARENT ||--o{ CHILD : relationship_name
- Always include a descriptive label before each diagram
- Keep diagrams simple and focus on the main flow/structure
- If you need conditions, use decision diamonds: B{Decision}

Be concise - focus only on the most important architectural changes."""
            },
            {
                "role": "user",
                "content": f"Analyze these code changes and create diagrams if they would help understand the impact:\n\n{context}"
            }
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent diagram generation
            max_tokens=800
        )
        
        if not response or response.strip() == "NO_DIAGRAMS_NEEDED":
            return []
        
        # Split response into lines and return as list
        diagram_lines = response.strip().split('\n')
        return diagram_lines


class PRSummarizerApp:
    """Main PR Summarizer application using Azure OpenAI."""
    
    def __init__(self, creativity_level: float = 0.1):
        """
        Initialize the PR Summarizer app.
        
        Args:
            creativity_level: Temperature for AI responses (0.0-1.0)
        """
        self.diff_parser = DiffParser()
        self.summary_agent = PRSummaryAgent(creativity_level)
    
    def summarize_diff(self, diff_content: str, additional_context: str = "") -> PRSummary:
        """
        Summarize a git diff.
        
        Args:
            diff_content: Git diff content
            additional_context: Additional context about the PR
            
        Returns:
            PRSummary object with comprehensive analysis
        """
        # Parse the diff
        file_changes = self.diff_parser.parse_diff(diff_content)
        
        if not file_changes:
            raise ValueError("No file changes found in the provided diff")
        
        # Generate summary
        return self.summary_agent.generate_summary(file_changes, additional_context)
    
    def summarize_from_json(self, json_data: List[Dict[str, Any]], additional_context: str = "") -> PRSummary:
        """
        Summarize changes from JSON list of file changes.
        
        Args:
            json_data: List of dictionaries containing file change information
            additional_context: Additional context about the PR
            
        Returns:
            PRSummary object with comprehensive analysis
        """
        # Convert JSON data to FileChange objects
        file_changes = []
        
        for item in json_data:
            # Extract file change information from JSON
            filename = item.get('filename', item.get('file', ''))
            if not filename:
                continue
                
            status = item.get('status', 'modified')
            additions = item.get('additions', item.get('added', 0))
            deletions = item.get('deletions', item.get('deleted', 0))
            old_filename = item.get('old_filename', item.get('previous_filename'))
            diff_content = item.get('diff', item.get('patch', ''))
            
            # Detect language from filename
            language = self.diff_parser._detect_language(filename)
            
            file_change = FileChange(
                filename=filename,
                status=status,
                additions=int(additions) if additions else 0,
                deletions=int(deletions) if deletions else 0,
                old_filename=old_filename,
                diff_content=diff_content,
                language=language
            )
            
            file_changes.append(file_change)
        
        if not file_changes:
            raise ValueError("No valid file changes found in the provided JSON data")
        
        # Generate summary
        return self.summary_agent.generate_summary(file_changes, additional_context)
    
    def summarize_file(self, diff_file_path: str, additional_context: str = "") -> PRSummary:
        """
        Summarize a diff from a file.
        
        Args:
            diff_file_path: Path to file containing git diff
            additional_context: Additional context about the PR
            
        Returns:
            PRSummary object with comprehensive analysis
        """
        try:
            with open(diff_file_path, 'r', encoding='utf-8') as f:
                diff_content = f.read()
            return self.summarize_diff(diff_content, additional_context)
        except FileNotFoundError:
            raise FileNotFoundError(f"Diff file not found: {diff_file_path}")
        except Exception as e:
            raise Exception(f"Error reading diff file: {e}")
    
    def format_summary(self, summary: PRSummary, format_type: str = "markdown") -> str:
        """
        Format the PR summary for output.
        
        Args:
            summary: PRSummary object
            format_type: Output format ("markdown", "json", "text")
            
        Returns:
            Formatted summary string
        """
        if format_type == "json":
            return json.dumps(asdict(summary), indent=2)
        elif format_type == "text":
            return self._format_text(summary)
        else:  # markdown
            return self._format_markdown(summary, self.summary_agent)
    
    def _format_markdown(self, summary: PRSummary, agent=None) -> str:
        """Format summary focused on importance and impact of changes."""
        lines = []
        
        lines.append(f"# {summary.title}")
        lines.append("")
        lines.append("## What Changed")
        lines.append(summary.description)
        lines.append("")
        
        lines.append("## Why It Matters")
        lines.append(summary.changes_overview)
        lines.append("")
        
        # Generate diagrams if they would help understand the changes
        if agent:
            diagrams = agent._generate_diagrams(summary)
            if diagrams:
                lines.append("## Architecture Overview")
                lines.extend(diagrams)
                lines.append("")
        
        if summary.key_changes:
            lines.append("## Key Improvements")
            for change in summary.key_changes:
                lines.append(f"- {change}")
            lines.append("")
        
        return "\n".join(lines)
    
    
    def _format_text(self, summary: PRSummary) -> str:
        """Format summary as plain text."""
        lines = []
        
        lines.append(f"TITLE: {summary.title}")
        lines.append("=" * len(f"TITLE: {summary.title}"))
        lines.append("")
        
        lines.append("DESCRIPTION:")
        lines.append(summary.description)
        lines.append("")
        
        lines.append("CHANGES OVERVIEW:")
        lines.append(summary.changes_overview)
        lines.append("")
        
        lines.append("STATISTICS:")
        lines.append(f"  Files changed: {summary.files_changed}")
        lines.append(f"  Lines added: {summary.total_additions}")
        lines.append(f"  Lines deleted: {summary.total_deletions}")
        lines.append("")
        
        if summary.key_changes:
            lines.append("KEY CHANGES:")
            for change in summary.key_changes:
                lines.append(f"  - {change}")
            lines.append("")
        
        if summary.potential_impacts:
            lines.append("POTENTIAL IMPACTS:")
            for impact in summary.potential_impacts:
                lines.append(f"  - {impact}")
            lines.append("")
        
        if summary.breaking_changes:
            lines.append("BREAKING CHANGES:")
            for change in summary.breaking_changes:
                lines.append(f"  - {change}")
            lines.append("")
        
        if summary.security_considerations:
            lines.append("SECURITY CONSIDERATIONS:")
            for consideration in summary.security_considerations:
                lines.append(f"  - {consideration}")
            lines.append("")
        
        if summary.testing_recommendations:
            lines.append("TESTING RECOMMENDATIONS:")
            for recommendation in summary.testing_recommendations:
                lines.append(f"  - {recommendation}")
            lines.append("")
        
        lines.append("FILES CHANGED:")
        for fc in summary.file_changes:
            lines.append(f"  - {fc.filename} ({fc.status}) +{fc.additions}/-{fc.deletions}")
            if fc.old_filename:
                lines.append(f"    Renamed from: {fc.old_filename}")
        
        return "\n".join(lines)


def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PR Summarizer - Analyze JSON file changes and generate PR summaries using Azure OpenAI")
    parser.add_argument("--json-file", "-f", help="Path to JSON file containing file changes")
    parser.add_argument("--json-input", "-j", help="JSON string of file changes (use '-' for stdin)")
    parser.add_argument("--context", "-c", help="Additional context about the PR", default="")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--creativity", type=float, default=0.1, 
                       help="Creativity level for AI responses (0.0-1.0)")
    
    args = parser.parse_args()
    
    if not args.json_file and not args.json_input:
        print("Error: Please provide either --json-file or --json-input")
        print("\nExample JSON format:")
        print("""[
  {
    "filename": "src/app.py",
    "status": "modified",
    "additions": 5,
    "deletions": 2,
    "diff": "diff content here..."
  }
]""")
        print("\nRequired Azure OpenAI environment variables:")
        print("  AZURE_TENANT_ID")
        print("  AZURE_CLIENT_ID") 
        print("  AZURE_CLIENT_SECRET")
        print("  AZURE_ENDPOINT")
        sys.exit(1)
    
    try:
        # Initialize the app
        app = PRSummarizerApp(creativity_level=args.creativity)
        
        # Get JSON data
        if args.json_file:
            with open(args.json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        else:
            if args.json_input == '-':
                json_content = sys.stdin.read()
            else:
                json_content = args.json_input
            json_data = json.loads(json_content)
        
        # Validate JSON data is a list
        if not isinstance(json_data, list):
            raise ValueError("JSON input must be a list of file changes")
        
        # Generate summary
        summary = app.summarize_from_json(json_data, args.context)
        
        # Format as markdown for the summary field
        markdown_summary = app.format_summary(summary, "markdown")
        
        # Convert markdown string to list of lines
        summary_lines = markdown_summary.split('\n')
        
        # Create JSON output with summary as list of strings
        output = {
            "summary": summary_lines
        }
        
        # Write output
        json_output = json.dumps(output, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"Summary written to {args.output}")
        else:
            print(json_output)
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
