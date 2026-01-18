"""
AI Granny Interview App
A simple interface for conducting interviews with elderly parents
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import sys
sys.path.append('utils')
from openai_helper import generate_followup_questions
from extraction import extract_structured_data, format_extraction_for_display
from query import get_all_interview_files, load_interview_file, search_and_answer
from audio_helper import transcribe_audio
from pdf_export import export_to_pdf
from translation import translate_question, SUPPORTED_LANGUAGES
from voice_helper import text_to_speech, get_voice_profile_names

# Configure the page
st.set_page_config(
    page_title="FamilyVaultAI",
    page_icon="🔷",  # Placeholder - represents FV brand colors (teal/blue)
    layout="centered"
)

# Load questions from JSON file
@st.cache_data
def load_questions():
    """Load interview questions from JSON file"""
    with open('data/questions.json', 'r') as f:
        data = json.load(f)
    return data['core_questions']


def save_interview_data(parent_name, answers, extracted_data, completed=True, current_question=0, total_questions=10, existing_filepath=None):
    """
    Save interview data to JSON file

    Args:
        parent_name (str): Name of the parent
        answers (list): All interview answers with followups
        extracted_data (dict): Extracted structured data
        completed (bool): Whether interview is complete
        current_question (int): Current question index (for resuming)
        total_questions (int): Total number of questions
        existing_filepath (str): If resuming, update existing file instead of creating new

    Returns:
        tuple: (success: bool, filepath: str, error: str)
    """
    try:
        if existing_filepath and Path(existing_filepath).exists():
            # Update existing file
            filepath = Path(existing_filepath)
        else:
            # Create new filename from parent name (sanitize for filesystem)
            safe_name = "".join(c for c in parent_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}.json"
            filepath = Path('data/parent_profiles') / filename

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Prepare the complete data structure
        interview_record = {
            "parent_name": parent_name,
            "interview_date": datetime.now().isoformat(),
            "interview_data": {
                "total_questions": len(answers),
                "total_followups": sum(len(ans.get('followups', [])) for ans in answers),
                "questions_and_answers": answers
            },
            "extracted_data": extracted_data.get('data') if extracted_data and extracted_data.get('success') else None,
            "metadata": {
                "app_version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "completed": completed,
                "current_question": current_question,
                "max_questions": total_questions
            }
        }

        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(interview_record, f, indent=2, ensure_ascii=False)

        return True, str(filepath), None

    except Exception as e:
        return False, None, str(e)

# Initialize session state variables
if 'started' not in st.session_state:
    st.session_state.started = False
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'parent_name' not in st.session_state:
    st.session_state.parent_name = ""
if 'followup_mode' not in st.session_state:
    st.session_state.followup_mode = False
if 'followup_questions' not in st.session_state:
    st.session_state.followup_questions = []
if 'current_followup' not in st.session_state:
    st.session_state.current_followup = 0
if 'main_answer' not in st.session_state:
    st.session_state.main_answer = ""
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'extraction_complete' not in st.session_state:
    st.session_state.extraction_complete = False
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "Interview"  # "Interview", "View", or "Q&A"
if 'selected_interview_file' not in st.session_state:
    st.session_state.selected_interview_file = None
if 'selected_interview_data' not in st.session_state:
    st.session_state.selected_interview_data = None
if 'search_target' not in st.session_state:
    st.session_state.search_target = "All Interviews"  # Which interview(s) to search
if 'qa_history' not in st.session_state:
    st.session_state.qa_history = []
if 'transcription_cache' not in st.session_state:
    st.session_state.transcription_cache = {}  # Cache transcriptions to avoid re-processing
if 'preferred_input_method' not in st.session_state:
    st.session_state.preferred_input_method = "Type answer"  # Persist input method preference
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "English"  # Default language for questions
if 'translate_audio_to_english' not in st.session_state:
    st.session_state.translate_audio_to_english = False  # Auto-translate audio to English
if 'voice_mode_enabled' not in st.session_state:
    st.session_state.voice_mode_enabled = False  # Voice input/output for Q&A
if 'selected_voice_profile' not in st.session_state:
    st.session_state.selected_voice_profile = "Warm Grandmother (Shimmer)"  # Default voice
if 'last_audio_response' not in st.session_state:
    st.session_state.last_audio_response = None  # Store last TTS audio path
if 'just_answered' not in st.session_state:
    st.session_state.just_answered = False  # Track if we just generated a new answer
if 'save_early' not in st.session_state:
    st.session_state.save_early = False  # Flag to trigger early save from sidebar
if 'resuming_filepath' not in st.session_state:
    st.session_state.resuming_filepath = None  # Track file being resumed
if 'question_tts_muted' not in st.session_state:
    st.session_state.question_tts_muted = True  # Mute TTS by default (browser autoplay restrictions)
if 'last_spoken_question' not in st.session_state:
    st.session_state.last_spoken_question = None  # Track which question was last spoken
if 'qa_auto_search_trigger' not in st.session_state:
    st.session_state.qa_auto_search_trigger = False  # Trigger auto-search after voice transcription
if 'qa_search_completed' not in st.session_state:
    st.session_state.qa_search_completed = False  # Track if search has been completed
if 'recording_for_question' not in st.session_state:
    st.session_state.recording_for_question = None  # Track which question we're recording for
if 'should_autoplay_question' not in st.session_state:
    st.session_state.should_autoplay_question = False  # Only auto-play when user explicitly toggles sound
# Load questions
questions = load_questions()

# ============================================
# MAIN APP
# ============================================

# FamilyVaultAI Brand-Compliant CSS
st.markdown("""
<style>
/* === FamilyVaultAI Visual Identity === */
/* Brand Colors (Authorized Palette Only):
   - Primary Gradient: Teal #2EC4B6, Fresh Blue #4A7DFF
   - Text: Deep Navy #0F1C2E, Soft Off-White #F6F8FB
   - Backgrounds: White #FFFFFF, Soft Off-White #F6F8FB
   - Accent: Soft Green #66CDAA (very sparing)
*/

/* Subheaders - Deep Navy */
h2, h3 {
    color: #0F1C2E !important;
    font-weight: 600;
}

/* Body text - Deep Navy */
body, p, div {
    color: #0F1C2E;
}

/* Primary CTAs - Brand Gradient */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2EC4B6 0%, #4A7DFF 100%);
    color: #F6F8FB;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(46, 196, 182, 0.3);
}

/* Secondary buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    color: #0F1C2E;
    border: 1px solid #2EC4B6;
    background: #FFFFFF;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #F6F8FB;
    transform: translateY(-1px);
}

/* Progress bar - Brand Gradient */
.stProgress > div > div {
    background: linear-gradient(90deg, #2EC4B6 0%, #4A7DFF 100%);
    border-radius: 10px;
}

/* Info boxes - Soft Off-White background */
.stAlert {
    border-radius: 8px;
    background-color: #F6F8FB;
    border-left: 4px solid #2EC4B6;
}

/* Interview question styling - Teal accent */
.question-card {
    background: #F6F8FB;
    border-left: 4px solid #2EC4B6;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0 8px 8px 0;
}

/* Success states - Soft Green (sparing) */
.success-banner {
    background: #F6F8FB;
    border-left: 4px solid #66CDAA;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    margin: 1rem 0;
}

/* Sidebar - Gradient background */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,
        rgba(46, 196, 182, 0.08) 0%,
        rgba(74, 125, 255, 0.05) 50%,
        #F6F8FB 100%);
}

section[data-testid="stSidebar"] .stRadio > label {
    font-weight: 500;
    color: #0F1C2E;
}

/* Main background - Gradient top section */
.main {
    background: linear-gradient(180deg,
        rgba(46, 196, 182, 0.03) 0%,
        rgba(74, 125, 255, 0.02) 50%,
        #FFFFFF 100%);
}

/* Dividers - Teal */
hr {
    border-color: #2EC4B6;
    opacity: 0.2;
}

/* Links - Fresh Blue */
a {
    color: #4A7DFF;
}

a:hover {
    color: #2EC4B6;
}
</style>
""", unsafe_allow_html=True)

# Main title with FV logo - Official FamilyVaultAI branding
st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <div style='display: inline-flex; align-items: center; gap: 12px;'>
        <div style='width: 50px; height: 50px; background: linear-gradient(135deg, #2EC4B6 0%, #4A7DFF 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 24px;'>FV</div>
        <h1 style='background: linear-gradient(90deg, #2EC4B6 0%, #4A7DFF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; font-size: 2.5em; font-weight: 700;'>FamilyVaultAI</h1>
    </div>
</div>
<p style='text-align: center; color: #0F1C2E;'>Preserve your family's history, stories, wisdom, and memories forever</p>
""", unsafe_allow_html=True)

