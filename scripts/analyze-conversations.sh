#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "           📞 CONVERSATION ANALYSIS REPORT"
echo "════════════════════════════════════════════════════════════"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Get overall stats first
STATS=$(curl -s "http://localhost:8000/analytics/stats")
TOTAL_CONVS=$(echo $STATS | jq -r '.total_conversations')
TOTAL_USERS=$(echo $STATS | jq -r '.total_users')
AVG_MSGS=$(echo $STATS | jq -r '.avg_messages_per_conversation')

echo "📊 OVERVIEW"
echo "────────────────────────────────────────────────────────────"
echo "Total Conversations: $TOTAL_CONVS"
echo "Total Users: $TOTAL_USERS"
echo "Avg Messages per Conversation: $AVG_MSGS"
echo ""
echo ""

# Analyze last 3 conversations
for i in 0 1 2; do
  CONV=$(curl -s "http://localhost:8000/analytics/conversations?skip=$i&limit=1" | jq '.conversations[0]')
  
  if [ "$CONV" = "null" ]; then
    break
  fi
  
  CONV_ID=$(echo $CONV | jq -r '.id')
  CALL_SID=$(echo $CONV | jq -r '.call_sid')
  PHONE=$(echo $CONV | jq -r '.phone_number')
  STATUS=$(echo $CONV | jq -r '.status')
  DURATION=$(echo $CONV | jq -r '.duration_seconds // "N/A"')
  STARTED=$(echo $CONV | jq -r '.started_at')
  
  echo "════════════════════════════════════════════════════════════"
  echo "🔵 CONVERSATION #$((i+1))"
  echo "════════════════════════════════════════════════════════════"
  echo "Call SID:    $CALL_SID"
  echo "Phone:       $PHONE"
  echo "Status:      $STATUS"
  echo "Duration:    ${DURATION}s"
  echo "Started:     $STARTED"
  echo ""
  
  # Get messages
  MESSAGES=$(curl -s "http://localhost:8000/analytics/conversations/$CONV_ID/messages" | jq -r '.messages')
  
  # Count messages by role
  USER_COUNT=$(echo $MESSAGES | jq '[.[] | select(.role == "USER")] | length')
  ASSISTANT_COUNT=$(echo $MESSAGES | jq '[.[] | select(.role == "ASSISTANT")] | length')
  SYSTEM_COUNT=$(echo $MESSAGES | jq '[.[] | select(.role == "SYSTEM")] | length')
  
  echo "📈 Message Breakdown:"
  echo "   👤 User:      $USER_COUNT messages"
  echo "   🤖 Assistant: $ASSISTANT_COUNT messages"
  echo "   ⚙️  System:    $SYSTEM_COUNT messages"
  echo ""
  
  # Show conversation transcript
  echo "💬 CONVERSATION TRANSCRIPT:"
  echo "────────────────────────────────────────────────────────────"
  
  # Format messages nicely
  echo "$MESSAGES" | jq -r '.[] | 
    if .role == "USER" then
      "👤 USER: \(.content)"
    elif .role == "ASSISTANT" then
      "🤖 MICA: \(.content)"
    else
      "⚙️  SYSTEM: \(.content)"
    end' | sed 's/^/   /'
  
  echo ""
  
  # Analyze issues
  echo "🔍 ISSUE DETECTION:"
  echo "────────────────────────────────────────────────────────────"
  
  ISSUES_FOUND=0
  
  # Check for technical hiccups
  HICCUP_COUNT=$(echo $MESSAGES | jq '[.[] | select(.content | contains("technical hiccup"))] | length')
  if [ "$HICCUP_COUNT" -gt 0 ]; then
    echo "   ⚠️  Technical Errors: $HICCUP_COUNT occurrences"
    ISSUES_FOUND=1
  fi
  
  # Check for repeated errors
  ERROR_COUNT=$(echo $MESSAGES | jq '[.[] | select(.content | contains("encountered an error"))] | length')
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "   ⚠️  Repeated Errors: $ERROR_COUNT occurrences"
    ISSUES_FOUND=1
  fi
  
  # Check for profanity in name
  if echo $MESSAGES | jq -e '.[] | select(.role == "ASSISTANT" and (.content | contains("Stupid")))' > /dev/null 2>&1; then
    echo "   ⚠️  Profanity detected in greeting"
    ISSUES_FOUND=1
  fi
  
  # Check for multiple questions at once
  MULTI_Q=$(echo $MESSAGES | jq '[.[] | select(.role == "ASSISTANT" and ((.content | contains("1.")) and (.content | contains("2."))))] | length')
  if [ "$MULTI_Q" -gt 0 ]; then
    echo "   ⚠️  Multiple questions at once: $MULTI_Q instances"
    ISSUES_FOUND=1
  fi
  
  # Check for transfer requests
  TRANSFER_REQ=$(echo $MESSAGES | jq '[.[] | select(.role == "USER" and (.content | test("connect|transfer|human|speak to"; "i")))] | length')
  if [ "$TRANSFER_REQ" -gt 0 ]; then
    TRANSFER_HANDLED=$(echo $MESSAGES | jq '[.[] | select(.role == "ASSISTANT" and (.content | test("connecting|connect you|dial"; "i")))] | length')
    if [ "$TRANSFER_HANDLED" -eq 0 ]; then
      echo "   ⚠️  Transfer requested but not handled ($TRANSFER_REQ requests)"
      ISSUES_FOUND=1
    else
      echo "   ✅ Transfer handled successfully"
    fi
  fi
  
  # Check for name collection
  HAS_NAME=$(echo $MESSAGES | jq -e '.[] | select(.role == "USER" and (.content | test("my name is|i'\''m |call me"; "i")))' > /dev/null 2>&1 && echo "yes" || echo "no")
  NAME_ASKED=$(echo $MESSAGES | jq -e '.[] | select(.role == "ASSISTANT" and (.content | test("what'\''s your name|your name"; "i")))' > /dev/null 2>&1 && echo "yes" || echo "no")
  
  if [ "$HAS_NAME" = "no" ] && [ "$USER_COUNT" -gt 3 ]; then
    echo "   ⚠️  Name not collected after $USER_COUNT exchanges"
    ISSUES_FOUND=1
  elif [ "$HAS_NAME" = "yes" ]; then
    echo "   ✅ Name collected successfully"
  fi
  
  # Check conversation length
  if [ "$USER_COUNT" -gt 10 ]; then
    echo "   ⚠️  Long conversation: $USER_COUNT user messages (may indicate confusion)"
    ISSUES_FOUND=1
  fi
  
  if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo "   ✅ No issues detected - clean conversation!"
  fi
  
  echo ""
  echo ""
done

echo "════════════════════════════════════════════════════════════"
echo "📋 RECOMMENDATIONS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "For AI-powered improvement suggestions, run:"
echo "   ./scripts/auto-analyze.sh"
echo ""
echo "For detailed AI recommendations, run:"
echo "   ./scripts/view-recommendations.sh"
echo ""
echo "════════════════════════════════════════════════════════════"