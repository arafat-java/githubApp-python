#!/usr/bin/env python3
"""
Code Reviewer Package
Multi-agent AI code review system for GitHub PRs
"""

__version__ = "1.0.0"
__author__ = "Code Review Team"

# Import main classes for easy access
try:
    from .multi_agent_reviewer import MultiAgentCodeReviewer
    from .consolidation_agent import ConsolidatedReview, ConsolidationAgent
    from .pr_review_formatter import PRReviewFormatter
    from .specialized_agents import (
        SecurityAgent, PerformanceAgent, CodingPracticesAgent,
        ArchitectureAgent, ReadabilityAgent, TestabilityAgent
    )
    from .code_reviewer import CodeReviewer
    from .llm_manager import get_llm_instance, SandboxInstances
    
    __all__ = [
        'MultiAgentCodeReviewer',
        'ConsolidatedReview', 
        'ConsolidationAgent',
        'PRReviewFormatter',
        'SecurityAgent',
        'PerformanceAgent', 
        'CodingPracticesAgent',
        'ArchitectureAgent',
        'ReadabilityAgent',
        'TestabilityAgent',
        'CodeReviewer',
        'get_llm_instance',
        'SandboxInstances'
    ]
    
except ImportError as e:
    # Handle import errors gracefully
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Some code_reviewer modules could not be imported: {e}")
    
    __all__ = []
