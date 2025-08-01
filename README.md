# 🇻🇳 Vietnamese AI Voice Chat System

Hệ thống AI nói chuyện realtime tiếng Việt với luồng STT → LLM → TTS mạnh mẽ và nhanh chóng.

## ✨ Tính năng

- **STT (Speech-to-Text)**: Sử dụng OpenAI Whisper API để chuyển đổi giọng nói thành text tiếng Việt
- **LLM (Language Model)**: Sử dụng OpenAI GPT-3.5 Turbo để xử lý và phản hồi thông minh
- **TTS (Text-to-Speech)**: Sử dụng Google TTS để tạo giọng nói tiếng Việt tự nhiên
- **Real-time Processing**: Xử lý audio real-time với Voice Activity Detection
- **Web Interface**: Giao diện web đẹp mắt với continuous listening
- **Easy Setup**: Cài đặt và sử dụng đơn giản

## 🚀 Cài đặt

### Yêu cầu hệ thống
- **Python**: 3.8+ (khuyến nghị 3.9+)
- **RAM**: Tối thiểu 2GB (khuyến nghị 4GB+)
- **Microphone & Speaker**: Cho voice chat
- **Internet**: Cho OpenAI API và Google TTS

### 1. Clone repository
```bash
git clone https://github.com/daovinhkhang/voice-ai.git
cd voice-ai
```

### 2. Tạo virtual environment
```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình API keys
```bash
# Copy template
cp .env.template .env

# Chỉnh sửa file .env với API keys của bạn
nano .env  # hoặc mở bằng editor yêu thích
```

**Nội dung file .env:**
```env
# OpenAI API (bắt buộc)
OPENAI_API_KEY=your_openai_api_key_here

# Audio settings
SAMPLE_RATE=16000
CHUNK_SIZE=1024
CHANNELS=1

# Model settings
STT_MODEL=whisper-1
LLM_MODEL=gpt-3.5-turbo

# Performance settings
MAX_AUDIO_LENGTH=30
RESPONSE_TIMEOUT=10

# Web server settings
PORT=8080
DEBUG=False
```

### 5. Kiểm tra cài đặt
```bash
python test_requirements.py
```

## 🎯 Sử dụng

### Chạy hệ thống
```bash
python app_realtime.py
```

### Hướng dẫn sử dụng
1. Chạy `python app_realtime.py`
2. Mở browser tại `http://localhost:8080`
3. Click nút microphone để bắt đầu continuous listening
4. Nói tiếng Việt và đợi phản hồi
5. Hệ thống sẽ tự động xử lý STT → LLM → TTS

## 🏗️ Cấu trúc dự án

```
voice-ai/
├── app_realtime.py          # Main application (real-time web)
├── sync_simple.py           # STT/LLM/TTS components
├── config.py                # Configuration
├── static/                  # Web assets
│   ├── css/
│   └── js/
├── templates/               # HTML templates
├── requirements.txt         # Dependencies
├── test_requirements.py     # Dependency checker
├── install.sh               # Installation script
└── README.md               # Documentation
```

## 📦 Dependencies

### Core Dependencies
- **Flask**: Web framework
- **OpenAI**: API client cho STT và LLM
- **SoundFile**: Audio processing
- **NumPy**: Numerical computing
- **PyDub**: Audio conversion
- **gTTS**: Google Text-to-Speech

## 🔧 Troubleshooting

### Lỗi cài đặt dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Check Python version
python --version  # Should be 3.8+
```

### Lỗi audio device
```bash
# Kiểm tra audio devices
python -c "import soundfile as sf; print('Audio libraries working')"

# Test microphone (browser-based)
# Check browser console for errors
```

### Lỗi OpenAI API
```bash
# Kiểm tra API key
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; print(openai.Model.list())"
```

## 📝 Ghi chú

- **Lần đầu chạy**: Có thể mất thời gian để tải TTS models
- **Audio quality**: Phụ thuộc vào microphone và môi trường
- **API costs**: OpenAI API có phí sử dụng
- **Internet**: Cần kết nối ổn định cho API calls

## 🐛 Debug Mode

```bash
# Enable debug logging
export DEBUG=True
python app_realtime.py

# Check logs
tail -f server.log
```

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📞 Support

Nếu gặp vấn đề, hãy:
1. Kiểm tra [Troubleshooting](#troubleshooting)
2. Chạy `python test_requirements.py`
3. Tạo issue trên GitHub

---

**Made with ❤️ for Vietnamese AI community**
