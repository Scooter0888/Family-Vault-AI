"""
Data Extraction Module
Extract structured information from interview responses
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_structured_data(interview_data, parent_name):
    """
    Extract structured data from complete interview responses

    Args:
        interview_data (list): List of interview Q&A with followups
        parent_name (str): Name of the person being interviewed

    Returns:
        dict: Extracted structured data organized by category
    """

    # Combine all interview responses into a single text
    full_transcript = f"Interview with {parent_name}\n\n"

    for idx, item in enumerate(interview_data, 1):
        full_transcript += f"Question {idx}: {item['question']}\n"
        full_transcript += f"Answer: {item['answer']}\n"

        # Add follow-ups if any
        if 'followups' in item and item['followups']:
            for fup_idx, followup in enumerate(item['followups'], 1):
                full_transcript += f"  Follow-up {fup_idx}: {followup['question']}\n"
                full_transcript += f"  Answer: {followup['answer']}\n"

        full_transcript += "\n"

    # Create extraction prompt
    extraction_prompt = f"""You are an expert at analyzing oral history interviews and extracting structured information to preserve family legacy.

Analyze the following interview transcript and extract comprehensive structured data.

{full_transcript}

Extract and organize the following information in JSON format:

{{
  "people": [
    {{
      "name": "Full name",
      "relationship": "Relationship to {parent_name}",
      "birth_date": "Date if mentioned",
      "birth_place": "Place if mentioned",
      "notes": "Any additional details"
    }}
  ],
  "places": [
    {{
      "location": "Place name",
      "significance": "Why this place matters",
      "time_period": "When they lived/visited",
      "details": "Additional context"
    }}
  ],
  "dates_and_events": [
    {{
      "date": "Date or time period",
      "event": "What happened",
      "significance": "Why it matters",
      "people_involved": ["Names"]
    }}
  ],
  "themes_and_topics": [
    {{
      "theme": "Main topic/category",
      "description": "What was discussed",
      "significance": "Why this is important to preserve"
    }}
  ],
  "values_and_personality": [
    {{
      "value_or_trait": "The value or personality trait",
      "evidence": "Specific story or quote that demonstrates this",
      "significance": "What this reveals about {parent_name}"
    }}
  ],
  "life_lessons": [
    {{
      "lesson": "The wisdom or advice",
      "context": "Story or experience it came from",
      "quote": "Direct quote if available"
    }}
  ],
  "career_and_education": {{
    "education": ["Schools, degrees, studies"],
    "jobs": [
      {{
        "position": "Job title/role",
        "organization": "Company/place",
        "time_period": "When",
        "key_learnings": "What they learned"
      }}
    ]
  }},
  "family_tree": {{
    "parents": [
      {{
        "name": "Full name",
        "birth_date": "Date if mentioned",
        "birth_place": "Place if mentioned",
        "notes": "Any additional details"
      }}
    ],
    "siblings": [
      {{
        "name": "Full name (include nicknames in parentheses)",
        "birth_date": "Date if mentioned",
        "birth_place": "Place if mentioned",
        "relationship": "older brother/younger sister/twin/etc",
        "notes": "Any additional details"
      }}
    ],
    "spouse": {{
      "name": "Spouse name if mentioned",
      "marriage_date": "Date if mentioned",
      "notes": "Any additional details"
    }},
    "children": [
      {{
        "name": "Child name if mentioned",
        "birth_date": "Date if mentioned",
        "notes": "Any additional details"
      }}
    ]
  }}
}}

Important guidelines:
- Only extract information explicitly stated in the interview
- **CRITICAL**: If something isn't mentioned, use null (not "Not mentioned" or empty string)
- Use null for missing birth_date, birth_place, notes, etc. - DO NOT use text like "Not mentioned"
- Use empty array [] for missing lists
- Preserve direct quotes where meaningful
- Capture emotional context and significance
- Focus on details that help preserve {parent_name}'s story and personality

Example of correct null usage:
{{
  "name": "Clint",
  "birth_date": "1967",
  "birth_place": null,  // CORRECT - use null, not "Not mentioned"
  "notes": null  // CORRECT
}}

