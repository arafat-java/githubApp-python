#!/usr/bin/env python3
"""
Consolidation Agent - Aggregates and synthesizes reviews from multiple specialized agents.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
from .specialized_agents import AgentReview, ReviewFinding, Severity
from .llm_manager import SandboxInstances
from .util.llm import AzureClient, OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ConsolidatedReview:
    """Represents the final consolidated review from all agents."""
    overall_score: int  # 1-10 scale
    summary: str
    agent_reviews: List[AgentReview]
    critical_issues: List[ReviewFinding]
    high_priority_recommendations: List[str]
    findings_by_category: Dict[str, List[ReviewFinding]]
    severity_distribution: Dict[str, int]
    detailed_analysis: str


class ConsolidationAgent:
    """Agent responsible for consolidating reviews from all specialized agents."""
    
    def __init__(self, is_local: bool = False, creativity_level: float = 0.2):
        """
        Initialize the consolidation agent.
        
        Args:
            is_local: Whether to use local Ollama (True) or Azure OpenAI (False)
            creativity_level: Temperature for AI responses (0.0-1.0)
        """
        self.is_local = is_local
        self.creativity_level = creativity_level
        
        # Get LLM instance through the sandbox manager
        self.llm_client = SandboxInstances.get_instance(
            name="consolidation_agent",
            is_local=is_local,
            creativity_level=creativity_level
        )
    
    def _make_api_request(self, prompt: str) -> Optional[str]:
        """Make a request to the AI model through the LLM client."""
        try:
            # Prepare messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": "You are a senior technical lead specializing in consolidating multiple code review reports. Provide comprehensive analysis and actionable recommendations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Make request through the LLM client
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=self.creativity_level,
                max_tokens=3000
            )
            
            if response:
                logger.debug("ConsolidationAgent completed successfully")
                return response
            else:
                logger.error("ConsolidationAgent returned empty response")
                return None
                
        except Exception as e:
            logger.error(f"Error in ConsolidationAgent: {e}")
            return None
    
    def consolidate_reviews(self, agent_reviews: List[AgentReview], 
                          original_code: str) -> ConsolidatedReview:
        """Consolidate multiple agent reviews into a single comprehensive review."""
        
        # Aggregate findings and statistics
        all_findings = []
        critical_issues = []
        all_recommendations = []
        findings_by_category = defaultdict(list)
        severity_distribution = defaultdict(int)
        
        for review in agent_reviews:
            all_findings.extend(review.findings)
            all_recommendations.extend(review.recommendations)
            
            for finding in review.findings:
                if finding.severity == Severity.CRITICAL:
                    critical_issues.append(finding)
                
                findings_by_category[finding.agent_type].append(finding)
                severity_distribution[finding.severity.value] += 1
        
        # Calculate overall score (weighted average of agent scores)
        total_score = sum(review.overall_score for review in agent_reviews)
        overall_score = round(total_score / len(agent_reviews)) if agent_reviews else 5
        
        # Generate AI-powered consolidated summary and analysis
        detailed_analysis = self._generate_consolidated_analysis(
            agent_reviews, all_findings, original_code
        )
        
        # Extract high-priority recommendations
        high_priority_recommendations = self._extract_high_priority_recommendations(
            all_recommendations, critical_issues
        )
        
        # Generate executive summary
        summary = self._generate_executive_summary(
            agent_reviews, overall_score, len(critical_issues)
        )
        
        return ConsolidatedReview(
            overall_score=overall_score,
            summary=summary,
            agent_reviews=agent_reviews,
            critical_issues=critical_issues,
            high_priority_recommendations=high_priority_recommendations,
            findings_by_category=dict(findings_by_category),
            severity_distribution=dict(severity_distribution),
            detailed_analysis=detailed_analysis
        )
    
    def _generate_consolidated_analysis(self, agent_reviews: List[AgentReview], 
                                      all_findings: List[ReviewFinding], 
                                      original_code: str) -> str:
        """Generate detailed consolidated analysis using AI."""
        
        # Prepare summary of all agent findings
        agent_summaries = []
        for review in agent_reviews:
            findings_summary = f"{len(review.findings)} findings" if review.findings else "no major issues"
            agent_summaries.append(f"- {review.agent_name}: Score {review.overall_score}/10, {findings_summary}")
        
        findings_summary = []
        for finding in all_findings[:10]:  # Limit to top 10 findings
            findings_summary.append(f"- [{finding.severity.value.upper()}] {finding.title}")
        
        prompt = f"""You are a senior technical lead consolidating multiple specialized code review reports.

