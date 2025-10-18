#!/bin/bash
# Automated conversation analysis script

echo "🔍 Running automated conversation analysis..."
echo "Timestamp: $(date)"
echo ""

# API endpoint
API_URL="http://localhost:8000/admin/analyze-conversations"

# Fetch analysis
echo "Fetching analysis from API..."
RESPONSE=$(curl -s -X POST "$API_URL?hours=168")

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo "❌ Error: Invalid response from API"
    echo "$RESPONSE"
    exit 1
fi

# Get status
STATUS=$(echo "$RESPONSE" | jq -r '.status // "error"')

echo "✅ Analysis complete"

# Save report with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="analysis_reports/report_${TIMESTAMP}.json"
echo "$RESPONSE" | jq . > "$REPORT_FILE"
echo "📄 Report saved: $REPORT_FILE"
echo ""

# Display summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$STATUS" == "no_data" ]; then
    echo "Status: ⚠️  No Data"
    MESSAGE=$(echo "$RESPONSE" | jq -r '.message // "No conversations found"')
    echo "Details: $MESSAGE"
elif [ "$STATUS" == "analyzed" ]; then
    echo "Status: ✅ Success"
    echo "Details:"
    echo "$RESPONSE" | jq '{
        status,
        timestamp,
        analysis_period,
        summary,
        issues,
        ai_recommendations
    }'
else
    echo "Status: ❌ Error"
    echo "Details:"
    echo "$RESPONSE" | jq .
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. View AI recommendations:"
echo "   ./scripts/view-recommendations.sh"
echo ""
echo "2. View conversation transcripts:"
echo "   ./scripts/analyze-conversations.sh"
echo ""
echo "3. Debug pattern detection:"
echo "   python scripts/debug-detection.py"
echo ""
echo "4. Reseed with fresh data:"
echo "   python scripts/seed_sample_data.py"
echo ""
echo "5. Re-run analysis after changes:"
echo "   ./scripts/auto-analyze.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""