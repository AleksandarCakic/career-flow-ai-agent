#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "        🤖 AI RECOMMENDATIONS & INSIGHTS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Find the latest report
LATEST=$(ls -t analysis_reports/report_*.json 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "❌ No analysis reports found!"
    echo ""
    echo "Run this first to generate a report:"
    echo "   ./scripts/auto-analyze.sh"
    echo ""
    exit 1
fi

REPORT_DATE=$(basename "$LATEST" | sed 's/report_\(.*\)\.json/\1/')
echo "📄 Latest Report: $(basename $LATEST)"
echo "📅 Generated: $(echo $REPORT_DATE | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)_\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')"
echo ""

# Check if report has data
STATUS=$(cat "$LATEST" | jq -r '.analysis.status')

if [ "$STATUS" != "analyzed" ]; then
    echo "⚠️  Report Status: $STATUS"
    echo ""
    if [ "$STATUS" = "insufficient_data" ]; then
        COUNT=$(cat "$LATEST" | jq -r '.analysis.count // 0')
        echo "Only $COUNT conversation(s) found."
        echo "Need more conversations for meaningful analysis."
    fi
    echo ""
    exit 0
fi

# Display analysis summary
echo "════════════════════════════════════════════════════════════"
echo "📊 ANALYSIS SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

TOTAL_CONVS=$(cat "$LATEST" | jq -r '.analysis.total_conversations')
PERIOD=$(cat "$LATEST" | jq -r '.analysis.period')

echo "Analyzed: $TOTAL_CONVS conversations"
echo "Period: $PERIOD"
echo ""

# Display issues
echo "🔍 ISSUES DETECTED:"
echo "────────────────────────────────────────────────────────────"

cat "$LATEST" | jq -r '.analysis.issues | to_entries[] | 
    if .value > 0 then
        "   ❌ \(.key | gsub("_"; " ") | ascii_upcase): \(.value) occurrence(s)"
    else
        "   ✅ \(.key | gsub("_"; " ") | ascii_upcase): None"
    end'

echo ""

# Check if improvements were generated
IMPROVEMENTS_STATUS=$(cat "$LATEST" | jq -r '.improvements.status')

if [ "$IMPROVEMENTS_STATUS" != "improvements_generated" ]; then
    echo "⚠️  No AI recommendations available"
    echo ""
    exit 0
fi

# Display AI recommendations
echo "════════════════════════════════════════════════════════════"
echo "🤖 AI-GENERATED RECOMMENDATIONS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if improvements is a string or object
IMPROVEMENTS_TYPE=$(cat "$LATEST" | jq -r '.improvements.improvements | type')

if [ "$IMPROVEMENTS_TYPE" = "string" ]; then
    # It's a JSON string, parse it
    IMPROVEMENTS=$(cat "$LATEST" | jq -r '.improvements.improvements | fromjson')
else
    # It's already an object
    IMPROVEMENTS=$(cat "$LATEST" | jq '.improvements.improvements')
fi

# Display critical issues
echo "🔴 CRITICAL ISSUES:"
echo "────────────────────────────────────────────────────────────"
echo "$IMPROVEMENTS" | jq -r '.critical_issues[]? | "   • \(.)"'
echo ""

# Display confidence level
CONFIDENCE=$(echo "$IMPROVEMENTS" | jq -r '.confidence // "unknown"')
echo "📊 AI Confidence Level: $(echo $CONFIDENCE | tr '[:lower:]' '[:upper:]')"
echo ""

# Display detailed recommendations
echo "════════════════════════════════════════════════════════════"
echo "💡 DETAILED RECOMMENDATIONS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Count total improvements
IMPROVEMENT_COUNT=$(echo "$IMPROVEMENTS" | jq '.improvements | length')

if [ "$IMPROVEMENT_COUNT" = "null" ] || [ "$IMPROVEMENT_COUNT" = "0" ]; then
    echo "   No specific recommendations available"
    echo ""
else
    for i in $(seq 0 $(($IMPROVEMENT_COUNT - 1))); do
        echo "────────────────────────────────────────────────────────────"
        ISSUE=$(echo "$IMPROVEMENTS" | jq -r ".improvements[$i].issue")
        SUGGESTION=$(echo "$IMPROVEMENTS" | jq -r ".improvements[$i].suggestion")
        REASONING=$(echo "$IMPROVEMENTS" | jq -r ".improvements[$i].reasoning")
        
        echo "🎯 ISSUE #$((i+1)): $ISSUE"
        echo ""
        echo "💡 Suggested Fix:"
        echo "$SUGGESTION" | fold -s -w 72 | sed 's/^/   /'
        echo ""
        echo "✅ Why This Helps:"
        echo "$REASONING" | fold -s -w 72 | sed 's/^/   /'
        echo ""
    done
fi

# Display sample conversations summary
echo "════════════════════════════════════════════════════════════"
echo "📞 SAMPLE CONVERSATIONS ANALYZED"
echo "════════════════════════════════════════════════════════════"
echo ""

SAMPLE_COUNT=$(cat "$LATEST" | jq '.analysis.conversation_samples | length')

for i in $(seq 0 $(($SAMPLE_COUNT - 1))); do
    CALL_SID=$(cat "$LATEST" | jq -r ".analysis.conversation_samples[$i].call_sid")
    EXCHANGES=$(cat "$LATEST" | jq -r ".analysis.conversation_samples[$i].exchanges")
    DURATION=$(cat "$LATEST" | jq -r ".analysis.conversation_samples[$i].duration // \"N/A\"")
    
    echo "   [$((i+1))] $CALL_SID"
    echo "       Exchanges: $EXCHANGES | Duration: ${DURATION}s"
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📋 NEXT STEPS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1. Review the recommendations above"
echo "2. Update system prompt in: src/services/voice_service.py"
echo "3. Test changes with sample calls"
echo "4. Run analysis again to verify improvements:"
echo "   ./scripts/auto-analyze.sh"
echo ""
echo "For human-readable conversation transcripts:"
echo "   ./scripts/analyze-conversations.sh"
echo ""
echo "To compare with previous reports:"
echo "   ./scripts/compare-reports.sh"
echo ""
echo "════════════════════════════════════════════════════════════"