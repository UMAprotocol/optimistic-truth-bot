#!/usr/bin/env python3
"""
Prompt creation utilities for ChatGPT overseer in the UMA Proposal Replayer.

This module provides the system prompt for the ChatGPT overseer to validate
responses from Perplexity and determine if they are accurate or need refinement.
"""

from datetime import datetime, timezone
import time


def get_overseer_prompt(
    user_prompt, system_prompt, perplexity_response, recommendation, attempt=1
):
    """
    Generate the prompt for the ChatGPT overseer based on the Perplexity response.
    """
    prompt = f"""You are an expert overseer evaluating the quality and accuracy of a Perplexity AI oracle response for UMA's optimistic oracle system. 

Your task is to:
1. Critically evaluate the Perplexity response for accuracy, completeness, and adherence to the system prompt instructions
2. Determine if the response is satisfactory or needs improvement
3. Make a clear decision on how to proceed

Here is the content you need to evaluate:

USER PROMPT:
{user_prompt}

SYSTEM PROMPT:
{system_prompt}

PERPLEXITY RESPONSE:
{perplexity_response}

PERPLEXITY RECOMMENDATION: {recommendation}
CURRENT ATTEMPT: {attempt}

Please perform a detailed evaluation, analyzing:
- Factual accuracy and adherence to instructions
- Logical reasoning and completeness
- Verification of event and alignment of recommendation with facts
- Any missing information, bias, or errors in the response

IMPORTANT: Use plain text in your response. Do not use markdown formatting, bold, italics, bullet points or other formatting. Your response should be simple plain text without any formatting.

CRITICAL RULE: If this is the first attempt AND the recommendation is p4, you MUST ALWAYS choose RETRY. It is never acceptable to return p4 on the first attempt - we must always try at least one more time with improved search strategies.

After your evaluation, you MUST provide a decision in a specific format at the end of your response:

```decision
{{
  "verdict": "[SATISFIED or RETRY or DEFAULT_TO_P4]",
  "require_rerun": [true or false],
  "reason": "Brief explanation of your decision",
  "critique": "Specific feedback about the response quality",
  "prompt_update": "Optional updated system prompt to use for the next attempt if require_rerun is true"
}}
```

Where:
- SATISFIED: The response is accurate and can be used confidently.
- RETRY: The response has issues but could be improved with another attempt.
- DEFAULT_TO_P4: The query cannot be resolved confidently and should default to p4.
- require_rerun: Must be true for RETRY, typically false for SATISFIED, and can be true or false for DEFAULT_TO_P4.
- prompt_update: For RETRY, provide ONLY the specific refinements or additional instructions needed, not a complete system prompt replacement. Only provide a full system prompt replacement if you believe the entire prompt structure needs to be changed.

IMPORTANT: When providing a prompt_update, focus on specific refinements and additions that would help improve the response. DO NOT rewrite the entire system prompt unless absolutely necessary. Your refinements will be appended to the existing system prompt, not replace it.

Be extremely critical and cautious. The response must be highly accurate and reliable. When in doubt, recommend DEFAULT_TO_P4 or RETRY with specific improvements.

Remember: First attempt p4 recommendations MUST always get a RETRY verdict with require_rerun=true.

EXTRA THINGS TO CONSIDER:
- Ensure that if the user prompt relates to a particular source that perplexity is using the correct source
- Ensure that if the user prompt contains updates, perplexity is using the updates to update its analysis and resolution and is factoring them heavily into its recommendation
- Perplexity can often be bad at identifying "how many times did x get mentioned" or "how many times did y say z" etc - be sure to verify that the reasoning is using the correct source
"""
    return prompt


# Simple function to get a system-only prompt when needed
def get_base_system_prompt():
    """
    Get a simplified system-only prompt for the ChatGPT overseer.

    Returns:
        str: A simplified system prompt for the ChatGPT overseer
    """
    return """You are an expert overseer AI tasked with critically evaluating responses from another AI (Perplexity) that resolves UMA optimistic oracle requests. Your primary goal is to ensure high accuracy and prevent incorrect outputs by providing an independent verification layer. Always default to p4 when uncertain, as incorrect answers can have severe consequences."""
