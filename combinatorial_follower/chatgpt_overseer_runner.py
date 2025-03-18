import os
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Note: You would need to install appropriate API clients for ChatGPT and Perplexity
# This script assumes you have the necessary API access


class IterativePromptRunner:
    def __init__(self, chatgpt_api_key: str, perplexity_api_key: str):
        """Initialize the runner with API keys."""
        self.chatgpt_api_key = chatgpt_api_key
        self.perplexity_api_key = perplexity_api_key
        self.max_iterations = 3  # Maximum number of follow-up prompts

    def call_chatgpt(self, prompt: str) -> Dict:
        """
        Call the ChatGPT API with the given prompt.

        This is a placeholder function - you would need to implement the actual API call
        using an appropriate client library.
        """
        # Placeholder for actual ChatGPT API call
        print(f"Calling ChatGPT API with prompt of length {len(prompt)}...")

        # In a real implementation, you would make the API call here
        # For example, using the OpenAI Python client:
        # from openai import OpenAI
        # client = OpenAI(api_key=self.chatgpt_api_key)
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return response

        # For now, return a mock response
        return {
            "content": "REVIEW:\nThe response is comprehensive and addresses the query correctly.\n\nSATISFACTION:\nYES\n\nREASONING:\nThe response follows the guidelines and provides accurate information.",
            "role": "assistant",
        }

    def call_perplexity(self, user_prompt: str, system_prompt: str) -> Dict:
        """
        Call the Perplexity API with the given prompts.

        This is a placeholder function - you would need to implement the actual API call
        using an appropriate client library.
        """
        # Placeholder for actual Perplexity API call
        print(
            f"Calling Perplexity API with user prompt of length {len(user_prompt)}..."
        )

        # In a real implementation, you would make the API call here
        # Return a mock response for now
        return {
            "response": "This is a mock response from Perplexity.",
            "recommendation": "p1",
        }

    def parse_chatgpt_response(self, response: Dict) -> Tuple[bool, Optional[str]]:
        """
        Parse the ChatGPT response to determine satisfaction and follow-up prompt.

        Returns:
            Tuple[bool, Optional[str]]: (is_satisfied, follow_up_prompt)
        """
        content = response.get("content", "")

        # Extract satisfaction (YES/NO)
        satisfaction_line = None
        for line in content.split("\n"):
            if line.startswith("SATISFACTION:"):
                satisfaction_line = line.replace("SATISFACTION:", "").strip()
                break

        is_satisfied = (
            satisfaction_line.upper() == "YES" if satisfaction_line else False
        )

        # Extract follow-up prompt if not satisfied
        follow_up_prompt = None
        if not is_satisfied:
            in_follow_up = False
            follow_up_lines = []

            for line in content.split("\n"):
                if line.startswith("FOLLOW-UP PROMPT"):
                    in_follow_up = True
                    continue
                if in_follow_up:
                    follow_up_lines.append(line)

            if follow_up_lines:
                follow_up_prompt = "\n".join(follow_up_lines).strip()

        return is_satisfied, follow_up_prompt

    def run_iterative_prompting(self, instance: Dict) -> Dict:
        """
        Run the iterative prompting process for a single instance.

        Args:
            instance: Dict containing user_prompt, system_prompt, response, etc.

        Returns:
            Dict: Results of the iterative prompting process
        """
        user_prompt = instance["user_prompt"]
        system_prompt = instance["system_prompt"]
        original_response = instance["response"]
        question_id = instance.get("question_id_short", "unknown")

        results = {
            "question_id": question_id,
            "original_user_prompt": user_prompt,
            "original_system_prompt": system_prompt,
            "original_response": original_response,
            "iterations": [],
        }

        # Create initial ChatGPT prompt to evaluate the original Perplexity response
        chatgpt_prompt = f"""
ORIGINAL USER PROMPT:
{user_prompt}

SYSTEM PROMPT:
{system_prompt}

PERPLEXITY RESPONSE:
{original_response}

Based on the above information, please provide your review, satisfaction level, reasoning, and follow-up prompt if needed.
"""

        current_iteration = 0
        current_user_prompt = user_prompt
        current_response = original_response

        while current_iteration < self.max_iterations:
            # Call ChatGPT to evaluate the response
            chatgpt_response = self.call_chatgpt(chatgpt_prompt)

            # Parse ChatGPT's response
            is_satisfied, follow_up_prompt = self.parse_chatgpt_response(
                chatgpt_response
            )

            # Record this iteration
            iteration_result = {
                "iteration": current_iteration,
                "chatgpt_prompt": chatgpt_prompt,
                "chatgpt_response": chatgpt_response.get("content", ""),
                "is_satisfied": is_satisfied,
                "follow_up_prompt": follow_up_prompt,
            }

            results["iterations"].append(iteration_result)

            # If ChatGPT is satisfied, we're done
            if is_satisfied or follow_up_prompt is None:
                break

            # Otherwise, call Perplexity with the follow-up prompt
            current_iteration += 1
            current_user_prompt = follow_up_prompt

            perplexity_response = self.call_perplexity(
                current_user_prompt, system_prompt
            )
            current_response = perplexity_response.get("response", "")

            # Update the iteration result with Perplexity's response
            iteration_result["perplexity_response"] = current_response

            # Update the ChatGPT prompt for the next iteration
            chatgpt_prompt = f"""
ORIGINAL USER PROMPT:
{user_prompt}

SYSTEM PROMPT:
{system_prompt}

PREVIOUS PERPLEXITY RESPONSE:
{original_response}

FOLLOW-UP PROMPT:
{current_user_prompt}

NEW PERPLEXITY RESPONSE:
{current_response}

Based on the above information, please provide your review, satisfaction level, reasoning, and follow-up prompt if needed.
"""

        # Final results
        results["final_satisfaction"] = results["iterations"][-1]["is_satisfied"]
        results["total_iterations"] = current_iteration

        return results


