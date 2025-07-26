#!/usr/bin/env python3
"""
Test bot run for a few seconds to ensure it starts properly
"""
import asyncio
import signal
import sys
from main import main

async def test_run():
    """Test running the bot for a few seconds"""
    print("🚀 Testing bot run for 10 seconds...")
    
    # Set up a timer to stop the bot after 10 seconds
    def timeout_handler():
        print("\n⏰ Test timeout reached - stopping bot")
        # Send SIGINT to stop the bot gracefully
        import os
        os.kill(os.getpid(), signal.SIGINT)
    
    # Schedule timeout
    loop = asyncio.get_event_loop()
    loop.call_later(10, timeout_handler)
    
    try:
        # Run the bot
        main()
    except KeyboardInterrupt:
        print("✅ Bot stopped gracefully")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        return False
    
    print("✅ Bot test run completed successfully!")
    return True

if __name__ == '__main__':
    try:
        asyncio.run(test_run())
    except KeyboardInterrupt:
        print("✅ Test completed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)