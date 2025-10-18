"""Debug script for pattern detection logic."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db
from src.models.models import Conversation, Message, MessageRole
from datetime import datetime, timedelta

def debug_pattern_detection():
    """Debug the pattern detection logic by analyzing sample conversations."""
    print("\n" + "="*70)
    print("🔍 DEBUG: Pattern Detection Analysis")
    print("="*70 + "\n")
    
    db = next(get_db())
    
    try:
        # Get recent conversations
        cutoff_time = datetime.now() - timedelta(hours=168)
        conversations = db.query(Conversation).filter(
            Conversation.started_at >= cutoff_time
        ).all()
        
        print(f"📊 Found {len(conversations)} conversations to analyze\n")
        
        for conv in conversations:
            print("─" * 70)
            print(f"🔵 Conversation: {conv.call_sid}")
            print(f"   Phone: {conv.phone_number}")
            print(f"   Duration: {conv.duration_seconds}s")
            print(f"   Started: {conv.started_at}")
            print()
            
            # Get messages
            messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).all()
            
            if not messages:
                print("   ⚠️  No messages found\n")
                continue
            
            # Separate by role
            user_messages = [m for m in messages if m.role.value == MessageRole.USER.value]
            assistant_messages = [m for m in messages if m.role.value == MessageRole.ASSISTANT.value]
            system_messages = [m for m in messages if m.role.value == MessageRole.SYSTEM.value]
            total_messages = len(messages)
            
            print(f"   📈 Message counts:")
            print(f"      User: {len(user_messages)}")
            print(f"      Assistant: {len(assistant_messages)}")
            print(f"      System: {len(system_messages)}")
            print(f"      Total: {total_messages}")
            print()
            
            # Check 1: Technical errors
            print("   🔍 Checking for technical errors...")
            error_keywords = ["error", "hiccup", "technical", "problem", "issue", 
                            "unintelligible", "didn't catch", "couldn't understand"]
            found_errors = []
            for msg in messages:
                if any(keyword in msg.content.lower() for keyword in error_keywords):
                    found_errors.append(msg.content[:50])
            
            if found_errors:
                print(f"      ❌ FOUND {len(found_errors)} technical error(s)")
                for err in found_errors:
                    print(f"         → {err}...")
            else:
                print("      ✅ No technical errors")
            print()
            
            # Check 2: Transfer failures
            print("   🔍 Checking for transfer failures...")
            transfer_requested = any(
                "transfer" in m.content.lower() or "connect" in m.content.lower() 
                for m in assistant_messages
            )
            transfer_failed = any(
                "not executed" in m.content.lower() or "failed" in m.content.lower() 
                for m in system_messages
            )
            
            if transfer_requested and transfer_failed:
                print("      ❌ FOUND transfer failure")
                print(f"         Transfer requested: {transfer_requested}")
                print(f"         Transfer failed: {transfer_failed}")
            else:
                print("      ✅ No transfer failures")
            print()
            
            # Check 3: Multiple questions
            print("   🔍 Checking for multiple questions...")
            multi_question_msgs = []
            for msg in user_messages:
                question_marks = msg.content.count('?')
                if question_marks >= 3:
                    multi_question_msgs.append((msg.content[:50], question_marks))
            
            if multi_question_msgs:
                print(f"      ❌ FOUND {len(multi_question_msgs)} message(s) with multiple questions")
                for content, count in multi_question_msgs:
                    print(f"         → {count} questions: {content}...")
            else:
                print("      ✅ No multiple question issues")
            print()
            
            # Check 4: Long conversations
            print("   🔍 Checking conversation length...")
            if total_messages > 10:
                print(f"      ❌ FOUND long conversation: {total_messages} messages")
            else:
                print(f"      ✅ Conversation length OK: {total_messages} messages")
            print()
            
            # Check 5: Name collection
            print("   🔍 Checking name collection...")
            name_collected = False
            name_keywords = ["name is", "i'm", "im", "this is", "call me"]
            
            # Check first 3 user messages for name
            for msg in user_messages[:3]:
                content_lower = msg.content.lower()
                
                # Check for name keywords
                if any(kw in content_lower for kw in name_keywords):
                    name_collected = True
                    print(f"      ✅ Name collected: \"{msg.content[:40]}...\"")
                    break
                
                # Check for short name response (1-3 words)
                if len(msg.content.split()) <= 3:
                    msg_index = user_messages.index(msg)
                    if msg_index < len(assistant_messages):
                        prev_assistant = assistant_messages[msg_index]
                        if "name" in prev_assistant.content.lower():
                            name_collected = True
                            print(f"      ✅ Name collected (short): \"{msg.content}\"")
                            break
            
            # Check if assistant asked for name
            assistant_asked_name = any(
                "name" in m.content.lower() and "?" in m.content 
                for m in assistant_messages[:2]
            )
            
            if assistant_asked_name and not name_collected and len(user_messages) > 2:
                print(f"      ❌ FOUND name not collected issue")
                print(f"         Assistant asked: {assistant_asked_name}")
                print(f"         Name collected: {name_collected}")
                print(f"         User messages: {len(user_messages)}")
            elif not name_collected:
                print("      ⚠️  Name not collected (but may not be required)")
            
            print()
        
        print("="*70)
        print("✅ Debug analysis complete!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # Next Steps
    print("="*70)
    print("📋 NEXT STEPS")
    print("="*70)
    print()
    print("1. View AI recommendations:")
    print("   ./scripts/view-recommendations.sh")
    print()
    print("2. View conversation transcripts:")
    print("   ./scripts/analyze-conversations.sh")
    print()
    print("3. Run full analysis:")
    print("   ./scripts/auto-analyze.sh")
    print()
    print("4. Reseed with fresh data:")
    print("   python scripts/seed_sample_data.py")
    print()
    print("="*70)
    print()

if __name__ == "__main__":
    debug_pattern_detection()