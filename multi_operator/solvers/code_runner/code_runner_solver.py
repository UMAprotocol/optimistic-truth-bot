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
from ...prompts.code_runner_prompt import get_code_generation_prompt


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
        
        # Discover available sample function templates dynamically
        self.sample_templates = self._discover_sample_templates()
        if self.verbose:
            self.logger.info(f"Discovered {len(self.sample_templates)} sample templates")
            for query_type, template_file in self.sample_templates.items():
                self.logger.info(f"  - {query_type}: {template_file.name}")

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
        Load API key names and endpoints from a configuration file.

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

                # Initialize data sources dictionary if not already present
                if not hasattr(self, "data_sources"):
                    self.data_sources = {}

                # Handle different JSON structures
                if isinstance(config_data, list):
                    # Legacy format: A simple list of API key names
                    self.available_api_keys.update(config_data)
                elif isinstance(config_data, dict):
                    # Handle new structured format with data_sources
                    if "data_sources" in config_data and isinstance(config_data["data_sources"], list):
                        for source in config_data["data_sources"]:
                            # Extract API keys
                            if "api_keys" in source and isinstance(source["api_keys"], list):
                                self.available_api_keys.update(source["api_keys"])
                            
                            # Store the entire data source configuration
                            if "name" in source:
                                source_name = source["name"]
                                self.data_sources[source_name] = source
                                
                                # Log the loaded data source
                                if self.verbose:
                                    self.logger.info(f"Loaded data source: {source_name}")
                                    
                                    # Log endpoints if available
                                    if "endpoints" in source:
                                        endpoints = source["endpoints"]
                                        for endpoint_type, url in endpoints.items():
                                            self.logger.info(f"  - {endpoint_type} endpoint: {url}")
                    
                    # Also add all regular keys from the config
                    for key, value in config_data.items():
                        if key != "data_sources":
                            # Add the key itself as an available API key
                            self.available_api_keys.add(key)
                            
                            # If the value is a dictionary, it might contain API keys too
                            if isinstance(value, dict):
                                # Look for any keys that seem like API keys
                                for subkey in value.keys():
                                    if "api" in subkey.lower() or "key" in subkey.lower():
                                        self.available_api_keys.add(subkey)
                                        
                                # If it contains an 'api_keys' list, add those too
                                if "api_keys" in value and isinstance(value["api_keys"], list):
                                    self.available_api_keys.update(value["api_keys"])
                    
                    # Legacy format handling
                    if "api_keys" in config_data:
                        if isinstance(config_data["api_keys"], dict):
                            # Dictionary with key-value pairs
                            self.available_api_keys.update(
                                config_data["api_keys"].keys()
                            )
                        elif isinstance(config_data["api_keys"], list):
                            # List of key names
                            self.available_api_keys.update(config_data["api_keys"])
                    if "available_api_keys" in config_data:
                        # Explicit list of available keys
                        self.available_api_keys.update(
                            config_data["available_api_keys"]
                        )
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
                                
            # Log summary of available data sources
            if hasattr(self, "data_sources") and self.data_sources:
                self.logger.info(f"Loaded {len(self.data_sources)} data sources")
                
                # Group sources by category
                categories = {}
                for source_name, source in self.data_sources.items():
                    category = source.get("category", "other")
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(source_name)
                
                # Log by category
                for category, sources in categories.items():
                    self.logger.info(f"  - {category.capitalize()}: {', '.join(sources)}")
                    
            self.logger.info(f"Total available API keys: {len(self.available_api_keys)}")
            if self.verbose:
                self.logger.info(f"API keys: {sorted(list(self.available_api_keys))}")
        
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

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

            # Store attempt information with the prompt that was used
            attempt_prompt = self._get_last_code_generation_prompt(user_prompt, query_type, system_prompt)
            attempts_info.append(
                {
                    "attempt": attempt_count,
                    "code_file": str(code_file_path) if code_file_path else None,
                    "code": code,
                    "output": code_output,
                    "execution_successful": execution_successful,
                    "retry_reason": "Output analysis suggests retry needed",
                    "prompt_used": attempt_prompt
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

        # Create a copy of the prompt for debugging and transparency
        generation_prompt = self._get_last_code_generation_prompt(user_prompt, query_type, system_prompt)
        
        return {
            "recommendation": recommendation,
            "response": summary,
            "solver": self.get_name(),
            "code_file": str(code_file_path) if code_file_path else None,
            "code": code,
            "code_output": code_output,
            "code_generation_prompt": generation_prompt,
            "response_metadata": response_metadata,
        }

    def determine_query_type(self, user_prompt: str) -> str:
        """
        Determine the type of query based on the user prompt.

        Args:
            user_prompt: The user prompt to analyze

        Returns:
            Query type: 'crypto', 'sports_mlb', 'sports_nhl', or 'unknown'
        """
        # First check if we have the required API keys for special types
        has_nhl_key = "SPORTS_DATA_IO_NHL_API_KEY" in self.available_api_keys
        if has_nhl_key and "NHL" in user_prompt or "hockey" in user_prompt.lower() or "kraken" in user_prompt.lower() or "golden knights" in user_prompt.lower():
            return "sports_nhl"
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
        
        # Check for NHL-related keywords and patterns
        nhl_keywords = [
            "hockey",
            "nhl",
            "national hockey league",
            "kraken",
            "golden knights",
            "vegas",
            "seattle",
            "maple leafs",
            "bruins",
            "penguins",
            "capitals",
            "rangers",
            "oilers",
            "canadiens",
            "stanley cup",
            "puck",
            "ice hockey",
            "hockey game",
            "hockey team",
            "nhl playoffs",
        ]
        
        nhl_patterns = [
            r"(kraken|golden knights|vegas|seattle).*(win|lose|beat|score|game)",
            r"(score|result).*(hockey|nhl|game)",
            r"(who won|outcome).*(hockey|nhl|game)",
            r"game between .*(teams|kraken|golden knights|maple leafs|bruins)",
        ]

        # Check for direct matches with keywords
        if any(kw in user_prompt_lower for kw in crypto_keywords):
            return "crypto"

        if any(kw in user_prompt_lower for kw in mlb_keywords):
            return "sports_mlb"
            
        if any(kw in user_prompt_lower for kw in nhl_keywords):
            return "sports_nhl"

        # Check for pattern matches
        import re

        for pattern in crypto_patterns:
            if re.search(pattern, user_prompt_lower):
                return "crypto"

        for pattern in mlb_patterns:
            if re.search(pattern, user_prompt_lower):
                return "sports_mlb"
                
        for pattern in nhl_patterns:
            if re.search(pattern, user_prompt_lower):
                return "sports_nhl"

        # If we can't determine, let's ask ChatGPT
        prompt = f"""Analyze the following query and determine if it's asking about:
1. Cryptocurrency prices (especially from Binance)
   Examples: "What was the price of BTC on March 30?", "How much did Ethereum cost yesterday?"

2. MLB sports data
   Examples: "Did the Blue Jays win against the Orioles?", "What was the score of the Yankees game?"

3. NHL hockey data
   Examples: "Did the Kraken beat the Golden Knights?", "What was the score of the Maple Leafs vs Bruins game?"

4. Something else
   Examples: "Who is the president?", "What's the weather like?", "How do I bake a cake?"

Query: {user_prompt}

Reply with ONLY ONE of: "crypto", "sports_mlb", "sports_nhl", or "unknown".
"""

        raw_response = query_chatgpt(
            prompt=prompt, api_key=self.api_key, model="gpt-4-turbo", verbose=False
        )

        response_text = raw_response.choices[0].message.content.strip().lower()

        if "crypto" in response_text:
            return "crypto"
        elif "sports_mlb" in response_text or "mlb" in response_text:
            return "sports_mlb"
        elif "sports_nhl" in response_text or "nhl" in response_text:
            return "sports_nhl"
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
        # Get template file from our discovered templates
        template_file = None
        template_code = None
        
        # Find the right template based on query type
        if query_type in self.sample_templates:
            template_file = self.sample_templates[query_type]
            self.logger.info(f"Using template for {query_type}: {template_file.name}")
        elif query_type == "unknown" and self.sample_templates:
            # For unknown query types, use the first available template as a generic starter
            template_file = next(iter(self.sample_templates.values()))
            self.logger.info(f"Using generic template for unknown query type: {template_file.name}")
            
        # Read template file if found
        if template_file and template_file.exists():
            try:
                with open(template_file, "r") as f:
                    template_code = f.read()
                    self.logger.info(f"Successfully loaded template code from {template_file.name}")
            except Exception as e:
                self.logger.error(f"Error reading template file {template_file}: {e}")
                # Continue without a template

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
        # Use the modular prompt generator from prompts module
        code_gen_prompt = get_code_generation_prompt(
            user_prompt=user_prompt,
            query_type=query_type,
            available_api_keys=self.available_api_keys,
            data_sources=self.data_sources if hasattr(self, "data_sources") else None,
            template_code=template_code,
            attempt=attempt,
            endpoint_info_getter=self._get_endpoint_info
        )

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
        elif query_type == "sports_nhl":
            if (
                "game" not in output.lower()
                and "team" not in output.lower()
                and "score" not in output.lower()
                and "hockey" not in output.lower()
                and "nhl" not in output.lower()
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
            query_type: Type of query ('crypto', 'sports_mlb', 'sports_nhl', or 'unknown')
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
        # Get template file from our discovered templates
        template_file = None
        template_code = None
        
        # Find the right template based on query type
        if query_type in self.sample_templates:
            template_file = self.sample_templates[query_type]
            self.logger.info(f"Using template for retry ({query_type}): {template_file.name}")
        elif query_type == "unknown" and self.sample_templates:
            # For unknown query types, use the first available template as a generic starter
            template_file = next(iter(self.sample_templates.values()))
            self.logger.info(f"Using generic template for retry (unknown query type): {template_file.name}")
            
        # Read template file if found
        if template_file and template_file.exists():
            try:
                with open(template_file, "r") as f:
                    template_code = f.read()
                    self.logger.info(f"Successfully loaded template code for retry from {template_file.name}")
            except Exception as e:
                self.logger.error(f"Error reading template file for retry {template_file}: {e}")
                # Continue without a template

        # Get current timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_basename = f"{query_type}_{timestamp}_retry{attempt}.py"
        code_file_path = self.executed_functions_dir / file_basename

        # Use the modular prompt generator for retry prompts, passing the template code
        code_gen_prompt = get_code_generation_prompt(
            user_prompt=user_prompt,
            query_type=query_type,
            available_api_keys=self.available_api_keys,
            data_sources=self.data_sources if hasattr(self, "data_sources") else None,
            template_code=template_code,
            attempt=attempt,
            endpoint_info_getter=self._get_endpoint_info
        )

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

        except Exception as e:
            self.logger.error(f"Error generating improved code: {e}")
            return None, None, None, False

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
        # Create feedback-specific prompt using get_code_generation_prompt
        # We'll set a higher attempt number to indicate this is a feedback-based retry
        feedback_attempt = attempt + 10  # Use a higher number to distinguish feedback retries
        
        # First, get the standard retry prompt from the prompt module
        code_gen_prompt = get_code_generation_prompt(
            user_prompt=user_prompt,
            query_type=query_type,
            available_api_keys=self.available_api_keys,
            data_sources=self.data_sources if hasattr(self, "data_sources") else None,
            template_code=template_code,
            attempt=feedback_attempt,  # Use higher attempt number
            endpoint_info_getter=self._get_endpoint_info
        )
        
        # Add specific feedback about the previous output
        feedback_section = f"""
FEEDBACK ON PREVIOUS EXECUTION:
Here's the output from the previous code execution:
```
{previous_output}
```

Issues with the previous output:
- The output doesn't clearly provide a recommendation in the expected format
- It doesn't properly extract and present the needed information
- Your code must return "recommendation: p1", "recommendation: p2", "recommendation: p3", or "recommendation: p4"

CRITICALLY IMPORTANT:
1. ALWAYS use environment variables loaded with python-dotenv for all API keys
2. Return results in a clear format with a "recommendation: pX" line
3. Make your code robust to handle all error cases gracefully
"""
        
        # Combine standard prompt with feedback
        final_prompt = code_gen_prompt + "\n\n" + feedback_section

        # Query ChatGPT for improved code generation
        try:
            raw_response = query_chatgpt(
                prompt=final_prompt,
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

    def _discover_sample_templates(self) -> Dict[str, Path]:
        """
        Dynamically discover all available sample function templates.
        
        This method scans the sample_functions directory for template files and
        maps them to their corresponding query types based on naming convention.
        
        Returns:
            Dictionary mapping query types to template file paths
        """
        templates = {}
        
        # Check if directory exists
        if not self.sample_functions_dir.exists():
            self.logger.warning(f"Sample functions directory not found: {self.sample_functions_dir}")
            return templates
            
        # Look for files following the pattern query_*.py
        for file_path in self.sample_functions_dir.glob("query_*.py"):
            # Extract query type from the filename (e.g., query_binance_price.py -> binance_price)
            file_name = file_path.stem  # 'query_binance_price'
            if file_name.startswith("query_"):
                # Extract the part after "query_"
                query_type = file_name[6:]  # 'binance_price'
                
                # Map common prefixes to simplified query types
                if query_type == "binance_price":
                    templates["crypto"] = file_path
                elif query_type.startswith("sports_"):
                    # For sports templates, keep the full name (sports_mlb, sports_nhl, etc.)
                    templates[query_type] = file_path
                else:
                    # For other templates, register with their full name
                    templates[query_type] = file_path
                    
                self.logger.info(f"Discovered template for query type '{query_type}': {file_path.name}")
                
        # Set up fallback relationships for similar query types
        fallbacks = {}
        
        # Define sports fallbacks - if a specific league template isn't available, 
        # try to use another sports template as fallback
        sports_templates = {k: v for k, v in templates.items() if k.startswith("sports_")}
        if sports_templates:
            # Use MLB as preferred fallback if available
            if "sports_mlb" in sports_templates:
                fallback = sports_templates["sports_mlb"]
                for sports_type in ["sports_nba", "sports_nfl", "sports_nhl"]:
                    if sports_type not in templates:
                        fallbacks[sports_type] = fallback
            # Otherwise use the first available sports template
            elif sports_templates:
                first_sports = next(iter(sports_templates.values()))
                for sports_type in ["sports_mlb", "sports_nba", "sports_nfl", "sports_nhl"]:
                    if sports_type not in templates:
                        fallbacks[sports_type] = first_sports
        
        # Add fallbacks to templates
        templates.update(fallbacks)
        
        return templates
            
    def _get_endpoint_info(self, category: str, endpoint_type: str) -> str:
        """
        Get endpoint information for a specific category and type.
        
        Args:
            category: The category of data source (e.g., "crypto", "sports")
            endpoint_type: The type of endpoint (e.g., "primary", "proxy")
            
        Returns:
            The endpoint URL or a default value if not found
        """
        # Default values for common endpoints
        defaults = {
            "crypto": {
                "primary": "https://api.binance.com/api/v3",
                "proxy": "Not available"
            },
            "sports": {
                "primary": "https://api.sportsdata.io/v3"
            }
        }
        
        # Check if we have data sources
        if not hasattr(self, "data_sources") or not self.data_sources:
            return defaults.get(category, {}).get(endpoint_type, "Not available")
            
        # Look for matching data sources
        for source in self.data_sources.values():
            if source.get("category") == category:
                endpoints = source.get("endpoints", {})
                if endpoint_type in endpoints:
                    return endpoints[endpoint_type]
                    
        # Return default if not found
        return defaults.get(category, {}).get(endpoint_type, "Not available")
        
    def _get_last_code_generation_prompt(self, user_prompt: str, query_type: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate the code generation prompt for storage and debugging.
        Instead of using a simplified version, we'll now store the actual prompt with template code.
        
        Args:
            user_prompt: The user prompt
            query_type: Type of query ('crypto', 'sports_mlb', 'sports_nhl', or 'unknown')
            system_prompt: Optional system prompt
            
        Returns:
            The full code generation prompt including template code
        """
        # Get template code for this query type
        template_code = None
        template_file = None
        
        # Find the right template based on query type
        if query_type in self.sample_templates:
            template_file = self.sample_templates[query_type]
        elif query_type == "unknown" and self.sample_templates:
            # For unknown query types, use the first available template as a generic starter
            template_file = next(iter(self.sample_templates.values()))
            
        # Read template file if found
        if template_file and template_file.exists():
            try:
                with open(template_file, "r") as f:
                    template_code = f.read()
            except Exception:
                # Continue without a template if there's an error
                pass
        
        # Generate the full prompt using the prompt generator
        full_prompt = get_code_generation_prompt(
            user_prompt=user_prompt,
            query_type=query_type,
            available_api_keys=self.available_api_keys,
            data_sources=self.data_sources if hasattr(self, "data_sources") else None,
            template_code=template_code,
            attempt=1,  # Always use first attempt format for storing
            endpoint_info_getter=self._get_endpoint_info
        )
        
        # Add a summary section specifically listing ALL API keys from config file
        # This ensures API keys are prominently visible in the stored prompt
        api_keys_summary = "\n\nAVAILABLE API KEYS SUMMARY:\n"
        for api_key_name in sorted(self.available_api_keys):
            api_keys_summary += f"- {api_key_name}\n"
        
        # Add data sources summary if available
        if hasattr(self, "data_sources") and self.data_sources:
            api_keys_summary += "\nAVAILABLE DATA SOURCES:\n"
            for source_name, source in self.data_sources.items():
                name = source.get("name", source_name)
                category = source.get("category", "Unknown")
                api_keys_summary += f"- {name} (Category: {category})\n"
                
                # Add API keys for this source
                if "api_keys" in source:
                    for api_key in source["api_keys"]:
                        api_keys_summary += f"  * API Key: {api_key}\n"
                        
                # Add endpoints info
                if "endpoints" in source:
                    for endpoint_type, url in source["endpoints"].items():
                        api_keys_summary += f"  * {endpoint_type} endpoint: {url}\n"
        
        # Combine original prompt with the API keys summary for maximum visibility
        enhanced_prompt = full_prompt + api_keys_summary
        
        # Return the enhanced prompt
        return enhanced_prompt

    def get_name(self) -> str:
        """
        Get the name of the solver.

        Returns:
            The name of the solver
        """
        return "code_runner"
