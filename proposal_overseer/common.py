#!/usr/bin/env python3
"""
Common utility functions for UMA Proposal Replayer with Perplexity-ChatGPT integration.
Handles API calls, response processing, and recommendation validation.
"""

import json
import re
import time
import threading
import sys
import logging
import os
from openai import OpenAI
from datetime import datetime
from pathlib import Path


def spinner_animation(stop_event, message="Processing"):
    """Display a spinner animation in the console while a process is running."""
    import itertools

    spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {next(spinner)} ")
        sys.stdout.flush()
        time.sleep(0.1)
    # Clear the spinner line when done
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()


def setup_logging(module_name, log_file):
    """Set up logging configuration for a module."""
    # Ensure the log file has a directory component
    log_path = (
        os.path.join("logs", log_file)
        if "/" not in log_file and "\\" not in log_file
        else log_file
    )

    # Ensure logs directory exists
    os.makedirs(
        os.path.dirname(log_path) if os.path.dirname(log_path) else "logs",
        exist_ok=True,
    )

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
        force=True,  # Ensure settings apply even if logging was configured elsewhere
    )

    # Create and return logger
    return logging.getLogger(module_name)


def query_perplexity(prompt, api_key, system_prompt=None, verbose=False):
    """
    Query the Perplexity API.

    Args:
        prompt (str): The user prompt content
        api_key (str): Perplexity API key
        system_prompt (str, optional): Custom system prompt to use
        verbose (bool): Whether to print verbose output

    Returns:
        API response object
    """
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if verbose:
        print("Sending request to Perplexity API...")
        print("Messages being sent to API:")
        for msg in messages:
            print(f"\nRole: {msg['role']}")
            print(f"Content:\n{msg['content']}\n")
            print("-" * 80)

    response = client.chat.completions.create(
        model="sonar-deep-research",
        messages=messages,
        temperature=0.0,
    )
    return response


def query_chatgpt(
    prompt, api_key, system_prompt=None, model="gpt-4-turbo", verbose=False
):
    """
    Query ChatGPT API.

    Args:
        prompt (str): The user prompt content
        api_key (str): OpenAI API key
        system_prompt (str, optional): Custom system prompt to use
        model (str): Model to use for the query
        verbose (bool): Whether to print verbose output

    Returns:
        API response object
    """
    client = OpenAI(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if verbose:
        print("Sending request to ChatGPT API...")
        print("Messages being sent to API:")
        for msg in messages:
            print(f"\nRole: {msg['role']}")
            print(f"Content:\n{msg['content']}\n")
            print("-" * 80)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
    )
    return response


