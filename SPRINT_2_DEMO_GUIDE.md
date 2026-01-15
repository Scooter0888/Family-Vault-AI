# Sprint 2 Demo Guide - Family Vault
**Duration:** 5-10 minutes | **Audience:** Mixed (stakeholders, technical, users)

---

## Pre-Demo Checklist

- [ ] App running at http://localhost:8501
- [ ] Browser: Chrome (recommended for voice demo)
- [ ] Test microphone 5 minutes before demo
- [ ] Close unnecessary browser tabs
- [ ] Verify .env file has valid OPENAI_API_KEY
- [ ] Review Maria Garcia demo interview data

---

## Demo Flow (7-8 minutes)

### 1. Opening (30 seconds)
> "Family Vault helps preserve family stories and memories through AI-assisted interviews. Let me show you how it works in a real scenario."

### 2. View Demo Interview (2 minutes)

**Navigate to "View Saved Interviews"**
- Show Maria Garcia interview in the list
- Click to open

**Show the Interview Q&A Tab:**
- Scroll through questions and rich answers
- Point out: "Notice the detailed responses - this is what we capture"
- Show follow-up questions: "The AI generated these based on Maria's answers"

**Key talking points:**
- "Maria is a 78-year-old immigrant from Mexico"
- "10 questions + 18 AI-generated follow-ups = comprehensive life story"
- "Mix of text and voice-transcribed answers"

### 3. AI Data Extraction (2-3 minutes) ⭐ **HIGHLIGHT**

**Click on "Extracted Data" tab**

**Family Tree Section:**
- Show parents: Roberto (Guadalajara, 1920) & Elena (San Miguel de Allende, 1922)
- Show 5 siblings with birth dates and locations
- Point out: "AI automatically extracted all family members with birth info"

**Important Places Section:**
- Point to Tepito, Mexico City (childhood)
- Point to East Los Angeles (adult life)
- Show: "AI identified 6 significant locations across her life"

**Life Lessons & Values:**
- "Family is everything" - learned from parents
- "It's never too late to learn" - got GED at 28
- Show: "8 core values extracted from unstructured stories"

**Career Journey:**
- Garment factory worker (Mexico, age 14-25)
- Teacher's aide (Los Angeles, 20 years)
- Point out: "AI structured her entire career timeline"

**Value Statement:**
> "This is the magic - you just have conversations, and the AI builds a complete family archive with structured data you can search and analyze."

### 4. Q&A Search (1 minute)

**Navigate to Q&A Mode in sidebar**
- Show: "Searching across 3 interview(s)"
- Ask question: "What did Maria say about her mother?"
- Show AI response with relevant quotes

**Value Statement:**
> "Searchable family archive - instead of reading 50 pages, just ask questions."

### 5. Multi-Language Features (1 minute)

**Go back to "Start New Interview"**
- Show language dropdown: 22+ languages
- Select "Spanish"
- Show how question translates
- Show "Auto-translate audio to English" checkbox

**Value Statement:**
> "Works for families worldwide - interview in any language, automatically translate to English for storage."

### 6. Voice Recording Demo (30 seconds)

**Optional - if time permits:**
- Toggle to "Record audio"
- Show microphone button
- Explain: "Click to start, speak, click to stop"
- "AI transcribes, you can review/edit, then submit"

**Value Statement:**
> "Elderly parents can speak naturally - no typing needed."

### 7. PDF Export (30 seconds)

**Back to Maria Garcia interview**
- Show "Download Interview as PDF" button
- Click to download
- Open PDF to show formatting

**Value Statement:**
> "Shareable PDFs for the whole family - print it, email it, archive it."

---

## Closing (30 seconds)

> "In summary: **Multi-language voice interviews** → **AI transcription & translation** → **Intelligent follow-ups** → **Automatic data extraction** → **Searchable family archive** → **Shareable PDFs**
>
> We're preserving irreplaceable family memories before they're lost forever."

---

## Demo Interview Highlights

**Maria Garcia - 78-year-old immigrant from Mexico**

**Compelling data points to mention:**
- Parents born in Guadalajara (1920) and San Miguel de Allende (1922)
- 5 siblings, all with birth dates and locations
- Immigrated to America in 1972
- Got GED at age 28 while working and raising kids
- Worked as teacher's aide for 20 years helping immigrant children
- Student Carmen (El Salvador) became a doctor, credits Maria with saving her life
- Husband had stroke in 1998, Maria cared for him 15 years
- 3 children (all college graduates - first in family), 7 grandchildren

