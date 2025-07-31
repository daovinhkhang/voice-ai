// Vietnamese AI Voice Chat - Frontend JavaScript
// Continuous Voice Chat with Auto VAD

class VoiceChat {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isProcessing = false;
        this.isContinuousMode = true; // New: continuous mode
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.vadThreshold = 0.01;
        this.silenceTimeout = null;
        this.silenceDuration = 1500; // 1.5 seconds of silence
        
        this.initializeElements();
        this.checkSystemHealth();
        this.setupEventListeners();
    }
    
    initializeElements() {
        // Get DOM elements
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.chatContainer = document.getElementById('chatContainer');
        this.recordBtn = document.getElementById('recordBtn');
        this.recordingIndicator = document.getElementById('recordingIndicator');
        this.textInput = document.getElementById('textInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
    }
    
    async checkSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('🟢', 'Sẵn sàng - Nói liên tục');
                this.enableControls();
                this.startContinuousListening();
            } else {
                this.updateStatus('🔴', 'Lỗi hệ thống');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateStatus('🔴', 'Không thể kết nối');
        }
    }
    
    updateStatus(indicator, text) {
        this.statusIndicator.textContent = indicator;
        this.statusText.textContent = text;
    }
    
    enableControls() {
        this.recordBtn.disabled = false;
        this.textInput.disabled = false;
        this.sendBtn.disabled = false;
    }
    
    disableControls() {
        this.recordBtn.disabled = true;
        this.textInput.disabled = true;
        this.sendBtn.disabled = true;
    }
    
    setupEventListeners() {
        // Toggle continuous mode button
        this.recordBtn.addEventListener('click', () => {
            if (this.isContinuousMode) {
                this.stopContinuousListening();
            } else {
                this.startContinuousListening();
            }
        });
        
        // Send button
        this.sendBtn.addEventListener('click', () => {
            this.sendTextMessage();
        });
        
        // Enter key in text input
        this.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });
    }
    
    async startContinuousListening() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Setup Web Audio API for VAD
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;
            this.analyser.minDecibels = -90;
            this.analyser.maxDecibels = -10;
            
            this.microphone.connect(this.analyser);
            
            this.isContinuousMode = true;
            this.isRecording = false;
            this.audioChunks = [];
            
            // Update UI
            this.recordBtn.classList.add('continuous');
            this.recordBtn.innerHTML = '<i class="fas fa-microphone-slash"></i><span>Dừng lắng nghe</span>';
            this.updateStatus('🟡', 'Đang lắng nghe...');
            
            // Start VAD monitoring
            this.startVADMonitoring();
            
        } catch (error) {
            console.error('Error starting continuous listening:', error);
            alert('Không thể truy cập microphone. Vui lòng cho phép quyền truy cập.');
        }
    }
    
    startVADMonitoring() {
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const checkAudioLevel = () => {
            if (!this.isContinuousMode) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            
            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;
            const normalizedVolume = average / 255;
            
            // VAD logic
            if (normalizedVolume > this.vadThreshold) {
                // Speech detected
                if (!this.isRecording) {
                    this.startRecording();
                }
                // Reset silence timeout
                if (this.silenceTimeout) {
                    clearTimeout(this.silenceTimeout);
                }
                this.silenceTimeout = setTimeout(() => {
                    if (this.isRecording) {
                        this.stopRecording();
                    }
                }, this.silenceDuration);
            }
            
            // Continue monitoring
            requestAnimationFrame(checkAudioLevel);
        };
        
        checkAudioLevel();
    }
    
    async startRecording() {
        if (this.isRecording || this.isProcessing) return;
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = '';
                    }
                }
            }

            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: mimeType
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processVoiceInput();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.recordingIndicator.classList.add('show');
            this.updateStatus('🔴', 'Đang ghi âm...');
            
        } catch (error) {
            console.error('Error starting recording:', error);
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.isRecording = false;
            
            // Update UI
            this.recordingIndicator.classList.remove('show');
            this.updateStatus('🟡', 'Đang lắng nghe...');
        }
    }
    
    stopContinuousListening() {
        this.isContinuousMode = false;
        this.isRecording = false;
        
        if (this.mediaRecorder) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
        }
        
        // Update UI
        this.recordBtn.classList.remove('continuous');
        this.recordBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Bắt đầu lắng nghe</span>';
        this.recordingIndicator.classList.remove('show');
        this.updateStatus('🟢', 'Sẵn sàng - Nói liên tục');
    }
    
    async processVoiceInput() {
        if (this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.disableControls();
            this.showLoading('Đang xử lý giọng nói...');
            
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: this.mediaRecorder.mimeType });

            // Create form data with original blob (backend will handle conversion)
            const formData = new FormData();

            // Determine file extension based on MIME type
            let fileName = 'audio.webm';
            if (this.mediaRecorder.mimeType.includes('mp4')) {
                fileName = 'audio.mp4';
            } else if (this.mediaRecorder.mimeType.includes('wav')) {
                fileName = 'audio.wav';
            }

            formData.append('audio', audioBlob, fileName);
            
            // Send to backend
            const response = await fetch('/api/voice-chat', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Add messages to chat
                this.addMessage(data.user_text, 'user');
                this.addMessage(data.ai_response, 'ai');
                
                // Play response audio
                if (data.audio_url) {
                    await this.playAudio(data.audio_url);
                }
                
                // Resume continuous listening if still in continuous mode
                if (this.isContinuousMode) {
                    this.updateStatus('🟡', 'Đang lắng nghe...');
                } else {
                    this.updateStatus('🟢', 'Sẵn sàng');
                }
            } else {
                throw new Error(data.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error processing voice input:', error);
            this.addMessage('Lỗi: ' + error.message, 'error');
            this.updateStatus('🔴', 'Lỗi xử lý');
        } finally {
            this.isProcessing = false;
            this.enableControls();
            this.hideLoading();
        }
    }
    
    async sendTextMessage() {
        const message = this.textInput.value.trim();
        if (!message || this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.disableControls();
            this.showLoading('Đang tạo phản hồi...');
            
            // Add user message to chat
            this.addMessage(message, 'user');
            this.textInput.value = '';
            
            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Add AI response to chat
                this.addMessage(data.response, 'ai');
                
                // Generate and play TTS
                if (data.response) {
                    await this.generateTTS(data.response);
                }
                
                // Resume continuous listening if still in continuous mode
                if (this.isContinuousMode) {
                    this.updateStatus('🟡', 'Đang lắng nghe...');
                } else {
                    this.updateStatus('🟢', 'Sẵn sàng');
                }
            } else {
                throw new Error(data.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error sending text message:', error);
            this.addMessage('Lỗi: ' + error.message, 'error');
        } finally {
            this.isProcessing = false;
            this.enableControls();
            this.hideLoading();
        }
    }
    
    async generateTTS(text) {
        try {
            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });
            
            const data = await response.json();
            
            if (data.status === 'success' && data.audio_url) {
                await this.playAudio(data.audio_url);
            }
            
        } catch (error) {
            console.error('Error generating TTS:', error);
        }
    }
    
    async playAudio(audioUrl) {
        try {
            this.audioPlayer.src = audioUrl;
            this.audioPlayer.load();
            
            // Wait for audio to load
            await new Promise((resolve, reject) => {
                this.audioPlayer.oncanplaythrough = resolve;
                this.audioPlayer.onerror = reject;
                this.audioPlayer.load();
            });
            
            // Play audio
            await this.audioPlayer.play();
            
            // Wait for audio to finish
            await new Promise((resolve) => {
                this.audioPlayer.onended = resolve;
            });
            
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'user') {
            contentDiv.innerHTML = `<strong>👤 Bạn:</strong><p>${content}</p>`;
        } else if (type === 'ai') {
            contentDiv.innerHTML = `<strong>🤖 AI:</strong><p>${content}</p>`;
        } else if (type === 'error') {
            contentDiv.innerHTML = `<strong>❌ Lỗi:</strong><p>${content}</p>`;
            messageDiv.className = 'message error-message';
        }
        
        messageDiv.appendChild(contentDiv);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
    
    async convertToWav(audioBlob) {
        // This function is no longer needed as backend handles conversion
        return audioBlob;
    }
    
    showLoading(text) {
        this.loadingText.textContent = text;
        this.loadingOverlay.classList.add('show');
    }
    
    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VoiceChat();
});