def extract_recommendation(response_text):
    """Extract the recommendation (p1, p2, p3, p4) from the response text."""
    # Handle various formats including markdown, bold, parenthetical remarks
    patterns = [
        # Standard format: recommendation: p1
        r"recommendation:\s*(p[1-4])",
        # Markdown with bold or emphasis: **Recommendation**: p1 (No)
        r"\*\*Recommendation\*\*:?\s*(p[1-4]).*?(?:\n|$)",
        # Markdown with emphasis: *Recommendation*: p1 (No)
        r"\*Recommendation\*:?\s*(p[1-4]).*?(?:\n|$)",
        # Capitalized: Recommendation: p1
        r"Recommendation:?\s*(p[1-4]).*?(?:\n|$)",
        # Just the p value at the end of the text
        r"(?:recommended|final)?\s*(?:value|result|answer|outcome)?:?\s*(p[1-4])(?:\s|$|\.|\)|\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).lower()  # Normalize to lowercase

    # If nothing found, try a more aggressive search just for p1-p4 near the end
    lines = response_text.split("\n")
    for line in lines[-5:]:  # Check last 5 lines
        p_match = re.search(r"(p[1-4])", line, re.IGNORECASE)
        if p_match:
            return p_match.group(1).lower()

    return None


def get_question_id_short_from_prompt(user_prompt):
    """
    Extract the question ID from a user prompt for logging purposes.

    Args:
        user_prompt (str): The user prompt that might contain question ID information

    Returns:
        str: Short question ID if found, otherwise "unknown"
    """
    # Try to find query ID patterns in the prompt - common formats include:
    # 1. Hex format: 0x84db9689...
    # 2. Just the ID: 84db9689...
    # 3. In a questionId_ format: questionId_84db9689

    # Try hex format first
    hex_pattern = r"0x([0-9a-f]{8})[0-9a-f]*"
    match = re.search(hex_pattern, user_prompt, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try questionId_ format
    id_pattern = r"questionId_([0-9a-f]{8})[0-9a-f]*"
    match = re.search(id_pattern, user_prompt, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try finding any 8+ hex digits
    generic_hex = r"[^0-9a-f]([0-9a-f]{8})[0-9a-f]*"
    match = re.search(generic_hex, user_prompt, re.IGNORECASE)
    if match:
        return match.group(1)

    return "unknown"


def extract_prompt_update(overseer_response):
    """
    Extract updated system prompt from ChatGPT overseer response.

    Args:
        overseer_response (str): The response from the ChatGPT overseer

    Returns:
        str or None: Updated system prompt if found, None otherwise
    """
    # Look for a section that contains updated instructions
    # Patterns might include: "Updated system prompt:", "New system prompt:", etc.
    patterns = [
        r"(?:Updated|New|Modified|Revised) system prompt:[\s]*(.*?)(?:$|(?:\n\n))",
        r"(?:UPDATED SYSTEM PROMPT|NEW SYSTEM PROMPT):[\s]*(.*?)(?:$|(?:\n\n))",
        r"```[\s\S]*?(You are an artificial intelligence oracle.*?)```",
    ]

    for pattern in patterns:
        match = re.search(pattern, overseer_response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def get_overseer_decision(overseer_response):
    """
    Extract the overseer's decision from the response.

    Args:
        overseer_response (str): The response from the ChatGPT overseer

    Returns:
        tuple: (decision, require_rerun, critique, prompt_update)
            decision - 'satisfied', 'retry', or 'default_p4'
            require_rerun - boolean indicating if a rerun is required
            critique - string with critique feedback
            prompt_update - string with updated prompt if provided, None otherwise
    """
    # First try to extract the new JSON format
    decision_match = re.search(
        r"```decision\s*(\{.*?\})\s*```", overseer_response, re.DOTALL
    )

    if decision_match:
        try:
            decision_data = json.loads(decision_match.group(1))
            verdict = decision_data.get("verdict", "").lower()

            if "satisfied" in verdict:
                decision = "satisfied"
            elif "retry" in verdict:
                decision = "retry"
            elif "default" in verdict or "p4" in verdict:
                decision = "default_p4"
            else:
                decision = "default_p4"  # Default to p4 as safest option

            return (
                decision,
                decision_data.get("require_rerun", False),
                decision_data.get("critique", ""),
                decision_data.get("prompt_update", None),
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to legacy format
            pass

    # More aggressive pattern matching for verdict fields that appear outside JSON
    verdict_match = re.search(
        r"verdict\s*:?\s*(SATISFIED|RETRY|DEFAULT[\s_-]TO[\s_-]P4)",
        overseer_response,
        re.IGNORECASE,
    )
    if verdict_match:
        verdict = verdict_match.group(1).lower()
        if "satisfied" in verdict:
            return "satisfied", False, extract_critique(overseer_response), None
        elif "retry" in verdict:
            return (
                "retry",
                True,
                extract_critique(overseer_response),
                extract_prompt_update(overseer_response),
            )
        elif "default" in verdict or "p4" in verdict:
            return "default_p4", False, extract_critique(overseer_response), None

    # Legacy format parsing with expanded patterns
    if re.search(
        r"Decision:\s*SATISFIED|response is accurate|response is correct|satisfied with the response|100% confident|completely confident|can be used confidently",
        overseer_response,
        re.IGNORECASE,
    ):
        return "satisfied", False, extract_critique(overseer_response), None

    elif re.search(
        r"Decision:\s*DEFAULT TO P4|default to p4|should return p4|use p4 instead|switch to p4|change to p4|recommend p4|uncertainty|insufficient evidence|not enough information|requires more data|better safe",
        overseer_response,
        re.IGNORECASE,
    ):
        return "default_p4", False, extract_critique(overseer_response), None

    elif re.search(
        r"Decision:\s*RETRY|retry|revise|requery|update the prompt|try again|needs improvement|should be clarified|can be fixed|could be improved",
        overseer_response,
        re.IGNORECASE,
    ):
        return (
            "retry",
            True,
            extract_critique(overseer_response),
            extract_prompt_update(overseer_response),
        )

    # If no clear pattern and we see any uncertainty language, default to p4
    if re.search(
        r"(uncertain|doubt|unclear|ambiguous|not confident|not sure|could be wrong|might be incorrect)",
        overseer_response,
        re.IGNORECASE,
    ):
        return "default_p4", False, extract_critique(overseer_response), None

    # If we see clear language about being satisfied, accept the response
    if re.search(
        r"(the response is accurate|can be used confidently|properly analyzed|answered correctly|addresses the query|provides appropriate|good recommendation)",
        overseer_response,
        re.IGNORECASE,
    ):
        return "satisfied", False, extract_critique(overseer_response), None

    # If no clear pattern, default to p4 as the safest option
    return "default_p4", False, extract_critique(overseer_response), None


def extract_critique(overseer_response):
    """Extract critique from the overseer response text."""
    # Look for explicit critique sections
    critique_patterns = [
        r"(?:Issues|Problems|Concerns|Weaknesses):(.*?)(?:\n\n|\Z)",
        r"(?:Missing information|What is missing|Gaps|Lacks):(.*?)(?:\n\n|\Z)",
        r"(?:Improvements needed|Areas to improve|Should improve):(.*?)(?:\n\n|\Z)",
        r"(?:Critique|Feedback|Assessment):(.*?)(?:\n\n|\Z)",
    ]

    for pattern in critique_patterns:
        match = re.search(pattern, overseer_response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # If no specific critique found, extract a generic section
    critique_section = re.search(
        r"(?:Decision:.*?\n)(.*?)(?:\n\n|$)", overseer_response, re.DOTALL
    )
    if critique_section:
        return critique_section.group(1).strip()

    # Return a default if nothing found
    return "No specific critique provided."


# Common proposal processing utilities
def format_prompt_from_json(proposal_data):
    """
    Format a proposal data object into a user prompt.

    Args:
        proposal_data (dict or list): The proposal data

    Returns:
        str: Formatted prompt string
    """
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        proposal_data = proposal_data[0]

    ancillary_data = proposal_data.get("ancillary_data", "")
    resolution_conditions = proposal_data.get("resolution_conditions", "")
    updates = proposal_data.get("updates", [])
    unix_timestamp = proposal_data.get("unix_timestamp", "")

    prompt = f"user:\n\nancillary_data:\n{ancillary_data}\n\n"
    prompt += f"resolution_conditions:\n{resolution_conditions}\n\n"
    prompt += f"updates:\n{updates}"
    prompt += f"proposal_unix_timestamp:\n{unix_timestamp}"
    return prompt


def get_query_id_from_proposal(proposal_data):
    """
    Extract the query ID from a proposal.

    Args:
        proposal_data (dict or list): The proposal data

    Returns:
        str: Query ID
    """
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("query_id", "")
    return proposal_data.get("query_id", "")


def get_question_id_short(query_id):
    """
    Create a shortened version of a query ID for display and filenames.

    Args:
        query_id (str): Full query ID

    Returns:
        str: Short query ID
    """
    if not query_id:
        return "unknown"
    return query_id[2:10] if query_id.startswith("0x") else query_id[:8]


def get_output_filename(query_id):
    """
    Generate an output filename for a query.

    Args:
        query_id (str): Query ID

    Returns:
        str: Output filename
    """
    return f"{get_question_id_short(query_id)}.json"


def get_block_number_from_proposal(proposal_data):
    """
    Extract the block number from a proposal.

    Args:
        proposal_data (dict or list): The proposal data

    Returns:
        int: Block number
    """
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("block_number", 0)
    return proposal_data.get("block_number", 0)


def should_process_proposal(proposal_data, start_block_number=0):
    """
    Determine if a proposal should be processed based on block number.

    Args:
        proposal_data (dict or list): The proposal data
        start_block_number (int): Minimum block number to process

    Returns:
        bool: True if the proposal should be processed
    """
    block_number = get_block_number_from_proposal(proposal_data)
    return block_number >= start_block_number


def enhanced_perplexity_chatgpt_loop(
    user_prompt,
    perplexity_api_key,
    chatgpt_api_key,
    original_system_prompt,
    logger,
    max_attempts=3,
    min_attempts=2,
):
    """
    Enhanced version of perplexity_chatgpt_loop that ensures at least min_attempts
    before defaulting to p4, and encourages deeper research on retry attempts.

    Args:
        user_prompt (str): The user prompt content
        perplexity_api_key (str): Perplexity API key
        chatgpt_api_key (str): OpenAI API key
        original_system_prompt (str): Initial system prompt for Perplexity
        logger (logging.Logger): Logger instance
        max_attempts (int): Maximum number of retry attempts
        min_attempts (int): Minimum number of attempts before defaulting to p4

    Returns:
        dict: Result containing final response, recommendation, and metadata
    """
    system_prompt = original_system_prompt
    attempts = 0
    responses = []
    previous_perplexity_response = None
    previous_overseer_critique = None

    while attempts < max_attempts:
        attempts += 1
        logger.info(f"Perplexity query attempt {attempts}/{max_attempts}")

        # For retry attempts, add guidance based on previous overseer feedback
        if attempts > 1:
            retry_instruction = (
                "\n\nIMPORTANT - I need you to improve your previous response:"
            )

            # If we have specific critique from the overseer, use it
            if previous_overseer_critique:
                retry_instruction += f"\n\nThe previous response had these issues:\n{previous_overseer_critique}\n"

            # Add general instructions for improvement on retry
            retry_instruction += "\n1. Dig deeper into available sources and data"
            retry_instruction += (
                "\n2. Be more critical of potentially unreliable sources"
            )
            retry_instruction += "\n3. Consider all interpretations of the query"
            retry_instruction += (
                "\n4. Provide more specific evidence for your recommendation"
            )
            retry_instruction += (
                "\n5. Make sure your recommendation is fully justified by your analysis"
            )

            if previous_perplexity_response and "p4" in previous_perplexity_response:
                # If the previous response defaulted to p4, encourage a more thorough search
                retry_instruction += "\n\nTry your best to find information that would lead to a definitive answer (p1/p2/p3) if possible, before defaulting to p4."

            # Add the retry instruction to the system prompt if not already present
            if "I need you to improve your previous response" not in system_prompt:
                system_prompt = system_prompt + retry_instruction
                logger.info("Added specific improvement instructions for retry attempt")

        # Query Perplexity
        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner_animation,
            args=(
                stop_spinner,
                f"Querying Perplexity API (attempt {attempts}/{max_attempts})",
            ),
            daemon=True,
        )
        spinner_thread.start()

        try:
            start_time = time.time()
            perplexity_response = query_perplexity(
                user_prompt, perplexity_api_key, system_prompt=system_prompt
            )
            api_response_time = time.time() - start_time

            perplexity_text = perplexity_response.choices[0].message.content
            recommendation = extract_recommendation(perplexity_text)
            previous_perplexity_response = perplexity_text

            # Store response metadata
            response_data = {
                "attempt": attempts,
                "response": perplexity_text,
                "recommendation": recommendation,
                "system_prompt": system_prompt,
                "response_metadata": {
                    "model": perplexity_response.model,
                    "created_timestamp": perplexity_response.created,
                    "created_datetime": datetime.fromtimestamp(
                        perplexity_response.created
                    ).isoformat(),
                    "completion_tokens": perplexity_response.usage.completion_tokens,
                    "prompt_tokens": perplexity_response.usage.prompt_tokens,
                    "total_tokens": perplexity_response.usage.total_tokens,
                    "api_response_time_seconds": api_response_time,
                },
                "citations": (
                    [citation for citation in perplexity_response.citations]
                    if hasattr(perplexity_response, "citations")
                    else []
                ),
                "interaction_type": "perplexity_query",
                "stage": (
                    "initial_response"
                    if attempts == 1
                    else f"revised_response_{attempts}"
                ),
            }
            responses.append(response_data)

            logger.info(f"Perplexity returned recommendation: {recommendation}")

            # If last attempt, no need to check with overseer
            if attempts == max_attempts:
                stop_spinner.set()
                spinner_thread.join()
                logger.info(f"Reached maximum attempts ({max_attempts})")
                break

            # Query ChatGPT as the overseer
            stop_spinner.set()
            spinner_thread.join()

            # Create new spinner for ChatGPT query
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(
                target=spinner_animation,
                args=(
                    stop_spinner,
                    "Consulting ChatGPT overseer for validation",
                ),
                daemon=True,
            )
            spinner_thread.start()

            from proposal_overseer.prompt_overseer import get_overseer_prompt

            # For later attempts, encourage more critical analysis from the overseer
            enhanced_overseer_prompt = get_overseer_prompt(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                perplexity_response=perplexity_text,
                recommendation=recommendation,
                attempt=attempts,
            )

            # Add additional instructions for the overseer on retry attempts
            if attempts > 1:
                enhanced_overseer_prompt += (
                    "\n\nThis is attempt #"
                    + str(attempts)
                    + ". Please be especially critical of this response. If you see any potential for improvement or additional information that could be found, explain specifically what is missing and what could be improved."
                )
                enhanced_overseer_prompt += "\n\nIf you recommend a retry, please be very specific about what additional information or improvements you want to see in the next response."

            start_time = time.time()
            overseer_response = query_chatgpt(enhanced_overseer_prompt, chatgpt_api_key)
            overseer_response_time = time.time() - start_time

            overseer_text = overseer_response.choices[0].message.content
            decision, require_rerun, critique, prompt_update = get_overseer_decision(
                overseer_text
            )

            # CRITICAL CHECK: ALWAYS force a retry if first attempt has p4 recommendation
            if attempts == 1 and recommendation == "p4":
                logger.info(
                    "First attempt with p4 recommendation - FORCING retry regardless of overseer decision"
                )
                decision = "retry"
                require_rerun = True
                if not critique or critique == "No specific critique provided.":
                    critique = "First attempt with p4 recommendation requires at least one more attempt with improved search strategies."

            # Save the extracted critique for potential next attempt
            if critique:
                previous_overseer_critique = critique
                logger.info("Extracted critique for next attempt")

            # Store overseer metadata
            overseer_data = {
                "interaction_type": "chatgpt_evaluation",
                "stage": f"evaluation_{attempts}",
                "response": overseer_text,
                "satisfaction_level": None,  # Will be set below
                "critique": critique,
                "metadata": {
                    "model": overseer_response.model,
                    "created_timestamp": overseer_response.created,
                    "created_datetime": datetime.fromtimestamp(
                        overseer_response.created
                    ).isoformat(),
                    "completion_tokens": overseer_response.usage.completion_tokens,
                    "prompt_tokens": overseer_response.usage.prompt_tokens,
                    "total_tokens": overseer_response.usage.total_tokens,
                    "api_response_time_seconds": overseer_response_time,
                },
                "prompt_updated": False,
                "system_prompt_before": system_prompt,
            }

            # Process the decision - CRITICAL FIX: Always respect the overseer's decision
            # If the overseer is satisfied, we must accept that and NEVER force a second verification
            if decision == "satisfied":
                logger.info(
                    "Overseer is satisfied with the response - accepting without question"
                )
                overseer_data["satisfaction_level"] = "satisfied"
                # Ensure system_prompt_after is set when satisfied
                overseer_data["system_prompt_after"] = system_prompt
                responses.append(overseer_data)
                stop_spinner.set()
                spinner_thread.join()
                break

            # Continue with remaining decision logic only if not satisfied
            if require_rerun:
                # If we have a prompt update from the decision, use it
                if prompt_update:
                    overseer_data["prompt_updated"] = True
                    overseer_data["system_prompt_before"] = system_prompt
                    overseer_data["system_prompt_after"] = prompt_update
                    system_prompt = prompt_update
                    logger.info("Using prompt update from overseer decision")
                else:
                    # Ensure system_prompt_after is set even when no update
                    overseer_data["system_prompt_after"] = system_prompt

                # Set satisfaction level based on decision
                if decision == "default_p4" and attempts >= min_attempts:
                    logger.info(
                        "Overseer recommends defaulting to p4 but first running again"
                    )
                    overseer_data["satisfaction_level"] = "uncertain_retry_requested"
                elif decision == "default_p4":
                    logger.info(
                        f"Overseer suggested p4 but forcing retry (attempt {attempts}/{min_attempts} min)"
                    )
                    overseer_data["satisfaction_level"] = "forced_retry"
                else:  # retry
                    logger.info("Overseer requested retry with improvements")
                    overseer_data["satisfaction_level"] = "retry_requested"

                responses.append(overseer_data)
                stop_spinner.set()
                spinner_thread.join()
                continue
            else:
                # No rerun required and not satisfied = default to p4
                # If we haven't reached min_attempts, force another run anyway
                if decision == "default_p4" and attempts < min_attempts:
                    logger.info(
                        f"Overseer wants to default to p4, but we need to meet min_attempts ({attempts}/{min_attempts})"
                    )

                    # Create a forced retry message
                    if not previous_overseer_critique:
                        previous_overseer_critique = f"This is attempt {attempts} of {min_attempts} minimum attempts. Even though the overseer suggests defaulting to p4, we're forcing another attempt to meet the minimum requirements."
                        overseer_data["critique"] = previous_overseer_critique

                    # Force a retry with a special system prompt
                    forced_retry_instruction = (
                        f"\n\nIMPORTANT - This is a forced attempt {attempts} of {min_attempts} minimum required attempts:"
                        "\n1. The previous attempt suggested defaulting to p4, but we need to make additional attempts"
                        "\n2. Try different search strategies to uncover information not found in previous attempts"
                        "\n3. Consider alternative interpretations or perspectives"
                        "\n4. Be creative in your research approach to find better information"
                        "\n5. This attempt is required to meet the minimum attempt count policy"
                    )

                    updated_system_prompt = system_prompt + forced_retry_instruction
                    overseer_data["prompt_updated"] = True
                    overseer_data["system_prompt_before"] = system_prompt
                    overseer_data["system_prompt_after"] = updated_system_prompt
                    system_prompt = updated_system_prompt

                    overseer_data["satisfaction_level"] = "forced_retry"
                    responses.append(overseer_data)
                    stop_spinner.set()
                    spinner_thread.join()
                    continue

                # The decision is default_p4 and we're ok with that
                logger.info(
                    "Overseer recommends defaulting to p4 - accepting this decision"
                )
                # Override the recommendation to p4
                response_data["recommendation"] = "p4"
                response_data["recommendation_overridden"] = True
                overseer_data["satisfaction_level"] = "defaulted_to_p4"
                overseer_data["override_action"] = "recommendation_changed_to_p4"
                # Ensure system_prompt_after is set
                overseer_data["system_prompt_after"] = system_prompt
                responses.append(overseer_data)
                stop_spinner.set()
                spinner_thread.join()
                break

        except Exception as e:
            stop_spinner.set()
            spinner_thread.join()
            logger.error(f"Error in API query loop: {str(e)}")
            # Add error to the last response if it exists
            if responses:
                responses[-1]["error"] = str(e)
            break

    # Construct final result with all response data
    # Find the most recent perplexity response for the final output
    final_perplexity_response = next(
        (
            r
            for r in reversed(responses)
            if r.get("interaction_type") == "perplexity_query"
        ),
        None,
    )

    # Add a final overseer evaluation for the last attempt if one doesn't exist
    # This ensures the overseer's evaluation is included even for the final attempt
    last_perplexity_attempt = max(
        [
            r.get("attempt", 0)
            for r in responses
            if r.get("interaction_type") == "perplexity_query"
        ],
        default=0,
    )
    last_evaluation_attempt = max(
        [
            r.get("stage", "").split("_")[-1]
            for r in responses
            if r.get("interaction_type") == "chatgpt_evaluation"
        ],
        default="0",
    )

    # Convert last_evaluation_attempt to int if it's a number
    try:
        last_evaluation_attempt = int(last_evaluation_attempt)
    except ValueError:
        last_evaluation_attempt = 0

    # If the last perplexity attempt doesn't have a corresponding evaluation, add one
    if last_perplexity_attempt > last_evaluation_attempt and final_perplexity_response:
        logger.info(
            f"Adding final overseer evaluation for attempt {last_perplexity_attempt}"
        )

        try:
            # Create a simple evaluation request for the final response
            overseer_start_time = time.time()

            from proposal_overseer.prompt_overseer import get_overseer_prompt

            enhanced_overseer_prompt = get_overseer_prompt(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                perplexity_response=final_perplexity_response.get("response", ""),
                recommendation=final_perplexity_response.get("recommendation", ""),
                attempt=last_perplexity_attempt,
            )

            overseer_response = query_chatgpt(
                enhanced_overseer_prompt,
                chatgpt_api_key,
                model="gpt-4-turbo",
            )

            overseer_text = overseer_response.choices[0].message.content
            decision, _, critique, _ = get_overseer_decision(overseer_text)

            # Add the final evaluation to responses
            final_evaluation = {
                "interaction_type": "chatgpt_evaluation",
                "stage": f"evaluation_{last_perplexity_attempt}",
                "response": overseer_text,
                "satisfaction_level": (
                    "satisfied" if decision == "satisfied" else "final_evaluation"
                ),
                "critique": critique,
                "metadata": {
                    "model": overseer_response.model,
                    "created_timestamp": overseer_response.created,
                    "created_datetime": datetime.fromtimestamp(
                        overseer_response.created
                    ).isoformat(),
                    "completion_tokens": overseer_response.usage.completion_tokens,
                    "prompt_tokens": overseer_response.usage.prompt_tokens,
                    "total_tokens": overseer_response.usage.total_tokens,
                    "api_response_time_seconds": time.time() - overseer_start_time,
                },
                "prompt_updated": False,  # No updates on final evaluation
                "system_prompt_before": system_prompt,
                "system_prompt_after": system_prompt,  # Same since no update
            }

            responses.append(final_evaluation)
            logger.info("Added final overseer evaluation")
        except Exception as e:
            logger.error(f"Error adding final evaluation: {str(e)}")

    # If there's no perplexity response at all (unlikely), create a default empty one
    if not final_perplexity_response and responses:
        final_perplexity_response = responses[-1]
    elif not final_perplexity_response and not responses:
        logger.error("No responses collected during the loop")
        final_perplexity_response = {
            "response": "",
            "recommendation": "p4",  # Default to p4 if something went wrong
            "system_prompt": original_system_prompt,
        }

    # For accuracy metrics - track whether we had multiple attempts and outcome changed
    initial_recommendation = None
    final_recommendation = None

    for r in responses:
        if r.get("interaction_type") == "perplexity_query":
            if r.get("attempt") == 1:
                initial_recommendation = r.get("recommendation")
            final_recommendation = r.get("recommendation")

    recommendation_changed = (initial_recommendation != final_recommendation) and (
        attempts > 1
    )

    final_result = {
        "attempts": attempts,
        "responses": responses,
        "initial_recommendation": initial_recommendation,
        "final_recommendation": (
            final_perplexity_response.get("recommendation", "p4")
            if final_perplexity_response
            else "p4"
        ),
        "recommendation_changed": recommendation_changed,
        "final_response": (
            final_perplexity_response.get("response", "")
            if final_perplexity_response
            else ""
        ),
        "final_system_prompt": (
            final_perplexity_response.get("system_prompt", original_system_prompt)
            if final_perplexity_response
            else original_system_prompt
        ),
    }

    return final_result
