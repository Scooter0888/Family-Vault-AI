"""
Q&A Query Module
Search through interview data and answer questions using AI
"""

import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_interview_file(filepath):
    """
    Load interview data from JSON file

    Args:
        filepath (str): Path to the interview JSON file

    Returns:
        dict: Interview data or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return None


def get_all_interview_files():
    """
    Get list of all saved interview files

    Returns:
        list: List of (filename, filepath) tuples
    """
    profiles_dir = Path('data/parent_profiles')
    if not profiles_dir.exists():
        return []

    files = []
    for filepath in profiles_dir.glob('*.json'):
        files.append((filepath.name, str(filepath)))

    # Sort by modification time (newest first)
    files.sort(key=lambda x: Path(x[1]).stat().st_mtime, reverse=True)

    return files


def search_and_answer(question, interview_data):
    """
    Search through interview data and generate an answer to the question

    Args:
        question (str): The user's question
        interview_data (dict): Complete interview data including responses and extracted data

    Returns:
        dict: Answer with sources and confidence
    """

    parent_name = interview_data.get('parent_name', 'the parent')

    # Prepare the context from interview data
    context = f"Interview with {parent_name}\n\n"

    # Add Q&A from interview
    if 'interview_data' in interview_data:
        qa_data = interview_data['interview_data'].get('questions_and_answers', [])
        context += "=== Interview Responses ===\n\n"

        for idx, item in enumerate(qa_data, 1):
            context += f"Q{idx}: {item['question']}\n"
            context += f"A: {item['answer']}\n"

            # Include follow-ups
            if 'followups' in item and item['followups']:
                for fup_idx, followup in enumerate(item['followups'], 1):
                    context += f"  Follow-up Q{fup_idx}: {followup['question']}\n"
                    context += f"  Follow-up A: {followup['answer']}\n"

            context += "\n"

    # Add extracted structured data
    if 'extracted_data' in interview_data and interview_data['extracted_data']:
        context += "\n=== Extracted Structured Data ===\n\n"
        context += json.dumps(interview_data['extracted_data'], indent=2)

    # Get today's date for age calculations
    from datetime import date
    today = date.today()
    today_str = today.strftime("%B %d, %Y")  # e.g., "January 12, 2026"

    # Create the query prompt
    query_prompt = f"""You are helping a family access their parent's preserved memories and stories.

Today's date: {today_str}

Context - Interview data for {parent_name}:
{context}

User's question: "{question}"

Instructions:
1. Search through the interview responses and extracted data above
2. Find information relevant to answering the question
3. Answer CONCISELY and DIRECTLY - just state the facts
4. If asked about age, CALCULATE it from birth year and today's date ({today_str})
5. DO NOT mention where the information came from (no "In Q2" or "during the interview" or similar references)
6. DO NOT include citations or explain the source
7. DO NOT use quotes or reference specific questions
8. Just answer the question naturally and conversationally
9. If the information isn't in the interview, say "I don't have information about that in this interview."
10. Keep your answer brief - 1-3 sentences maximum unless more detail is clearly needed

Examples:
Question: "What year was John born?"
GOOD: "John was born in 1967."

Question: "How old is John?"
GOOD: "John is 58 years old. He was born in 1967."

Provide your concise answer below:
"""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an AI assistant helping families access their parent's preserved memories. You answer questions concisely and directly based solely on interview data provided. You never mention sources, citations, or where information came from. You are warm and natural in your responses about {parent_name}'s story."
                },
                {
                    "role": "user",
                    "content": query_prompt
                }
            ],
            temperature=0.7,
            max_tokens=300
        )

        answer = response.choices[0].message.content.strip()

        return {
            "success": True,
            "answer": answer,
            "parent_name": parent_name,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "answer": None,
            "parent_name": parent_name,
            "error": str(e)
        }


def test_query():
    """
    Test function to verify query works
    """

    # Sample interview data
    sample_data = {
        "parent_name": "Margaret Smith",
        "interview_data": {
            "questions_and_answers": [
                {
                    "question": "Where did you grow up?",
                    "answer": "I grew up in Cleveland, Ohio on Maple Street. We lived there from 1946 until I went to college in 1966.",
                    "followups": []
                }
            ]
        },
        "extracted_data": {
            "places": [
                {
                    "location": "Cleveland, Ohio",
                    "significance": "Childhood home",
                    "time_period": "1946-1966"
                }
            ]
        }
    }

    question = "Where did Margaret grow up?"

    print(f"Testing query: '{question}'")
    print("\nSearching interview data...")

    result = search_and_answer(question, sample_data)

    if result['success']:
        print("\n✅ Query successful!")
        print(f"\nAnswer:\n{result['answer']}")
    else:
        print(f"\n❌ Query failed: {result['error']}")


if __name__ == "__main__":
    test_query()
