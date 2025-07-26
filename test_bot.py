#!/usr/bin/env python3
"""
Test script for the Domain Checker Bot
Tests all major functionality without requiring Telegram
"""

import asyncio
import logging
from datetime import datetime

from config.settings import settings
from services.database import DatabaseService
from services.checker import DomainChecker

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_operations():
    """Test database operations"""
    print("\n🔧 Testing Database Operations...")
    
    try:
        db = DatabaseService(settings.MONGO_URL)
        
        # Test adding domains
        test_domains = ['google.com', 'github.com', 'nonexistent-domain-12345.com']
        
        for domain in test_domains:
            result = db.add_domain(domain)
            print(f"  ➕ Add {domain}: {'✅ Success' if result else '❌ Failed'}")
        
        # Test getting all domains
        domains = db.get_all_domains()
        print(f"  📋 Total domains: {len(domains)}")
        
        # Test domain count
        count = db.get_domains_count()
        print(f"  🔢 Domain count: {count}")
        
        # Test getting specific domain
        domain_doc = db.get_domain('google.com')
        print(f"  🔍 Get google.com: {'✅ Found' if domain_doc else '❌ Not found'}")
        
        # Clean up test domains
        for domain in test_domains:
            db.remove_domain(domain)
            print(f"  🗑️ Remove {domain}: ✅ Done")
        
        db.close()
        print("  ✅ Database tests completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")

async def test_domain_checker():
    """Test domain checking functionality"""
    print("\n🔍 Testing Domain Checker...")
    
    try:
        # Test single domain check (sync)
        print("  Testing synchronous domain check...")
        result = DomainChecker.check_domain_sync('google.com')
        print(f"    google.com: {result['status']} ({result.get('response_time', 0):.2f}s)")
        
        # Test single domain check (async)
        print("  Testing asynchronous domain check...")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            result = await DomainChecker.check_domain_async(session, 'github.com')
            print(f"    github.com: {result['status']} ({result.get('response_time', 0):.2f}s)")
        
        # Test multiple domains check
        print("  Testing multiple domains check...")
        test_domains = ['google.com', 'github.com', 'stackoverflow.com', 'nonexistent-domain-12345.com']
        results = await DomainChecker.check_multiple_domains(test_domains)
        
        for result in results:
            status_emoji = "✅" if result['status'] == 'up' else "🚨"
            time_text = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
            error_text = f" - {result['error']}" if result['error'] else ""
            print(f"    {status_emoji} {result['domain']}: {result['status'].upper()}{time_text}{error_text}")
        
        print("  ✅ Domain checker tests completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Domain checker test failed: {e}")

async def test_integration():
    """Test integration between database and checker"""
    print("\n🔗 Testing Integration...")
    
    try:
        db = DatabaseService(settings.MONGO_URL)
        
        # Add test domains
        test_domains = ['google.com', 'github.com']
        for domain in test_domains:
            db.add_domain(domain)
        
        # Check domains and update database
        results = await DomainChecker.check_multiple_domains(test_domains)
        
        for result in results:
            db.update_domain_status(result['domain'], result)
            print(f"  📊 Updated {result['domain']}: {result['status']}")
        
        # Verify updates
        for domain in test_domains:
            domain_doc = db.get_domain(domain)
            if domain_doc:
                last_status = domain_doc.get('last_status', 'unknown')
                last_checked = domain_doc.get('last_checked')
                print(f"  ✅ {domain}: {last_status} (checked: {last_checked})")
        
        # Clean up
        for domain in test_domains:
            db.remove_domain(domain)
        
        db.close()
        print("  ✅ Integration tests completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        print(f"  🔑 Telegram token: {'✅ Set' if settings.TELEGRAM_TOKEN else '❌ Missing'}")
        print(f"  👥 Admin chat IDs: {settings.ADMIN_CHAT_IDS}")
        print(f"  🗄️ MongoDB URL: {'✅ Set' if settings.MONGO_URL else '❌ Missing'}")
        
        # Test admin check function
        admin_check = settings.is_admin
        if settings.ADMIN_CHAT_IDS:
            test_id = settings.ADMIN_CHAT_IDS[0]
            is_admin = admin_check(test_id)
            print(f"  🔐 Admin check for {test_id}: {'✅ Admin' if is_admin else '❌ Not admin'}")
        
        print("  ✅ Configuration tests completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Domain Checker Bot Tests")
    print("=" * 50)
    
    # Test configuration first
    test_configuration()
    
    # Test database operations
    await test_database_operations()
    
    # Test domain checker
    await test_domain_checker()
    
    # Test integration
    await test_integration()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nIf all tests passed, your bot should be ready to run!")
    print("Start the bot with: python main.py")

if __name__ == '__main__':
    asyncio.run(run_all_tests())