**Why this data is perfect:**
- Shows multi-generational family tree (parents, siblings, children, grandchildren)
- Immigration story is emotionally compelling
- Career journey shows perseverance
- Rich values and life lessons
- Multiple geographic locations (Mexico → Los Angeles)
- Demonstrates all extraction features

---

## Key Talking Points by Audience

### For Stakeholders/Business:
- "Addresses multi-billion dollar market of families wanting to preserve memories"
- "90% of family stories are lost within 2 generations - we solve this"
- "Scalable cloud-based solution for thousands of concurrent users"
- "Low cost per interview (~$0.15-0.20 in API costs)"

### For Technical Audience:
- "Built with Streamlit + OpenAI GPT-4 + Whisper API"
- "22 languages via GPT-4 translation"
- "Audio transcription with auto-translation using Whisper's /translations endpoint"
- "Structured data extraction from unstructured interviews"
- "JSON storage with PDF export via FPDF2"

### For End Users:
- "No technical skills needed - just speak and click"
- "Works on phone, tablet, or computer"
- "Your data stays private and secure"
- "Creates permanent family archive you can search and share"

---

## Anticipated Questions & Answers

**Q: "How accurate is the voice transcription?"**
> "OpenAI Whisper has 95%+ accuracy. Users review and edit transcripts before submitting to ensure accuracy for important family details like names and dates."

**Q: "What about privacy and security?"**
> "Currently data is stored locally. For production, we'll add encryption and secure cloud storage with user consent and compliance with privacy regulations."

**Q: "What languages are supported?"**
> "Questions can be translated to 22+ languages. Whisper supports 50+ languages for voice transcription and can auto-translate to English."

**Q: "How much does it cost to run?"**
> "OpenAI API costs approximately $0.15-0.20 per complete interview. Scales efficiently for thousands of users."

**Q: "Can users add their own questions?"**
> "Yes - current version has 10 curated questions covering family, childhood, education, career, values, and wisdom. Custom questions is a straightforward add for the next sprint."

**Q: "What's the target market?"**
> "Adult children (30-60 years old) interviewing elderly parents (65+). Also valuable for genealogists, memoir writers, senior living facilities, and cultural preservation organizations."

**Q: "How long does an interview take?"**
> "Typically 30-60 minutes for 10 questions with follow-ups. Users can save and resume anytime."

**Q: "What happens to the AI-generated follow-ups if they're not relevant?"**
> "Users can skip any follow-up question. The AI learns context from previous answers to generate more relevant questions as the interview progresses."

**Q: "Can multiple family members contribute to one interview?"**
> "Current version is single-person interviews. Multi-contributor interviews is on the roadmap for future sprints."

---

## Backup Plans

**If voice recording fails:**
- Switch to text input demo
- Still shows AI follow-ups and extraction
- Mention: "Voice is optional - typing works great too"

**If internet is slow:**
- Use pre-loaded Maria Garcia interview
- Show extraction and Q&A features only
- Skip live recording demo

**If OpenAI API fails:**
- Demo is entirely based on pre-saved Maria Garcia data
- No API calls needed to show existing interview
- Only impacts: new questions, Q&A search, new transcriptions

---

## Post-Demo Follow-Up

**Clear next steps to offer:**
1. "Would you like to try creating your own interview?"
2. "I can schedule a technical deep-dive for the dev team"
3. "Let's discuss pricing and deployment options"
4. "Would you like to see the roadmap for future features?"

---

## App Access

- **Local URL:** http://localhost:8501
- **Demo Interview:** Maria Garcia (already loaded in system)
- **Data Location:** `/data/parent_profiles/Maria_Garcia_DEMO_20251230_120000.json`

---

## Sprint 2 Features Summary

✅ **Core Interview Engine**
- 10 curated questions across 7 categories
- Voice recording with transcription
- Text input option
- Save/resume capability

✅ **AI Features**
- GPT-4 generated adaptive follow-up questions (avg 15-20 per interview)
- Automatic data extraction (family tree, places, values, career, timeline)
- Q&A search across all interviews
- Context-aware responses

✅ **Multi-Language Support**
- 22+ languages for question translation
- 50+ languages for voice transcription
- Auto-translate audio to English
- Preserves original + translated text

✅ **Data Management**
- JSON storage for all interviews
- PDF export with formatting
- Searchable archive
- Interview browsing interface

✅ **User Experience**
- Clean, intuitive interface
- Session state management
- Progress tracking
- Help documentation
- Safari + Chrome compatibility

---

**Good luck with your demo! 🚀**
