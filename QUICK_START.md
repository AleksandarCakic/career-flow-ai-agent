## 🎯 For Interviewers: Quick Setup Guide

### Prerequisites
- Python 3.13+
- OpenAI API key
- Twilio account (optional - can demo without it)

### Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/AleksandarCakic/career-flow-ai-agent.git
cd career-flow-ai-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Edit .env with your API keys
# Required:
#   - OPENAI_API_KEY (get from https://platform.openai.com/api-keys)
# Optional (for voice testing):
#   - TWILIO_ACCOUNT_SID (get from https://console.twilio.com/)
#   - TWILIO_AUTH_TOKEN
#   - TWILIO_PHONE_NUMBER
#   - ALEX_PHONE_NUMBER (any phone number for transfer testing)

# 6. Initialize database
python -c "from src.database import init_db; init_db()"

# 7. Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Test It's Working

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "openai": "configured"
}
```

### Quick Demo (No Twilio Required) ⚡

**Fastest way to see the analysis system in action:**

```bash
# 1. Seed sample data (5 conversations with various issues)
python scripts/seed_sample_data.py

# 2. Run analysis
./scripts/auto-analyze.sh

# 3. View AI recommendations
./scripts/view-recommendations.sh

# 4. Explore conversations
./scripts/analyze-conversations.sh
```

**What you'll see:**
- ✅ Pattern detection finds 5 types of issues
- ✅ GPT-4o-mini generates specific recommendations
- ✅ Confidence scoring (high/medium/low)
- ✅ Full conversation transcripts with issue highlighting

### Test API Endpoints 

**Health & Status**
```bash
# Check API health
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/
```

**View Conversations**
```bash
# Get all conversations with messages
curl -s http://localhost:8000/analytics/conversations | jq '.conversations[] | {call_sid, duration_seconds, message_count: (.messages | length)}'

# Get specific conversation by call SID
curl -s http://localhost:8000/analytics/conversations/call/CA_sample_001 | jq .

# Get conversation stats
curl -s http://localhost:8000/analytics/stats | jq .
```

**View Users**
```bash
# Get all users
curl -s http://localhost:8000/analytics/users | jq '.users[] | {phone_number, first_name, last_name, last_call_at, user_data}'

# Get specific user by phone
curl -s http://localhost:8000/analytics/users/+15551234567 | jq .

# Get user's conversation history
curl -s http://localhost:8000/analytics/users/+15551234567/conversations | jq '.conversations[] | {call_sid, started_at, duration_seconds}'
```

### One-Line Power Commands
```bash
# Quick summary: Total conversations and issues
curl -s -X POST "http://localhost:8000/admin/analyze-conversations?hours=168" | jq '{total: .summary.total_conversations, issues: .summary.issues_found}'

# Find the longest conversation
curl -s http://localhost:8000/analytics/conversations | jq '[.conversations[] | {call_sid, duration_seconds, messages: (.messages | length)}] | sort_by(.duration_seconds) | reverse | .[0]'

# Show all conversations from last 24 hours
curl -s http://localhost:8000/analytics/conversations | jq --arg date "$(date -u -v-24H +%Y-%m-%d)" '.conversations[] | select(.started_at >= $date) | {call_sid, started_at}'
```


### Demo With Twilio (Full Experience)

If you want to test the voice agent:

1. **Set up Twilio webhook:**
   - Go to https://console.twilio.com/
   - Buy a phone number
   - Configure webhook URL: `http://your-ngrok-url/webhooks/twilio/voice`
   - Use ngrok for local testing: `ngrok http 8000`

2. **Call your Twilio number** - Talk to Mica AI

3. **Run analysis:**
   ```bash
   ./scripts/auto-analyze.sh
   ```

4. **View AI recommendations:**
   ```bash
   ./scripts/view-recommendations.sh
   ```

### What to Explore

**Core Analysis Engine:**
- `src/services/prompt_optimizer_service.py` - Two-phase analysis logic
- `src/api/routes/admin.py` - Analysis API endpoints

**Automation:**
- `scripts/auto-analyze.sh` - Daily automated analysis
- `ecosystem.config.js` - PM2 production config

**See [CODE_SAMPLE.md](CODE_SAMPLE.md) for detailed walkthrough!**

### Troubleshooting

**"ModuleNotFoundError":**
```bash
pip install -r requirements.txt
```

**"Database not found":**
```bash
python -c "from src.database import init_db; init_db()"
```

**"OpenAI API error":**
- Check your API key in `.env`
- Verify you have credits: https://platform.openai.com/usage

**"Twilio webhook not receiving calls":**
- Use ngrok: `ngrok http 8000`
- Update Twilio webhook URL to ngrok URL

**"No conversations to analyze":**
```bash
# Seed sample data
python scripts/seed_sample_data.py
```

### Questions?

Contact: acakic92@gmail.com