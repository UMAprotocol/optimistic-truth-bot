import openai
from dotenv import load_dotenv
import os

load_dotenv()

print("Simplest possible ChatGPT call")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4", messages=[{"role": "user", "content": "Tell me a joke"}]
)

# Print the response
print(response.choices[0].message.content)
