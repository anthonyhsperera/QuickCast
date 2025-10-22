# AI Podcast Generator

Transform any news article or blog post into an engaging podcast conversation between two AI hosts (Sarah and Theo) using OpenAI and Speechmatics TTS.

## Features

- **URL-based Input**: Simply paste a news article or blog URL
- **AI-Powered Dialogue**: GPT-4 generates natural, conversational podcast scripts
- **Realistic Voices**: Speechmatics TTS with Sarah and Theo voices
- **5-10 Minute Podcasts**: Perfect length for quick consumption
- **Web Player**: Built-in audio player with play/pause, seek, and volume controls
- **Download Support**: Save podcasts for offline listening

## Architecture

```
┌─────────────┐
│   Frontend  │  Simple browser UI
│  (HTML/CSS/ │
│     JS)     │
└──────┬──────┘
       │
       │ HTTP API
       │
┌──────▼──────┐
│   Backend   │  Flask API Server
│   (Python)  │
└──────┬──────┘
       │
   ┌───┴────┬──────────┬────────┐
   │        │          │        │
┌──▼──┐ ┌──▼──┐ ┌────▼────┐ ┌──▼──┐
│ Web │ │ GPT-4│ │Speechma-│ │Audio│
│Scra-│ │(OpenAI)│ │ tics TTS│ │Proc.│
│ per │ │      │ │         │ │     │
└─────┘ └──────┘ └─────────┘ └─────┘
```

## Prerequisites

- Python 3.8+
- OpenAI API key
- Speechmatics API key
- ffmpeg (for audio processing)

### Install ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

## Setup

### 1. Clone or Navigate to Project Directory

```bash
cd "TTS Project 1"
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-...your_openai_key_here
SPEECHMATICS_API_KEY=your_speechmatics_key_here
FLASK_ENV=development
FLASK_PORT=5000
```

### 5. Verify Installation

```bash
python app.py
```

You should see:
```
============================================================
Podcast Generator API
============================================================
Server starting on http://localhost:5000
Health check: http://localhost:5000/api/health
============================================================
```

## Usage

### Starting the Server

```bash
cd backend
source ../venv/bin/activate  # If not already activated
python app.py
```

### Using the Web Interface

1. Open your browser to `http://localhost:5000`
2. Paste a news article or blog URL
3. Click "Generate Podcast"
4. Wait for processing (usually 2-5 minutes)
5. Play, pause, seek, and download your podcast!

### API Endpoints

**Generate Podcast**
```bash
POST /api/generate
Content-Type: application/json

{
  "url": "https://example.com/article"
}

Response:
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Job created"
}
```

**Check Status**
```bash
GET /api/status/{job_id}

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 75,
  "message": "Combining audio segments...",
  "metadata": {...}
}
```

**Get Audio**
```bash
GET /api/audio/{job_id}

Returns: WAV audio file
```

## Project Structure

```
TTS Project 1/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   ├── .env                  # Your API keys (not in git)
│   ├── services/
│   │   ├── scraper.py        # URL content extraction
│   │   ├── llm.py            # OpenAI dialogue generation
│   │   ├── tts.py            # Speechmatics TTS integration
│   │   └── audio.py          # Audio segment combining
│   └── utils/
│       └── config.py         # Configuration loader
├── frontend/
│   ├── index.html            # Main UI
│   ├── styles.css            # Styling
│   └── app.js                # API calls & player logic
├── output/                   # Generated audio files
└── README.md                 # This file
```

## How It Works

1. **URL Scraping**: BeautifulSoup extracts the article title, author, and main content
2. **Script Generation**: GPT-4 transforms the article into a conversational dialogue between Sarah and Theo
3. **Speech Synthesis**: Speechmatics TTS generates audio for each dialogue segment using parallel processing
4. **Audio Combining**: Pydub combines all segments with appropriate pauses
5. **Delivery**: Flask serves the audio file to the web player

## Example Workflow

```
User Input: https://techcrunch.com/2024/01/15/ai-breakthrough
                            ↓
            [Web Scraper extracts content]
                            ↓
[GPT-4 generates 2-person dialogue]
        "SARAH: Hey Theo, have you heard about..."
        "THEO: Yes! It's really fascinating because..."
                            ↓
  [Speechmatics generates audio for each line]
        Sarah: segment_001_sarah.wav
        Theo:  segment_002_theo.wav
        Sarah: segment_003_sarah.wav
        ...
                            ↓
        [Combine all segments → podcast.wav]
                            ↓
            [Serve to web player]
```

## Customization

### Adjusting Podcast Duration

Edit `backend/services/llm.py`:

```python
# Change target_duration (in minutes)
dialogue = script_generator.generate_podcast_script(article, target_duration=8)
```

### Changing Pause Duration Between Speakers

Edit `backend/app.py`:

```python
# Change pause_duration (in milliseconds)
audio_processor = AudioProcessor(pause_duration=700)
```

### Modifying Voice Characteristics

Currently using Sarah and Theo. To add more voices, update:
- `backend/utils/config.py` - Add new voice URLs
- `backend/services/llm.py` - Update speaker assignments

## Troubleshooting

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**"Failed to fetch URL" errors**
- Some websites block automated scraping
- Try a different article URL
- Check if the website requires authentication

**"Audio generation failed"**
- Verify your Speechmatics API key is correct
- Check your API quota/limits
- Ensure you have internet connectivity

**"OpenAI API error"**
- Verify your OpenAI API key is correct
- Check your API quota/billing
- Ensure you have access to GPT-4

**Audio processing errors**
- Ensure ffmpeg is installed: `ffmpeg -version`
- Check file permissions in the `output` directory

## Performance

- **Average Generation Time**: 2-5 minutes for a 5-minute podcast
- **Parallel Processing**: TTS requests run concurrently for faster generation
- **Memory Usage**: ~200-500 MB depending on article length

## Limitations

- Currently supports only English articles
- Best results with well-structured articles (news sites, blogs)
- May struggle with highly technical content
- Limited to articles under ~8000 characters

## Future Enhancements

- [ ] Support for multiple languages
- [ ] Custom voice selection
- [ ] Background music and sound effects
- [ ] Transcript display with highlighting
- [ ] User authentication and history
- [ ] Queue system for multiple requests
- [ ] Mobile app
- [ ] Podcast RSS feed generation

## License

MIT License - Feel free to use and modify as needed.

## Credits

- **OpenAI GPT-4**: Dialogue generation
- **Speechmatics TTS**: Voice synthesis
- **Flask**: Backend framework
- **BeautifulSoup**: Web scraping

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review API documentation:
   - [OpenAI API Docs](https://platform.openai.com/docs)
   - [Speechmatics TTS Docs](https://docs.speechmatics.com/text-to-speech/quickstart)
3. Open an issue in the project repository

---

Built with NotebookLM inspiration
