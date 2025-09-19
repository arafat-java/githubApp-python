#!/usr/bin/env python3
"""
PR Summarizer Integration Module
Integrates the pr_summarizer functionality into the main GitHub App PR review process
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add pr_summarizer to path for imports
sys.path.append(str(Path(__file__).parent / "pr_summarizer"))

# Add code_reviewer to path for config utilities
sys.path.append(str(Path(__file__).parent / "code_reviewer"))

try:
    import pr_summarizer
    from pr_summarizer import PRSummarizerApp, PRSummary
except ImportError as e:
    print(f"Warning: Could not import pr_summarizer modules: {e}")
    PRSummarizerApp = None
    PRSummary = None

# Import config utilities for environment variable loading
try:
    from util.config import load_env_file, get_secrets, validate_azure_config
except ImportError as e:
    print(f"Warning: Could not import config utilities: {e}")
    load_env_file = None
    get_secrets = None
    validate_azure_config = None

logger = logging.getLogger(__name__)


class PRSummarizerIntegration:
    """Integrates PR summarizer functionality into GitHub PR handling."""
    
    def __init__(self, creativity_level: float = 0.1):
        """
        Initialize the PR summarizer integration.
        
        Args:
            creativity_level: Temperature for AI responses (0.0-1.0)
        """
        self.creativity_level = creativity_level
        self.pr_summarizer = None
        self.initialization_error = None
        
        # Load environment variables from .env file
        if load_env_file:
            try:
                load_env_file()
                logger.info("Environment variables loaded from .env file")
            except Exception as e:
                logger.warning(f"Failed to load .env file: {e}")
        
        # Initialize the PR summarizer if available
        if PRSummarizerApp:
            try:
                self.pr_summarizer = PRSummarizerApp(creativity_level=creativity_level)
                logger.info(f"PR Summarizer initialized successfully with creativity level: {creativity_level}")
            except Exception as e:
                self.initialization_error = str(e)
                logger.error(f"Failed to initialize PR summarizer: {e}")
                
                # Check if Azure config is valid
                if validate_azure_config:
                    if validate_azure_config():
                        logger.error("Azure configuration appears valid, but initialization still failed")
                    else:
                        logger.error("Azure configuration is invalid. Please check your .env file:")
                        secrets = get_secrets() if get_secrets else {}
                        missing = [key for key, value in secrets.items() if not value]
                        if missing:
                            logger.error(f"Missing environment variables: {missing}")
                        logger.error("Required variables:")
                        logger.error("  - AZURE_TENANT_ID")
                        logger.error("  - AZURE_CLIENT_ID") 
                        logger.error("  - AZURE_CLIENT_SECRET")
                        logger.error("  - AZURE_ENDPOINT")
                else:
                    logger.error("Could not validate Azure configuration")
                
                self.pr_summarizer = None
        else:
            logger.warning("PR Summarizer module not available - import failed")
    
    def is_available(self) -> bool:
        """Check if PR summarizer functionality is available."""
        return self.pr_summarizer is not None
    
    def summarize_pr_files(self, files_data: List[Dict[str, Any]], pr_info: Dict[str, Any]) -> Optional[str]:
        """
        Generate a PR summary from file changes data.
        
        Args:
            files_data: List of file change data from GitHub API
            pr_info: Dictionary containing PR information (title, number, etc.)
            
        Returns:
            Formatted PR summary or None if summarization failed
        """
        if not self.is_available():
            logger.warning("PR summarizer functionality not available - using fallback summary")
            return self._generate_fallback_summary(files_data, pr_info)
        
        try:
            logger.info(f"Starting PR summarization for PR #{pr_info.get('number', 'unknown')}")
            
            # Convert GitHub API file data to the format expected by PRSummarizerApp
            json_data = self._convert_files_to_json(files_data)
            
            if not json_data:
                logger.warning("No file changes to summarize")
                return None
            
            # Generate additional context from PR info
            additional_context = self._create_pr_context(pr_info)
            
            # Generate summary using the PR summarizer
            summary = self.pr_summarizer.summarize_from_json(json_data, additional_context)
            
            if not summary:
                logger.error("Failed to generate PR summary")
                return None
            
            # Format the summary for PR comment
            formatted_summary = self._format_summary_for_pr(summary, pr_info)
            
            logger.info("PR summarization completed successfully")
            return formatted_summary
            
        except Exception as e:
            logger.error(f"Error during PR summarization: {e}")
            return None
    
    def summarize_pr_diff(self, diff_content: str, pr_info: Dict[str, Any]) -> Optional[str]:
        """
        Generate a PR summary from diff content.
        
        Args:
            diff_content: The PR diff content
            pr_info: Dictionary containing PR information
            
        Returns:
            Formatted PR summary or None if summarization failed
        """
        if not self.is_available():
            logger.warning("PR summarizer functionality not available")
            return None
        
        try:
            logger.info(f"Starting PR summarization from diff for PR #{pr_info.get('number', 'unknown')}")
            
            # Generate additional context from PR info
            additional_context = self._create_pr_context(pr_info)
            
            # Generate summary using the PR summarizer
            summary = self.pr_summarizer.summarize_diff(diff_content, additional_context)
            
            if not summary:
                logger.error("Failed to generate PR summary from diff")
                return None
            
            # Format the summary for PR comment
            formatted_summary = self._format_summary_for_pr(summary, pr_info)
            
            logger.info("PR summarization from diff completed successfully")
            return formatted_summary
            
        except Exception as e:
            logger.error(f"Error during PR summarization from diff: {e}")
            return None
    
    def _convert_files_to_json(self, files_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert GitHub API file data to JSON format expected by PRSummarizerApp.
        
        Args:
            files_data: List of file change data from GitHub API
            
        Returns:
            List of file change dictionaries in PRSummarizerApp format
        """
        json_data = []
        
        for file_info in files_data:
            # Extract file change information
            filename = file_info.get('filename', '')
            if not filename:
                continue
            
            status = file_info.get('status', 'modified')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            patch = file_info.get('patch', '')
            
            # Handle renamed files
            old_filename = None
            if status == 'renamed' and 'previous_filename' in file_info:
                old_filename = file_info['previous_filename']
            
            # Create file change object
            file_change = {
                'filename': filename,
                'status': status,
                'additions': additions,
                'deletions': deletions,
                'diff': patch,
                'old_filename': old_filename
            }
            
            json_data.append(file_change)
        
        return json_data
    
    def _create_pr_context(self, pr_info: Dict[str, Any]) -> str:
        """
        Create additional context for PR summarization.
        
        Args:
            pr_info: Dictionary containing PR information
            
        Returns:
            Context string for the PR summarizer
        """
        context_parts = []
        
        pr_number = pr_info.get('number', 'unknown')
        pr_title = pr_info.get('title', 'Unknown PR')
        repo_owner = pr_info.get('repo_owner', 'unknown')
        repo_name = pr_info.get('repo_name', 'unknown')
        
        context_parts.append(f"PR #{pr_number}: {pr_title}")
        context_parts.append(f"Repository: {repo_owner}/{repo_name}")
        
        # Add any additional context from PR description if available
        pr_description = pr_info.get('description', '')
        if pr_description:
            context_parts.append(f"Description: {pr_description}")
        
        return "\n".join(context_parts)
    
    def _generate_fallback_summary(self, files_data: List[Dict[str, Any]], pr_info: Dict[str, Any]) -> str:
        """
        Generate a basic fallback summary when AI summarizer is not available.
        
        Args:
            files_data: List of file change data from GitHub API
            pr_info: Dictionary containing PR information
            
        Returns:
            Basic formatted summary
        """
        try:
            pr_number = pr_info.get('number', 'unknown')
            pr_title = pr_info.get('title', 'Unknown PR')
            
            # Calculate basic statistics
            total_files = len(files_data)
            total_additions = sum(f.get('additions', 0) for f in files_data)
            total_deletions = sum(f.get('deletions', 0) for f in files_data)
            
            # Group files by status
            status_groups = {}
            for file_info in files_data:
                status = file_info.get('status', 'modified')
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(file_info)
            
            # Generate basic summary
            summary_lines = []
            summary_lines.append(f"## 📋 **Basic PR Summary for PR #{pr_number}**")
            summary_lines.append("")
            summary_lines.append(f"**PR Title:** {pr_title}")
            summary_lines.append("")
            summary_lines.append("### 📊 **Change Statistics**")
            summary_lines.append(f"- **Files changed:** {total_files}")
            summary_lines.append(f"- **Lines added:** {total_additions}")
            summary_lines.append(f"- **Lines deleted:** {total_deletions}")
            summary_lines.append(f"- **Net change:** +{total_additions - total_deletions}")
            summary_lines.append("")
            
            # Add file breakdown
            summary_lines.append("### 📁 **Files Changed**")
            for status, files in status_groups.items():
                status_emoji = {
                    'added': '🆕',
                    'modified': '📝', 
                    'deleted': '🗑️',
                    'renamed': '📛'
                }.get(status, '📄')
                
                summary_lines.append(f"**{status_emoji} {status.title()} ({len(files)} files):**")
                for file_info in files[:10]:  # Limit to first 10 files per status
                    filename = file_info.get('filename', 'unknown')
                    additions = file_info.get('additions', 0)
                    deletions = file_info.get('deletions', 0)
                    summary_lines.append(f"  - `{filename}` (+{additions}/-{deletions})")
                
                if len(files) > 10:
                    summary_lines.append(f"  - ... and {len(files) - 10} more files")
                summary_lines.append("")
            
            # Add note about AI summarizer
            summary_lines.append("---")
            summary_lines.append("")
            summary_lines.append("⚠️ **Note:** This is a basic summary. For detailed AI-powered analysis including:")
            summary_lines.append("- Key improvements and business impact")
            summary_lines.append("- Security and performance considerations") 
            summary_lines.append("- Testing recommendations")
            summary_lines.append("- Breaking change detection")
            summary_lines.append("")
            summary_lines.append("Please ensure Azure OpenAI credentials are configured:")
            summary_lines.append("- `AZURE_TENANT_ID`")
            summary_lines.append("- `AZURE_CLIENT_ID`")
            summary_lines.append("- `AZURE_CLIENT_SECRET`")
            summary_lines.append("- `AZURE_ENDPOINT`")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"Error generating fallback summary: {e}")
            return f"❌ **Summary Error:** Failed to generate summary: {str(e)}"
    
    def _format_summary_for_pr(self, summary: PRSummary, pr_info: Dict[str, Any]) -> str:
        """
        Format the PR summary for posting as a PR comment.
        
        Args:
            summary: PRSummary object from the summarizer
            pr_info: Dictionary containing PR information
            
        Returns:
            Formatted summary comment for PR
        """
        try:
            # Get the markdown formatted summary
            markdown_summary = self.pr_summarizer.format_summary(summary, "markdown")
            
            # Add a header to make it clear this is an automated summary
            pr_number = pr_info.get('number', 'unknown')
            formatted_comment = f"""## 📋 **Automated PR Summary for PR #{pr_number}**

{markdown_summary}

---
*This summary was generated automatically by our AI-powered PR analysis system.*"""
            
            return formatted_comment
            
        except Exception as e:
            logger.error(f"Error formatting PR summary: {e}")
            return f"❌ **Summary Error:** Failed to format PR summary: {str(e)}"
    


def create_pr_summarizer_integration(creativity_level: float = 0.1) -> PRSummarizerIntegration:
    """
    Factory function to create a PR summarizer integration instance.
    
    Args:
        creativity_level: Temperature for AI responses (0.0-1.0)
        
    Returns:
        PRSummarizerIntegration instance
    """
    return PRSummarizerIntegration(creativity_level=creativity_level)


# Global instance for easy access
_pr_summarizer_integration = None

def get_pr_summarizer_integration() -> Optional[PRSummarizerIntegration]:
    """Get the global PR summarizer integration instance."""
    global _pr_summarizer_integration
    if _pr_summarizer_integration is None:
        # Get creativity level from environment variable or use default
        creativity_level = float(os.getenv('PR_SUMMARIZER_CREATIVITY', '0.1'))
        _pr_summarizer_integration = create_pr_summarizer_integration(creativity_level=creativity_level)
    return _pr_summarizer_integration
