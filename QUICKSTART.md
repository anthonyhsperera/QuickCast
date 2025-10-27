# Quick Start Guide

Get your AI Podcast Generator running in 5 minutes!

## Prerequisites

You'll need:
1. OpenAI API key → Get it at https://platform.openai.com/api-keys
2. Speechmatics API key → Get it at https://portal.speechmatics.com/
3. Python 3.8+ installed
4. ffmpeg installed

## Installation

### Option 1: Automated Setup (Recommended)

```bash
./setup.sh
```

Then edit `backend/.env` with your API keys and run:

```bash
source venv/bin/activate
cd backend
python app.py
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env and add your keys

# 4. Run the server
python app.py
```

## First Podcast

1. Open http://localhost:8080 in your browser
2. Paste any article URL (e.g., from TechCrunch, Medium, etc.)
3. Click "Generate Podcast"
4. Wait 2-5 minutes
5. Play your podcast!

## Example URLs to Try

- https://techcrunch.com/latest/
- https://blog.openai.com/
- https://www.theverge.com/tech
- Any Medium.com article
- Most news sites and blogs

## Troubleshooting

**Server won't start?**
- Check that port 8080 is available
- Verify API keys are set in `backend/.env`

**Generation fails?**
- Check API key validity and quotas
- Try a different article URL
- Check console logs for errors

**No audio?**
- Verify ffmpeg is installed: `ffmpeg -version`
- Check browser console for errors

## Project Structure

```
TTS Project 1/
├── backend/          # Python Flask API
│   ├── app.py       # Main server
│   ├── services/    # Core functionality
│   └── .env         # Your API keys (create this!)
├── frontend/         # Web interface
└── output/          # Generated podcasts (auto-created)
```

## What Happens When You Generate a Podcast?

1. **Scraping** (10s): Extracts article content
2. **Script Generation** (30s): GPT-4 writes dialogue for Sarah & Theo
3. **Speech Synthesis** (60-90s): Speechmatics generates audio
4. **Audio Processing** (20s): Combines and normalizes audio
5. **Done!** 🎉

## Tips

- Shorter articles work better (5-10 min read time)
- News articles and blog posts work best
- Technical documentation may not work as well
- Each podcast costs ~$0.10-0.30 in API credits

## Next Steps

- Read the full README.md for detailed documentation
- Customize dialogue style in `backend/services/llm.py`
- Adjust pause duration in `backend/app.py`
- Add background music (see README.md)

## Need Help?

Check the full README.md for:
- Detailed API documentation
- Customization options
- Advanced troubleshooting
- Architecture details

---

Have fun creating podcasts! 🎙️