# Language selector
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    # Get index safely for Safari compatibility
    try:
        current_index = list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.selected_language)
    except (ValueError, AttributeError):
        current_index = 0
        st.session_state.selected_language = "English"

    selected_language = st.selectbox(
        "🌍 Interview Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=current_index,
        help="Questions will be translated to this language",
        key="language_selector"
    )
    st.session_state.selected_language = selected_language

with col2:
    translate_audio = st.checkbox(
        "🔄 Auto-translate audio to English",
        value=st.session_state.translate_audio_to_english,
        help="Automatically detect and translate non-English audio recordings to English",
        key="translate_audio_checkbox"
    )
    st.session_state.translate_audio_to_english = translate_audio

st.divider()

# Help section
with st.expander("ℹ️ How to Use FamilyVaultAI", expanded=False):
    st.markdown("""
    ### Two Modes:

    **📝 Interview Mode:**
    1. Enter your name (or your parent/grandparent's name)
    2. Answer 10 core questions about their life
    3. **🎤 Choose to type OR record audio** - your choice persists for all questions!
    4. **If recording:** Audio is transcribed automatically - review and edit before submitting
    5. AI generates adaptive follow-up questions for deeper stories
    6. Review and approve all responses
    7. **✨ Save the interview:**
       - AI automatically extracts names, dates, places, and values

    **💬 Q&A Mode:**
    1. Ask any question about your family (type or speak!)
    2. AI searches through saved interviews to find the answer
    3. Toggle Voice Mode to enable spoken questions and answers
    4. Build a conversation history of your queries

    ### Tips:
    - 💡 Give detailed answers for better AI follow-ups
    - 🎤 Record in a quiet environment for best transcription quality
    - 🎤 Always review transcripts - fix names, dates, and places
    - 💡 Use the sidebar Quick Search for fast lookups

    ### Requirements:
    - ✅ OpenAI API key (in .env file)
    - ✅ Internet connection
    - 🎤 Microphone access (for voice features)
    """)

# Sidebar with mode selector and progress
with st.sidebar:
    # Sidebar header with FV logo and gradient text
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
        <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #2EC4B6 0%, #4A7DFF 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 18px;'>FV</div>
        <h2 style='background: linear-gradient(90deg, #2EC4B6 0%, #4A7DFF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; font-size: 1.2em; font-weight: 700;'>FamilyVaultAI</h2>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Mode selector
    mode_map = {"Interview": 0, "View": 1, "Q&A": 2}
    current_index = mode_map.get(st.session_state.app_mode, 0)

    mode = st.radio(
        "Select Mode:",
        ["📝 Interview", "📚 View Interviews", "💬 Q&A"],
        index=current_index,
        help="Interview: Conduct new interviews | View: Browse saved interviews | Q&A: Search across interviews"
    )

    # Update mode if changed
    if mode == "📝 Interview" and st.session_state.app_mode != "Interview":
        st.session_state.app_mode = "Interview"
        st.rerun()
    elif mode == "📚 View Interviews" and st.session_state.app_mode != "View":
        st.session_state.app_mode = "View"
        st.rerun()
    elif mode == "💬 Q&A" and st.session_state.app_mode != "Q&A":
        st.session_state.app_mode = "Q&A"
        st.session_state.just_answered = False  # Clear flag when entering Q&A mode
        st.rerun()

    st.divider()

    # Show appropriate sidebar content based on mode
    if st.session_state.app_mode == "Interview":
        st.subheader("Interview Progress")
        if st.session_state.started:
            current_q = st.session_state.current_question
            total_q = len(questions)
            progress = current_q / total_q

            # Visual progress bar
            st.progress(progress)

            # Progress stats
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Question", f"{current_q + 1}/{total_q}")
            with col_b:
                answers_count = len(st.session_state.answers)
                st.metric("Answered", answers_count)

            st.write(f"**Interviewing:** {st.session_state.parent_name}")

            # Show completion percentage
            pct = int(progress * 100)
            if pct < 30:
                st.caption(f"Just getting started...")
            elif pct < 70:
                st.caption(f"Great progress! {pct}% complete")
            else:
                st.caption(f"Almost done! {pct}% complete")
        else:
            st.info("Start an interview to see progress")

        # Save & Exit button (available anytime during interview)
        if st.session_state.started and len(st.session_state.answers) > 0:
            if st.button("💾 Save & Exit", type="primary", use_container_width=True):
                st.session_state.save_early = True
                st.rerun()

        # Reset button
        if st.session_state.started:
            if st.button("🔄 Start Over", use_container_width=True):
                st.session_state.started = False
                st.session_state.current_question = 0
                st.session_state.answers = []
                st.session_state.parent_name = ""
                st.session_state.followup_mode = False
                st.session_state.followup_questions = []
                st.session_state.current_followup = 0
                st.session_state.main_answer = ""
                st.session_state.transcription_cache = {}  # Clear transcription cache
                st.session_state.resuming_filepath = None  # Clear resume tracking
                st.rerun()

    elif st.session_state.app_mode == "View":
        st.subheader("Saved Interviews")
        try:
            all_interviews = get_all_interview_files()
            st.info(f"📚 {len(all_interviews)} interview(s) saved")
        except Exception as e:
            st.warning("Unable to load interviews")

    else:  # Q&A mode
        st.subheader("Q&A Session")
        # Get all interview files with error handling for Safari
        try:
            all_interviews = get_all_interview_files()
            st.info(f"Searching across {len(all_interviews)} interview(s)")
        except Exception as e:
            st.warning("Unable to load interviews")
            all_interviews = []
        st.write(f"**Questions asked:** {len(st.session_state.qa_history)}")

        if st.button("🔄 Clear Q&A History"):
            st.session_state.qa_history = []
            st.rerun()

    # Quick Search feature - search across interviews
    st.divider()
    st.subheader("🔍 Quick Search")

    # Interview selector for search
    try:
        all_interviews = get_all_interview_files()
        if all_interviews:
            interview_options = ["All Interviews"] + [interview_data.get('parent_name', 'Unknown')
                                                      for filename, filepath in all_interviews
                                                      for interview_data in [load_interview_file(filepath)] if interview_data]

            search_target = st.selectbox(
                "Search in:",
                options=interview_options,
                index=interview_options.index(st.session_state.search_target) if st.session_state.search_target in interview_options else 0,
                help="Choose which interview(s) to search",
                key="search_target_selector"
            )
            st.session_state.search_target = search_target
        else:
            st.info("No interviews saved yet")
            search_target = None
    except:
        search_target = None

    quick_question = st.text_input(
        "Ask anything about your family:",
        placeholder="e.g., What year was Clint Johnson born?",
        help="Search across selected interview(s)",
        key="quick_search"
    )

    if st.button("🔍 Search", use_container_width=True):
        if quick_question.strip() and search_target:
            try:
                all_interviews = get_all_interview_files()

                if not all_interviews:
                    st.warning("No interviews saved yet")
                else:
                    # Filter interviews based on selection
                    if search_target == "All Interviews":
                        interviews_to_search = all_interviews
                    else:
                        interviews_to_search = [(filename, filepath) for filename, filepath in all_interviews
                                               if load_interview_file(filepath) and
                                               load_interview_file(filepath).get('parent_name') == search_target]

                    with st.spinner(f"🔍 Searching {search_target}..."):
                        found_answer = False
                        for filename, filepath in interviews_to_search:
                            interview_data = load_interview_file(filepath)
                            if interview_data:
                                try:
                                    result = search_and_answer(quick_question, interview_data)
                                    if result['success'] and result['answer']:
                                        # Check if answer contains actual information
                                        if "don't have information" not in result['answer'].lower():
                                            st.success(f"**Found in {interview_data.get('parent_name', 'Unknown')}'s interview:**")
                                            st.info(result['answer'])
                                            found_answer = True
                                            if search_target != "All Interviews":
                                                break  # Only show first match for specific interview
                                        if search_target == "All Interviews" and found_answer:
                                            break  # Stop after first match when searching all
                                except:
                                    continue

                        if not found_answer:
                            st.warning(f"No relevant information found in {search_target}")
            except Exception as e:
                st.error(f"Oops! Something went wrong with the search. Please try again.")
                st.caption(f"Technical details: {str(e)}")
        elif not quick_question.strip():
            st.warning("Please type a question to search your family vault")
        else:
            st.info("No interviews saved yet. Complete an interview first to use Q&A!")

