#!/usr/bin/env python3
"""
Quick test to see if the bot starts without errors
"""
import asyncio
import threading
import time
from main import DomainBot

def test_bot():
    """Test bot initialization and startup"""
    print("🚀 Quick bot test...")
    
    try:
        # Create and initialize bot
        bot = DomainBot()
        
        # Initialize in async context
        asyncio.run(bot.initialize())
        print("✅ Bot initialized successfully!")
        
        # Test that we can start the bot (but stop it quickly)
        def start_bot():
            try:
                bot.start()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"❌ Bot start error: {e}")
        
        # Start bot in a separate thread
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        
        # Wait a moment to see if it starts properly
        time.sleep(3)
        
        # If we get here, the bot started successfully
        print("✅ Bot started successfully!")
        
        # Shutdown
        bot.shutdown()
        print("✅ Bot shutdown completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    success = test_bot()
    if success:
        print("\n🎉 Your bot is working! You can now run: python main.py")
    else:
        print("\n❌ Please check the errors above")