Return ONLY valid JSON, no additional text.
"""

    try:
        # Call OpenAI API for extraction
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured data from oral history interviews. You return valid JSON only."
                },
                {
                    "role": "user",
                    "content": extraction_prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=2000
        )

        # Parse the JSON response
        extracted_json = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if extracted_json.startswith("```json"):
            extracted_json = extracted_json[7:]
        if extracted_json.startswith("```"):
            extracted_json = extracted_json[3:]
        if extracted_json.endswith("```"):
            extracted_json = extracted_json[:-3]

        extracted_data = json.loads(extracted_json.strip())

        return {
            "success": True,
            "data": extracted_data,
            "error": None
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "data": None,
            "error": f"Failed to parse JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Extraction failed: {str(e)}"
        }


def format_extraction_for_display(extracted_data):
    """
    Format extracted data for nice display in Streamlit

    Args:
        extracted_data (dict): The extracted structured data (can be raw data or wrapped in 'data' key)

    Returns:
        str: Formatted markdown text
    """

    if not extracted_data:
        return "No data to display"

    # Handle both formats: direct data or wrapped in 'data' key
    if 'data' in extracted_data:
        data = extracted_data['data']
    else:
        # Data is already in the correct format (directly in extracted_data)
        data = extracted_data

    if not data:
        return "No data to display"

    markdown = ""

    # People
    if data.get('people'):
        markdown += "### 👥 People Mentioned\n\n"
        for person in data['people']:
            markdown += f"**{person.get('name', 'Unknown')}**"
            if person.get('relationship'):
                markdown += f" - {person['relationship']}"
            markdown += "\n"
            if person.get('birth_date'):
                markdown += f"- Born: {person['birth_date']}"
                if person.get('birth_place'):
                    markdown += f" in {person['birth_place']}"
                markdown += "\n"
            if person.get('notes'):
                markdown += f"- {person['notes']}\n"
            markdown += "\n"

    # Places - handle both 'places' and old 'important_places'
    places = data.get('places') or data.get('important_places')
    if places:
        markdown += "### 📍 Places\n\n"
        for place in places:
            markdown += f"**{place.get('location', 'Unknown')}**\n"
            if place.get('significance'):
                markdown += f"- {place['significance']}\n"
            if place.get('time_period'):
                markdown += f"- Time period: {place['time_period']}\n"
            markdown += "\n"

    # Values and Personality - handle old combined format 'life_lessons_and_values'
    values = data.get('values_and_personality')
    if values:
        markdown += "### 💎 Values & Personality\n\n"
        for item in values:
            markdown += f"**{item.get('value_or_trait', 'Unknown')}**\n"
            if item.get('evidence'):
                markdown += f"- Evidence: {item['evidence']}\n"
            markdown += "\n"

    # Life Lessons - handle both new 'life_lessons' and old 'life_lessons_and_values'
    life_lessons = data.get('life_lessons') or data.get('life_lessons_and_values')
    if life_lessons:
        markdown += "### 🎓 Life Lessons & Wisdom\n\n"
        for lesson in life_lessons:
            markdown += f"**{lesson.get('lesson', 'Unknown')}**\n"
            if lesson.get('context'):
                markdown += f"- Context: {lesson['context']}\n"
            if lesson.get('quote'):
                markdown += f"- Quote: *\"{lesson['quote']}\"*\n"
            if lesson.get('source'):
                markdown += f"- Source: {lesson['source']}\n"
            markdown += "\n"

    # Themes
    if data.get('themes_and_topics'):
        markdown += "### 📚 Themes & Topics\n\n"
        themes = [t.get('theme', 'Unknown') for t in data['themes_and_topics']]
        markdown += ", ".join(themes) + "\n\n"

    # Family Tree
    if data.get('family_tree'):
        markdown += "### 👨‍👩‍👧‍👦 Family Tree\n\n"
        family = data['family_tree']

        # Parents - handle both old dict format and new list format
        if family.get('parents'):
            markdown += "**Parents:**\n\n"
            parents_data = family['parents']

            # Check if it's old format (dict with 'father'/'mother' keys) or new format (list)
            if isinstance(parents_data, dict):
                # Old format: { father: {...}, mother: {...} }
                for role, parent in parents_data.items():
                    if isinstance(parent, dict):
                        name = parent.get('name', 'Unknown')
                        markdown += f"- **{name}** ({role.title()})"

                        birth_info = []
                        if parent.get('birth_date'):
                            birth_info.append(f"born {parent['birth_date']}")
                        if parent.get('birth_place'):
                            birth_info.append(f"in {parent['birth_place']}")

                        if birth_info:
                            markdown += f" - {', '.join(birth_info)}"
                        markdown += "\n"

                        if parent.get('notes'):
                            markdown += f"  - {parent['notes']}\n"
                        markdown += "\n"
            else:
                # New format: list of parent dicts
                for parent in parents_data:
                    if isinstance(parent, dict):
                        name = parent.get('name', 'Unknown')
                        markdown += f"- **{name}**"

                        birth_info = []
                        if parent.get('birth_date'):
                            birth_info.append(f"born {parent['birth_date']}")
                        if parent.get('birth_place'):
                            birth_info.append(f"in {parent['birth_place']}")

                        if birth_info:
                            markdown += f" ({', '.join(birth_info)})"
                        markdown += "\n"

                        if parent.get('notes'):
                            markdown += f"  - {parent['notes']}\n"
                        markdown += "\n"

        # Siblings
        if family.get('siblings'):
            markdown += "**Siblings:**\n\n"
            for sibling in family['siblings']:
                name = sibling.get('name', 'Unknown')
                relationship = sibling.get('relationship', '')
                if relationship:
                    markdown += f"- **{name}** ({relationship})"
                else:
                    markdown += f"- **{name}**"

                birth_info = []
                if sibling.get('birth_date'):
                    birth_info.append(f"born {sibling['birth_date']}")
                else:
                    birth_info.append("birth date not mentioned")

                if sibling.get('birth_place'):
                    birth_info.append(f"in {sibling['birth_place']}")
                else:
                    birth_info.append("birth place not mentioned")

                if birth_info:
                    markdown += f" - {', '.join(birth_info)}"
                markdown += "\n"

                if sibling.get('notes'):
                    markdown += f"  - {sibling['notes']}\n"
                markdown += "\n"

        # Spouse
        if family.get('spouse') and family['spouse'].get('name'):
            markdown += "**Spouse:**\n\n"
            spouse = family['spouse']
            markdown += f"- **{spouse.get('name')}**"
            if spouse.get('marriage_date'):
                markdown += f" (married {spouse['marriage_date']})"
            markdown += "\n"
            if spouse.get('notes'):
                markdown += f"  - {spouse['notes']}\n"
            markdown += "\n"

        # Children
        if family.get('children'):
            markdown += "**Children:**\n\n"
            for child in family['children']:
                name = child.get('name', 'Unknown')
                markdown += f"- **{name}**"
                if child.get('birth_date'):
                    markdown += f" (born {child['birth_date']})"
                markdown += "\n"
                if child.get('notes'):
                    markdown += f"  - {child['notes']}\n"
                markdown += "\n"

    return markdown


def test_extraction():
    """
    Test function to verify extraction works
    """

    # Sample interview data
    sample_data = [
        {
            "question": "What were your parents' full names? When and where were they born?",
            "category": "Family Tree",
            "answer": "My father was James Robert Thompson, born March 15, 1920 in Pittsburgh. My mother was Margaret Ann Kelly, born in 1922 in Cleveland.",
            "followups": []
        }
    ]

    print("Testing extraction...")
    result = extract_structured_data(sample_data, "Test Person")

    if result['success']:
        print("\n✅ Extraction successful!")
        print(json.dumps(result['data'], indent=2))
    else:
        print(f"\n❌ Extraction failed: {result['error']}")


if __name__ == "__main__":
    test_extraction()
