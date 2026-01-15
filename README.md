# AI Granny Prototype - Setup Instructions

## Day 1 Setup Status

✅ Python 3.9.6 installed
✅ Project folder created
✅ Required libraries installed (streamlit, openai, python-dotenv)
✅ Test script created

## Next Steps to Complete Day 1

### 1. Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create an account (or sign in if you have one)
3. Click the **"Create new secret key"** button
4. Give it a name like "AI Granny Dev"
5. **Copy the key immediately** (you won't be able to see it again!)

### 2. Add API Key to .env File

1. Open the `.env` file in this folder (it's a hidden file)
2. Find the line: `OPENAI_API_KEY=your_api_key_here`
3. Replace `your_api_key_here` with your actual API key
4. Save the file

**Example:**
```
OPENAI_API_KEY=sk-proj-abc123xyz789...
```

**IMPORTANT:** Never share this key or commit the .env file to git!

### 3. Add Credits to OpenAI Account

1. Go to https://platform.openai.com/settings/organization/billing
2. Add **$20** in credits (this should be plenty for MVP development)
3. This is required for the API to work

### 4. Test the Connection

Open Terminal and run:
```bash
cd ~/Desktop/AI\ Granny/ai-granny-prototype
python3 test_openai.py
```

If you see "✅ SUCCESS! OpenAI API is working!" - you're done with Day 1!

If you see errors:
- Double-check your API key in the .env file
- Make sure you added billing credits
- Wait a few minutes if you just created the key

## Project Structure

```
ai-granny-prototype/
├── README.md                  # This file
├── test_openai.py             # API connection test
├── .env                       # Your API key (DO NOT COMMIT!)
├── data/                      # Data storage folder
│   └── parent_profiles/       # Interview data will go here
└── utils/                     # Helper functions (will create later)
```

## What's Next?

Once Day 1 is complete, you'll move on to **Day 2: Learn Streamlit + Build Interview UI**

Refer to your Sprint2_Build_Plan.md for the full schedule!

## Getting Help

- First: Ask Claude Code (paste any error messages)
- Second: Bootcamp Slack channel
- Third: OpenAI community forum

---

**You're doing great! Keep going!** 🚀
