#!/usr/bin/env python3
"""
Prompt creation utilities for ChatGPT overseer in the UMA Multi-Operator System.

This module provides the system prompt for the ChatGPT overseer to validate
responses from solvers and determine if they are accurate or need refinement.
"""

from datetime import datetime, timezone
import time
import re
from typing import Optional, List, Dict, Any
import re  # Make sure regex module is imported


def get_overseer_prompt(
    user_prompt: str,
    system_prompt: str,
    solver_response: str,
    recommendation: str,
    attempt: int = 1,
    market_price_info: Optional[str] = None,
    solver_name: str = "perplexity",
) -> str:
    """
    Generate the overseer prompt for ChatGPT to evaluate a solver response.

    Args:
        user_prompt: The original user prompt
        system_prompt: The system prompt used for the solver
        solver_response: The response from the solver
        recommendation: The recommendation from the solver (p1, p2, p3, p4)
        attempt: The current attempt number
        market_price_info: Optional market price information
        solver_name: The name of the solver that produced the response

    Returns:
        The overseer prompt for ChatGPT
    """
    prompt = f"""You are a UMA optimistic oracle overseer AI, responsible for evaluating responses for UMA's optimistic oracle system.

The response you are evaluating came from the {solver_name} solver, attempt {attempt}.

Your task is to determine whether the response is sufficient to provide a definitive recommendation for the query. You will also provide a critique of the response and suggest improvements if necessary.

ORIGINAL QUERY:
{user_prompt}

SYSTEM PROMPT:
{system_prompt}

RESPONSE FROM {solver_name.upper()} SOLVER:
{solver_response}

RECOMMENDATION FROM SOLVER: {recommendation}

"""

    # Add market price information if available
    if market_price_info:
        prompt += f"""
MARKET PRICE INFORMATION:
{market_price_info}

"""
    else:
        prompt += """
NOTE: No market price information is available for this query. In your evaluation, explicitly state that you are making your assessment without market price data.

"""

    # Add specific evaluation criteria for code_runner
    if "code_runner" in solver_name.lower():
        # Extract code from solver response for more precise validation
        code_block = None
        if "```" in solver_response:
            code_blocks = re.findall(r'```(?:python)?(.*?)```', solver_response, re.DOTALL)
            if code_blocks:
                code_block = code_blocks[0].strip()
        
        # Extract dates from the market description for verification
        dates_in_description = []
        # Look for dates in various formats
        date_patterns = [
            r'(\d{2}\s+[A-Za-z]{3}\s+[\']?\d{2})', # 03 Apr '25
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',      # 3 April 2025
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',    # April 3, 2025
            r'(\d{4}-\d{2}-\d{2})'                 # 2025-04-03
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, user_prompt)
            dates_in_description.extend(matches)
        
        # Compare with code output
        dates_in_output = []
        if "BTC price on" in solver_response or "price on" in solver_response:
            date_output_patterns = re.findall(r'(?:BTC|ETH|price) (?:price )?on (\d{4}-\d{2}-\d{2})', solver_response)
            dates_in_output.extend(date_output_patterns)
        
        date_validation_info = ""
        if dates_in_description and dates_in_output:
            date_validation_info = f"""
DATES IN MARKET DESCRIPTION: {', '.join(dates_in_description)}
DATES IN CODE OUTPUT: {', '.join(dates_in_output)}

You must verify that these dates match conceptually (e.g., "03 Apr '25" should correspond to "2025-04-03").
"""
        
        prompt += f"""
ADDITIONAL CODE EVALUATION CRITERIA:
For code runner solutions, please evaluate:
1. Whether the code correctly extracts and interprets the data needed from APIs
2. Whether the logic for determining the recommendation is correct
3. If the code handles edge cases and errors appropriately
4. If the API calls and data processing approach are sensible
5. Whether the code correctly maps outcomes to recommendation codes (p1, p2, p3, p4)
6. CRITICAL: Whether dates and times in the code match those specified in the market description exactly (pay close attention to date formats, timezones, and potential month/day swaps)
7. CRITICAL: Whether the code outputs align with the expected results based on the market description (check for any discrepancies between output values and what should be expected)

IMPORTANT: Be particularly vigilant about date-related errors. Check if the dates in the code output match exactly those mentioned in the market description. If there's any date mismatch (e.g., using March instead of April, or 2024 instead of 2025), this is an immediate FAILURE that requires a retry.
{date_validation_info}
VALIDATION REQUIREMENT: You MUST closely check any dates in the code output against those mentioned in the market description. If you detect ANY discrepancy (wrong month, wrong year, wrong day), you MUST return verdict "RETRY" and explicitly mention the date error in your critique.

Your critique should focus both on the code correctness AND whether the final recommendation is justified by the data.
"""

    prompt += """
Please evaluate this response and recommendation according to the following criteria:
1. Is the information provided accurate and relevant to the query?
2. Is there sufficient information to make a definitive recommendation?
3. Is the recommendation (p1, p2, p3, p4) consistent with the information provided?
4. Does the response answer all aspects of the query?
5. Are there any notable omissions or errors in the response?
6. CRITICALLY IMPORTANT: Does the recommendation align with market sentiment? If there is a STRONG market sentiment (>85% confidence) that contradicts the solver's recommendation, this is a serious issue requiring immediate action.

Based on your evaluation, determine one of the following verdicts:
- SATISFIED: The response is accurate and complete, and the recommendation is justified.
- RETRY: The response needs improvement or contains inaccuracies that should be addressed.
- DEFAULT_TO_P4: The response quality is unsatisfactory, and the system should default to a p4 recommendation.

Special Market Alignment Rule:
VERY IMPORTANT: When checking market alignment, you MUST carefully consider the resolution conditions mapping first. For example, if "p1 corresponds to Texas Rangers", then a recommendation of "p1" means Texas Rangers wins, and you should check if this aligns with market sentiment for Texas Rangers, NOT by the p1 label itself.

If you are provided with resolution conditions that map p1, p2, p3 to specific outcomes, you must use those mappings when determining if the recommendation aligns with market sentiment.

Only after correctly interpreting the recommendation through resolution conditions mapping, if the market STRONGLY favors a specific outcome (>85% confidence) but the solver recommendation contradicts this without compelling evidence, you MUST:
1. Set verdict to DEFAULT_TO_P4
2. Explicitly note this market/solver disagreement in your critique
3. In prompt_update, suggest trying a different solver because the current one is producing results that conflict with strong market signals

IMPORTANT: Return your evaluation in a specific format:
```decision
{
  "verdict": "SATISFIED/RETRY/DEFAULT_TO_P4",
  "require_rerun": true/false,
  "reason": "Brief explanation of your verdict",
  "critique": "Detailed critique of the response",
  "market_alignment": "Statement about whether the recommendation aligns with market data or a note about the absence of market data",
  "prompt_update": "Optional additional instructions for a rerun"
}
```

Where:
- verdict: Your verdict (SATISFIED, RETRY, or DEFAULT_TO_P4)
- require_rerun: Boolean indicating whether another attempt should be made
- reason: Brief explanation of your verdict (1-2 sentences)
- critique: Detailed critique of the response, including strengths and weaknesses
- market_alignment: REQUIRED field explaining alignment with market data or noting its absence
- prompt_update: Additional instructions to include in the prompt for a rerun (leave empty if not needed)

IMPORTANT: You MUST include the market_alignment field in your decision, even if market data is not available. In that case, state explicitly that your assessment does not include market data considerations.

Remember, your goal is to ensure that UMA token holders receive accurate and well-reasoned recommendations for their queries.
"""

    return prompt


