# Career Flow AI Agent 🎯

> **👔 Interview Demo:** See [QUICK_START.md](QUICK_START.md) for 5-minute setup | [CODE_SAMPLE.md](CODE_SAMPLE.md) for technical deep-dive

AI-powered voice assistant for career coaching with automated conversation quality monitoring, used by Career-Flow platform (www.career-flow.com)

## What It Does ✨

**Mica Voice Agent** - Handles phone calls, qualifies leads, matches coaches, schedules sessions

**AI Quality Analysis** - Automatically detects conversation issues and generates improvement recommendations using GPT-4o-mini

## Tech Stack 🛠️

FastAPI · Python 3.13 · OpenAI GPT-4o-mini · Twilio · PostgreSQL · PM2 · Pytest

## Quick Start 🚀

```bash
# Setup
git clone https://github.com/AleksandarCakic/career-flow-ai-agent.git
cd career-flow-ai-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# Run
pm2 start ecosystem.config.js

# Demo Analysis
python scripts/seed_sample_data.py
./scripts/auto-analyze.sh
./scripts/view-recommendations.sh
```

**Full setup:** [QUICK_START.md](QUICK_START.md) | **Architecture:** [CODE_SAMPLE.md](CODE_SAMPLE.md)

## Project Structure 📁

```
src/
├── api/routes/          # Webhooks, analytics, admin endpoints
├── services/            # Voice agent, analytics, AI analysis
├── models/              # Database models (users, conversations, messages)
└── main.py              # FastAPI app

scripts/
├── auto-analyze.sh      # Run AI analysis
├── view-recommendations.sh
├── analyze-conversations.sh
└── seed_sample_data.py  # Demo data

tests/                   # 63 passing tests
analysis_reports/        # AI-generated insights
```

## Key Features 🎯

### AI Conversation Analysis
- **Pattern Detection**: Technical errors, transfer failures, multiple questions, long conversations, missing name collection
- **GPT-4o-mini Recommendations**: Actionable improvements with confidence scoring
- **Cost Optimized**: ~$1-3/month for 100 conversations via intelligent sampling

### Voice Agent (Mica)
- Real-time phone conversations via Twilio
- User recognition and personalization
- Coach matching and scheduling
- Lead qualification

### Production Ready
- 24/7 uptime with PM2
- Automated daily analysis (cron)
- Comprehensive test coverage
- PostgreSQL-ready architecture

## API Endpoints 📡

```bash
# Analysis
POST /admin/analyze-conversations?hours=168

# Analytics  
GET /analytics/conversations
GET /analytics/stats
GET /analytics/users/{phone}

# Voice Webhooks
POST /webhooks/twilio/voice
POST /webhooks/twilio/process-speech

# Health
GET /health
```

**Interactive docs:** http://localhost:8000/docs

## Testing 🧪

```bash
pytest                    # Run all tests (63 passing)
pytest --cov=src          # With coverage
./scripts/health-check.sh # System validation
```

## Configuration ⚙️

```env
# .env
OPENAI_API_KEY=sk-proj-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
DATABASE_URL=sqlite:///./career_flow.db  # or postgresql://...
```

## Documentation 📚

- **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide with curl commands
- **[CODE_SAMPLE.md](CODE_SAMPLE.md)** - Technical architecture and design decisions
- **[API Docs](http://localhost:8000/docs)** - Interactive Swagger UI

## Monitoring Scripts 📊

```bash
./scripts/dashboard.sh              # System status
./scripts/auto-analyze.sh           # Run AI analysis
./scripts/view-recommendations.sh   # View AI suggestions
./scripts/analyze-conversations.sh  # View transcripts
```

## Production Deployment 🚀

```bash
# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Setup automated analysis (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /path/to/scripts/auto-analyze.sh >> /path/to/analysis_reports/cron.log 2>&1
```

## Database Schema 🗄️

**Users** - Phone numbers, names, conversation history, preferences

**Conversations** - Call tracking (call_sid), status, duration, timestamps

**Messages** - Full transcripts with role (user/assistant/system)

**Migrations** - Alembic for schema management

## Contact 💬

**Interview Questions:** acakic92@gmail.com | [LinkedIn](https://www.linkedin.com/in/aleksandar-cakic/)

**General:** support@career-flow.com | [career-flow.com](https://www.career-flow.com/)

---

**Built with ❤️ for Career Flow** | MIT License

**Interview Ready:** [QUICK_START.md](QUICK_START.md) → [CODE_SAMPLE.md](CODE_SAMPLE.md) 🎯