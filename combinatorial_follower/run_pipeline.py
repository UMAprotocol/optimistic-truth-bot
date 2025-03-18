import os
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the ChatGPT overseer prompt pipeline"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="proposal_replayer/results/14032025-gpt-refined-prompt/outputs",
        help="Directory containing JSON files with Perplexity outputs",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="combinatorial_follower",
        help="Directory to save output files",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=5,
        help="Number of samples to process (default: 5, use 0 for all)",
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
    parser.add_argument(
        "--skip_prompt_creation",
        action="store_true",
        help="Skip the prompt creation step (use existing prompts)",
    )
    parser.add_argument(
        "--skip_iterative_prompting",
        action="store_true",
        help="Skip the iterative prompting step (use existing results)",
    )
    parser.add_argument(
        "--skip_final_prompt",
        action="store_true",
        help="Skip the final prompt generation step",
    )
    return parser.parse_args()


def run_command(command, description):
    """Run a shell command and print a message."""
    print(f"Running {description}...")
    try:
        subprocess.run(command, check=True)
        print(f"Completed {description} successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False


def ensure_directory_exists(directory):
    """Ensure a directory exists, creating it if necessary."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def main():
    args = parse_args()

    # Ensure output directory exists
    ensure_directory_exists(args.output_dir)

    # Step 1: Create ChatGPT overseer prompts
    prompt_file = os.path.join(args.output_dir, "chatgpt_overseer_prompts.md")
    if not args.skip_prompt_creation:
        success = run_command(
            [
                "python",
                "combinatorial_follower/chatgpt_overseer_prompt_creator.py",
                "--input_dir",
                args.input_dir,
                "--output_file",
                prompt_file,
                "--sample_size",
                str(args.sample_size),
            ],
            "prompt creation",
        )

        if not success:
            print("Failed to create prompts. Exiting.")
            return
    else:
        print("Skipping prompt creation step")

    # Step 2: Run iterative prompting
    results_file = os.path.join(args.output_dir, "iterative_results.json")
    if not args.skip_iterative_prompting:
        # Set environment variables for API keys
        env = os.environ.copy()
        if args.chatgpt_api_key:
            env["CHATGPT_API_KEY"] = args.chatgpt_api_key
        if args.perplexity_api_key:
            env["PERPLEXITY_API_KEY"] = args.perplexity_api_key

        success = run_command(
            [
                "python",
                "combinatorial_follower/chatgpt_overseer_runner.py",
                "--input_file",
                prompt_file,
                "--output_file",
                results_file,
            ],
            "iterative prompting",
        )

        if not success:
            print("Failed to run iterative prompting. Exiting.")
            return
    else:
        print("Skipping iterative prompting step")

    # Step 3: Generate final prompt
    final_prompt_file = os.path.join(args.output_dir, "final_overseer_prompt.md")
    if not args.skip_final_prompt:
        success = run_command(
            [
                "python",
                "combinatorial_follower/generate_final_overseer_prompt.py",
                "--input_file",
                results_file,
                "--output_file",
                final_prompt_file,
            ],
            "final prompt generation",
        )

        if not success:
            print("Failed to generate final prompt. Exiting.")
            return
    else:
        print("Skipping final prompt generation step")

    print("Pipeline completed successfully!")
    print(f"Final overseer prompt saved to: {final_prompt_file}")


if __name__ == "__main__":
    main()
