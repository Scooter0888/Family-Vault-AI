"""
PDF Export Module
Export Family Vault interviews to PDF format
"""

from fpdf import FPDF
from datetime import datetime
import json


class FamilyVaultPDF(FPDF):
    """Custom PDF class for Family Vault interviews"""

    def __init__(self, parent_name):
        super().__init__()
        self.parent_name = parent_name

    def header(self):
        """PDF header with Family Vault branding"""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, '🏛️ Family Vault', 0, 0, 'C')
        self.ln(5)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Interview with {self.parent_name}', 0, 0, 'C')
        self.ln(15)

    def footer(self):
        """PDF footer with page number"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        """Add a chapter title"""
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def section_title(self, title):
        """Add a section title"""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

    def body_text(self, text):
        """Add body text"""
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def question_answer(self, question, answer):
        """Format a Q&A pair"""
        # Question
        self.set_font('Arial', 'B', 11)
        self.set_text_color(0, 51, 102)
        self.multi_cell(0, 6, f'Q: {question}')
        self.ln(1)

        # Answer
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, f'A: {answer}')
        self.ln(4)


def export_to_pdf(interview_data, output_path):
    """
    Export interview data to a formatted PDF

    Args:
        interview_data (dict): Complete interview data
        output_path (str): Path where PDF should be saved

    Returns:
        bool: True if successful, False otherwise
    """

    try:
        parent_name = interview_data.get('parent_name', 'Unknown')
        interview_date = interview_data.get('interview_date', 'Unknown date')

        # Create PDF
        pdf = FamilyVaultPDF(parent_name)
        pdf.add_page()

        # Title page info
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Interview Date: {interview_date[:10]}', 0, 1)
        pdf.cell(0, 6, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
        pdf.ln(10)

        # Interview Q&A Section
        if 'interview_data' in interview_data:
            pdf.chapter_title('📝 Interview Responses')

            qa_data = interview_data['interview_data'].get('questions_and_answers', [])

            for idx, item in enumerate(qa_data, 1):
                pdf.section_title(f'{item.get("category", "General")} - Question {idx}')

                # Main question and answer
                pdf.question_answer(
                    item.get('question', 'No question'),
                    item.get('answer', 'No answer')
                )

                # Follow-up questions
                if item.get('followups'):
                    for fup_idx, followup in enumerate(item['followups'], 1):
                        pdf.set_font('Arial', 'I', 10)
                        pdf.set_text_color(100, 100, 100)
                        pdf.cell(0, 5, f'Follow-up {fup_idx}:', 0, 1)

                        pdf.question_answer(
                            followup.get('question', ''),
                            followup.get('answer', '')
                        )

        # Extracted Data Section
        if interview_data.get('extracted_data'):
            pdf.add_page()
            pdf.chapter_title('📊 Extracted Structured Data')

            extracted = interview_data['extracted_data']

            # Family Tree
            if extracted.get('family_tree'):
                pdf.section_title('👨‍👩‍👧‍👦 Family Tree')
                family = extracted['family_tree']

                # Parents
                if family.get('parents'):
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 6, 'Parents:', 0, 1)
                    pdf.set_font('Arial', '', 10)
                    for parent in family['parents']:
                        name = parent.get('name', 'Unknown')
                        birth = parent.get('birth_date', 'Unknown')
                        place = parent.get('birth_place', 'Unknown')
                        pdf.cell(0, 5, f'  • {name} (born {birth} in {place})', 0, 1)
                        if parent.get('notes'):
                            pdf.set_font('Arial', 'I', 9)
                            pdf.multi_cell(0, 5, f'    {parent["notes"]}')
                            pdf.set_font('Arial', '', 10)
                    pdf.ln(3)

                # Siblings
                if family.get('siblings'):
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 6, 'Siblings:', 0, 1)
                    pdf.set_font('Arial', '', 10)
                    for sibling in family['siblings']:
                        name = sibling.get('name', 'Unknown')
                        relationship = sibling.get('relationship', '')
                        birth = sibling.get('birth_date', 'Unknown')
                        pdf.cell(0, 5, f'  • {name} ({relationship}) - born {birth}', 0, 1)
                        if sibling.get('notes'):
                            pdf.set_font('Arial', 'I', 9)
                            pdf.multi_cell(0, 5, f'    {sibling["notes"]}')
                            pdf.set_font('Arial', '', 10)
                    pdf.ln(3)

            # Places
            if extracted.get('places'):
                pdf.section_title('📍 Important Places')
                for place in extracted['places']:
                    location = place.get('location', 'Unknown')
                    significance = place.get('significance', '')
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(0, 5, f'  • {location}', 0, 1)
                    if significance:
                        pdf.set_font('Arial', '', 10)
                        pdf.multi_cell(0, 5, f'    {significance}')
                pdf.ln(3)

            # Values and Personality
            if extracted.get('values_and_personality'):
                pdf.section_title('💎 Values & Personality')
                for value in extracted['values_and_personality']:
                    trait = value.get('value_or_trait', '')
                    evidence = value.get('evidence', '')
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(0, 5, f'  • {trait}', 0, 1)
                    if evidence:
                        pdf.set_font('Arial', '', 10)
                        pdf.multi_cell(0, 5, f'    {evidence}')
                pdf.ln(3)

            # Life Lessons
            if extracted.get('life_lessons'):
                pdf.section_title('🎓 Life Lessons & Wisdom')
                for lesson in extracted['life_lessons']:
                    lesson_text = lesson.get('lesson', '')
                    quote = lesson.get('quote', '')
                    pdf.set_font('Arial', 'B', 10)
                    pdf.multi_cell(0, 5, f'  • {lesson_text}')
                    if quote:
                        pdf.set_font('Arial', 'I', 10)
                        pdf.multi_cell(0, 5, f'    "{quote}"')
                    pdf.set_font('Arial', '', 10)
                pdf.ln(3)

        # Save PDF
        pdf.output(output_path)
        return True

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False


def test_pdf_export():
    """Test PDF export with sample data"""

    sample_data = {
        "parent_name": "Test Person",
        "interview_date": datetime.now().isoformat(),
        "interview_data": {
            "questions_and_answers": [
                {
                    "question": "Where did you grow up?",
                    "category": "Childhood",
                    "answer": "I grew up in Cleveland, Ohio.",
                    "followups": []
                }
            ]
        }
    }

    output = "test_export.pdf"
    success = export_to_pdf(sample_data, output)

    if success:
        print(f"✅ PDF export test successful! Created: {output}")
    else:
        print("❌ PDF export test failed")

    return success


if __name__ == "__main__":
    test_pdf_export()
