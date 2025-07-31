import asyncio
import logging
import torch
import numpy as np
from typing import Optional, Tuple, Union
import tempfile
import os
import sys
import soundfile as sf
from src.utils.config import config

# Compatibility fix for Python 3.9
if sys.version_info < (3, 10):
    from typing import Union
    def Optional_fix(x):
        return Union[x, type(None)]
else:
    def Optional_fix(x):
        return Optional[x]

logger = logging.getLogger(__name__)

class VietnameseTTS:
    """Text-to-Speech using zalopay/vietnamese-tts model"""

    def __init__(self):
        """Initialize Vietnamese TTS model"""
        self.model = None
        self.vocoder = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.sample_rate = 24000  # Default sample rate for F5-TTS
        self.is_initialized = False
        logger.info(f"Initializing VietnameseTTS on device: {self.device}")

    async def initialize(self):
        """Initialize the TTS model and vocoder"""
        try:
            if self.is_initialized:
                return

            # Try to import and initialize F5-TTS
            try:
                from huggingface_hub import login
                from cached_path import cached_path

                # Login to Hugging Face
                if config.HUGGINGFACE_TOKEN:
                    login(token=config.HUGGINGFACE_TOKEN)
                    logger.info("Logged in to Hugging Face")

                # Import F5-TTS modules with error handling
                from f5_tts.infer.utils_infer import (
                    preprocess_ref_audio_text,
                    load_vocoder,
                    load_model,
                    infer_process,
                )
                from f5_tts.model import DiT

                # Load vocoder
                logger.info("Loading vocoder...")
                self.vocoder = load_vocoder()

                # Load the Vietnamese TTS model
                logger.info("Loading Vietnamese TTS model...")
                model_config = dict(
                    dim=1024,
                    depth=22,
                    heads=16,
                    ff_mult=2,
                    text_dim=512,
                    conv_layers=4
                )

                # Download model checkpoint
                model_path = str(cached_path("hf://zalopay/vietnamese-tts/model_960000.pt"))
                vocab_path = str(cached_path("hf://zalopay/vietnamese-tts/vocab.txt"))

                self.model = load_model(
                    DiT,
                    model_config,
                    ckpt_path=model_path,
                    mel_spec_type="vocos",
                    vocab_file=vocab_path,
                )

                # Store inference utilities
                self.preprocess_ref_audio_text = preprocess_ref_audio_text
                self.infer_process = infer_process

                self.is_initialized = True
                self.use_fallback = False
                logger.info("Vietnamese TTS model initialized successfully")
                return

            except Exception as model_error:
                logger.error(f"Error loading F5-TTS model: {model_error}")
                logger.info("Falling back to system TTS...")

        except Exception as e:
            logger.error(f"Error in TTS initialization: {e}")

        # Fallback to simple TTS
        await self._initialize_fallback()

    async def _initialize_fallback(self):
        """Initialize fallback TTS system"""
        try:
            # Try gTTS first (Google Text-to-Speech)
            try:
                from gtts import gTTS
                self.gtts_available = True
                self.use_fallback = True
                logger.info("Using Google TTS (gTTS) as fallback")
                self.is_initialized = True
                return
            except ImportError:
                logger.warning("gTTS not available")

            # Try system TTS (macOS)
            try:
                import subprocess
                subprocess.run(['say', '--version'], capture_output=True, check=True)
                self.tts_available = True
                self.use_fallback = True
                logger.info("Using system TTS as fallback")
                self.is_initialized = True
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("System TTS not available")

            # Final fallback - placeholder
            self.tts_available = False
            self.gtts_available = False
            self.use_fallback = True
            logger.warning("No TTS available, will use placeholder")

        except Exception as e:
            logger.error(f"Error in fallback initialization: {e}")
            self.tts_available = False
            self.gtts_available = False
            self.use_fallback = True

        self.is_initialized = True

    def create_default_reference(self) -> Tuple[str, str]:
        """
        Create a default reference audio and text for voice cloning
        Returns a tuple of (ref_audio_path, ref_text)
        """
        ref_text = "Xin chào, tôi là trợ lý AI của bạn."

        # Create a temporary silent audio file as reference
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

        # Create 1 second of silence at 24kHz
        silence = np.zeros(int(self.sample_rate * 1.0), dtype=np.float32)
        sf.write(temp_audio.name, silence, self.sample_rate)

        return temp_audio.name, ref_text

    async def synthesize(
        self,
        text: str,
        ref_audio_path: Optional[str] = None,
        ref_text: Optional[str] = None,
        speed: float = 1.0
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            ref_audio_path: Path to reference audio for voice cloning
            ref_text: Reference text corresponding to reference audio
            speed: Speech speed multiplier

        Returns:
            Audio array or None if failed
        """
        try:
            if not self.is_initialized:
                await self.initialize()

            # Use fallback if F5-TTS model failed to load
            if hasattr(self, 'use_fallback') and self.use_fallback:
                return await self._synthesize_fallback(text, speed)

            # Use default reference if not provided
            if ref_audio_path is None or ref_text is None:
                ref_audio_path, ref_text = self.create_default_reference()

            # Preprocess reference audio and text
            ref_audio, ref_text_processed = self.preprocess_ref_audio_text(
                ref_audio_path, ref_text
            )

            logger.info(f"Synthesizing: '{text}' with reference: '{ref_text_processed}'")

            # Generate speech
            final_wave, final_sample_rate, combined_spectrogram = await asyncio.to_thread(
                self.infer_process,
                ref_audio,
                ref_text_processed,
                text,
                self.model,
                self.vocoder,
                cross_fade_duration=0.15,
                nfe_step=32,
                speed=speed,
            )

            # Clean up temporary reference file if we created it
            if ref_audio_path and ref_audio_path.startswith(tempfile.gettempdir()):
                try:
                    os.unlink(ref_audio_path)
                except:
                    pass

            logger.info(f"Successfully synthesized audio with sample rate: {final_sample_rate}")
            return final_wave

        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
            return await self._synthesize_fallback(text, speed)

    async def _synthesize_fallback(self, text: str, speed: float = 1.0) -> Optional[np.ndarray]:
        """Fallback synthesis using gTTS, system TTS or placeholder"""
        try:
            # Try gTTS first (Google Text-to-Speech)
            if hasattr(self, 'gtts_available') and self.gtts_available:
                try:
                    from gtts import gTTS
                    from pydub import AudioSegment
                    from pydub.playback import play
                    import io

                    logger.info(f"Using gTTS to synthesize: '{text}'")

                    # Create gTTS object
                    tts = gTTS(text=text, lang='vi', slow=False)

                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                        temp_path = temp_file.name

                    try:
                        # Generate speech
                        await asyncio.to_thread(tts.save, temp_path)

                        # Convert MP3 to WAV and load
                        audio_segment = AudioSegment.from_mp3(temp_path)

                        # Convert to numpy array
                        audio_data = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)

                        # Normalize
                        if np.max(np.abs(audio_data)) > 0:
                            audio_data = audio_data / np.max(np.abs(audio_data))

                        # Convert to mono if stereo
                        if audio_segment.channels == 2:
                            audio_data = audio_data.reshape((-1, 2))
                            audio_data = np.mean(audio_data, axis=1)

                        # Resample to target sample rate if needed
                        if audio_segment.frame_rate != self.sample_rate:
                            import librosa
                            audio_data = librosa.resample(
                                audio_data,
                                orig_sr=audio_segment.frame_rate,
                                target_sr=self.sample_rate
                            )

                        logger.info(f"Successfully synthesized with gTTS - Duration: {len(audio_data) / self.sample_rate:.2f}s")
                        return audio_data.astype(np.float32)

                    finally:
                        try:
                            os.unlink(temp_path)
                        except:
                            pass

                except Exception as gtts_error:
                    logger.error(f"Error with gTTS: {gtts_error}")

            # Try system TTS (macOS)
            if hasattr(self, 'tts_available') and self.tts_available:
                try:
                    import subprocess
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_path = temp_file.name

                    try:
                        cmd = ['say', '-o', temp_path, '--data-format=LEF32@22050', text]
                        await asyncio.to_thread(
                            subprocess.run, cmd, capture_output=True, check=True
                        )

                        audio_data, sample_rate = sf.read(temp_path)
                        if audio_data.dtype != np.float32:
                            audio_data = audio_data.astype(np.float32)

                        if len(audio_data.shape) > 1:
                            audio_data = np.mean(audio_data, axis=1)

                        return audio_data
                    finally:
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                except Exception as sys_tts_error:
                    logger.error(f"Error with system TTS: {sys_tts_error}")

            # Final fallback - placeholder audio
            logger.warning("Creating placeholder audio")
            duration = len(text) * 0.1
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            audio = 0.1 * np.sin(2 * np.pi * 440 * t)
            return audio.astype(np.float32)

        except Exception as e:
            logger.error(f"Error in fallback synthesis: {e}")
            # Final fallback - placeholder audio
            duration = len(text) * 0.1
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            audio = 0.1 * np.sin(2 * np.pi * 440 * t)
            return audio.astype(np.float32)

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        ref_audio_path: Optional[str] = None,
        ref_text: Optional[str] = None,
        speed: float = 1.0
    ) -> bool:
        """
        Synthesize speech and save to file

        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
            ref_audio_path: Path to reference audio for voice cloning
            ref_text: Reference text corresponding to reference audio
            speed: Speech speed multiplier

        Returns:
            True if successful, False otherwise
        """
        try:
            audio_array = await self.synthesize(text, ref_audio_path, ref_text, speed)

            if audio_array is not None:
                sf.write(output_path, audio_array, self.sample_rate)
                logger.info(f"Audio saved to: {output_path}")
                return True
            else:
                logger.error("Failed to synthesize audio")
                return False

        except Exception as e:
            logger.error(f"Error saving audio to file: {e}")
            return False
