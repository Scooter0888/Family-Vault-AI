"""
OpenAI Helper Functions
Functions for interacting with OpenAI API for AI Granny interviews
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_followup_questions(question, answer, num_followups=2):
    """
    Generate adaptive follow-up questions based on the parent's answer

    Args:
        question (str): The original question that was asked
        answer (str): The parent's response
        num_followups (int): Number of follow-up questions to generate (default: 2)

    Returns:
        list: List of follow-up questions as strings
    """

    # Create the prompt for GPT-4
    prompt = f"""You are an empathetic interviewer helping to preserve an elderly parent's life story and memories.

Original question: "{question}"

Parent's answer: "{answer}"

Based on the parent's answer, generate {num_followups} thoughtful follow-up questions that:
1. **PRIORITY: Identify missing critical information** - If they mentioned people (siblings, parents, friends) but didn't mention WHERE they were born, WHEN they were born, or other key biographical details, ask those specific questions first
2. **Fill information gaps** - Look for incomplete stories or details that need clarification (e.g., "Where was your brother Clint born?", "What year did you move to that house?")
3. Go deeper into specific details they mentioned
4. Explore emotions or significance behind what they shared
5. Are natural and conversational (like a caring family member would ask)
6. Help preserve complete, detailed information for family legacy
7. Are respectful and gentle (avoid questions that might be too painful unless they brought it up)

**Important**: If they mentioned family members (siblings, parents, children) without key details like birth place, birth date, or full names, those are CRITICAL gaps to fill with follow-up questions.

Return ONLY the follow-up questions, one per line, without numbering or bullet points.
"""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert interviewer specializing in oral history and family legacy preservation. You ask thoughtful, empathetic follow-up questions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Balanced creativity
            max_tokens=200
        )

        # Extract the follow-up questions
        followup_text = response.choices[0].message.content.strip()

        # Split into individual questions
        followups = [q.strip() for q in followup_text.split('\n') if q.strip()]

        # Return the requested number of follow-ups
        return followups[:num_followups]

    except Exception as e:
        error_msg = str(e)
        print(f"Error generating follow-ups: {error_msg}")

        # Provide user-friendly error messages
        if "rate_limit" in error_msg.lower():
            print("⚠️ Rate limit reached. Please wait a moment and try again.")
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            print("⚠️ API key issue. Please check your OpenAI API key in the .env file.")
        elif "insufficient_quota" in error_msg.lower():
            print("⚠️ OpenAI account has insufficient credits. Please add credits at platform.openai.com.")
        else:
            print(f"⚠️ Unexpected error: {error_msg}")

        return []


def test_followup_generation():
    """
    Test function to verify follow-up generation works
    """

    # Test example
    question = "What was your first real job, and what did you learn from it?"
    answer = """My first real job was working at Meyer's Hardware Store when I was 16.
    Mr. Meyer, the owner, he was tough but fair. He taught me that showing up on time
    meant showing up 10 minutes early. I made $1.25 an hour, which felt like a fortune
    back then."""

    print("Testing follow-up generation...")
    print(f"\nOriginal Question: {question}")
    print(f"\nAnswer: {answer}")
    print("\nGenerating follow-ups...")

    followups = generate_followup_questions(question, answer, num_followups=2)

    print("\nFollow-up Questions:")
    for i, followup in enumerate(followups, 1):
        print(f"{i}. {followup}")

    return followups


if __name__ == "__main__":
    # Run test if this file is executed directly
    test_followup_generation()