Original Code:
```
{original_code[:1000]}{'...' if len(original_code) > 1000 else ''}
```

Agent Review Summary:
{chr(10).join(agent_summaries)}

Key Findings:
{chr(10).join(findings_summary)}

Provide a comprehensive consolidated analysis that:

1. **Cross-Agent Correlation**: Identify patterns and connections between different agents' findings
2. **Priority Assessment**: Rank issues by business impact and technical risk
3. **Root Cause Analysis**: Identify underlying causes that contribute to multiple issues
4. **Implementation Roadmap**: Suggest a logical order for addressing issues
5. **Trade-off Analysis**: Highlight any conflicts between different recommendations
6. **Quality Gates**: Recommend what must be fixed before code can be deployed

Structure your response as a detailed technical analysis that helps developers understand:
- Which issues are interconnected
- What to fix first and why
- How different aspects of code quality relate to each other
- Long-term implications of current code state

Be specific, actionable, and focus on helping the development team make informed decisions."""
        
        response = self._make_api_request(prompt)
        return response if response else "Unable to generate detailed analysis due to AI service unavailability."
    
    def _extract_high_priority_recommendations(self, all_recommendations: List[str], 
                                             critical_issues: List[ReviewFinding]) -> List[str]:
        """Extract and prioritize the most important recommendations."""
        
        high_priority = []
        
        # Add recommendations for critical issues
        for issue in critical_issues:
            if issue.suggestion:
                high_priority.append(f"CRITICAL: {issue.suggestion}")
        
        # Use keyword-based prioritization for other recommendations
        priority_keywords = [
            'security', 'vulnerability', 'critical', 'fix immediately',
            'performance', 'bottleneck', 'memory leak', 'sql injection',
            'xss', 'authentication', 'authorization'
        ]
        
        for rec in all_recommendations:
            if any(keyword in rec.lower() for keyword in priority_keywords):
                if rec not in high_priority:
                    high_priority.append(rec)
        
        return high_priority[:10]  # Limit to top 10
    
    def _generate_executive_summary(self, agent_reviews: List[AgentReview], 
                                   overall_score: int, critical_count: int) -> str:
        """Generate an executive summary of the consolidated review."""
        
        agent_names = [review.agent_type.replace('_', ' ').title() for review in agent_reviews]
        agent_list = ', '.join(agent_names)
        
        if overall_score >= 8:
            quality_assessment = "excellent"
        elif overall_score >= 6:
            quality_assessment = "good"
        elif overall_score >= 4:
            quality_assessment = "acceptable"
        else:
            quality_assessment = "needs improvement"
        
        critical_text = ""
        if critical_count > 0:
            critical_text = f" However, {critical_count} critical issue{'s' if critical_count != 1 else ''} require immediate attention."
        
        return f"""Code review completed by {len(agent_reviews)} specialized agents: {agent_list}. 
