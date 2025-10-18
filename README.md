# Career Flow AI Agent 🎯

> **📄 For LG NOVA Interview:** See [CODE_SAMPLE.md](CODE_SAMPLE.md) for a comprehensive technical walkthrough of the AI-powered conversation analysis system.

An intelligent voice-based AI assistant for Career Flow's career coaching service. Powered by OpenAI and Twilio, Mica provides conversational support for clients seeking career guidance, coaching, and professional development services.

**Featured Component:** AI-powered conversation quality monitoring that automatically analyzes voice calls and generates improvement recommendations. See [CODE_SAMPLE.md](CODE_SAMPLE.md) for details.

## Features ✨

### Voice Agent (Mica AI)
- **Voice Interaction**: Real-time phone conversations with AI assistant "Mica"
- **User Recognition**: Identifies returning users and personalizes greetings
- **Lead Qualification**: Collects user information and schedules coaching sessions
- **Coach Matching**: Recommends appropriate coaches based on user needs
- **Service Information**: Provides details about Career Flow's offerings

### Automated Quality Monitoring (Featured)
- **Two-Phase Analysis**: Rule-based pattern detection + GPT-4o-mini insights
- **Conversation Sampling**: Analyzes representative samples for cost-effective monitoring
- **AI Recommendations**: Generates actionable improvements with confidence scoring
- **24/7 Automation**: Daily analysis via cron, PM2-managed uptime
- **Production Analytics**: Full conversation tracking and trend analysis

## Tech Stack 🛠️

- **Backend**: FastAPI (Python 3.13)
- **AI**: OpenAI GPT-4o-mini (voice agent + analysis)
- **Telephony**: Twilio Voice API
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Process Management**: PM2 (24/7 uptime)
- **Testing**: Pytest with comprehensive test coverage

## Quick Start 🚀

### 1. Clone and Install

```bash
git clone https://github.com/AleksandarCakic/career-flow-ai-agent.git
cd career-flow-ai-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - TWILIO_ACCOUNT_SID
# - TWILIO_AUTH_TOKEN
# - TWILIO_PHONE_NUMBER
```

### 3. Start the Server

```bash
# Option 1: Development (with auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Production (with PM2)
pm2 start ecosystem.config.js
```

### 4. View Dashboard & Run Analysis

```bash
# System status
./scripts/dashboard.sh

# Run conversation analysis
./scripts/auto-analyze.sh

# View AI recommendations
./scripts/view-recommendations.sh
```

## Project Structure 📁

```
career-flow-ai-agent/
├── src/
│   ├── api/routes/
│   │   ├── webhooks.py           # Twilio voice webhooks
│   │   ├── analytics.py          # Conversation analytics API
│   │   └── admin.py              # Analysis trigger endpoints
│   ├── services/
│   │   ├── voice_service.py      # AI voice agent logic
│   │   ├── analytics_service.py  # Conversation tracking
│   │   └── prompt_optimizer_service.py  # ⭐ AI analysis engine
│   ├── models/models.py          # Database models
│   ├── database.py               # SQLAlchemy setup
│   ├── config.py                 # Configuration
│   └── main.py                   # FastAPI app
├── scripts/
│   ├── auto-analyze.sh           # Automated analysis (cron)
│   ├── view-recommendations.sh   # Display AI suggestions
│   ├── analyze-conversations.sh  # View transcripts
│   ├── dashboard.sh              # System monitoring
│   └── health-check.sh           # Health validation
├── tests/                        # Comprehensive test suite
├── analysis_reports/             # Timestamped analysis outputs
├── ecosystem.config.js           # PM2 configuration
├── CODE_SAMPLE.md               # ⭐ Technical deep-dive
└── README.md                     # This file
```

## Key API Endpoints 📡

### Conversation Analysis (Featured)
```bash
# Trigger analysis (last 7 days)
POST /admin/analyze-conversations?hours=168&min_conversations=1

# Response: Pattern detection + AI recommendations
{
  "analysis": {
    "status": "analyzed",
    "total_conversations": 14,
    "issues": {
      "technical_errors": 2,
      "transfer_failures": 2,
      "name_not_collected": 3
    }
  },
  "improvements": {
    "critical_issues": [...],
    "recommendations": [...],
    "confidence": "high"
  }
}
```

### Voice Agent
- `POST /webhooks/twilio/voice` - Incoming call handler
- `POST /webhooks/twilio/process-speech` - Speech processing
- `POST /webhooks/twilio/status` - Call status updates

### Analytics
- `GET /analytics/conversations` - List conversations
- `GET /analytics/conversations/{id}/messages` - Get messages
- `GET /analytics/stats` - System statistics
- `GET /analytics/users` - List users

### Health
- `GET /` - API info
- `GET /health` - Health check

Full API docs: http://localhost:8000/docs

## Testing 🧪

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Test specific module
pytest tests/test_prompt_optimizer.py -v

