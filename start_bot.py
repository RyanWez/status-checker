#!/usr/bin/env python3
"""
Production bot starter with better error handling
"""
import asyncio
import logging
import sys
from main import main

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        print("🤖 Starting Telegram Domain Checker Bot...")
        print("Press Ctrl+C to stop the bot")
        print("-" * 50)
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Bot failed to start: {e}")
        sys.exit(1)