Overall code quality is {quality_assessment} with a score of {overall_score}/10.{critical_text} 
Review covers security, performance, coding practices, architecture, readability, and testability aspects."""
    
    def generate_report(self, consolidated_review: ConsolidatedReview, 
                       format_type: str = "json") -> str:
        """Generate a report of the consolidated review."""
        if format_type == "json_issues_markdown":
            return self._generate_json_issues_markdown(consolidated_review)
        else:
            return self._generate_json_report(consolidated_review)
    
    
    def _generate_json_report(self, review: ConsolidatedReview) -> str:
        """Generate a JSON format report."""
        # Convert dataclass to dict, handling nested objects
        def serialize_finding(finding):
            return {
                'agent_type': finding.agent_type,
                'severity': finding.severity.value,
                'title': finding.title,
                'description': finding.description,
                'line_number': finding.line_number,
                'code_snippet': finding.code_snippet,
                'suggestion': finding.suggestion,
                'category': finding.category
            }
        
        def serialize_agent_review(agent_review):
            return {
                'agent_name': agent_review.agent_name,
                'agent_type': agent_review.agent_type,
                'overall_score': agent_review.overall_score,
                'summary': agent_review.summary,
                'findings': [serialize_finding(f) for f in agent_review.findings],
                'recommendations': agent_review.recommendations
            }
        
        report_dict = {
            'overall_score': review.overall_score,
            'summary': review.summary,
            'agent_reviews': [serialize_agent_review(ar) for ar in review.agent_reviews],
            'critical_issues': [serialize_finding(ci) for ci in review.critical_issues],
            'high_priority_recommendations': review.high_priority_recommendations,
            'findings_by_category': {
                k: [serialize_finding(f) for f in v] 
                for k, v in review.findings_by_category.items()
            },
            'severity_distribution': review.severity_distribution,
            'detailed_analysis': review.detailed_analysis
        }
        
        return json.dumps(report_dict, indent=2, ensure_ascii=False)
    
    def _generate_json_issues_markdown(self, review: ConsolidatedReview) -> str:
        """Generate a JSON list of review comments in the specified format."""
        review_comments = []
        
        # Extract file path from the first agent review if available
        file_path = "unknown_file"
        
        # Process each agent review to extract line-specific feedback
        for agent_review in review.agent_reviews:
            agent_name = agent_review.agent_type.replace('_', ' ').title()
            
            # Parse the agent summary to extract line-specific issues
            summary_lines = agent_review.summary.split('\n')
            
            for line in summary_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for line-specific issues or general feedback
                line_number = None
                review_comment = ""
                
                # Try to extract line numbers from the summary
                import re
                line_match = re.search(r'line\s*(\d+)', line, re.IGNORECASE)
                if line_match:
                    line_number = int(line_match.group(1))
                
                # Generate review comment based on agent type and content
                if any(keyword in line.lower() for keyword in ['issue:', 'problem:', 'vulnerability:', 'warning:', 'concern:']):
                    # Extract the main issue
                    review_comment = line
                    
                    # Add specific suggestions based on agent type
                    if agent_review.agent_type == 'security':
                        if 'sql injection' in line.lower():
                            review_comment += " Use parameterized queries instead of string concatenation."
                        elif 'xss' in line.lower():
                            review_comment += " Sanitize user input and use proper encoding."
                        elif 'input validation' in line.lower():
                            review_comment += " Add proper input validation and sanitization."
                    
                    elif agent_review.agent_type == 'performance':
                        if 'loop' in line.lower():
                            review_comment += " Consider using modern array methods like filter(), map(), or reduce()."
                        elif 'inefficient' in line.lower():
                            review_comment += " Optimize this operation for better performance."
                    
                    elif agent_review.agent_type == 'coding_practices':
                        if 'var' in line.lower():
                            review_comment += " Use 'const' or 'let' instead of 'var'."
                        elif '==' in line.lower():
                            review_comment += " Use strict equality (===) instead of loose equality (==)."
                
                # If we found a meaningful comment, add it to the list
                if review_comment:
                    comment_obj = {
                        "file_path": file_path,
                        "line_number": line_number,
                        "review_comment": review_comment
                    }
                    review_comments.append(comment_obj)
        
        # If no specific line comments found, create general feedback
        if not review_comments:
            for agent_review in review.agent_reviews:
                # Create a general review comment from the summary
                summary_excerpt = agent_review.summary[:200].replace('\n', ' ').strip()
                if summary_excerpt:
                    comment_obj = {
                        "file_path": file_path,
                        "line_number": None,
                        "review_comment": f"{agent_review.agent_type.replace('_', ' ').title()}: {summary_excerpt}..."
                    }
                    review_comments.append(comment_obj)
        
        # Return as JSON array
        return json.dumps(review_comments, indent=2, ensure_ascii=False)
    
    def _extract_file_paths_from_diff(self, review: ConsolidatedReview) -> List[str]:
        """Extract file paths from the diff content in the review."""
        import re
        
        print("🔍 Starting file path extraction from diff content")
        
        # Try to get the original diff content from the first agent review
        if review.agent_reviews:
            print(f"📋 Found {len(review.agent_reviews)} agent reviews to check for diff content")
            
            # Look for diff content in the agent summaries
            for i, agent_review in enumerate(review.agent_reviews):
                summary = agent_review.summary
                print(f"🔍 Checking agent review {i+1} ({agent_review.agent_type}) for diff content")
                print(f"📏 Summary length: {len(summary)} characters")
                
                # Log first 500 characters of summary for debugging
                summary_preview = summary[:500] + "..." if len(summary) > 500 else summary
                print(f"📄 Summary preview: {summary_preview}")
                
                # Look for diff headers like "diff --git a/file.js b/file.js"
                diff_pattern = r'diff --git a/([^\s]+) b/([^\s]+)'
                matches = re.findall(diff_pattern, summary)
                print(f"🎯 Found {len(matches)} diff pattern matches: {matches}")
                
                if matches:
                    # Extract unique file paths
                    file_paths = set()
                    for old_path, new_path in matches:
                        file_paths.add(new_path)  # Use the new path (after changes)
                    extracted_files = list(file_paths)
                    print(f"✅ Extracted file paths from diff pattern: {extracted_files}")
                    return extracted_files
                
                # Also look for "+++ b/filename" patterns
                plus_pattern = r'\+\+\+ b/([^\s\n]+)'
                plus_matches = re.findall(plus_pattern, summary)
                print(f"🎯 Found {len(plus_matches)} plus pattern matches: {plus_matches}")
                
                if plus_matches:
                    extracted_files = list(set(plus_matches))
                    print(f"✅ Extracted file paths from plus pattern: {extracted_files}")
                    return extracted_files
        else:
            print("⚠️ No agent reviews found in consolidated review")
        
        print("❌ No file paths extracted from diff content")
        return []
    
    def generate_json_review_comments(self, review: ConsolidatedReview, file_path: str, extracted_files: List[str] = None) -> str:
        """Generate JSON review comments using AI to format properly."""
        
        print(f"🚀 generate_json_review_comments called with file_path: '{file_path}'")
        
        # Use provided extracted files or try to extract from review
        if extracted_files is None:
            extracted_files = self._extract_file_paths_from_diff(review)
        print(f"📁 Extracted files: {extracted_files}")
        
        # Prepare all agent findings for the consolidation agent
        agent_summaries = []
        for agent_review in review.agent_reviews:
            agent_summaries.append(f"""
