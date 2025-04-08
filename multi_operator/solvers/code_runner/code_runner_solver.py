#!/usr/bin/env python3
"""
Code Runner solver implementation for UMA Multi-Operator System.
Uses ChatGPT to generate and execute code to solve prediction market questions.
"""

import json
import logging
import os
import subprocess
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from ..base_solver import BaseSolver
from ...common import query_chatgpt, extract_recommendation


class CodeRunnerSolver(BaseSolver):
    """
    Code Runner solver implementation for UMA Multi-Operator System.
    Uses ChatGPT to generate and execute code for solving prediction market questions.
    """

    def __init__(
        self,
        api_key: str,
        verbose: bool = False,
        max_retries: int = 3,
        additional_api_keys: Dict[str, str] = None,
        config_file: str = None,
    ):
        """
        Initialize the Code Runner solver.

        Args:
            api_key: OpenAI API key for ChatGPT
            verbose: Whether to print verbose output
            max_retries: Maximum number of retries for code generation and execution
            additional_api_keys: Dictionary of additional API keys to make available to generated code
            config_file: Path to a configuration file that contains API keys
        """
        super().__init__(api_key, verbose)
        self.logger = logging.getLogger("code_runner_solver")
        self.max_retries = max_retries

        # Create executed_functions directory if it doesn't exist
        self.executed_functions_dir = Path(
            "multi_operator/solvers/code_runner/executed_functions"
        )
        self.executed_functions_dir.mkdir(parents=True, exist_ok=True)

        # Sample functions directory for reference
        self.sample_functions_dir = Path(
            "multi_operator/solvers/code_runner/sample_functions"
        )

        # Set up available API keys
        self.available_api_keys = set()

        # Add default API keys
        self.available_api_keys.add("SPORTS_DATA_IO_MLB_API_KEY")

        # Load API keys from config file if provided
        if config_file:
            self._load_api_keys_from_config(config_file)

        # Add additional API keys passed directly to the constructor
        if additional_api_keys:
            if isinstance(additional_api_keys, dict):
                # If it's a dictionary, just take the keys
                self.available_api_keys.update(additional_api_keys.keys())
            elif isinstance(additional_api_keys, (list, set)):
                # If it's already a list or set, add them directly
                self.available_api_keys.update(additional_api_keys)

        if self.verbose:
            self.logger.info(
                f"Available API keys: {sorted(list(self.available_api_keys))}"
            )

    def _load_api_keys_from_config(self, config_file: str):
        """
        Load API key names from a configuration file.

        Args:
            config_file: Path to the configuration file
        """
        config_path = Path(config_file)

        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_file}")
            return

        try:
            if config_path.suffix.lower() == ".json":
                with open(config_path, "r") as f:
                    config_data = json.load(f)

                # Handle different JSON structures
                if isinstance(config_data, list):
                    # A simple list of API key names
                    self.available_api_keys.update(config_data)
                elif isinstance(config_data, dict):
                    if "api_keys" in config_data:
                        if isinstance(config_data["api_keys"], dict):
                            # Dictionary with key-value pairs
                            self.available_api_keys.update(
                                config_data["api_keys"].keys()
                            )
                        elif isinstance(config_data["api_keys"], list):
                            # List of key names
                            self.available_api_keys.update(config_data["api_keys"])
                    elif "available_api_keys" in config_data:
                        # Explicit list of available keys
                        self.available_api_keys.update(
                            config_data["available_api_keys"]
                        )
                    else:
                        # Assume all top-level keys are API key names
                        self.available_api_keys.update(config_data.keys())
            else:
                # Assume it's a .env style file
                with open(config_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                # It's a key=value format, just take the key
                                key, _ = line.split("=", 1)
                                self.available_api_keys.add(key.strip())
                            else:
                                # It's just a key name
                                self.available_api_keys.add(line.strip())
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")

    def solve(
        self, user_prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solve a proposal by generating and executing code using ChatGPT.

        Args:
            user_prompt: The user prompt to solve
            system_prompt: Optional system prompt to use

        Returns:
            Dictionary containing:
                - 'recommendation': The recommendation (p1, p2, p3, p4)
                - 'response': The full response from the solver
                - 'solver': The name of the solver
                - 'code_file': Path to the generated code file
                - 'code_output': Output from the executed code
                - 'response_metadata': Metadata about the response (timing, tokens, etc.)
        """
        self.logger.info("Solving proposal with Code Runner")
        if self.verbose:
            print("Solving proposal with Code Runner...")

        # Record start time for timing
        import time
        from datetime import datetime

        start_time = time.time()

        # Determine which type of data we need to fetch
        query_type = self.determine_query_type(user_prompt)
        self.logger.info(f"Determined query type: {query_type}")

        # Generate and execute code
        code_file_path, code, code_output, execution_successful = (
            self.generate_and_execute_code(user_prompt, query_type, system_prompt)
        )

        # Track attempts to analyze and improve code
        attempt_count = 1
        attempts_info = []

        # Even if execution was successful, check if the output suggests we should retry
        while (
            execution_successful
            and self.should_retry_on_output(code_output, query_type)
            and attempt_count < self.max_retries
        ):
            # Log a snippet of the output for debugging
            output_preview = code_output[:500].strip() if code_output else "No output"
            if code_output and len(code_output) > 500:
                output_preview += "..."

            self.logger.info(
                f"Execution succeeded but output suggests retry is needed (attempt {attempt_count}/{self.max_retries})"
            )
            self.logger.info(f"Output preview: {output_preview}")
            if self.verbose:
                print(
                    f"Execution succeeded but output suggests retry is needed (attempt {attempt_count}/{self.max_retries})"
                )
                print(f"Output preview: {output_preview}")

            # Store attempt information
            attempts_info.append(
                {
                    "attempt": attempt_count,
                    "code_file": str(code_file_path) if code_file_path else None,
                    "code": code,
                    "output": code_output,
                    "execution_successful": execution_successful,
                    "retry_reason": "Output analysis suggests retry needed",
                }
            )

            attempt_count += 1

            # Regenerate code with specific feedback about the output
            new_code_file_path, new_code, new_code_output, new_execution_successful = (
                self.generate_and_execute_code_with_output_feedback(
                    user_prompt, query_type, system_prompt, code_output, attempt_count
                )
            )

            # Update only if execution was successful
            if new_execution_successful:
                code_file_path = new_code_file_path
                code = new_code
                code_output = new_code_output
                execution_successful = new_execution_successful
            else:
                # If new execution failed, stick with the previous successful run
                self.logger.info(
                    "Retry execution failed, keeping previous successful result"
                )
                if self.verbose:
                    print("Retry execution failed, keeping previous successful result")

        if not execution_successful:
            self.logger.warning("Code execution failed after all retries")
            recommendation = "p4"  # Default to p4 if code execution fails
            summary = f"Code execution failed after {self.max_retries} attempts. Unable to resolve the query."
        else:
            # Process the code output to extract recommendation
            # Log the complete output for successful runs
            output_preview = code_output[:1000].strip() if code_output else "No output"
            if code_output and len(code_output) > 1000:
                output_preview += "..."
            self.logger.info(f"Final code output: {output_preview}")

            recommendation, summary = self.process_code_output(code_output, user_prompt)
            self.logger.info(f"Extracted recommendation: {recommendation}")

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        if self.verbose:
            print(f"Code Runner recommendation: {recommendation}")
            print("-" * 40)
            print("Summary:")
            print(summary)
            print("-" * 40)

        response_metadata = {
            "query_type": query_type,
            "created_timestamp": int(time.time()),
            "created_datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "api_response_time_seconds": elapsed_time,
            "execution_successful": execution_successful,
            "attempts": attempt_count,
            "attempts_info": attempts_info,
        }

        return {
            "recommendation": recommendation,
            "response": summary,
            "solver": self.get_name(),
            "code_file": str(code_file_path) if code_file_path else None,
            "code": code,
            "code_output": code_output,
            "response_metadata": response_metadata,
        }

    def determine_query_type(self, user_prompt: str) -> str:
        """
        Determine the type of query based on the user prompt.

        Args:
            user_prompt: The user prompt to analyze

        Returns:
            Query type: 'crypto', 'sports_mlb', or 'unknown'
        """
        user_prompt_lower = user_prompt.lower()

        # Check for crypto-related keywords and patterns
        crypto_keywords = [
            "bitcoin",
            "btc",
            "ethereum",
            "eth",
            "crypto",
            "binance",
            "price",
            "cryptocurrency",
            "token price",
            "coin price",
            "exchange rate",
            "usdt",
            "trading",
            "market price",
            "crypto market",
            "satoshi",
        ]

        crypto_patterns = [
            r"price of (btc|bitcoin|eth|ethereum)",
            r"(btc|bitcoin|eth|ethereum) price",
            r"worth (of )?(btc|bitcoin|eth|ethereum)",
            r"(btc|bitcoin|eth|ethereum).*(worth|value|price)",
            r"price.*(on|at).*(\d{4}-\d{2}-\d{2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",  # Date patterns
        ]

        # Check for MLB-related keywords and patterns
        mlb_keywords = [
            "baseball",
            "mlb",
            "major league",
            "blue jays",
            "orioles",
            "yankees",
            "red sox",
            "ballgame",
            "innings",
            "pitcher",
            "home run",
            "baseball game",
            "ballpark",
            "stadium",
            "bat",
            "baseball team",
            "world series",
            "playoffs",
        ]

        mlb_patterns = [
            r"(blue jays|orioles|yankees|red sox).*(win|lose|beat|score|game)",
            r"(score|result).*(baseball|mlb|game)",
            r"(who won|outcome).*(baseball|mlb|game)",
            r"game between .*(teams|blue jays|orioles|yankees)",
        ]

        # Check for direct matches with keywords
        if any(kw in user_prompt_lower for kw in crypto_keywords):
            return "crypto"

        if any(kw in user_prompt_lower for kw in mlb_keywords):
            return "sports_mlb"

        # Check for pattern matches
        import re

        for pattern in crypto_patterns:
            if re.search(pattern, user_prompt_lower):
                return "crypto"

        for pattern in mlb_patterns:
            if re.search(pattern, user_prompt_lower):
                return "sports_mlb"

        # If we can't determine, let's ask ChatGPT
        prompt = f"""Analyze the following query and determine if it's asking about:
1. Cryptocurrency prices (especially from Binance)
   Examples: "What was the price of BTC on March 30?", "How much did Ethereum cost yesterday?"

2. MLB sports data
   Examples: "Did the Blue Jays win against the Orioles?", "What was the score of the Yankees game?"

3. Something else
   Examples: "Who is the president?", "What's the weather like?", "How do I bake a cake?"

Query: {user_prompt}

Reply with ONLY ONE of: "crypto", "sports_mlb", or "unknown".
"""

        raw_response = query_chatgpt(
            prompt=prompt, api_key=self.api_key, model="gpt-4-turbo", verbose=False
        )

        response_text = raw_response.choices[0].message.content.strip().lower()

        if "crypto" in response_text:
            return "crypto"
        elif "sports_mlb" in response_text or "mlb" in response_text:
            return "sports_mlb"
        else:
            return "unknown"

    def generate_and_execute_code(
        self, user_prompt: str, query_type: str, system_prompt: Optional[str] = None
    ) -> Tuple[Optional[Path], Optional[str], Optional[str], bool]:
        """
        Generate code using ChatGPT and execute it.

        Args:
            user_prompt: The user prompt
            query_type: Type of query ('crypto', 'sports_mlb', or 'unknown')
            system_prompt: Optional system prompt

        Returns:
            Tuple containing:
                - Path to the generated code file (or None if failed)
                - The generated code (or None if failed)
                - Output from the executed code (or None if failed)
                - Boolean indicating whether execution was successful
        """
        template_file = None
        if query_type == "crypto":
            template_file = self.sample_functions_dir / "query_binance_price.py"
        elif query_type == "sports_mlb":
            template_file = self.sample_functions_dir / "query_sports_mlb_data.py"

        # Read template file if available
        template_code = None
        if template_file and template_file.exists():
            with open(template_file, "r") as f:
                template_code = f.read()

        # Get current timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_basename = f"{query_type}_{timestamp}.py"
        code_file_path = self.executed_functions_dir / file_basename

        for attempt in range(1, self.max_retries + 1):
            self.logger.info(f"Code generation attempt {attempt}/{self.max_retries}")

            # Generate code
            code = self.generate_code(
                user_prompt, query_type, template_code, attempt, system_prompt
            )
            if not code:
                continue

            # Save code to file
            with open(code_file_path, "w") as f:
                f.write(code)

            # Execute code
            self.logger.info(f"Executing generated code from {code_file_path}")
            execution_result = self.execute_code(code_file_path)

            if execution_result["success"]:
                self.logger.info("Code execution successful")
                return code_file_path, code, execution_result["output"], True

            self.logger.warning(f"Code execution failed: {execution_result['error']}")
            if attempt < self.max_retries:
                self.logger.info("Retrying with improved code...")

        return None, code, None, False

    def generate_code(
        self,
        user_prompt: str,
        query_type: str,
        template_code: Optional[str] = None,
        attempt: int = 1,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate code using ChatGPT.

        Args:
            user_prompt: The user prompt
            query_type: Type of query ('crypto', 'sports_mlb', or 'unknown')
            template_code: Template code to use as reference
            attempt: Current attempt number
            system_prompt: Optional system prompt

        Returns:
            Generated code or None if generation failed
        """
        # Construct a prompt for ChatGPT to generate code
        if attempt == 1:
            # First attempt uses template as reference
            code_gen_prompt = f"""You are an expert Python programmer. I need you to generate code to solve the following prediction market question:

{user_prompt}

Please write Python code that will gather the necessary data to answer this question definitively.

IMPORTANT REQUIREMENTS:
1. DO NOT use command-line arguments. Extract all necessary information from the question itself.
2. Load environment variables from .env files using the python-dotenv package.
3. For API keys, use the following environment variables:
"""
            # Add information about all available API keys
            for api_key_name in sorted(self.available_api_keys):
                if api_key_name.startswith("SPORTS_DATA_IO"):
                    sports_league = api_key_name.replace("SPORTS_DATA_IO_", "").replace(
                        "_API_KEY", ""
                    )
                    code_gen_prompt += f"   - For Sports Data IO {sports_league} data: {api_key_name}\n"
                else:
                    code_gen_prompt += f"   - For {api_key_name.lower().replace('_', ' ')}: {api_key_name}\n"

            code_gen_prompt += """
4. NEVER include actual API key values in the code, always load them from environment variables.

The code should be completely self-contained and runnable with no arguments.

"""
            if template_code:
                code_gen_prompt += f"""
Here's a similar code example that you can use as reference:

```python
{template_code}
```

MODIFY THE ABOVE TEMPLATE by:
1. Removing all command-line argument handling
2. Using dotenv to load API keys from environment variables
3. Extracting required info (dates, teams, etc.) directly from the question
4. Making the code runnable with no arguments
5. Handling errors gracefully
6. Returning results in a clear format (either JSON or plaintext with a 'recommendation: X' line)
"""
            else:
                code_gen_prompt += """
Your code should:
1. Import all necessary libraries including python-dotenv for loading environment variables
2. Load API keys from environment variables, NOT hardcoded
3. Extract required parameters (dates, teams, etc.) directly from the question
4. Make appropriate API calls to fetch data
5. Process the data to determine the answer
6. Handle errors gracefully
7. Return results in a clear format (either JSON or plaintext with a 'recommendation: X' line)

For crypto queries, use Binance API. For MLB sports data, use Sports Data IO API with the SPORTS_DATA_IO_MLB_API_KEY environment variable.
"""
        else:
            # Subsequent attempts provide the error and ask for fixes
            code_gen_prompt = f"""You previously generated Python code to solve this prediction market question, but it failed to execute correctly. Please fix the issues and provide an improved version.

Original question:
{user_prompt}

Previous code had the following issues:
- Failed on attempt {attempt-1}
- Common errors: 
  * Requiring command-line arguments
  * Hardcoded API keys
  * Incorrect imports
  * API connection issues
  * Incorrect use of RESOLUTION_MAP (using "p1" as a key instead of as a value)
  * KeyError exceptions when accessing dictionaries

Please provide a new, corrected version that:
1. DOES NOT use command-line arguments - extract all needed info from the question itself
2. Uses python-dotenv to load environment variables 
"""
            # Add information about all available API keys
            for api_key_name in sorted(self.available_api_keys):
                if api_key_name.startswith("SPORTS_DATA_IO"):
                    sports_league = api_key_name.replace("SPORTS_DATA_IO_", "").replace(
                        "_API_KEY", ""
                    )
                    code_gen_prompt += f"   - For Sports Data IO {sports_league} data: {api_key_name}\n"
                else:
                    code_gen_prompt += f"   - For {api_key_name.lower().replace('_', ' ')}: {api_key_name}\n"

            code_gen_prompt += """
3. NEVER include actual API key values in the code, always load them from environment variables.
4. Makes the code runnable with no arguments
5. Handles errors more gracefully with try/except blocks
6. Returns results in a clear format: "recommendation: p1", "recommendation: p2", etc.
7. For sports data: Uses RESOLUTION_MAP correctly (keys are outcomes, values are recommendation codes)
"""

        # Add specific advice based on query type
        if query_type == "crypto":
            code_gen_prompt += """
For cryptocurrency data:
- Use the Binance API to fetch historical prices (no API key required for public endpoints)
- Handle timeframe conversions between timezones carefully
- Make sure to use the correct symbol format (e.g., BTCUSDT)
- Extract dates and times from the question
"""
        elif query_type == "sports_mlb":
            code_gen_prompt += """
For MLB sports data:
- Use Sports Data IO API with the SPORTS_DATA_IO_MLB_API_KEY from environment variables
- Use python-dotenv to load the API key: 
  ```python
  from dotenv import load_dotenv
  import os
  
  load_dotenv()
  api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
  ```
- Extract team names and dates from the question
- Properly resolve outcomes based on game status
- IMPORTANT: When using RESOLUTION_MAP, the keys are outcome names and values are recommendation codes:
  ```python
  RESOLUTION_MAP = {
    "Blue Jays": "p1",   # Home team wins
    "Orioles": "p2",     # Away team wins  
    "50-50": "p3",       # Tie or undetermined
    "Too early to resolve": "p4"  # Not enough data
  }
  
  # CORRECT usage - use team/outcome names as keys:
  if home_team_wins:
      return "recommendation: " + RESOLUTION_MAP["Blue Jays"]   # Returns "recommendation: p1"
  elif away_team_wins:
      return "recommendation: " + RESOLUTION_MAP["Orioles"]     # Returns "recommendation: p2"
  
  # INCORRECT usage - DO NOT do this:
  # return RESOLUTION_MAP["p1"]  # This will cause KeyError: 'p1'
  ```
"""

        # Add a final instruction to focus on working code
        code_gen_prompt += """
IMPORTANT: Your code MUST run successfully without errors and without requiring any command-line arguments. Focus on robustness rather than features.
Return ONLY the Python code without explanation.
"""

        # Query ChatGPT for code generation
        try:
            raw_response = query_chatgpt(
                prompt=code_gen_prompt,
                api_key=self.api_key,
                model="gpt-4-turbo",
                system_prompt=system_prompt,
                verbose=self.verbose,
            )

            response_text = raw_response.choices[0].message.content

            # Extract code from response
            import re

            code_pattern = r"```python\s*([\s\S]*?)\s*```"
            code_match = re.search(code_pattern, response_text)

            if code_match:
                code = code_match.group(1)
            else:
                # If no code block is found, assume the entire response is code
                code = response_text

            # Check if the code seems valid
            if "import" not in code or len(code.strip().split("\n")) < 10:
                self.logger.warning("Generated code appears incomplete or invalid")
                return None

            return code

        except Exception as e:
            self.logger.error(f"Error generating code: {e}")
            return None

    def execute_code(self, code_file_path: Path) -> Dict[str, Any]:
        """
        Execute the generated code file.

        Args:
            code_file_path: Path to the code file to execute

        Returns:
            Dictionary containing:
                - 'success': Boolean indicating whether execution was successful
                - 'output': Output from the execution (if successful)
                - 'error': Error message (if failed)
        """
        try:
            # Create a temporary file for capturing output
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_output:
                temp_output_path = temp_output.name

            # Execute the Python script and capture output
            # No arguments needed, code should be self-contained
            result = subprocess.run(
                ["python", str(code_file_path)],
                capture_output=True,
                text=True,
                timeout=60,  # Set a timeout to prevent hanging
            )

            if result.returncode == 0:
                output = result.stdout
                # Log a preview of the output
                output_preview = output[:500].strip() if output else "No output"
                if output and len(output) > 500:
                    output_preview += "..."
                self.logger.info(f"Code execution successful: {output_preview}")

                return {"success": True, "output": output, "error": None}
            else:
                error_msg = f"Execution failed with error code {result.returncode}:\n{result.stderr}"
                self.logger.warning(f"Code execution failed: {error_msg}")
                return {"success": False, "output": None, "error": error_msg}

        except subprocess.TimeoutExpired:
            self.logger.warning("Code execution timed out after 60 seconds")
            return {
                "success": False,
                "output": None,
                "error": "Execution timed out after 60 seconds",
            }
        except Exception as e:
            self.logger.warning(f"Code execution failed with exception: {str(e)}")
            return {
                "success": False,
                "output": None,
                "error": f"Execution failed with exception: {str(e)}",
            }
        finally:
            # Clean up temporary file
            if "temp_output_path" in locals():
                try:
                    os.unlink(temp_output_path)
                except:
                    pass

    def process_code_output(self, output: str, user_prompt: str) -> Tuple[str, str]:
        """
        Process the output from the executed code to extract a recommendation.

        Args:
            output: Output from the executed code
            user_prompt: The original user prompt

        Returns:
            Tuple containing:
                - Recommendation (p1, p2, p3, p4)
                - Summary of the results
        """
        # First check if the output contains a direct recommendation
        recommendation = extract_recommendation(output)

        if recommendation:
            self.logger.info(f"Found direct recommendation in output: {recommendation}")
            summary = f"Code execution successful. Recommendation found: {recommendation}.\n\nOutput:\n{output}"
            return recommendation, summary

        # If no direct recommendation, try to parse JSON output
        try:
            if "{" in output and "}" in output:
                # Extract JSON from output if mixed with other text
                import re

                json_pattern = r"(\{[\s\S]*\})"
                json_match = re.search(json_pattern, output)

                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)

                    # Look for recommendation in JSON
                    if "recommendation" in data:
                        recommendation = data["recommendation"]
                    elif "resolution" in data:
                        recommendation = data["resolution"]

                    # If we found a recommendation, return it
                    if recommendation:
                        summary = f"Code execution successful. Parsed JSON output. Recommendation found: {recommendation}.\n\nOutput:\n{output}"
                        return recommendation, summary
        except:
            pass

        # If we still don't have a recommendation, ask ChatGPT to interpret the output
        try:
            interpret_prompt = f"""
Based on the following code output, please determine the recommendation (p1, p2, p3, or p4) that best answers this prediction market question:

Question: {user_prompt}

Code output:
{output}

Reply with ONLY ONE of:
"p1" - Represents YES or TRUE or the first option
"p2" - Represents NO or FALSE or the second option
"p3" - Represents a 50/50 or indeterminate outcome
"p4" - Represents "too early to resolve" or insufficient data

Reply with only the recommendation (p1, p2, p3, or p4) and nothing else.
"""

            raw_response = query_chatgpt(
                prompt=interpret_prompt,
                api_key=self.api_key,
                model="gpt-4-turbo",
                verbose=False,
            )

            response_text = raw_response.choices[0].message.content.strip().lower()

            # Extract p1, p2, p3, or p4
            if response_text in ["p1", "p2", "p3", "p4"]:
                recommendation = response_text
                summary = f"Code execution successful, but no direct recommendation found. Used AI interpretation to determine: {recommendation}.\n\nOutput:\n{output}"
                return recommendation, summary

        except Exception as e:
            self.logger.error(f"Error interpreting code output: {e}")

        # Default to p4 if we couldn't determine a recommendation
        summary = f"Code execution successful, but could not determine a clear recommendation. Defaulting to 'too early to resolve'.\n\nOutput:\n{output}"
        return "p4", summary

    def should_retry_on_output(self, output: str, query_type: str) -> bool:
        """
        Analyze output to determine if we should retry code generation even if execution succeeded.

        Args:
            output: Output from code execution
            query_type: Type of query ('crypto', 'sports_mlb', or 'unknown')

        Returns:
            Boolean indicating whether to retry based on output analysis
        """
        if not output or output.strip() == "":
            # Empty output suggests something went wrong
            return True

        # First check if we have a clean recommendation in the correct format
        # If we have a properly formatted recommendation, we don't need to retry
        recommendation_pattern = r"recommendation:\s*(p[1-4])\s*$"
        import re

        recommendation_match = re.search(
            recommendation_pattern, output.strip(), re.IGNORECASE
        )
        if recommendation_match:
            # We found a properly formatted recommendation, no retry needed
            self.logger.info(
                f"Found valid recommendation format: {recommendation_match.group(0)}"
            )
            return False

        # Check for error messages in the output
        error_indicators = [
            "error",
            "exception",
            "traceback",
            "failed",
            "cannot",
            "unable to",
            "not found",
            "missing",
            "invalid",
            "timeout",
            "no module named",
            "importerror",
            "modulenotfounderror",
        ]

        if any(indicator in output.lower() for indicator in error_indicators):
            return True

        # Check for incomplete or unhelpful output
        if "none" in output.lower() and len(output.strip()) < 50:
            return True

        # Check for recommendation patterns (if we didn't already find a clean match)
        if (
            "recommendation" not in output.lower()
            and "resolution" not in output.lower()
            and "p1" not in output.lower()
            and "p2" not in output.lower()
            and "p3" not in output.lower()
            and "p4" not in output.lower()
        ):
            return True

        # Type-specific checks
        if query_type == "crypto":
            if "price" not in output.lower():
                return True
        elif query_type == "sports_mlb":
            if (
                "game" not in output.lower()
                and "team" not in output.lower()
                and "score" not in output.lower()
                and len(output.strip()) < 30
            ):
                # Only retry if output is too minimal - simple outputs with just the recommendation are fine
                return True

        return False

    def generate_and_execute_code_with_output_feedback(
        self,
        user_prompt: str,
        query_type: str,
        system_prompt: Optional[str] = None,
        previous_output: str = None,
        attempt: int = 2,
    ) -> Tuple[Optional[Path], Optional[str], Optional[str], bool]:
        """
        Generate improved code using ChatGPT based on previous output and execute it.

        Args:
            user_prompt: The user prompt
            query_type: Type of query ('crypto', 'sports_mlb', or 'unknown')
            system_prompt: Optional system prompt
            previous_output: Output from previous code execution
            attempt: Current attempt number

        Returns:
            Tuple containing:
                - Path to the generated code file (or None if failed)
                - The generated code (or None if failed)
                - Output from the executed code (or None if failed)
                - Boolean indicating whether execution was successful
        """
        template_file = None
        if query_type == "crypto":
            template_file = self.sample_functions_dir / "query_binance_price.py"
        elif query_type == "sports_mlb":
            template_file = self.sample_functions_dir / "query_sports_mlb_data.py"

        # Read template file if available
        template_code = None
        if template_file and template_file.exists():
            with open(template_file, "r") as f:
                template_code = f.read()

        # Get current timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_basename = f"{query_type}_{timestamp}_retry{attempt}.py"
        code_file_path = self.executed_functions_dir / file_basename

        # Generate improved code with feedback from previous output
        code = self.generate_code_with_output_feedback(
            user_prompt,
            query_type,
            template_code,
            previous_output,
            attempt,
            system_prompt,
        )

        if not code:
            return None, None, None, False

        # Save code to file
        with open(code_file_path, "w") as f:
            f.write(code)

        # Execute code
        self.logger.info(f"Executing improved code from {code_file_path}")
        execution_result = self.execute_code(code_file_path)

        if execution_result["success"]:
            self.logger.info("Improved code execution successful")
            return code_file_path, code, execution_result["output"], True

        self.logger.warning(
            f"Improved code execution failed: {execution_result['error']}"
        )
        return None, code, None, False

    def generate_code_with_output_feedback(
        self,
        user_prompt: str,
        query_type: str,
        template_code: Optional[str] = None,
        previous_output: str = None,
        attempt: int = 2,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate improved code based on previous output using ChatGPT.

        Args:
            user_prompt: The user prompt
            query_type: Type of query ('crypto', 'sports_mlb', or 'unknown')
            template_code: Template code to use as reference
            previous_output: Output from previous code execution
            attempt: Current attempt number
            system_prompt: Optional system prompt

        Returns:
            Generated code or None if generation failed
        """
        code_gen_prompt = f"""You previously generated Python code to solve this prediction market question, but the output wasn't ideal. The code executed successfully, but the output needs improvement.

Original question:
{user_prompt}

Here's the output from the previous code execution:
```
{previous_output}
```

Issues with the previous output:
- The output doesn't clearly provide a recommendation
- It doesn't properly extract and present the needed information
- The format doesn't follow our expected pattern

Please provide an improved version that:
1. DOES NOT use command-line arguments - extract all needed info from the question itself
2. Uses python-dotenv to load environment variables (e.g., SPORTS_DATA_IO_MLB_API_KEY)
3. Makes the code runnable with no arguments
4. Processes the data more effectively
5. Returns a CLEAR recommendation in the format "recommendation: p1", "recommendation: p2", "recommendation: p3", or "recommendation: p4"
   - p1 = YES/TRUE/First option
   - p2 = NO/FALSE/Second option
   - p3 = 50-50 outcome
   - p4 = Too early to resolve

Make sure the output is clean and specifically includes the recommendation format.
"""

        # Add query-specific advice
        if query_type == "crypto":
            code_gen_prompt += """
For cryptocurrency data:
- Clearly extract the prices and compare them if needed
- Format the output to clearly show the price data and the recommendation
- Handle all error cases gracefully
"""
        elif query_type == "sports_mlb":
            code_gen_prompt += """
For MLB sports data:
- Clearly extract game results and team information
- Make sure to handle all possible game statuses
- Format the output to clearly show the game data and the recommendation
- IMPORTANT: When using RESOLUTION_MAP, the keys are outcome names and values are recommendation codes:
  ```python
  RESOLUTION_MAP = {
    "Blue Jays": "p1",   # Home team wins
    "Orioles": "p2",     # Away team wins  
    "50-50": "p3",       # Tie or undetermined
    "Too early to resolve": "p4"  # Not enough data
  }
  
  # CORRECT usage - use team/outcome names as keys:
  if home_team_wins:
      return "recommendation: " + RESOLUTION_MAP["Blue Jays"]   # Returns "recommendation: p1"
  elif away_team_wins:
      return "recommendation: " + RESOLUTION_MAP["Orioles"]     # Returns "recommendation: p2"
  
  # INCORRECT usage - DO NOT do this:
  # return RESOLUTION_MAP["p1"]  # This will cause KeyError: 'p1'
  ```
"""

        # Final instruction
        code_gen_prompt += """
IMPORTANT: Your code MUST run successfully without errors and without requiring any command-line arguments. The output MUST include a recommendation in the format "recommendation: pX" where X is 1, 2, 3, or 4.
Return ONLY the Python code without explanation.
"""

        # Query ChatGPT for improved code generation
        try:
            raw_response = query_chatgpt(
                prompt=code_gen_prompt,
                api_key=self.api_key,
                model="gpt-4-turbo",
                system_prompt=system_prompt,
                verbose=self.verbose,
            )

            response_text = raw_response.choices[0].message.content

            # Extract code from response
            import re

            code_pattern = r"```python\s*([\s\S]*?)\s*```"
            code_match = re.search(code_pattern, response_text)

            if code_match:
                code = code_match.group(1)
            else:
                # If no code block is found, assume the entire response is code
                code = response_text

            # Check if the code seems valid
            if "import" not in code or len(code.strip().split("\n")) < 10:
                self.logger.warning(
                    "Generated improved code appears incomplete or invalid"
                )
                return None

            return code

        except Exception as e:
            self.logger.error(f"Error generating improved code: {e}")
            return None

    def get_name(self) -> str:
        """
        Get the name of the solver.

        Returns:
            The name of the solver
        """
        return "code_runner"
