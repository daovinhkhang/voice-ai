import asyncio
import logging
import signal
import sys
from typing import Optional
import numpy as np

from src.stt.whisper_stt import WhisperSTT
from src.llm.gpt_llm import GPTLLM
from src.tts.vietnamese_tts import VietnameseTTS
from src.audio.audio_handler import AudioHandler
from src.utils.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VietnameseVoiceChat:
    """Main Vietnamese AI Voice Chat System"""
    
    def __init__(self):
        """Initialize the voice chat system"""
        self.stt = WhisperSTT()
        self.llm = GPTLLM()
        self.tts = VietnameseTTS()
        self.audio_handler = AudioHandler()
        
        self.is_running = False
        self.conversation_count = 0
        
        logger.info("Vietnamese Voice Chat System initialized")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing TTS model...")
            await self.tts.initialize()
            
            logger.info("Checking audio devices...")
            self.audio_handler.get_audio_devices()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    async def process_voice_input(self) -> Optional[str]:
        """Record and process voice input"""
        try:
            logger.info("🎤 Listening... (speak now)")
            
            # Record audio with VAD
            audio_data = await self.audio_handler.record_with_vad(
                max_duration=config.MAX_AUDIO_LENGTH
            )
            
            if audio_data is None:
                logger.warning("No audio recorded")
                return None
            
            logger.info("🔄 Processing speech...")
            
            # Convert speech to text
            text = await self.stt.transcribe_audio(audio_data)
            
            if text:
                logger.info(f"👤 User: {text}")
                return text
            else:
                logger.warning("Could not transcribe audio")
                return None
                
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return None
    
    async def generate_response(self, user_input: str) -> Optional[str]:
        """Generate AI response"""
        try:
            logger.info("🤖 Thinking...")
            
            # Generate response using LLM
            response = await self.llm.generate_response(user_input)
            
            if response:
                logger.info(f"🤖 AI: {response}")
                return response
            else:
                logger.warning("Could not generate response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    async def speak_response(self, text: str) -> bool:
        """Convert text to speech and play"""
        try:
            logger.info("🔊 Speaking...")
            
            # Generate speech
            audio_data = await self.tts.synthesize(text)
            
            if audio_data is not None:
                # Play audio
                success = await self.audio_handler.play_audio_async(
                    audio_data, self.tts.sample_rate
                )
                
                if success:
                    logger.info("✅ Speech completed")
                    return True
                else:
                    logger.error("Failed to play audio")
                    return False
            else:
                logger.error("Failed to synthesize speech")
                return False
                
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
            return False
    
    async def conversation_loop(self):
        """Main conversation loop"""
        try:
            while self.is_running:
                self.conversation_count += 1
                logger.info(f"\n--- Conversation {self.conversation_count} ---")
                
                # Step 1: Record and transcribe user input
                user_input = await self.process_voice_input()
                
                if user_input is None:
                    logger.info("No input detected, continuing...")
                    await asyncio.sleep(1)
                    continue
                
                # Check for exit commands
                if user_input.lower().strip() in ['thoát', 'exit', 'quit', 'bye', 'tạm biệt']:
                    logger.info("Exit command detected")
                    break
                
                # Step 2: Generate AI response
                ai_response = await self.generate_response(user_input)
                
                if ai_response is None:
                    logger.warning("Could not generate response, continuing...")
                    continue
                
                # Step 3: Convert response to speech and play
                speech_success = await self.speak_response(ai_response)
                
                if not speech_success:
                    logger.warning("Could not speak response")
                
                # Small delay before next iteration
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            logger.info("Conversation interrupted by user")
        except Exception as e:
            logger.error(f"Error in conversation loop: {e}")
    
    async def run(self):
        """Run the voice chat system"""
        try:
            logger.info("🚀 Starting Vietnamese AI Voice Chat System")
            
            # Initialize components
            if not await self.initialize():
                logger.error("Failed to initialize system")
                return
            
            self.is_running = True
            
            # Print instructions
            print("\n" + "="*60)
            print("🇻🇳 VIETNAMESE AI VOICE CHAT SYSTEM")
            print("="*60)
            print("📋 Instructions:")
            print("   • Speak in Vietnamese after you see '🎤 Listening...'")
            print("   • Say 'thoát' or 'exit' to quit")
            print("   • Press Ctrl+C to force quit")
            print("="*60)
            print()
            
            # Start conversation loop
            await self.conversation_loop()
            
        except Exception as e:
            logger.error(f"Error running voice chat system: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("🧹 Cleaning up...")
            self.is_running = False
            self.audio_handler.cleanup()
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main function"""
    voice_chat = VietnameseVoiceChat()
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        logger.info("Received interrupt signal")
        voice_chat.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await voice_chat.run()
    except KeyboardInterrupt:
        logger.info("Program interrupted")
    finally:
        await voice_chat.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
