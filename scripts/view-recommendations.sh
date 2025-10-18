#!/bin/bash
# View the latest AI recommendations in a formatted way

# Find the latest report
LATEST_REPORT=$(ls -t analysis_reports/report_*.json 2>/dev/null | head -1)

if [ -z "$LATEST_REPORT" ]; then
    echo "❌ No analysis reports found"
    echo "Run ./scripts/auto-analyze.sh first"
    exit 1
fi

# Extract report name and timestamp
REPORT_NAME=$(basename "$LATEST_REPORT")
TIMESTAMP=$(cat "$LATEST_REPORT" | jq -r '.timestamp // empty')

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Header
echo ""
echo "════════════════════════════════════════════════════════════"
echo "        🤖 AI RECOMMENDATIONS & INSIGHTS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📄 Latest Report: $REPORT_NAME"
echo "📅 Generated: $TIMESTAMP"
echo ""

# Summary Section
echo "════════════════════════════════════════════════════════════"
echo "📊 ANALYSIS SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

TOTAL_CONVS=$(cat "$LATEST_REPORT" | jq -r '.summary.total_conversations // 0')
HOURS_BACK=$(cat "$LATEST_REPORT" | jq -r '.analysis_period.hours_back // 168')

echo "Analyzed: $TOTAL_CONVS conversations"
echo "Period: last $HOURS_BACK hours"
echo ""

# Issues Found
echo "🔍 ISSUES DETECTED:"
echo "────────────────────────────────────────────────────────────"

# Parse each issue type
for issue_type in "technical_errors" "transfer_failures" "multiple_questions" "long_conversations" "name_not_collected"; do
    count=$(cat "$LATEST_REPORT" | jq -r ".summary.issues_found.$issue_type // 0")
    display_name=$(echo "$issue_type" | tr '_' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')
    
    if [ "$count" -gt 0 ]; then
        echo "   ❌ ${display_name^^}: $count occurrence(s)"
    else
        echo "   ✅ ${display_name^^}: None"
    fi
done
echo ""

# AI Recommendations Section
echo "════════════════════════════════════════════════════════════"
echo "🤖 AI-GENERATED RECOMMENDATIONS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Critical Issues
CRITICAL=$(cat "$LATEST_REPORT" | jq -r '.ai_recommendations.critical_issues[]? // empty')
if [ ! -z "$CRITICAL" ]; then
    echo "🔴 CRITICAL ISSUES:"
    echo "────────────────────────────────────────────────────────────"
    cat "$LATEST_REPORT" | jq -r '.ai_recommendations.critical_issues[]?' | while read issue; do
        echo "   • $issue"
    done
    echo ""
fi

# Confidence Level
CONFIDENCE=$(cat "$LATEST_REPORT" | jq -r '.ai_recommendations.confidence // "N/A"')
echo "📊 AI Confidence Level: $CONFIDENCE"
echo ""

# Detailed Recommendations
echo "════════════════════════════════════════════════════════════"
echo "💡 DETAILED RECOMMENDATIONS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Parse recommendations
cat "$LATEST_REPORT" | jq -c '.ai_recommendations.recommendations[]?' | while read rec; do
    issue=$(echo "$rec" | jq -r '.issue')
    suggestion=$(echo "$rec" | jq -r '.suggestion')
    rationale=$(echo "$rec" | jq -r '.rationale')
    
    echo "────────────────────────────────────────────────────────────"
    echo "🎯 ISSUE: $issue"
    echo ""
    echo "💡 Suggested Fix:"
    echo "   $(echo "$suggestion" | fold -s -w 60 | sed '2,$s/^/   /')"
    echo ""
    echo "✅ Why This Helps:"
    echo "   $(echo "$rationale" | fold -s -w 60 | sed '2,$s/^/   /')"
    echo ""
done

# Sample Conversations
echo "════════════════════════════════════════════════════════════"
echo "📞 SAMPLE CONVERSATIONS ANALYZED"
echo "════════════════════════════════════════════════════════════"
echo ""

cat "$LATEST_REPORT" | jq -c '.summary.sample_conversations[]?' | head -5 | while IFS= read -r conv; do
    call_sid=$(echo "$conv" | jq -r '.call_sid')
    duration=$(echo "$conv" | jq -r '.duration_seconds')
    
    # Simple counter for numbering
    num=$((num + 1))
    printf "   [%03d] %s\n" "$num" "$call_sid"
    echo "       Duration: ${duration}s"
done
echo ""

# Detailed Issue Breakdown
echo "════════════════════════════════════════════════════════════"
echo "🔍 DETAILED ISSUE BREAKDOWN"
echo "════════════════════════════════════════════════════════════"
echo ""

# Technical Errors
tech_count=$(cat "$LATEST_REPORT" | jq '.issues.technical_errors | length')
if [ "$tech_count" -gt 0 ]; then
    echo "⚠️  TECHNICAL ERRORS ($tech_count found):"
    cat "$LATEST_REPORT" | jq -r '.issues.technical_errors[]? | "   • \(.call_sid): \(.message[0:50])..."'
    echo ""
fi

# Transfer Failures
transfer_count=$(cat "$LATEST_REPORT" | jq '.issues.transfer_failures | length')
if [ "$transfer_count" -gt 0 ]; then
    echo "⚠️  TRANSFER FAILURES ($transfer_count found):"
    cat "$LATEST_REPORT" | jq -r '.issues.transfer_failures[]? | "   • \(.call_sid): \(.system_message)"'
    echo ""
fi

# Multiple Questions
multi_q_count=$(cat "$LATEST_REPORT" | jq '.issues.multiple_questions | length')
if [ "$multi_q_count" -gt 0 ]; then
    echo "⚠️  MULTIPLE QUESTIONS ($multi_q_count found):"
    cat "$LATEST_REPORT" | jq -r '.issues.multiple_questions[]? | "   • \(.call_sid): \(.num_questions) questions in one message"'
    echo ""
fi

# Long Conversations
long_count=$(cat "$LATEST_REPORT" | jq '.issues.long_conversations | length')
if [ "$long_count" -gt 0 ]; then
    echo "⚠️  LONG CONVERSATIONS ($long_count found):"
    cat "$LATEST_REPORT" | jq -r '.issues.long_conversations[]? | "   • \(.call_sid): \(.num_messages) messages (\(.duration_seconds)s)"'
    echo ""
fi

# Name Not Collected
name_count=$(cat "$LATEST_REPORT" | jq '.issues.name_not_collected | length')
if [ "$name_count" -gt 0 ]; then
    echo "⚠️  NAME NOT COLLECTED ($name_count found):"
    cat "$LATEST_REPORT" | jq -r '.issues.name_not_collected[]? | "   • \(.call_sid): \(.num_user_messages) messages without name"'
    echo ""
fi

# Next Steps
echo "════════════════════════════════════════════════════════════"
echo "📋 NEXT STEPS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1. View conversation transcripts:"
echo "   ./scripts/analyze-conversations.sh"
echo ""
echo "2. Debug pattern detection:"
echo "   python scripts/debug-detection.py"
echo ""
echo "3. Update system prompt based on recommendations:"
echo "   Edit: src/services/voice_service.py"
echo ""
echo "4. Re-run analysis after changes:"
echo "   ./scripts/auto-analyze.sh"
echo ""
echo "5. Reseed with fresh data:"
echo "   python scripts/seed_sample_data.py"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""