// Vietnamese AI Voice Chat - Ultra Minimalist Futuristic Theme

class UltraMinimalistVoiceChat {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isProcessing = false;
        this.isContinuousMode = true;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.vadThreshold = 0.015;
        this.silenceTimeout = null;
        this.silenceDuration = 2000;
        this.minRecordingDuration = 500;
        this.recordingStartTime = 0;
        
        this.initializeElements();
        this.checkSystemHealth();
        this.setupEventListeners();
    }
    
    initializeElements() {
        // Get DOM elements
        this.recordBtn = document.getElementById('recordBtn');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        
        // Hidden elements for functionality
        this.chatContainer = document.getElementById('chatContainer');
        this.textInput = document.getElementById('textInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.audioPlayer = document.getElementById('audioPlayer');
    }
    
    async checkSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.enableControls();
                this.startContinuousListening();
            } else {
                this.recordBtn.style.opacity = '0.3';
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.recordBtn.style.opacity = '0.3';
        }
    }
    
    enableControls() {
        this.recordBtn.disabled = false;
    }
    
    disableControls() {
        this.recordBtn.disabled = true;
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
    }
    
    async startContinuousListening() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Setup Web Audio API for VAD
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            
            this.analyser.fftSize = 512;
            this.analyser.smoothingTimeConstant = 0.8;
            this.analyser.minDecibels = -90;
            this.analyser.maxDecibels = -10;
            
            this.microphone.connect(this.analyser);
            
            this.isContinuousMode = true;
            this.isRecording = false;
            this.audioChunks = [];
            
            // Update UI
            this.recordBtn.classList.add('continuous');
            this.recordBtn.classList.remove('recording');
            
            // Start VAD monitoring
            this.startVADMonitoring();
            
        } catch (error) {
            console.error('Error starting continuous listening:', error);
        }
    }
    
    startVADMonitoring() {
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        let speechDetected = false;
        let consecutiveSpeechFrames = 0;
        let consecutiveSilenceFrames = 0;
        
        const checkAudioLevel = () => {
            if (!this.isContinuousMode) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            
            // Calculate average volume with frequency weighting
            let sum = 0;
            let weightedSum = 0;
            let weight = 1;
            
            for (let i = 0; i < bufferLength; i++) {
                const value = dataArray[i];
                sum += value;
                weightedSum += value * weight;
                weight += 0.1;
            }
            
            const average = sum / bufferLength;
            const weightedAverage = weightedSum / (bufferLength * (1 + 0.1 * bufferLength / 2));
            const normalizedVolume = Math.max(average / 255, weightedAverage / 255);
            
            // Enhanced VAD logic
            if (normalizedVolume > this.vadThreshold) {
                consecutiveSpeechFrames++;
                consecutiveSilenceFrames = 0;
                
                if (consecutiveSpeechFrames > 3 && !speechDetected) {
                    speechDetected = true;
                    if (!this.isRecording) {
                        this.startRecording();
                    }
                }
                
                // Reset silence timeout
                if (this.silenceTimeout) {
                    clearTimeout(this.silenceTimeout);
                }
                this.silenceTimeout = setTimeout(() => {
                    if (this.isRecording) {
                        const recordingDuration = Date.now() - this.recordingStartTime;
                        if (recordingDuration >= this.minRecordingDuration) {
                            this.stopRecording();
                        }
                    }
                }, this.silenceDuration);
                
            } else {
                consecutiveSilenceFrames++;
                consecutiveSpeechFrames = 0;
                
                if (consecutiveSilenceFrames > 10) {
                    speechDetected = false;
                }
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
                    noiseSuppression: true,
                    autoGainControl: true
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
            this.recordingStartTime = Date.now();
            
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
            this.recordBtn.classList.remove('continuous');
            this.recordBtn.classList.add('recording');
            
        } catch (error) {
            console.error('Error starting recording:', error);
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.isRecording = false;
            
            // Update UI - processing will be handled in processVoiceInput
            this.recordBtn.classList.remove('recording');
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
        this.recordBtn.classList.remove('continuous', 'recording');
    }
    
    async processVoiceInput() {
        if (this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.disableControls();
            
            // Update UI to processing state
            this.recordBtn.classList.remove('recording', 'continuous');
            this.recordBtn.classList.add('processing');
            
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: this.mediaRecorder.mimeType });

            // Create form data
            const formData = new FormData();
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
                // Play response audio
                if (data.audio_url) {
                    await this.playAudio(data.audio_url);
                }
                
                // Resume continuous listening
                if (this.isContinuousMode) {
                    this.recordBtn.classList.remove('processing');
                    this.recordBtn.classList.add('continuous');
                }
            } else {
                throw new Error(data.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error processing voice input:', error);
            // On error, return to continuous state
            if (this.isContinuousMode) {
                this.recordBtn.classList.remove('processing');
                this.recordBtn.classList.add('continuous');
            }
        } finally {
            this.isProcessing = false;
            this.enableControls();
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
    new UltraMinimalistVoiceChat();
}); 