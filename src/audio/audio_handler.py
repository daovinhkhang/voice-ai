import asyncio
import logging
import numpy as np
import sounddevice as sd
import threading
import queue
import time
from typing import Optional, Callable, Any
from src.utils.config import config

logger = logging.getLogger(__name__)

class AudioHandler:
    """Handle real-time audio recording and playback"""
    
    def __init__(self):
        """Initialize audio handler"""
        self.sample_rate = config.SAMPLE_RATE
        self.channels = config.CHANNELS
        self.chunk_size = config.CHUNK_SIZE
        
        # Recording state
        self.is_recording = False
        self.recorded_frames = []
        self.recording_thread = None
        self.audio_queue = queue.Queue()
        
        # Playback state
        self.is_playing = False
        
        # Voice Activity Detection (simple threshold-based)
        self.vad_threshold = 0.01
        self.silence_duration = 1.0  # seconds of silence to stop recording
        self.min_recording_duration = 0.5  # minimum recording duration
        
        logger.info(f"AudioHandler initialized - Sample Rate: {self.sample_rate}, Channels: {self.channels}")
    
    def get_audio_devices(self):
        """Get available audio devices"""
        try:
            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for i, device in enumerate(devices):
                logger.info(f"  {i}: {device['name']} - {device['max_input_channels']} in, {device['max_output_channels']} out")
            return devices
        except Exception as e:
            logger.error(f"Error querying audio devices: {e}")
            return []
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio recording"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        if self.is_recording:
            # Convert to mono if stereo
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata[:, 0]
            
            self.audio_queue.put(audio_data.copy())
    
    def start_recording(self) -> bool:
        """Start recording audio"""
        try:
            if self.is_recording:
                logger.warning("Already recording")
                return False
            
            self.is_recording = True
            self.recorded_frames = []
            
            # Clear the queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Start recording stream
            self.recording_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self.audio_callback,
                blocksize=self.chunk_size,
                dtype=np.float32
            )
            self.recording_stream.start()
            
            logger.info("Started recording")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
            return False
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return recorded audio"""
        try:
            if not self.is_recording:
                logger.warning("Not currently recording")
                return None
            
            self.is_recording = False
            
            # Stop the recording stream
            if hasattr(self, 'recording_stream'):
                self.recording_stream.stop()
                self.recording_stream.close()
            
            # Collect remaining audio data
            while not self.audio_queue.empty():
                try:
                    frame = self.audio_queue.get_nowait()
                    self.recorded_frames.append(frame)
                except queue.Empty:
                    break
            
            if self.recorded_frames:
                # Concatenate all frames
                audio_data = np.concatenate(self.recorded_frames)
                logger.info(f"Stopped recording - Duration: {len(audio_data) / self.sample_rate:.2f}s")
                return audio_data
            else:
                logger.warning("No audio data recorded")
                return None
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None
    
    async def record_with_vad(self, max_duration: float = 30.0) -> Optional[np.ndarray]:
        """
        Record audio with Voice Activity Detection
        
        Args:
            max_duration: Maximum recording duration in seconds
            
        Returns:
            Recorded audio array or None
        """
        try:
            if not self.start_recording():
                return None
            
            start_time = time.time()
            last_voice_time = start_time
            recording_started = False
            
            while self.is_recording:
                # Check for timeout
                if time.time() - start_time > max_duration:
                    logger.info("Recording timeout reached")
                    break
                
                # Get audio data from queue
                try:
                    frame = self.audio_queue.get(timeout=0.1)
                    self.recorded_frames.append(frame)
                    
                    # Simple VAD - check if audio level is above threshold
                    audio_level = np.max(np.abs(frame))
                    
                    if audio_level > self.vad_threshold:
                        last_voice_time = time.time()
                        if not recording_started:
                            recording_started = True
                            logger.info("Voice detected, started recording")
                    
                    # Check for silence after voice was detected
                    if recording_started:
                        silence_duration = time.time() - last_voice_time
                        if silence_duration > self.silence_duration:
                            # Check minimum recording duration
                            total_duration = time.time() - start_time
                            if total_duration >= self.min_recording_duration:
                                logger.info("Silence detected, stopping recording")
                                break
                
                except queue.Empty:
                    continue
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
            
            return self.stop_recording()
            
        except Exception as e:
            logger.error(f"Error in VAD recording: {e}")
            self.stop_recording()
            return None
    
    def play_audio(self, audio_data: np.ndarray, sample_rate: Optional[int] = None) -> bool:
        """
        Play audio data
        
        Args:
            audio_data: Audio array to play
            sample_rate: Sample rate (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.is_playing:
                logger.warning("Already playing audio")
                return False
            
            if sample_rate is None:
                sample_rate = self.sample_rate
            
            self.is_playing = True
            
            # Ensure audio is in the right format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Play audio
            sd.play(audio_data, samplerate=sample_rate)
            sd.wait()  # Wait until playback is finished
            
            self.is_playing = False
            logger.info(f"Played audio - Duration: {len(audio_data) / sample_rate:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            self.is_playing = False
            return False
    
    async def play_audio_async(self, audio_data: np.ndarray, sample_rate: Optional[int] = None) -> bool:
        """
        Play audio data asynchronously
        
        Args:
            audio_data: Audio array to play
            sample_rate: Sample rate (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        return await asyncio.to_thread(self.play_audio, audio_data, sample_rate)
    
    def stop_playback(self):
        """Stop current audio playback"""
        try:
            sd.stop()
            self.is_playing = False
            logger.info("Stopped audio playback")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
    
    def cleanup(self):
        """Clean up audio resources"""
        try:
            self.stop_recording()
            self.stop_playback()
            logger.info("Audio handler cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
