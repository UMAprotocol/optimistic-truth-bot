# ChatGPT Overseer Pipeline for Perplexity

This pipeline creates a prompt for ChatGPT to act as an overseer for Perplexity responses. It iteratively analyzes responses, provides feedback, and generates follow-up prompts to improve Perplexity's performance.

## Overview

The pipeline consists of the following scripts:

1. `chatgpt_overseer_prompt_creator.py`:
   - Extracts user_prompt, system_prompt, and response from JSON files
   - Creates a prompt template for ChatGPT to evaluate Perplexity's responses
   - Outputs a markdown file with the main prompt and test instances

2. `chatgpt_overseer_runner.py`:
   - Takes the overseer prompts and runs the iterative prompting process
   - Calls ChatGPT to evaluate Perplexity's responses
   - Creates follow-up prompts for Perplexity (up to 3 iterations if needed)
   - Outputs results as a JSON file

3. `generate_final_overseer_prompt.py`:
   - Analyzes the results from the iterative prompting process
   - Extracts patterns, common issues, and effective follow-up techniques
   - Generates a final, optimized ChatGPT overseer prompt
   - Outputs the final prompt as a markdown file

4. `run_pipeline.py`:
   - Orchestrates the entire pipeline
   - Provides command-line options for customization and skipping steps
   - Handles error cases and ensures directories exist

## Setup and Run

Here are the commands to set up and run the ChatGPT overseer pipeline:

```bash
# 1. Ensure the required directories exist
mkdir -p proposal_replayer/combinatorial_follower

# 2. Optional: Set environment variables for API keys
export CHATGPT_API_KEY="your_openai_api_key_here"
export PERPLEXITY_API_KEY="your_perplexity_api_key_here"

# 3. Run the entire pipeline with default settings (5 samples)
python proposal_replayer/combinatorial_follower/run_pipeline.py

# Alternative: Run with more samples (e.g., 10)
python proposal_replayer/combinatorial_follower/run_pipeline.py --sample_size 10

# Alternative: Run with all samples
python proposal_replayer/combinatorial_follower/run_pipeline.py --sample_size 0
```

If you prefer to run each step individually:

```bash
# 1. Generate the overseer prompts
python proposal_replayer/combinatorial_follower/chatgpt_overseer_prompt_creator.py --sample_size 10

# 2. Run the iterative prompting
python proposal_replayer/combinatorial_follower/chatgpt_overseer_runner.py

# 3. Generate the final overseer prompt
python proposal_replayer/combinatorial_follower/generate_final_overseer_prompt.py
```

## Output

The final overseer prompt will be saved to:
`proposal_replayer/combinatorial_follower/final_overseer_prompt.md`

This prompt can be used to guide ChatGPT in evaluating and improving Perplexity's responses, creating a system where:

1. Perplexity runs first to answer a query
2. ChatGPT evaluates the response
3. If unsatisfied, ChatGPT creates follow-up prompts for Perplexity (up to 3 times)
4. The process continues until a satisfactory response is obtained or the maximum iterations are reached

## Customization

The pipeline can be customized with various command-line arguments:

- `--input_dir`: Specify the directory containing the JSON files with Perplexity outputs
- `--output_dir`: Specify the directory to save the output files
- `--sample_size`: Specify the number of samples to process (0 for all)
- `--chatgpt_api_key`: Specify the API key for ChatGPT
- `--perplexity_api_key`: Specify the API key for Perplexity
- `--skip_prompt_creation`: Skip the prompt creation step (use existing prompts)
- `--skip_iterative_prompting`: Skip the iterative prompting step (use existing results)
- `--skip_final_prompt`: Skip the final prompt generation step 