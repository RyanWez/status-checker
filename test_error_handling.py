#!/usr/bin/env python3
"""
Test error handling functionality
"""
import asyncio
from telegram.error import BadRequest
from main import DomainBot

async def test_error_handling():
    """Test that error handling works properly"""
    print("🧪 Testing error handling...")
    
    try:
        # Create and initialize bot
        bot = DomainBot()
        await bot.initialize()
        
        # Test error handler with a mock update and context
        class MockUpdate:
            def __init__(self):
                self.callback_query = None
                self.message = None
        
        class MockContext:
            def __init__(self, error):
                self.error = error
        
        # Test BadRequest error handling
        mock_update = MockUpdate()
        mock_context = MockContext(BadRequest("Message is not modified"))
        
        # This should not raise an exception
        await bot._error_handler(mock_update, mock_context)
        print("✅ BadRequest error handling works")
        
        # Test general error handling
        mock_context = MockContext(Exception("Test error"))
        await bot._error_handler(mock_update, mock_context)
        print("✅ General error handling works")
        
        # Clean shutdown
        await bot.shutdown()
        print("✅ Error handling test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_error_handling())
    if success:
        print("\n🎉 Error handling is working properly!")
    else:
        print("\n❌ Error handling needs fixing")