**{agent_review.agent_type.replace('_', ' ').title()} Agent Review:**
{agent_review.summary}

**Recommendations:**
{chr(10).join([f"- {rec}" for rec in agent_review.recommendations])}
""")
        
        REVIEW_GOAL = """**Goal:**
Review each hunk of diff and agent feedback
    - If there is any feedback for that hunk: Provide crisp feedback with line numbers and suggest the change to be made.
    - If there is no feedback for that hunk: Ignore and move on the next hunk.
    - Do not provide a highly verbose review, so that its not overwhelming for the user to read.
"""

        OUTPUT_FORMAT = """
CRITICAL: Your response must be ONLY a valid JSON array. Do not include any other text, explanations, or markdown formatting.

Output format (return ONLY this JSON, nothing else):
[
    {
        "file_path": "filename.js",
        "line_number": 10,
        "review_comment": "Specific issue description and suggested fix"
    }
]

If no issues found, return: []
"""
        
        # Create file context for the prompt
        file_context = ""
        if extracted_files:
            file_context = f"\nFiles in this diff: {', '.join(extracted_files)}\n"
        else:
            file_context = f"\nFile being reviewed: {file_path}\n"
        
        prompt = f"""{REVIEW_GOAL}

{OUTPUT_FORMAT}

Agent Reviews to Consolidate:
{chr(10).join(agent_summaries)}
{file_context}

CRITICAL CONSOLIDATION INSTRUCTIONS:
1. ANALYZE ALL AGENT FEEDBACK thoroughly - do not miss any issues mentioned by any agent
2. DEDUPLICATE similar findings: If multiple agents mention the same issue on the same line or similar lines, consolidate them into ONE comprehensive review comment
3. PRIORITIZE the most actionable and specific feedback
4. COMBINE related issues: If agents mention related problems (e.g., "input validation" from security and "parameter validation" from coding practices), merge them into one comprehensive comment
5. FOCUS on unique, distinct issues - ensure ALL different types of issues are captured
6. Extract specific line numbers where mentioned and create crisp, actionable review comments
7. BE COMPREHENSIVE: If agents found multiple different issues, ensure ALL are included in the final output

