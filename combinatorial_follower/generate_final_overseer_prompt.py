import argparse
import json
from pathlib import Path
from typing import Dict, List
import os


def load_results(results_file: str) -> List[Dict]:
    """Load results from the iterative prompting process."""
    with open(results_file, "r", encoding="utf-8") as file:
        return json.load(file)


def analyze_results(results: List[Dict]) -> Dict:
    """Analyze the iterative prompting results to extract patterns."""
    stats = {
        "total_instances": len(results),
        "satisfied_instances": 0,
        "unsatisfied_instances": 0,
        "iteration_counts": {0: 0, 1: 0, 2: 0, 3: 0},
        "common_issues": [],
        "effective_follow_ups": [],
    }

    for result in results:
        iterations = result.get("iterations", [])
        final_iteration = iterations[-1] if iterations else {}
        final_satisfaction = final_iteration.get("is_satisfied", False)

        if final_satisfaction:
            stats["satisfied_instances"] += 1
        else:
            stats["unsatisfied_instances"] += 1

        iteration_count = result.get("total_iterations", 0)
        stats["iteration_counts"][iteration_count] += 1

        # Extract common issues and effective follow-ups
        for iteration in iterations:
            chatgpt_response = iteration.get("chatgpt_response", "")
            if not iteration.get("is_satisfied", True) and iteration.get(
                "follow_up_prompt"
            ):
                # This is an unsatisfactory response with a follow-up

                # Extract issue from reasoning section
                reasoning = ""
                in_reasoning = False
                for line in chatgpt_response.split("\n"):
                    if line.startswith("REASONING:"):
                        in_reasoning = True
                        continue
                    elif in_reasoning and (
                        line.startswith("FOLLOW-UP PROMPT") or not line.strip()
                    ):
                        in_reasoning = False
                    elif in_reasoning:
                        reasoning += line + " "

                if reasoning:
                    stats["common_issues"].append(reasoning.strip())

                # If this is not the last iteration and the next iteration was satisfied,
                # consider the follow-up prompt effective
                if iteration.get("iteration") < len(iterations) - 1:
                    next_iteration = iterations[iteration.get("iteration") + 1]
                    if next_iteration.get("is_satisfied", False):
                        follow_up = iteration.get("follow_up_prompt", "")
                        if follow_up:
                            stats["effective_follow_ups"].append(follow_up)

    # Limit the number of issues and follow-ups to include
    stats["common_issues"] = stats["common_issues"][:10]  # Top 10 issues
    stats["effective_follow_ups"] = stats["effective_follow_ups"][
        :5
    ]  # Top 5 effective follow-ups

    return stats


def generate_final_prompt(stats: Dict) -> str:
    """Generate the final ChatGPT overseer prompt based on analysis."""
    prompt = """# ChatGPT Overseer Prompt for Perplexity Evaluation

You are acting as an Overseer for Perplexity AI responses. Your task is to evaluate responses from Perplexity AI and determine if they are satisfactory or need improvement.

## Your Role and Responsibilities

Your primary responsibility is to:
1. Evaluate if Perplexity's response accurately addresses the user's query
2. Ensure the response adheres to guidelines in the system prompt
3. Identify any issues or shortcomings in the response
4. Create follow-up prompts when necessary to improve the response

## Evaluation Process

For each Perplexity response, you will follow this process:
1. First, understand the user's original query and the system prompt
2. Carefully review Perplexity's response for accuracy, completeness, and adherence to guidelines
3. Determine whether the response is satisfactory or needs improvement
4. If improvement is needed, craft a precise follow-up prompt for Perplexity

## Response Format

Your evaluation should follow this format:

```
EVALUATION:
[Detailed analysis of the response, highlighting strengths and weaknesses]

ISSUES:
[List specific issues with the response if any]

SATISFACTION:
[YES/NO] - Indicate if you are satisfied with the response

REASONING:
[Explain your reasoning for your satisfaction determination]

FOLLOW-UP PROMPT (if not satisfied):
[Write a follow-up prompt for Perplexity to address the identified issues]
```

## Iteration Protocol

You may provide up to 3 follow-up prompts for each response. For each iteration:
1. Evaluate the new response in light of the original query and previous responses
2. Determine if the new response resolves the issues identified
3. If satisfied, indicate this and conclude the evaluation
4. If not satisfied, provide another follow-up prompt (up to 3 total iterations)

"""

    # Add insights from the analysis
    prompt += "## Insights from Previous Evaluations\n\n"

    prompt += (
        f"Based on analysis of {stats['total_instances']} previous evaluations:\n\n"
    )

    # Satisfaction statistics
    satisfaction_rate = (
        (stats["satisfied_instances"] / stats["total_instances"]) * 100
        if stats["total_instances"] > 0
        else 0
    )
    prompt += f"- {satisfaction_rate:.1f}% of responses required no follow-up or were satisfactory after follow-ups\n"

    # Iteration statistics
    if stats["total_instances"] > 0:
        prompt += "- Iteration statistics:\n"
        for i in range(4):
            percentage = (stats["iteration_counts"][i] / stats["total_instances"]) * 100
            prompt += f"  - {percentage:.1f}% required {i} {'iteration' if i == 1 else 'iterations'}\n"

    # Common issues
    if stats["common_issues"]:
        prompt += "\n### Common Issues to Watch For:\n\n"
        for i, issue in enumerate(stats["common_issues"][:5], 1):
            prompt += f"{i}. {issue}\n\n"

    # Effective follow-up examples
    if stats["effective_follow_ups"]:
        prompt += "\n### Examples of Effective Follow-up Prompts:\n\n"
        for i, follow_up in enumerate(stats["effective_follow_ups"][:3], 1):
            prompt += f"Example {i}:\n```\n{follow_up}\n```\n\n"

    prompt += "## Final Guidelines\n\n"
    prompt += "- Be thorough but concise in your evaluations\n"
    prompt += "- Focus on substantive issues rather than minor stylistic preferences\n"
    prompt += "- Ensure follow-up prompts are clear, specific, and actionable\n"
    prompt += "- Remember that your goal is to help Perplexity provide the most accurate and helpful response possible\n"

    return prompt


def save_prompt(prompt: str, output_file: str):
    """Save the generated prompt to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Generate final ChatGPT overseer prompt"
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="combinatorial_follower/iterative_results.json",
        help="Input file with iterative prompting results",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="combinatorial_follower/final_overseer_prompt.md",
        help="Output file to save the final prompt",
    )
    args = parser.parse_args()

    # Check if input file exists
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file '{args.input_file}' does not exist.")
        return

    # Extract just the filename, ignore any directory in the path
    _, input_basename = os.path.split(args.input_file)
    _, output_basename = os.path.split(args.output_file)

    # Define output directory path
    output_dir = Path("combinatorial_follower/overseer_prompt_output")
    output_dir.mkdir(exist_ok=True)

    # Use the filename in the output directory
    input_path = (
        args.input_file
        if os.path.exists(args.input_file)
        else os.path.join(output_dir, input_basename)
    )
    output_path = os.path.join(output_dir, output_basename)

    # Load results
    results = load_results(input_path)
    print(f"Loaded results for {len(results)} instances from {input_path}")

    # Analyze results
    stats = analyze_results(results)
    print("Analyzed results to extract patterns")

    # Generate final prompt
    prompt = generate_final_prompt(stats)
    print("Generated final ChatGPT overseer prompt")

    # Save prompt
    with open(output_path, "w") as f:
        f.write(prompt)

    print(f"Final prompt written to {output_path}")


if __name__ == "__main__":
    main()
