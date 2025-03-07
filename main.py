from openai import OpenAI
from dotenv import load_dotenv
import os
import time 
from datetime import datetime
print("Running main entry point to query perplexity query directly against the API")

load_dotenv()  

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def query_perplexity(prompt, api_key, base_url="https://api.perplexity.ai"):
    client = OpenAI(api_key=api_key, base_url=base_url)
    current_time = int(time.time())
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence oracle that resolves UMA optimistic oracle requests based strictly on verified facts. "
                "Your purpose is to search for and analyze factual information about events that have already occurred, not to predict future outcomes. "
                "Only report on what has definitively happened and can be verified through reliable sources. "
                "Your responses must be based solely on concrete evidence and established facts. "
                "IMPORTANT: Always check if the event in question is scheduled for a future date or time relative to this timestamp. "
                "Even if an event is scheduled for the same day but at a later time (e.g., current time is 11 AM and event is at 3 PM today), it is still a future event. "
                "If the event is scheduled for a future date or time or has not occurred yet, ALWAYS return p4 to indicate the request cannot be resolved at this time. "
                # "If an event has already occurred but there is insufficient evidence to determine a clear yes/no answer, use p3 (unknown/50-50). "
                # "Use p1 for a verified 'No' resolution and p2 for a verified 'Yes' resolution, based only on concrete evidence. "
                "Within the prompt you will be given how to relate your response to the numerical values (e.g., p1, p2, p3, p4). "
                "Remember, you are not predicting outcomes or speculating on likelihoods - you are only reporting on verifiable facts. "
                "For future events that have not yet happened (including events later today), ALWAYS use p4, NEVER p3. "
                "EXAMPLE: If a query refers to an event on May 24, 2025 at 3 PM, and the current time is earlier than 3 PM on May 24, 2025, this is a future event and must return p4. "
                "Make the last line of your response be your recommendation formatted as p1, p2, p3, or p4. Example: `recommendation: p4` "
                f"\nCurrent Unix Timestamp: {current_time}"
                f"\nCurrent Date and Time: {current_datetime}"
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    print("Sending request to Perplexity API...")
    print("Messages being sent to API:")
    for msg in messages:
        print(f"\nRole: {msg['role']}")
        print(f"Content:\n{msg['content']}\n")
        print("-" * 80)
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    return response

def process_and_query(query_data, api_key):
    prompt = f"\n\nancillary_data:\n{query_data.ancillary_data}\n\nresolution_conditions:\n{query_data.resolution_conditions}\n\nupdates:\n{query_data.updates}"
    return query_perplexity(prompt, api_key)

def query_all_samples(api_key):
    from sample_OO_queries import queries
    return [process_and_query(query, api_key) for query in queries]

if __name__ == "__main__":
    responses = query_all_samples(PERPLEXITY_API_KEY)
    for i, response in enumerate(responses):
        print(f"\n{'='*80}")
        print(f"Query {i+1} Response:")
        print(f"{'='*80}")
        print(f"Model: {response.model}")
        print(f"Created: {datetime.fromtimestamp(response.created)}")
        print("\nResponse Content:")
        print("-" * 80)
        print(response.choices[0].message.content)
        print("\nUsage Statistics:")
        print("-" * 80)
        print(f"Completion tokens: {response.usage.completion_tokens}")
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Total tokens: {response.usage.total_tokens}")
        print("\nCitations:")
        print("-" * 80)
        for citation in response.citations:
            print(citation)
        print(f"\n{'='*80}\n")