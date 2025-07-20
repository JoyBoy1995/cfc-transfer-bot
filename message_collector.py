#!/usr/bin/env python3
"""
Telegram Message Fetcher
Fetches 50 recent messages from transfer_news_football for analysis
"""

import asyncio
from datetime import datetime
from telethon import TelegramClient

# Your Telegram API credentials
API_ID = 28505309
API_HASH = '8a967c95f14482abb3f347bdda238992'
PHONE = '+13475861486'  # Replace with your phone number (e.g., +1234567890)

# Target channel
CHANNEL_USERNAME = 'transfer_news_football'

async def fetch_messages():
    """Fetch and format messages from the channel"""
    
    print("🔗 Connecting to Telegram...")
    
    # Create client
    client = TelegramClient('session', API_ID, API_HASH)
    
    try:
        # Start client (will ask for verification code first time)
        await client.start(phone=PHONE)
        print("✅ Connected to Telegram")
        
        # Get the channel
        print(f"📡 Fetching messages from @{CHANNEL_USERNAME}...")
        channel = await client.get_entity(CHANNEL_USERNAME)
        
        # Fetch 50 recent messages
        messages = []
        count = 0
        
        async for message in client.iter_messages(channel, limit=300):
            if message.text:  # Only text messages
                count += 1
                messages.append({
                    'number': count,
                    'text': message.text,
                    'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'views': getattr(message, 'views', 0) or 0
                })
        
        print(f"✅ Fetched {len(messages)} messages")
        
        # Format for analysis
        output_lines = []
        output_lines.append(f"TELEGRAM MESSAGES FOR ANALYSIS ({len(messages)} messages)")
        output_lines.append("=" * 60)
        output_lines.append(f"Channel: @{CHANNEL_USERNAME}")
        output_lines.append(f"Fetched: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("=" * 60)
        
        for msg in messages:
            output_lines.append(f"\nMessage {msg['number']}:")
            output_lines.append(f"Date: {msg['date']} | Views: {msg['views']}")
            output_lines.append(f"{msg['text']}")
            output_lines.append("-" * 40)
        
        # Create final output
        formatted_output = "\n".join(output_lines)
        
        # Save to file
        filename = f"telegram_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        
        print(f"💾 Messages saved to: {filename}")
        print("\n" + "=" * 60)
        print("📋 COPY THE TEXT BELOW FOR ANALYSIS:")
        print("=" * 60)
        print(formatted_output)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.disconnect()
        print("👋 Disconnected from Telegram")

def main():
    """Main function"""
    # Check if phone number is set
    if PHONE == '+YOUR_PHONE_NUMBER_HERE':
        print("❌ Please set your phone number in the script!")
        print("Edit the PHONE variable with your number (e.g., +1234567890)")
        return
    
    print("📱 Telegram Message Fetcher")
    print("=" * 40)
    print(f"API ID: {API_ID}")
    print(f"Phone: {PHONE}")
    print(f"Target: @{CHANNEL_USERNAME}")
    print("=" * 40)
    
    # Run the async function
    asyncio.run(fetch_messages())

if __name__ == "__main__":
    main()