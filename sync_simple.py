#!/usr/bin/env python3
"""
Pure synchronous wrappers without asyncio
To completely avoid asyncio conflicts on macOS
"""

import sys
import os
import logging
import tempfile
import io

from config import config
import openai
from openai import OpenAI
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

class PureSyncSTT:
    """Pure synchronous STT using OpenAI directly"""
    
    def __init__(self):
        config.validate()
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.STT_MODEL
        logger.info(f"PureSyncSTT initialized with model: {self.model}")
    
    def transcribe_audio(self, audio_data, language="vi"):
        """Pure synchronous transcription"""
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
            
            # Convert audio to bytes
            audio_bytes = self.audio_array_to_bytes(audio_data, config.SAMPLE_RATE)
            
            # Create a file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"  # Required for the API
            
            # Call Whisper API synchronously
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="text",
                prompt="Đây là đoạn audio tiếng Việt."  # Vietnamese prompt
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

class PureSyncLLM:
    """Pure synchronous LLM using OpenAI directly"""
    
    def __init__(self):
        config.validate()
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL
        self.conversation_history = []
        self.system_prompt = self._get_system_prompt()
        logger.info(f"PureSyncLLM initialized with model: {self.model}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Vietnamese AI assistant"""
        return """Bạn là một trợ lý AI thông minh và thân thiện, có thể nói chuyện bằng tiếng Việt một cách tự nhiên. 
        
Hãy tuân thủ các nguyên tắc sau:
1. Luôn trả lời bằng tiếng Việt
2. Giữ câu trả lời ngắn gọn, súc tích (tối đa 2-3 câu)
3. Sử dụng ngôn ngữ thân thiện, gần gũi
4. Tránh sử dụng các từ khó hiểu hoặc thuật ngữ phức tạp
5. Nếu không hiểu câu hỏi, hãy lịch sự yêu cầu người dùng nói rõ hơn
6. Luôn giữ thái độ tích cực và hữu ích

Hãy trả lời một cách tự nhiên như đang nói chuyện trực tiếp với người dùng."""
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only last 10 messages to avoid token limit
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def generate_response(self, user_input):
        """Pure synchronous response generation"""
        try:
            # Add user input to history
            self.add_to_history("user", user_input)
            
            # Prepare messages for API
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history)
            
            # Call GPT API synchronously
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=150,  # Keep responses short for voice chat
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Extract response text
            if response.choices and len(response.choices) > 0:
                ai_response = response.choices[0].message.content.strip()
                
                if ai_response:
                    # Add AI response to history
                    self.add_to_history("assistant", ai_response)
                    logger.info(f"✅ LLM Success: '{ai_response}'")
                    return ai_response
                else:
                    logger.warning("⚠️ Empty response from LLM")
                    return None
            else:
                logger.warning("⚠️ No choices in LLM response")
                return None
                
        except Exception as e:
            logger.error(f"❌ LLM Error: {e}")
            return None

class PureSyncTTS:
    """Pure synchronous TTS using gTTS (simpler approach)"""
    
    def __init__(self):
        self.is_initialized = False
        self.sample_rate = 22050  # gTTS default
        logger.info("PureSyncTTS initialized")
    
    def initialize(self):
        """Initialize TTS"""
        try:
            # Try to import gTTS
            from gtts import gTTS
            self.gtts_available = True
            self.is_initialized = True
            logger.info("✅ PureSyncTTS ready (using gTTS)")
            return True
        except ImportError:
            logger.error("❌ gTTS not available")
            return False
    
    def synthesize(self, text):
        """Pure synchronous speech synthesis with optimizations"""
        try:
            if not self.is_initialized:
                logger.warning("PureSyncTTS not initialized")
                return None
            
            from gtts import gTTS
            from pydub import AudioSegment
            import tempfile
            
            # Limit text length to avoid timeout
            if len(text) > 200:
                text = text[:200] + "..."
                logger.warning("⚠️ Text truncated to 200 chars for performance")
            
            logger.info(f"🔊 TTS generating speech for: '{text[:50]}...' ({len(text)} chars)")
            
            # Create gTTS object with optimizations
            tts = gTTS(text=text, lang='vi', slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Generate speech with threading timeout (signal doesn't work in threads)
                import threading
                import time
                
                success = [False]
                error = [None]
                
                def tts_thread():
                    try:
                        tts.save(temp_path)
                        success[0] = True
                    except Exception as e:
                        error[0] = e
                
                # Start TTS in thread with timeout
                thread = threading.Thread(target=tts_thread, daemon=True)
                thread.start()
                thread.join(timeout=5.0)  # 5 second timeout
                
                if not success[0]:
                    if error[0]:
                        raise error[0]
                    else:
                        raise TimeoutError("TTS generation timeout")
                
                # Quick conversion
                audio_segment = AudioSegment.from_mp3(temp_path)
                
                # Optimize for 16kHz mono
                if audio_segment.frame_rate != 16000:
                    audio_segment = audio_segment.set_frame_rate(16000)
                if audio_segment.channels != 1:
                    audio_segment = audio_segment.set_channels(1)
                
                # Convert to numpy array (faster method)
                audio_data = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
                
                # Quick normalize
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data / max_val * 0.9
                
                self.sample_rate = 16000
                
                duration = len(audio_data) / self.sample_rate
                logger.info(f"✅ TTS Success: duration={duration:.2f}s")
                return audio_data.astype(np.float32)
                
            except TimeoutError:
                logger.error("❌ TTS timeout - generating fallback beep")
                # Fallback: simple beep
                sample_rate = 16000
                duration = 0.5
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
                self.sample_rate = sample_rate
                return audio_data.astype(np.float32)
                
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ TTS Error: {e}")
            # Final fallback
            try:
                sample_rate = 16000
                duration = 0.3
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_data = 0.2 * np.sin(2 * np.pi * 800 * t)  # Error tone
                self.sample_rate = sample_rate
                logger.warning("🔔 TTS fallback: Generated error tone")
                return audio_data.astype(np.float32)
            except:
                return None 