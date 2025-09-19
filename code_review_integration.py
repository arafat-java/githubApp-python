#!/usr/bin/env python3
"""
Code Review Integration Module
Integrates the code_reviewer functionality into the main GitHub App PR review process
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add code_reviewer to path for imports
sys.path.append(str(Path(__file__).parent / "code_reviewer"))

try:
    from code_reviewer.multi_agent_reviewer import MultiAgentCodeReviewer
    from code_reviewer.consolidation_agent import ConsolidatedReview
    from code_reviewer.pr_review_formatter import PRReviewFormatter
except ImportError as e:
    print(f"Warning: Could not import code_reviewer modules: {e}")
    MultiAgentCodeReviewer = None
    ConsolidatedReview = None
    PRReviewFormatter = None

logger = logging.getLogger(__name__)


class CodeReviewIntegration:
    """Integrates code review functionality into GitHub PR handling."""
    
    def __init__(self, use_local_llm: bool = False, creativity_level: float = 0.1):
        """
        Initialize the code review integration.
        
        Args:
            use_local_llm: Whether to use local Ollama (True) or Azure OpenAI (False)
            creativity_level: Temperature for AI responses (0.0-1.0)
        """
        self.use_local_llm = use_local_llm
        self.creativity_level = creativity_level
        self.multi_agent_reviewer = None
        
        # Initialize the multi-agent reviewer if available
        if MultiAgentCodeReviewer:
            try:
                # Try to initialize with the specified backend
                self.multi_agent_reviewer = MultiAgentCodeReviewer(
                    is_local=use_local_llm,
                    creativity_level=creativity_level,
                    enabled_agents=['security', 'performance', 'coding_practices', 'readability']
                )
                logger.info(f"Multi-agent code reviewer initialized successfully (local: {use_local_llm})")
            except Exception as e:
                logger.error(f"Failed to initialize multi-agent reviewer with {use_local_llm and 'local' or 'Azure'} backend: {e}")
                
                # Try fallback to local LLM if Azure failed
                if not use_local_llm:
                    try:
                        logger.info("Attempting fallback to local Ollama...")
                        self.multi_agent_reviewer = MultiAgentCodeReviewer(
                            is_local=True,
                            creativity_level=creativity_level,
                            enabled_agents=['security', 'performance', 'coding_practices', 'readability']
                        )
                        logger.info("Multi-agent code reviewer initialized successfully with local Ollama fallback")
                    except Exception as fallback_error:
                        logger.error(f"Fallback to local Ollama also failed: {fallback_error}")
                        self.multi_agent_reviewer = None
                else:
                    self.multi_agent_reviewer = None
        else:
            logger.warning("Multi-agent code reviewer not available")
    
    def is_available(self) -> bool:
        """Check if code review functionality is available."""
        return self.multi_agent_reviewer is not None
    
    def review_pr_diff(self, diff_content: str, pr_info: Dict[str, Any]) -> Optional[str]:
        """
        Review a PR diff using the multi-agent system.
        
        Args:
            diff_content: The PR diff content
            pr_info: Dictionary containing PR information (title, number, etc.)
            
        Returns:
            Formatted review comment or None if review failed
        """
        if not self.is_available():
            logger.warning("Code review functionality not available")
            return None
        
        try:
            logger.info(f"Starting code review for PR #{pr_info.get('number', 'unknown')}")
            
            # Perform multi-agent review
            consolidated_review = self.multi_agent_reviewer.review_diff(
                diff_content, 
                parallel=True
            )
            
            if not consolidated_review:
                logger.error("Failed to get consolidated review")
                return None
            
            # Generate JSON issues format for structured review comments
            file_path = pr_info.get('title', 'PR Changes')
            json_issues = self.multi_agent_reviewer.consolidation_agent.generate_json_review_comments(
                consolidated_review, 
                file_path
            )
            
            # Convert JSON issues to formatted review comment
            formatted_review = self._format_json_issues_for_pr(json_issues, pr_info)
            
            logger.info("Code review completed successfully")
            return formatted_review
            
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            return None
    
    def review_pr_files(self, files_data: List[Dict[str, Any]], pr_info: Dict[str, Any]) -> Optional[str]:
        """
        Review PR files using the multi-agent system.
        
        Args:
            files_data: List of file change data from GitHub API
            pr_info: Dictionary containing PR information
            
        Returns:
            Formatted review comment or None if review failed
        """
        if not self.is_available():
            logger.warning("Code review functionality not available")
            return None
        
        try:
            logger.info(f"Starting file-based code review for PR #{pr_info.get('number', 'unknown')}")
            
            # Combine all file changes into a single review
            combined_content = self._combine_file_changes(files_data)
            
            if not combined_content:
                logger.warning("No file changes to review")
                return None
            
            # Perform multi-agent review
            consolidated_review = self.multi_agent_reviewer.review_code(
                combined_content, 
                parallel=True
            )
            
            if not consolidated_review:
                logger.error("Failed to get consolidated review")
                return None
            
            # Generate JSON issues format for structured review comments
            file_path = f"PR #{pr_info.get('number', 'unknown')} Changes"
            json_issues = self.multi_agent_reviewer.consolidation_agent.generate_json_review_comments(
                consolidated_review, 
                file_path
            )
            
            # Convert JSON issues to formatted review comment
            pr_review = self._format_json_issues_for_pr(json_issues, pr_info)
            
            logger.info("File-based code review completed successfully")
            return pr_review
            
        except Exception as e:
            logger.error(f"Error during file-based code review: {e}")
            return None
    
    def _combine_file_changes(self, files_data: List[Dict[str, Any]]) -> str:
        """
        Combine file changes into a single reviewable content.
        
        Args:
            files_data: List of file change data from GitHub API
            
        Returns:
            Combined content string
        """
        combined_content = "=== PR FILE CHANGES ===\n\n"
        
        for file_info in files_data:
            filename = file_info.get('filename', 'unknown')
            status = file_info.get('status', 'unknown')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            patch = file_info.get('patch', '')
            
            combined_content += f"File: {filename}\n"
            combined_content += f"Status: {status}\n"
            combined_content += f"Changes: +{additions} -{deletions}\n"
            
            if patch:
                # Truncate very large patches to avoid token limits
                if len(patch) > 8000:
                    patch = patch[:8000] + "\n... (truncated due to size)"
                combined_content += f"Patch:\n{patch}\n"
            
            combined_content += "\n" + "="*50 + "\n\n"
        
        return combined_content
    
    def _format_json_issues_for_pr(self, json_issues: str, pr_info: Dict[str, Any]) -> str:
        """
        Convert JSON issues to formatted PR review comment.
        
        Args:
            json_issues: JSON string containing review issues
            pr_info: Dictionary containing PR information
            
        Returns:
            Formatted review comment for PR
        """
        try:
            import json
            issues = json.loads(json_issues)
            
            if not issues:
                return "✅ **No issues found!** The code looks good and follows best practices."
            
            # Group issues by file
            issues_by_file = {}
            for issue in issues:
                file_path = issue.get('file_path', 'unknown')
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)
            
            # Format the review comment
            review_comment = "## 🔍 **Code Review Results**\n\n"
            
            for file_path, file_issues in issues_by_file.items():
                review_comment += f"### 📁 **{file_path}**\n\n"
                
                for issue in file_issues:
                    line_number = issue.get('line_number', 'N/A')
                    comment = issue.get('review_comment', 'No comment provided')
                    
                    review_comment += f"**Line {line_number}:** {comment}\n\n"
                
                review_comment += "---\n\n"
            
            # Add summary
            total_issues = len(issues)
            review_comment += f"**📊 Summary:** Found {total_issues} issue{'s' if total_issues != 1 else ''} across {len(issues_by_file)} file{'s' if len(issues_by_file) != 1 else ''}.\n\n"
            review_comment += "Please review the feedback above and address any critical issues before merging."
            
            return review_comment
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON issues: {e}")
            return f"❌ **Review Error:** Failed to parse review results. Raw output:\n\n```json\n{json_issues}\n```"
        except Exception as e:
            logger.error(f"Error formatting JSON issues: {e}")
            return f"❌ **Review Error:** {str(e)}"
    


def create_code_review_integration(use_local_llm: bool = False) -> CodeReviewIntegration:
    """
    Factory function to create a code review integration instance.
    
    Args:
        use_local_llm: Whether to use local Ollama instead of Azure OpenAI
        
    Returns:
        CodeReviewIntegration instance
    """
    return CodeReviewIntegration(use_local_llm=use_local_llm)


# Global instance for easy access
_code_review_integration = None

def get_code_review_integration() -> Optional[CodeReviewIntegration]:
    """Get the global code review integration instance."""
    global _code_review_integration
    if _code_review_integration is None:
        # Check if we should use local LLM (set via environment variable)
        use_local = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'
        _code_review_integration = create_code_review_integration(use_local_llm=use_local)
    return _code_review_integration
