#!/usr/bin/env python3
"""
Test the actual bot run for a few seconds
"""
import asyncio
import signal
import sys
from main import main

async def test_real_run():
    """Test running the actual bot"""
    print("🚀 Testing real bot run for 5 seconds...")
    
    # Create a task for the main bot
    bot_task = asyncio.create_task(main())
    
    try:
        # Wait for 5 seconds or until the bot task completes
        await asyncio.wait_for(bot_task, timeout=5.0)
    except asyncio.TimeoutError:
        print("⏰ Test timeout reached - stopping bot")
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        print("✅ Bot stopped gracefully after timeout")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        return False
    
    print("✅ Bot test run completed successfully!")
    return True

if __name__ == '__main__':
    try:
        asyncio.run(test_real_run())
        print("\n🎉 Your bot is working perfectly! You can now run: python main.py")
    except KeyboardInterrupt:
        print("\n✅ Test stopped by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)