# Simple function to get a system-only prompt when needed
def get_base_system_prompt():
    """
    Get a simplified system-only prompt for the ChatGPT overseer.

    Returns:
        str: A simplified system prompt for the ChatGPT overseer
    """
    return """You are an expert overseer AI tasked with critically evaluating responses from other AI solvers that resolve UMA optimistic oracle requests. Your primary goal is to ensure high accuracy and prevent incorrect outputs by providing an independent verification layer. Always default to p4 when uncertain, as incorrect answers can have severe consequences."""


def format_market_price_info(tokens):
    """
    Format market price information from tokens for inclusion in the overseer prompt.

    Args:
        tokens: A list of token objects containing price information

    Returns:
        str: Formatted string with market price information
    """
    if not tokens or not isinstance(tokens, list):
        return None

    output = "Token Prices from Polymarket:\n"
    
    # Try to extract resolution conditions from proposal metadata for proper p1/p2/p3 mapping
    resolution_conditions = ""
    res_p1_outcome = ""
    res_p2_outcome = ""
    
    # First try to get from the first token if it has metadata or resolution_conditions
    if len(tokens) > 0:
        if isinstance(tokens[0], dict):
            if "resolution_conditions" in tokens[0]:
                resolution_conditions = tokens[0]["resolution_conditions"]
            elif tokens[0].get("metadata", {}) and isinstance(tokens[0]["metadata"], dict):
                resolution_conditions = tokens[0]["metadata"].get("resolution_conditions", "")
                
    # If no resolution conditions found in tokens, look at the parent object
    if not resolution_conditions:
        try:
            if hasattr(tokens, "proposal_metadata") and tokens.proposal_metadata:
                resolution_conditions = tokens.proposal_metadata.get("resolution_conditions", "")
        except Exception:
            pass
    
    # Extract p1/p2 outcomes from resolution conditions if available
    if resolution_conditions:
        # Look for patterns like "p1 corresponds to X" or "p1 to X"
        p1_patterns = [
            r'p1\s+corresponds\s+to\s+([\w\s]+)',
            r'p1\s+to\s+([\w\s]+)',
            r'p1[:\s]+([^,\.]+)'
        ]
        
        p2_patterns = [
            r'p2\s+corresponds\s+to\s+([\w\s]+)',
            r'p2\s+to\s+([\w\s]+)',
            r'p2[:\s]+([^,\.]+)'
        ]
        
        # Try each pattern
        for pattern in p1_patterns:
            match = re.search(pattern, resolution_conditions)
            if match:
                res_p1_outcome = match.group(1).strip()
                break
                
        for pattern in p2_patterns:
            match = re.search(pattern, resolution_conditions)
            if match:
                res_p2_outcome = match.group(1).strip()
                break

    # Helper function to safely convert price to float
    def safe_float(price, default=0.0):
        if price is None:
            return default
        try:
            return float(price)
        except (TypeError, ValueError):
            return default

    for token in tokens:
        outcome = token.get("outcome", "Unknown")
        price = token.get("price")
        price_str = str(price) if price is not None else "Unknown"
        token_id = token.get("token_id", "Unknown")
        winner = "Yes" if token.get("winner", False) else "No"

        output += f"- Token: {outcome}, Price: {price_str}, ID: {token_id}, Winner: {winner}\n"

    # Add resolution conditions mapping if available
    if resolution_conditions:
        output += f"\nResolution Conditions: {resolution_conditions}\n"
        
        if res_p1_outcome and res_p2_outcome:
            output += f"Resolution mapping: p1 = {res_p1_outcome}, p2 = {res_p2_outcome}\n"
    
    output += "\nInterpretation: "

    # Check if we have winner information but null prices
    winner_token = next((t for t in tokens if t.get("winner", False) is True), None)
    all_prices_null = all(t.get("price") is None for t in tokens)

    if winner_token and all_prices_null:
        output += (
            f"Market outcome is determined: {winner_token.get('outcome')} is the WINNER"
        )
        return output

    # First check for YES/NO tokens
    yes_token = next((t for t in tokens if t.get("outcome", "").upper() == "YES"), None)
    no_token = next((t for t in tokens if t.get("outcome", "").upper() == "NO"), None)

    if yes_token and no_token:
        yes_price = safe_float(yes_token.get("price"))
        no_price = safe_float(no_token.get("price"))

        if yes_price > 0.85:
            output += f"Market STRONGLY favors YES outcome ({yes_price:.3f} = {yes_price*100:.1f}% confidence)"
        elif no_price > 0.85:
            output += f"Market STRONGLY favors NO outcome ({no_price:.3f} = {no_price*100:.1f}% confidence)"
        elif yes_price > 0.65:
            output += f"Market moderately favors YES outcome ({yes_price:.3f} = {yes_price*100:.1f}% confidence)"
        elif no_price > 0.65:
            output += f"Market moderately favors NO outcome ({no_price:.3f} = {no_price*100:.1f}% confidence)"
        else:
            output += f"Market is relatively uncertain (YES: {yes_price:.3f}, NO: {no_price:.3f})"
    elif yes_token:
        yes_price = safe_float(yes_token.get("price"))
        if yes_price > 0.85:
            output += f"Market STRONGLY favors YES outcome ({yes_price:.3f} = {yes_price*100:.1f}% confidence)"
        elif yes_price > 0.65:
            output += f"Market moderately favors YES outcome ({yes_price:.3f} = {yes_price*100:.1f}% confidence)"
        else:
            output += f"Market shows some preference for YES, but not decisively ({yes_price:.3f} = {yes_price*100:.1f}% confidence)"
    elif no_token:
        no_price = safe_float(no_token.get("price"))
        if no_price > 0.85:
            output += f"Market STRONGLY favors NO outcome ({no_price:.3f} = {no_price*100:.1f}% confidence)"
        elif no_price > 0.65:
            output += f"Market moderately favors NO outcome ({no_price:.3f} = {no_price*100:.1f}% confidence)"
        else:
            output += f"Market shows some preference for NO, but not decisively ({no_price:.3f} = {no_price*100:.1f}% confidence)"
    else:
        # Handle binary markets with arbitrary token names (non YES/NO)
        if len(tokens) == 2:
            # First check if we have a clear winner but prices are null
            winner = next((t for t in tokens if t.get("winner", False) is True), None)
            if winner and all(t.get("price") is None for t in tokens):
                output += f"Market outcome is determined: {winner.get('outcome')} is the WINNER"
            else:
                # Get the token with the highest price
                sorted_tokens = sorted(
                    tokens, key=lambda t: safe_float(t.get("price")), reverse=True
                )
                high_token = sorted_tokens[0]
                low_token = sorted_tokens[1]

                high_price = safe_float(high_token.get("price"))
                low_price = safe_float(low_token.get("price"))

                # Check for winner information if prices are too close
                winner = next(
                    (t for t in tokens if t.get("winner", False) is True), None
                )
                if winner and high_price < 0.6:
                    output += f"Market outcome is determined despite uncertain prices: {winner.get('outcome')} is the WINNER"
                elif high_price > 0.85:
                    high_outcome = high_token.get('outcome')
                    
                    # Check if there's a mapping between outcomes and p1/p2
                    outcome_mapping = ""
                    if res_p1_outcome and high_outcome and res_p1_outcome in high_outcome:
                        outcome_mapping = f" (maps to p1 in resolution conditions)"
                    elif res_p2_outcome and high_outcome and res_p2_outcome in high_outcome:
                        outcome_mapping = f" (maps to p2 in resolution conditions)"
                        
                    output += f"Market STRONGLY favors {high_outcome} outcome{outcome_mapping} ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                elif high_price > 0.65:
                    high_outcome = high_token.get('outcome')
                    
                    # Check if there's a mapping between outcomes and p1/p2
                    outcome_mapping = ""
                    if res_p1_outcome and high_outcome and res_p1_outcome in high_outcome:
                        outcome_mapping = f" (maps to p1 in resolution conditions)"
                    elif res_p2_outcome and high_outcome and res_p2_outcome in high_outcome:
                        outcome_mapping = f" (maps to p2 in resolution conditions)"
                        
                    output += f"Market moderately favors {high_outcome} outcome{outcome_mapping} ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                elif high_price >= 0.5:
                    high_outcome = high_token.get('outcome')
                    
                    # Check if there's a mapping between outcomes and p1/p2
                    outcome_mapping = ""
                    if res_p1_outcome and high_outcome and res_p1_outcome in high_outcome:
                        outcome_mapping = f" (maps to p1 in resolution conditions)"
                    elif res_p2_outcome and high_outcome and res_p2_outcome in high_outcome:
                        outcome_mapping = f" (maps to p2 in resolution conditions)"
                        
                    output += f"Market slightly favors {high_outcome}{outcome_mapping}, but not decisively ({high_price:.3f} vs {low_price:.3f})"
                else:
                    # Check for winner information before declaring uncertainty
                    winner = next(
                        (t for t in tokens if t.get("winner", False) is True), None
                    )
                    if winner:
                        output += f"Market outcome is determined despite uncertain prices: {winner.get('outcome')} is the WINNER"
                    else:
                        output += f"Market is uncertain ({high_token.get('outcome')}: {high_price:.3f}, {low_token.get('outcome')}: {low_price:.3f})"
        else:
            # For markets with more than 2 tokens or single token
            # Check for winner information first
            winner = next((t for t in tokens if t.get("winner", False) is True), None)
            if winner:
                output += f"Market outcome is determined: {winner.get('outcome')} is the WINNER"
            else:
                # Use max with a key function that handles None values
                try:
                    high_token = max(
                        tokens, key=lambda t: safe_float(t.get("price")), default=None
                    )
                    if high_token:
                        high_price = safe_float(high_token.get("price"))
                        high_outcome = high_token.get('outcome')
                        
                        # Check if there's a mapping between outcomes and p1/p2
                        outcome_mapping = ""
                        if res_p1_outcome and high_outcome and res_p1_outcome in high_outcome:
                            outcome_mapping = f" (maps to p1 in resolution conditions)"
                        elif res_p2_outcome and high_outcome and res_p2_outcome in high_outcome:
                            outcome_mapping = f" (maps to p2 in resolution conditions)"
                            
                        if high_price > 0.85:
                            output += f"Market STRONGLY favors {high_outcome} outcome{outcome_mapping} ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                        elif high_price > 0.65:
                            output += f"Market moderately favors {high_outcome} outcome{outcome_mapping} ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                        elif high_price > 0.5:
                            output += f"Market shows some preference for {high_outcome}{outcome_mapping}, but not decisively ({high_price:.3f})"
                        else:
                            # Final check for winner
                            winner = next(
                                (t for t in tokens if t.get("winner", False) is True),
                                None,
                            )
                            if winner:
                                output += f"Market outcome is determined despite uncertain prices: {winner.get('outcome')} is the WINNER"
                            else:
                                output += "Insufficient market information to determine sentiment"
                    else:
                        # Check for winner as last resort
                        winner = next(
                            (t for t in tokens if t.get("winner", False) is True), None
                        )
                        if winner:
                            output += f"Market outcome is determined despite no price data: {winner.get('outcome')} is the WINNER"
                        else:
                            output += "No token with valid price information found"
                except (ValueError, TypeError):
                    # One last check for winner
                    winner = next(
                        (t for t in tokens if t.get("winner", False) is True), None
                    )
                    if winner:
                        output += f"Market outcome is determined despite price processing errors: {winner.get('outcome')} is the WINNER"
                    else:
                        output += "Error processing token prices - unable to determine market sentiment"

    return output