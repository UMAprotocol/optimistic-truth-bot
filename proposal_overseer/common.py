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
    match = re.search(r"recommendation:\s*(p[1-4])", response_text, re.IGNORECASE)
    if match:
        return match.group(1).lower()  # Normalize to lowercase
    return None


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
        str: 'satisfied', 'retry', or 'default_p4'
    """
    # Look for clear decision indicators in the response
    if re.search(
        r"Decision:\s*SATISFIED|response is accurate|response is correct|satisfied with the response|100% confident|completely confident",
        overseer_response,
        re.IGNORECASE,
    ):
        return "satisfied"

    elif re.search(
        r"Decision:\s*DEFAULT TO P4|default to p4|should return p4|use p4 instead|switch to p4|change to p4|recommend p4|uncertainty|insufficient evidence|not enough information|requires more data|better safe",
        overseer_response,
        re.IGNORECASE,
    ):
        return "default_p4"

    elif re.search(
        r"Decision:\s*RETRY|retry|revise|requery|update the prompt|try again|needs improvement|should be clarified|can be fixed|could be improved",
        overseer_response,
        re.IGNORECASE,
    ):
        return "retry"

    # If no clear pattern and we see any uncertainty language, default to p4
    if re.search(
        r"(uncertain|doubt|unclear|ambiguous|not confident|not sure|could be wrong|might be incorrect)",
        overseer_response,
        re.IGNORECASE,
    ):
        return "default_p4"

    # If no clear pattern, default to p4 as the safest option
    return "default_p4"


def perplexity_chatgpt_loop(
    user_prompt,
    perplexity_api_key,
    chatgpt_api_key,
    original_system_prompt,
    logger,
    max_attempts=3,
):
    """
    Implement the loop between Perplexity and ChatGPT for validation and refinement.

    Args:
        user_prompt (str): The user prompt content
        perplexity_api_key (str): Perplexity API key
        chatgpt_api_key (str): OpenAI API key
        original_system_prompt (str): Initial system prompt for Perplexity
        logger (logging.Logger): Logger instance
        max_attempts (int): Maximum number of retry attempts

    Returns:
        dict: Result containing final response, recommendation, and metadata
    """
    system_prompt = original_system_prompt
    attempts = 0
    responses = []

    while attempts < max_attempts:
        attempts += 1
        logger.info(f"Perplexity query attempt {attempts}/{max_attempts}")

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
                break

            # Query ChatGPT as the overseer
            stop_spinner.set()
            spinner_thread.join()

            # Create new spinner for ChatGPT query
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(
                target=spinner_animation,
                args=(stop_spinner, "Consulting ChatGPT overseer for validation"),
                daemon=True,
            )
            spinner_thread.start()

            from proposal_overseer.prompt_overseer import get_overseer_prompt

            overseer_prompt = get_overseer_prompt(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                perplexity_response=perplexity_text,
                recommendation=recommendation,
            )

            start_time = time.time()
            overseer_response = query_chatgpt(overseer_prompt, chatgpt_api_key)
            overseer_response_time = time.time() - start_time

            overseer_text = overseer_response.choices[0].message.content
            decision = get_overseer_decision(overseer_text)

            # Store overseer metadata
            overseer_data = {
                "interaction_type": "chatgpt_evaluation",
                "stage": f"evaluation_{attempts}",
                "response": overseer_text,
                "decision": decision,
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

            # Process the overseer's decision
            if decision == "satisfied":
                logger.info("Overseer is satisfied with the response")
                overseer_data["satisfaction_level"] = "satisfied"
                responses.append(overseer_data)
                stop_spinner.set()
                spinner_thread.join()
                break

            elif decision == "default_p4":
                logger.info("Overseer recommends defaulting to p4")
                # Override the recommendation to p4
                response_data["recommendation"] = "p4"
                response_data["recommendation_overridden"] = True
                overseer_data["satisfaction_level"] = "not_satisfied_defaulted_to_p4"
                overseer_data["override_action"] = "recommendation_changed_to_p4"
                responses.append(overseer_data)
                stop_spinner.set()
                spinner_thread.join()
                break

            else:  # "retry"
                # Extract updated system prompt if available
                updated_prompt = extract_prompt_update(overseer_text)
                if updated_prompt:
                    overseer_data["prompt_updated"] = True
                    overseer_data["system_prompt_before"] = system_prompt
                    overseer_data["system_prompt_after"] = updated_prompt
                    system_prompt = updated_prompt
                    logger.info("System prompt updated for next attempt")
                else:
                    logger.info(
                        "No system prompt update found, using original for next attempt"
                    )

                overseer_data["satisfaction_level"] = "not_satisfied_retry_requested"
                responses.append(overseer_data)
                stop_spinner.set()
                spinner_thread.join()

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

    final_result = {
        "attempts": attempts,
        "responses": responses,
        "final_response": (
            final_perplexity_response.get("response", "")
            if final_perplexity_response
            else ""
        ),
        "final_recommendation": (
            final_perplexity_response.get("recommendation", "p4")
            if final_perplexity_response
            else "p4"
        ),
        "final_system_prompt": (
            final_perplexity_response.get("system_prompt", original_system_prompt)
            if final_perplexity_response
            else original_system_prompt
        ),
    }

    return final_result
