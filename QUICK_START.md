# Quick Start Guide 🚀

> **👔 Interview Demo:** See [CODE_SAMPLE.md](CODE_SAMPLE.md) for technical deep-dive | [README.md](README.md) for complete details
> **5-minute setup** to demo the AI-powered conversation analysis system

## Prerequisites

- Python 3.13+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Twilio account (optional - can demo without it)

## Setup

```bash
# 1. Clone & install
git clone https://github.com/AleksandarCakic/career-flow-ai-agent.git
cd career-flow-ai-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Initialize database
python -c "from src.database import init_db; init_db()"

# 4. Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify Setup

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected"}
```

## Quick Demo ⚡

**See the AI analysis in action (no Twilio needed):**

```bash
# 1. Seed sample conversations
python scripts/seed_sample_data.py

# 2. Run AI analysis
./scripts/auto-analyze.sh

# 3. View recommendations
./scripts/view-recommendations.sh

# 4. View transcripts
./scripts/analyze-conversations.sh
```

**What you'll see:**
- ✅ 5 conversations with known issues seeded
- ✅ Pattern detection identifies 4-5 issues
- ✅ GPT-4o-mini generates specific fixes
- ✅ Confidence scoring (HIGH/MEDIUM/LOW)
- ✅ Full transcripts with issue highlighting

## Test API Endpoints

### Core Analysis
```bash
# Run analysis (last 7 days)
curl -s -X POST "http://localhost:8000/admin/analyze-conversations?hours=168" | jq .

# View detected issues
curl -s -X POST "http://localhost:8000/admin/analyze-conversations?hours=168" | jq '.summary.issues_found'

# View AI recommendations
curl -s -X POST "http://localhost:8000/admin/analyze-conversations?hours=168" | jq '.ai_recommendations.recommendations'
```

### Conversations
```bash
# Get all conversations
curl -s http://localhost:8000/analytics/conversations | jq '.conversations[] | {call_sid, duration_seconds, messages: (.messages | length)}'

# Get specific conversation
curl -s http://localhost:8000/analytics/conversations/call/CA_sample_001 | jq .

# Get stats
curl -s http://localhost:8000/analytics/stats | jq .
```

### Users
```bash
# Get all users
curl -s http://localhost:8000/analytics/users | jq '.users[] | {phone_number, first_name, last_call_at}'

# Get user by phone
curl -s http://localhost:8000/analytics/users/+15551234567 | jq .

# Get user's conversations
curl -s http://localhost:8000/analytics/users/+15551234567/conversations | jq '.conversations[] | {call_sid, started_at}'
```

### Power Commands
```bash
# Quick summary
curl -s -X POST "http://localhost:8000/admin/analyze-conversations?hours=168" | jq '{total: .summary.total_conversations, issues: .summary.issues_found}'

# Find longest conversation
curl -s http://localhost:8000/analytics/conversations | jq '[.conversations[] | {call_sid, duration_seconds, messages: (.messages | length)}] | max_by(.duration_seconds)'

# Conversations in last 24h
curl -s http://localhost:8000/analytics/conversations | jq --arg date "$(date -u -v-24H +%Y-%m-%d)" '.conversations[] | select(.started_at >= $date)'
```

## Demo With Voice (Optional)

**Test the full Twilio voice agent:**

1. **Setup Twilio webhook:**
   ```bash
   # Start ngrok for local testing
   ngrok http 8000
   
   # Configure Twilio webhook to:
   # http://your-ngrok-url/webhooks/twilio/voice
   ```

2. **Call your Twilio number** - Talk to Mica AI

3. **Analyze the call:**
   ```bash
   ./scripts/auto-analyze.sh
   ./scripts/view-recommendations.sh
   ```

## What to Explore

**Core Analysis Engine:**
- `src/services/prompt_optimizer_service.py` - Two-phase AI analysis
- `src/api/routes/admin.py` - Analysis endpoints

**Sample Data:**
- Conversation 1: Perfect (name collected, clean)
- Conversation 2: Missing name
- Conversation 3: Transfer failure
- Conversation 4: Technical error
- Conversation 5: Long + multiple questions

**Scripts:**
- `scripts/auto-analyze.sh` - Automated analysis
- `scripts/view-recommendations.sh` - Formatted recommendations
- `scripts/analyze-conversations.sh` - Full transcripts
- `scripts/debug-detection.py` - Debug pattern detection

## Troubleshooting

**Module not found:**
```bash
pip install -r requirements.txt
```

**Database error:**
```bash
python -c "from src.database import init_db; init_db()"
```

**OpenAI API error:**
- Check API key in `.env`
- Verify credits at https://platform.openai.com/usage

**No conversations:**
```bash
python scripts/seed_sample_data.py
```

## Next Steps

📚 **Deep dive:** See [CODE_SAMPLE.md](CODE_SAMPLE.md) for architecture details

🏗️ **Production:** See [README.md](README.md#production-deployment-) for PM2 setup

🧪 **Tests:** Run `pytest` to see 63 passing tests

## Contact

Questions? acakic92@gmail.com | [LinkedIn](https://www.linkedin.com/in/aleksandar-cakic/)

---

**Built for Career Flow** | [www.career-flow.com](https://www.career-flow.com/)