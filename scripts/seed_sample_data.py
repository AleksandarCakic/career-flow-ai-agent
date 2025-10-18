"""Seed database with sample conversations for demo purposes."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db, init_db
from src.models.models import Conversation, Message, User, ConversationStatus, MessageRole

def clear_existing_data(db):
    """Clear existing sample data."""
    print("🗑️  Clearing existing data...")
    
    # Delete sample conversations first (has foreign key to users)
    sample_call_sids = [f"CA_sample_{str(i).zfill(3)}" for i in range(1, 10)]
    deleted_convs = db.query(Conversation).filter(
        Conversation.call_sid.in_(sample_call_sids)
    ).delete(synchronize_session=False)
    
    db.commit()
    print(f"   Deleted {deleted_convs} conversations")
    
    # Delete users with sample phone numbers
    sample_phones = ["+15551234567", "+15559876543"]
    deleted_users = db.query(User).filter(
        User.phone_number.in_(sample_phones)
    ).delete(synchronize_session=False)
    
    db.commit()
    print(f"   Deleted {deleted_users} users")
    print("✅ Cleared existing data")

def create_sample_users(db):
    """Create sample users."""
    users = [
        User(
            phone_number="+15551234567",
            first_name="Alex",
            last_name="Johnson",
            email="alex.johnson@example.com",
            user_data={"industry": "software_engineering", "experience_years": 5}
        ),
        User(
            phone_number="+15559876543",
            first_name="Sarah",
            last_name="Chen",
            email="sarah.chen@example.com",
            user_data={"industry": "marketing", "experience_years": 3}
        )
    ]
    
    db.add_all(users)
    db.commit()
    db.refresh(users[0])
    db.refresh(users[1])
    
    print(f"✅ Created {len(users)} users")
    return users

def create_conversation(
    db,
    call_sid: str,
    user_id,
    phone_number: str,
    status: ConversationStatus,
    duration_seconds: int,
    hours_ago: int = 0
) -> Conversation:
    """Helper to create a conversation."""
    started_at = datetime.now() - timedelta(hours=hours_ago)
    ended_at = started_at + timedelta(seconds=duration_seconds)
    
    conv = Conversation(
        call_sid=call_sid,
        user_id=user_id,
        phone_number=phone_number,
        status=status,
        duration_seconds=duration_seconds,
        started_at=started_at,
        ended_at=ended_at
    )
    
    db.add(conv)
    db.commit()
    db.refresh(conv)
    
    # Update user's last_call_at
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if not user.last_call_at or started_at > user.last_call_at:
            user.last_call_at = started_at
            db.commit()
    
    return conv

def add_messages(db, conversation_id, messages_data):
    """Helper to add multiple messages at once."""
    messages = [
        Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        for role, content in messages_data
    ]
    db.add_all(messages)
    db.commit()
    print(f"   Added {len(messages)} messages to conversation")

def seed_conversations(db, users):
    """Create sample conversations with various issues."""
    
    user_alex = users[0]
    user_sarah = users[1]
    
    print("\n📝 Creating conversations...")
    
    # Conversation 1: Perfect conversation (name collected, transfer successful)
    print("\n1️⃣  Creating perfect conversation...")
    conv1 = create_conversation(
        db,
        call_sid="CA_sample_001",
        user_id=user_alex.id,
        phone_number="+15551234567",
        status=ConversationStatus.COMPLETED,
        duration_seconds=120,
        hours_ago=2
    )
    
    add_messages(db, conv1.id, [
        (MessageRole.ASSISTANT, "Hi! I'm Mica, your AI career coach. What's your name?"),
        (MessageRole.USER, "I'm Alex Johnson"),
        (MessageRole.ASSISTANT, "Nice to meet you, Alex! How can I help you today?"),
        (MessageRole.USER, "I need help with my resume"),
        (MessageRole.ASSISTANT, "I'd be happy to help with your resume, Alex! What industry are you targeting?"),
        (MessageRole.USER, "Software engineering"),
        (MessageRole.ASSISTANT, "Perfect! Would you like me to connect you with Alex, our tech career specialist?"),
    ])
    
    # Conversation 2: Name NOT collected (user didn't provide name)
    print("2️⃣  Creating conversation with missing name...")
    conv2 = create_conversation(
        db,
        call_sid="CA_sample_002",
        user_id=user_sarah.id,
        phone_number="+15559876543",
        status=ConversationStatus.COMPLETED,
        duration_seconds=90,
        hours_ago=120  # 5 days ago
    )
    
    add_messages(db, conv2.id, [
        (MessageRole.ASSISTANT, "Hi! I'm Mica. What's your name?"),
        (MessageRole.USER, "I want to learn about your services"),
        (MessageRole.ASSISTANT, "Great! We offer career coaching, resume writing, LinkedIn optimization, and interview prep."),
        (MessageRole.USER, "How much does it cost?"),
        (MessageRole.ASSISTANT, "Our main package is $1,000 per month. Would you like to schedule a consultation?"),
    ])
    
    # Conversation 3: Transfer requested but NOT executed
    print("3️⃣  Creating conversation with transfer failure...")
    conv3 = create_conversation(
        db,
        call_sid="CA_sample_003",
        user_id=user_sarah.id,
        phone_number="+15559876543",
        status=ConversationStatus.COMPLETED,
        duration_seconds=150,
        hours_ago=165  # Almost 7 days ago
    )
    
    add_messages(db, conv3.id, [
        (MessageRole.ASSISTANT, "Hi! I'm Mica, your AI career coach. What's your name?"),
        (MessageRole.USER, "Sarah Chen"),
        (MessageRole.ASSISTANT, "Nice to meet you, Sarah! How can I help?"),
        (MessageRole.USER, "Can you connect me with Alex?"),
        (MessageRole.ASSISTANT, "I'd be happy to connect you with Alex! Let me transfer you now."),
        (MessageRole.SYSTEM, "Transfer requested but not executed"),
    ])
    
    # Conversation 4: Technical error occurred
    print("4️⃣  Creating conversation with technical error...")
    conv4 = create_conversation(
        db,
        call_sid="CA_sample_004",
        user_id=user_sarah.id,
        phone_number="+15559876543",
        status=ConversationStatus.COMPLETED,
        duration_seconds=60,
        hours_ago=72  # 3 days ago
    )
    
    add_messages(db, conv4.id, [
        (MessageRole.ASSISTANT, "Hi! I'm Mica. What's your name?"),
        (MessageRole.USER, "[unintelligible]"),
        (MessageRole.ASSISTANT, "Sorry, I had a technical hiccup. Could you repeat that?"),
        (MessageRole.USER, "My name is Sarah"),
        (MessageRole.ASSISTANT, "Got it, Sarah! How can I help you today?"),
    ])
    
    # Conversation 5: Long conversation + multiple questions
    print("5️⃣  Creating long conversation with multiple questions...")
    conv5 = create_conversation(
        db,
        call_sid="CA_sample_005",
        user_id=user_alex.id,
        phone_number="+15551234567",
        status=ConversationStatus.COMPLETED,
        duration_seconds=300,
        hours_ago=1
    )
    
    add_messages(db, conv5.id, [
        (MessageRole.ASSISTANT, "Hi! I'm Mica, your AI career coach. What's your name?"),
        (MessageRole.USER, "Alex"),
        (MessageRole.ASSISTANT, "Hi Alex! How can I help?"),
        (MessageRole.USER, "I have a lot of questions about career coaching"),
        (MessageRole.ASSISTANT, "I'm here to help! What's your first question?"),
        (MessageRole.USER, "What services do you offer? How much do they cost? Who are the coaches? Can I choose my coach?"),
        (MessageRole.ASSISTANT, "Let me answer each question. We offer career coaching, resume help, interview prep..."),
        (MessageRole.USER, "Tell me more about the coaches"),
        (MessageRole.ASSISTANT, "We have Alex for tech careers, Atiyeh for executive coaching, Anna for design..."),
        (MessageRole.USER, "What about LinkedIn help?"),
        (MessageRole.ASSISTANT, "Yes, we offer LinkedIn profile optimization as part of our coaching package."),
        (MessageRole.USER, "And resume writing?"),
        (MessageRole.ASSISTANT, "Absolutely! Resume writing is one of our core services."),
    ])
    
    return [conv1, conv2, conv3, conv4, conv5]

def main():
    """Main seeding function."""
    print("\n🌱 Seeding sample data...")
    
    # Initialize database
    init_db()
    db = next(get_db())
    
    try:
        # Always clear existing data first
        clear_existing_data(db)
        
        # Create users
        users = create_sample_users(db)
        
        # Create conversations (pass users)
        conversations = seed_conversations(db, users)
        
        # Count messages
        total_messages = db.query(Message).count()
        
        print("\n✅ Sample data seeded successfully!")
        print(f"   📞 {len(conversations)} conversations")
        print(f"   💬 {total_messages} messages")
        print(f"   👤 {len(users)} users")
        
        print("\n🔍 Issues to detect:")
        print("   - Conversation 2: Name NOT collected")
        print("   - Conversation 3: Transfer requested but not executed")
        print("   - Conversation 4: Technical error occurred")
        print("   - Conversation 5: Long conversation (13 messages)")
        print("   - Conversation 5: Multiple questions asked at once")
        
        print("\n" + "="*70)
        print("📋 NEXT STEPS")
        print("="*70)
        print()
        print("1. Run full analysis:")
        print("   ./scripts/auto-analyze.sh")
        print()
        print("2. View AI recommendations:")
        print("   ./scripts/view-recommendations.sh")
        print()
        print("3. View conversation transcripts:")
        print("   ./scripts/analyze-conversations.sh")
        print()
        print("4. Debug pattern detection:")
        print("   python scripts/debug-detection.py")
        print()
        print("="*70)
        print()
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()