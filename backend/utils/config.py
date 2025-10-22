import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the application"""

    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SPEECHMATICS_API_KEY = os.getenv('SPEECHMATICS_API_KEY')

    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

    # Speechmatics TTS Configuration
    SPEECHMATICS_BASE_URL = "https://preview.tts.speechmatics.com/generate"
    SARAH_VOICE_URL = f"{SPEECHMATICS_BASE_URL}/sarah"
    THEO_VOICE_URL = f"{SPEECHMATICS_BASE_URL}/theo"

    # Audio Configuration
    SAMPLE_RATE = 16000
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output')

    # OpenAI Configuration
    OPENAI_MODEL = "gpt-4o"

    @staticmethod
    def validate():
        """Validate that required configuration is present"""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        if not Config.SPEECHMATICS_API_KEY:
            raise ValueError("SPEECHMATICS_API_KEY is not set in environment variables")
        return True
