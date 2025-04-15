import json
import os
import glob
from collections import Counter, defaultdict

# Path to the output files
output_dir = os.path.join(os.path.dirname(__file__), "outputs")
output_files = glob.glob(os.path.join(output_dir, "output_*.json"))

print(f"Found {len(output_files)} output files to analyze")

# Initialize counters
correct_count = 0
incorrect_count = 0
no_data_count = 0  # recommendation = p4 but resolved_price_outcome != p4
recommendation_counters = Counter()
resolution_counters = Counter()
recommendation_vs_resolution = defaultdict(Counter)
bad_responses = []

# For additional metrics
p123_correct = 0
p123_total = 0
p12_correct = 0
p12_total = 0

# Analyze each file
for file_path in output_files:
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        recommendation = data.get("recommendation")
        resolved_outcome = data.get("resolved_price_outcome")

        # Replace None with 'None' string for consistent sorting
        if recommendation is None:
            recommendation = "None"
        if resolved_outcome is None:
            resolved_outcome = "None"

        # Count recommendations and resolutions
        recommendation_counters[recommendation] += 1
        resolution_counters[resolved_outcome] += 1

        # Track recommendation vs actual resolution
        recommendation_vs_resolution[recommendation][resolved_outcome] += 1

        # Check if correct
        if recommendation == resolved_outcome:
            correct_count += 1

            # Count correct p1/p2/p3 predictions
            if recommendation in ["p1", "p2", "p3"]:
                p123_correct += 1

            # Count correct p1/p2 predictions
            if recommendation in ["p1", "p2"]:
                p12_correct += 1
        else:
            incorrect_count += 1

            # Check for no data cases (p4 recommendation but different resolution)
            if recommendation == "p4" and resolved_outcome != "p4":
                no_data_count += 1

            # Flag particularly bad responses (p3 recommendation when resolution wasn't p3)
            if recommendation == "p3" and resolved_outcome != "p3":
                file_name = os.path.basename(file_path)
                question_id = data.get("question_id_short", "unknown")
                bad_responses.append(
                    {
                        "file": file_name,
                        "question_id": question_id,
                        "recommendation": recommendation,
                        "resolved_outcome": resolved_outcome,
                    }
                )

        # Count total p1/p2/p3 recommendations
        if recommendation in ["p1", "p2", "p3"]:
            p123_total += 1

        # Count total p1/p2 recommendations
        if recommendation in ["p1", "p2"]:
            p12_total += 1

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Calculate accuracy
total_analyzed = correct_count + incorrect_count
accuracy = (correct_count / total_analyzed * 100) if total_analyzed > 0 else 0

# Calculate p123 accuracy (ignoring p4)
p123_accuracy = (p123_correct / p123_total * 100) if p123_total > 0 else 0

# Calculate p12 accuracy (only considering p1/p2)
p12_accuracy = (p12_correct / p12_total * 100) if p12_total > 0 else 0

# Print results
print("\n===== ANALYSIS RESULTS =====")
print(f"Total files analyzed: {total_analyzed}")
print(f"Correct recommendations: {correct_count} ({accuracy:.2f}%)")
print(f"Incorrect recommendations: {incorrect_count} ({100-accuracy:.2f}%)")
print(f"Cases where model couldn't find data (p4): {no_data_count}")

print(
    f"\nAccuracy when ignoring p4 (only p1/p2/p3): {p123_correct}/{p123_total} ({p123_accuracy:.2f}%)"
)
print(
    f"Accuracy when only considering p1/p2: {p12_correct}/{p12_total} ({p12_accuracy:.2f}%)"
)

print("\nRecommendation distribution:")
for rec, count in sorted(recommendation_counters.items()):
    print(f"  {rec}: {count} ({count/total_analyzed*100:.2f}%)")

print("\nResolution distribution:")
for res, count in sorted(resolution_counters.items()):
    print(f"  {res}: {count} ({count/total_analyzed*100:.2f}%)")

print("\nRecommendation vs Resolution breakdown:")
for rec, res_counter in sorted(recommendation_vs_resolution.items()):
    print(f"  {rec} recommendations:")
    for res, count in sorted(res_counter.items()):
        print(f"    → {res}: {count}")

if bad_responses:
    print("\nParticularly bad responses (p3 when resolution wasn't p3):")
    for response in bad_responses:
        print(f"  File: {response['file']} (Question ID: {response['question_id']})")
        print(
            f"    Recommendation: {response['recommendation']} | Actual resolution: {response['resolved_outcome']}"
        )
