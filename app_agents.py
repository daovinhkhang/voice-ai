#!/usr/bin/env python3
"""
Vietnamese AI Voice Chat System with Business Agents
Tích hợp Knowledge Base Agent và Booking Agent
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
from werkzeug.utils import secure_filename

# Import agents
from agents.knowledge_agent import KnowledgeBaseAgent
from agents.booking_agent import BookingAgent

# Import sync components
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
knowledge_agent = None
booking_agent = None
is_initialized = False

def initialize_components():
    """Initialize all AI components and agents"""
    global stt, llm, tts, knowledge_agent, booking_agent, is_initialized
    
    try:
        logger.info("🔄 Initializing business agents system...")
        
        # Initialize core components
        stt = PureSyncSTT()
        llm = PureSyncLLM()
        tts = PureSyncTTS()
        
        # Initialize agents
        knowledge_agent = KnowledgeBaseAgent()
        booking_agent = BookingAgent()
        
        # Initialize TTS
        logger.info("🔄 Initializing TTS...")
        tts_success = tts.initialize()
        
        is_initialized = True
        logger.info("✅ Business agents system ready!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing components: {e}")
        return False

def convert_audio_to_numpy(audio_file, target_sample_rate=16000):
    """Convert uploaded audio file to numpy array"""
    try:
        filename = audio_file.filename or 'audio.webm'
        file_ext = os.path.splitext(filename)[1].lower()
        
        input_temp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        try:
            audio_file.save(input_temp.name)
            input_temp.close()
            output_temp.close()
            
            if file_ext not in ['.wav']:
                import subprocess
                logger.info(f"🔄 Converting {file_ext} to WAV...")
                
                cmd = [
                    'ffmpeg', '-i', input_temp.name,
                    '-acodec', 'pcm_s16le',
                    '-ar', str(target_sample_rate),
                    '-ac', '1',
                    '-y',
                    output_temp.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(input_temp.name)
                    audio = audio.set_frame_rate(target_sample_rate).set_channels(1)
                    audio.export(output_temp.name, format="wav")
                
                audio_data, sample_rate = sf.read(output_temp.name)
            else:
                audio_data, sample_rate = sf.read(input_temp.name)
            
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            if sample_rate != target_sample_rate:
                import librosa
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=target_sample_rate
                )
            
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            logger.info(f"✅ Audio converted: {len(audio_data)} samples, {target_sample_rate}Hz")
            return audio_data
            
        finally:
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
            'message': 'Business agents system ready',
            'components': {
                'stt': 'ready',
                'llm': 'ready', 
                'tts': 'ready' if tts and tts.is_initialized else 'limited',
                'knowledge_agent': 'ready',
                'booking_agent': 'ready'
            }
        })
    else:
        return jsonify({
            'status': 'initializing',
            'message': 'Components still loading...'
        }), 503

@app.route('/api/voice-chat', methods=['POST'])
def voice_chat():
    """Handle voice chat requests with agent routing"""
    try:
        if not is_initialized:
            return jsonify({
                'status': 'error',
                'error': 'System not initialized yet'
            }), 503
        
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
        
        # Step 2: Route to appropriate agent
        ai_response = route_to_agent(user_text)
        
        if not ai_response:
            return jsonify({
                'status': 'error',
                'error': 'Could not generate AI response'
            }), 500
        
        logger.info(f"✅ Agent Response: '{ai_response}'")
        
        # Step 3: Text-to-Speech
        audio_url = None
        if tts and tts.is_initialized:
            logger.info("🔊 Generating speech...")
            audio_array = tts.synthesize(ai_response)
            
            if audio_array is not None:
                audio_id = str(uuid.uuid4())
                audio_filename = f"response_{audio_id}.wav"
                audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
                
                sf.write(audio_path, audio_array, tts.sample_rate)
                audio_url = f"/api/audio/{audio_id}"
                
                logger.info(f"✅ TTS completed: {audio_url}")
        
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

def route_to_agent(user_text: str) -> str:
    """Route user input to appropriate agent"""
    try:
        # Keywords để xác định agent
        knowledge_keywords = ['tài liệu', 'document', 'file', 'upload', 'hỏi', 'tư vấn', 'thông tin']
        booking_keywords = ['đặt lịch', 'booking', 'lịch hẹn', 'appointment', 'khách hàng', 'email']
        
        user_text_lower = user_text.lower()
        
        # Check for knowledge base queries
        if any(keyword in user_text_lower for keyword in knowledge_keywords):
            if 'upload' in user_text_lower or 'tải lên' in user_text_lower:
                return "Để upload tài liệu, vui lòng sử dụng giao diện web hoặc API /api/upload-document"
            else:
                return knowledge_agent.get_advice(user_text)
        
        # Check for booking queries
        elif any(keyword in user_text_lower for keyword in booking_keywords):
            return handle_booking_request(user_text)
        
        # Default to general conversation
        else:
            return llm.generate_response(user_text)
            
    except Exception as e:
        logger.error(f"Error routing to agent: {e}")
        return llm.generate_response(user_text)

def handle_booking_request(user_text: str) -> str:
    """Handle booking-related requests"""
    try:
        # Simple booking intent detection
        if 'thêm khách hàng' in user_text.lower() or 'add customer' in user_text.lower():
            return "Để thêm khách hàng, vui lòng sử dụng API /api/customers với thông tin: tên, email, số điện thoại"
        
        elif 'tạo booking' in user_text.lower() or 'create booking' in user_text.lower():
            return "Để tạo booking, vui lòng sử dụng API /api/bookings với thông tin: customer_id, service_type, booking_date"
        
        elif 'danh sách khách hàng' in user_text.lower():
            customers = booking_agent.get_customer_list()
            if customers:
                return f"Có {len(customers)} khách hàng trong hệ thống. Vui lòng sử dụng API /api/customers để xem chi tiết."
            else:
                return "Chưa có khách hàng nào trong hệ thống."
        
        else:
            return "Tôi có thể giúp bạn với booking. Bạn muốn thêm khách hàng, tạo lịch hẹn, hay xem danh sách?"
            
    except Exception as e:
        logger.error(f"Error handling booking request: {e}")
        return "Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu booking."

# Knowledge Base Agent APIs
@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """Upload document to knowledge base"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in ['.pdf', '.docx', '.txt', '.md']:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # Process document
        success = knowledge_agent.process_document(temp_path, file_ext[1:])
        
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Document {filename} processed successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to process document'
            }), 500
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/query', methods=['POST'])
def query_knowledge():
    """Query knowledge base"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        answer = knowledge_agent.get_advice(question)
        
        return jsonify({
            'status': 'success',
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/summary', methods=['GET'])
def get_knowledge_summary():
    """Get knowledge base summary"""
    try:
        summary = knowledge_agent.get_document_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting knowledge summary: {e}")
        return jsonify({'error': str(e)}), 500

# Booking Agent APIs
@app.route('/api/customers', methods=['GET', 'POST'])
def handle_customers():
    """Handle customer operations"""
    try:
        if request.method == 'GET':
            customers = booking_agent.get_customer_list()
            return jsonify(customers)
        
        elif request.method == 'POST':
            data = request.get_json()
            result = booking_agent.add_customer(data)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error handling customers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    """Handle booking operations"""
    try:
        if request.method == 'GET':
            status = request.args.get('status')
            bookings = booking_agent.get_booking_list(status)
            return jsonify(bookings)
        
        elif request.method == 'POST':
            data = request.get_json()
            result = booking_agent.create_booking(data)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error handling bookings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>/confirm', methods=['POST'])
def confirm_booking(booking_id):
    """Confirm booking"""
    try:
        result = booking_agent.confirm_booking(booking_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error confirming booking: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/customers', methods=['POST'])
def export_customers():
    """Export customer data"""
    try:
        data = request.get_json()
        file_path = data.get('file_path', 'customers_export.json')
        
        success = booking_agent.export_customer_data(file_path)
        
        if success:
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to export data'}), 500
            
    except Exception as e:
        logger.error(f"Error exporting customers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio/<audio_id>')
def serve_audio(audio_id):
    """Serve generated audio files"""
    try:
        if not audio_id.replace('-', '').replace('_', '').isalnum():
            return "Invalid audio ID", 400
        
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
    logger.info("🚀 Starting Vietnamese AI Voice Chat with Business Agents")
    
    # Initialize components in background
    def init_components():
        success = initialize_components()
        if success:
            logger.info("🎉 ALL SYSTEMS READY!")
        else:
            logger.error("❌ Initialization failed")
    
    init_thread = Thread(target=init_components, daemon=True)
    init_thread.start()
    
    # Run Flask app
    port = config.PORT
    debug = config.DEBUG
    
    logger.info(f"🌐 Starting web server on http://localhost:{port}")
    logger.info("📋 Available endpoints:")
    logger.info("   • /                    - Web interface")
    logger.info("   • /api/health          - Health check")
    logger.info("   • /api/voice-chat      - Voice chat with agent routing")
    logger.info("   • /api/upload-document - Upload documents")
    logger.info("   • /api/knowledge/*     - Knowledge base operations")
    logger.info("   • /api/customers       - Customer management")
    logger.info("   • /api/bookings        - Booking management")
    
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