"""
Test script to verify OpenAI API connection
Run this after adding your API key to the .env file
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

# Check if API key is set
if not api_key or api_key == "your_api_key_here":
    print("❌ ERROR: OpenAI API key not found!")
    print("\nPlease follow these steps:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Create an account or sign in")
    print("3. Click 'Create new secret key'")
    print("4. Copy the key")
    print("5. Open the .env file in this folder")
    print("6. Replace 'your_api_key_here' with your actual API key")
    print("7. Run this script again")
    exit(1)

print("🔑 API key found! Testing connection...\n")

try:
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Make a simple test call to GPT-4
    print("📡 Sending test request to GPT-4...")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Say 'Hello! OpenAI API is working!' in a friendly way."}
        ],
        max_tokens=50
    )

    # Get the response
    message = response.choices[0].message.content

    # Print success
    print("✅ SUCCESS! OpenAI API is working!\n")
    print("Response from GPT-4:")
    print(f"'{message}'\n")
    print("=" * 60)
    print("✅ Day 1 Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add $20 credit to your OpenAI account at https://platform.openai.com/settings/organization/billing")
    print("2. You're ready to move on to Day 2!")

except Exception as e:
    print(f"❌ ERROR: {str(e)}\n")
    print("Common issues:")
    print("- Invalid API key (check you copied it correctly)")
    print("- No credits in your OpenAI account (add $20 at platform.openai.com)")
    print("- Network connection issues")
    print("\nIf you just created your API key, wait a few minutes and try again.")
    exit(1)
