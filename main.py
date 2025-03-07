from openai import OpenAI
from dotenv import load_dotenv
import os
import time 
from datetime import datetime
from urllib.parse import urlparse
import re
import requests
import json

print("Running main entry point to query perplexity query directly against the API")

load_dotenv()  

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_BASE = "https://api.perplexity.ai/chat/completions"

def query_perplexity(prompt, api_key, domain_filters=None, base_url="https://api.perplexity.ai"):
    current_time = int(time.time())
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add domain filtering information to the system prompt if applicable
    domain_filter_instruction = ""
    if domain_filters:
        domain_str = ", ".join(domain_filters)
        domain_filter_instruction = (
            f"DOMAIN RESTRICTION: You are ONLY allowed to search and cite information from the following domain(s): {domain_str}. "
            "This is a STRICT requirement. Do NOT use or cite ANY information from other domains. "
            "If you cannot find relevant information from these specific domains, explicitly state this limitation. "
        )
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence oracle that resolves UMA optimistic oracle requests based strictly on verified facts. "
                "Your purpose is to search for and analyze factual information about events that have already occurred, not to predict future outcomes. "
                f"{domain_filter_instruction}"
                "MANDATORY RULE: If the request mentions a specific URL as the resolution source (e.g., 'The resolution source for this market will be...'), "
                "then you MUST COMPLETELY IGNORE all other data sources. ONLY use information from the EXACT URL mentioned "
                "as the resolution source. This rule overrides everything else. STOP your search and do not consider ANY other sources. "
                "If you cannot access the exact URL specified as the resolution source, explicitly state this and return p4. "
                "If the specified URL does not contain sufficient information to answer the query, explicitly state this and return p3. "
                "Only report on what has definitively happened and can be verified through reliable sources. "
                "Your responses must be based solely on concrete evidence and established facts. "
                "CRITICAL TIMING RULE: Always check if the event in question is scheduled for a future date or time relative to this timestamp. "
                "Even if an event is scheduled for the same day but at a later time (e.g., current time is 11 AM and event is at 3 PM today), it is still a future event. "
                "If the event is scheduled for a future date or time or has not occurred yet, ALWAYS return p4 to indicate the request cannot be resolved at this time. "
                "NEVER resolve a market for an event that hasn't happened yet, even if you think you know the outcome. "
                "SPECIFIC CASE: If a query refers to a White House Crypto Summit on March 7, 2025, and the current time is before the end of that summit, this is a future event and must return p4. "
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
    
    # Create the request payload
    payload = {
        "model": "sonar-reasoning-pro",
        "messages": messages,
    }
    
    # Add domain filters if provided
    if domain_filters:
        print(f"Using domain filters: {domain_filters}")
        payload["search_domain_filter"] = domain_filters
    
    # Setup headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Make the API request
    try:
        response = requests.post(
            PERPLEXITY_API_BASE,
            headers=headers,
            json=payload
        )
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        # Parse the response
        return response.json()
    except Exception as e:
        print(f"Error calling Perplexity API: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Response text: {response.text}")
        raise

def extract_domain_from_url(url_text):
    # Extract URL from text
    url_match = re.search(r'https?://[^\s"\'<>]+', url_text)
    if not url_match:
        return None
    
    url = url_match.group(0)
    
    # Parse the URL and extract the domain
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain
    except:
        return None

def process_and_query(query_data, api_key):
    # Extract the original prompt content
    prompt = f"\n\nancillary_data:\n{query_data.ancillary_data}\n\nresolution_conditions:\n{query_data.resolution_conditions}\n\nupdates:\n{query_data.updates}"
    
    # Look for resolution source URLs
    domain_filters = None
    if "resolution source" in query_data.ancillary_data.lower() and "http" in query_data.ancillary_data:
        # Extract domain from URL to use as a filter
        domain = extract_domain_from_url(query_data.ancillary_data)
        if domain:
            domain_filters = [domain]
            print(f"Extracted domain filter: {domain}")
            
            # Add even more explicit instructions about the domain restriction
            prompt = (
                f"CRITICAL INSTRUCTION: This query REQUIRES you to ONLY use data from the domain '{domain}'. "
                f"Do NOT use or cite ANY information from other domains. "
                f"The specific URL mentioned in the query is the ONLY authorized source for resolving this market. "
                f"\n\n{prompt}"
            )
    
    return query_perplexity(prompt, api_key, domain_filters)

def query_all_samples(api_key):
    from sample_OO_queries import queries
    return [process_and_query(query, api_key) for query in queries]

if __name__ == "__main__":
    responses = query_all_samples(PERPLEXITY_API_KEY)
    for i, response in enumerate(responses):
        print(f"\n{'='*80}")
        print(f"Query {i+1} Response:")
        print(f"{'='*80}")
        
        # Handle the direct API response format
        model = response.get("model", "unknown")
        created = response.get("created", 0)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "No content")
        usage = response.get("usage", {})
        
        print(f"Model: {model}")
        print(f"Created: {datetime.fromtimestamp(created)}")
        print("\nResponse Content:")
        print("-" * 80)
        print(content)
        print("\nUsage Statistics:")
        print("-" * 80)
        print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
        print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
        print(f"Total tokens: {usage.get('total_tokens', 'N/A')}")
        print("\nCitations:")
        print("-" * 80)
        for citation in response.get("citations", []):
            print(citation)
        print(f"\n{'='*80}\n")