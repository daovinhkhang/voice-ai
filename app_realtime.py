#!/usr/bin/env python3
"""
Real-time Vietnamese Voice Chat System with Continuous Mode
Using pure synchronous components - NO ASYNCIO
"""

import logging
import tempfile
import os
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import numpy as np
import soundfile as sf
from threading import Thread
import uuid

# Import our pure sync components
from sync_simple import PureSyncSTT, PureSyncLLM, PureSyncTTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global components
stt = None
llm = None
tts = None
is_initialized = False

def initialize_components():
    """Initialize all AI components synchronously"""
    global stt, llm, tts, is_initialized
    
    try:
        logger.info("🔄 Initializing real-time voice chat system...")
        
        # Initialize components
        stt = PureSyncSTT()
        llm = PureSyncLLM()
        tts = PureSyncTTS()
        
        # Initialize TTS
        logger.info("🔄 Initializing TTS...")
        tts_success = tts.initialize()
        
        is_initialized = True
        logger.info("✅ Real-time voice chat system ready!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing components: {e}")
        return False

def convert_audio_to_numpy(audio_file, target_sample_rate=16000):
    """Convert uploaded audio file to numpy array (supports WebM, MP4, WAV)"""
    try:
        # Get file extension from filename
        filename = audio_file.filename or 'audio.webm'
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Create temporary files
        input_temp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        try:
            # Save uploaded file
            audio_file.save(input_temp.name)
            input_temp.close()
            output_temp.close()
            
            # Convert using ffmpeg if not WAV
            if file_ext not in ['.wav']:
                import subprocess
                logger.info(f"🔄 Converting {file_ext} to WAV using ffmpeg...")
                
                # Use ffmpeg to convert to WAV
                cmd = [
                    'ffmpeg', '-i', input_temp.name,
                    '-acodec', 'pcm_s16le',
                    '-ar', str(target_sample_rate),
                    '-ac', '1',  # mono
                    '-y',  # overwrite
                    output_temp.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"ffmpeg failed, trying pydub fallback: {result.stderr}")
                    # Fallback to pydub
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(input_temp.name)
                    audio = audio.set_frame_rate(target_sample_rate).set_channels(1)
                    audio.export(output_temp.name, format="wav")
            else:
                # Already WAV, just copy
                import shutil
                shutil.copy2(input_temp.name, output_temp.name)
            
            # Read the converted WAV file
            audio_data, sample_rate = sf.read(output_temp.name)
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data)) * 0.9
            
            logger.info(f"✅ Audio converted: {len(audio_data)} samples, {sample_rate}Hz")
            return audio_data, sample_rate
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(input_temp.name)
                os.unlink(output_temp.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Error converting audio: {e}")
        return None, None

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if is_initialized and stt and llm and tts:
            return jsonify({
                'status': 'healthy',
                'components': {
                    'stt': 'ready',
                    'llm': 'ready', 
                    'tts': 'ready'
                }
            })
        else:
            return jsonify({
                'status': 'initializing',
                'message': 'Components are still initializing'
            }), 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/voice-chat', methods=['POST'])
def voice_chat():
    """Process voice input and return AI response with TTS"""
    try:
        if not is_initialized:
            return jsonify({'status': 'error', 'error': 'System not initialized'}), 503
        
        # Debug: Log request details
        logger.info(f"📥 Received voice chat request")
        logger.info(f"📁 Request files: {list(request.files.keys())}")
        logger.info(f"📋 Request form: {list(request.form.keys())}")
        
        # Check if audio file was uploaded
        if 'audio' not in request.files:
            logger.error("❌ No 'audio' key in request.files")
            return jsonify({'status': 'error', 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        logger.info(f"📄 Audio file: {audio_file.filename}, size: {audio_file.content_length if hasattr(audio_file, 'content_length') else 'unknown'}")
        
        if audio_file.filename == '':
            logger.error("❌ Audio file has empty filename")
            return jsonify({'status': 'error', 'error': 'No audio file selected'}), 400
        
        logger.info(f"🎤 Processing audio file: {audio_file.filename}")
        
        # Convert audio to numpy array
        logger.info(f"🔄 Converting audio file to numpy array...")
        audio_data, sample_rate = convert_audio_to_numpy(audio_file)
        if audio_data is None:
            logger.error("❌ Failed to convert audio to numpy array")
            return jsonify({'status': 'error', 'error': 'Failed to process audio file'}), 400
        
        logger.info(f"✅ Audio converted: {len(audio_data)} samples, {sample_rate}Hz")
        
        # STT: Convert speech to text
        logger.info("🔄 Converting speech to text...")
        user_text = stt.transcribe_audio(audio_data)
        
        if not user_text:
            return jsonify({'status': 'error', 'error': 'Could not transcribe speech'}), 400
        
        logger.info(f"✅ STT Result: '{user_text}'")
        
        # LLM: Generate AI response
        logger.info("🤖 Generating AI response...")
        ai_response = llm.generate_response(user_text)
        
        if not ai_response:
            return jsonify({'status': 'error', 'error': 'Could not generate response'}), 400
        
        logger.info(f"✅ LLM Response: '{ai_response}'")
        
        # TTS: Generate speech from AI response
        logger.info("🔊 Generating speech...")
        audio_data_tts = tts.synthesize(ai_response)
        
        if audio_data_tts is None:
            return jsonify({'status': 'error', 'error': 'Could not generate speech'}), 400
        
        # Save audio file
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(tempfile.gettempdir(), f"{audio_id}.wav")
        
        sf.write(audio_path, audio_data_tts, tts.sample_rate)
        logger.info(f"✅ TTS completed: /api/audio/{audio_id}")
        
        return jsonify({
            'status': 'success',
            'user_text': user_text,
            'ai_response': ai_response,
            'audio_url': f'/api/audio/{audio_id}'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in voice chat: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def text_chat():
    """Process text input and return AI response"""
    try:
        if not is_initialized:
            return jsonify({'status': 'error', 'error': 'System not initialized'}), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'status': 'error', 'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'status': 'error', 'error': 'Empty message'}), 400
        
        logger.info(f"📝 Text chat: '{user_message}'")
        
        # Generate AI response
        ai_response = llm.generate_response(user_message)
        
        if not ai_response:
            return jsonify({'status': 'error', 'error': 'Could not generate response'}), 400
        
        logger.info(f"✅ AI Response: '{ai_response}'")
        
        return jsonify({
            'status': 'success',
            'response': ai_response
        })
        
    except Exception as e:
        logger.error(f"❌ Error in text chat: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    try:
        if not is_initialized:
            return jsonify({'status': 'error', 'error': 'System not initialized'}), 503
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'status': 'error', 'error': 'No text provided'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'status': 'error', 'error': 'Empty text'}), 400
        
        logger.info(f"🔊 TTS request: '{text[:50]}...'")
        
        # Generate speech
        audio_data = tts.synthesize(text)
        
        if audio_data is None:
            return jsonify({'status': 'error', 'error': 'Could not generate speech'}), 400
        
        # Save audio file
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(tempfile.gettempdir(), f"{audio_id}.wav")
        
        sf.write(audio_path, audio_data, tts.sample_rate)
        logger.info(f"✅ TTS completed: /api/audio/{audio_id}")
        
        return jsonify({
            'status': 'success',
            'audio_url': f'/api/audio/{audio_id}'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in TTS: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/audio/<audio_id>')
def serve_audio(audio_id):
    """Serve audio files"""
    try:
        audio_path = os.path.join(tempfile.gettempdir(), f"{audio_id}.wav")
        
        if not os.path.exists(audio_path):
            return jsonify({'status': 'error', 'error': 'Audio file not found'}), 404
        
        return send_file(
            audio_path,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=f"{audio_id}.wav"
        )
        
    except Exception as e:
        logger.error(f"❌ Error serving audio: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

def main():
    """Main function to run the Flask app"""
    logger.info("🚀 Starting Real-time Vietnamese Voice Chat System")
    
    def init_components():
        """Initialize components in background"""
        initialize_components()
    
    # Initialize components in background
    init_thread = Thread(target=init_components)
    init_thread.daemon = True
    init_thread.start()
    
    # Start Flask app
    logger.info("🌐 Server starting on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == "__main__":
    main() 