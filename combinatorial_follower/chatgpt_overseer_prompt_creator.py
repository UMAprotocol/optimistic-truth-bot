import os
import json
import argparse
from pathlib import Path


def load_json_files(directory_path):
    """Load all JSON files from the specified directory."""
    json_files = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    json_files.append(data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    return json_files


def extract_data_from_files(json_files):
    """Extract user_prompt, system_prompt, and response from each JSON file."""
    extracted_data = []
    for data in json_files:
        try:
            extracted_data.append(
                {
                    "question_id_short": data.get("question_id_short", ""),
                    "user_prompt": data.get("user_prompt", ""),
                    "system_prompt": data.get("system_prompt", ""),
                    "response": data.get("response", ""),
                    "recommendation": data.get("recommendation", ""),
                }
            )
        except Exception as e:
            print(f"Error extracting data: {e}")
    return extracted_data


def create_chatgpt_prompt():
    """Create the main prompt for ChatGPT to act as an overseer."""
    prompt = """
You are acting as an Overseer for AI responses. Your task is to evaluate responses from Perplexity AI and determine if they are satisfactory or need improvement.

You will be given:
1. The original user prompt that was sent to Perplexity
2. The system prompt that guided Perplexity
3. Perplexity's response to the query

Your job is to:
1. Analyze if Perplexity's response appropriately addresses the query
2. Determine if the response is accurate, complete, and follows the guidelines in the system prompt
3. If you are NOT satisfied with the response, you should create a follow-up prompt for Perplexity
4. You can re-prompt Perplexity up to 3 times with either follow-up questions or refinements

Your output format should be:

REVIEW:
[Your detailed review of Perplexity's response, highlighting strengths and weaknesses]

SATISFACTION:
[YES/NO] - Indicate if you are satisfied with the response

REASONING:
[Explain your reasoning for being satisfied or not]

FOLLOW-UP PROMPT (if not satisfied):
[Write a follow-up prompt for Perplexity that addresses the issues in the initial response]

Approach this task thoughtfully and critically, focusing on ensuring the responses are factual, comprehensive, and adhere to the guidelines.
"""
    return prompt


def create_instance_prompt(data_instance):
    """Create a prompt for a specific instance to send to ChatGPT."""
    prompt = f"""
ORIGINAL USER PROMPT:
{data_instance['user_prompt']}

SYSTEM PROMPT:
{data_instance['system_prompt']}

PERPLEXITY RESPONSE:
{data_instance['response']}

RECOMMENDATION:
{data_instance['recommendation']}

Based on the above information, please provide your review, satisfaction level, reasoning, and follow-up prompt if needed.
"""
    return prompt


def save_prompts_to_file(main_prompt, instance_prompts, output_file):
    """Save the generated prompts to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# ChatGPT Overseer Prompt\n\n")
        file.write("## Main Prompt\n\n")
        file.write(main_prompt)
        file.write("\n\n## Instance Prompts\n\n")
        for i, prompt in enumerate(instance_prompts):
            file.write(f"### Instance {i+1}\n\n")
            file.write(prompt)
            file.write("\n\n---\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Create ChatGPT overseer prompts for Perplexity responses"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="proposal_replayer/results/14032025-gpt-refined-prompt/outputs",
        help="Directory containing JSON files with Perplexity outputs",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="combinatorial_follower/chatgpt_overseer_prompts.md",
        help="Output file to save the generated prompts",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=5,
        help="Number of samples to process (default: 5, use 0 for all)",
    )
    args = parser.parse_args()

    # Ensure input directory exists
    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        print(
            f"Error: Input directory '{args.input_dir}' does not exist or is not a directory."
        )
        return

    # Create output directory if it doesn't exist
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load JSON files
    json_files = load_json_files(args.input_dir)
    print(f"Loaded {len(json_files)} JSON files.")

    # Sample files if specified
    if args.sample_size > 0 and args.sample_size < len(json_files):
        import random

        json_files = random.sample(json_files, args.sample_size)
        print(f"Sampled {args.sample_size} files for processing.")

    # Extract data
    extracted_data = extract_data_from_files(json_files)
    print(f"Extracted data from {len(extracted_data)} files.")

    # Create prompts
    main_prompt = create_chatgpt_prompt()
    instance_prompts = [create_instance_prompt(data) for data in extracted_data]

    # Save prompts
    save_prompts_to_file(main_prompt, instance_prompts, args.output_file)
    print(f"Saved prompts to {args.output_file}")


if __name__ == "__main__":
    main()
