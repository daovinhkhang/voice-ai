import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Vietnamese AI Voice Chat System"""
    
    # OpenAI API settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    STT_MODEL = os.getenv('STT_MODEL', 'whisper-1')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')

    # Hugging Face settings
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    
    # TTS Model settings
    TTS_MODEL = os.getenv('TTS_MODEL', 'zalopay/vietnamese-tts')
    
    # Audio settings
    SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 16000))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1024))
    CHANNELS = int(os.getenv('CHANNELS', 1))
    
    # Performance settings
    MAX_AUDIO_LENGTH = int(os.getenv('MAX_AUDIO_LENGTH', 30))
    RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT', 10))
    
    # Web Server settings
    PORT = int(os.getenv('PORT', 8080))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Email settings (for Booking Agent) - Default Gmail settings
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'daovinhkhang0834@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'uftt xnbv wphb oqsh')
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///booking_system.db')
    
    # File storage settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        return True

# Global config instance
config = Config() 