# Main content area
if st.session_state.app_mode == "Interview":
    # INTERVIEW MODE
    if not st.session_state.started:
        # Welcome screen - get person's name
        st.subheader("Welcome! Let's get started.")
        st.write("This interview will help preserve your life story through a series of questions about your childhood, family, career, and life lessons.")

        parent_name = st.text_input(
            "What is your name?",
            placeholder="e.g., Margaret Smith",
            help="Enter your full name"
        )

        st.divider()

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ Start Interview", type="primary", use_container_width=True):
                if parent_name.strip():
                    st.session_state.parent_name = parent_name
                    st.session_state.started = True
                    st.rerun()
                else:
                    st.warning("Please enter your name to begin the interview")

    else:
        # Check if user wants to save early
        if st.session_state.save_early:
            st.subheader("💾 Save Interview Early")
            st.write(f"You have answered **{len(st.session_state.answers)}** question(s) so far.")
            st.info("💡 You can resume this interview later from the **View Interviews** section.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save Now", type="primary", use_container_width=True):
                    with st.spinner("💾 Saving interview..."):
                        try:
                            # Run extraction
                            extraction_result = extract_structured_data(
                                st.session_state.answers,
                                st.session_state.parent_name
                            )

                            # Save as incomplete interview
                            success, filepath, error = save_interview_data(
                                st.session_state.parent_name,
                                st.session_state.answers,
                                extraction_result,
                                completed=False,
                                current_question=st.session_state.current_question,
                                total_questions=len(questions),
                                existing_filepath=st.session_state.resuming_filepath
                            )

                            if success:
                                st.success(f"✅ Interview saved!")
                                st.info(f"📁 Saved to: `{filepath}`")

                                # Reset interview state
                                st.session_state.started = False
                                st.session_state.current_question = 0
                                st.session_state.answers = []
                                st.session_state.parent_name = ""
                                st.session_state.followup_mode = False
                                st.session_state.followup_questions = []
                                st.session_state.current_followup = 0
                                st.session_state.main_answer = ""
                                st.session_state.transcription_cache = {}
                                st.session_state.save_early = False
                                st.session_state.resuming_filepath = None
                                if 'followup_answers' in st.session_state:
                                    st.session_state.followup_answers = []

                                st.balloons()
                                # Switch to View mode
                                st.session_state.app_mode = "View"
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to save: {error}")
                                st.session_state.save_early = False
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.session_state.save_early = False

            with col2:
                if st.button("❌ Cancel, Continue Interview", use_container_width=True):
                    st.session_state.save_early = False
                    st.rerun()

        # Interview in progress
        elif st.session_state.current_question < len(questions):
            current_q = questions[st.session_state.current_question]

            # Check if we're in follow-up mode
            if not st.session_state.followup_mode:
                # MAIN QUESTION MODE
                st.subheader(f"Question {st.session_state.current_question + 1}")
                st.info(f"**Category:** {current_q['category']}")

                # Show the question (translated if not English)
                question_text = current_q['question']
                if st.session_state.selected_language != "English":
                    question_text = translate_question(question_text, st.session_state.selected_language)

                st.markdown(f"### {question_text}")

                # Show original question in small text if translated
                if st.session_state.selected_language != "English":
                    st.caption(f"Original: {current_q['question']}")

                # TTS controls - always generate audio, let user click play button
                col_tts1, col_tts2 = st.columns([4, 1])
                with col_tts2:
                    # Audio toggle - plays question immediately when enabled
                    if st.session_state.question_tts_muted:
                        button_label = "🔇 Play Audio"
                        button_help = "Click to hear question spoken aloud"
                    else:
                        button_label = "🔊 Mute Audio"
                        button_help = "Click to turn off audio"

                    if st.button(button_label,
                                key=f"tts_mute_{st.session_state.current_question}",
                                help=button_help):
                        # If we're unmuting (turning on sound), set autoplay flag
                        if st.session_state.question_tts_muted:
                            st.session_state.should_autoplay_question = True
                        else:
                            st.session_state.should_autoplay_question = False
                        st.session_state.question_tts_muted = not st.session_state.question_tts_muted
                        st.rerun()

                # Show tip on first question if audio hidden
                if st.session_state.current_question == 0 and st.session_state.question_tts_muted:
                    st.info("💡 **Tip:** Click '🔇 Show Audio' above to hear this question spoken aloud!")

                # Generate and show audio player (if not muted)
                if not st.session_state.question_tts_muted:
                    question_key = f"q_{st.session_state.current_question}"
                    # Always generate audio for current question using gentle voice
                    with st.spinner("🎤 Generating question audio..."):
                        try:
                            success, audio_path, error = text_to_speech(
                                question_text,
                                "Gentle & Soothing (Echo)"  # Use soothing voice for interview questions
                            )
                            if success and audio_path and os.path.exists(audio_path):
                                with open(audio_path, 'rb') as audio_file:
                                    audio_bytes = audio_file.read()
                                # Only auto-play if user just toggled sound ON (should_autoplay_question=True)
                                # After playing once, reset flag so it doesn't auto-play again on reruns
                                autoplay_now = st.session_state.should_autoplay_question
                                if autoplay_now:
                                    st.session_state.should_autoplay_question = False
                                st.audio(audio_bytes, format='audio/wav', autoplay=autoplay_now)
                                if autoplay_now:
                                    st.caption("🔊 Question audio playing...")
                                else:
                                    st.caption("🔊 Question audio (click to play)")
                            else:
                                st.error(f"❌ Audio generation failed: {error}")
                        except Exception as e:
                            st.error(f"❌ Audio error: {str(e)}")

                # Input method selection (persists across questions)
                input_options = ["Type answer", "Record audio"]
                default_idx = input_options.index(st.session_state.preferred_input_method) if st.session_state.preferred_input_method in input_options else 0
                input_method = st.radio(
                    "Choose input method:",
                    input_options,
                    index=default_idx,
                    horizontal=True,
                    key=f"input_method_{st.session_state.current_question}"
                )
                # Update preference when changed
                if input_method != st.session_state.preferred_input_method:
                    st.session_state.preferred_input_method = input_method

                answer = ""

                if input_method == "Type answer":
                    # Text area for typed answer
                    answer = st.text_area(
                        f"**{st.session_state.parent_name}'s response:**",
                        height=200,
                        placeholder="Type the answer here...",
                        key=f"answer_{st.session_state.current_question}",
                        help="You can also have your parent type their answer directly"
                    )
                else:  # Record audio
                    st.write(f"**{st.session_state.parent_name}'s response:**")

                    audio_bytes = st.audio_input(
                        "🎤 Click to start/stop recording",
                        key=f"audio_{st.session_state.current_question}"
                    )

                    # Only process audio if we have it and we're recording for this question
                    if audio_bytes:
                        # Mark that we're recording for this question to prevent premature navigation
                        st.session_state.recording_for_question = st.session_state.current_question

                        # Generate unique key for this audio
                        audio_data_bytes = audio_bytes.getbuffer().tobytes()
                        audio_hash = hash(audio_data_bytes)
                        audio_key = f"transcript_{st.session_state.current_question}_{audio_hash}"

                        if audio_key not in st.session_state.transcription_cache:
                            spinner_text = "🎤 Transcribing audio..."
                            if st.session_state.translate_audio_to_english:
                                spinner_text = "🎤 Transcribing and translating to English..."

                            with st.spinner(spinner_text):
                                transcript = transcribe_audio(
                                    audio_bytes,
                                    translate_to_english=st.session_state.translate_audio_to_english
                                )
                                if transcript:
                                    st.session_state.transcription_cache[audio_key] = transcript
                                    st.session_state.recording_for_question = st.session_state.current_question
                                    success_msg = "✅ Transcription complete! Review and edit below:"
                                    if st.session_state.translate_audio_to_english:
                                        success_msg = "✅ Transcription and translation complete! Review and edit below:"
                                    st.success(success_msg)
                                else:
                                    st.error("Couldn't understand the audio. Try speaking louder or in a quieter environment.")
                                    st.caption("You can also switch to 'Type answer' to enter your response manually.")

                        # Show editable text area with the transcript
                        if audio_key in st.session_state.transcription_cache:
                            answer = st.text_area(
                                "Review and edit transcript:",
                                value=st.session_state.transcription_cache[audio_key],
                                height=200,
                                key=f"edit_transcript_{st.session_state.current_question}",
                                help="The audio has been transcribed. You can edit this text to fix any errors before submitting."
                            )
                            st.info("💡 **Tip**: Review the transcript above and make any corrections to names, dates, or places before continuing.")
                    elif st.session_state.recording_for_question == st.session_state.current_question and st.session_state.transcription_cache:
                        # If we were recording for this question but now have no audio_bytes,
                        # show the cached transcription for editing/confirmation
                        for cache_key in st.session_state.transcription_cache:
                            if f"transcript_{st.session_state.current_question}_" in cache_key:
                                answer = st.text_area(
                                    "Review and edit transcript:",
                                    value=st.session_state.transcription_cache[cache_key],
                                    height=200,
                                    key=f"edit_transcript_{st.session_state.current_question}",
                                    help="The audio has been transcribed. You can edit this text to fix any errors before submitting."
                                )
                                st.info("💡 **Tip**: Review the transcript above and make any corrections to names, dates, or places before continuing.")
                                break

                st.divider()

                # Navigation buttons
                col1, col2, col3 = st.columns([1, 2, 1])

                with col1:
                    # Back button (if not on first question and not recording)
                    if st.session_state.current_question > 0:
                        # Disable Previous if we're in the middle of recording for this question
                        if input_method == "Record audio" and st.session_state.recording_for_question == st.session_state.current_question:
                            st.button("⬅️ Previous", disabled=True, help="Finish recording first")
                        else:
                            if st.button("⬅️ Previous"):
                                st.session_state.current_question -= 1
                                st.session_state.recording_for_question = None
                                st.rerun()

                with col2:
                    # Generate Follow-ups button
                    if st.button("✨ Answer & Generate Follow-ups", type="primary", use_container_width=True):
                        if answer.strip():
                            # Save the main answer temporarily
                            st.session_state.main_answer = answer
                            # Clear recording flag since we're submitting the answer
                            st.session_state.recording_for_question = None

                            # Show loading message
                            with st.spinner("🤖 AI is generating thoughtful follow-up questions..."):
                                try:
                                    # Generate follow-up questions using AI
                                    followups = generate_followup_questions(
                                        current_q['question'],
                                        answer,
                                        num_followups=2
                                    )

                                    if followups:
                                        st.session_state.followup_questions = followups
                                        st.session_state.followup_mode = True
                                        st.session_state.current_followup = 0
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Could not generate follow-ups. Saving your answer and moving to next question.")
                                        # Save answer and move on
                                        st.session_state.answers.append({
                                            'question': current_q['question'],
                                            'category': current_q['category'],
                                            'answer': answer,
                                            'followups': []
                                        })
                                        st.session_state.current_question += 1
                                        st.rerun()

                                except Exception as e:
                                    st.error(f"❌ API Error: {str(e)}")
                                    st.info("💡 Tip: Check your internet connection and OpenAI API credits. You can skip to the next question or try again.")
                        else:
                            st.warning("Please record or type an answer before continuing, or click 'Skip' to move on")

                with col3:
                    # Skip button
                    if st.button("Skip ⏭️"):
                        st.session_state.current_question += 1
                        st.session_state.recording_for_question = None
                        st.rerun()

                # Save & Resume Later button (below navigation buttons)
                st.divider()
                if st.button("💾 Save & Resume Later", use_container_width=True, help="Save this interview and continue later"):
                    st.session_state.save_early = True
                    st.rerun()

            else:
                # FOLLOW-UP QUESTION MODE
                st.subheader(f"Question {st.session_state.current_question + 1} - Follow-up {st.session_state.current_followup + 1}")
                st.info(f"**Category:** {current_q['category']} | **AI-Generated Follow-up**")

                # Show the original answer
                with st.expander("📖 View Original Answer", expanded=False):
                    st.write(f"**Original Question:** {current_q['question']}")
                    st.write(f"**Answer:** {st.session_state.main_answer}")

                # Show the follow-up question (translated if not English)
                followup_q = st.session_state.followup_questions[st.session_state.current_followup]
                followup_q_translated = followup_q
                if st.session_state.selected_language != "English":
                    followup_q_translated = translate_question(followup_q, st.session_state.selected_language)

                st.markdown(f"### {followup_q_translated}")

                # Show original question in small text if translated
                if st.session_state.selected_language != "English":
                    st.caption(f"Original: {followup_q}")

                # TTS controls - always generate audio, let user click play button
                col_tts1, col_tts2 = st.columns([4, 1])
                with col_tts2:
                    # Audio toggle - plays question immediately when enabled
                    if st.session_state.question_tts_muted:
                        button_label = "🔇 Play Audio"
                        button_help = "Click to hear question spoken aloud"
                    else:
                        button_label = "🔊 Mute Audio"
                        button_help = "Click to turn off audio"

                    if st.button(button_label,
                                key=f"tts_mute_followup_{st.session_state.current_question}_{st.session_state.current_followup}",
                                help=button_help):
                        # If we're unmuting (turning on sound), set autoplay flag
                        if st.session_state.question_tts_muted:
                            st.session_state.should_autoplay_question = True
                        else:
                            st.session_state.should_autoplay_question = False
                        st.session_state.question_tts_muted = not st.session_state.question_tts_muted
                        st.rerun()

                # Generate and show audio player (if not muted)
                if not st.session_state.question_tts_muted:
                    with st.spinner("🎤 Generating question audio..."):
                        try:
                            success, audio_path, error = text_to_speech(
                                followup_q_translated,
                                "Gentle & Soothing (Echo)"  # Use soothing voice for interview questions
                            )
                            if success and audio_path and os.path.exists(audio_path):
                                with open(audio_path, 'rb') as audio_file:
                                    audio_bytes = audio_file.read()
                                # Only auto-play if user just toggled sound ON (should_autoplay_question=True)
                                # After playing once, reset flag so it doesn't auto-play again on reruns
                                autoplay_now = st.session_state.should_autoplay_question
                                if autoplay_now:
                                    st.session_state.should_autoplay_question = False
                                st.audio(audio_bytes, format='audio/wav', autoplay=autoplay_now)
                                if autoplay_now:
                                    st.caption("🔊 Question audio playing...")
                                else:
                                    st.caption("🔊 Question audio (click to play)")
                            else:
                                st.error(f"❌ Audio generation failed: {error}")
                        except Exception as e:
                            st.error(f"❌ Audio error: {str(e)}")

                # Input method selection for follow-up (persists across questions)
                followup_input_options = ["Type answer", "Record audio"]
                followup_default_idx = followup_input_options.index(st.session_state.preferred_input_method) if st.session_state.preferred_input_method in followup_input_options else 0
                followup_input_method = st.radio(
                    "Choose input method:",
                    followup_input_options,
                    index=followup_default_idx,
                    horizontal=True,
                    key=f"followup_input_method_{st.session_state.current_question}_{st.session_state.current_followup}"
                )
                # Update preference when changed
                if followup_input_method != st.session_state.preferred_input_method:
                    st.session_state.preferred_input_method = followup_input_method

                followup_answer = ""

                if followup_input_method == "Type answer":
                    # Text area for typed follow-up answer
                    followup_answer = st.text_area(
                        f"**{st.session_state.parent_name}'s response:**",
                        height=150,
                        placeholder="Type the answer here...",
                        key=f"followup_{st.session_state.current_question}_{st.session_state.current_followup}",
                        help="Answer this follow-up question to add more detail to your story"
                    )
                else:  # Record audio for follow-up
                    st.write(f"**{st.session_state.parent_name}'s response:**")

                    followup_audio_bytes = st.audio_input(
                        "🎤 Click to start/stop recording",
                        key=f"followup_audio_{st.session_state.current_question}_{st.session_state.current_followup}"
                    )

                    if followup_audio_bytes:
                        # Generate unique key for this audio
                        followup_audio_data = followup_audio_bytes.getbuffer().tobytes()
                        followup_audio_hash = hash(followup_audio_data)
                        followup_audio_key = f"followup_transcript_{st.session_state.current_question}_{st.session_state.current_followup}_{followup_audio_hash}"

                        if followup_audio_key not in st.session_state.transcription_cache:
                            spinner_text = "🎤 Transcribing audio..."
                            if st.session_state.translate_audio_to_english:
                                spinner_text = "🎤 Transcribing and translating to English..."

                            with st.spinner(spinner_text):
                                followup_transcript = transcribe_audio(
                                    followup_audio_bytes,
                                    translate_to_english=st.session_state.translate_audio_to_english
                                )
                                if followup_transcript:
                                    st.session_state.transcription_cache[followup_audio_key] = followup_transcript
                                    success_msg = "✅ Transcription complete! Review and edit below:"
                                    if st.session_state.translate_audio_to_english:
                                        success_msg = "✅ Transcription and translation complete! Review and edit below:"
                                    st.success(success_msg)
                                else:
                                    st.error("Couldn't understand the audio. Try speaking louder or in a quieter environment.")
                                    st.caption("You can also switch to 'Type answer' to enter your response manually.")

                        # Show editable text area with the transcript
                        if followup_audio_key in st.session_state.transcription_cache:
                            followup_answer = st.text_area(
                                "Review and edit transcript:",
                                value=st.session_state.transcription_cache[followup_audio_key],
                                height=150,
                                key=f"edit_followup_transcript_{st.session_state.current_question}_{st.session_state.current_followup}",
                                help="The audio has been transcribed. You can edit this text to fix any errors before submitting."
                            )
                            st.info("💡 **Tip**: Review the transcript above and make any corrections before continuing.")

                st.divider()

                # Navigation buttons for follow-ups
                col1, col2, col3 = st.columns([1, 2, 1])

                with col1:
                    # Back button in follow-up mode
                    if st.session_state.current_followup > 0:
                        # Go back to previous follow-up
                        if st.button("⬅️ Previous"):
                            st.session_state.current_followup -= 1
                            st.rerun()
                    else:
                        # Go back to main question
                        if st.button("⬅️ Back to Question"):
                            st.session_state.followup_mode = False
                            st.session_state.followup_questions = []
                            st.session_state.current_followup = 0
                            if 'followup_answers' in st.session_state:
                                st.session_state.followup_answers = []
                            st.rerun()

                with col2:
                    # Check if this is the last follow-up
                    if st.session_state.current_followup < len(st.session_state.followup_questions) - 1:
                        button_text = "Next Follow-up ➡️"
                    else:
                        button_text = "✅ Continue to Next Question"

                    if st.button(button_text, type="primary", use_container_width=True):
                        # Save the follow-up answer if provided
                        if followup_answer.strip():
                            # Initialize followup_answers if needed
                            if 'followup_answers' not in st.session_state:
                                st.session_state.followup_answers = []

                            st.session_state.followup_answers.append({
                                'question': followup_q,
                                'answer': followup_answer
                            })

                        # Move to next follow-up or finish
                        if st.session_state.current_followup < len(st.session_state.followup_questions) - 1:
                            st.session_state.current_followup += 1
                            st.rerun()
                        else:
                            # Save all answers (main + follow-ups) and move to next main question
                            st.session_state.answers.append({
                                'question': current_q['question'],
                                'category': current_q['category'],
                                'answer': st.session_state.main_answer,
                                'followups': st.session_state.followup_answers if 'followup_answers' in st.session_state else []
                            })

                            # Reset for next question
                            st.session_state.followup_mode = False
                            st.session_state.followup_questions = []
                            st.session_state.current_followup = 0
                            st.session_state.main_answer = ""
                            if 'followup_answers' in st.session_state:
                                st.session_state.followup_answers = []
                            st.session_state.current_question += 1
                            st.rerun()

                with col3:
                    # Skip follow-ups button
                    if st.button("Skip Follow-ups ⏭️"):
                        # Save main answer only and move to next question
                        st.session_state.answers.append({
                            'question': current_q['question'],
                            'category': current_q['category'],
                            'answer': st.session_state.main_answer,
                            'followups': st.session_state.followup_answers if 'followup_answers' in st.session_state else []
                        })

                        # Reset for next question
                        st.session_state.followup_mode = False
                        st.session_state.followup_questions = []
                        st.session_state.current_followup = 0
                        st.session_state.main_answer = ""
                        if 'followup_answers' in st.session_state:
                            st.session_state.followup_answers = []
                        st.session_state.current_question += 1
                        st.rerun()

                # Save & Resume Later button (below follow-up navigation buttons)
                st.divider()
                if st.button("💾 Save & Resume Later", use_container_width=True, help="Save this interview and continue later"):
                    st.session_state.save_early = True
                    st.rerun()

        else:
            # Interview complete!
            st.success("🎉 Interview Complete!")
            st.balloons()

            st.subheader(f"Thank you for sharing your story, {st.session_state.parent_name}!")

            # Calculate statistics
            total_responses = len(st.session_state.answers)
            total_followups = sum(len(ans.get('followups', [])) for ans in st.session_state.answers)
            total_questions = total_responses + total_followups

            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Main Questions", f"{total_responses}/{len(questions)}")
            with col2:
                st.metric("Follow-up Answers", total_followups)
            with col3:
                st.metric("Total Responses", total_questions)

            st.divider()

            # Comprehensive review summary
            st.subheader("📋 Review Your Interview")
            st.write("Please review all your responses below. You can go back and edit if needed.")

            # Display full summary with all details
            for idx, answer_data in enumerate(st.session_state.answers):
                with st.expander(f"Q{idx+1}: {answer_data['category']} - {answer_data['question'][:60]}...", expanded=False):
                    st.markdown(f"**Category:** {answer_data['category']}")
                    st.markdown(f"**Question:** {answer_data['question']}")
                    st.markdown(f"**Answer:**")
                    st.info(answer_data['answer'])

                    # Show follow-ups if any
                    if 'followups' in answer_data and answer_data['followups']:
                        st.divider()
                        st.markdown("**AI Follow-up Questions & Answers:**")
                        for fup_idx, followup in enumerate(answer_data['followups'], 1):
                            st.markdown(f"*Follow-up {fup_idx}: {followup['question']}*")
                            st.success(followup['answer'])
                            if fup_idx < len(answer_data['followups']):
                                st.write("")

            st.divider()

            # Summary before saving
            st.subheader("💾 Ready to Save?")
            st.write("Your interview will be saved with AI-extracted structured data automatically.")

            # Action buttons
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                if st.button("⬅️ Back to Edit", use_container_width=True):
                    # Go back to last question for editing
                    if total_responses > 0:
                        st.session_state.current_question = total_responses - 1
                        st.rerun()

            with col2:
                if st.button("💾 Save Interview", type="primary", use_container_width=True):
                    # Automatically extract data before saving
                    with st.spinner("💾 Saving interview and extracting data with AI..."):
                        try:
                            # Run extraction
                            extraction_result = extract_structured_data(
                                st.session_state.answers,
                                st.session_state.parent_name
                            )

                            # Save the interview data with extracted data (marked as complete)
                            success, filepath, error = save_interview_data(
                                st.session_state.parent_name,
                                st.session_state.answers,
                                extraction_result,
                                completed=True,
                                current_question=len(questions),
                                total_questions=len(questions),
                                existing_filepath=st.session_state.resuming_filepath
                            )

                            if success:
                                if extraction_result['success']:
                                    st.success(f"✅ Interview saved successfully with AI-extracted data!")
                                else:
                                    st.success(f"✅ Interview saved successfully!")
                                    st.warning(f"⚠️ Data extraction failed: {extraction_result['error']}")
                                st.info(f"📁 Saved to: `{filepath}`")

                                st.balloons()
                            else:
                                st.error(f"❌ Failed to save interview: {error}")

                        except Exception as e:
                            st.error(f"❌ Unexpected error: {str(e)}")
                            st.info("💡 The interview data could not be saved. Please try again.")

                    # If save was successful, continue with PDF generation
                    if success:

                        # Generate PDF and offer download
                        import tempfile
                        import os

                        # Create PDF in temp directory
                        temp_dir = tempfile.gettempdir()
                        pdf_filename = f"{st.session_state.parent_name.replace(' ', '_')}_interview.pdf"
                        pdf_path = os.path.join(temp_dir, pdf_filename)

                        # Load the saved interview data
                        import json
                        with open(filepath, 'r', encoding='utf-8') as f:
                            interview_data = json.load(f)

                        # Generate PDF
                        pdf_success = export_to_pdf(interview_data, pdf_path)

                        if pdf_success:
                            # Offer PDF download
                            with open(pdf_path, 'rb') as pdf_file:
                                st.download_button(
                                    label="📄 Download Interview as PDF",
                                    data=pdf_file,
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    use_container_width=True
                                )

                        # Show what was saved
                        with st.expander("📄 View saved data summary"):
                            st.write(f"**Parent:** {st.session_state.parent_name}")
                            st.write(f"**Questions answered:** {len(st.session_state.answers)}")
                            total_followups = sum(len(ans.get('followups', [])) for ans in st.session_state.answers)
                            st.write(f"**Follow-up answers:** {total_followups}")
                            st.write(f"**Extracted data:** {'Yes ✓' if st.session_state.extracted_data else 'No'}")
                            st.write(f"**File:** {filepath}")
                    else:
                        st.error(f"❌ Failed to save interview: {error}")

            with col3:
                if st.button("🔄 Start New Interview", use_container_width=True):
                    st.session_state.started = False
                    st.session_state.current_question = 0
                    st.session_state.answers = []
                    st.session_state.parent_name = ""
                    st.session_state.followup_mode = False
                    st.session_state.followup_questions = []
                    st.session_state.current_followup = 0
                    st.session_state.main_answer = ""
                    st.session_state.extracted_data = None
                    st.session_state.extraction_complete = False
                    st.session_state.transcription_cache = {}  # Clear transcription cache
                    st.session_state.resuming_filepath = None  # Clear resume tracking
                    if 'followup_answers' in st.session_state:
                        st.session_state.followup_answers = []
                    st.rerun()