# Manual API testing
curl -X POST http://localhost:8000/admin/analyze-conversations?hours=168
```

## Production Features 🚀

### 24/7 Monitoring
- **PM2**: Auto-restart on crashes, memory monitoring
- **Cron**: Daily automated analysis at 2 AM
- **Logging**: Comprehensive logs with timestamps
- **Health checks**: Automated system validation

### Cost Optimization
- **Conversation sampling**: Analyze 5 instead of all (10x cheaper)
- **GPT-4o-mini**: 90% cost reduction vs GPT-4, same insights
- **Pattern detection**: Rule-based checks cost $0
- **Result**: ~$1-3/month for 100 conversations

### Scalability
- **SQLAlchemy ORM**: Easy PostgreSQL migration
- **Indexed queries**: Fast conversation lookups
- **Async-ready**: FastAPI supports async processing
- **Horizontal scaling**: Stateless design

## Database Schema 🗄️

### Users
- Stores phone numbers, names, contact info
- Tracks conversation history
- User preferences and metadata

### Conversations
- Call tracking (Twilio call_sid)
- Status monitoring (active/completed/failed)
- Duration and timestamp metrics

### Messages
- Full conversation transcripts
- Role-based (user/assistant/system)
- Metadata for analysis

### Pattern Detection
- Integrated into conversation analysis
- Detects 5 issue types automatically
- Logs findings for trend analysis

## Mica AI Assistant 🤖

### Personality
- Calm, conversational tone
- Professional yet approachable
- Brief responses (1-2 sentences)
- Handles interruptions gracefully

### Services Offered
✅ Career coaching, resume writing, LinkedIn optimization, mock interviews, LeetCode prep, executive coaching

❌ Therapy, mental health, non-career topics

### Coach Specialties
- **Alex**: Tech careers, LeetCode prep
- **Atiyeh**: Executive coaching, leadership
- **Anna**: Design, marketing careers
- **Dimitri**: QA, career strategy

### Pricing
- Main service: $1,000/month coaching
- Custom packages available

## Development Workflow 💻

### Local Development
```bash
# Start server with hot reload
uvicorn src.main:app --reload

# Run tests on file change
pytest-watch

# View logs in real-time
pm2 logs career-flow-api --lines 50
```

### Production Deployment
```bash
# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 config
pm2 save

# Setup auto-start on reboot
pm2 startup

# View dashboard
./scripts/dashboard.sh
```

### Automation Setup
```bash
# Install cron job for daily analysis
crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * /Users/serber/Documents/Engineering/Repositories/career-flow-ai-agent/scripts/auto-analyze.sh >> /Users/serber/Documents/Engineering/Repositories/career-flow-ai-agent/analysis_reports/cron.log 2>&1
```

## Configuration ⚙️

### Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./career_flow.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/career_flow_db

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### PM2 Configuration

See `ecosystem.config.js` for:
- Auto-restart on crash
- Memory limit monitoring
- Log file configuration
- Environment variables

## Monitoring & Analytics 📊

### Available Scripts

```bash
# System status
./scripts/dashboard.sh

# Run analysis
./scripts/auto-analyze.sh

# View recommendations
./scripts/view-recommendations.sh

# Analyze conversations
./scripts/analyze-conversations.sh

# Compare reports over time
./scripts/compare-reports.sh

# Health check
./scripts/health-check.sh
```

### Analysis Reports

Generated daily and saved to `analysis_reports/`:
- Timestamped JSON files
- Pattern detection results
- AI-generated recommendations
- Confidence scoring
- Sample conversations

### Metrics Tracked

- Total conversations
- Average duration
- Issue detection rates
- User engagement
- Transfer success rates
- Name collection rates

## Future Roadmap 🔮

See [CODE_SAMPLE.md](CODE_SAMPLE.md) for detailed roadmap including:

**Phase 1:** Intelligent sampling, real-time alerts, sentiment analysis

**Phase 2:** A/B testing, multi-model analysis, voice tone analysis

**Phase 3:** PostgreSQL migration, async queue, analytics dashboard

**Phase 4:** Predictive analytics, automated tuning, benchmarking

## Documentation 📚

- **[CODE_SAMPLE.md](CODE_SAMPLE.md)** - Technical deep-dive (⭐ start here for interview)
- **[API Docs](http://localhost:8000/docs)** - Interactive Swagger UI
- **[ReDoc](http://localhost:8000/redoc)** - Alternative API documentation

## Contributing 🤝

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new features
4. Ensure tests pass (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## Support 💬

**For LG NOVA Interview Questions:**
- See [CODE_SAMPLE.md](CODE_SAMPLE.md) for technical details
- Contact: acakic92@gmail.com
- LinkedIn: https://www.linkedin.com/in/aleksandar-cakic/

**For General Issues:**
- Open an issue on GitHub
- Email: support@career-flow.com
- Website: https://www.career-flow.com/

## License 📄

This project is licensed under the MIT License.

## Acknowledgments 🙏

- **OpenAI** for GPT-4o-mini (voice + analysis)
- **Twilio** for voice infrastructure
- **FastAPI** for the excellent web framework
- **SQLAlchemy** for database ORM
- **LG NOVA** for the interview opportunity

---

**Built with ❤️ for Career Flow**

**For technical interview:** Start with [CODE_SAMPLE.md](CODE_SAMPLE.md) 📄