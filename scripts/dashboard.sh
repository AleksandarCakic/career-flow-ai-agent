#!/bin/bash

clear
echo "════════════════════════════════════════════════════════════"
echo "        📊 CAREER FLOW AI AGENT - DASHBOARD"
echo "════════════════════════════════════════════════════════════"
echo ""

# Server Status
echo "🖥️  SERVER STATUS"
echo "────────────────────────────────────────────────────────────"
if pm2 status | grep -q "career-flow-api"; then
    STATUS=$(pm2 jlist | jq -r '.[] | select(.name=="career-flow-api") | .pm2_env.status')
    UPTIME=$(pm2 jlist | jq -r '.[] | select(.name=="career-flow-api") | .pm2_env.pm_uptime')
    CPU=$(pm2 jlist | jq -r '.[] | select(.name=="career-flow-api") | .monit.cpu')
    MEMORY=$(pm2 jlist | jq -r '.[] | select(.name=="career-flow-api") | .monit.memory')
    
    # Calculate uptime
    NOW=$(date +%s)
    UPTIME_SECS=$(((NOW - UPTIME / 1000)))
    UPTIME_HOURS=$((UPTIME_SECS / 3600))
    
    echo "Status: ✅ $STATUS"
    echo "Uptime: ${UPTIME_HOURS}h"
    echo "CPU: ${CPU}%"
    echo "Memory: $((MEMORY / 1024 / 1024))MB"
else
    echo "Status: ❌ Not running"
fi
echo ""

# API Health
echo "🏥 API HEALTH"
echo "────────────────────────────────────────────────────────────"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API responding on http://localhost:8000"
    
    # Get stats
    STATS=$(curl -s http://localhost:8000/analytics/stats)
    TOTAL_CONVS=$(echo $STATS | jq -r '.total_conversations')
    TOTAL_USERS=$(echo $STATS | jq -r '.total_users')
    
    echo "Total Conversations: $TOTAL_CONVS"
    echo "Total Users: $TOTAL_USERS"
else
    echo "❌ API not responding"
fi
echo ""

# Cron Status
echo "⏰ AUTOMATION STATUS"
echo "────────────────────────────────────────────────────────────"
if crontab -l 2>/dev/null | grep -q "auto-analyze.sh"; then
    echo "✅ Cron job active (runs daily at 2 AM)"
    echo "Next run: $(date -v+1d -v2H -v0M '+%Y-%m-%d 02:00:00')"
else
    echo "❌ Cron job not configured"
fi
echo ""

# Latest Analysis
echo "📊 LATEST ANALYSIS"
echo "────────────────────────────────────────────────────────────"
LATEST=$(ls -t analysis_reports/report_*.json 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    REPORT_DATE=$(basename "$LATEST" | sed 's/report_\(.*\)\.json/\1/' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)_\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
    AGE=$(($(date +%s) - $(stat -f %m "$LATEST")))
    HOURS=$((AGE / 3600))
    
    STATUS=$(cat "$LATEST" | jq -r '.analysis.status')
    
    echo "Report: $(basename $LATEST)"
    echo "Date: $REPORT_DATE ($HOURS hours ago)"
    echo "Status: $STATUS"
    
    if [ "$STATUS" = "analyzed" ]; then
        TOTAL=$(cat "$LATEST" | jq -r '.analysis.total_conversations')
        ISSUES=$(cat "$LATEST" | jq '[.analysis.issues[]] | add')
        echo "Conversations Analyzed: $TOTAL"
        echo "Total Issues Found: $ISSUES"
    fi
else
    echo "⚠️  No analysis reports found"
    echo "Run: ./scripts/auto-analyze.sh"
fi
echo ""

echo "════════════════════════════════════════════════════════════"
echo "📋 QUICK COMMANDS"
echo "════════════════════════════════════════════════════════════"
echo "  pm2 logs career-flow-api    - View server logs"
echo "  ./scripts/auto-analyze.sh   - Run analysis now"
echo "  ./scripts/view-recommendations.sh - View AI suggestions"
echo "  ./scripts/analyze-conversations.sh - View conversations"
echo "  pm2 restart career-flow-api - Restart server"
echo ""
echo "════════════════════════════════════════════════════════════"