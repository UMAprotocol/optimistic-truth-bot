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
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence oracle that fulfills UMA optimistic oracle requests. You're goal is to"
                "look online and find information to correctly resolve the market based on the resolution conditions and updates provided."
                "Being accurate is more important than anything else, and you should do whatever it takes to be accurate."
                "Only if you are totally sure that you know the correct answer should you return that response, else return p4 which is early request, that the market is unresovable at this time."
                "Within the prompt you will be given how to relate your response to the numerical values (eg p1,p2,p3,p4)."
                "p4 might not be defined which is again the early request response which should be returned if you think the market is not resovable."
                "make the last line of your response be your recommendation formatted as p1,p2,p3,p4. eg `recommendation: p4`"
                f"\nCurrent Unix Timestamp: {str(int(time.time()))}"
                f"\nCurrent Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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

def query_first_sample(api_key):
    from sample_OO_queries import queries
    first_query = queries[0]
    return process_and_query(first_query, api_key)

if __name__ == "__main__":
    response = query_first_sample(PERPLEXITY_API_KEY)
    print("\nPerplexity API Response:")
    print("-" * 80)
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