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
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not cls.HUGGINGFACE_TOKEN:
            raise ValueError("HUGGINGFACE_TOKEN is required")
        return True

# Global config instance
config = Config()
