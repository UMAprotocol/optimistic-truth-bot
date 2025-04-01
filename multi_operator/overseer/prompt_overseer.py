#!/usr/bin/env python3
"""
Prompt creation utilities for ChatGPT overseer in the UMA Multi-Operator System.

This module provides the system prompt for the ChatGPT overseer to validate
responses from solvers and determine if they are accurate or need refinement.
"""

from datetime import datetime, timezone
import time
from typing import Optional


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
        prompt += """
ADDITIONAL CODE EVALUATION CRITERIA:
For code runner solutions, please evaluate:
1. Whether the code correctly extracts and interprets the data needed from APIs
2. Whether the logic for determining the recommendation is correct
3. If the code handles edge cases and errors appropriately
4. If the API calls and data processing approach are sensible
5. Whether the code correctly maps outcomes to recommendation codes (p1, p2, p3, p4)

Your critique should focus both on the code correctness AND whether the final recommendation is justified by the data.
"""

    prompt += """
Please evaluate this response and recommendation according to the following criteria:
1. Is the information provided accurate and relevant to the query?
2. Is there sufficient information to make a definitive recommendation?
3. Is the recommendation (p1, p2, p3, p4) consistent with the information provided?
4. Does the response answer all aspects of the query?
5. Are there any notable omissions or errors in the response?
6. IMPORTANT: Does the recommendation align with market sentiment? (Or explicitly note the absence of market data if none is available)

Based on your evaluation, determine one of the following verdicts:
- SATISFIED: The response is accurate and complete, and the recommendation is justified.
- RETRY: The response needs improvement or contains inaccuracies that should be addressed.
- DEFAULT_TO_P4: The response quality is unsatisfactory, and the system should default to a p4 recommendation.

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
