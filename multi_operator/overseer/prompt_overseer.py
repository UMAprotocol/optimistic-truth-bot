#!/usr/bin/env python3
"""
Prompt creation utilities for ChatGPT overseer in the UMA Multi-Operator System.

This module provides the system prompt for the ChatGPT overseer to validate
responses from solvers and determine if they are accurate or need refinement.
"""

from datetime import datetime, timezone
import time


def get_overseer_prompt(
    user_prompt,
    system_prompt,
    solver_response,
    recommendation,
    attempt=1,
    market_price_info=None,
    solver_name="perplexity",
):
    """
    Generate the prompt for the ChatGPT overseer based on the solver response.

    Args:
        user_prompt: The original user prompt
        system_prompt: The system prompt used for the solver
        solver_response: The response from the solver
        recommendation: The recommendation extracted from the solver (p1, p2, p3, p4)
        attempt: The current attempt number
        market_price_info: Optional market price information from Polymarket
        solver_name: The name of the solver that produced the response
    """
    market_price_section = ""
    if market_price_info:
        market_price_section = f"""
MARKET PRICE INFORMATION:
{market_price_info}

IMPORTANT MARKET PRICE CONSIDERATION:
The above market price is a leading indicator from Polymarket for this prediction market. This reflects what market participants collectively believe about the outcome. A high price (close to 1.0) for a YES token indicates strong market confidence in YES outcome, while a high price for a NO token indicates strong confidence in NO outcome. This market signal should be considered a very strong indicator for correctness.

If the solver's recommendation aligns with market sentiment (e.g., p2/YES when YES token price is high), this strengthens confidence in the recommendation. If they conflict (e.g., p1/NO when YES token price is high), this should trigger more scrutiny and likely warrant a retry. In conflicting cases, the market price should be heavily weighted in your evaluation.

RULE: If the solver's recommendation conflicts with strong market signals (>0.85 confidence in one direction), you should almost always select RETRY.
"""

    prompt = f"""You are an expert overseer evaluating the quality and accuracy of a {solver_name} response for UMA's optimistic oracle system. 

Your task is to:
1. Critically evaluate the {solver_name} response for accuracy, completeness, and adherence to the system prompt instructions
2. Determine if the response is satisfactory or needs improvement
3. Make a clear decision on how to proceed

Here is the content you need to evaluate:

USER PROMPT:
{user_prompt}

SYSTEM PROMPT:
{system_prompt}

{solver_name.upper()} RESPONSE:
{solver_response}

{solver_name.upper()} RECOMMENDATION: {recommendation}
CURRENT ATTEMPT: {attempt}
{market_price_section}

Please perform a detailed evaluation, analyzing:
- Factual accuracy and adherence to instructions
- Logical reasoning and completeness
- Verification of event and alignment of recommendation with facts
- Any missing information, bias, or errors in the response
- Alignment with market price signals (when available)

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

Note that the result should NEVER be p3. if the solver returns p3, you MUST return RETRY or DEFAULT_TO_P4 and under no circumstances should you return p3 as this is ambiguous and could lead to incorrect resolutions: either P1 or P2 could be correct or not sure yet via P4.

EXTRA THINGS TO CONSIDER:
- Ensure that if the user prompt relates to a particular source that the solver is using the correct source
- Ensure that if the user prompt contains updates, the solver is using the updates to update its analysis and resolution and is factoring them heavily into its recommendation
- The solver can often be bad at identifying "how many times did x get mentioned" or "how many times did y say z" etc - be sure to verify that the reasoning is using the correct source
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
                    output += f"Market STRONGLY favors {high_token.get('outcome')} outcome ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                elif high_price > 0.65:
                    output += f"Market moderately favors {high_token.get('outcome')} outcome ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                elif high_price >= 0.5:
                    output += f"Market slightly favors {high_token.get('outcome')}, but not decisively ({high_price:.3f} vs {low_price:.3f})"
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
                        if high_price > 0.85:
                            output += f"Market STRONGLY favors {high_token.get('outcome')} outcome ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                        elif high_price > 0.65:
                            output += f"Market moderately favors {high_token.get('outcome')} outcome ({high_price:.3f} = {high_price*100:.1f}% confidence)"
                        elif high_price > 0.5:
                            output += f"Market shows some preference for {high_token.get('outcome')}, but not decisively ({high_price:.3f})"
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