elif st.session_state.app_mode == "View":
    # VIEW INTERVIEWS MODE
    st.subheader("📚 Browse Saved Interviews")

    # Get all saved interview files
    try:
        interview_files = get_all_interview_files()
    except:
        interview_files = []

    if not interview_files:
        st.warning("📭 No saved interviews found yet!")
        st.info("Complete an interview first, then come back here to view it.")
    else:
        # If no interview is selected, show the list
        if not st.session_state.selected_interview_data:
            st.write(f"**{len(interview_files)} interview(s) available**")
            st.write("Click on an interview to view details:")
            st.divider()

            # Display each interview as a clickable card
            for idx, (filename, filepath) in enumerate(interview_files, 1):
                interview_data = load_interview_file(filepath)
                if interview_data:
                    parent_name = interview_data.get('parent_name', 'Unknown')
                    interview_date = interview_data.get('interview_date', 'Unknown')[:10]
                    total_questions = interview_data.get('interview_data', {}).get('total_questions', 0)
                    total_followups = interview_data.get('interview_data', {}).get('total_followups', 0)

                    # Check if interview is incomplete
                    metadata = interview_data.get('metadata', {})
                    is_complete = metadata.get('completed', True)  # Default to True for old interviews
                    current_q = metadata.get('current_question', 0)
                    max_q = metadata.get('max_questions', 10)

                    col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1.5])

                    with col1:
                        label = f"📄 {parent_name}"
                        if not is_complete:
                            label = f"⏸️ {parent_name}"
                        if st.button(label, key=f"view_btn_{idx}", use_container_width=True):
                            st.session_state.selected_interview_data = interview_data
                            st.session_state.selected_interview_file = filepath
                            st.rerun()

                    with col2:
                        st.write(f"📅 {interview_date}")

                    with col3:
                        st.write(f"💬 {total_questions}+{total_followups}")

                    with col4:
                        if not is_complete:
                            if st.button("▶️ Resume", key=f"resume_btn_{idx}", type="primary"):
                                # Load interview data into session state to resume
                                st.session_state.parent_name = parent_name
                                st.session_state.answers = interview_data.get('interview_data', {}).get('questions_and_answers', [])
                                st.session_state.current_question = current_q
                                st.session_state.started = True
                                st.session_state.followup_mode = False
                                st.session_state.followup_questions = []
                                st.session_state.current_followup = 0
                                st.session_state.main_answer = ""
                                st.session_state.resuming_filepath = filepath
                                st.session_state.app_mode = "Interview"
                                st.rerun()
                        else:
                            st.write("✅ Complete")

                    if not is_complete:
                        st.caption(f"📊 Progress: {current_q}/{max_q} questions")
                    st.caption(f"File: {filename}")
                    st.divider()

        # If an interview is selected, show its details
        else:
            interview_data = st.session_state.selected_interview_data
            parent_name = interview_data.get('parent_name', 'Unknown')

            # Check if interview is incomplete
            metadata = interview_data.get('metadata', {})
            is_complete = metadata.get('completed', True)
            current_q = metadata.get('current_question', 0)
            max_q = metadata.get('max_questions', 10)

            # Show incomplete banner if applicable
            if not is_complete:
                st.warning(f"⏸️ **This interview is incomplete** ({current_q}/{max_q} questions answered)")
                if st.button("▶️ Resume Interview", type="primary", use_container_width=True):
                    st.session_state.parent_name = parent_name
                    st.session_state.answers = interview_data.get('interview_data', {}).get('questions_and_answers', [])
                    st.session_state.current_question = current_q
                    st.session_state.started = True
                    st.session_state.followup_mode = False
                    st.session_state.followup_questions = []
                    st.session_state.current_followup = 0
                    st.session_state.main_answer = ""
                    st.session_state.resuming_filepath = st.session_state.selected_interview_file
                    st.session_state.selected_interview_data = None
                    st.session_state.selected_interview_file = None
                    st.session_state.app_mode = "Interview"
                    st.rerun()
                st.divider()

            # Header with back button and delete button
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                if st.button("← Back to List"):
                    st.session_state.selected_interview_data = None
                    st.session_state.selected_interview_file = None
                    st.rerun()

            with col2:
                # PDF Download button
                import tempfile, os
                temp_dir = tempfile.gettempdir()
                pdf_filename = f"{parent_name.replace(' ', '_')}_interview.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)

                if export_to_pdf(interview_data, pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        st.download_button(
                            label="📄 PDF",
                            data=pdf_file,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            use_container_width=True
                        )

            with col3:
                if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                    st.session_state.confirm_delete = True

            # Delete confirmation
            if st.session_state.get('confirm_delete', False):
                st.warning(f"⚠️ **Are you sure you want to delete {parent_name}'s interview?**")
                st.write("This action cannot be undone.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
                        try:
                            import os
                            os.remove(st.session_state.selected_interview_file)
                            st.session_state.selected_interview_data = None
                            st.session_state.selected_interview_file = None
                            st.session_state.confirm_delete = False
                            st.success(f"✅ {parent_name}'s interview has been deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting interview: {str(e)}")

                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.confirm_delete = False
                        st.rerun()

            st.divider()

            # Show interview details with tabs
            st.title(f"Interview with {parent_name}")
            interview_date = interview_data.get('interview_date', 'Unknown')[:10]
            st.caption(f"Conducted on: {interview_date}")

            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📝 Interview Q&A", "📊 Extracted Data", "📄 Documents"])

            with tab1:
                # Display all Q&A
                questions_and_answers = interview_data.get('interview_data', {}).get('questions_and_answers', [])

                for idx, qa in enumerate(questions_and_answers, 1):
                    st.markdown(f"### Question {idx}: {qa.get('question', 'Unknown')}")
                    st.markdown(f"**Category:** {qa.get('category', 'Unknown')}")
                    st.info(qa.get('answer', 'No answer'))

                    # Show follow-up questions
                    followups = qa.get('followups', [])
                    if followups:
                        with st.expander(f"💬 {len(followups)} Follow-up Question(s)"):
                            for f_idx, followup in enumerate(followups, 1):
                                st.markdown(f"**Follow-up {f_idx}:** {followup.get('question', 'Unknown')}")
                                st.info(followup.get('answer', 'No answer'))
                                if f_idx < len(followups):
                                    st.divider()

                    st.divider()

            with tab2:
                # Display extracted data
                extracted_data = interview_data.get('extracted_data')

                if extracted_data:
                    display_markdown = format_extraction_for_display(extracted_data)
                    st.markdown(display_markdown)
                else:
                    st.warning("⚠️ No structured data extracted from this interview yet")
                    st.info("Data extraction may have failed or was not performed for this interview.")

            with tab3:
                # Documents tab
                st.markdown("### 📄 Family Documents")
                st.write("Upload and store important family documents like birth certificates, marriage certificates, news clippings, and photos.")

                # Create documents directory structure
                docs_dir = Path('data/documents') / parent_name.replace(' ', '_')
                docs_dir.mkdir(parents=True, exist_ok=True)

                # File uploader
                uploaded_files = st.file_uploader(
                    "Upload documents",
                    type=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'txt', 'doc', 'docx'],
                    accept_multiple_files=True,
                    help="Upload family documents - PDFs, images, or text files"
                )

                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        # Save file
                        file_path = docs_dir / uploaded_file.name
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(f"✅ Uploaded: {uploaded_file.name}")

                st.divider()

                # Display existing documents
                if docs_dir.exists():
                    existing_docs = list(docs_dir.glob('*'))
                    if existing_docs:
                        st.markdown(f"**Stored Documents ({len(existing_docs)}):**")
                        for doc_path in sorted(existing_docs):
                            col_a, col_b, col_c = st.columns([3, 1, 1])
                            with col_a:
                                st.write(f"📎 {doc_path.name}")
                            with col_b:
                                # Download button
                                with open(doc_path, 'rb') as f:
                                    st.download_button(
                                        "Download",
                                        data=f,
                                        file_name=doc_path.name,
                                        key=f"download_{doc_path.name}"
                                    )
                            with col_c:
                                # Delete button
                                if st.button("Delete", key=f"delete_{doc_path.name}"):
                                    try:
                                        doc_path.unlink()
                                        st.success(f"Deleted {doc_path.name}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {str(e)}")
                    else:
                        st.info("No documents uploaded yet. Use the uploader above to add files.")
                else:
                    st.info("No documents uploaded yet. Use the uploader above to add files.")

elif st.session_state.app_mode == "Q&A":
    # Q&A MODE
    st.subheader("💬 Ask Questions About Your Family")
    st.write("Search across all saved interviews to find answers")

    # Get all saved interview files
    try:
        interview_files = get_all_interview_files()
    except:
        interview_files = []

    if not interview_files:
        st.warning("📭 No saved interviews found yet!")
        st.info("Complete an interview first, then come back here to query your family vault.")
    else:
        # Show vault statistics
        st.success(f"📚 **FamilyVaultAI:** {len(interview_files)} interview(s) available")

        # Show all interviews in vault
        with st.expander("📊 View All Interviews"):
            for idx, (filename, filepath) in enumerate(interview_files, 1):
                interview_data = load_interview_file(filepath)
                if interview_data:
                    st.write(f"{idx}. **{interview_data.get('parent_name', 'Unknown')}** - {interview_data.get('interview_date', 'Unknown')[:10]}")

        st.divider()

        # Q&A Interface
        st.markdown("### Ask Anything About Your Family")

        # Interview selector for Q&A
        interview_options = ["All Interviews"] + [interview_data.get('parent_name', 'Unknown')
                                                  for filename, filepath in interview_files
                                                  for interview_data in [load_interview_file(filepath)] if interview_data]

        # Initialize qa_search_target if not exists
        if 'qa_search_target' not in st.session_state:
            st.session_state.qa_search_target = "All Interviews"

        col1, col2 = st.columns([2, 1])

        with col1:
            qa_search_target = st.selectbox(
                "Search in:",
                options=interview_options,
                index=interview_options.index(st.session_state.qa_search_target) if st.session_state.qa_search_target in interview_options else 0,
                help="Choose which interview(s) to search",
                key="qa_search_target_selector"
            )
            st.session_state.qa_search_target = qa_search_target

        with col2:
            voice_mode = st.checkbox(
                "🎤 Voice Mode",
                value=st.session_state.voice_mode_enabled,
                help="Enable voice input for questions and voice output for answers",
                key="voice_mode_checkbox"
            )
            st.session_state.voice_mode_enabled = voice_mode

        # Voice settings (only show if voice mode is enabled)
        if st.session_state.voice_mode_enabled:
            voice_profiles = get_voice_profile_names()
            selected_voice = st.selectbox(
                "AI Voice Style:",
                options=voice_profiles,
                index=voice_profiles.index(st.session_state.selected_voice_profile) if st.session_state.selected_voice_profile in voice_profiles else 0,
                help="Choose the voice style for AI answers",
                key="voice_profile_selector"
            )
            st.session_state.selected_voice_profile = selected_voice

            st.divider()

        # Question input - voice or text
        question = ""

        if st.session_state.voice_mode_enabled:
            # Voice input option
            input_method = st.radio(
                "Ask your question by:",
                ["Typing", "Speaking"],
                horizontal=True,
                key="qa_input_method"
            )

            if input_method == "Typing":
                question = st.text_input(
                    "What would you like to know?",
                    placeholder="e.g., What year was Clint Johnson born? Where did grandpa grow up?",
                    help="Type your question",
                    key="qa_text_question"
                )
            else:
                st.write("**🎤 Record your question (hands-free mode):**")
                st.caption("Record as many questions as you want - the latest one will be used!")

                # Add clear button if there's an active question
                if 'qa_current_question' in st.session_state and st.session_state.qa_current_question:
                    col_q1, col_q2 = st.columns([3, 1])
                    with col_q1:
                        st.info(f"**Current question:** {st.session_state.qa_current_question}")
                    with col_q2:
                        if st.button("🔄 Clear", use_container_width=True, help="Clear current question and record a new one"):
                            st.session_state.qa_current_question = None
                            st.session_state.qa_current_audio_key = None
                            st.session_state.qa_search_completed = False
                            st.session_state.qa_auto_search_trigger = False
                            st.rerun()

                audio_question = st.audio_input(
                    "Click to start/stop recording",
                    key="qa_audio_question"
                )

                if audio_question:
                    # Use audio bytes as unique key to track this specific recording
                    audio_hash = hash(audio_question.getbuffer().tobytes())
                    audio_key = f"qa_audio_transcription_{audio_hash}"

                    # Only transcribe if this is a new recording (different hash)
                    if audio_key != st.session_state.get('qa_current_audio_key'):
                        with st.spinner("🎤 Transcribing your question..."):
                            transcript = transcribe_audio(audio_question)
                            if transcript:
                                st.session_state.transcription_cache[audio_key] = transcript
                                st.session_state.qa_current_question = transcript
                                st.session_state.qa_current_audio_key = audio_key
                                st.session_state.qa_auto_search_trigger = True  # Trigger auto-search
                                st.session_state.qa_search_completed = False  # Reset search state
                                st.success(f"✅ Heard: \"{transcript}\"")
                                st.info("🔍 Searching for answer...")
                                st.rerun()
                    else:
                        # Show cached transcription
                        if audio_key in st.session_state.transcription_cache:
                            question = st.session_state.transcription_cache[audio_key]

                # Use the current question if available
                if 'qa_current_question' in st.session_state and st.session_state.qa_current_question:
                    question = st.session_state.qa_current_question
        else:
            # Standard text input
            question = st.text_input(
                "What would you like to know?",
                placeholder="e.g., What year was Clint Johnson born? Where did grandpa grow up?",
                help="AI will search through selected interview(s) to find the answer",
                key="qa_text_question_simple"
            )

        # Check if auto-search should be triggered
        should_auto_search = st.session_state.qa_auto_search_trigger and not st.session_state.qa_search_completed

        # Manual search button (fallback for errors/empty transcripts)
        col1, col2 = st.columns([3, 1])

        manual_search_clicked = False
        with col1:
            search_button_label = f"🔍 Search {qa_search_target}" if qa_search_target != "All Interviews" else "🔍 Search All Interviews"
            if st.button(search_button_label, type="primary", use_container_width=True):
                manual_search_clicked = True

        # Execute search if auto-triggered or manual button clicked
        if (should_auto_search or manual_search_clicked) and question:
                    # Filter interviews based on selection
                    if qa_search_target == "All Interviews":
                        interviews_to_search = interview_files
                    else:
                        interviews_to_search = [(filename, filepath) for filename, filepath in interview_files
                                               if load_interview_file(filepath) and
                                               load_interview_file(filepath).get('parent_name') == qa_search_target]

                    with st.spinner(f"🤖 Searching {qa_search_target}..."):
                        try:
                            # Search across selected interviews
                            found_answer = False
                            best_answer = None

                            for filename, filepath in interviews_to_search:
                                interview_data = load_interview_file(filepath)
                                if interview_data:
                                    result = search_and_answer(question, interview_data)

                                    if result['success'] and result['answer']:
                                        # Check if answer contains actual information
                                        if "don't have information" not in result['answer'].lower():
                                            parent_name = interview_data.get('parent_name', 'Unknown')

                                            # Generate audio if voice mode is enabled
                                            audio_paths = {}  # Store audio for different voices
                                            if st.session_state.voice_mode_enabled:
                                                with st.spinner("🔊 Generating voice response..."):
                                                    try:
                                                        # Use OpenAI TTS
                                                        success, audio_path, error = text_to_speech(
                                                            result['answer'],
                                                            st.session_state.selected_voice_profile
                                                        )
                                                        voice_key = st.session_state.selected_voice_profile

                                                        if not success:
                                                            st.error(f"⚠️ Voice generation failed: {error}")
                                                        elif audio_path and os.path.exists(audio_path):
                                                            audio_paths[voice_key] = audio_path
                                                            st.success(f"✅ Voice generated")
                                                        else:
                                                            st.warning(f"⚠️ Voice file not found at: {audio_path}")
                                                    except Exception as e:
                                                        st.error(f"❌ Exception during TTS: {str(e)}")
                                                        import traceback
                                                        st.code(traceback.format_exc())

                                            # Add to history
                                            st.session_state.qa_history.append({
                                                'question': question,
                                                'answer': result['answer'],
                                                'source': parent_name,
                                                'audio_paths': audio_paths
                                            })

                                            # Set flag to auto-play this new answer
                                            st.session_state.just_answered = True

                                            found_answer = True
                                            break  # Found answer, stop searching

                            if found_answer:
                                # Mark search as completed and clear auto-search trigger
                                st.session_state.qa_search_completed = True
                                st.session_state.qa_auto_search_trigger = False
                                st.rerun()
                            else:
                                st.warning(f"❌ No relevant information found in {qa_search_target}")
                                st.info("💡 Try rephrasing your question or check if this information was captured in the interviews.")
                                # Mark search as completed even if no answer found
                                st.session_state.qa_search_completed = True
                                st.session_state.qa_auto_search_trigger = False

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.info("💡 Please check your internet connection and OpenAI API status.")
                            # Mark search as completed even on error
                            st.session_state.qa_search_completed = True
                            st.session_state.qa_auto_search_trigger = False
        elif should_auto_search and not question:
            # Auto-search triggered but no question (edge case)
            st.warning("⚠️ Please enter a question")
            st.session_state.qa_auto_search_trigger = False

        with col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.qa_history = []
                st.rerun()

        # Show "Ask another question" button after search is completed
        if st.session_state.qa_search_completed:
            st.divider()
            col_aq1, col_aq2, col_aq3 = st.columns([1, 2, 1])
            with col_aq2:
                if st.button("🎤 Ask Another Question", type="primary", use_container_width=True, help="Clear current question and ask a new one"):
                    # Reset Q&A state
                    st.session_state.qa_current_question = None
                    st.session_state.qa_current_audio_key = None
                    st.session_state.qa_search_completed = False
                    st.session_state.qa_auto_search_trigger = False
                    st.rerun()

        # Display Q&A History and Extracted Data with Tabs
        st.divider()

        # Create tabs for Q&A history and extracted data
        tab1, tab2 = st.tabs(["💬 Q&A History", "📊 All Extracted Data"])

        with tab1:
            if st.session_state.qa_history:
                st.markdown("### Conversation History")

                for idx, qa in enumerate(reversed(st.session_state.qa_history)):
                    with st.container():
                        st.markdown(f"**Q{len(st.session_state.qa_history) - idx}:** {qa['question']}")
                        st.markdown(f"*Source: {qa.get('source', 'Unknown')}'s interview*")

                        # Show text answer
                        st.info(qa['answer'])

                        # Generate and play audio if voice mode is enabled
                        if st.session_state.voice_mode_enabled and qa.get('answer'):
                            audio_paths = qa.get('audio_paths', {})
                            current_voice = st.session_state.selected_voice_profile

                            # Check if we have audio for this voice, generate if not
                            if current_voice not in audio_paths or not os.path.exists(audio_paths.get(current_voice, '')):
                                try:
                                    success, audio_path, error = text_to_speech(qa['answer'], current_voice)
                                    if success and audio_path:
                                        audio_paths[current_voice] = audio_path
                                        qa['audio_paths'] = audio_paths
                                except:
                                    pass

                            # Play audio if available
                            if current_voice in audio_paths and os.path.exists(audio_paths[current_voice]):
                                try:
                                    with open(audio_paths[current_voice], 'rb') as audio_file:
                                        audio_bytes = audio_file.read()
                                    is_most_recent = (idx == 0)
                                    should_autoplay = is_most_recent and st.session_state.just_answered
                                    st.audio(audio_bytes, format='audio/wav', autoplay=should_autoplay)

                                    if should_autoplay:
                                        st.caption(f"🔊 Playing response")
                                    else:
                                        st.caption(f"Voice: {current_voice}")
                                except Exception as e:
                                    st.caption(f"⚠️ Audio playback error: {str(e)}")

                        st.divider()

                # Clear the just_answered flag after rendering
                if st.session_state.just_answered:
                    st.session_state.just_answered = False
            else:
                st.info("No questions asked yet. Enter a question above to start searching your family vault.")

        with tab2:
            st.markdown("### Extracted Data from All Interviews")

            # Show extracted data from all interviews
            for idx, (filename, filepath) in enumerate(interview_files, 1):
                interview_data = load_interview_file(filepath)
                if interview_data:
                    parent_name = interview_data.get('parent_name', 'Unknown')
                    extracted_data = interview_data.get('extracted_data')

                    with st.expander(f"📄 {parent_name}'s Extracted Data", expanded=(idx == 1)):
                        if extracted_data:
                            display_markdown = format_extraction_for_display(extracted_data)
                            st.markdown(display_markdown)
                        else:
                            st.warning("⚠️ No structured data extracted from this interview yet")

        # Example questions
        st.divider()
        st.markdown("### 💡 Example Questions")
        st.write("Try asking:")

        example_questions = [
            "What year was [name] born?",
            "Where did [name] grow up?",
            "What was [name]'s first job?",
            "What values did [name] learn from their parents?",
            "Tell me about [name]'s childhood",
            "What life lessons did [name] share?"
        ]

        for ex_q in example_questions:
            st.write(f"• {ex_q}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #0F1C2E; padding: 20px;'>
    <small>
    FamilyVaultAI v1.0 | Preserve family memories forever<br>
    Powered by OpenAI GPT-4 | Built with Streamlit<br>
    💡 <b>Tip:</b> Use Quick Search in the sidebar to find information across all interviews
    </small>
</div>
""", unsafe_allow_html=True)
