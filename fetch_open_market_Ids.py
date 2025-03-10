import sys
from web3 import Web3
from dotenv import load_dotenv
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import load_abi, UmaCtfAdapter


def main(from_block, output_file):
    # Load environment and setup Web3
    load_dotenv()
    w3 = Web3(Web3.HTTPProvider(os.getenv("POLYGON_RPC_URL")))
    if not w3.is_connected():
        print("Failed to connect to Polygon RPC")
        return

    print(f"Connected to Polygon: {w3.is_connected()}")

    # Setup contract instance
    adapter_contract = w3.eth.contract(
        address=UmaCtfAdapter, abi=load_abi("UmaCtfAdapter.json")
    )

    events = adapter_contract.events.QuestionInitialized.get_logs(
        from_block=from_block, to_block="latest"
    )

    print(f"Found {len(events)} QuestionInitialized events")

    results = []
    total_events = len(events)
    processed = 0

    # Process each event
    print("\nProcessing question details:")
    print("=" * 80)

    def fetch_question_data(event):
        nonlocal processed

        question_id = event["args"]["questionID"]
        hex_question_id = (
            question_id.hex() if isinstance(question_id, bytes) else hex(question_id)
        )
        if not hex_question_id.startswith("0x"):
            hex_question_id = "0x" + hex_question_id

        try:
            # Query question data
            question_data = adapter_contract.functions.questions(question_id).call()

            # Extract data with correct indices
            timestamp = question_data[0]
            proposal_bond = question_data[2]
            resolved = question_data[4]
            creator = question_data[8]

            # Convert bytes to string for JSON serialization
            ancillary_data_bytes = question_data[9]
            try:
                raw_data = ancillary_data_bytes.decode("utf-8")

                # Replace escape characters
                raw_data = raw_data.replace("\u201c", '"').replace("\u201d", '"')

                # Split at res_data if present
                if "res_data:" in raw_data:
                    question_part, res_part = raw_data.split("res_data:", 1)

                    # Further split to remove updates text
                    if "Updates made by" in res_part:
                        res_part = res_part.split("Updates made by", 1)[0].strip()

                    # Clean up any trailing commas or whitespace
                    res_part = res_part.strip()
                    if res_part.endswith(","):
                        res_part = res_part[:-1].strip()

                    ancillary_data = question_part.strip()
                    resolution_conditions = "res_data:" + res_part.strip()
                else:
                    ancillary_data = raw_data
                    resolution_conditions = "x"  # Default placeholder
            except UnicodeDecodeError:
                # Fallback to hex representation if not valid UTF-8
                ancillary_data = "0x" + ancillary_data_bytes.hex()
                resolution_conditions = "x"  # Default placeholder

            # Get question updates - needs both questionID and creator address
            updates = adapter_contract.functions.getUpdates(question_id, creator).call()

            # Convert any bytes in updates to strings
            string_updates = []
            for update in updates:
                try:
                    string_updates.append(update.decode("utf-8"))
                except (UnicodeDecodeError, AttributeError):
                    if isinstance(update, bytes):
                        string_updates.append("0x" + update.hex())
                    else:
                        string_updates.append(str(update))

            # Format according to QueryData structure
            return {
                "query_id": hex_question_id,
                "unix_timestamp": timestamp,
                "ancillary_data": ancillary_data,
                "resolution_conditions": resolution_conditions,
                "updates": string_updates,
                "creator": creator,
                "proposal_bond": proposal_bond,
            }

        except Exception as e:
            return {"query_id": hex_question_id, "error": str(e)}
        finally:
            # Update progress
            processed += 1
            progress = int(50 * processed / total_events)
            sys.stdout.write(
                f"\r[{'=' * progress}{' ' * (50 - progress)}] {processed}/{total_events} ({processed/total_events:.1%})"
            )
            sys.stdout.flush()

    # Use ThreadPoolExecutor to fetch question data in parallel
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(fetch_question_data, event): event for event in events
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Complete progress bar
    print("\n")

    # Prepare data for JSON export (matching QueryData format with added fields)
    export_data = []
    for result in results:
        if "error" not in result:
            export_data.append(
                {
                    "query_id": result["query_id"],
                    "unix_timestamp": result["unix_timestamp"],
                    "ancillary_data": result["ancillary_data"],
                    "resolution_conditions": result["resolution_conditions"],
                    "updates": result["updates"],
                    "creator": result["creator"],
                    "proposal_bond": result["proposal_bond"],
                }
            )
        else:
            print(f"Error with question {result['query_id']}: {result['error']}")

    # Save to JSON file
    with open(output_file, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\nSaved {len(export_data)} queries to {output_file}")

    # Summary of open vs resolved
    open_questions = [q for q in results if "_resolved" in q and not q["_resolved"]]
    resolved_questions = [q for q in results if "_resolved" in q and q["_resolved"]]

    print("\n" + "=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Total questions: {len(results)}")
    print(f"Open questions: {len(open_questions)}")
    print(f"Resolved questions: {len(resolved_questions)}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python fetch_open_market_Ids.py <from_block> [output_file.json]")
        sys.exit(1)

    try:
        from_block = int(sys.argv[1])
    except ValueError:
        print("Error: from_block must be an integer")
        sys.exit(1)

    output_file = sys.argv[2] if len(sys.argv) == 3 else "queries_output.json"

    main(from_block, output_file)
