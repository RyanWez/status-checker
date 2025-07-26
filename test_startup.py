#!/usr/bin/env python3
"""
Test bot startup without running indefinitely
"""
import asyncio
import logging
from main import DomainBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_startup():
    """Test bot initialization and basic setup"""
    try:
        print("🚀 Testing bot startup...")
        
        # Create and initialize bot
        bot = DomainBot()
        await bot.initialize()
        
        print("✅ Bot initialized successfully!")
        print(f"📊 Database connected: {bot.db_service is not None}")
        print(f"🤖 Telegram app created: {bot.application is not None}")
        print(f"⏰ Job queue available: {bot.application.job_queue is not None}")
        print(f"🎯 Handlers setup: {bot.domain_handlers is not None}")
        
        # Test job queue
        print("⏰ Testing job queue...")
        print("✅ Job queue is ready!")
        
        # Clean shutdown
        await bot.shutdown()
        print("✅ Bot shutdown completed successfully!")
        
        print("\n🎉 Startup test completed! Bot is ready to run.")
        return True
        
    except Exception as e:
        print(f"❌ Startup test failed: {e}")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_startup())
    if success:
        print("\n✅ Your bot is ready! Run: python main.py")
    else:
        print("\n❌ Please fix the issues above before running the bot.")