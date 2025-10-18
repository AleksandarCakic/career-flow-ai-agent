#!/bin/bash

echo "🔍 Running automated conversation analysis..."
echo "Timestamp: $(date)"
echo ""

# Create report directory if it doesn't exist
mkdir -p analysis_reports

# Run analysis and save to file with pretty formatting
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="analysis_reports/report_$TIMESTAMP.json"

echo "Fetching analysis from API..."
curl -s -X POST "http://localhost:8000/admin/analyze-conversations?hours=168&min_conversations=1" | jq '.' > "$REPORT_FILE"

# Check if the request was successful
if [ $? -eq 0 ]; then
    echo "✅ Analysis complete"
    echo "📄 Report saved: $REPORT_FILE"
    echo ""
    
    # Display summary
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    STATUS=$(cat "$REPORT_FILE" | jq -r '.analysis.status // "error"')
    
    if [ "$STATUS" = "analyzed" ]; then
        echo "Status: ✅ Analysis Complete"
        echo "Total Conversations: $(cat "$REPORT_FILE" | jq -r '.analysis.total_conversations')"
        echo "Time Period: $(cat "$REPORT_FILE" | jq -r '.analysis.period')"
        echo ""
        echo "Issues Found:"
        cat "$REPORT_FILE" | jq -r '.analysis.issues | to_entries[] | select(.value > 0) | "  ❌ \(.key | gsub("_"; " ") | ascii_upcase): \(.value)"'
        echo ""
        
        # Check if improvements were generated
        IMPROVEMENTS=$(cat "$REPORT_FILE" | jq -r '.improvements.status // "none"')
        if [ "$IMPROVEMENTS" = "improvements_generated" ]; then
            echo "🤖 AI RECOMMENDATIONS:"
            echo ""
            
            # Parse and display the improvements JSON
            cat "$REPORT_FILE" | jq -r '.improvements.improvements | fromjson | 
                "Critical Issues:\n" + 
                (.critical_issues | map("  • " + .) | join("\n")) + 
                "\n\nRecommended Changes:\n" + 
                (.improvements | map("
  " + (.issue | ascii_upcase) + ":
  💡 " + .suggestion + "
  ✓ Why: " + .reasoning + "
") | join("\n"))'
            
            echo ""
            echo "📊 Full report: $REPORT_FILE"
        else
            echo "ℹ️  No AI recommendations generated"
        fi
    elif [ "$STATUS" = "insufficient_data" ]; then
        echo "Status: ⚠️  Insufficient Data"
        echo "Conversations found: $(cat "$REPORT_FILE" | jq -r '.count // 0')"
        echo "Need at least 1 conversation for analysis"
    else
        echo "Status: ❌ Error"
        echo "Details:"
        cat "$REPORT_FILE" | jq '.'
    fi
else
    echo "❌ Failed to fetch analysis from API"
    echo "Make sure the server is running on http://localhost:8000"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"