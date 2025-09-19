#!/usr/bin/env python3
"""
Multi-Agent Code Reviewer - Orchestrates multiple specialized agents for comprehensive code review.
"""

import asyncio
import concurrent.futures
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
import os

# Import specialized agents
from .specialized_agents import (
    SecurityAgent, PerformanceAgent, CodingPracticesAgent, 
    ArchitectureAgent, ReadabilityAgent, TestabilityAgent,
    AgentReview
)
from .consolidation_agent import ConsolidationAgent, ConsolidatedReview
from .pr_review_formatter import PRReviewFormatter


class MultiAgentCodeReviewer:
    """Orchestrates multiple specialized agents for comprehensive code review."""
    
    def __init__(self, 
                 is_local: bool = False,
                 creativity_level: float = 0.1,
                 enabled_agents: Optional[List[str]] = None):
        """
        Initialize the multi-agent code reviewer.
        
        Args:
            is_local: Whether to use local Ollama (True) or Azure OpenAI (False)
            creativity_level: Temperature for AI responses (0.0-1.0)
            enabled_agents: List of agent types to enable. If None, all agents are enabled.
        """
        self.is_local = is_local
        self.creativity_level = creativity_level
        
        # Initialize all available agents
        self.available_agents = {
            'security': SecurityAgent(is_local, creativity_level),
            'performance': PerformanceAgent(is_local, creativity_level),
            'coding_practices': CodingPracticesAgent(is_local, creativity_level),
            'architecture': ArchitectureAgent(is_local, creativity_level),
            'readability': ReadabilityAgent(is_local, creativity_level),
            'testability': TestabilityAgent(is_local, creativity_level)
        }
        
        # Set enabled agents
        if enabled_agents is None:
            self.enabled_agents = list(self.available_agents.keys())
        else:
            self.enabled_agents = [agent for agent in enabled_agents 
                                 if agent in self.available_agents]
        
        # Initialize consolidation agent
        self.consolidation_agent = ConsolidationAgent(is_local, creativity_level * 2)  # Slightly higher creativity for consolidation
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return list(self.available_agents.keys())
    
    def set_enabled_agents(self, agent_types: List[str]) -> None:
        """Set which agents should be enabled for reviews."""
        self.enabled_agents = [agent for agent in agent_types 
                             if agent in self.available_agents]
    
    def review_code(self, code: str, parallel: bool = True, diff_only: bool = False) -> Optional[ConsolidatedReview]:
        """
        Perform multi-agent code review.
        
        Args:
            code: The code to review
            parallel: Whether to run agents in parallel (faster) or sequentially
            
        Returns:
            ConsolidatedReview object with results from all agents
        """
        if not self.enabled_agents:
            print("No agents enabled for review.")
            return None
        
        print(f"🚀 Starting multi-agent code review with {len(self.enabled_agents)} agents...")
        print(f"Enabled agents: {', '.join(self.enabled_agents)}")
        
        if parallel:
            agent_reviews = self._run_agents_parallel(code, diff_only)
        else:
            agent_reviews = self._run_agents_sequential(code, diff_only)
        
        if not agent_reviews:
            print("❌ No agent reviews were completed successfully.")
            return None
        
        print(f"✅ Completed {len(agent_reviews)} agent reviews. Consolidating results...")
        
        # Consolidate all agent reviews
        consolidated_review = self.consolidation_agent.consolidate_reviews(
            agent_reviews, code
        )
        
        print("🎯 Multi-agent review completed!")
        return consolidated_review
    
    def _run_agents_parallel(self, code: str, diff_only: bool = False) -> List[AgentReview]:
        """Run all enabled agents in parallel using ThreadPoolExecutor."""
        agent_reviews = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.enabled_agents)) as executor:
            # Submit all agent tasks
            future_to_agent = {
                executor.submit(self.available_agents[agent_type].review_code, code, diff_only): agent_type
                for agent_type in self.enabled_agents
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_type = future_to_agent[future]
                try:
                    review = future.result(timeout=360)  # 6 minute timeout per agent
                    if review:
                        agent_reviews.append(review)
                        print(f"✅ {agent_type.replace('_', ' ').title()} review completed")
                    else:
                        print(f"⚠️ {agent_type.replace('_', ' ').title()} review failed")
                except Exception as e:
                    print(f"❌ {agent_type.replace('_', ' ').title()} review error: {e}")
        
        return agent_reviews
    
    def _run_agents_sequential(self, code: str, diff_only: bool = False) -> List[AgentReview]:
        """Run all enabled agents sequentially."""
        agent_reviews = []
        
        for agent_type in self.enabled_agents:
            print(f"🔄 Running {agent_type.replace('_', ' ').title()} review...")
            try:
                review = self.available_agents[agent_type].review_code(code, diff_only)
                if review:
                    agent_reviews.append(review)
                    print(f"✅ {agent_type.replace('_', ' ').title()} review completed")
                else:
                    print(f"⚠️ {agent_type.replace('_', ' ').title()} review failed")
            except Exception as e:
                print(f"❌ {agent_type.replace('_', ' ').title()} review error: {e}")
        
        return agent_reviews
    
    def review_file(self, file_path: str, parallel: bool = True) -> Optional[ConsolidatedReview]:
        """
        Review code from a file using multiple agents.
        
        Args:
            file_path: Path to the file to review
            parallel: Whether to run agents in parallel
            
        Returns:
            ConsolidatedReview object with results from all agents
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
            
            print(f"📁 Reviewing file: {file_path}")
            return self.review_code(code, parallel)
            
        except FileNotFoundError:
            print(f"❌ Error: File '{file_path}' not found.")
            return None
        except IOError as e:
            print(f"❌ Error reading file '{file_path}': {e}")
            return None
    
    def review_diff(self, diff_content: str, parallel: bool = True) -> Optional[ConsolidatedReview]:
        """
        Review a git diff using multiple agents.
        
        Args:
            diff_content: The diff content to review
            parallel: Whether to run agents in parallel
            
        Returns:
            ConsolidatedReview object with results from all agents
        """
        print("📋 Reviewing git diff...")
        return self.review_code(diff_content, parallel)
    
    def review_diff_with_context(self, diff_content: str, file_path: str, parallel: bool = True) -> Optional[ConsolidatedReview]:
        """
        Review a git diff using the full file as context.
        
        Args:
            diff_content: The diff content to review
            file_path: Path to the full file for context
            parallel: Whether to run agents in parallel
            
        Returns:
            ConsolidatedReview object with results from all agents
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                full_file_content = file.read()
            
            print(f"📋 Reviewing diff with file context: {file_path}")
            
            # Create enhanced prompt that includes both diff and full file context
            enhanced_content = f"""DIFF TO REVIEW:
{diff_content}

FULL FILE CONTEXT:
{full_file_content}

INSTRUCTIONS: Please focus your review specifically on the changes shown in the DIFF section above, but use the FULL FILE CONTEXT to understand the broader codebase and provide more accurate recommendations."""
            
            return self.review_code(enhanced_content, parallel, diff_only=True)
            
        except FileNotFoundError:
            print(f"❌ Error: File '{file_path}' not found. Falling back to diff-only review.")
            return self.review_diff(diff_content, parallel)
        except IOError as e:
            print(f"❌ Error reading file '{file_path}': {e}. Falling back to diff-only review.")
            return self.review_diff(diff_content, parallel)
    
    def generate_pr_review(self, consolidated_review: ConsolidatedReview, file_path: str) -> str:
        """Generate a PR-style review from the consolidated review."""
        # Convert consolidated review to JSON format first
        json_report = self.consolidation_agent.generate_report(consolidated_review, "json")
        
        # Use PR formatter to create GitHub/GitLab style review
        formatter = PRReviewFormatter(file_path)
        return formatter.format_pr_review(json_report)
    
    def print_pr_review(self, consolidated_review: ConsolidatedReview, file_path: str) -> None:
        """Print the PR-style review."""
        pr_review = self.generate_pr_review(consolidated_review, file_path)
        print(pr_review)
    
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about available and enabled agents."""
        return {
            'total_agents': len(self.available_agents),
            'enabled_agents': len(self.enabled_agents),
            'available_agent_types': list(self.available_agents.keys()),
            'enabled_agent_types': self.enabled_agents,
            'disabled_agent_types': [
                agent for agent in self.available_agents.keys() 
                if agent not in self.enabled_agents
            ]
        }


def main():
    """Main function for CLI usage of multi-agent code reviewer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Multi-Agent Code Review Bot - Comprehensive code analysis using specialized AI agents"
    )
    parser.add_argument("--file", "-f", help="Path to file to review")
    parser.add_argument("--code", "-c", help="Code string to review")
    parser.add_argument("--diff", "-d", help="Diff content to review")
    parser.add_argument("--diff-with-context", help="Diff content to review with full file context")
    parser.add_argument("--context-file", help="Path to full file for context (used with --diff-with-context)")
    parser.add_argument("--agents", "-a", nargs='+', 
                       choices=['security', 'performance', 'coding_practices', 
                               'architecture', 'readability', 'testability'],
                       help="Specific agents to run (default: all agents)")
    # PR format is now the default and only format
    parser.add_argument("--sequential", action="store_true", 
                       help="Run agents sequentially instead of in parallel")
    parser.add_argument("--use-ollama", action="store_true", help="Use local Ollama instead of Azure OpenAI")
    parser.add_argument("--creativity", type=float, default=0.1, help="Creativity level for AI responses (0.0-1.0)")
    parser.add_argument("--list-agents", action="store_true", 
                       help="List available agents and exit")
    parser.add_argument("--json-issues", action="store_true",
                       help="Output issues as JSON list with markdown descriptions")
    
    args = parser.parse_args()
    
    # Initialize multi-agent reviewer
    is_local = args.use_ollama
    reviewer = MultiAgentCodeReviewer(
        is_local=is_local,
        creativity_level=args.creativity,
        enabled_agents=args.agents
    )
    
    # Handle list agents command
    if args.list_agents:
        stats = reviewer.get_agent_statistics()
        print("📊 Multi-Agent Code Reviewer Statistics:")
        print(f"Total Available Agents: {stats['total_agents']}")
        print(f"Currently Enabled: {stats['enabled_agents']}")
        print("\n🤖 Available Agents:")
        for agent in stats['available_agent_types']:
            status = "✅ ENABLED" if agent in stats['enabled_agent_types'] else "⏸️ DISABLED"
            print(f"  {agent.replace('_', ' ').title()}: {status}")
        return
    
    # Validate input
    if not any([args.file, args.code, args.diff, args.diff_with_context]):
        print("❌ Error: Please provide either --file, --code, --diff, or --diff-with-context")
        sys.exit(1)
    
    # Validate diff-with-context requires context-file
    if args.diff_with_context and not args.context_file:
        print("❌ Error: --diff-with-context requires --context-file")
        sys.exit(1)
    
    try:
        print("🚀 Multi-Agent Code Review Bot Starting...")
        if is_local:
            print("Using local Ollama: llama3.2 @ http://localhost:11434")
        else:
            print("Using Azure OpenAI with client secret authentication")
        print(f"Creativity level: {args.creativity}")
        
        # Show agent configuration
        stats = reviewer.get_agent_statistics()
        print(f"Running {stats['enabled_agents']}/{stats['total_agents']} agents")
        
        # Perform review
        if args.file:
            consolidated_review = reviewer.review_file(
                args.file, 
                parallel=not args.sequential
            )
            file_path = args.file
        elif args.code:
            consolidated_review = reviewer.review_code(
                args.code, 
                parallel=not args.sequential
            )
            file_path = "code_snippet"
        elif args.diff:
            consolidated_review = reviewer.review_diff(
                args.diff, 
                parallel=not args.sequential
            )
            file_path = "diff_content"
        elif args.diff_with_context:
            consolidated_review = reviewer.review_diff_with_context(
                args.diff_with_context,
                args.context_file,
                parallel=not args.sequential
            )
            file_path = args.context_file
        
        # Generate and display review
        if consolidated_review:
            if args.json_issues:
                # Use consolidation agent to generate properly formatted JSON
                json_issues = reviewer.consolidation_agent.generate_json_review_comments(consolidated_review, file_path)
                print(json_issues)
            else:
                # Default PR-style review
                reviewer.print_pr_review(consolidated_review, file_path)
        else:
            print("❌ Multi-agent review failed. Please check your AI model connection and inputs.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹ Multi-agent review cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