QUALITY REQUIREMENTS:
- NEVER ignore or skip issues mentioned by agents
- ALWAYS provide COMPLETE review comments with specific code suggestions
- NEVER use placeholder text like "(Recommendation details not provided)" or truncate responses
- Each review_comment must be fully detailed and actionable with specific fix suggestions
- If multiple agents found different issues on different lines, include ALL of them

Please consolidate these agent reviews into the JSON format specified above, ensuring NO DUPLICATE issues for the same line but INCLUDING ALL DISTINCT ISSUES found by any agent."""

        try:
            # Prepare messages for chat completion with JSON formatting instructions
            messages = [
                {
                    "role": "system", 
                    "content": f"You are a senior technical lead consolidating code review reports. {REVIEW_GOAL}\n\n{OUTPUT_FORMAT}"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Make request through the LLM client with retry logic
            import json
            max_retries = 2
            response = None
            
            for attempt in range(max_retries + 1):
                try:
                    response = self.llm_client.chat_completion(
                        messages=messages,
                        temperature=0.2,  # Slightly higher for more diverse responses
                        max_tokens=4000  # Reduced to avoid model limits
                    )
                    if response and response.strip():
                        break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries:
                        logger.error(f"All {max_retries + 1} attempts failed")
                        return "[]"
            
            if response:
                print(f"🤖 AI response received: {response[:500]}...")
                
                # Try to parse and validate the JSON
                try:
                    parsed_json = json.loads(response.strip())
                    print(f"✅ Successfully parsed JSON with {len(parsed_json)} items")
                    
                    if isinstance(parsed_json, list):
                        # Update file paths to actual files from diff
                        for i, item in enumerate(parsed_json):
                            if isinstance(item, dict):
                                original_file_path = item.get('file_path', 'unknown')
                                print(f"📝 Item {i+1} original file_path: '{original_file_path}'")
                                
                                # If we have extracted files, try to match the comment to the right file
                                if extracted_files:
                                    # Try to match based on line number or use round-robin distribution
                                    original_file_path = item.get('file_path', 'unknown')
                                    
                                    # If the AI already set a reasonable file path, keep it
                                    if original_file_path != 'unknown' and any(extracted_file in original_file_path for extracted_file in extracted_files):
                                        new_file_path = original_file_path
                                        print(f"🔄 Item {i+1} keeping AI-set file_path: '{new_file_path}'")
                                    else:
                                        # Use round-robin distribution across extracted files
                                        file_index = i % len(extracted_files)
                                        new_file_path = extracted_files[file_index]
                                        print(f"🔄 Item {i+1} distributed to file: '{new_file_path}' (index {file_index})")
                                    
                                    item['file_path'] = new_file_path
                                else:
                                    item['file_path'] = file_path
                                    print(f"🔄 Item {i+1} set file_path to fallback: '{file_path}'")
                        
                        final_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                        print(f"📤 Final JSON output: {final_json}")
                        return final_json
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract JSON from markdown blocks
                    import re
                    json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
                    if not json_match:
                        json_match = re.search(r'(\[.*?\])', response, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(1)
                        try:
                            parsed_json = json.loads(json_str)
                            if isinstance(parsed_json, list):
                                for i, item in enumerate(parsed_json):
                                    if isinstance(item, dict):
                                        # If we have extracted files, use them
                                        if extracted_files:
                                            # Use round-robin distribution across extracted files
                                            file_index = i % len(extracted_files)
                                            item['file_path'] = extracted_files[file_index]
                                        else:
                                            item['file_path'] = file_path
                                return json.dumps(parsed_json, indent=2, ensure_ascii=False)
                        except json.JSONDecodeError:
                            pass
                
                # Fallback: return empty array if parsing fails
                return json.dumps([], indent=2, ensure_ascii=False)
            else:
                return json.dumps([], indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error generating JSON review comments: {e}")
            return json.dumps([], indent=2, ensure_ascii=False)
