import os
from anthropic import Anthropic

# This initializes the client using your GitHub secret key
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# This requests the list of all models available to your account
models = client.models.list()

print("--- AVAILABLE MODELS ---")
for model in models.data:
    print(f"Model ID: {model.id}")
