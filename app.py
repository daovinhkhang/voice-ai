#!/usr/bin/env python3
"""
Final Flask Web Application for Vietnamese AI Voice Chat System
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
        logger.info("🔄 Initializing pure sync components...")
        
        # Initialize components
        stt = PureSyncSTT()
        llm = PureSyncLLM()
        tts = PureSyncTTS()
        
        # Initialize TTS
        logger.info("🔄 Initializing TTS...")
        tts_success = tts.initialize()
        
        is_initialized = True
        logger.info("✅ All pure sync components ready!")
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
                
                # Read converted WAV file
                audio_data, sample_rate = sf.read(output_temp.name)
            else:
                # Direct read for WAV files
                audio_data, sample_rate = sf.read(input_temp.name)
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Resample if necessary
            if sample_rate != target_sample_rate:
                import librosa
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=target_sample_rate
                )
            
            # Ensure float32 format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            logger.info(f"✅ Audio converted: {len(audio_data)} samples, {target_sample_rate}Hz")
            return audio_data
            
        finally:
            # Clean up temp files
            try:
                os.unlink(input_temp.name)
                os.unlink(output_temp.name)
            except:
                pass
            
    except Exception as e:
        logger.error(f"❌ Error converting audio: {e}")
        return None

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if is_initialized:
        return jsonify({
            'status': 'healthy',
            'message': 'All pure sync components ready',
            'stt': 'ready',
            'llm': 'ready', 
            'tts': 'ready' if tts and tts.is_initialized else 'limited'
        })
    else:
        return jsonify({
            'status': 'initializing',
            'message': 'Components still loading...'
        }), 503

@app.route('/api/voice-chat', methods=['POST'])
def voice_chat():
    """Handle voice chat requests (STT + LLM + TTS)"""
    try:
        if not is_initialized:
            return jsonify({
                'status': 'error',
                'error': 'System not initialized yet'
            }), 503
        
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No audio file selected'
            }), 400
        
        # Convert audio to numpy array
        logger.info(f"🎤 Processing audio file: {audio_file.filename}")
        audio_data = convert_audio_to_numpy(audio_file)
        
        if audio_data is None:
            return jsonify({
                'status': 'error',
                'error': 'Failed to process audio file'
            }), 400
        
        # Step 1: Speech-to-Text
        logger.info("🔄 Converting speech to text...")
        user_text = stt.transcribe_audio(audio_data, language="vi")
        
        if not user_text:
            return jsonify({
                'status': 'error',
                'error': 'Could not transcribe audio. Please speak clearly in Vietnamese.'
            }), 400
        
        logger.info(f"✅ STT Result: '{user_text}'")
        
        # Step 2: Generate AI response
        logger.info("🤖 Generating AI response...")
        ai_response = llm.generate_response(user_text)
        
        if not ai_response:
            return jsonify({
                'status': 'error',
                'error': 'Could not generate AI response'
            }), 500
        
        logger.info(f"✅ LLM Response: '{ai_response}'")
        
        # Step 3: Text-to-Speech
        audio_url = None
        if tts and tts.is_initialized:
            logger.info("🔊 Generating speech...")
            audio_array = tts.synthesize(ai_response)
            
            if audio_array is not None:
                # Save audio to temporary file
                audio_id = str(uuid.uuid4())
                audio_filename = f"response_{audio_id}.wav"
                audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
                
                sf.write(audio_path, audio_array, tts.sample_rate)
                audio_url = f"/api/audio/{audio_id}"
                
                logger.info(f"✅ TTS completed: {audio_url}")
            else:
                logger.warning("⚠️ TTS failed, returning text only")
        else:
            logger.warning("⚠️ TTS not available, returning text only")
        
        return jsonify({
            'status': 'success',
            'user_text': user_text,
            'ai_response': ai_response,
            'audio_url': audio_url
        })
        
    except Exception as e:
        logger.error(f"❌ Error in voice chat: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def text_chat():
    """Handle text-only chat requests (LLM only)"""
    try:
        if not is_initialized:
            return jsonify({
                'status': 'error',
                'error': 'System not initialized yet'
            }), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'error': 'No message provided'
            }), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'status': 'error',
                'error': 'Empty message'
            }), 400
        
        # Generate AI response
        logger.info(f"💬 Text chat request: '{user_message}'")
        ai_response = llm.generate_response(user_message)
        
        if not ai_response:
            return jsonify({
                'status': 'error',
                'error': 'Could not generate response'
            }), 500
        
        logger.info(f"✅ Text chat response: '{ai_response}'")
        
        return jsonify({
            'status': 'success',
            'response': ai_response
        })
        
    except Exception as e:
        logger.error(f"❌ Error in text chat: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Handle text-to-speech requests"""
    try:
        if not is_initialized or not tts or not tts.is_initialized:
            return jsonify({
                'status': 'error',
                'error': 'TTS system not available'
            }), 503
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'error': 'No text provided'
            }), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({
                'status': 'error',
                'error': 'Empty text'
            }), 400
        
        # Generate speech
        logger.info(f"🔊 TTS request: '{text}'")
        audio_array = tts.synthesize(text)
        
        if audio_array is None:
            return jsonify({
                'status': 'error',
                'error': 'Could not generate speech'
            }), 500
        
        # Save audio to temporary file
        audio_id = str(uuid.uuid4())
        audio_filename = f"tts_{audio_id}.wav"
        audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
        
        sf.write(audio_path, audio_array, tts.sample_rate)
        audio_url = f"/api/audio/{audio_id}"
        
        logger.info(f"✅ TTS completed: {audio_url}")
        
        return jsonify({
            'status': 'success',
            'audio_url': audio_url
        })
        
    except Exception as e:
        logger.error(f"❌ Error in TTS: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/audio/<audio_id>')
def serve_audio(audio_id):
    """Serve generated audio files"""
    try:
        # Security: validate audio_id format
        if not audio_id.replace('-', '').replace('_', '').isalnum():
            return "Invalid audio ID", 400
        
        # Find audio file (could be response_* or tts_*)
        for prefix in ['response_', 'tts_']:
            audio_filename = f"{prefix}{audio_id}.wav"
            audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
            
            if os.path.exists(audio_path):
                return send_file(
                    audio_path,
                    mimetype='audio/wav',
                    as_attachment=False,
                    download_name=f'audio_{audio_id}.wav'
                )
        
        return "Audio file not found", 404
        
    except Exception as e:
        logger.error(f"❌ Error serving audio: {e}")
        return "Error serving audio", 500

def main():
    """Main function to run the Flask app"""
    logger.info("🚀 Starting Vietnamese AI Voice Chat Web Application (FINAL VERSION)")
    
    # Initialize components in background
    def init_components():
        success = initialize_components()
        if success:
            logger.info("🎉 ALL SYSTEMS READY!")
        else:
            logger.error("❌ Initialization failed")
    
    # Start initialization in background thread
    init_thread = Thread(target=init_components, daemon=True)
    init_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🌐 Starting web server on http://localhost:{port}")
    logger.info("📋 Available endpoints:")
    logger.info("   • /                    - Web interface")
    logger.info("   • /api/health          - Health check")
    logger.info("   • /api/voice-chat      - Voice chat (STT+LLM+TTS)")
    logger.info("   • /api/chat            - Text chat (LLM only)")
    logger.info("   • /api/tts             - Text-to-speech")
    logger.info("")
    logger.info("🎯 STT DEBUGGING TIPS:")
    logger.info("   ✅ Speak clearly in Vietnamese")
    logger.info("   ✅ Keep audio 1-10 seconds")
    logger.info("   ✅ Check microphone permissions")
    logger.info("   ✅ Use Chrome/Firefox (not Safari)")
    logger.info("   ✅ Check browser console for errors")
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == '__main__':
    main() 