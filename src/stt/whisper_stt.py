import asyncio
import io
import logging
from typing import Optional
import openai
from openai import OpenAI
import numpy as np
import soundfile as sf
from src.utils.config import config

logger = logging.getLogger(__name__)

class WhisperSTT:
    """Speech-to-Text using OpenAI Whisper-1 API for Vietnamese"""
    
    def __init__(self):
        """Initialize Whisper STT client"""
        config.validate()
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.STT_MODEL
        logger.info(f"Initialized WhisperSTT with model: {self.model}")
    
    def audio_array_to_bytes(self, audio_array: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Convert numpy audio array to bytes format for API"""
        try:
            # Ensure audio is in the right format
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)
            
            # Remove DC offset
            audio_array = audio_array - np.mean(audio_array)
            
            # Normalize audio to prevent clipping
            max_val = np.max(np.abs(audio_array))
            if max_val > 0:
                # Normalize to 0.9 to leave some headroom
                audio_array = audio_array * (0.9 / max_val)
            
            # Apply a simple high-pass filter to remove very low frequencies
            if len(audio_array) > 100:
                # Simple first-order high-pass filter
                alpha = 0.95
                for i in range(1, len(audio_array)):
                    audio_array[i] = alpha * (audio_array[i-1] + audio_array[i] - audio_array[i-1])
            
            # Create bytes buffer with higher quality
            buffer = io.BytesIO()
            sf.write(buffer, audio_array, sample_rate, format='WAV', subtype='PCM_16')
            buffer.seek(0)
            
            logger.debug(f"Audio converted: {len(audio_array)} samples, {sample_rate}Hz, max_val={max_val:.3f}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting audio array to bytes: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: np.ndarray, language: str = "vi") -> Optional[str]:
        """
        Transcribe audio data to text using Whisper API
        
        Args:
            audio_data: numpy array of audio samples
            language: language code (default: "vi" for Vietnamese)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Validate audio data
            if audio_data is None or len(audio_data) == 0:
                logger.warning("Empty audio data received")
                return None
            
            # Check audio duration (minimum 0.1 seconds)
            duration = len(audio_data) / config.SAMPLE_RATE
            if duration < 0.1:
                logger.warning(f"Audio too short: {duration:.2f}s")
                return None
            
            logger.info(f"Processing audio: duration={duration:.2f}s, samples={len(audio_data)}")
            
            # Convert audio array to bytes
            audio_bytes = self.audio_array_to_bytes(audio_data, config.SAMPLE_RATE)
            
            # Create a file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"  # Required for the API
            
            # Call Whisper API with Vietnamese language specification
            response = await asyncio.to_thread(
                self.client.audio.transcriptions.create,
                model=self.model,
                file=audio_file,
                language=language,
                response_format="text",
                prompt="Đây là đoạn audio tiếng Việt."  # Vietnamese prompt to improve accuracy
            )
            
            # Extract text from response
            if isinstance(response, str):
                text = response.strip()
            else:
                text = response.text.strip() if hasattr(response, 'text') else str(response).strip()
            
            if text and text.lower() not in ['', 'you', 'thank you', 'thanks']:
                logger.info(f"✅ STT Success: '{text}' (duration: {duration:.2f}s)")
                return text
            else:
                logger.warning(f"⚠️ STT returned empty or generic result: '{text}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ STT Error: {e}")
            return None
    
    async def transcribe_file(self, file_path: str, language: str = "vi") -> Optional[str]:
        """
        Transcribe audio file to text
        
        Args:
            file_path: path to audio file
            language: language code (default: "vi" for Vietnamese)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            with open(file_path, "rb") as audio_file:
                response = await asyncio.to_thread(
                    self.client.audio.transcriptions.create,
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
                
                # Extract text from response
                if isinstance(response, str):
                    text = response.strip()
                else:
                    text = response.text.strip() if hasattr(response, 'text') else str(response).strip()
                
                if text:
                    logger.info(f"Transcribed from file: {text}")
                    return text
                else:
                    logger.warning("Empty transcription result from file")
                    return None
                    
        except Exception as e:
            logger.error(f"Error transcribing file {file_path}: {e}")
            return None