def load_instance_prompts(prompt_file: str) -> List[Dict]:
    """
    Load instance prompts from the generated markdown file.

    Args:
        prompt_file: Path to the markdown file containing instance prompts

    Returns:
        List[Dict]: List of instances with user_prompt, system_prompt, response, etc.
    """
    instances = []
    current_instance = {}
    current_section = None

    with open(prompt_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()

        if line.startswith("### Instance"):
            if current_instance:
                instances.append(current_instance)
            current_instance = {}
            current_section = None
        elif line.startswith("ORIGINAL USER PROMPT:"):
            current_section = "user_prompt"
            current_instance["user_prompt"] = ""
        elif line.startswith("SYSTEM PROMPT:"):
            current_section = "system_prompt"
            current_instance["system_prompt"] = ""
        elif line.startswith("PERPLEXITY RESPONSE:"):
            current_section = "response"
            current_instance["response"] = ""
        elif line.startswith("RECOMMENDATION:"):
            current_section = "recommendation"
            current_instance["recommendation"] = ""
        elif line == "---":
            current_section = None
        elif current_section:
            if current_instance[current_section]:
                current_instance[current_section] += "\n" + line
            else:
                current_instance[current_section] = line

    # Add the last instance
    if current_instance:
        instances.append(current_instance)

    return instances


def save_results(results, filename="iterative_results.json"):
    # Extract just the filename, ignore any directory in the path
    _, basename = os.path.split(filename)

    # Define output directory path
    output_dir = Path("combinatorial_follower/overseer_prompt_output")
    output_dir.mkdir(exist_ok=True)

    # Use the filename in the output directory
    output_path = os.path.join(output_dir, basename)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run iterative prompting with ChatGPT overseer and Perplexity"
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="combinatorial_follower/chatgpt_overseer_prompts.md",
        help="Input file with ChatGPT overseer prompts",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="combinatorial_follower/iterative_results.json",
        help="Output file to save results",
    )
    parser.add_argument(
        "--chatgpt_api_key",
        type=str,
        default=os.environ.get("CHATGPT_API_KEY", ""),
        help="API key for ChatGPT",
    )
    parser.add_argument(
        "--perplexity_api_key",
        type=str,
        default=os.environ.get("PERPLEXITY_API_KEY", ""),
        help="API key for Perplexity",
    )
    args = parser.parse_args()

    # Check if input file exists
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file '{args.input_file}' does not exist.")
        return

    # Create output directory if it doesn't exist
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load instance prompts
    instances = load_instance_prompts(args.input_file)
    print(f"Loaded {len(instances)} instances from {args.input_file}")

    # Initialize the runner
    runner = IterativePromptRunner(args.chatgpt_api_key, args.perplexity_api_key)

    # Run iterative prompting for each instance
    results = []
    for i, instance in enumerate(instances):
        print(f"Processing instance {i+1}/{len(instances)}...")
        result = runner.run_iterative_prompting(instance)
        results.append(result)

        # Sleep to avoid API rate limits
        if i < len(instances) - 1:
            time.sleep(1)

    # Save results
    save_results(results, args.output_file)
    print(f"Saved results to {args.output_file}")


if __name__ == "__main__":
    main()
