from langchain_community.chat_models import ChatPerplexity
import os
from dotenv import load_dotenv
load_dotenv()

print("Running simple perplexity query with langchain")

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
os.environ["PPLX_API_KEY"] = PERPLEXITY_API_KEY

chat = ChatPerplexity(
    model="llama-3.1-sonar-small-128k-online", pplx_api_key=PERPLEXITY_API_KEY
)
prompt = "How many stars are in the universe?"
print("Prompt: ", prompt)

response = chat.invoke(prompt)

print("Response: ", response.content)
