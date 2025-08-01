# 🤖 Vietnamese AI Voice Chat System with Business Agents

Hệ thống AI Voice Chat tiếng Việt tích hợp 2 agent chuyên biệt cho doanh nghiệp:
- **Knowledge Base Agent**: Tư vấn dựa trên tài liệu (PDF, DOCX, TXT, MD)
- **Booking Agent**: Quản lý lịch hẹn, khách hàng và gửi email tự động

## ✨ Tính năng chính

### 🎤 Voice Chat với Agent Routing
- **Speech-to-Text**: Chuyển đổi giọng nói tiếng Việt thành văn bản
- **Agent Routing**: Tự động chuyển hướng đến agent phù hợp
- **Text-to-Speech**: Chuyển đổi phản hồi thành giọng nói tiếng Việt
- **Real-time Processing**: Xử lý âm thanh thời gian thực

### 📚 Knowledge Base Agent
- **Document Upload**: Hỗ trợ PDF, DOCX, TXT, MD
- **RAG System**: Retrieval-Augmented Generation với ChromaDB
- **Vietnamese Q&A**: Tư vấn dựa trên nội dung tài liệu
- **Document Summary**: Tóm tắt thông tin tài liệu

### 📅 Booking Agent
- **Customer Management**: Quản lý thông tin khách hàng
- **Booking System**: Tạo và quản lý lịch hẹn
- **Email Automation**: Gửi email xác nhận tự động
- **Google Calendar**: Tích hợp với Google Calendar
- **Data Export**: Xuất dữ liệu khách hàng

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- FFmpeg (cho xử lý âm thanh)
- Microphone (cho voice chat)

### 1. Clone repository
```bash
git clone https://github.com/daovinhkhang/voice-ai.git
cd voice-ai
```

### 2. Tạo virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements_agents.txt
```

### 4. Cấu hình API keys
Tạo file `.env` từ `env_example.txt`:
```bash
cp env_example.txt .env
```

Cập nhật các giá trị trong `.env`:
```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Email (cho Booking Agent)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

### 5. Chạy hệ thống
```bash
python app_agents.py
```

Truy cập: http://localhost:8080

## 📖 Hướng dẫn sử dụng

### Voice Chat
1. **Bắt đầu**: Nhấn "Start Recording" và nói bằng tiếng Việt
2. **Agent Routing**: 
   - Nói "tài liệu" hoặc "document" → Knowledge Base Agent
   - Nói "booking" hoặc "lịch hẹn" → Booking Agent
   - Các câu khác → General AI Chat

### Knowledge Base Agent
1. **Upload tài liệu**: Chọn file PDF/DOCX/TXT/MD và upload
2. **Đặt câu hỏi**: Gõ câu hỏi về nội dung tài liệu
3. **Nhận tư vấn**: AI trả lời dựa trên nội dung tài liệu

### Booking Agent
1. **Thêm khách hàng**: Điền thông tin khách hàng
2. **Tạo booking**: Chọn khách hàng, dịch vụ, thời gian
3. **Xác nhận**: Hệ thống gửi email xác nhận tự động
4. **Quản lý**: Xem danh sách khách hàng và booking

## 🔧 API Endpoints

### Voice Chat
- `POST /api/voice-chat` - Voice chat với agent routing

### Knowledge Base
- `POST /api/upload-document` - Upload tài liệu
- `POST /api/knowledge/query` - Đặt câu hỏi
- `GET /api/knowledge/summary` - Tóm tắt knowledge base

### Booking Management
- `GET /api/customers` - Lấy danh sách khách hàng
- `POST /api/customers` - Thêm khách hàng
- `GET /api/bookings` - Lấy danh sách booking
- `POST /api/bookings` - Tạo booking
- `POST /api/bookings/{id}/confirm` - Xác nhận booking
- `POST /api/export/customers` - Xuất dữ liệu khách hàng

### System
- `GET /api/health` - Kiểm tra trạng thái hệ thống
- `GET /api/audio/{id}` - Lấy file âm thanh

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Input   │───▶│   STT Engine    │───▶│  Agent Router   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TTS Engine    │◀───│  Response Gen   │◀───│  Agent System   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                       ┌─────────────────┐
                                       │  Knowledge Base │
                                       │     Agent       │
                                       └─────────────────┘
                                       │  Booking Agent  │
                                       └─────────────────┘
```

## 📁 Cấu trúc project

```
voice_new/
├── app_agents.py              # Main application với agents
├── sync_simple.py             # Core AI components
├── config.py                  # Configuration
├── requirements_agents.txt    # Dependencies cho agents
├── env_example.txt           # Environment variables template
├── agents/
│   ├── knowledge_agent.py    # Knowledge Base Agent
│   └── booking_agent.py      # Booking Agent
├── templates/
│   └── index.html            # Web interface
├── knowledge_base/           # Vector database
├── uploads/                  # Uploaded files
└── booking_system.db         # SQLite database
```

## 🔧 Cấu hình nâng cao

### Email Configuration
Để sử dụng tính năng gửi email:
1. Tạo App Password cho Gmail
2. Cập nhật SMTP settings trong `.env`

### Google Calendar Integration
1. Tạo Google Cloud Project
2. Enable Calendar API
3. Download `credentials.json`
4. Chạy setup lần đầu để authorize

### Database
- Mặc định: SQLite
- Có thể thay đổi sang PostgreSQL/MySQL trong config

## 🐛 Troubleshooting

### Lỗi âm thanh
```bash
# Kiểm tra FFmpeg
ffmpeg -version

# Cài đặt FFmpeg
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download từ https://ffmpeg.org/
```

### Lỗi OpenAI API
```bash
# Kiểm tra API key
echo $OPENAI_API_KEY

# Test API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### Lỗi dependencies
```bash
# Cài đặt lại dependencies
pip install --upgrade -r requirements_agents.txt

# Kiểm tra Python version
python --version
```

### Lỗi database
```bash
# Xóa database cũ
rm booking_system.db

# Restart application
python app_agents.py
```

## 📊 Performance

### Tối ưu hóa
- **Vector Database**: ChromaDB cho RAG
- **Audio Processing**: FFmpeg cho conversion
- **Caching**: Temporary file caching
- **Async Processing**: Background initialization

### Monitoring
- Health check endpoint
- Logging system
- Error handling
- Performance metrics

## 🔒 Security

### Best Practices
- Environment variables cho sensitive data
- File upload validation
- SQL injection prevention
- CORS configuration
- Rate limiting (có thể thêm)

## 🚀 Deployment

### Local Development
```bash
python app_agents.py
```

### Production
```bash
# Sử dụng Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app_agents:app

# Hoặc Docker
docker build -t voice-ai .
docker run -p 8080:8080 voice-ai
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License - xem file [LICENSE](LICENSE)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/daovinhkhang/voice-ai/issues)
- **Email**: [Your Email]
- **Documentation**: [Wiki](https://github.com/daovinhkhang/voice-ai/wiki)

## 🔮 Roadmap

### Phase 1: Core Agents ✅
- [x] Knowledge Base Agent
- [x] Booking Agent
- [x] Voice Interface
- [x] Web UI

### Phase 2: Advanced Features
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] API documentation

### Phase 3: Enterprise
- [ ] Multi-tenant support
- [ ] Advanced security
- [ ] Cloud deployment
- [ ] Integration APIs

---

**Made with ❤️ for Vietnamese businesses**
