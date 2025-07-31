# 🇻🇳 Vietnamese AI Voice Chat System

Hệ thống AI nói chuyện realtime tiếng Việt với luồng STT → LLM → TTS mạnh mẽ và nhanh chóng.

## ✨ Tính năng

- **STT (Speech-to-Text)**: Sử dụng OpenAI GPT-4o-Transcribe API để chuyển đổi giọng nói thành text tiếng Việt
- **LLM (Language Model)**: Sử dụng OpenAI GPT-3.5 Turbo để xử lý và phản hồi thông minh
- **TTS (Text-to-Speech)**: Sử dụng model zalopay/vietnamese-tts để tạo giọng nói tiếng Việt tự nhiên
- **Real-time Processing**: Xử lý audio real-time với Voice Activity Detection
- **Easy Setup**: Cài đặt và sử dụng đơn giản

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd voice_new
```

### 2. Tạo virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình API key
Tạo file `.env` và thêm OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## 🎯 Sử dụng

### Chạy hệ thống
```bash
python main.py
```

### Hướng dẫn sử dụng
1. Chạy chương trình và đợi thông báo "🎤 Listening..."
2. Nói tiếng Việt vào microphone
3. Hệ thống sẽ tự động:
   - Chuyển đổi giọng nói thành text (STT)
   - Xử lý và tạo phản hồi thông minh (LLM)
   - Chuyển đổi phản hồi thành giọng nói (TTS)
4. Nói "thoát" hoặc "exit" để kết thúc

## 🏗️ Cấu trúc dự án

```
voice_new/
├── src/
│   ├── stt/                 # Speech-to-Text module
│   │   └── whisper_stt.py
│   ├── llm/                 # Language Model module
│   │   └── gpt_llm.py
│   ├── tts/                 # Text-to-Speech module
│   │   └── vietnamese_tts.py
│   ├── audio/               # Audio handling
│   │   └── audio_handler.py
│   ├── utils/               # Utilities
│   │   └── config.py
│   └── voice_chat.py        # Main application
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
└── README.md               # Documentation
```

## ⚙️ Cấu hình

Các cài đặt có thể được điều chỉnh trong file `.env`:

```env
# OpenAI API
OPENAI_API_KEY=your_api_key

# Audio settings
SAMPLE_RATE=16000
CHUNK_SIZE=1024
CHANNELS=1

# Model settings
STT_MODEL=whisper-1
LLM_MODEL=gpt-3.5-turbo
TTS_MODEL=zalopay/vietnamese-tts

# Performance settings
MAX_AUDIO_LENGTH=30
RESPONSE_TIMEOUT=10
```

## 🔧 Yêu cầu hệ thống

- Python 3.8+
- Microphone và speaker/headphones
- Kết nối internet (cho OpenAI API)
- RAM: tối thiểu 4GB (khuyến nghị 8GB+)
- GPU: không bắt buộc nhưng sẽ tăng tốc TTS

## 📝 Ghi chú

- Lần đầu chạy có thể mất thời gian để tải model TTS
- Chất lượng âm thanh phụ thuộc vào microphone và môi trường
- Cần OpenAI API key hợp lệ để sử dụng STT và LLM

## 🐛 Troubleshooting

### Lỗi audio device
```bash
# Kiểm tra audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Lỗi model TTS
- Đảm bảo có kết nối internet để tải model
- Kiểm tra dung lượng ổ cứng (model khoảng 1-2GB)

### Lỗi API
- Kiểm tra OpenAI API key trong file `.env`
- Đảm bảo có credit trong tài khoản OpenAI

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.
