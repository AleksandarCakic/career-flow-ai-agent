#!/bin/bash
# Human-readable conversation transcript viewer

echo "════════════════════════════════════════════════════════════"
echo "           📞 CONVERSATION ANALYSIS REPORT"
echo "════════════════════════════════════════════════════════════"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Fetch conversations from API
API_URL="http://localhost:8000/analytics/conversations"
RESPONSE=$(curl -s "$API_URL?limit=10")

# Check if response is valid
if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo "❌ Error: Could not fetch conversations"
    exit 1
fi

# Parse overview stats
TOTAL=$(echo "$RESPONSE" | jq -r '.total_conversations // 0')
USERS=$(echo "$RESPONSE" | jq -r '.unique_users // 0')
AVG_MESSAGES=$(echo "$RESPONSE" | jq -r '.avg_messages_per_conversation // "N/A"')

echo "📊 OVERVIEW"
echo "────────────────────────────────────────────────────────────"
echo "Total Conversations: $TOTAL"
echo "Total Users: $USERS"
echo "Avg Messages per Conversation: $AVG_MESSAGES"
echo ""
echo ""

# Loop through conversations
echo "$RESPONSE" | jq -c '.conversations[]?' | while IFS= read -r conv; do
    # Parse conversation details
    call_sid=$(echo "$conv" | jq -r '.call_sid')
    phone=$(echo "$conv" | jq -r '.phone_number')
    status=$(echo "$conv" | jq -r '.status')
    duration=$(echo "$conv" | jq -r '.duration_seconds')
    started=$(echo "$conv" | jq -r '.started_at')
    
    # Count messages by role
    user_count=$(echo "$conv" | jq '[.messages[]? | select(.role == "USER")] | length')
    assistant_count=$(echo "$conv" | jq '[.messages[]? | select(.role == "ASSISTANT")] | length')
    system_count=$(echo "$conv" | jq '[.messages[]? | select(.role == "SYSTEM")] | length')
    
    # Print conversation header
    echo "════════════════════════════════════════════════════════════"
    echo "🔵 CONVERSATION #$((++counter))"
    echo "════════════════════════════════════════════════════════════"
    echo "Call SID:    $call_sid"
    echo "Phone:       $phone"
    echo "Status:      $status"
    echo "Duration:    ${duration}s"
    echo "Started:     $started"
    echo ""
    
    echo "📈 Message Breakdown:"
    echo "   👤 User:      $user_count messages"
    echo "   🤖 Assistant: $assistant_count messages"
    echo "   ⚙️  System:    $system_count messages"
    echo ""
    
    # Print transcript
    echo "💬 CONVERSATION TRANSCRIPT:"
    echo "────────────────────────────────────────────────────────────"
    
    echo "$conv" | jq -r '.messages[]? | 
        if .role == "USER" then
            "   👤 USER: \(.content)"
        elif .role == "ASSISTANT" then
            "   🤖 MICA: \(.content)"
        elif .role == "SYSTEM" then
            "   ⚙️  SYSTEM: \(.content)"
        else
            "   ❓ \(.role): \(.content)"
        end'
    
    echo ""
    
    # Issue detection
    echo "🔍 ISSUE DETECTION:"
    echo "────────────────────────────────────────────────────────────"
    
    # Check for name collection
    has_name=$(echo "$conv" | jq -r '[.messages[]? | select(.role == "USER" and (.content | test("name is|i'\''m|im|this is|call me"; "i")))] | length > 0')
    asked_name=$(echo "$conv" | jq -r '[.messages[]? | select(.role == "ASSISTANT" and (.content | test("name"; "i")))] | length > 0')
    
    if [ "$asked_name" == "true" ] && [ "$has_name" == "false" ] && [ "$user_count" -gt 2 ]; then
        echo "   ⚠️  Name not collected after $user_count exchanges"
    elif [ "$has_name" == "true" ]; then
        echo "   ✅ Name collected successfully"
    fi
    
    # Check for technical errors
    has_error=$(echo "$conv" | jq -r '[.messages[]? | select(.content | test("error|hiccup|technical|problem|unintelligible"; "i"))] | length')
    if [ "$has_error" -gt 0 ]; then
        echo "   ⚠️  Technical Errors: $has_error occurrences"
    fi
    
    # Check for transfer issues
    has_transfer_request=$(echo "$conv" | jq -r '[.messages[]? | select(.role == "ASSISTANT" and (.content | test("transfer|connect"; "i")))] | length > 0')
    has_transfer_failure=$(echo "$conv" | jq -r '[.messages[]? | select(.role == "SYSTEM" and (.content | test("not executed|failed"; "i")))] | length > 0')
    
    if [ "$has_transfer_request" == "true" ] && [ "$has_transfer_failure" == "true" ]; then
        echo "   ⚠️  Transfer requested but not executed"
    fi
    
    # Check for multiple questions
    multi_questions=$(echo "$conv" | jq -r '[.messages[]? | select(.role == "USER" and (.content | gsub("\\?"; "?") | split("?") | length) >= 3)] | length')
    if [ "$multi_questions" -gt 0 ]; then
        echo "   ⚠️  Multiple questions in single message: $multi_questions occurrences"
    fi
    
    # If no issues
    total_messages=$((user_count + assistant_count + system_count))
    if [ "$has_name" == "true" ] && [ "$has_error" -eq 0 ] && [ "$has_transfer_failure" == "false" ] && [ "$multi_questions" -eq 0 ]; then
        echo "   ✅ No issues detected - clean conversation!"
    fi
    
    echo ""
    echo ""
done

# Next Steps
echo "════════════════════════════════════════════════════════════"
echo "📋 NEXT STEPS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1. View AI recommendations:"
echo "   ./scripts/view-recommendations.sh"
echo ""
echo "2. Debug pattern detection:"
echo "   python scripts/debug-detection.py"
echo ""
echo "3. Run full analysis:"
echo "   ./scripts/auto-analyze.sh"
echo ""
echo "4. Reseed with fresh data:"
echo "   python scripts/seed_sample_data.py"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""