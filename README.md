# Career Flow AI Agent 🎯

An intelligent voice-based AI assistant for Career Flow's career coaching service. Powered by OpenAI and Twilio, Mica provides conversational support for clients seeking career guidance, coaching, and professional development services.

## Features ✨

- **Voice Interaction**: Real-time phone conversations with AI assistant "Mica"
- **User Recognition**: Identifies returning users and personalizes greetings
- **Conversation Tracking**: Full analytics and logging of all interactions
- **Lead Qualification**: Collects user information and schedules coaching sessions
- **Coach Matching**: Recommends appropriate coaches based on user needs
- **Service Information**: Provides details about Career Flow's offerings
- **Analytics Dashboard**: REST API endpoints for conversation insights

## Tech Stack 🛠️

- **Backend**: FastAPI (Python 3.13)
- **AI**: OpenAI GPT-4o-mini
- **Telephony**: Twilio Voice API
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Testing**: Pytest with 57 passing tests

## Prerequisites 📋

- Python 3.13+
- PostgreSQL
- Twilio account with phone number
- OpenAI API key

## Installation 🚀

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/career-flow-ai-agent.git
cd career-flow-ai-agent
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

```bash
# Create database and user
psql postgres
CREATE DATABASE career_flow_db;
CREATE USER career_flow_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE career_flow_db TO career_flow_user;
\q
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567

# Database
DATABASE_URL=postgresql://career_flow_user:your_password@localhost:5432/career_flow_db

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 6. Initialize database

```bash
# Tables will be created automatically on first run
python3 -c "from src.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Usage 💻

### Start the server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Run tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_webhooks.py -v
```

### Access API documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints 📡

### Health & Info

- `GET /` - Root endpoint with API info
- `GET /health` - Health check

### Twilio Webhooks

- `POST /webhooks/twilio/voice` - Incoming call handler
- `POST /webhooks/twilio/process-speech` - Speech processing
- `POST /webhooks/twilio/status` - Call status updates
- `POST /webhooks/twilio/recording` - Recording completion

### Analytics

- `GET /analytics/conversations` - List all conversations
- `GET /analytics/conversations/{id}` - Get conversation by ID
- `GET /analytics/conversations/call/{call_sid}` - Get by Twilio call SID
- `GET /analytics/conversations/{id}/messages` - Get conversation messages
- `GET /analytics/users` - List all users
- `GET /analytics/users/{phone}` - Get user by phone number
- `GET /analytics/users/{phone}/conversations` - Get user's conversations
- `GET /analytics/stats` - System statistics

## Project Structure 📁

```
career-flow-ai-agent/
├── src/
│   ├── api/
│   │   └── routes/
│   │       ├── analytics.py      # Analytics endpoints
│   │       └── webhooks.py       # Twilio webhooks
│   ├── services/
│   │   ├── analytics_service.py  # Data logging & retrieval
│   │   └── voice_service.py      # AI conversation logic
│   ├── models/
│   │   └── models.py             # SQLAlchemy models
│   ├── config.py                 # Configuration
│   ├── database.py               # Database connection
│   └── main.py                   # FastAPI application
├── tests/                        # Test suite
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Mica AI Assistant 🤖

### Personality

Mica is Career Flow's AI assistant with a:
- Calm, conversational tone
- Professional yet approachable demeanor
- Ability to handle interruptions gracefully
- Focus on brief, clear responses (1-2 sentences)

### Services Offered

✅ **Yes:**
- Career coaching (1:1 and group)
- Resume writing and tailoring
- LinkedIn optimization
- Mock interviews
- LeetCode prep
- Executive coaching
- Career strategy

❌ **No:**
- Therapy
- Mental health services
- Non-career topics

### Coach Specialties

- **Alex**: Tech careers, LeetCode prep
- **Atiyeh**: Executive visibility, leadership, stakeholder management
- **Anna**: Design, marketing careers
- **Dimitri**: QA, career strategy

### Pricing

- Main service: $1,000/month coaching
- Custom packages available on website

## Testing 🧪

### Manual Testing with cURL

```bash
# Test incoming call
curl -X POST http://localhost:8000/webhooks/twilio/voice \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=TEST123&From=+15551234567&To=+15559876543"

# Simulate user speech
curl -X POST http://localhost:8000/webhooks/twilio/process-speech \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=TEST123&SpeechResult=I need help with my resume"

# Get conversation
curl http://localhost:8000/analytics/conversations/call/TEST123

# End call
curl -X POST http://localhost:8000/webhooks/twilio/status \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=TEST123&CallStatus=completed"

# View stats
curl http://localhost:8000/analytics/stats
```

### Automated Testing

```bash
# Run full test suite
pytest -v

# Expected output: 57 passed
```

## Database Schema 🗄️

### Users
- `id` (UUID, PK)
- `phone_number` (String, unique)
- `first_name`, `last_name`, `email`
- `user_data` (JSON)
- `created_at`, `last_call_at`

### Conversations
- `id` (UUID, PK)
- `call_sid` (String, unique)
- `user_id` (UUID, FK)
- `phone_number` (String)
- `status` (ACTIVE/COMPLETED/FAILED)
- `started_at`, `ended_at`, `duration_seconds`

### Messages
- `id` (UUID, PK)
- `conversation_id` (UUID, FK)
- `role` (USER/ASSISTANT/SYSTEM)
- `content` (Text)
- `timestamp`
- `extra_data` (JSON)

## Deployment 🚢

### Using Docker

```bash
# Build image
docker build -t career-flow-ai .

# Run container
docker run -p 8000:8000 --env-file .env career-flow-ai
```

### Using Docker Compose

```bash
docker-compose up -d
```

### Production Considerations

- Use environment-specific `.env` files
- Set up SSL/TLS certificates
- Configure Twilio webhook URLs to production domain
- Set up monitoring (Sentry, CloudWatch, etc.)
- Use managed PostgreSQL (RDS, Heroku Postgres, etc.)
- Implement rate limiting
- Set up automated backups

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For issues and questions:
- Open an issue on GitHub
- Email: support@career-flow.com
- Website: https://www.career-flow.com/

## Acknowledgments 🙏

- OpenAI for GPT-4o-mini
- Twilio for voice infrastructure
- FastAPI framework
- SQLAlchemy ORM

---

**Built with ❤️ for Career Flow**
